# Arcane Deployment

These notes supplement `SELF-HOSTING.md` for installations where Arcane manages the
SideBySide stack and a separate TLS reverse proxy sits in front of it.

For persistent Development, release-candidate verification, Production promotion and
rollback, the authoritative workflow is
[`DEVELOPMENT-AND-RELEASE-ENVIRONMENTS.md`](DEVELOPMENT-AND-RELEASE-ENVIRONMENTS.md).
This document defines Arcane mechanics; it does not create a competing release policy.

## One Compose file

SideBySide supports exactly one tracked Docker Compose manifest: repository-root
`compose.yaml`.

Arcane uses that same manifest and the `self-hosted` profile. The distinction between
Development and released Production is **image origin**, not a second topology:

- Development may build local images from Git with
  `scripts/build_self_hosted_source.py` and use local tags with pull disabled;
- released Production consumes the published versioned/digest-qualified GHCR images and
  keeps pull enabled;
- services, volumes, networks, health checks and startup dependencies remain one
  canonical contract.

Normal Self-Hosted ordering is:

```text
postgres -> migrate -> api/worker -> web
```

`demo-init` is an explicit Demo-only lifecycle service and is not part of normal
Self-Hosted startup.

## Persistent Development in Arcane

Create a dedicated Arcane project, for example `sidebyside-development`, separate from
any Production or Demo project. Start from:

```text
deploy/persistent-development.env.example
```

It uses local Development image tags and remote Git source contexts. For ordinary
integration on `main`:

```dotenv
COMPOSE_PROFILES=self-hosted
SBS_SELF_HOSTED_BACKEND_IMAGE=sidebyside-backend:source-development
SBS_SELF_HOSTED_WEB_IMAGE=sidebyside-web:source-development
SBS_SELF_HOSTED_PULL_POLICY=never
SBS_BACKEND_BUILD_CONTEXT=https://github.com/baerenmarke90/SideBySide-Next.git#main:backend
SBS_WEB_BUILD_CONTEXT=https://github.com/baerenmarke90/SideBySide-Next.git#main:web
SBS_BUILD_REVISION=main
```

The build workspace/runner executes:

```bash
python3 scripts/build_self_hosted_source.py \
  --env-file deploy/persistent-development.env.example
```

Then Arcane starts/recreates canonical `compose.yaml`. The helper builds backend/Web
images only; it does not create another Compose manifest.

Before release acceptance, replace `main` in both source contexts and
`SBS_BUILD_REVISION` with the exact candidate commit SHA, rebuild the Development images
and recreate the stack. API/Web source revision endpoints must both equal that SHA.

Development remains a separate project with unique database credentials, volumes/media,
cursor signing key, bootstrap/admin state, callbacks and provider credentials. Do not
import the Production environment wholesale.

## Released Production in Arcane

Released Production must **not** use remote Git build contexts as its deployment
identity and must not build backend/Web source on the Docker host.

Start from:

```text
deploy/self-hosted-release.env.example
```

Select the published product release:

```dotenv
COMPOSE_PROFILES=self-hosted
SBS_ENVIRONMENT=production
SBS_RELEASE_VERSION=X.Y.Z
```

The canonical manifest then pulls:

```text
ghcr.io/baerenmarke90/eimir-backend:vX.Y.Z
ghcr.io/baerenmarke90/eimir-web:vX.Y.Z
```

For exact transport locking, use the digest-qualified references from the release asset
`self-hosted-image-identity.json`:

```dotenv
SBS_SELF_HOSTED_BACKEND_IMAGE=ghcr.io/baerenmarke90/eimir-backend:vX.Y.Z@sha256:<digest>
SBS_SELF_HOSTED_WEB_IMAGE=ghcr.io/baerenmarke90/eimir-web:vX.Y.Z@sha256:<digest>
```

Production keeps `SBS_SELF_HOSTED_PULL_POLICY=always` (the Compose default). A missing
registry image is a deployment failure, not permission to compile local source.

After Arcane recreates the stack, run `scripts/deployment_smoke.py` against the public
origin with the exact source SHA from the published release manifest.

## Account-deletion authority bootstrap

Arcane has no separate bootstrap manifest. It uses root `compose.yaml`, profile
`self-hosted`, and the named `deletion_journal_data` volume.

For a project that has **never had an Account-deletion authority**, leave
`SBS_ACCOUNT_DELETION_INSTANCE_ID` unset and run exactly one bootstrap against that
project's API service:

```bash
docker compose --profile self-hosted --env-file .env run --rm --no-deps api \
  python -m sidebyside.identity.deletion_bootstrap \
  --confirm-new-installation
```

The command creates the forward journal and prints the stable
`SBS_ACCOUNT_DELETION_INSTANCE_ID`. Store that exact emitted value in the Arcane project
environment and protected operator configuration backup, then force-recreate the
affected containers. Never generate the UUID independently.

Run the command with the **same Arcane project environment** that owns the Production
volumes/images. If Arcane stores variables outside `.env`, use its one-off/exec facility
or otherwise supply those exact variables. Do not accidentally use a different
`COMPOSE_PROJECT_NAME` or Development image identity.

If an established project's journal is missing/corrupt, this is recovery failure, not a
bootstrap opportunity. Do not clear the instance ID or initialize a replacement journal;
follow `ACCOUNT-DELETION-SELF-HOSTED.md` and recover the newest protected journal.

## Runtime environment and container recreation

Compose interpolation precedence matters: an explicitly defined process variable,
including an empty value, overrides `.env`. Arcane project variables must therefore not
contain stale/blank duplicates of non-empty runtime settings.

`SBS_ACCOUNT_DELETION_INSTANCE_ID` is recovery-critical. A blank process override is a
deployment failure; do not weaken API startup or re-bootstrap the deletion journal.

The shared guard verifies rendered configuration from a checkout containing the same
canonical Compose file:

```bash
ARCANE_PROJECT_DIR=/path/to/arcane-project
ARCANE_COMPOSE_PROJECT=sidebyside-production

python3 scripts/check_runtime_environment.py \
  --env-file "$ARCANE_PROJECT_DIR/.env" \
  --compose-file "$ARCANE_PROJECT_DIR/compose.yaml" \
  --profile self-hosted \
  --project-name "$ARCANE_COMPOSE_PROJECT"
```

For Production it also rejects unsafe application image identity such as `latest`,
branch/local source tags, backend-role divergence, backend/Web release-version mismatch,
application `build:` fallback, or disabled pulling.

After changing runtime environment settings, **force-recreate affected containers**.
Restart alone is insufficient because Docker fixes container environment at creation.
Do not enable any option that deletes named volumes; `deletion_journal_data`,
`postgres_data`, and `media_data` must survive ordinary configuration updates.

After recreation, include runtime inspection:

```bash
python3 scripts/check_runtime_environment.py \
  --env-file "$ARCANE_PROJECT_DIR/.env" \
  --compose-file "$ARCANE_PROJECT_DIR/compose.yaml" \
  --profile self-hosted \
  --project-name "$ARCANE_COMPOSE_PROJECT" \
  --check-running
```

The guard reports only variable/service names, not compared values.

If a full checkout is unavailable on the host, a minimum deletion-authority incident
check may compare `.env`, rendered Compose and running API without printing the UUID:

```bash
cd /path/to/arcane-project

expected=$(grep '^SBS_ACCOUNT_DELETION_INSTANCE_ID=' .env | cut -d= -f2-)
rendered=$(docker compose --profile self-hosted --env-file .env config --format json \
  | python3 -c 'import json,sys; print(json.load(sys.stdin)["services"]["api"]["environment"].get("SBS_ACCOUNT_DELETION_INSTANCE_ID", ""))')
container=$(docker compose --profile self-hosted --env-file .env ps -aq api | head -n1)
running=$(docker inspect "$container" --format '{{range .Config.Env}}{{println .}}{{end}}' \
  | sed -n 's/^SBS_ACCOUNT_DELETION_INSTANCE_ID=//p')

test -n "$expected" && test "$expected" = "$rendered" && test "$rendered" = "$running"
```

Interpret failures as follows:

- `.env` differs from rendered Compose: inspect Arcane/process overrides;
- rendered Compose differs from the container: correct environment and force-recreate;
- journal validation still fails with matching values: stop and follow the deletion
  recovery procedure; never synthesize a replacement authority.

## Public and private repositories

Remote Git contexts used for **Development source builds** may require BuildKit/Arcane Git
authentication for private repositories. Do not embed credentials/tokens in Git URLs,
`compose.yaml`, or checked-in env templates.

Production image pulling uses the released package identity instead of Git contexts. If
registry authentication is needed, configure it in the Docker/Arcane registry credential
boundary; do not add registry tokens to Compose or release evidence.

Do not create another Compose manifest as an authentication or deployment workaround.

## Reverse proxy architecture

The reverse proxy is the only public TLS endpoint. On one public origin it routes:

| Path | Internal target |
|---|---|
| `/api/` | SideBySide API on `API_PORT` |
| all other paths | SideBySide Web on `WEB_PORT` |

The `/api/` route goes directly to the API. In Production it must not first pass through
the Web Nginx container because that would lose the trusted TLS proxy hop for
`X-Forwarded-Proto`.

### Same host

```dotenv
SBS_BIND_IP=127.0.0.1
API_PORT=8000
WEB_PORT=8080
```

### Separate private reverse-proxy host

```dotenv
SBS_BIND_IP=192.168.10.20
API_PORT=8000
WEB_PORT=8099
SBS_ENVIRONMENT=production
SBS_PUBLIC_BASE_URL=https://sidebyside.example
SBS_ALLOWED_HOSTS=["sidebyside.example","localhost","127.0.0.1"]
TRUSTED_PROXY_IPS=192.168.10.30,192.168.10.31
```

`TRUSTED_PROXY_IPS` contains only the addresses/smallest CIDR from which the reverse
proxy reaches the API. Never use `*`.

## Web Space context

The Web client does not accept an operator-provided Space UUID. After authentication it
discovers active Memberships through the API and uses only a server-authorized Space.
Arcane needs no Space-specific Web build argument or environment value.

## Post-deployment verification

From the reverse-proxy host or same private network:

```bash
curl --fail http://<docker-host>:<WEB_PORT>/healthz
curl --fail http://<docker-host>:<WEB_PORT>/.well-known/sidebyside-revision
curl --fail --include https://sidebyside.example/api/v1/health/ready
```

For release acceptance prefer:

```bash
python3 scripts/deployment_smoke.py \
  --base-url https://sidebyside.example \
  --expected-revision <published-release-source-sha>
```

Both Web and API must report the exact source SHA bound by the selected published
release.
