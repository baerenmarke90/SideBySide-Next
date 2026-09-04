"""Restore-time replay of the forward-only Account deletion journal."""

from __future__ import annotations

import json
from datetime import timedelta
from pathlib import Path
from typing import Any
from uuid import UUID, uuid4

import pytest
from sqlalchemy import select
from sqlalchemy.orm import Session, sessionmaker

from sidebyside.auth import sessions
from sidebyside.authorization import PrivacyClass
from sidebyside.core.clock import now
from sidebyside.core.errors import UnauthenticatedError
from sidebyside.identity import deletion_reconciliation as reconciliation
from sidebyside.identity.deletion import (
    DELETED_ACCOUNT_DISPLAY_NAME,
    apply_accepted_tombstone,
)
from sidebyside.identity.deletion_journal import DeletionJournal, DeletionJournalError
from sidebyside.identity.deletion_models import AccountDeletion, AccountDeletionStatus
from sidebyside.identity.models import Account, AccountEmail
from sidebyside.memories.models import Memory, MemoryPayload
from sidebyside.private_notes.models import PrivateNote, PrivateNotePayload
from sidebyside.relationship.models import Membership, MembershipStatus
from sidebyside.relationship.service import add_member
from tests.conftest import make_account, make_space, requires_database

pytestmark = [pytest.mark.integration, requires_database]


def _journal(tmp_path: Path) -> DeletionJournal:
    return DeletionJournal.initialize(
        tmp_path / "account-deletions.v1.jsonl",
        instance_id=uuid4(),
    )


def _private_note(
    session: Session,
    *,
    owner_id: UUID,
    space_id: UUID,
    title: str,
) -> PrivateNote:
    note = PrivateNote(
        space_id=space_id,
        owner_id=owner_id,
        privacy_class=PrivacyClass.OWNER_ONLY.value,
        pinned=False,
        payload=PrivateNotePayload(title=title, body="private"),
    )
    session.add(note)
    session.flush()
    return note


def _maker(production_client: Any) -> sessionmaker[Session]:
    _, maker = production_client
    return maker


def test_reconciliation_replays_restored_account_and_converges(
    production_client: Any,
    tmp_path: Path,
) -> None:
    maker = _maker(production_client)
    with maker() as session:
        account = make_account(session, "Anna")
        partner = make_account(session, "Ben")
        space = make_space(session, account)
        add_member(session, space.id, partner)

        shared = Memory(
            space_id=space.id,
            owner_id=account.id,
            privacy_class=PrivacyClass.SPACE_SHARED.value,
            payload=MemoryPayload(title="Shared", body="survives restore reconciliation"),
        )
        session.add(shared)
        own_private = _private_note(
            session,
            owner_id=account.id,
            space_id=space.id,
            title="deleted owner's private row",
        )
        partner_private = _private_note(
            session,
            owner_id=partner.id,
            space_id=space.id,
            title="surviving partner private row",
        )
        session.add(
            AccountEmail(
                account_id=account.id,
                email="anna-reconcile@example.test",
                is_primary=True,
                verified_at=now(),
            )
        )
        _, issued = sessions.start_session(session, account, device_name="restored-device")
        session.flush()

        account_id = account.id
        space_id = space.id
        shared_id = shared.id
        own_private_id = own_private.id
        partner_private_id = partner_private.id
        access_token = issued.access_token
        session.commit()

    journal = _journal(tmp_path)
    accepted_at = now()
    journal.accept(account_id, accepted_at=accepted_at)

    result = reconciliation.reconcile_journal(journal)

    assert result.tombstones == 1
    assert result.present_accounts == 1
    assert result.absent_accounts == 0
    assert result.cleaned_accounts == 1

    with maker() as session:
        restored_account = session.get(Account, account_id)
        assert restored_account is not None
        assert restored_account.disabled_at == accepted_at
        assert restored_account.display_name == DELETED_ACCOUNT_DISPLAY_NAME
        assert not restored_account.is_active

        deletion = session.get(AccountDeletion, account_id)
        assert deletion is not None
        assert deletion.accepted_at == accepted_at
        assert deletion.status == AccountDeletionStatus.PENDING.value
        assert deletion.completed_at is None

        membership = session.execute(
            select(Membership).where(
                Membership.account_id == account_id,
                Membership.space_id == space_id,
            )
        ).scalar_one()
        assert membership.status == MembershipStatus.LEFT.value
        assert membership.ended_at == accepted_at

        assert session.get(Memory, shared_id) is not None
        assert session.get(PrivateNote, own_private_id) is None
        assert session.get(PrivateNote, partner_private_id) is not None
        assert (
            session.execute(
                select(AccountEmail).where(AccountEmail.account_id == account_id)
            ).scalar_one_or_none()
            is None
        )
        with pytest.raises(UnauthenticatedError):
            sessions.authenticate(session, access_token)

    repeated = reconciliation.reconcile_journal(journal)
    assert repeated == result


def test_journal_acceptance_timestamp_overrides_restored_partial_state(
    production_client: Any,
    tmp_path: Path,
) -> None:
    maker = _maker(production_client)
    journal_accepted_at = now()
    restored_accepted_at = journal_accepted_at + timedelta(hours=1)

    with maker() as session:
        account = make_account(session, "Anna")
        make_space(session, account)
        account_id = account.id
        deletion = apply_accepted_tombstone(
            session,
            account_id,
            accepted_at=restored_accepted_at,
        )
        assert deletion is not None
        session.commit()

    journal = _journal(tmp_path)
    journal.accept(account_id, accepted_at=journal_accepted_at)

    reconciliation.reconcile_journal(journal)

    with maker() as session:
        account = session.get(Account, account_id)
        deletion = session.get(AccountDeletion, account_id)
        assert account is not None
        assert deletion is not None
        assert deletion.accepted_at == journal_accepted_at
        assert account.disabled_at == journal_accepted_at


def test_cleanup_failure_cannot_reactivate_or_block_later_tombstones(
    production_client: Any,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    maker = _maker(production_client)
    with maker() as session:
        first = make_account(session, "First")
        second = make_account(session, "Second")
        make_space(session, first)
        make_space(session, second)
        _, first_issued = sessions.start_session(session, first)
        _, second_issued = sessions.start_session(session, second)
        session.flush()
        first_id = first.id
        second_id = second.id
        first_token = first_issued.access_token
        second_token = second_issued.access_token
        session.commit()

    journal = _journal(tmp_path)
    accepted_at = now()
    journal.accept(first_id, accepted_at=accepted_at)
    journal.accept(second_id, accepted_at=accepted_at + timedelta(microseconds=1))

    original_cleanup = reconciliation.apply_core_cleanup

    def fail_first_cleanup(session: Session, account_id: UUID) -> AccountDeletion | None:
        if account_id == first_id:
            raise RuntimeError("synthetic cleanup detail that must not reach persisted state")
        return original_cleanup(session, account_id)

    monkeypatch.setattr(reconciliation, "apply_core_cleanup", fail_first_cleanup)

    with pytest.raises(reconciliation.DeletionReconciliationError) as captured:
        reconciliation.reconcile_journal(journal)

    error = captured.value
    assert error.fail_closed_failures == 0
    assert error.cleanup_failures == 1
    assert error.failure_record_failures == 0
    assert str(first_id) not in str(error)
    assert str(second_id) not in str(error)
    assert "synthetic cleanup detail" not in str(error)

    with maker() as session:
        first_account = session.get(Account, first_id)
        second_account = session.get(Account, second_id)
        assert first_account is not None
        assert second_account is not None
        assert first_account.disabled_at == accepted_at
        assert second_account.disabled_at == accepted_at + timedelta(microseconds=1)
        assert second_account.display_name == DELETED_ACCOUNT_DISPLAY_NAME

        first_deletion = session.get(AccountDeletion, first_id)
        second_deletion = session.get(AccountDeletion, second_id)
        assert first_deletion is not None
        assert second_deletion is not None
        assert first_deletion.status == AccountDeletionStatus.FAILED.value
        assert first_deletion.last_failure_code == "RECONCILIATION_CLEANUP_FAILED"
        assert second_deletion.status == AccountDeletionStatus.PENDING.value

        with pytest.raises(UnauthenticatedError):
            sessions.authenticate(session, first_token)
        with pytest.raises(UnauthenticatedError):
            sessions.authenticate(session, second_token)


def test_invalid_journal_is_rejected_before_database_replay(
    production_client: Any,
    tmp_path: Path,
) -> None:
    maker = _maker(production_client)
    with maker() as session:
        account = make_account(session, "Anna")
        make_space(session, account)
        account_id = account.id
        session.commit()

    journal = _journal(tmp_path)
    journal.accept(account_id, accepted_at=now())

    lines = journal.path.read_text(encoding="utf-8").splitlines()
    record = json.loads(lines[1])
    record["accountId"] = str(uuid4())
    journal.path.write_text(
        lines[0] + "\n" + json.dumps(record, sort_keys=True, separators=(",", ":")) + "\n",
        encoding="utf-8",
    )

    with pytest.raises(DeletionJournalError):
        reconciliation.reconcile_journal(journal)

    with maker() as session:
        restored_account = session.get(Account, account_id)
        assert restored_account is not None
        assert restored_account.is_active
        assert session.get(AccountDeletion, account_id) is None


def test_missing_account_tombstone_is_an_idempotent_noop(
    production_client: Any,
    tmp_path: Path,
) -> None:
    _maker(production_client)
    journal = _journal(tmp_path)
    journal.accept(uuid4(), accepted_at=now())

    result = reconciliation.reconcile_journal(journal)

    assert result.tombstones == 1
    assert result.present_accounts == 0
    assert result.absent_accounts == 1
    assert result.cleaned_accounts == 0
