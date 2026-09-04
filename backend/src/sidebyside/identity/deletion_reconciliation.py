"""Restore-time replay of the forward-only Account deletion journal.

A point-in-time database restore can predate an already accepted Account
deletion. Reconciliation therefore replays the external tombstone authority in
two phases:

1. every surviving Account referenced by the journal is made fail-closed and
   that transaction is committed independently;
2. directly readable private/authentication state is cleaned up in a second
   transaction per Account.

The phase split is deliberate. A cleanup defect for one tombstone must never
prevent later tombstones from losing authentication and Space access before
normal traffic is allowed to resume.
"""

from __future__ import annotations

from dataclasses import dataclass

from sidebyside.db.session import unit_of_work
from sidebyside.identity.deletion import (
    apply_accepted_tombstone,
    apply_core_cleanup,
    mark_deletion_failed,
)
from sidebyside.identity.deletion_journal import DeletionJournal, DeletionTombstone

_RECONCILIATION_FAILURE_CODE = "RECONCILIATION_CLEANUP_FAILED"


@dataclass(frozen=True, slots=True)
class DeletionReconciliationResult:
    """PII-free reconciliation counters suitable for operational reporting."""

    tombstones: int
    present_accounts: int
    absent_accounts: int
    cleaned_accounts: int


class DeletionReconciliationError(RuntimeError):
    """One or more journal tombstones could not be safely reconciled."""

    def __init__(
        self,
        *,
        fail_closed_failures: int,
        cleanup_failures: int,
        failure_record_failures: int,
    ) -> None:
        self.fail_closed_failures = fail_closed_failures
        self.cleanup_failures = cleanup_failures
        self.failure_record_failures = failure_record_failures
        super().__init__(
            "Account deletion reconciliation did not converge: "
            f"fail_closed_failures={fail_closed_failures}, "
            f"cleanup_failures={cleanup_failures}, "
            f"failure_record_failures={failure_record_failures}."
        )


def _apply_fail_closed(tombstone: DeletionTombstone) -> bool:
    """Commit one tombstone's fail-closed DB phase and report Account presence."""
    with unit_of_work() as session:
        deletion = apply_accepted_tombstone(
            session,
            tombstone.account_id,
            accepted_at=tombstone.accepted_at,
        )
        return deletion is not None


def _apply_cleanup(tombstone: DeletionTombstone) -> bool:
    """Commit one tombstone's directly readable private/auth cleanup phase."""
    with unit_of_work() as session:
        deletion = apply_core_cleanup(session, tombstone.account_id)
        return deletion is not None


def _record_cleanup_failure(tombstone: DeletionTombstone) -> None:
    """Persist only a bounded technical failure code after fail-closed commit."""
    with unit_of_work() as session:
        mark_deletion_failed(
            session,
            tombstone.account_id,
            failure_code=_RECONCILIATION_FAILURE_CODE,
        )


def reconcile_journal(journal: DeletionJournal) -> DeletionReconciliationResult:
    """Replay every validated tombstone before restored traffic may resume.

    Journal validation completes before the first database mutation. Then all
    tombstones receive their independent fail-closed transaction before any
    slower cleanup starts. Per-record failures are collected so one bad record
    cannot leave later deleted Accounts active merely because the batch aborted
    early.

    The caller must treat :class:`DeletionReconciliationError` as a startup /
    restore gate failure. Successful core cleanup intentionally leaves the
    overall lifecycle ``PENDING`` until #520's media and asynchronous-work
    cleanup paths have also converged.
    """
    tombstones = journal.read_all()
    cleanup_candidates: list[DeletionTombstone] = []
    present_accounts = 0
    absent_accounts = 0
    fail_closed_failures = 0

    # Phase 1: make every restorable Account unusable first. Each successful
    # transaction commits before the next tombstone is attempted.
    for tombstone in tombstones:
        try:
            account_present = _apply_fail_closed(tombstone)
        except Exception:
            fail_closed_failures += 1
            continue

        if account_present:
            present_accounts += 1
            cleanup_candidates.append(tombstone)
        else:
            absent_accounts += 1

    # Phase 2: remove directly readable private/auth state. A failure here does
    # not undo the already committed fail-closed phase.
    cleanup_failures = 0
    failure_record_failures = 0
    cleaned_accounts = 0
    for tombstone in cleanup_candidates:
        try:
            account_present = _apply_cleanup(tombstone)
        except Exception:
            cleanup_failures += 1
            try:
                _record_cleanup_failure(tombstone)
            except Exception:
                failure_record_failures += 1
            continue

        if account_present:
            cleaned_accounts += 1

    if fail_closed_failures or cleanup_failures or failure_record_failures:
        raise DeletionReconciliationError(
            fail_closed_failures=fail_closed_failures,
            cleanup_failures=cleanup_failures,
            failure_record_failures=failure_record_failures,
        )

    return DeletionReconciliationResult(
        tombstones=len(tombstones),
        present_accounts=present_accounts,
        absent_accounts=absent_accounts,
        cleaned_accounts=cleaned_accounts,
    )
