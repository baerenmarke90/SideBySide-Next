# Self-Hosted Account-deletion authority

**Status:** binding operational supplement to `SELF-HOSTED-RECOVERY.md`

**Related:** #520, #644, #190

SideBySide Account deletion uses a forward-only deletion journal outside the
point-in-time PostgreSQL backup. That separation is intentional: restoring a
database backup created before an accepted deletion must never resurrect the
Account, its credentials, sessions, or `OWNER_ONLY` data.

## 1. Two independent identities

A normal Self-Hosted instance needs one stable deletion-authority UUID:

```bash
python3 -c 'import uuid; print(uuid.uuid4())'
```

Store the resulting value as:

```dotenv
SBS_ACCOUNT_DELETION_INSTANCE_ID=<stable-instance-uuid>
```

Generate it once per installation. Keep it stable across application upgrades,
container recreation, and database/media restores. Development and Production
must use different values. Do not derive it from an Account ID, Space ID,
database credential, hostname, or another secret.

The UUID is not a credential, but it is part of the recovery identity and belongs
in the protected operator configuration backup. A journal from another instance
must not be accepted merely because its format is valid.

## 2. The forward-only journal is a separate recovery unit

Canonical Compose mounts the private named volume:

```text
deletion_journal_data -> /var/lib/sidebyside/deletion-journal
```

The journal file is:

```text
/var/lib/sidebyside/deletion-journal/account-deletions.journal
```

This unit is deliberately separate from:

- PostgreSQL;
- `LocalMediaStore` / S3 objects;
- ordinary application configuration and secrets.

It must never be treated as a point-in-time data snapshot that may be rolled back
together with PostgreSQL. Once a tombstone has been accepted, every recovery
point that can still restore older application data must remain paired with a
journal state at least as new as that tombstone.

Use operator-controlled backup/versioning that preserves the newest validated
journal. Do not replace a newer journal with an older backup. Retain the forward
journal until every database/media backup from before the represented deletions
has expired and can no longer be restored.

## 3. Live acceptance ordering

The public self-service API follows one fixed order:

1. reject Demo mode and validate the authenticated caller;
2. append/fsync or idempotently read the forward tombstone;
3. commit fail-closed Account/session state plus one PostgreSQL convergence job;
4. attempt one best-effort confirmation mail;
5. let the normal worker converge Core -> Media -> Async -> `COMPLETED`.

The client may disconnect after step 3. Deletion no longer depends on Web or
Android remaining open.

There is an unavoidable process-crash boundary between the filesystem fsync and
the PostgreSQL commit. API startup therefore validates/replays the configured
journal before normal traffic is served. If the journal exists but the matching
instance UUID is unavailable, startup fails closed rather than serving stale
credentials.

## 4. Backup rules

The ordinary `scripts/self_hosted_recovery.py backup` archive intentionally
contains PostgreSQL plus durable local media only. It does **not** absorb the
forward journal, because doing so would make a later restore capable of rolling
accepted deletions backwards.

Protect these recovery units independently:

1. PostgreSQL + durable local media through the coordinated SideBySide recovery
   archive;
2. the newest forward deletion journal through an operator-controlled protected
   copy/versioned store;
3. configuration/secrets, including the stable
   `SBS_ACCOUNT_DELETION_INSTANCE_ID`, through the operator secret/config backup.

For S3 media, follow the provider-specific consistency boundary in
`SELF-HOSTED-RECOVERY.md`; the forward deletion journal remains independent of the
object-store snapshot.

## 5. Restoring an older application backup

Normal API/worker traffic must remain stopped while an old backup is restored.
After PostgreSQL/media restoration, replay the newest protected journal before
starting writers:

```bash
SBS_RECOVERY_PROJECT=$(
  docker compose --env-file .env -f compose.yaml config --format json |
    python3 -c 'import json, sys; print(json.load(sys.stdin)["name"])'
)

python3 scripts/self_hosted_deletion_reconcile.py \
  --compose-file compose.yaml \
  --env-file .env \
  --confirm-project "$SBS_RECOVERY_PROJECT" \
  --journal /secure/path/account-deletions.journal \
  --confirm-instance-id "$SBS_ACCOUNT_DELETION_INSTANCE_ID"
```

For Arcane use `compose.arcane.yaml` consistently.

The command:

- refuses to run while API, worker, migration, or Demo initialization writers are
  active;
- migrates the restored database to the current schema;
- validates the complete forward journal and exact instance UUID;
- replays deletion convergence before normal traffic may resume;
- leaves writers stopped so the rest of the recovery verification can finish.

Only after successful reconciliation, readiness/revision checks, and the remaining
`SELF-HOSTED-RECOVERY.md` acceptance steps may API and worker resume.

## 6. Destructive operator actions

Treat the deletion journal volume as deletion-safety state, not disposable cache.
In particular:

- `docker compose down -v` destroys the named journal volume along with other
  volumes and is unsafe while any pre-deletion backup remains restorable;
- recreating only the API container is safe because the named volume persists;
- changing `COMPOSE_PROJECT_NAME` creates a different named volume and therefore
  requires an explicit migration/recovery decision;
- moving to a new host requires transferring the newest journal and the matching
  instance UUID before the target may accept or reconcile deletions;
- never edit, truncate, compact, or hand-rewrite journal records to repair a
  recovery. Validation failures are fail-closed and require investigation.

## 7. Demo deployments

Demo Accounts cannot invoke self-service Account deletion. The server rejects Demo
mode before journal access or any irreversible side effect. A public Demo therefore
does not need a deletion-authority UUID solely for Demo Account deletion.

Do not weaken this by assigning Demo-user email/name heuristics or by sharing the
normal Production deletion journal with the Demo deployment.
