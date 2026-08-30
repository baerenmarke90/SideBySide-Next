# Secure Self-Hosted Operation

## Two operating modes

The bundled Compose stack supports two operating modes, and the distinction is
not incidental:

| | local test mode | production mode |
|---|---|---|
| `SBS_ENVIRONMENT` | `development` (default) | `production` |
| cursor signing key | local fallback value | required, at least 32 characters |
| outgoing mail | written to the log | `smtp` or `none`, never `log` |
| `SBS_PUBLIC_BASE_URL` | `http://localhost:8080` | must use `https://` |
| HTTPS enforcement, host validation | off | on |
| schema documentation `/docs` | open | closed |

The default is test mode. This is a deliberate decision
([ADR 0002](decisions/0002-self-hosted-first-start-mode.md)): initial startup
must be possible without SMTP access and without an HTTPS domain. The Web PoC
and API are bound exclusively to `127.0.0.1` in this mode and therefore remain
unreachable from the LAN or Internet even if the host firewall is configured
too permissively.

On every startup, the application reports which operating mode it is using. In
test mode this appears as a warning in `docker compose logs api`.

## Local test

```bash
cp .env.example .env
# Replace at least POSTGRES_PASSWORD with a long, random secret.
# Set SBS_BOOTSTRAP_TOKEN in .env to a separately generated secret with
# at least 32 characters.
docker compose config --quiet
docker compose up -d --wait --wait-timeout 300
```

`API_PORT=8000` and `WEB_PORT=8080` are only default values. Both ports must be
free on the Docker host. If either port is already in use, choose a free port in
`.env` before startup, for example:

```dotenv
API_PORT=8010
WEB_PORT=8081
SBS_PUBLIC_BASE_URL=http://localhost:8081
```

This changes only the host ports. The API and Web service continue to listen on
8000 and 8080 respectively inside their containers. A host port that is already
in use must not be shared by a second service; `docker compose up` must fail
clearly in that case.

Compose shows the port that is actually published:

```bash
docker compose port api 8000
docker compose port web 8080
```

Both outputs must be bound to `127.0.0.1`. An output containing `0.0.0.0`, `::`,
or an unexpected external address is not allowed for the default setup.

After startup, verify operational readiness rather than only whether the HTTP
process is running:

```bash
api_port=$(docker compose port api 8000 | awk -F: '{print $NF}')
web_port=$(docker compose port web 8080 | awk -F: '{print $NF}')
curl --fail "http://127.0.0.1:${api_port}/api/v1/health/ready"
curl --fail "http://127.0.0.1:${web_port}/healthz"
curl --fail "http://127.0.0.1:${web_port}/"
```

Expected response:

```json
{"status":"ok","database":"ok"}
```

The Web start page requires no Space configuration. After authentication, the
client discovers the account's active Memberships through the API and uses only
a server-authorized Space. No Space UUID is embedded in the Web image.

This state is intended for evaluation, not publication. Before making the
instance reachable, complete the production checklist below.

The source-code development workflow is separate again:
`deploy/docker-compose.dev.yml` starts PostgreSQL only. A locally started
Uvicorn process is a development server and is not a template for an
externally reachable production service.

## Compose network and readiness

`postgres`, `migrate`, `api`, `worker`, and `web` are explicitly attached to the
same project-specific bridge network `app` in `compose.yaml`. The concrete
Docker network name also contains the Compose project name so multiple
SideBySide stacks on the same host do not collide.

The database URL deliberately uses the Compose service name `postgres:5432`.
Container IDs, fixed Docker IP addresses, and host ports do not belong in
`SBS_DATABASE_URL`.

After a deployment, the Docker DNS path can be checked directly from the API:

```bash
docker compose exec -T api python -c \
  'import socket; print(socket.gethostbyname("postgres"))'
```

Additional check of the actual network state:

```bash
api_id=$(docker compose ps -q api)
docker inspect "$api_id" --format '{{json .NetworkSettings.Networks}}'
```

A running API container with an empty `{}` result is **not** ready. In that
state, Docker DNS cannot resolve `postgres`.

SideBySide separates two health questions:

- `/api/v1/health` is pure **liveness**: the API process responds.
- `/api/v1/health/ready` is **readiness**: the API can also reach PostgreSQL and
  execute a real `SELECT 1`.
- `/healthz` on the Web service confirms only that the static server responds.
  API dependency is represented separately through Compose and API readiness.

The API Docker health check deliberately uses the readiness route. This makes
`docker compose up -d --wait` report a missing database/network path as a
deployment failure even if Uvicorn itself is still running. Docker Compose does
not restart a process merely because its status is `unhealthy`, so a temporary
database outage remains distinct from a process crash.

## Production operation checklist

Before the first public startup, set the following in `.env`:

```dotenv
SBS_ENVIRONMENT=production
SBS_CURSOR_SIGNING_KEY=...        # openssl rand -base64 48
SBS_PUBLIC_BASE_URL=https://your-domain.example
SBS_ALLOWED_HOSTS=["your-domain.example"]
TRUSTED_PROXY_IPS=...             # smallest IP range used by the reverse proxy
# With a mail server:
SBS_MAIL_TRANSPORT=smtp
SBS_MAIL_FROM=no-reply@your-domain.example
SBS_SMTP_HOST=smtp.your-domain.example

# Or without a mail server - see below:
# SBS_MAIL_TRANSPORT=none
```

If the cursor signing key is missing or the base URL does not use `https://`,
the application refuses to start. This is intentional and must not be bypassed:
the cursor signing key protects the integrity of opaque pagination cursors, and
a sign-in link delivered over plaintext HTTP is a transferable credential.

### Operation without a mail server

SMTP access is **not** a startup requirement. With `SBS_MAIL_TRANSPORT=none`,
the instance runs without a mail path:

- Magic Link, password Recovery, and email verification return
  `503 MAIL_TRANSPORT_UNAVAILABLE` instead of promising a message that will
  never arrive.
- Sign-in through password, Passkey/WebAuthn, and OIDC continues to work.
- A user who forgets their password and has no Passkey cannot recover access
  without mail delivery. That is the trade-off of this operating mode.

Production explicitly **does not** accept `SBS_MAIL_TRANSPORT=log`. That mode
would place valid single-use tokens in API logs and therefore in any log
aggregation or backup containing them. The distinction from `none` is
substantive: with `none`, no token leaves the system.

Then run `docker compose up -d --build --force-recreate --wait --wait-timeout
300` and verify that `docker compose logs api` reports production mode.
`--build` ensures the deployed Web and backend images match the selected source revision.

## Media storage

`SBS_MEDIA_STORE=local` is the default. The API and worker use the private
Compose volume `media_data`; filesystem paths are not exposed to clients.

For an S3-compatible object store, configure `.env` instead as follows:

```dotenv
SBS_MEDIA_STORE=s3
SBS_S3_ENDPOINT=https://s3.example.com
SBS_S3_REGION=eu-central-1
SBS_S3_BUCKET=sidebyside-private
SBS_S3_ACCESS_KEY_ID=...
SBS_S3_SECRET_ACCESS_KEY=...
# Only for temporary provider credentials:
# SBS_S3_SESSION_TOKEN=...
```

The endpoint is an S3 API origin without embedded credentials or a subpath.
HTTPS must be used for production traffic over networks that are not fully
trusted. The bucket itself remains private: no public ACLs, no anonymous read
policy, and no static website exposure. Server credentials need only the
GET/PUT/HEAD/DELETE object operations for the bucket/key prefix in use; making
the bucket public is not required.

With S3, the client uploads directly to the exact generated storage key using a
server-signed PUT capability. The upload URL is valid for exactly 10 minutes and
is bound with `If-None-Match: *` to prevent later overwriting of the same object.
A provider upload does not set the Attachment to `READY`: `finalizeUpload`
verifies the object server-side and the existing validation remains the sole
authority for transitioning to `READY`.

Reads are released only after the normal Membership/parent authorization. The
signed GET URL is valid for exactly 5 minutes and only for that object. An
already-issued URL can technically continue to work after Membership or privacy
revocation until those 5 minutes have elapsed. This is the documented privacy
trade-off of the S3 adapter; no new URLs are issued after revocation.

Descriptor responses and stored objects use `Cache-Control: private, no-store`;
the API additionally sets `Referrer-Policy: no-referrer` for descriptors.
Presigned URLs, signatures, and storage credentials must not be copied into
access logs, analytics, support data, or persistent client caches.

For a browser client, the bucket requires a narrow CORS rule for the concrete
SideBySide origin. Uploads require `PUT` and the `Content-Type`, `Cache-Control`,
and `If-None-Match` headers; direct reads require `GET`/`HEAD`. No CORS rule
replaces the private bucket policy or server-side authorization.

The Web container also permits this direct connection in its Content Security
Policy. Compose forwards only the exact `SBS_S3_ENDPOINT` origin into
`connect-src`. Wildcards, scheme-wide allowances such as `https:`, paths,
credentials, and free-form CSP fragments are rejected before Nginx starts.
Normal users do not configure this. An alternative Cloud/hosting topology may
set multiple exact origins on the Web container as a whitespace-separated
`SBS_WEB_CSP_CONNECT_ORIGINS` value; in the canonical Compose path this
technical value is derived automatically.

## One-time initial registration

An empty instance accepts the first account only with the `SBS_BOOTSTRAP_TOKEN`
configured in the local `.env`. The value is passed as `bootstrapToken` to
`POST /api/v1/auth/register`. It is neither stored in the database nor logged by
the application.

For an instance without existing users:

1. Generate a random secret with at least 32 characters and store it only as
   `SBS_BOOTSTRAP_TOKEN` in the untracked `.env`.
2. Start the stack and perform the first registration locally through
   `127.0.0.1`.
3. After successful registration, remove `SBS_BOOTSTRAP_TOKEN` from `.env` and
   recreate the API container with `docker compose up -d --force-recreate api`.
4. Register all additional accounts exclusively through invitations.

The database records successful bootstrap completion permanently. Neither the
same value nor a later replacement bootstrap value can create a second initial
owner. Two concurrent initial registrations are serialized by PostgreSQL;
exactly one can succeed.

The secret must not enter shell history, screenshots, support requests, or
repository files. `.env` is therefore excluded by `.gitignore`.

## Access from the LAN or Internet

External access is provided exclusively through a TLS reverse proxy on the
same host or in a controlled private network. The secure default in
`compose.yaml` binds Web and API to loopback only.

On the same host, the proxy requires two targets on the same public HTTPS
origin:

| Path | Internal target |
|---|---|
| `/api/` | `http://127.0.0.1:<API_PORT>` |
| all other paths | `http://127.0.0.1:<WEB_PORT>` |

The more specific `/api/` route must take precedence over the general Web
route. In production it goes **directly** to the API, not through the Web
container. Only the local loopback test uses the Web container's internal
`/api/` proxy. This preserves the TLS reverse proxy as the single trusted hop
for `X-Forwarded-*`, so `TRUSTED_PROXY_IPS` does not need to include the Compose
network or `*`.

If the reverse proxy runs on a **different** host, neither loopback target is
reachable from it. The deployment then needs a deliberately configured,
private-network-limited exposure for Web and API instead of a blanket bind to
`0.0.0.0`. That exposure belongs to hosting configuration and must not arise
accidentally from the standard Compose stack.

Set the following additionally in `.env`:

```dotenv
SBS_ALLOWED_HOSTS=["sidebyside.example.com","localhost","127.0.0.1"]
TRUSTED_PROXY_IPS=192.0.2.10
```

- `SBS_ALLOWED_HOSTS` is a JSON list of public API hostnames. A global `"*"` is
  rejected in production.
- `TRUSTED_PROXY_IPS` is the exact address or smallest CIDR range from which the
  proxy reaches the API container. Never use `*`.
- The proxy sets `Host`, `X-Forwarded-For`, and `X-Forwarded-Proto: https`
  itself; Forwarded headers supplied by the client are not trusted blindly.
- TLS certificates must be valid and renewed automatically.

The application still rejects an allowed external host unless the request
scheme sanitized by Uvicorn is `https`. A normal client cannot bypass this
check merely by forging a Forwarded header.

After proxy configuration, both paths must work:

```bash
curl --fail https://sidebyside.example.com/
curl --fail https://sidebyside.example.com/api/v1/health/ready
web/scripts/check_csp_header.sh https://sidebyside.example.com/
```

If API readiness responds but the start page does not, the general route still
points to the API port instead of the Web port.

## Outgoing email

Magic Link and password Recovery require a mail path. The default is
`SBS_MAIL_TRANSPORT=log`: the message is written to the API log so both flows
can be tested without a mail server.

For real operation, configure an SMTP server:

```dotenv
SBS_MAIL_TRANSPORT=smtp
SBS_MAIL_FROM=no-reply@your-domain.example
SBS_SMTP_HOST=smtp.your-domain.example
SBS_SMTP_PORT=587
SBS_SMTP_USERNAME=...
SBS_SMTP_PASSWORD=...
SBS_PUBLIC_BASE_URL=https://your-domain.example
```

`SBS_PUBLIC_BASE_URL` appears in every link. It deliberately comes from
configuration rather than from the request Host header.

With `SBS_ENVIRONMENT=production`, the API refuses to start if log transport is
still enabled or the base URL does not use `https://`. Otherwise valid sign-in
links would appear in logs.

If no mail server is available, use `SBS_MAIL_TRANSPORT=none` instead of `log`;
see [Operation without a mail server](#operation-without-a-mail-server).

## Smoke test after changes

```bash
# Determine the actual host port.
api_port=$(docker compose port api 8000 | awk -F: '{print $NF}')

# Liveness: the API process responds.
curl --fail "http://127.0.0.1:${api_port}/api/v1/health"

# Readiness: Docker DNS and PostgreSQL work as well.
curl --fail "http://127.0.0.1:${api_port}/api/v1/health/ready"

# The API container can resolve the Compose service postgres.
docker compose exec -T api python -c \
  'import socket; print(socket.gethostbyname("postgres"))'

# The Web server serves exactly the documented restrictive CSP.
web_port=$(docker compose port web 8080 | awk -F: '{print $NF}')
web/scripts/check_csp_header.sh "http://127.0.0.1:${web_port}/"

# The public address must use HTTPS.
curl --fail https://sidebyside.example.com/api/v1/health

# Plaintext HTTP must not return a successful external API response.
curl --fail http://sidebyside.example.com/api/v1/health && exit 1 || true
```

The container health check accesses `127.0.0.1` internally and evaluates
`/health/ready`. This makes an API process without a functioning database path
visible as `unhealthy` without changing the separate liveness route.
