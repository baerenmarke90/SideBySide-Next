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
| Development | persistent integration, migration and release-candidate verification | fictional/test only | `main` or an explicit candidate commit |
| Demo | public product demonstration and manual QA | canonical fictional demo data | independently deployed |
| Production | supported service with real user data | real | immutable commit SHA |

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

- PR/local: branch or PR commit;
- normal Development: `main` may float;
- release-candidate Development: exact commit SHA;
- Production: exact immutable commit SHA only.

A human-readable release tag may point to the production commit, but the production
Arcane `SBS_SOURCE_REF` should be the resolved 40-character commit SHA. This avoids
relying on a movable tag during deployment.

For v1, SideBySide continues to build from Git/BuildKit rather than introducing a
container registry solely for promotion. This means Development and Production may
rebuild the same immutable source; the invariant is **same known source revision**,
not byte-identical image layers. Versioned registry images remain a valid later
improvement if build-once/promote-the-identical-artifact becomes operationally
important.

## 6. Deployed revision observability

The backend image receives its source revision at build time. The API returns it on
both health endpoints as:

```text
X-SideBySide-Revision: <revision>
```

For Arcane builds this value is derived from `SBS_SOURCE_REF`; API, worker, and
migrate use the same backend build context. The Web build uses the same Git ref.
For a normal local checkout the fallback is `local-checkout` unless
`SBS_BUILD_REVISION` is explicitly supplied.

A release smoke check must compare the header with the expected candidate or
production commit. A healthy service serving the wrong revision is a failed
promotion.

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
8. `X-SideBySide-Revision` equals the candidate commit;
9. authenticated sign-in and one authenticated core read succeed;
10. affected manual acceptance paths are exercised where automated coverage is
    insufficient;
11. worker/job behavior is checked when the release changes asynchronous work;
12. media read/write behavior is checked in Development when the release changes
    media;
13. rollback/forward-fix implications of every new migration are known.

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
- API `/api/v1/health/ready` and database readiness;
- the deployed revision header;
- optionally, password sign-in plus `GET /api/v1/auth/memberships` when
  `SBS_SMOKE_EMAIL` and `SBS_SMOKE_PASSWORD` are provided.

Smoke credentials must belong to a fictional Development/Production smoke account
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

## 10. Release and production promotion

Recommended operator sequence:

```bash
# In a trusted checkout after CI and Development acceptance:
CANDIDATE=$(git rev-parse <candidate-ref>^{commit})
git tag -a vX.Y.Z "$CANDIDATE" -m "SidebySide vX.Y.Z"
git push origin vX.Y.Z
```

Record both the tag and `$CANDIDATE`. Configure Production with:

```dotenv
SBS_ENVIRONMENT=production
SBS_SOURCE_REF=<CANDIDATE>
```

Then rebuild/recreate the complete Production stack. Confirm migrations, readiness,
Web health, and the revision header before declaring the release complete.

A tag is the human release name; the resolved commit SHA is the deployment identity.

## 11. Rollback and recovery

Before every Production promotion record:

- current Production commit SHA;
- candidate commit SHA;
- latest verified database backup/restore point;
- migrations introduced between the two commits;
- whether application rollback is schema-compatible.

If the candidate fails before an incompatible migration is committed, redeploy the
previous known-good commit SHA and repeat smoke verification.

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
and the deployment guard.

Operators own environment facts CI cannot prove from the repository: actual secret
separation, persistent Development health, external reverse proxy/TLS behavior,
backup availability, manual release acceptance, and the final Production promotion.

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
