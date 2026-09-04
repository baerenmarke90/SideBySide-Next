"""Self-service Account-deletion acceptance and confirmation-mail boundary.

The public API may accept only the authenticated Account. Irreversible acceptance
belongs to the forward-only deletion journal; the database fail-closed phase and
background convergence job are committed immediately afterwards. Confirmation
mail is deliberately best effort and never owns deletion success.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from uuid import UUID

from pydantic_settings import BaseSettings, SettingsConfigDict
from sqlalchemy import select

from sidebyside.config import Environment, get_settings
from sidebyside.core.clock import now
from sidebyside.core.errors import ForbiddenError, ServiceUnavailableError
from sidebyside.db.session import unit_of_work
from sidebyside.identity.deletion import apply_accepted_tombstone
from sidebyside.identity.deletion_jobs import enqueue_convergence
from sidebyside.identity.deletion_journal import DeletionJournal, DeletionJournalError
from sidebyside.identity.deletion_models import (
    AccountDeletion,
    AccountDeletionStatus,
    DeletionConfirmationMailStatus,
)
from sidebyside.identity.models import Account, AccountEmail
from sidebyside.mail import (
    MailMessage,
    MailSender,
    MailTransportError,
    MailUnavailableError,
    sender as configured_mail_sender,
)

log = logging.getLogger(__name__)


class SelfDeletionErrorCode:
    DEMO_ACCOUNT = "ACCOUNT_DELETION_DEMO_FORBIDDEN"
    AUTHORITY_UNAVAILABLE = "ACCOUNT_DELETION_AUTHORITY_UNAVAILABLE"
    ACCOUNT_UNAVAILABLE = "ACCOUNT_DELETION_ACCOUNT_UNAVAILABLE"


class DeletionAuthoritySettings(BaseSettings):
    """Deployment adapter for the independently protected deletion journal."""

    model_config = SettingsConfigDict(
        env_prefix="SBS_ACCOUNT_DELETION_",
        env_file=".env",
        extra="ignore",
    )

    journal_path: Path = Path(
        "/var/lib/sidebyside/deletion-journal/account-deletions.journal"
    )
    instance_id: UUID | None = None


@dataclass(frozen=True, slots=True)
class AcceptedSelfDeletion:
    accepted_at: datetime
    status: AccountDeletionStatus


def _authority_unavailable() -> ServiceUnavailableError:
    return ServiceUnavailableError(
        "Account deletion is unavailable because the protected deletion authority "
        "is not configured or cannot be validated.",
        SelfDeletionErrorCode.AUTHORITY_UNAVAILABLE,
    )


def _configured_journal() -> DeletionJournal:
    authority = DeletionAuthoritySettings()
    if authority.instance_id is None:
        raise _authority_unavailable()

    path = authority.journal_path
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        if not path.exists():
            try:
                journal = DeletionJournal.initialize(path, instance_id=authority.instance_id)
            except DeletionJournalError:
                # A concurrent request may have created the same journal after
                # the existence check. Validate the resulting file before use.
                journal = DeletionJournal(path, instance_id=authority.instance_id)
        else:
            journal = DeletionJournal(path, instance_id=authority.instance_id)
        journal.read_all()
        return journal
    except (DeletionJournalError, OSError) as exc:
        raise _authority_unavailable() from exc


def _preflight(account_id: UUID) -> str | None:
    """Reject Demo self-delete and snapshot only a verified primary address."""
    settings = get_settings()
    if settings.environment is Environment.DEMO or settings.demo_mode:
        raise ForbiddenError(
            "Demo Accounts are managed by the Demo environment and cannot be deleted "
            "through the self-service Account flow.",
            SelfDeletionErrorCode.DEMO_ACCOUNT,
        )

    with unit_of_work() as session:
        account = session.get(Account, account_id)
        if account is None or account.disabled_at is not None:
            raise ForbiddenError(
                "This Account cannot start a new self-service deletion request.",
                SelfDeletionErrorCode.ACCOUNT_UNAVAILABLE,
            )
        return session.execute(
            select(AccountEmail.email).where(
                AccountEmail.account_id == account_id,
                AccountEmail.is_primary.is_(True),
                AccountEmail.verified_at.is_not(None),
            )
        ).scalar_one_or_none()


def _claim_confirmation_mail(
    deletion: AccountDeletion,
    *,
    primary_email: str | None,
) -> bool:
    """Claim at most one confirmation attempt without retaining the address."""
    if deletion.confirmation_mail_attempted_at is not None:
        return False

    deletion.confirmation_mail_attempted_at = now()
    if primary_email is None:
        deletion.confirmation_mail_status = (
            DeletionConfirmationMailStatus.NO_VERIFIED_PRIMARY.value
        )
        return False

    # Commit the claim before touching a provider. A crash may therefore omit a
    # best-effort confirmation, but it cannot create duplicate mail on retry.
    deletion.confirmation_mail_status = DeletionConfirmationMailStatus.CLAIMED.value
    return True


def _record_confirmation_mail_result(
    account_id: UUID,
    result: DeletionConfirmationMailStatus,
) -> None:
    with unit_of_work() as session:
        deletion = session.execute(
            select(AccountDeletion)
            .where(AccountDeletion.account_id == account_id)
            .with_for_update()
        ).scalar_one_or_none()
        if (
            deletion is not None
            and deletion.confirmation_mail_status
            == DeletionConfirmationMailStatus.CLAIMED.value
        ):
            deletion.confirmation_mail_status = result.value
            session.flush()


def _deliver_confirmation(
    account_id: UUID,
    *,
    primary_email: str,
    mail: MailSender | None,
) -> None:
    result = DeletionConfirmationMailStatus.FAILED
    try:
        active_mail = mail if mail is not None else configured_mail_sender()
        active_mail.send(
            MailMessage(
                to=primary_email,
                subject="Deine Kontoloeschung wurde gestartet",
                body=(
                    "Deine Kontoloeschung wurde gestartet. Du musst nichts weiter tun.\n\n"
                    "Der Zugriff auf dein SideBySide-Konto wurde beendet. Die weitere "
                    "Loeschung laeuft automatisch nach den geltenden Aufbewahrungsregeln."
                ),
            )
        )
    except MailUnavailableError:
        result = DeletionConfirmationMailStatus.UNAVAILABLE
    except MailTransportError:
        result = DeletionConfirmationMailStatus.FAILED
    except Exception:
        # A provider/library bug must not roll back an already accepted deletion.
        # Do not log exception text because transports may include recipient data.
        log.warning("account deletion confirmation mail failed")
        result = DeletionConfirmationMailStatus.FAILED
    else:
        result = DeletionConfirmationMailStatus.SENT

    try:
        _record_confirmation_mail_result(account_id, result)
    except Exception:
        # Delivery-state persistence is observability only. The irreversible
        # tombstone, fail-closed state, and convergence job already committed.
        log.warning("could not record account deletion confirmation mail state")


def accept_self_deletion(
    account_id: UUID,
    *,
    journal: DeletionJournal | None = None,
    mail: MailSender | None = None,
) -> AcceptedSelfDeletion:
    """Irreversibly accept deletion for exactly one authenticated Account.

    Ordering is deliberate:

    1. snapshot the verified primary address and reject Demo mode;
    2. durably append/idempotently read the external tombstone;
    3. commit fail-closed Account/session state and a convergence job together;
    4. attempt one best-effort confirmation mail without retaining its address.

    The existing worker then drives Core -> Media -> Async -> COMPLETED. Client
    connectivity is no longer required after step 3 commits.
    """
    primary_email = _preflight(account_id)
    active_journal = journal if journal is not None else _configured_journal()
    tombstone = active_journal.accept(account_id, accepted_at=now())

    with unit_of_work() as session:
        deletion = apply_accepted_tombstone(
            session,
            account_id,
            accepted_at=tombstone.accepted_at,
        )
        if deletion is None:
            # The Account row is intentionally retained by #520 while shared
            # references exist. Missing here is therefore an inconsistent live
            # acceptance, not a reason to silently claim success.
            raise ServiceUnavailableError(
                "The accepted Account deletion could not establish fail-closed state.",
                SelfDeletionErrorCode.ACCOUNT_UNAVAILABLE,
            )

        should_send = _claim_confirmation_mail(deletion, primary_email=primary_email)
        if deletion.status != AccountDeletionStatus.COMPLETED.value:
            enqueue_convergence(
                session,
                account_id=account_id,
                accepted_at=tombstone.accepted_at,
            )
        status = AccountDeletionStatus(deletion.status)
        session.flush()

    if should_send and primary_email is not None:
        _deliver_confirmation(account_id, primary_email=primary_email, mail=mail)

    return AcceptedSelfDeletion(accepted_at=tombstone.accepted_at, status=status)
