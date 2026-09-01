# Self-Hosted Backup, Restore, and Upgrade

**Status:** authoritative operator contract for the canonical Compose deployments

**Scope:** PostgreSQL 17 plus `LocalMediaStore`; S3 boundary documented separately

**Related:** #190, #375, `SELF-HOSTING.md`, `DEVELOPMENT-AND-RELEASE-ENVIRONMENTS.md`

This runbook covers operational recovery of a complete SideBySide Self-Hosted
instance. It is separate from the user-facing Transfer Bundle: a Transfer Bundle
is scoped, portable product data, while an operational backup contains the whole
instance and preserves authentication, tenant, ownership, privacy, and internal
state.

## 1. Recovery contract

A recoverable instance consists of three independently protected units:

| Unit | Backup mechanism | Included in the recovery archive |
|---|---|---|
| PostgreSQL | PostgreSQL 17 `pg_dump --format=custom`; restored with `pg_restore --single-transaction` | yes |
| `LocalMediaStore` | exact durable object set from the private Compose `media_data` volume | yes |
| configuration and secrets | operator secret/configuration backup | no |

The archive contains every PostgreSQL row. This includes all accounts, tenants,
memberships, owner-only content, sessions, jobs, and other internal state. The media
part contains only `READY` attachments with a durable product binding: a Memory,
Heart Moment, or account profile attachment. It includes each required original
and declared thumbnail. Temporary or unbound upload objects are deliberately
excluded; their database lifecycle state may remain and normal cleanup may expire
it after recovery.

The helper quiesces the normal writers by stopping API and worker, takes the
database dump, resolves the durable media set from that stable database, archives
exactly that set, and restarts only the writer services that were running before
the operation. It rejects a running migration/demo initialization, a missing media
object, a non-local media adapter, an unexpected Compose project, or an existing
output file.

The outer tar archive has exactly three regular members:

- `manifest.json`, including format version, source Alembic revision, object
  count, and SHA-256 checksums;
- `database.dump`, in PostgreSQL custom format;
- `media.tar`, containing only validated generated storage paths.

The archive is created atomically with mode `0600`. It is still a complete copy of
highly sensitive relationship data. Encrypt it before off-host transfer, limit
access, define retention, and test deletion. SideBySide does not log archive
content, database errors with bound values, credentials, or protected payloads.

## 2. Configuration and secret backup

Back up the following through the hoster's secret/configuration system, separately
from the data archive:

- the untracked `.env` or equivalent secret-manager entries;
- PostgreSQL credentials and the stable cursor signing key;
- mail, OIDC, WebAuthn, S3, and other provider configuration/credentials in use;
- the Compose project name and public origin;
- reverse-proxy, TLS, DNS, firewall, and scheduler configuration;
- the exact deployed commit SHA and SideBySide Compose variant;
- any external backup encryption keys and restore instructions.

Do not place this material inside the SideBySide archive. Do not store the archive
next to an unencrypted copy of its decryption key. The one-time bootstrap token is
normally absent after initial registration and must not be restored as a permanent
credential.

## 3. Create a coordinated backup

Run from a complete repository checkout containing the deployed recovery helper.
The environment file must identify the actual project through
`COMPOSE_PROJECT_NAME`. Create the destination directory with operator-only
permissions first.

```bash
install -d -m 0700 /srv/sidebyside-backups

SBS_RECOVERY_PROJECT=$(
  docker compose --env-file .env -f compose.yaml config --format json |
    python3 -c 'import json, sys; print(json.load(sys.stdin)["name"])'
)
SBS_RECOVERY_ARCHIVE="/srv/sidebyside-backups/sidebyside-$(date -u +%Y%m%dT%H%M%SZ).tar"

python3 scripts/self_hosted_recovery.py backup \
  --compose-file compose.yaml \
  --env-file .env \
  --confirm-project "$SBS_RECOVERY_PROJECT" \
  --output "$SBS_RECOVERY_ARCHIVE"
```

Use `compose.arcane.yaml` in both commands for an Arcane deployment. Keep the
maintenance interval free of other database writers, including direct operator
sessions. API and worker are unavailable while the stable snapshot is created.

The command's successful exit proves archive structure, source revision capture,
and component checksums at creation time. It does not prove the offsite copy,
retention policy, encryption-key recovery, storage durability, or a later restore.
Copy the archive through an operator-selected encrypted backup path and verify the
result there. Established tools such as restic or rclone may provide encryption,
retention, and remote transport; they are an operator layer and not a new
SideBySide runtime dependency.

## 4. Restore into a fresh target

Restore only into a new Compose project with an empty PostgreSQL database and
empty `media_data` volume. Recover the target configuration/secrets separately,
check out the intended immutable SideBySide revision, and place the archive on the
host with restrictive permissions.

```bash
# In the clean target checkout, with the separately recovered .env in place:
docker compose --env-file .env -f compose.yaml \
  up -d --wait --wait-timeout 120 postgres

SBS_RECOVERY_PROJECT=$(
  docker compose --env-file .env -f compose.yaml config --format json |
    python3 -c 'import json, sys; print(json.load(sys.stdin)["name"])'
)
SBS_RECOVERY_ARCHIVE=/srv/sidebyside-backups/sidebyside-YYYYmmddTHHMMSSZ.tar

python3 scripts/self_hosted_recovery.py restore \
  --compose-file compose.yaml \
  --env-file .env \
  --confirm-project "$SBS_RECOVERY_PROJECT" \
  --archive "$SBS_RECOVERY_ARCHIVE" \
  --confirm-empty-target
```

The explicit project and empty-target confirmations are safety barriers, not
convenience flags. Restore validates the exact member set, checksums, media object
count, regular-file-only storage paths, an empty database, an empty media volume,
the restored file set, and the restored Alembic revision. API and worker must not
be running.

After restore, migrate first with the verified candidate and only then start the
application:

```bash
CANDIDATE=$(git rev-parse HEAD)

python3 scripts/compose_checked.py \
  --expected-revision "$CANDIDATE" \
  run --rm migrate alembic upgrade head

python3 scripts/compose_checked.py \
  --expected-revision "$CANDIDATE" \
  up -d --build --force-recreate --wait --wait-timeout 300

python3 scripts/deployment_smoke.py \
  --base-url https://sidebyside.example \
  --expected-revision "$CANDIDATE"
```

For Arcane, pin `SBS_SOURCE_REF` to the exact candidate SHA, run the migration,
recreate the complete stack, and perform the same revision-aware smoke check.

Also verify an authenticated shared-content read and an owner-only content path
with fictional operator accounts appropriate for the target. A restore is accepted
only when database readiness, tenant/owner assignments, privacy behavior, media
bytes, and both application revision identities are correct.

If restore fails after writing either target, keep API/worker stopped. Discard only
the explicitly confirmed fresh target project's database and media volumes, fix the
cause, and repeat from a verified archive. Do not attempt to merge a partial
restore with existing data.

## 5. Upgrade and rollforward

Before every Production upgrade:

1. record the current and candidate commit SHAs;
2. create a coordinated backup and protect its separate configuration/secret set;
3. retain the previous known-good application revision;
4. know the migrations between both revisions and whether old code remains
   compatible with the post-migration schema;
5. verify the candidate and migrations in persistent Development;
6. apply Alembic before starting API/worker;
7. require readiness, revision parity, authenticated reads, and affected media/job
   acceptance before declaring success.

The repository gate executes a reproducible prior-schema exercise from Alembic
revision `0032` (the delivered final M4 schema), seeds tenant, owner-only, shared,
authentication, and local-media state, migrates to the current head, and verifies
the current application. It also creates a current-schema backup, destroys the
source volumes, restores into fresh volumes, and repeats the integrity and
authorization checks. Run it locally with:

```bash
python3 scripts/self_hosted_recovery_acceptance.py
```

This CI baseline proves the maintained migration chain, not every historical
binary, database size, host filesystem, proxy, or provider. Large installations
must additionally measure their maintenance window and restore time on
representative infrastructure.

Alembic rollforward is the default recovery strategy. If application startup fails
after a compatible migration, prefer a forward fix. Never assume that checking out
old application code reverses schema changes. For an incompatible failed upgrade,
use only one explicitly reviewed path:

- a tested corrective forward migration and compatible application;
- a separately tested downgrade migration; or
- discard the failed target, restore the verified pre-upgrade archive, and deploy
  the previous compatible immutable revision.

## 6. S3/object-storage boundary

`scripts/self_hosted_recovery.py` intentionally rejects `SBS_MEDIA_STORE=s3`.
There is no provider-neutral mechanism that can promise one atomic snapshot across
PostgreSQL and every S3-compatible provider.

An S3-backed operator must establish a provider-specific coordinated procedure:

1. quiesce API, worker, migrations, and all other writers;
2. create the PostgreSQL custom dump;
3. create or identify an immutable/versioned object-store snapshot for the same
   quiesced point;
4. preserve bucket/prefix, version identifiers, region/endpoint configuration,
   credentials, encryption keys, retention, and deletion policy separately;
5. restore database and objects into an isolated target before starting writers;
6. verify database references, exact media availability, tenant/privacy behavior,
   readiness, and application revision.

Bucket replication alone is not database consistency. A database-only backup is
not media recovery. Object versioning alone is not a tested restore. Provider
snapshots, managed database backups, cross-region replication, retention, cost,
and support remain hoster/operator responsibilities until a separately reviewed
provider-specific implementation exists.

## 7. CI and release evidence

`.github/workflows/self-hosted-recovery.yml` is the repository recovery gate. It
runs for relevant Compose, backend, migration, recovery-tooling, and runbook
changes, and on every push to `main` or manual invocation. It proves:

- archive format and tamper/path-traversal rejection;
- PostgreSQL and durable LocalMediaStore backup consistency;
- destruction of the source followed by restore into fresh volumes;
- exact durable media and exclusion of temporary/unbound media;
- account, tenant, membership, owner, shared, and owner-only invariants;
- authorization behavior through the current HTTP API;
- API/database/Web readiness and backend/Web revision parity after restore;
- rollforward from the reproducible prior schema to the current Alembic head.

CI uses only generated fictional data and a randomly named disposable Compose
project. Its cleanup is scoped to that project. CI does not prove the operator's
real offsite archive, secrets, S3/provider snapshot, encryption-key custody,
retention, hardware capacity, or actual Production restore time; those require a
recorded infrastructure exercise.
