# Secure Self-Hosted Operation

Persistent Development, release-candidate verification, Production promotion, and
rollback are governed by
[`DEVELOPMENT-AND-RELEASE-ENVIRONMENTS.md`](DEVELOPMENT-AND-RELEASE-ENVIRONMENTS.md).
This document covers secure instance operation; it must not be used to bypass the
Development-before-Production promotion gates defined there.

## Operating modes

The bundled stack supports a convenient local test mode and a hardened Production
mode:

| | local test mode | Production mode |
|---|---|---|
| `SBS_ENVIRONMENT` | `development` (default) | `production` |
| cursor signing key | local fallback | required, at least 32 characters |
| outgoing mail | `log` allowed | `smtp` or `none`, never `log` |
| `SBS_PUBLIC_BASE_URL` | HTTP localhost allowed | HTTPS required |
| HTTPS/host enforcement | off | on |
| `/docs` | available | disabled |
| deployment revision | explicitly unverified with raw Compose | exact verified commit required |

The default is test mode by design ([ADR 0002](decisions/0002-self-hosted-first-start-mode.md)).
Initial evaluation must work without an SMTP account or public HTTPS domain. Web
and API bind to loopback by default.

## Local test

```bash
cp .env.example .env
# Replace at least POSTGRES_PASSWORD with a strong random value.
# Set SBS_BOOTSTRAP_TOKEN to a separate random value with at least 32 characters.
docker compose config --quiet
docker compose up -d --wait --wait-timeout 300
```

`API_PORT=8000` and `WEB_PORT=8080` are defaults only. If either host port is
already occupied, select a free port in `.env` before startup, for example:

```dotenv
API_PORT=8010
WEB_PORT=8081
SBS_PUBLIC_BASE_URL=http://localhost:8081
```

The published ports must remain bound to the intended interface. For the default
local setup:

```bash
docker compose port api 8000
docker compose port web 8080
```

Both should report `127.0.0.1`. An unexpected `0.0.0.0`, `::`, or external
address is not an acceptable default.

Raw `docker compose` intentionally builds both application images with the
identity:

```text
unverified-local-checkout
```

That identity is useful for local diagnosis but is **not** a release proof. It
cannot be changed from `.env` to impersonate an approved commit.

## Verified complete-checkout deployment

A release candidate or Production deployment from a complete repository checkout
must use `scripts/compose_checked.py`, not raw `docker compose`.

The wrapper derives the revision from Git, rejects a dirty checkout, and can
require the checkout to match an expected immutable commit before Compose runs.
It injects that exact revision into both backend and Web builds.

Example:

```bash
CANDIDATE=<40-character-approved-commit-sha>
git checkout "$CANDIDATE"
python3 scripts/compose_checked.py \
  --expected-revision "$CANDIDATE" \
  up -d --build --force-recreate --wait --wait-timeout 300
```

Do not substitute a manually supplied revision environment variable. The release
identity must come from the source that is actually being built.

Arcane uses the equivalent remote-source invariant instead: see `ARCANE.md`.

## Compose network and readiness

`postgres`, `migrate`, `demo-init`, `api`, `worker`, and `web` use the same
project-specific bridge network. The database URL deliberately resolves
`postgres:5432` through Docker DNS rather than using container IDs, fixed Docker
addresses, or published host ports.

Startup ordering is:

```text
postgres -> migrate -> demo-init(no-op outside Demo) -> api/worker -> web
```

`migrate` must complete successfully before API and worker start. Web waits for
API readiness.

Useful network checks:

```bash
docker compose exec -T api python -c \
  'import socket; print(socket.gethostbyname("postgres"))'

api_id=$(docker compose ps -q api)
docker inspect "$api_id" --format '{{json .NetworkSettings.Networks}}'
```

A running API container with no attached Docker network is not ready.

SideBySide exposes separate health signals:

- `/api/v1/health`: API process liveness;
- `/api/v1/health/ready`: API plus database readiness;
- `/healthz`: Web server liveness;
- `/.well-known/sidebyside-revision`: immutable Web build identity.

The API health responses include:

```text
X-SideBySide-Revision: <backend-build-revision>
```

A release is valid only when the Web revision endpoint and the API header both
match the expected commit. This prevents a partially recreated stack from
silently pairing a stale Web image with a newer backend.

## Production configuration

Before the first Production startup, configure at least:

```dotenv
SBS_ENVIRONMENT=production
SBS_CURSOR_SIGNING_KEY=...        # openssl rand -base64 48
SBS_PUBLIC_BASE_URL=https://your-domain.example
SBS_ALLOWED_HOSTS=["your-domain.example"]
TRUSTED_PROXY_IPS=...             # smallest real reverse-proxy IP/CIDR

# With mail delivery:
SBS_MAIL_TRANSPORT=smtp
SBS_MAIL_FROM=no-reply@your-domain.example
SBS_SMTP_HOST=smtp.your-domain.example

# Or without mail delivery:
# SBS_MAIL_TRANSPORT=none
```

Production refuses unsafe configuration such as a missing cursor signing key, a
plaintext public base URL, or `SBS_MAIL_TRANSPORT=log`. These are secure-default
startup failures and must not be bypassed.

The exact source revision must first pass the persistent Development gates in
`DEVELOPMENT-AND-RELEASE-ENVIRONMENTS.md`. For complete-checkout Production,
perform the actual deploy with `scripts/compose_checked.py`; for Arcane, pin
`SBS_SOURCE_REF` to the exact approved commit SHA.

## Operation without a mail server

SMTP is not a startup requirement. With:

```dotenv
SBS_MAIL_TRANSPORT=none
```

the instance remains usable through password, Passkey/WebAuthn, and OIDC, but
mail-dependent Magic Link, password recovery, and address verification return a
clear unavailable response instead of pretending to send a message.

`log` transport is for local testing only. It would put valid one-time
credentials in logs and is therefore rejected in Production.

## Media storage

`SBS_MEDIA_STORE=local` is the default. API and worker share the private Compose
`media_data` volume; filesystem paths are not exposed to clients.

For S3-compatible private object storage:

```dotenv
SBS_MEDIA_STORE=s3
SBS_S3_ENDPOINT=https://s3.example.com
SBS_S3_REGION=eu-central-1
SBS_S3_BUCKET=sidebyside-private
SBS_S3_ACCESS_KEY_ID=...
SBS_S3_SECRET_ACCESS_KEY=...
# Optional temporary credentials only:
# SBS_S3_SESSION_TOKEN=...
```

The bucket must remain private. Production traffic over untrusted networks uses
HTTPS. Provider credentials need only the object operations required by the
SideBySide media lifecycle; no public bucket policy or static website exposure is
required.

Uploads use short-lived server-signed PUT capabilities for the exact generated
object key. A provider upload does not make an Attachment `READY`; server-side
finalization and validation remain authoritative. Reads receive short-lived
server-authorized GET capabilities only after normal membership/parent checks.

Presigned URLs, signatures, storage keys, and credentials must not enter logs,
analytics, support bundles, or persistent client caches.

For browser direct upload/read, configure a narrow CORS rule for the concrete
SideBySide origin. Compose derives the Web CSP `connect-src` allowance from the
exact `SBS_S3_ENDPOINT`; wildcard origins, scheme-wide allowances, paths, and
credentials are rejected.

Development and Production must never share an S3 bucket/credential set. Use
`scripts/check_environment_isolation.py` before promotion when environment files
are available to the operator.

## One-time initial registration

An empty instance accepts its first account only with `SBS_BOOTSTRAP_TOKEN` from
the untracked environment. The value is neither persisted as product data nor
logged by SideBySide.

1. Generate a random secret with at least 32 characters.
2. Put it only in the target environment as `SBS_BOOTSTRAP_TOKEN`.
3. Start the stack and perform the first registration.
4. Remove the bootstrap token and recreate the API container.
5. Create additional accounts through the normal invitation flow.

The bootstrap token must not enter repository files, shell history, screenshots,
or support requests. Development and Production use different bootstrap secrets.

## Reverse proxy and public exposure

The TLS reverse proxy is the only public endpoint. On the same public origin it
routes:

| Path | Internal target |
|---|---|
| `/api/` | SideBySide API on `API_PORT` |
| all other paths | SideBySide Web on `WEB_PORT` |

The `/api/` route goes directly to the API in Production. It must not first pass
through the Web Nginx container, because the configured trusted TLS proxy is the
authority for `X-Forwarded-*` handling.

### Reverse proxy on the same host

The secure default is sufficient:

```dotenv
SBS_BIND_IP=127.0.0.1
API_PORT=8000
WEB_PORT=8080
```

### Reverse proxy on another private host

Bind only to the intended private address, not unnecessarily to all interfaces:

```dotenv
SBS_BIND_IP=192.168.10.20
API_PORT=8000
WEB_PORT=8099
```

Then configure the public origin and exact proxy source:

```dotenv
SBS_PUBLIC_BASE_URL=https://sidebyside.example
SBS_ALLOWED_HOSTS=["sidebyside.example","localhost","127.0.0.1"]
TRUSTED_PROXY_IPS=192.168.10.30
```

Never use `*` for trusted proxies or Production allowed hosts. Client-supplied
Forwarded headers are not independently trusted.

After proxy configuration:

```bash
curl --fail https://sidebyside.example/
curl --fail https://sidebyside.example/.well-known/sidebyside-revision
curl --fail https://sidebyside.example/api/v1/health/ready
web/scripts/check_csp_header.sh https://sidebyside.example/
```

## Outgoing email

For actual delivery configure a Production-specific SMTP account:

```dotenv
SBS_MAIL_TRANSPORT=smtp
SBS_MAIL_FROM=no-reply@your-domain.example
SBS_SMTP_HOST=smtp.your-domain.example
SBS_SMTP_PORT=587
SBS_SMTP_USERNAME=...
SBS_SMTP_PASSWORD=...
```

`SBS_PUBLIC_BASE_URL` is used to construct application links. It comes from
configuration rather than from an untrusted request host.

## Smoke verification

The release smoke helper is the preferred post-deploy check:

```bash
python3 scripts/deployment_smoke.py \
  --base-url https://sidebyside.example \
  --expected-revision <exact-commit-sha>
```

It verifies Web health, Web build identity, API/database readiness, and the API
build identity. With `SBS_SMOKE_EMAIL` and `SBS_SMOKE_PASSWORD`, it also performs
a password sign-in and authenticated membership read without creating product
content.

For host-level diagnosis, these checks remain useful:

```bash
api_port=$(docker compose port api 8000 | awk -F: '{print $NF}')
web_port=$(docker compose port web 8080 | awk -F: '{print $NF}')

curl --fail "http://127.0.0.1:${api_port}/api/v1/health"
curl --fail "http://127.0.0.1:${api_port}/api/v1/health/ready"
curl --fail "http://127.0.0.1:${web_port}/healthz"
curl --fail "http://127.0.0.1:${web_port}/.well-known/sidebyside-revision"

docker compose exec -T api python -c \
  'import socket; print(socket.gethostbyname("postgres"))'
```

A health check proves availability; the revision checks prove that the intended
application components are actually the ones serving traffic. Production is not
accepted until both are true.
