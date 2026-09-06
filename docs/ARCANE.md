# Arcane Deployment

These notes supplement `SELF-HOSTING.md` for installations where Arcane manages
the SideBySide stack and a separate TLS reverse proxy sits in front of it.

For persistent Development, release-candidate verification, Production promotion,
and rollback, the authoritative workflow is
[`DEVELOPMENT-AND-RELEASE-ENVIRONMENTS.md`](DEVELOPMENT-AND-RELEASE-ENVIRONMENTS.md).
This document defines Arcane mechanics; it does not create a competing release
policy.

## One Compose file

SideBySide supports exactly one Docker Compose manifest: repository-root
`compose.yaml`.

Arcane uses the same `self-hosted` profile as a complete repository checkout.
The only source-specific difference is the build context:

- complete checkout: defaults to local `./backend` and `./web`;
- Arcane / remote workspace: set Git/BuildKit URLs through
  `SBS_BACKEND_BUILD_CONTEXT` and `SBS_WEB_BUILD_CONTEXT`.

This keeps services, volumes, networks, runtime settings, health checks and
startup dependencies in one contract instead of duplicating the stack.

## Configure Arcane

1. Create a dedicated SideBySide project in Arcane.
2. Select repository-root `compose.yaml` as the Compose file.
3. Set `COMPOSE_PROFILES=self-hosted`.
4. Import the remaining values from `.env.example` or, for persistent
   Development, `deploy/persistent-development.env.example`.
5. Set at least `POSTGRES_PASSWORD` and any environment-specific secrets.
6. Configure the two remote build contexts and one matching revision value.
7. Start the deployment. `migrate` must complete before `demo-init`; API and
   worker wait for initialization, and Web waits for API readiness.

For ordinary Development integration on `main`:

```dotenv
SBS_BACKEND_BUILD_CONTEXT=https://github.com/baerenmarke90/SideBySide-Next.git#main:backend
SBS_WEB_BUILD_CONTEXT=https://github.com/baerenmarke90/SideBySide-Next.git#main:web
SBS_BUILD_REVISION=main
```

Before release acceptance, replace `main` in **all three values** with exactly
the candidate commit SHA. Production uses only the exact approved commit SHA.
Never point Backend, Web and the declared build revision at different refs.

The API exposes `SBS_BUILD_REVISION` through `X-SideBySide-Revision`; the Web
image exposes it through `/.well-known/sidebyside-revision`. Release smoke
requires both values to equal the expected commit.

## Persistent Development in Arcane

A long-lived Development instance is a separate Arcane project, not a mode of
the Production project. Start from `deploy/persistent-development.env.example`.
It already selects `COMPOSE_PROFILES=self-hosted` and contains remote Git build
contexts for `main`.

Use a unique `COMPOSE_PROJECT_NAME`, database password, cursor signing key,
bootstrap state and media storage. Before Production promotion:

1. resolve the candidate commit SHA;
2. pin both build-context URLs and `SBS_BUILD_REVISION` to that SHA;
3. rebuild/recreate the complete Development stack;
4. verify migrations, API/Web health, both revision identities, authenticated
   smoke, and the affected product path;
5. configure Production to the same exact commit SHA only after acceptance.

Use `scripts/check_environment_isolation.py` before promotion when Development
and Production dotenv files are available. Use `scripts/deployment_smoke.py`
for the non-destructive network smoke.

## Public and private repositories

Docker/BuildKit can load a public Git build context directly. Private
repositories require Git authentication supplied by the operator or Arcane to
the build environment. Do not embed credentials or tokens in Git URLs,
`compose.yaml`, or checked-in env templates.

If the Arcane/BuildKit setup cannot authenticate remote Git contexts, configure
that capability first or use a verified complete checkout. Do not create another
Compose manifest as a workaround.

## Target architecture with a reverse proxy

The reverse proxy is the only public TLS endpoint. On the same public origin it
routes to two internal targets:

| Path | Internal target |
|---|---|
| `/api/` | SideBySide API on `API_PORT` |
| all other paths | SideBySide Web on `WEB_PORT` |

The `/api/` route must go directly to the API. In Production it must not first
pass through the Web Nginx container because that would lose the trusted TLS
proxy hop for `X-Forwarded-Proto`.

### Reverse proxy on the same host

```dotenv
SBS_BIND_IP=127.0.0.1
API_PORT=8000
WEB_PORT=8080
```

### Reverse proxy on another host

Bind only the private Docker/Arcane host address, not an unnecessarily broad
`0.0.0.0` listener:

```dotenv
SBS_BIND_IP=192.168.10.20
API_PORT=8000
WEB_PORT=8099
SBS_ENVIRONMENT=production
SBS_PUBLIC_BASE_URL=https://sidebyside.example
SBS_ALLOWED_HOSTS=["sidebyside.example","localhost","127.0.0.1"]
TRUSTED_PROXY_IPS=192.168.10.30,192.168.10.31
```

`TRUSTED_PROXY_IPS` contains only the addresses or smallest CIDR range from
which the reverse proxy actually reaches the API. Never use `*`.

## Web Space context

The Web client does not accept an operator-provided Space UUID. After
authentication it discovers the account's active Memberships through the API
and uses only a server-authorized Space. Arcane therefore needs no
Space-specific Web build argument or environment value.

## Post-deployment verification

From the reverse-proxy host or the same private network:

```bash
curl --fail http://<docker-host>:<WEB_PORT>/healthz
curl --fail http://<docker-host>:<WEB_PORT>/.well-known/sidebyside-revision
curl --fail --include https://sidebyside.example/api/v1/health/ready
```

The normal API readiness response is:

```json
{"status":"ok","database":"ok"}
```

For release acceptance prefer the shared helper:

```bash
python3 scripts/deployment_smoke.py \
  --base-url https://sidebyside.example \
  --expected-revision <expected-commit-sha>
```

Both Web and API must report the expected commit SHA.
