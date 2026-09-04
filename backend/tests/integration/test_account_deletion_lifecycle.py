"""Terminal orchestration for the server-authoritative Account deletion lifecycle."""

from __future__ import annotations

from uuid import UUID

import pytest
from sqlalchemy.orm import Session

from sidebyside.core.clock import now
from sidebyside.identity import deletion_lifecycle
from sidebyside.identity.deletion import mark_deletion_failed
from sidebyside.identity.deletion_lifecycle import (
    DeletionMediaCleanupError,
    converge_accepted_deletion,
)
from sidebyside.identity.deletion_media import (
    MEDIA_CLEANUP_FAILURE_CODE,
    AccountMediaCleanupResult,
)
from sidebyside.identity.deletion_models import AccountDeletion, AccountDeletionStatus
from sidebyside.identity.models import Account
from tests.conftest import make_account, make_space, requires_database

pytestmark = [pytest.mark.integration, requires_database]


def _setup_account(maker) -> UUID:  # type: ignore[no-untyped-def]
    with maker() as setup, setup.begin():
        account = make_account(setup, "Anna")
        make_space(setup, account)
        return account.id


def test_full_deletion_convergence_marks_completed_once(production_client) -> None:  # type: ignore[no-untyped-def]
    _, maker = production_client
    account_id = _setup_account(maker)
    accepted_at = now()

    converge_accepted_deletion(account_id, accepted_at=accepted_at)

    with maker() as verify:
        account = verify.get(Account, account_id)
        deletion = verify.get(AccountDeletion, account_id)
        assert account is not None and account.disabled_at == accepted_at
        assert deletion is not None
        assert deletion.status == AccountDeletionStatus.COMPLETED.value
        assert deletion.completed_at is not None
        assert deletion.failed_at is None
        assert deletion.last_failure_code is None
        first_completed_at = deletion.completed_at

    converge_accepted_deletion(account_id, accepted_at=accepted_at)

    with maker() as verify:
        deletion = verify.get(AccountDeletion, account_id)
        assert deletion is not None
        assert deletion.status == AccountDeletionStatus.COMPLETED.value
        assert deletion.completed_at == first_completed_at


def test_failed_phase_cannot_complete_and_retry_converges(
    production_client,
    monkeypatch: pytest.MonkeyPatch,
) -> None:  # type: ignore[no-untyped-def]
    _, maker = production_client
    account_id = _setup_account(maker)
    accepted_at = now()
    attempts = 0

    def fail_media_once(session: Session, target_id) -> AccountMediaCleanupResult:  # type: ignore[no-untyped-def]
        nonlocal attempts
        attempts += 1
        if attempts == 1:
            mark_deletion_failed(
                session,
                target_id,
                failure_code=MEDIA_CLEANUP_FAILURE_CODE,
            )
            return AccountMediaCleanupResult(purge_failures=1)
        return AccountMediaCleanupResult()

    monkeypatch.setattr(
        deletion_lifecycle,
        "apply_account_media_cleanup",
        fail_media_once,
    )

    with pytest.raises(DeletionMediaCleanupError):
        converge_accepted_deletion(account_id, accepted_at=accepted_at)

    with maker() as verify:
        account = verify.get(Account, account_id)
        deletion = verify.get(AccountDeletion, account_id)
        assert account is not None and account.disabled_at == accepted_at
        assert deletion is not None
        assert deletion.status == AccountDeletionStatus.FAILED.value
        assert deletion.completed_at is None
        assert deletion.last_failure_code == MEDIA_CLEANUP_FAILURE_CODE

    converge_accepted_deletion(account_id, accepted_at=accepted_at)

    with maker() as verify:
        deletion = verify.get(AccountDeletion, account_id)
        assert deletion is not None
        assert deletion.status == AccountDeletionStatus.COMPLETED.value
        assert deletion.completed_at is not None
        assert deletion.failed_at is None
        assert deletion.last_failure_code is None
