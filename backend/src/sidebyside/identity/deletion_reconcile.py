"""Replay forward Account-deletion tombstones into the current database state."""

from __future__ import annotations

import argparse
from pathlib import Path
from uuid import UUID

from sidebyside.db.session import unit_of_work
from sidebyside.identity.deletion import apply_accepted_tombstone, apply_core_cleanup
from sidebyside.identity.deletion_journal import DeletionJournalError, load_tombstones


def reconcile(journal_path: Path, *, instance_id: UUID) -> int:
    """Re-apply accepted deletions in the required fail-closed transaction order."""
    tombstones = load_tombstones(journal_path, expected_instance_id=instance_id)
    for tombstone in tombstones:
        # The fail-closed phase is committed independently so a later cleanup
        # failure can never reactivate an Account restored from an older backup.
        with unit_of_work() as session:
            apply_accepted_tombstone(
                session,
                tombstone.account_id,
                accepted_at=tombstone.accepted_at,
            )
        with unit_of_work() as session:
            apply_core_cleanup(session, tombstone.account_id)
    return len(tombstones)


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Re-apply the protected Account-deletion reconciliation journal "
            "before API or worker traffic resumes."
        )
    )
    parser.add_argument("--journal", type=Path, required=True)
    parser.add_argument(
        "--confirm-instance-id",
        type=UUID,
        required=True,
        help="Stable instance UUID expected in every journal record",
    )
    return parser


def main() -> int:
    args = _parser().parse_args()
    try:
        count = reconcile(args.journal, instance_id=args.confirm_instance_id)
    except DeletionJournalError as exc:
        # Journal errors are intentionally bounded and contain neither record
        # payloads nor identifiers.
        print(f"Account deletion reconciliation failed: {exc}")
        return 1
    print(f"Account deletion core reconciliation completed for {count} tombstone(s).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
