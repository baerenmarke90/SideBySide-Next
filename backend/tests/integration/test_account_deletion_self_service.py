"""Integration coverage for the public self-service Account-deletion boundary."""

from __future__ import annotations

from uuid import uuid4

from sqlalchemy import func, select

from sidebyside.auth import sessions
from sidebyside.config import Environment, get_settings
from sidebyside.core.clock import now
from sidebyside.identity import deletion_jobs, deletion_self_service
from sidebyside.identity.deletion_journal import DeletionJournal
from sidebyside.identity.deletion_models import (
    AccountDeletion,
    AccountDeletionStatus,
    DeletionConfirmationMailStatus,
)
from sidebyside.identity.models import Account, AccountEmail, DeviceSession
from sidebyside.jobs.models import Job, JobStatus
from sidebyside.jobs.worker import run_once
from sidebyside.mail import MailMessage, MailSender
from tests.conftest import auth, requires_database


class RecordingMailSender(MailSender):
    def __init__(self) -> None:
        self.messages: list[MailMessage] = []

    def send(self, message: MailMessage) -> None:
        self.messages.append(message)


def _account_with_session(maker):  # type: ignore[no-untyped-def]
    with maker() as session:
        account = Account(display_name="Delete Me")
        session.add(account)
        session.flush()
        session.add(
            AccountEmail(
                account_id=account.id,
                email="delete-me@example.org",
                is_primary=True,
                verified_at=now(),
            )
        )
        device_session, tokens = sessions.start_session(session, account)
        account_id = account.id
        device_session_id = device_session.id
        session.commit()
    return account_id, device_session_id, tokens.access_token


@requires_database
class TestSelfServiceAccountDeletion:
    def test_acceptance_is_fail_closed_and_worker_completes_without_client(
        self, production_client, tmp_path, monkeypatch  # type: ignore[no-untyped-def]
    ) -> None:
        client, maker = production_client
        account_id, device_session_id, token = _account_with_session(maker)
        journal = DeletionJournal.initialize(tmp_path / "deletions.journal", instance_id=uuid4())
        mail = RecordingMailSender()
        monkeypatch.setattr(deletion_self_service, "_configured_journal", lambda: journal)
        monkeypatch.setattr(deletion_self_service, "configured_mail_sender", lambda: mail)

        response = client.post(
            "/api/v1/account/deletion",
            headers=auth(token),
            json={"confirmation": "DELETE_ACCOUNT"},
        )

        assert response.status_code == 202
        assert response.json()["status"] == AccountDeletionStatus.PENDING.value
        assert len(mail.messages) == 1
        assert mail.messages[0].to == "delete-me@example.org"

        with maker() as session:
            account = session.get(Account, account_id)
            device_session = session.get(DeviceSession, device_session_id)
            deletion = session.get(AccountDeletion, account_id)
            assert account is not None and account.disabled_at is not None
            assert device_session is not None and device_session.revoked_at is not None
            assert deletion is not None
            assert deletion.confirmation_mail_status == DeletionConfirmationMailStatus.SENT.value
            assert session.execute(
                select(func.count()).select_from(Job).where(
                    Job.kind == deletion_jobs.CONVERGENCE_JOB,
                    Job.status == JobStatus.PENDING.value,
                )
            ).scalar_one() == 1

        # The client is no longer involved. The normal PostgreSQL worker owns
        # the remaining idempotent Core -> Media -> Async -> COMPLETED path.
        deletion_jobs.register_handlers()
        assert run_once("deletion-test-worker", limit=1) == 1

        with maker() as session:
            deletion = session.get(AccountDeletion, account_id)
            account = session.get(Account, account_id)
            assert deletion is not None
            assert deletion.status == AccountDeletionStatus.COMPLETED.value
            assert account is not None and account.disabled_at is not None
            assert session.execute(
                select(func.count()).select_from(AccountEmail).where(
                    AccountEmail.account_id == account_id
                )
            ).scalar_one() == 0
            assert session.execute(
                select(Job).where(Job.kind == deletion_jobs.CONVERGENCE_JOB)
            ).scalar_one().status == JobStatus.SUCCEEDED.value

    def test_demo_rejection_happens_before_tombstone_or_side_effects(
        self, production_client, tmp_path, monkeypatch  # type: ignore[no-untyped-def]
    ) -> None:
        client, maker = production_client
        account_id, device_session_id, token = _account_with_session(maker)
        journal_path = tmp_path / "must-not-exist.journal"
        base = get_settings()
        demo_settings = base.model_copy(
            update={"environment": Environment.DEMO, "demo_mode": True}
        )
        monkeypatch.setattr(deletion_self_service, "get_settings", lambda: demo_settings)

        def forbidden_authority() -> DeletionJournal:
            raise AssertionError("Demo rejection must happen before deletion authority access")

        monkeypatch.setattr(deletion_self_service, "_configured_journal", forbidden_authority)

        response = client.post(
            "/api/v1/account/deletion",
            headers=auth(token),
            json={"confirmation": "DELETE_ACCOUNT"},
        )

        assert response.status_code == 403
        assert response.json()["code"] == deletion_self_service.SelfDeletionErrorCode.DEMO_ACCOUNT
        assert not journal_path.exists()
        with maker() as session:
            account = session.get(Account, account_id)
            device_session = session.get(DeviceSession, device_session_id)
            assert account is not None and account.disabled_at is None
            assert device_session is not None and device_session.revoked_at is None
            assert session.get(AccountDeletion, account_id) is None
            assert session.execute(
                select(func.count()).select_from(Job).where(Job.kind == deletion_jobs.CONVERGENCE_JOB)
            ).scalar_one() == 0

    def test_confirmation_literal_is_required_before_authority_access(
        self, production_client, monkeypatch  # type: ignore[no-untyped-def]
    ) -> None:
        client, maker = production_client
        _, _, token = _account_with_session(maker)

        def forbidden_authority() -> DeletionJournal:
            raise AssertionError("Validation must happen before deletion authority access")

        monkeypatch.setattr(deletion_self_service, "_configured_journal", forbidden_authority)
        response = client.post(
            "/api/v1/account/deletion",
            headers=auth(token),
            json={"confirmation": "yes"},
        )
        assert response.status_code == 422
