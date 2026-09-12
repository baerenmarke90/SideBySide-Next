# Secure Self-Hosted Operation

Persistent Development, release-candidate verification, Production promotion and
rollback are governed by
[`DEVELOPMENT-AND-RELEASE-ENVIRONMENTS.md`](DEVELOPMENT-AND-RELEASE-ENVIRONMENTS.md).
This document is the operator runbook for Self-Hosted instances.

## Operating modes

The repository has one tracked runtime topology: `compose.yaml`.

| | local source test | released Production |
|---|---|---|
| `SBS_ENVIRONMENT` | `development` | `production` |
| application images | local images built before Compose | published GHCR release images |
| application `build:` in Compose | none | none |
| pull policy | `never` for intentional local tags | `always` |
| supported start entry point | raw Compose after local prebuild | `scripts/self_hosted_release.py` |
| release identity | non-release local tag | release version + source SHA + OCI digest |
| mail | `log`, `smtp`, or `none` | `smtp` or `none`; never `log` |
| public origin | HTTP localhost allowed | HTTPS required |

The default development experience remains usable without SMTP or a public HTTPS domain.
Released Production is deliberately stricter.

## Local source test

Local source testing builds application images first, then runs the same canonical
Compose topology:

```bash
cp .env.example .env
# Replace POSTGRES_PASSWORD and optionally set a bootstrap token.
python3 scripts/build_self_hosted_source.py --env-file .env
docker compose --profile self-hosted --env-file .env config --quiet
docker compose --profile self-hosted --env-file .env \
  up -d --wait --wait-timeout 300
```

`.env.example` points application services at local tags and sets
`SBS_SELF_HOSTED_PULL_POLICY=never`. The source builder refuses Production and refuses
registry/digest targets. It is not a Production fallback.

For verified source acceptance, `scripts/compose_checked.py` may export one exact clean
Git snapshot, build local backend/Web images and run canonical Compose against those
local tags. That wrapper also refuses Production. It proves source; it does not create a
published release.

## Released Production files

A released Self-Hosted installation needs the release bundle files plus Docker/Compose:

- `compose.yaml`;
- `deploy/self-hosted-release.env.example`;
- `scripts/self_hosted_release.py`;
- `scripts/check_runtime_environment.py`.

The protected release workflow packages these operator files with the published release.
The target host does **not** need backend/Web source and never builds application images.

Start from the release template:

```bash
cp deploy/self-hosted-release.env.example .env
```

Set instance-specific values and select the published product version:

```dotenv
SBS_ENVIRONMENT=production
SBS_RELEASE_VERSION=0.1.0
POSTGRES_PASSWORD=<strong-production-only-value>
SBS_PUBLIC_BASE_URL=https://sidebyside.example
SBS_ALLOWED_HOSTS=["sidebyside.example"]
SBS_CURSOR_SIGNING_KEY=<stable-random-value-at-least-32-characters>
```

The default application images are the matching GHCR version tags:

```text
ghcr.io/baerenmarke90/eimir-backend:v<release-version>
ghcr.io/baerenmarke90/eimir-web:v<release-version>
```

For byte-level locking, use the digest-qualified references from the same GitHub
Release's `self-hosted-image-identity.json`:

```dotenv
SBS_SELF_HOSTED_BACKEND_IMAGE=ghcr.io/baerenmarke90/eimir-backend:v0.1.0@sha256:<digest>
SBS_SELF_HOSTED_WEB_IMAGE=ghcr.io/baerenmarke90/eimir-web:v0.1.0@sha256:<digest>
```

Both overrides must still carry the exact `SBS_RELEASE_VERSION`. Backend `migrate`,
`api`, and `worker` must share one exact backend image. Web must use the same product
version. Production requires `pull_policy=always` and permits no application `build:`
fallback.

## Mandatory released launcher

Do not start released Production with a raw `docker compose pull/up` sequence. The
supported entry point is:

```bash
python3 scripts/self_hosted_release.py --env-file .env <operation>
```

The launcher always uses repository-root `compose.yaml` and profile `self-hosted`. Before
it can pull, bootstrap or start anything, it renders the actual Compose configuration
and validates the published image identity. It rejects:

- a non-Production release env;
- process-level environment drift away from Production;
- missing `SBS_RELEASE_VERSION`;
- local, branch or `latest` application images;
- backend/Web versions that differ from `SBS_RELEASE_VERSION`;
- backend-role image divergence;
- application `build:` fallback;
- disabled Production pulling.

`deploy` additionally runs the full runtime-environment guard, including deletion
authority and other Production-critical configuration, before pull/start.

Available operations are:

```text
validate
pull
bootstrap-deletion-authority
deploy
```

A registry outage or missing release image is a deployment failure. The launcher never
falls back to a source build.

## First Production installation

### 1. Configure and pull the selected release

With `SBS_ACCOUNT_DELETION_INSTANCE_ID` still blank on a brand-new installation:

```bash
python3 scripts/self_hosted_release.py --env-file .env pull
```

This performs the image-identity gate without requiring an already-created deletion
authority.

### 2. Create the deletion authority exactly once

Only for an installation that has **never** had an Account-deletion authority:

```bash
python3 scripts/self_hosted_release.py \
  --env-file .env \
  bootstrap-deletion-authority
```

The command runs the released backend image and creates the UUID plus forward journal as
one operation. It prints:

```dotenv
SBS_ACCOUNT_DELETION_INSTANCE_ID=<stable-instance-uuid>
```

Store exactly that value in `.env` and in the protected operator configuration backup.
Do not pre-generate or replace the UUID independently of the journal.

If the installation previously had an authority and its journal is missing or damaged,
**do not bootstrap again**. Restore the newest protected journal and matching stable
instance ID according to
[`ACCOUNT-DELETION-SELF-HOSTED.md`](ACCOUNT-DELETION-SELF-HOSTED.md).

### 3. Validate and deploy

After recording `SBS_ACCOUNT_DELETION_INSTANCE_ID`:

```bash
python3 scripts/self_hosted_release.py --env-file .env validate
python3 scripts/self_hosted_release.py --env-file .env deploy
```

`deploy` validates, pulls the selected release images, runs migrations through the
canonical dependency graph, force-recreates runtime containers and waits for health.

## Runtime topology

Normal Self-Hosted ordering is:

```text
postgres -> migrate -> api/worker -> web
```

- `postgres` remains the upstream PostgreSQL image.
- `migrate` is an explicit one-shot service to avoid concurrent migration races.
- `api` and `worker` share one backend image but remain separate runtime processes.
- `web` remains a separate static/runtime boundary.
- `demo-init` is profile `demo` only and is not part of normal Self-Hosted startup.

All services use the project-specific bridge network. The application reaches PostgreSQL
through Docker DNS at `postgres:5432`; do not depend on container IDs or fixed Docker IPs.

## Production configuration requirements

Production rejects insecure runtime settings. At minimum:

- `SBS_CURSOR_SIGNING_KEY` is stable and at least 32 characters;
- `SBS_PUBLIC_BASE_URL` uses HTTPS;
- `SBS_ALLOWED_HOSTS` names concrete hosts and never `*`;
- `TRUSTED_PROXY_IPS` is the smallest real proxy IP/CIDR set;
- `SBS_ACCOUNT_DELETION_INSTANCE_ID` matches the protected forward journal;
- `SBS_MAIL_TRANSPORT` is `smtp` or `none`, never `log`.

SMTP is optional. With:

```dotenv
SBS_MAIL_TRANSPORT=none
```

password, Passkey/WebAuthn and OIDC remain available while mail-dependent Magic Link,
password recovery and email verification report that mail delivery is unavailable.

## Account deletion authority

Self-service Account deletion has a stronger recovery requirement than ordinary
point-in-time application data. Canonical Compose mounts a separate private
`deletion_journal_data` volume at:

```text
/var/lib/sidebyside/deletion-journal
```

Keep the stable instance UUID and newest validated forward journal outside ordinary
PostgreSQL/media rollback. Retain journal tombstones until all backups that could predate
those deletions have expired. API startup reconciles configured tombstones before normal
traffic so an older database restore cannot resurrect a deleted Account.

Treat `docker compose down -v` as destructive to this safety state. A normal application
recreate is safe because named volumes persist; deleting/changing the project or journal
volume requires an explicit recovery/migration decision.

## Media storage

`SBS_MEDIA_STORE=local` uses the private Compose `media_data` volume shared by API and
worker. For S3-compatible private object storage:

```dotenv
SBS_MEDIA_STORE=s3
SBS_S3_ENDPOINT=https://s3.example.com
SBS_S3_REGION=eu-central-1
SBS_S3_BUCKET=sidebyside-private
SBS_S3_ACCESS_KEY_ID=...
SBS_S3_SECRET_ACCESS_KEY=...
```

The bucket stays private. Production/Demo require HTTPS S3 endpoints. Provider
credentials should permit only the object operations needed by the media lifecycle.
Presigned URLs, signatures, storage keys and credentials must not enter logs, analytics,
support bundles or persistent client caches.

Development and Production must never share an S3 bucket or credential set.

## Backup, restore, upgrade and rollback

The binding recovery procedure is
[`SELF-HOSTED-RECOVERY.md`](SELF-HOSTED-RECOVERY.md). For LocalMediaStore,
`scripts/self_hosted_recovery.py` coordinates PostgreSQL and durable media while
configuration/secrets and the forward deletion journal remain separate protected
recovery units.

Before every Production upgrade:

1. create/verify a fresh coordinated recovery point;
2. protect the current deletion journal and operator configuration;
3. select one exact published release/image identity;
4. run the released launcher against the new `.env` selection;
5. verify migration, health and revision identity.

Application rollback selects a previous published release/image identity. It does not
imply database rollback. For incompatible schema changes use the tested forward-fix,
downgrade or coordinated restore path defined by #190/#375 and the recovery runbook.

## Initial Account registration

An empty instance accepts its first Account only with `SBS_BOOTSTRAP_TOKEN` from the
untracked environment.

1. Generate a random value of at least 32 characters.
2. Put it only in the target `.env`.
3. Deploy and complete the first registration.
4. Remove the bootstrap token and run the released launcher `deploy` again to recreate
   the affected runtime with the token absent.
5. Add further Accounts through the normal invitation flow.

The bootstrap token must not enter repository files, screenshots, support requests or
shell history.

## Reverse proxy and public exposure

The TLS reverse proxy is the only public endpoint and routes one public origin:

| Path | Internal target |
|---|---|
| `/api/` | API on `API_PORT` |
| all other paths | Web on `WEB_PORT` |

Same-host secure default:

```dotenv
SBS_BIND_IP=127.0.0.1
API_PORT=8000
WEB_PORT=8080
```

For a proxy on another private host, bind only the intended private address and set the
exact proxy source in `TRUSTED_PROXY_IPS`. Never use `*` for trusted proxies or Production
allowed hosts.

The `/api/` route must go directly to the API rather than through Web Nginx, otherwise
the trusted TLS proxy hop is lost for `X-Forwarded-*` handling.

## Post-deploy verification

The release smoke helper verifies Web health/revision, API/database readiness and API
revision:

```bash
python3 scripts/deployment_smoke.py \
  --base-url https://sidebyside.example \
  --expected-revision <release-source-sha>
```

With `SBS_SMOKE_EMAIL` and `SBS_SMOKE_PASSWORD`, it also performs a non-destructive
password sign-in and membership read using an operator/fictional smoke Account.

After a successful released deployment, raw Compose is acceptable for diagnosis only,
for example:

```bash
docker compose --profile self-hosted --env-file .env ps
docker compose --profile self-hosted --env-file .env logs --tail=100 migrate api worker web
```

Do not replace the released launcher with raw Compose for Production pull, bootstrap or
startup. A healthy component serving a different revision than the release manifest is a
failed promotion.
