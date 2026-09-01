# Development and Release Environments

This document is the authoritative operating model for moving SideBySide from a
source change to a production deployment. It deliberately separates development,
public demo, and production so ongoing development never depends on production
data or experiments on the production stack.

## Environment topology

SideBySide uses four operational purposes:

| Environment | Purpose | Source revision | Data | Exposure |
|---|---|---|---|---|
| Local / PR | developer feedback and automated validation | feature branch / PR commit | disposable test data | local only |
| Development | persistent integration, migration and release-candidate verification | `main` or an explicitly selected candidate commit | isolated fictional/test data | private or access-controlled |
| Demo | public product demonstration and manual QA | explicitly selected deployed revision | canonical fictional Lea/Alex data | public, hardened demo mode |
| Production | real supported user data | immutable release tag or immutable commit | real data | public through TLS reverse proxy |

The public Demo deployment is **not** the Development release gate. Development
may seed the canonical demo scenario for repeatable QA, but Demo, Development and
Production must remain separate Compose projects with separate volumes and
secrets.

The binding flow is:

```text
feature branch / PR
        |
        +-- repository CI + automated tests
        v
merge to main
        v
Development deployment
        |
        +-- migrate
        +-- readiness / health
        +-- smoke verification
        +-- affected manual acceptance
        v
immutable release tag / commit
        v
Production deployment
        v
post-deploy smoke verification
```

A failed Development deployment or failed release verification blocks ordinary
Production promotion.

## Supported deployment primitives

No additional orchestrator is required for this workflow.

- `compose.yaml` remains the canonical complete-checkout Compose entry point.
- `compose.arcane.yaml` remains the Arcane / remote Git build-context entry point.
- `SBS_ENVIRONMENT=development` is used by the persistent Development instance.
- `SBS_ENVIRONMENT=demo` plus `SBS_DEMO_MODE=true` is reserved for the isolated public Demo deployment.
- `SBS_ENVIRONMENT=production` is reserved for real Production.
- The existing `migrate` service is the authoritative schema-upgrade step.
- API readiness is `/api/v1/health/ready`.
- Web health is `/healthz`.

For Arcane, API, worker, migration and Web are all built from the same
`SBS_SOURCE_REF`; therefore a single project deployment cannot silently combine
backend services from one source revision with Web from another.

## Persistent Development instance

Development is a long-lived, resettable integration environment. A typical
Arcane project may use a name such as `sidebyside-development`; Production must
use a different project such as `sidebyside-production`.

Minimum Development configuration:

```dotenv
SBS_ENVIRONMENT=development
SBS_SOURCE_REF=main
SBS_DEMO_MODE=false
POSTGRES_USER=sidebyside_dev
POSTGRES_PASSWORD=<development-only secret>
POSTGRES_DB=sidebyside_dev
SBS_CURSOR_SIGNING_KEY=<development-only secret>
SBS_PUBLIC_BASE_URL=https://dev.sidebyside.example
SBS_ALLOWED_HOSTS=["dev.sidebyside.example"]
SBS_MAIL_TRANSPORT=none
```

If the reverse proxy is on another host, configure `SBS_BIND_IP` and
`TRUSTED_PROXY_IPS` as described in `ARCANE.md`.

### Isolation invariant

Development and Production must never share:

- Compose project name;
- PostgreSQL volume;
- media volume or S3 bucket/prefix;
- database credentials;
- cursor/signing keys;
- bootstrap/admin credentials;
- OIDC client secrets or callback registration where separate clients are possible;
- WebAuthn relying-party configuration where the hostname differs;
- SMTP/provider credentials unless an explicitly reviewed non-production provider is used;
- external-provider/API keys that can affect Production resources.

With the bundled Compose files, PostgreSQL and local media use named volumes.
Docker scopes those volumes by Compose project name. Running Development and
Production as distinct projects therefore produces distinct `postgres_data` and
`media_data` volumes even when both stacks are on the same Docker host.

Do not override that isolation by manually attaching a Development service to a
Production volume.

If S3-compatible storage is used, Development requires its own bucket or a
strictly isolated bucket prefix and separate credentials. Production media must
not be used as a Development fixture.

## Data policy

The normal Development data source is generated or fictional data.

Preferred sources:

- unit/integration fixtures;
- the canonical Lea/Alex demo scenario where representative product data is useful;
- purpose-built synthetic data for a specific regression.

Do not routinely restore Production PostgreSQL dumps or Production media into
Development.

If a production incident genuinely cannot be reproduced without production-
derived data, that is a separate incident procedure. It requires explicit
minimization/anonymization and privacy review before data leaves the production
boundary. This document does not authorize such a copy.

## Source and revision policy

### Local / PR

Use the feature branch or exact PR head commit. Repository CI is authoritative
for the commit being reviewed.

### Development

The normal Development source is:

```dotenv
SBS_SOURCE_REF=main
```

For release-candidate verification, Development may instead be pinned temporarily
to an explicit candidate commit or immutable tag. Record that value before
acceptance testing.

### Demo

Demo is independently deployed. It may follow an explicitly selected candidate
for QA, but it is not the release gate and must not share Development or
Production storage.

### Production

Production must **never** follow a floating branch such as `main`.

Use either:

- an immutable release tag, preferred for the current Git-build-context model; or
- an explicit immutable commit SHA when an emergency deployment process requires it.

Example:

```dotenv
SBS_SOURCE_REF=v0.1.0
```

The release tag must resolve to the exact commit that passed the intended
Development verification. Retagging or moving a Production release tag is not
allowed.

## Build and promotion model

The current v1 model is **immutable Git source promotion**:

1. merge code to `main` only after repository CI is green;
2. deploy that exact `main` commit to Development;
3. run migration, readiness, smoke and acceptance verification;
4. create an immutable release tag on that verified commit;
5. set Production `SBS_SOURCE_REF` to that tag;
6. rebuild/recreate the Production stack from that immutable ref;
7. run post-deploy smoke verification.

This is intentionally not a claim that the binary image built in Development is
bit-for-bit promoted to Production. The invariant in v1 is the immutable source
revision plus the same pinned build definitions and dependency verification.

A future move to versioned registry images may strengthen this into literal
build-once/promote-the-same-image semantics. That is optional follow-up work and
must not weaken the current immutable-source requirement.

## Migration gate

Production must never be the first persistent environment on which a new Alembic
migration runs.

For every candidate containing a migration:

1. repository migration/schema-drift CI must be green;
2. deploy the candidate to Development;
3. allow the normal `migrate` service to execute `alembic upgrade head`;
4. require API readiness after migration;
5. verify the affected feature path;
6. only then promote the revision to Production.

Before a high-risk or non-reversible schema change, verify the Production backup
and restore path before deployment.

A migration that cannot be safely downgraded must be treated as forward-fix only.
Do not describe application-code rollback as safe unless the previous application
revision is compatible with the migrated schema.

## Required promotion gates

A normal Production promotion requires all of the following:

- repository CI green on the candidate revision;
- migration/schema-drift gates green;
- generated OpenAPI clients consistent where the revision changes the API;
- security, privacy, tenant-isolation, reuse, supply-chain and engineering-language gates green;
- Development migration completed successfully;
- Development API readiness green;
- Development Web health green;
- affected authenticated core path exercised;
- affected worker/job path exercised when asynchronous behavior changed;
- affected media read/write path exercised when media behavior changed;
- manual acceptance completed where automated tests do not provide enough product confidence;
- exact candidate commit recorded before release tagging.

No individual failed gate is waived merely because Production appears healthy on
the previous revision.

## Development deployment procedure

For Arcane:

1. Use a dedicated Development project and `compose.arcane.yaml`.
2. Configure Development-only secrets and volumes.
3. Set `SBS_ENVIRONMENT=development` and `SBS_SOURCE_REF=main` or an explicit candidate ref.
4. Apply/update the project.
5. Confirm `migrate` completes successfully.
6. Confirm API and Web become healthy.
7. Record the deployed source ref/commit in the release notes or operator log.
8. Run the smoke suite below.
9. Run affected manual acceptance paths.

For a complete repository checkout, the same verification can be performed with
`compose.yaml`; the difference is only how the build context is supplied.

## Smoke verification

The smoke suite is deliberately small and non-destructive. Replace the example
origins with the relevant Development or Production values.

### Web and API

```bash
curl --fail https://dev.sidebyside.example/healthz
curl --fail https://dev.sidebyside.example/api/v1/health/ready
curl --fail https://dev.sidebyside.example/
```

Expected API readiness includes:

```json
{"status":"ok","database":"ok"}
```

### Compose state

On the deployment host or through the Arcane service view, verify:

- `migrate` exited successfully;
- `api` is healthy;
- `worker` is running;
- `web` is running/healthy as configured;
- `postgres` is healthy.

### Authentication and core read

Use a Development-only test account or the canonical fictional scenario:

1. authenticate through the configured Development auth path;
2. open an authorized Space;
3. load at least one core read surface such as Story/Memory;
4. verify no Production account or Production content is present.

### Worker path

If the release changes jobs or asynchronous behavior, exercise one safe
Development-only job and confirm it reaches its expected terminal state.

### Media path

If the release changes media behavior, upload/read/delete one Development-only
fixture through the normal Attachment/MediaStore flow. Do not test against
Production media from Development.

### Deployed revision

Arcane operators must retain the effective `SBS_SOURCE_REF` for every deployment.
For Production, the value must be an immutable tag or commit. Pair the tag with
its Git commit in release notes so the running source can be reconstructed
without relying on a floating branch.

## Release and Production promotion

After Development acceptance:

1. Resolve the exact candidate commit from `main`.
2. Confirm no newer `main` commit is being silently included in the candidate.
3. Create the release tag on the accepted commit.
4. Verify the tag resolves to that exact commit.
5. Update Production `SBS_SOURCE_REF` to the immutable tag.
6. Confirm Production has its own secrets, volumes and provider configuration.
7. Ensure required database backup prerequisites are satisfied for the migration risk.
8. Apply the Production deployment.
9. Require migration completion and API readiness.
10. Run the non-destructive smoke suite against Production.
11. Record the deployed tag/commit and the previous known-good tag/commit.

Production must not be promoted by changing Development's project into
Production or by reusing its volumes. Promotion changes the source revision of
the separate Production deployment.

## Rollback and recovery

Every Production deployment record must identify:

- the newly deployed release tag and commit;
- the previous known-good release tag and commit;
- whether the release contains schema migrations;
- whether those migrations are backward-compatible with the previous application revision;
- the backup/restore point required for a destructive recovery.

### Application-only rollback

If no incompatible schema/data migration occurred, set Production
`SBS_SOURCE_REF` back to the previous immutable release and recreate the affected
services. Run the full Production smoke suite afterwards.

### Migration-aware recovery

Do **not** automatically roll application code backward across an incompatible
migration.

Choose explicitly between:

- a safe Alembic downgrade that has been designed and tested;
- a forward fix on the current schema;
- restoring the required database/media backup and then redeploying the previous release.

The decision depends on the concrete migration and must be made before a
high-risk Production change, not improvised after failure.

## Exposure policy for Development

`SBS_ENVIRONMENT=development` has intentionally less production hardening and is
not a public deployment mode.

The persistent Development instance must therefore be one of:

- reachable only from a private/internal network;
- protected by reverse-proxy access control/VPN;
- otherwise explicitly security-reviewed before wider exposure.

Do not expose an unrestricted Development instance to the public Internet merely
because it has an HTTPS hostname.

## Secrets and configuration separation checklist

Before first Development and Production deployment, verify that each environment
has independent values for every applicable item:

- `POSTGRES_PASSWORD`;
- `SBS_CURSOR_SIGNING_KEY`;
- `SBS_BOOTSTRAP_TOKEN` while bootstrap is needed;
- SMTP credentials;
- OIDC client ID/secret and redirect URI;
- WebAuthn RP ID/origins;
- S3 bucket/prefix and credentials;
- external provider/API credentials;
- reverse-proxy hostnames and TLS configuration.

Never copy an entire Production `.env` into Development and then edit only the
hostname.

## Relationship to the public Demo

Demo exists to let visitors and testers experience canonical fictional product
data. It is deliberately isolated and periodically reset.

Development exists to prove that a source revision can migrate, start and behave
correctly before release.

Therefore:

- Demo may be useful evidence, but it does not replace Development verification;
- Development may use canonical demo fixtures without enabling public Demo mode;
- Demo and Development never share database/media volumes;
- neither may read Production data as a normal fixture source.

## Responsibilities

### CI owns

- deterministic repository tests;
- formatting/lint/type checks;
- migration/schema-drift checks;
- generated-client drift;
- security/privacy/reuse/supply-chain policy gates;
- build validation that can run without a persistent environment.

### Development owns

- real persistent migration execution;
- service startup/readiness together;
- integration with the deployed reverse-proxy/auth configuration;
- release-candidate smoke and targeted manual acceptance.

### Production promotion owns

- immutable revision selection;
- backup/risk check for migrations;
- deployment of one known revision;
- post-deploy health/smoke verification;
- recording current and previous known-good releases.

## Reuse-before-build decision

This workflow deliberately reuses Docker Compose, Arcane Git build contexts, the
existing migration service, health/readiness endpoints, repository CI and the
canonical demo tooling.

Alternatives considered:

- Kubernetes or another orchestrator: rejected; it adds an unrelated deployment platform.
- a custom release orchestrator: rejected; Arcane/Compose already provide the required deployment primitive.
- routine Production database clones: rejected for privacy and coupling reasons.
- floating `main` in Production: rejected because it is not reproducible.
- versioned registry images: potentially useful later for literal binary promotion, but not required to establish the v1 safety boundary.

No new runtime dependency, provider or product entitlement behavior is introduced.
