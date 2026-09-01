# Arcane Deployment

These notes supplement `SELF-HOSTING.md` for installations where Arcane manages
the SideBySide stack and a separate TLS reverse proxy sits in front of it.

For persistent Development, release-candidate verification, Production promotion,
and rollback, the authoritative workflow is
[`DEVELOPMENT-AND-RELEASE-ENVIRONMENTS.md`](DEVELOPMENT-AND-RELEASE-ENVIRONMENTS.md).
This document defines Arcane mechanics; it does not create a competing release
policy.

## Which Compose file?

SideBySide has two deliberately separate Self-Hosting entry points:

| Environment | Compose file | Build context |
|---|---|---|
| complete repository checkout | `compose.yaml` | local: `./backend`, `./web` |
| Arcane / remote workspace | `compose.arcane.yaml` | Git repository + ref |

`compose.yaml` is the canonical entry point for normal Docker Compose users.
Arcane should instead use **`compose.arcane.yaml`**. This file requires neither
`./backend` nor `./web` in the Arcane project directory and therefore avoids the
`build context not found` error for `/app/data/projects/<project>/backend`.

Both variants contain the same services, volumes, networks, runtime settings,
and startup dependencies. CI compares their rendered configuration. The remote
Git build contexts and the backend/Web build-revision arguments derived from the
same ref are the intentional source-specific differences.

## Configure Arcane

1. Create the SideBySide project in Arcane with GitOps or the desired repository
   source.
2. Select `compose.arcane.yaml` as the Compose file.
3. Import the values from `.env.example` as the project environment and set at
   least `POSTGRES_PASSWORD` and, for initial registration,
   `SBS_BOOTSTRAP_TOKEN` securely.
4. `SBS_SOURCE_REF=main` may be used for ordinary Development integration. Pin
   persistent Development to an exact candidate commit before release acceptance.
   Production uses only the exact approved commit SHA.
5. Start the deployment. `migrate` must complete successfully before API and
   worker start; Web additionally waits for API readiness.

The Arcane file uses these defaults:

```dotenv
SBS_SOURCE_REPOSITORY=https://github.com/baerenmarke90/SideBySide-Next.git
SBS_SOURCE_REF=main
```

This produces build contexts such as:

```text
https://github.com/baerenmarke90/SideBySide-Next.git#main:backend
https://github.com/baerenmarke90/SideBySide-Next.git#main:web
```

`api`, `worker`, and `migrate` always use the same backend context. Backend and
Web both receive `SBS_BUILD_REVISION` directly from the same `SBS_SOURCE_REF`.
The API exposes that identity through `X-SideBySide-Revision`; the Web image
exposes it through `/.well-known/sidebyside-revision`. Release smoke requires
both values to equal the expected commit, so a stale Web image cannot be accepted
alongside a newer backend.

## Persistent Development in Arcane

A long-lived Development instance is a separate Arcane project, not a mode of the
Production project. Start from `deploy/persistent-development.env.example` and use
a unique `COMPOSE_PROJECT_NAME`, database password, cursor signing key, bootstrap
state, and media storage.

The safe default binds Development to loopback. Device/Android access should be
provided through a controlled private network/VPN or protected reverse proxy, not
by publishing unrestricted development settings to the Internet.

Before a production promotion:

1. resolve the candidate commit SHA;
2. set Development `SBS_SOURCE_REF` to that exact SHA;
3. rebuild/recreate the complete Development stack;
4. verify migrations, API/Web health, both revision identities, authenticated
   smoke, and the affected product path;
5. only then configure Production to the same exact commit SHA.

Use `scripts/check_environment_isolation.py` before promotion when Development and
Production dotenv files are available to the operator. Use
`scripts/deployment_smoke.py` for the non-destructive network smoke.

## Public and private repositories

For a public repository, Docker/BuildKit can load the Git build context without
repository credentials.

For a private repository, the Docker/BuildKit process instead requires Git
authentication provided by the operator or Arcane. This authentication belongs
to the build environment and is **not** stored in `compose.arcane.yaml`,
`.env.example`, or a Git URL with an embedded token.

If the Arcane/BuildKit configuration in use does not support authenticated
remote Git builds, `compose.arcane.yaml` alone is not sufficient for a private
repository. In that case, configure build authentication correctly first or
later switch to versioned registry images. Repository visibility itself is not
a SideBySide requirement.

## Why Git build contexts?

Docker Compose and BuildKit natively support Git repositories with refs and
subdirectories. Arcane therefore does not require a custom deployment
orchestrator or SideBySide-specific synchronization logic.

The previous approach of setting `SBS_BACKEND_BUILD_CONTEXT` and
`SBS_WEB_BUILD_CONTEXT` manually in the standard Compose file was deliberately
removed. The normal Compose file remains focused on complete repository
checkouts, while Arcane has one explicit dedicated entry point.

For v1, Production still rebuilds from an immutable source revision rather than
promoting versioned registry images. The exact commit SHA is the deployment
identity. A registry-based build-once/promote-identical-artifact model may be
introduced later if it materially improves release reproducibility.

## Target architecture with a reverse proxy

The reverse proxy is the only public TLS endpoint. On the same public origin it
routes to two internal targets:

| Path | Internal target |
|---|---|
| `/api/` | SideBySide API on `API_PORT` |
| all other paths | SideBySide Web on `WEB_PORT` |

The `/api/` route must go **directly** to the API. In production it must not
first pass through the Web Nginx container because that would lose the trusted
TLS proxy hop for `X-Forwarded-Proto`.

## Reverse proxy on the same host

The secure default is sufficient:

```dotenv
SBS_BIND_IP=127.0.0.1
API_PORT=8000
WEB_PORT=8080
```

The proxy then uses `127.0.0.1:<API_PORT>` and `127.0.0.1:<WEB_PORT>`.

## Reverse proxy on another host

If the proxy runs on a separate host in the private network, bind SideBySide
specifically to the private address of the Docker/Arcane host:

```dotenv
SBS_BIND_IP=192.168.10.20
API_PORT=8000
WEB_PORT=8099
```

`SBS_BIND_IP` is deliberately **one concrete host address**. `0.0.0.0` is not
required for this topology and unnecessarily increases exposure.

The reverse proxy then routes, for example:

```text
https://sidebyside.example/
    -> http://192.168.10.20:8099

https://sidebyside.example/api/
    -> http://192.168.10.20:8000
```

Configure the public origin and proxy addresses in SideBySide as follows:

```dotenv
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
and uses only a server-authorized Space. Arcane therefore needs no Space-specific
Web build argument or environment value.

## Post-deployment verification

From the reverse-proxy host or the same private network, first verify the Web
service and its exact build identity:

```bash
curl --fail http://<docker-host>:<WEB_PORT>/healthz
curl --fail http://<docker-host>:<WEB_PORT>/.well-known/sidebyside-revision
```

Verify the production API over the real TLS path and inspect the backend
revision:

```bash
curl --fail --include https://sidebyside.example/api/v1/health/ready
```

The API response must include:

```text
X-SideBySide-Revision: <expected-commit-sha>
```

Both targets should work through the public origin:

```bash
curl --fail https://sidebyside.example/
curl --fail https://sidebyside.example/.well-known/sidebyside-revision
curl --fail https://sidebyside.example/api/v1/health/ready
```

The normal API readiness response is:

```json
{"status":"ok","database":"ok"}
```

For release acceptance prefer the shared helper. It fails unless **both** Web
and API report the expected commit:

```bash
python3 scripts/deployment_smoke.py \
  --base-url https://sidebyside.example \
  --expected-revision <expected-commit-sha>
```

## Reuse review

The reviewed alternatives were a custom Arcane synchronization mechanism,
published registry images, and existing Docker/Compose capabilities. Native Git
build contexts were selected because they solve the concrete workspace problem
without introducing a new runtime component or provider abstraction.

- Standard/platform: Docker Compose + BuildKit Git contexts
- new runtime dependencies: none
- external provider: none; Git hosting is only source transport during build
- privacy/user data: this step does not send SideBySide user data off-host
- cost: no additional SideBySide runtime cost
- fallback: verified complete checkout with `compose.yaml`; optionally versioned
  registry images later if remote Git builds become operationally unsuitable
