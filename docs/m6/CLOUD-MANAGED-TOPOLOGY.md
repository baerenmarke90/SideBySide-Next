# Cloud/Managed v1 launch topology

**Owner:** #521
**Depends on:** #189, #190, #375, #519, #520
**Consumed by:** #524, #525
**Status:** frozen v1 contract

This document freezes the supported Cloud/Managed v1 production topology. It is
operationally distinct from Self-Hosted (`docs/SELF-HOSTING.md`, `docs/m6/
OPERATIONS-RECOVERY.md`) but reuses the same Domain, Privacy, authorization,
portability and entitlement contracts. It introduces no Cloud-only Domain branch,
no second migration mechanism and no mandatory Kubernetes/Redis/Celery/Kafka
dependency.

`deploy/compose.cloud.yml` and `deploy/cloud-managed.env.example` are the versioned
deployment representation this document points to.

## 1. Reuse baseline

Cloud/Managed reuses, unchanged:

- the modular-monolith process boundary (API, Web, worker, one-shot `migrate`);
- PostgreSQL as the authoritative database and the existing PostgreSQL Job
  Queue/Outbox (`FOR UPDATE SKIP LOCKED`) for worker concurrency;
- the `MediaStore` abstraction, including the existing S3-compatible object-storage
  adapter (`SBS_MEDIA_STORE=s3`);
- `/api/v1/health` and `/api/v1/health/ready`, and the `X-SideBySide-Revision`
  response header;
- `#375`'s environment/promotion/revision contract and `scripts/deployment_smoke.py`
  (already base-URL/target-agnostic — no Cloud-specific smoke tool is added);
- `#519`'s immutable release identity and build-once image archives;
- `#189` structured JSON logs, request/correlation IDs and redaction;
- `#304` Demo isolation (Demo stays outside this topology's promotion chain).

No new queue, cache, orchestration platform, second backup engine or Cloud-only
Domain service is introduced. Where this document requires infrastructure beyond
what Self-Hosted uses, the reuse justification is stated inline (see §3.5).

## 2. Runtime topology

| Process | Image | Replicas | State |
|---|---|---|---|
| `migrate` | backend runtime image, `alembic upgrade head` | exactly one execution per release, run to completion before `api`/`worker` start | none (must not run concurrently against the same database) |
| `api` | backend runtime image, ASGI server | N, horizontally replicated behind the ingress | stateless, except the deletion-journal file described in §3.5 |
| `worker` | backend runtime image, `python -m sidebyside.jobs.runner` | N, horizontally replicated | stateless; job/outbox concurrency is already `SKIP LOCKED`-safe |
| `web` | Web runtime image (static assets + Nginx) | N, horizontally replicated | fully stateless |
| PostgreSQL | managed provider service | provider-managed (primary + standby/read-replica per provider offering) | authoritative persistent state |
| Object storage | provider S3-compatible service | provider-managed | durable media |

This is the same five-process shape `compose.yaml` already uses for Self-Hosted;
Cloud/Managed removes the bundled `postgres` container and the `local` MediaStore
default in favor of managed equivalents, and removes `demo-init` (§5).

## 3. Required launch-topology decisions

### 3.1 Scaling

- `api` and `web` are safe to run with an arbitrary number of replicas behind the
  ingress; they hold no process-local state that another replica needs, other than
  the shared deletion-journal volume in §3.5.
- `worker` is safe to run with multiple replicas. The existing PostgreSQL Job
  Queue claims work with `FOR UPDATE SKIP LOCKED`; concurrent workers do not
  double-process a job.
- `migrate` is **not** safe to run concurrently. Alembic does not provide its own
  cross-process advisory lock; the deployment must serialize `migrate` as a single
  run-to-completion step (a one-shot job/init container, exactly as `compose.yaml`
  already gates `api`/`worker` behind `migrate`'s `service_completed_successfully`)
  before any `api`/`worker` replica using incompatible schema starts.
- Restart/rollout behavior: replace replicas only after the new revision's
  `/api/v1/health/ready` reports `200`; do not route traffic to a replica before
  its readiness check passes. This is the same gate `#375`'s promotion smoke
  already exercises against a single instance; Cloud/Managed applies it per
  replica during rollout.

### 3.2 Database

- Managed PostgreSQL (a provider's managed PostgreSQL offering) is the supported
  v1 database, not a self-operated PostgreSQL container. This mirrors the existing
  `SBS_DATABASE_URL` connection contract; no application code change is required.
- Connection pooling is the deploying operator's responsibility (provider-side
  pooler, e.g. a managed pooling endpoint, or an application-tier pooler placed in
  front of `SBS_DATABASE_URL`). Core does not bundle a pooler.
- The database must live inside a private network boundary reachable only from
  `api`, `worker` and `migrate`; it must not be publicly reachable.
- Backup/snapshot creation is the managed-provider's responsibility. Per §6, a
  provider snapshot is not recovery evidence until a restore has actually been
  exercised against this topology.

### 3.3 MediaStore

- `SBS_MEDIA_STORE=s3` against a provider S3-compatible bucket is the only
  supported Cloud/Managed v1 media backend; `local` is rejected (§7).
- One bucket (or one clearly separated prefix per environment inside a single
  bucket, consistent with `#375`/`#304` isolation) per environment
  (Development/Demo/Production); Production must not share a bucket or prefix
  with Development or Demo.
- Credentials are scoped to that bucket/prefix only (least privilege); the
  application never exposes a public bucket URL — all media access continues to
  go through the existing signed/read-descriptor path already used by
  `OkHttpReferenceApi`/Web transfer code.
- Object lifecycle, versioning and backup/export strategy are the provider's
  responsibility, consistent with `docs/m6/OPERATIONS-RECOVERY.md` §6; Core does
  not implement a second application-level object backup engine.
- Backup/recovery-point coordination between PostgreSQL and object storage is the
  operator's responsibility: a media backup and a database backup used together
  for restore must be reconciled to the same point in time or later reconciled
  through the existing consistency checks used by Self-Hosted recovery.

### 3.4 Ingress / TLS

- A managed load balancer or reverse proxy is the only public origin, terminating
  TLS in front of `web` and `api`, exactly as `docs/SELF-HOSTING.md`'s "Reverse
  proxy and public exposure" section already defines for Self-Hosted:

  | Path | Internal target |
  |---|---|
  | `/api/` | `api` service, direct (not proxied through `web`) |
  | all other paths | `web` service |

- `SBS_PUBLIC_BASE_URL`, `SBS_ALLOWED_HOSTS` and `TRUSTED_PROXY_IPS` (or the
  platform-native trusted-proxy-range equivalent) must be set to the exact managed
  ingress's public origin and source ranges; `*` is rejected in Production
  (existing `Settings` validation already fails closed here).
- OIDC/WebAuthn callback origins (`SBS_OIDC_CONNECTIONS`, `SBS_WEBAUTHN_ORIGINS`,
  `SBS_WEBAUTHN_RP_ID`) must be configured against the managed public origin, not
  a per-replica internal address.
- PostgreSQL and object storage are never exposed on the public ingress.

### 3.5 Account-deletion journal durability (reuse of #520's contract)

`docs/m6/ACCOUNT-DELETION-RETENTION.md` §7.2 requires the forward-only deletion
reconciliation journal (`SBS_ACCOUNT_DELETION_JOURNAL_PATH`,
`backend/src/sidebyside/identity/deletion_journal.py`) to durably record every
accepted self-service deletion, independent of the point-in-time database backup,
and explicitly assigns Cloud/Managed the obligation to provide an equivalent
provider-neutral durability contract rather than inventing different Domain
semantics.

The journal implementation is a single hash-chained append-only file per
`SBS_ACCOUNT_DELETION_INSTANCE_ID`, guarded by `fcntl` advisory locking. A
self-service deletion request can land on any `api` replica. Therefore:

- **the journal path must resolve to one shared durable volume mounted by every
  `api` replica** (the same file, not a per-replica copy) — for example a managed
  network file service (AWS EFS, GCP Filestore, Azure Files, or an equivalent
  ReadWriteMany-capable volume) that supports POSIX advisory locking (`fcntl`)
  correctly across clients (NFSv4 with proper lock-manager support; a network
  filesystem that only emulates locking, or lacks cross-client `fcntl` semantics,
  is not supported);
- if the deploying operator's platform genuinely cannot provide a shared
  POSIX-lockable volume, the only supported fallback for v1 is dedicating exactly
  one `api` replica (or a separate single-replica internal service) as the sole
  writer of self-service deletion acceptance, with the remaining replicas routing
  that one endpoint to it; this document does not choose that fallback for a
  specific provider and it must be justified against the actual selected
  platform's constraints before use;
- the same volume/writer requirement applies if `worker` ever reads the journal
  for reconciliation (`deletion_reconcile.py`) — it must see the same file `api`
  wrote;
- the volume is a protected recovery unit exactly like the Self-Hosted
  `/var/lib/sidebyside/deletion-journal` volume and must be included in the
  Cloud/Managed backup/recovery scope in §6, independent of the PostgreSQL backup
  window, per `ACCOUNT-DELETION-RETENTION.md` §7.2's retention-horizon coupling.

This is the one piece of the v1 topology that is not "purely stateless
replicas behind a load balancer," and it exists because #520 already defined the
journal's Domain contract; #521 is not permitted to weaken that contract to make
horizontal scaling simpler.

### 3.6 Secrets and configuration

Cloud/Managed keeps the same three-environment separation `#375`/`#304` already
require (Development, Demo, Production), with independent values for at least:

- `SBS_DATABASE_URL` (managed PostgreSQL credentials/endpoint);
- `SBS_S3_ACCESS_KEY_ID` / `SBS_S3_SECRET_ACCESS_KEY` / `SBS_S3_SESSION_TOKEN` /
  `SBS_S3_BUCKET` / `SBS_S3_ENDPOINT`;
- `SBS_CURSOR_SIGNING_KEY`;
- `SBS_BOOTSTRAP_TOKEN` (removed after first ServerAdmin bootstrap, as today);
- `SBS_SMTP_*` mail credentials;
- push credentials (existing engagement/push provider configuration);
- `SBS_OIDC_CONNECTIONS` client secrets;
- entitlement/billing provider credentials (Phase 2 of this launch effort;
  none exist yet in Core beyond the `TEST_FIXTURE` source already rejected in
  Production by `entitlements/service.py::_ensure_source_allowed`);
- operator/platform credentials (deploy/rotate access to the managed platform
  itself).

Secrets are supplied by the managed platform's own secret store (for example a
platform secret-manager binding injected as container environment variables at
deploy time) and must never be committed to the repository, baked into an image,
or written into the `#519` release manifest/SBOM. `deploy/cloud-managed.env.example`
documents the required keys with placeholder values only, exactly like
`deploy/persistent-development.env.example`.

`scripts/check_environment_isolation.py` already generalizes to any two `.env`
files: it compares `SBS_DATABASE_URL` directly (not a `POSTGRES_*` triple) and
only flags a sensitive key when both files actually set it to the same
non-empty value. `deploy/cloud-managed.env.example` therefore needs no
Self-Hosted `POSTGRES_*` fields at all, and the existing tool already accepts it
paired with `deploy/persistent-development.env.example` without modification;
§7 wires this pairing into a repeatable contract test rather than a one-off
manual check.

### 3.7 Environment isolation

Development, Demo and Production Cloud/Managed deployments must not share:
database, bucket/prefix, signing keys, bootstrap token, mail/push/OIDC/entitlement
credentials, or public origin. Demo (#304) remains outside this topology and its
own promotion chain entirely — it is not "Cloud staging."

### 3.8 Availability / restart behavior

- `api`/`web`/`worker` use the same `restart: unless-stopped`-equivalent policy
  Self-Hosted uses; the managed platform's own health-checked replacement
  (readiness-gated rolling replacement) supersedes a local restart policy where
  the platform provides one.
- `migrate` never restarts automatically; a failed migration must stop the
  rollout rather than retry blindly against a partially-migrated schema.
- Health checks reuse `/api/v1/health` (liveness) and `/api/v1/health/ready`
  (readiness, checks the database) exactly as `compose.yaml` already configures.

### 3.9 Operator / break-glass access

Reuses `docs/m6/ADMIN-OBSERVABILITY.md` §1's role boundary unchanged:

- the managed platform's infrastructure access (deploy, restart, rotate secrets,
  read infrastructure logs/metrics) is a separate trust boundary from
  application ServerAdmin, and does not by itself grant Tenant/`OWNER_ONLY`
  content access;
- ServerAdmin's application-level operations (`#334`/`#335`) are unchanged by the
  operating model;
- emergency/break-glass infrastructure access (for example a platform's
  "emergency operator" role) must be least-privilege, time-bounded where the
  platform supports it, and does not imply a content browser — it is
  infrastructure access, not a Domain permission.

### 3.10 Region / residency

v1 launch assumption: a single managed region, selected to match the initial
target user base's expected primary residency, with PostgreSQL, object storage
and compute co-located in that region to avoid unnecessary cross-region latency
and egress cost. No multi-region active/active architecture is introduced for v1;
this is a documented limitation, not a silent gap — a region/provider outage is a
recovery scenario (§6.5), not a mitigated failure mode in v1.

The exact provider/region is an operator/deployment-time choice, not hard-coded in
the repository; this document fixes the *decision to run single-region* and the
*co-location requirement*, not a specific vendor region name.

### 3.11 Capacity

Documented v1 assumption (revisited by `#524`'s measured evidence, not asserted as
an SLA):

- initial expected load: a small-to-moderate number of concurrent couples
  (two-person Spaces), consistent with the product's relationship-scoped model;
- `api`: minimum 2 replicas for rollout availability (no single point of failure
  during a rolling deploy), scaled by observed CPU/request-latency;
- `worker`: minimum 1 replica, scaled by observed job-queue backlog age;
- database: the smallest managed PostgreSQL class that keeps `/api/v1/health/ready`
  latency and job-processing latency within the `#524` measured baseline; upgraded
  by observed connection/CPU pressure, not by a priori sizing;
- object storage: no fixed capacity limit assumed beyond the provider's own
  service limits; per-account storage quota, if any, is a `#262` product decision,
  not a topology decision.

No SLA/RPO/RTO number is asserted here; `#524` records measured values against
this topology.

## 4. Deployment representation

`deploy/compose.cloud.yml` is the versioned, reviewable deployment representation
for this topology, reusing the existing Compose-based recipe rather than
introducing Terraform/Kubernetes/a custom orchestrator (no demonstrated launch
need for those exists yet, per Reuse-before-build). It differs from `compose.yaml`
only as required by this document:

- no bundled `postgres` service — `SBS_DATABASE_URL` must point at the managed
  database;
- no `local` MediaStore default and no `media_data` volume — `SBS_MEDIA_STORE=s3`
  is required;
- no `demo-init` service (§5);
- `api`/`worker`/`web`/`migrate` use `image:` references to the exact `#519`
  released image archives (loaded/pushed by the operator to a registry the
  managed platform can pull from — see §4.1) instead of `build:` — Cloud/Managed
  never builds from source at deploy time;
- an explicit named volume for the deletion-journal path, documented as requiring
  a shared/network-backed implementation per §3.5 (Compose's own named-volume
  driver is the local/single-host expression of this; the managed platform's
  actual multi-replica deployment descriptor generated from this Compose file
  must bind that mount to its ReadWriteMany-equivalent volume type).

This file is the reviewable *contract* (process shape, environment variables,
health checks, volume/network boundaries); the operator's actual managed-platform
deployment descriptor (whichever container platform is selected) is generated
from it, the same way `scripts/compose_checked.py` already treats `compose.yaml`
as the verified source of truth for Self-Hosted rather than hand-maintaining a
second recipe.

### 4.1 Image provenance

Per `docs/m6/IMMUTABLE-RELEASES.md`, `#519` publishes `backend-runtime.image.tar`
and `web-runtime.image.tar` (`docker save` archives) attached to an immutable
GitHub Release, not a registry push. For Cloud/Managed:

1. the operator downloads the exact release's image archives and manifest;
2. verifies the manifest/attestation/SBOM per `#519`/`#193`;
3. `docker load`s the archives and pushes them, unmodified, to the registry the
   managed platform pulls from, tagged with the immutable release tag
   (`v<product-version>`) — never `latest`;
4. `deploy/compose.cloud.yml`'s `SBS_BACKEND_IMAGE`/`SBS_WEB_IMAGE` variables are
   set to that exact pushed reference.

No image is rebuilt from source for Cloud/Managed promotion; this is the "build
once, publish immutable artifacts" decision `#519` already made, applied at the
deployment boundary. A floating tag (`latest`, `main`, or an unpinned branch
reference) is never an acceptable Production image reference (§7).

## 5. Demo exclusion

`compose.yaml`'s `demo-init` service (`python -m scripts.demo_space ensure`) is
intentionally **not** part of `deploy/compose.cloud.yml`. The canonical public Demo
(`#304`) is its own isolated deployment, not a step inside the Cloud/Managed
Production topology; Cloud/Managed Production must never auto-provision demo
content.

## 6. Recovery and rollback

Maps `docs/m6/OPERATIONS-RECOVERY.md` §4's "Cloud/Managed" recovery units to this
topology:

1. **Managed PostgreSQL** — provider automated backup/point-in-time-recovery
   configured at the smallest interval the provider offers; restore path is the
   provider's own restore-to-new-instance mechanism, followed by repointing
   `SBS_DATABASE_URL`.
2. **Object storage** — provider bucket versioning (or equivalent
   backup/replication feature) enabled on the Production bucket.
3. **Deletion-journal volume (§3.5)** — included in the same recovery-point
   discipline as the database; a database restore without the matching journal
   state (or vice versa) is treated as an inconsistent recovery point and must be
   reconciled before the application resumes traffic, exactly as
   `ACCOUNT-DELETION-RETENTION.md` §7.2 requires.
4. **Managed secrets/config** — recovered through the platform's own
   secret-store backup/versioning, or re-provisioned from the operator's protected
   secret-management process; secrets are never recovered from application
   backups.
5. **Application release identity** — `#519`'s previous-known-good release
   selection; redeploying an old image never implies a database rollback (same
   rule as `OPERATIONS-RECOVERY.md` §5).

**Provider-managed backup is not recovery evidence until a real restore has been
exercised against this exact topology.** `#524` is responsible for performing (or
explicitly marking `BLOCKED` with the missing external prerequisite for) that
restore; this document only fixes which units must be restorable and how they
must be reconciled.

### 6.1 Failure/outage assumption

A full managed-region outage in the v1 single-region topology (§3.10) is a
documented unmitigated scenario: recovery is "redeploy in another region from the
last coordinated recovery point," not automatic failover. This is stated
explicitly rather than silently assumed away.

## 7. Contract tests

`tools/ci/test_cloud_managed_topology.py` (added by this change) enforces the
mechanical parts of this contract so they cannot silently regress:

- `deploy/compose.cloud.yml` declares no `postgres` service and no `local`-backed
  media volume;
- `demo-init` is absent from the Cloud Compose file;
- `api`/`worker`/`web`/`migrate` use `image:` (not `build:`);
- the default/example image reference is neither empty nor `latest`/`main`
  (fails closed rather than silently defaulting to a floating tag);
- `migrate` has no automatic restart policy;
- the deletion-journal path is mounted from a dedicated named volume, not an
  ephemeral container-local path;
- `deploy/cloud-managed.env.example` requires `SBS_ENVIRONMENT=production`,
  `SBS_DEPLOYMENT=cloud`, `SBS_MEDIA_STORE=s3` and rejects a `local` media
  configuration;
- `scripts/check_environment_isolation.py`, unmodified, accepts the Cloud
  template paired with the existing Development template and rejects a Cloud
  Production file that reuses a Development signing key or bootstrap token.

These are configuration-contract tests, not a new deployment platform or a second
CI environment; they reuse the existing `tools/ci` `unittest` layout used by the
`#519` release tooling tests, and run as the "Cloud/Managed deployment recipe
contract (#521)" step inside the existing `Self-Hosted Deployment Guard` workflow
(`.github/workflows/self-hosted-deployment-guard.yml`), gated by the same
`deployment_guard` change-scope classification as the Self-Hosted Compose
contract (`tools/ci/change_scope.py`).

## 8. Security / privacy

- no ServerAdmin content-browsing shortcut is introduced by this topology (§3.9);
- least-privilege service credentials: `api`/`worker` receive only the database
  and bucket/prefix credentials they need; platform/infrastructure credentials
  are never handed to the application process;
- database and object storage are never publicly reachable (§3.2, §3.4);
- secrets stay outside images/source/release manifests/SBOM (§3.6);
- backup, log and metrics data receive the same sensitivity treatment as
  Production data — `#189` redaction already strips ProtectedPayload/`OWNER_ONLY`/
  tokens/signed URLs from logs, and that same log stream is what any managed
  observability export consumes (§9); no Cloud-specific logging path bypasses
  that redaction;
- Tenant/Privacy semantics are identical to Self-Hosted — no code in
  `backend/src/sidebyside` branches Domain authorization on `Deployment.CLOUD`
  vs. `Deployment.SELF_HOSTED` (the only existing `Deployment` branch,
  `entitlements/service.py::_grant_capabilities`, gates commercial *capability*
  availability, not privacy/authorization).

## 9. Observability

Cloud/Managed consumes `#189`'s existing structured JSON stdout logs and
request/correlation IDs unchanged. The managed platform may forward that stdout
stream to a managed logging/metrics stack (log shipping is an infrastructure
concern outside the application); Core itself gains no mandatory SaaS telemetry
dependency, so Self-Hosted is unaffected.

Minimum operational signals for G5, all already available without new Cloud-only
code:

- `/api/v1/health` and `/api/v1/health/ready` (liveness/readiness, consumed by
  the platform's own health-gated rollout);
- `X-SideBySide-Revision` header (deployed-revision verification, `#375`'s
  existing smoke check);
- `#189` structured request logs (status, latency, redacted correlation) for
  error-rate/latency SLO-style indicators;
- worker job-queue backlog age, derived from the existing Outbox/Job Queue tables
  (no new metrics pipeline; a read-only query against existing tables, exposed
  operationally exactly as any other operational check).

## 10. Business / freemium

Self-Hosted vs. Cloud/Managed remains the `Deployment` operating-model axis;
Free/Premium remains the `#262`/`#523` product-tier axis. This document adds no
new capability gate. The one existing `Deployment`-conditioned behavior
(`CLOUD_ONLY_CAPABILITIES` in `entitlements/service.py`) predates this issue and
is a `#262`/`#523` product decision, not a topology decision; this document does
not change it.

## 11. Out of scope (unchanged from the issue)

- replacing Self-Hosted `#375`;
- using the public Demo as staging;
- application feature work;
- entitlement provider selection (Phase 2 of this launch effort, tracked
  separately);
- Kubernetes or multi-region architecture without a demonstrated launch need;
- copying real Production data into Development/Demo.
