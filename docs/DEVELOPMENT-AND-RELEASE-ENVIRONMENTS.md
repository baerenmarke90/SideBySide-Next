# Development and Release Environments

**Status:** authoritative operations contract for persistent Development and production promotion  
**Scope:** Self-Hosted / Arcane / Docker Compose  
**Related:** #375, #304

This document defines how SideBySide remains continuously developable after a real
production instance exists. It is the binding environment and promotion contract;
`ARCANE.md`, `SELF-HOSTING.md`, and environment templates must point here rather
than defining competing release rules.

## 1. Environment topology

SideBySide has four distinct operational purposes:

| Environment | Purpose | Data | Source revision |
|---|---|---|---|
| Local / PR | developer feedback and automated validation | disposable/generated | feature branch or PR commit |
| Development | persistent integration, migration and release-candidate verification | fictional/test only | `main` or an exact candidate commit |
| Demo | public product demonstration and manual QA | canonical fictional demo data | independently deployed |
| Production | supported service with real user data | real | exact immutable commit SHA |

The public Demo from #304 is **not** a staging environment and is not a production
release gate. Development may use the canonical fictional scenario as test data,
but Development, Demo, and Production never share PostgreSQL volumes, media
volumes/buckets, secrets, sessions, signing keys, or Compose/Arcane projects.

## 2. Non-negotiable isolation

A persistent Development deployment must have its own:

- Arcane/Compose project name;
- PostgreSQL volume and credentials;
- media volume or S3 bucket/prefix and credentials;
- cursor signing key;
- bootstrap/admin credentials;
- authentication callback configuration;
- provider credentials;
- session state and user accounts.

Production data is not a development fixture. Do not routinely copy a production
database or production media into Development. Incident-specific use of
production-derived data requires a separate minimization/anonymization and privacy
review; it is not part of this workflow.

Before production promotion, operators should run
`scripts/check_environment_isolation.py` against the Development and Production
environment files. The check fails without printing secret values when it detects
obvious reuse of project names, public origins, database URLs, cursor keys, or
storage credentials/buckets.

## 3. Supported deployment primitives

No new orchestrator is introduced for v1.

- Complete repository checkout: `compose.yaml`.
- Verified release-candidate/Production deployment from a complete checkout:
  `scripts/compose_checked.py` wrapping `compose.yaml`.
- Arcane / remote Git workspace: `compose.arcane.yaml`.
- Development database only for source-code work: `deploy/docker-compose.dev.yml`.
- Persistent Development: the complete SideBySide stack, normally through
  `compose.arcane.yaml`, with a dedicated Arcane project and the template at
  `deploy/persistent-development.env.example`.

Both complete-stack Compose variants keep the same services and dependency order:

```text
postgres -> migrate -> demo-init(no-op outside Demo) -> api/worker -> web
```

The `migrate` service must succeed before API/worker start, and Web waits for API
readiness. Production is never the first persistent environment to execute a new
migration.

### 3.1 Raw Compose is not a release identity

Direct `docker compose` from a complete checkout remains the convenient local/test
path. Its backend and Web images deliberately report:

```text
unverified-local-checkout
```

That marker cannot be replaced through `.env`. Therefore a dirty checkout or an
operator-selected value cannot impersonate an approved commit.

A complete-checkout release candidate or Production deployment must use
`scripts/compose_checked.py`. The wrapper:

- derives the exact 40-character revision from Git `HEAD`;
- refuses a checkout with tracked or untracked changes;
- optionally requires `--expected-revision` to match `HEAD` exactly;
- injects that derived revision into backend **and** Web build arguments;
- refuses alternate Compose files/project directories that could detach the proof
  from the canonical checkout.

Arcane does not use this wrapper because its remote Git build context and build
identity are both derived from the same `SBS_SOURCE_REF`.

## 4. Persistent Development

### 4.1 Recommended Arcane setup

Create a dedicated Arcane project, for example `sidebyside-development`, separate
from any Production or Demo project.

Use:

```text
Compose file: compose.arcane.yaml
SBS_ENVIRONMENT=development
SBS_SOURCE_REF=main
```

Start from `deploy/persistent-development.env.example`, then replace every secret
placeholder with a Development-only value. Never import the Production environment
wholesale and edit only the hostname.

Development may follow `main` for ordinary integration. For release-candidate
verification, pin Development temporarily to the exact candidate commit SHA:

```dotenv
SBS_SOURCE_REF=<40-character-candidate-commit-sha>
```

Rebuild/recreate the complete stack and perform the promotion gates below against
that exact candidate.

### 4.2 Exposure policy

`SBS_ENVIRONMENT=development` intentionally has less public-runtime hardening than
Production. Therefore persistent Development is private/internal by default.

Accepted exposure models are:

1. loopback only plus SSH/VPN access;
2. a private network address reachable only from a controlled management/test
   network;
3. a TLS reverse proxy protected by access control and not publicly discoverable.

Do not publish an unrestricted Development instance to the Internet merely to make
Android testing convenient. If Android must reach it, provide a controlled private
network/VPN path or a protected TLS origin.

## 5. Source revision policy

The revision policy is intentionally different by environment:

- PR/local: branch or PR commit; raw Compose remains explicitly unverified;
- normal Development: `main` may float;
- release-candidate Development: exact commit SHA;
- Production: exact immutable commit SHA only.

A human-readable release tag may point to the production commit, but an Arcane
Production `SBS_SOURCE_REF` must be the resolved 40-character commit SHA. This
avoids relying on a movable tag during deployment.

For v1, SideBySide continues to build from Git/BuildKit rather than introducing a
container registry solely for promotion. Development and Production may rebuild
the same immutable source; the invariant is **same verified source revision for
all application components**, not byte-identical image layers. Versioned registry
images remain a valid later improvement if build-once/promote-the-identical-artifact
becomes operationally important.

## 6. Deployed revision observability

Backend and Web carry independent build identities so a mixed-version deployment
cannot pass release smoke.

The API returns the backend identity on both health endpoints as:

```text
X-SideBySide-Revision: <revision>
```

The Web image exposes its build identity at:

```text
/.well-known/sidebyside-revision
```

For Arcane, both identities are derived from `SBS_SOURCE_REF`; API, worker, and
migrate use one backend build context while Web uses the same source ref for its
own build context. For a verified complete checkout, `scripts/compose_checked.py`
injects the exact clean Git `HEAD` into both builds.

A release smoke check must require **both** Web and API identities to equal the
expected candidate/Production commit. A healthy component serving the wrong
revision, or a stale Web image paired with a new backend, is a failed promotion.

## 7. Promotion gates

Production promotion is allowed only when all of the following are true for the
candidate commit:

1. repository CI is green;
2. migration/schema-drift checks are green;
3. OpenAPI and generated clients are consistent when affected;
4. security/privacy/reuse/supply-chain/engineering-language gates are green;
5. candidate commit is deployed to persistent Development;
6. Development migration succeeds;
7. API readiness and Web health succeed;
8. Web and API deployment identities both equal the candidate commit;
9. authenticated sign-in and one authenticated core read succeed;
10. affected manual acceptance paths are exercised where automated coverage is
    insufficient;
11. worker/job behavior is checked when the release changes asynchronous work;
12. media read/write behavior is checked in Development when the release changes
    media;
13. rollback/forward-fix implications of every new migration are known.
14. the repository recovery gate is green and Production has a fresh coordinated
    recovery point according to `SELF-HOSTED-RECOVERY.md` before migration.

A failing Development deployment blocks ordinary Production promotion.

## 8. Smoke verification

The non-destructive network smoke helper is:

```bash
python3 scripts/deployment_smoke.py \
  --base-url https://dev.sidebyside.example \
  --expected-revision <candidate-sha>
```

It verifies:

- Web `/healthz`;
- Web `/.well-known/sidebyside-revision`;
- API `/api/v1/health/ready` and database readiness;
- API `X-SideBySide-Revision`;
- exact equality of both component identities with the requested revision;
- optionally, password sign-in plus `GET /api/v1/auth/memberships` when
  `SBS_SMOKE_EMAIL` and `SBS_SMOKE_PASSWORD` are provided.

Smoke credentials must belong to a fictional Development/operator smoke account
appropriate for the target environment and must not be committed. Do not use a
real user's credentials as an automated test secret.

The remote smoke helper deliberately does not create or modify product content.
When a release affects worker jobs or media writes, exercise those paths in
Development with fictional data and verify the worker remains healthy. Production
post-deploy smoke should remain non-destructive unless a separately approved
operator test account and cleanup procedure exist.

For a host with Compose access, additionally verify:

```bash
docker compose ps
docker compose logs --tail=100 migrate api worker web
```

`migrate` must have exited successfully; API and Web must be healthy; worker must
be running.

## 9. Migration safety

Every new Alembic migration follows this order:

1. CI migration and schema-drift validation;
2. candidate deployment to persistent Development;
3. `migrate` succeeds against Development's persistent database;
4. affected read/write path is exercised;
5. backup requirement and downgrade compatibility are reviewed;
6. only then may Production run the migration.

Do not describe `git checkout` as a complete rollback strategy. If a migration is
not safely reversible, the recovery plan is normally a forward fix or restore from
a verified pre-change backup plus a compatible application revision.

High-risk schema changes require a confirmed Production backup/restore point before
promotion.

The complete PostgreSQL, LocalMediaStore, configuration/secret, and S3 consistency
contract is defined in `SELF-HOSTED-RECOVERY.md`. A database-only dump is not a
complete recovery point when the instance stores media.

## 10. Release and Production promotion

After CI and Development acceptance, resolve and record the immutable candidate:

```bash
CANDIDATE=$(git rev-parse <candidate-ref>^{commit})
git tag -a vX.Y.Z "$CANDIDATE" -m "SidebySide vX.Y.Z"
git push origin vX.Y.Z
```

A tag is the human release name; `$CANDIDATE` is the deployment identity.

### 10.1 Arcane Production

Configure Production with:

```dotenv
SBS_ENVIRONMENT=production
SBS_SOURCE_REF=<CANDIDATE>
```

Rebuild/recreate the complete Arcane stack and run the smoke helper with exactly
that candidate SHA.

### 10.2 Complete-checkout Production

Use a trusted checkout at the candidate, verify it is clean, and deploy only
through the checked wrapper:

```bash
git checkout "$CANDIDATE"
git status --short
python3 scripts/compose_checked.py \
  --expected-revision "$CANDIDATE" \
  up -d --build --force-recreate --wait --wait-timeout 300
```

The wrapper refuses dirty or mismatched source before Docker Compose runs. Do not
replace this release command with raw `docker compose`; raw Compose intentionally
reports `unverified-local-checkout` and cannot satisfy a commit-specific smoke.

After either deployment path, confirm migrations, readiness, Web health, and both
revision identities before declaring the release complete.

## 11. Rollback and recovery

Before every Production promotion record:

- current Production commit SHA;
- candidate commit SHA;
- latest verified coordinated database/media backup plus separately protected
  configuration and secrets;
- migrations introduced between the two commits;
- whether application rollback is schema-compatible.

If the candidate fails before an incompatible migration is committed, redeploy the
previous known-good commit SHA and repeat smoke verification. Arcane pins the old
SHA as `SBS_SOURCE_REF`; a complete checkout uses the same verified wrapper against
a clean checkout at the old SHA.

If the candidate has already applied a schema change that is not backward
compatible, do **not** blindly redeploy old code. Choose one of:

- forward-fix application/schema;
- explicitly tested downgrade migration;
- restore the pre-change database backup and redeploy the previous revision.

Media compatibility must be reviewed separately when the release changes media
formats, storage keys, or lifecycle semantics.

## 12. Demo relationship

The public Demo remains independent:

```text
Local / PR -> Development -> Production
                  X
                  |
                Demo
```

Demo can receive its own chosen revision for product demonstrations, but its health
is not a substitute for Development acceptance. Demo data/storage must not be
promoted into Production.

## 13. CI versus operator responsibility

CI owns deterministic repository checks: tests, migrations from clean schemas,
OpenAPI/client drift, security/privacy/reuse/supply-chain rules, Compose rendering,
verified-checkout refusal behavior, Web/API revision parity, and the deployment
guard.

Operators own environment facts CI cannot prove from the repository: actual secret
separation, persistent Development health, external reverse proxy/TLS behavior,
offsite archive/key availability, real restore drills and timing, provider-specific
S3 consistency, manual release acceptance, and the final Production promotion.

## 14. Completion evidence for #375

Repository-side implementation is complete when this runbook, the persistent
Development template, revision reporting, smoke helper, isolation check, and CI
coverage are merged.

The final operational acceptance criterion for #375 requires one real end-to-end
exercise on the intended infrastructure:

```text
candidate -> persistent Development -> migrate/smoke/accept -> immutable commit ->
Production -> post-deploy smoke
```

Do not mark that infrastructure exercise complete merely because CI passed. Record
the Development and Production revision SHAs and the successful smoke result in the
issue/PR when the exercise is actually performed.
