# Secure Self-Hosted Operation

Persistent Development, release-candidate verification, Production promotion, and
rollback are governed by
[`DEVELOPMENT-AND-RELEASE-ENVIRONMENTS.md`](DEVELOPMENT-AND-RELEASE-ENVIRONMENTS.md).
This document covers secure instance operation; it must not be used to bypass the
Development-before-Production promotion gates defined there.

## Operating modes

The bundled stack supports a convenient local source-test mode and a hardened released
Production mode. Both use the **same tracked `compose.yaml`**. There is no second
Production Compose topology.

| | local source test | released Production |
|---|---|---|
| `SBS_ENVIRONMENT` | `development` | `production` |
| application images | local images built by `scripts/build_self_hosted_source.py` | versioned GHCR release images |
| Compose application `build:` | none | none |
| pull policy | `never` for the intentionally local tags | `always` |
| cursor signing key | local fallback allowed | required, at least 32 characters |
| Account deletion authority | optional until self-delete is exercised | stable instance UUID + protected forward journal required before API traffic is served |
| outgoing mail | `log` allowed | `smtp` or `none`, never `log` |
| `SBS_PUBLIC_BASE_URL` | HTTP localhost allowed | HTTPS required |
| `/docs` | available | disabled |
| release identity | explicitly non-release local image | GitHub Release + source SHA + published OCI identity |

The default is test mode by design ([ADR 0002](decisions/0002-self-hosted-first-start-mode.md)).
Initial evaluation must work without an SMTP account or public HTTPS domain. Web and API
bind to loopback by default.

## Local source test

Copy the development template, build the two local application images, then start the
single canonical Compose topology:

```bash
cp .env.example .env
# Replace at least POSTGRES_PASSWORD with a strong random value.
# Set SBS_BOOTSTRAP_TOKEN to a separate random value with at least 32 characters.
python3 scripts/build_self_hosted_source.py --env-file .env
docker compose --profile self-hosted --env-file .env config --quiet
docker compose --profile self-hosted --env-file .env \
  up -d --wait --wait-timeout 300
```

`.env.example` points the canonical Compose services at local tags and sets
`SBS_SELF_HOSTED_PULL_POLICY=never`, so Docker will not accidentally replace those test
images from a registry. `scripts/build_self_hosted_source.py` is a development/CI tool;
it is not a released Production fallback.

`API_PORT=8000` and `WEB_PORT=8080` are defaults only. If either host port is already
occupied, select a free port in `.env` before startup, for example:

```dotenv
API_PORT=8010
WEB_PORT=8081
SBS_PUBLIC_BASE_URL=http://localhost:8081
```

The published ports must remain bound to the intended interface. For the default local
setup:

```bash
docker compose --profile self-hosted --env-file .env port api 8000
docker compose --profile self-hosted --env-file .env port web 8080
```

Both should report `127.0.0.1`. An unexpected `0.0.0.0`, `::`, or external address is
not an acceptable default.

## Verified source testing

`scripts/compose_checked.py` remains available for CI and exceptional verified-source
acceptance. It is **not** the released Production install path.

The wrapper:

- requires a clean checkout;
- can require an exact 40-character source SHA;
- exports `compose.yaml`, backend and Web from that exact committed tree;
- builds local backend/Web images from the exported source;
- runs the exported canonical Compose file against those local tags with pull disabled.

Example:

```bash
CANDIDATE=<40-character-approved-commit-sha>
git checkout "$CANDIDATE"
python3 scripts/compose_checked.py \
  --expected-revision "$CANDIDATE" \
  up -d --force-recreate --wait --wait-timeout 300
```

This proves a checkout/source candidate. It does not turn a source checkout into a
published release.

## Released Production installation

Released Self-Hosted consumes the OCI images published by the protected #519/#827
release workflow. The target host does **not** compile backend or Web source.

Start from the release template:

```bash
cp deploy/self-hosted-release.env.example .env
```

Set at least the Production database password, public origin/hosts, cursor signing key,
mail choice and the other instance-specific values. Select the exact product release:

```dotenv
SBS_RELEASE_VERSION=0.1.0
```

The default references are:

```text
ghcr.io/baerenmarke90/eimir-backend:v<release-version>
ghcr.io/baerenmarke90/eimir-web:v<release-version>
```

For a fully locked deployment, use the digest-qualified references from the GitHub
Release asset `self-hosted-image-identity.json`:

```dotenv
SBS_SELF_HOSTED_BACKEND_IMAGE=ghcr.io/baerenmarke90/eimir-backend:v0.1.0@sha256:<digest>
SBS_SELF_HOSTED_WEB_IMAGE=ghcr.io/baerenmarke90/eimir-web:v0.1.0@sha256:<digest>
```

Do not set `SBS_SELF_HOSTED_PULL_POLICY=never` in Production. The Production runtime
contract requires `pull_policy=always`, no application `build:` blocks, one exact backend
image shared by `migrate`, `api`, and `worker`, and one matching-version Web image.

Validate and start:

```bash
docker compose --profile self-hosted --env-file .env config --quiet
docker compose --profile self-hosted --env-file .env pull
docker compose --profile self-hosted --env-file .env \
  up -d --wait --wait-timeout 300
```

A registry outage or missing release image is a deployment failure. Production must not
silently build whatever source happens to be present on the target host.

## Compose network and startup

`postgres`, `migrate`, `api`, `worker`, and `web` use the same project-specific bridge
network. The database URL deliberately resolves `postgres:5432` through Docker DNS
rather than using container IDs, fixed Docker addresses, or published host ports.

Normal Self-Hosted startup ordering is:

```text
postgres -> migrate -> api/worker -> web
```

`migrate` must complete successfully before API and worker start. Web waits for API
readiness.

`demo-init` is deliberately **not** part of normal Self-Hosted startup. It is an
explicit Demo-only one-shot lifecycle service under profile `demo`. Public Demo
operations intentionally activate/run that lifecycle; ordinary Self-Hosted installations
do not seed Demo state.

Useful network checks:

```bash
docker compose --profile self-hosted --env-file .env exec -T api python -c \
  'import socket; print(socket.gethostbyname("postgres"))'

api_id=$(docker compose --profile self-hosted --env-file .env ps -q api)
docker inspect "$api_id" --format '{{json .NetworkSettings.Networks}}'
```

A running API container with no attached Docker network is not ready.

SideBySide exposes separate health signals:

- `/api/v1/health`: API process liveness;
- `/api/v1/health/ready`: API plus database readiness;
- `/healthz`: Web server liveness;
- `/.well-known/sidebyside-revision`: Web build identity.

The API health responses include:

```text
X-SideBySide-Revision: <backend-build-revision>
```

A released deployment is valid only when the Web revision endpoint and API header both
match the release manifest's source revision. This prevents a partially recreated stack
from silently pairing stale Web and backend images.

## Production configuration

Start from `deploy/self-hosted-release.env.example`. Configure ordinary Production
values first, but leave `SBS_ACCOUNT_DELETION_INSTANCE_ID` unset until the deletion
authority has been provisioned by the explicit bootstrap command below:

```dotenv
SBS_ENVIRONMENT=production
SBS_CURSOR_SIGNING_KEY=...        # openssl rand -base64 48
SBS_ACCOUNT_DELETION_INSTANCE_ID=
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

If this installation has **never had an Account-deletion authority**, create the stable
UUID and empty forward journal together exactly once:

```bash
docker compose --profile self-hosted --env-file .env run --rm --no-deps api \
  python -m sidebyside.identity.deletion_bootstrap \
  --confirm-new-installation
```

The command prints:

```dotenv
SBS_ACCOUNT_DELETION_INSTANCE_ID=<stable-instance-uuid>
```

Store that exact emitted value in `.env` and the protected operator configuration backup
before normal Production startup. Do not pre-generate or replace the UUID independently
of the journal.

If this installation already had an authority and its journal is now missing, corrupt,
or unavailable, **do not run bootstrap**. Recover the newest protected journal and its
matching stable instance ID as described in
[`ACCOUNT-DELETION-SELF-HOSTED.md`](ACCOUNT-DELETION-SELF-HOSTED.md).

Production refuses unsafe configuration such as a missing cursor signing key, plaintext
public base URL, or `SBS_MAIL_TRANSPORT=log`. Production also refuses normal API traffic
until the configured Account-deletion authority is present, readable, and matches
`SBS_ACCOUNT_DELETION_INSTANCE_ID`.

## Account deletion authority

Self-service Account deletion has a stronger recovery requirement than ordinary
point-in-time application data. Canonical Compose gives the API a separate private
`deletion_journal_data` volume mounted at:

```text
/var/lib/sidebyside/deletion-journal
```

The stable instance UUID in `SBS_ACCOUNT_DELETION_INSTANCE_ID` belongs to the operator
configuration backup. It is emitted by the one-time
`sidebyside.identity.deletion_bootstrap` command when that command creates the matching
forward journal. Keep both authority artifacts unchanged across application upgrades and
database/media restores. Do not reuse the Production UUID or journal for Development or
Demo.

The forward journal must not be rolled back together with PostgreSQL or media. Protect
the newest validated journal independently and retain it until every pre-deletion
backup represented by its tombstones has expired. API startup replays configured
tombstones before normal traffic so a crash after journal fsync but before the database
fail-closed commit cannot reopen an Account.

Treat `docker compose down -v` as destructive to this safety state. Recreating an API
container is safe because named volumes persist; deleting/changing the Compose project or
journal volume requires an explicit migration/recovery decision.

The full operator contract, including bootstrap, upgrades that first introduce the
authority, and post-restore replay, is in
[`ACCOUNT-DELETION-SELF-HOSTED.md`](ACCOUNT-DELETION-SELF-HOSTED.md).

## Operation without a mail server

SMTP is not a startup requirement. With:

```dotenv
SBS_MAIL_TRANSPORT=none
```

the instance remains usable through password, Passkey/WebAuthn, and OIDC, but
mail-dependent Magic Link, password recovery, and address verification return a clear
unavailable response instead of pretending to send a message. An accepted Account
deletion also continues without rollback when its best-effort confirmation mail cannot
be sent.

`log` transport is for local testing only. It would put valid one-time credentials in
logs and is therefore rejected in Production.

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

The bucket must remain private. Presigned PUT/GET capabilities use the exact configured
origin. Production/Demo require HTTPS for S3 endpoints; Development may use HTTP for
local fixtures such as MinIO. Provider credentials need only the object operations
required by the media lifecycle.

Uploads use short-lived server-signed PUT capabilities for the generated object key. A
provider upload does not make an Attachment `READY`; server-side finalization and
validation remain authoritative. Reads receive short-lived server-authorized GET
capabilities only after normal membership/parent checks.

Presigned URLs, signatures, storage keys, and credentials must not enter logs,
analytics, support bundles, or persistent client caches.

Development and Production must never share an S3 bucket/credential set. Use
`scripts/check_environment_isolation.py` before promotion when environment files are
available to the operator.

## Backup, restore, upgrade, and rollback

The binding recovery contract and copy-paste operator procedure are in
[`SELF-HOSTED-RECOVERY.md`](SELF-HOSTED-RECOVERY.md). For the default
`LocalMediaStore`, `scripts/self_hosted_recovery.py` creates/restores one coordinated
PostgreSQL/durable-media archive while configuration/secrets and the forward
Account-deletion journal remain independently protected recovery units.

Production upgrades require:

1. a fresh coordinated recovery point;
2. current protected deletion-journal state;
3. selection of the exact new published release/image identity;
4. migration-first startup;
5. post-start health and revision checks.

Application rollback selects the previous published release/image identity. It does
**not** imply database rollback. Follow #190/#375 and the recovery runbook for schema
compatibility, forward-fix, downgrade, or restore decisions.

A database dump without matching media, deletion authority, and configuration/secret
recovery material is not a complete SideBySide recovery plan.

## One-time initial registration

An empty instance accepts its first account only with `SBS_BOOTSTRAP_TOKEN` from the
untracked environment. The value is neither persisted as product data nor logged by
SideBySide.

1. Generate a random secret with at least 32 characters.
2. Put it only in the target environment as `SBS_BOOTSTRAP_TOKEN`.
3. Start the stack and perform the first registration.
4. Remove the bootstrap token and recreate the API container.
5. Create additional accounts through the normal invitation flow.

The bootstrap token must not enter repository files, shell history, screenshots, or
support requests. Development and Production use different bootstrap secrets.

## Reverse proxy and public exposure

The TLS reverse proxy is the only public endpoint. On the same public origin it routes:

| Path | Internal target |
|---|---|
| `/api/` | SideBySide API on `API_PORT` |
| all other paths | SideBySide Web on `WEB_PORT` |

The `/api/` route goes directly to the API in Production. It must not first pass through
the Web Nginx container, because the configured trusted TLS proxy is the authority for
`X-Forwarded-*` handling.

### Reverse proxy on the same host

```dotenv
SBS_BIND_IP=127.0.0.1
API_PORT=8000
WEB_PORT=8080
```

### Reverse proxy on another private host

Bind only to the intended private address:

```dotenv
SBS_BIND_IP=192.168.10.20
API_PORT=8000
WEB_PORT=8099
SBS_PUBLIC_BASE_URL=https://sidebyside.example
SBS_ALLOWED_HOSTS=["sidebyside.example","localhost","127.0.0.1"]
TRUSTED_PROXY_IPS=192.168.10.30
```

Never use `*` for trusted proxies or Production allowed hosts. Client-supplied Forwarded
headers are not independently trusted.

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

`SBS_PUBLIC_BASE_URL` constructs application links from configuration rather than an
untrusted request host.

## Smoke verification

The release smoke helper is the preferred post-deploy check:

```bash
python3 scripts/deployment_smoke.py \
  --base-url https://sidebyside.example \
  --expected-revision <exact-release-source-sha>
```

It verifies Web health, Web build identity, API/database readiness, and API build
identity. With `SBS_SMOKE_EMAIL` and `SBS_SMOKE_PASSWORD`, it also performs a password
sign-in and authenticated membership read without creating product content.

For host-level diagnosis:

```bash
api_port=$(docker compose --profile self-hosted --env-file .env port api 8000 | awk -F: '{print $NF}')
web_port=$(docker compose --profile self-hosted --env-file .env port web 8080 | awk -F: '{print $NF}')

curl --fail "http://127.0.0.1:${api_port}/api/v1/health"
curl --fail "http://127.0.0.1:${api_port}/api/v1/health/ready"
curl --fail "http://127.0.0.1:${web_port}/healthz"
curl --fail "http://127.0.0.1:${web_port}/.well-known/sidebyside-revision"

docker compose --profile self-hosted --env-file .env exec -T api python -c \
  'import socket; print(socket.gethostbyname("postgres"))'
```

A health check proves availability; the revision checks prove that the intended release
components are actually serving traffic. Production is not accepted until both are
true.
