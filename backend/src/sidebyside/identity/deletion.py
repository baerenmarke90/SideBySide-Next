"""Account deletion lifecycle after the external tombstone is durable.

The restore-safe journal defined by #520 is intentionally outside this module.
Callers may invoke :func:`apply_accepted_tombstone` only after that journal has
accepted the Account tombstone. This module then provides the database-side,
retry-safe fail-closed and core-cleanup phases.
"""

from __future__ import annotations

import re
from datetime import datetime
from typing import TYPE_CHECKING, Any, cast
from uuid import UUID

from sqlalchemy import delete, or_, select
from sqlalchemy.orm import Session

if TYPE_CHECKING:
    from sqlalchemy import CursorResult

from sidebyside.auth import sessions
from sidebyside.authorization.retention import hard_delete_owner_only
from sidebyside.core.clock import now
from sidebyside.engagement.models import Notification, PushEndpoint, ThinkingOfYouRequest
from sidebyside.identity.deletion_models import AccountDeletion, AccountDeletionStatus
from sidebyside.identity.models import (
    Account,
    AccountEmail,
    AccountRecoveryToken,
    AuthIdentity,
    DeviceSession,
    OidcAuthRequest,
    WebAuthnChallenge,
    WebAuthnCredential,
)
from sidebyside.profiles.models import PartnerProfile
from sidebyside.relationship.models import Invitation, Membership, MembershipStatus
from sidebyside.relationship.service import end_membership

DELETED_ACCOUNT_DISPLAY_NAME = "Deleted account"
DELETED_ACCOUNT_LOCALE = "de-DE"
DELETED_ACCOUNT_TIMEZONE = "Europe/Berlin"

_FAILURE_CODE = re.compile(r"[A-Z0-9_-]{1,64}\Z")


class DeletionNotAcceptedError(RuntimeError):
    """Cleanup was attempted without an accepted external tombstone."""


def _deletion_for_update(session: Session, account_id: UUID) -> AccountDeletion | None:
    return session.execute(
        select(AccountDeletion).where(AccountDeletion.account_id == account_id).with_for_update()
    ).scalar_one_or_none()


def _account_for_update(session: Session, account_id: UUID) -> Account | None:
    return session.execute(
        select(Account).where(Account.id == account_id).with_for_update()
    ).scalar_one_or_none()


def _enforce_fail_closed(
    session: Session,
    account: Account,
    deletion: AccountDeletion,
) -> None:
    """Make an accepted deletion unusable before slower cleanup runs."""
    if account.disabled_at is None:
        account.disabled_at = deletion.accepted_at

    sessions.revoke_all(session, account)

    memberships = (
        session.execute(
            select(Membership)
            .where(
                Membership.account_id == account.id,
                Membership.status == MembershipStatus.ACTIVE.value,
            )
            .with_for_update()
        )
        .scalars()
        .all()
    )
    for membership in memberships:
        end_membership(membership)

    # An invitation created before deletion must not remain a usable bearer
    # path into a Space after the creator has lost all active Memberships.
    invitations = (
        session.execute(
            select(Invitation)
            .where(
                Invitation.created_by == account.id,
                Invitation.accepted_at.is_(None),
                Invitation.revoked_at.is_(None),
            )
            .with_for_update()
        )
        .scalars()
        .all()
    )
    for invitation in invitations:
        invitation.revoked_at = deletion.accepted_at

    endpoints = (
        session.execute(
            select(PushEndpoint)
            .where(
                PushEndpoint.account_id == account.id,
                PushEndpoint.disabled_at.is_(None),
            )
            .with_for_update()
        )
        .scalars()
        .all()
    )
    for endpoint in endpoints:
        endpoint.disabled_at = deletion.accepted_at


def apply_accepted_tombstone(
    session: Session,
    account_id: UUID,
    *,
    accepted_at: datetime,
) -> AccountDeletion | None:
    """Persist the DB-side fail-closed phase for an already durable tombstone.

    The caller must commit this phase before attempting full cleanup. That
    transaction split is intentional: if later cleanup fails, a rollback must
    never reactivate an Account whose external deletion tombstone is already
    irreversible.

    Returning ``None`` for an absent Account makes restore reconciliation
    idempotent when a future retention pass has already hard-deleted the final
    pseudonymous row.
    """
    account = _account_for_update(session, account_id)
    if account is None:
        return None

    deletion = _deletion_for_update(session, account_id)
    if deletion is None:
        deletion = AccountDeletion(
            account_id=account_id,
            status=AccountDeletionStatus.PENDING.value,
            accepted_at=accepted_at,
        )
        session.add(deletion)
    elif deletion.status != AccountDeletionStatus.COMPLETED.value:
        deletion.status = AccountDeletionStatus.PENDING.value
        deletion.failed_at = None
        deletion.last_failure_code = None

    _enforce_fail_closed(session, account, deletion)
    session.flush()
    return deletion


def _delete_account_rows(session: Session, model: type[Any], account_id: UUID, column: Any) -> int:
    result = cast(
        "CursorResult[Any]",
        session.execute(delete(model).where(column == account_id)),
    )
    return int(result.rowcount or 0)


def apply_core_cleanup(session: Session, account_id: UUID) -> AccountDeletion | None:
    """Delete/pseudonymize core Account data after fail-closed acceptance committed.

    This function deliberately does **not** mark the overall deletion
    ``COMPLETED``. Attachments/media, stale asynchronous work and restore
    reconciliation are separate required #520 cleanup paths. The future
    orchestrator may set ``COMPLETED`` only after every required path has
    converged successfully.

    Attachments are deliberately not removed here. Their technical rows are
    OWNER_ONLY even when a binding points at retained SPACE_SHARED content, so
    #520's media slice must decide from the binding and then reuse the existing
    retry-safe MediaStore deletion path.
    """
    account = _account_for_update(session, account_id)
    if account is None:
        return None

    deletion = _deletion_for_update(session, account_id)
    if deletion is None:
        raise DeletionNotAcceptedError(
            "Account deletion cleanup requires an accepted deletion tombstone."
        )

    _enforce_fail_closed(session, account, deletion)
    if deletion.status == AccountDeletionStatus.COMPLETED.value:
        session.flush()
        return deletion

    # Recipient-scoped notification state and provider endpoints are not
    # historical shared content. PushDelivery rows cascade from either side.
    _delete_account_rows(
        session,
        Notification,
        account_id,
        Notification.recipient_account_id,
    )
    session.execute(
        delete(ThinkingOfYouRequest).where(
            or_(
                ThinkingOfYouRequest.sender_account_id == account_id,
                ThinkingOfYouRequest.recipient_account_id == account_id,
            )
        )
    )
    _delete_account_rows(session, PushEndpoint, account_id, PushEndpoint.account_id)

    # The active partner-facing profile is not retained as historical Account
    # identity. SELF_PROFILE preferences cascade with it; owner-only partner
    # notes authored by this Account are covered by the privacy cleanup below.
    _delete_account_rows(session, PartnerProfile, account_id, PartnerProfile.owner_id)

    # This is the central privacy-class delete. It cannot touch SPACE_SHARED
    # rows and intentionally excludes Attachment rows until their binding is
    # evaluated by the media lifecycle slice.
    hard_delete_owner_only(session, account_id)

    # Revoke first (done above), then remove the token families and their
    # consumed-refresh history. Other authentication proofs are Account-owned
    # and have no post-deletion retention purpose.
    _delete_account_rows(session, DeviceSession, account_id, DeviceSession.account_id)
    _delete_account_rows(session, OidcAuthRequest, account_id, OidcAuthRequest.account_id)
    _delete_account_rows(
        session,
        AccountRecoveryToken,
        account_id,
        AccountRecoveryToken.account_id,
    )
    _delete_account_rows(session, WebAuthnChallenge, account_id, WebAuthnChallenge.account_id)
    _delete_account_rows(
        session,
        WebAuthnCredential,
        account_id,
        WebAuthnCredential.account_id,
    )
    _delete_account_rows(session, AuthIdentity, account_id, AuthIdentity.account_id)
    _delete_account_rows(session, AccountEmail, account_id, AccountEmail.account_id)

    account.display_name = DELETED_ACCOUNT_DISPLAY_NAME
    account.birthday = None
    account.locale = DELETED_ACCOUNT_LOCALE
    account.timezone = DELETED_ACCOUNT_TIMEZONE
    if account.disabled_at is None:
        account.disabled_at = deletion.accepted_at

    # Overall status intentionally remains PENDING until media/async/restore
    # reconciliation has also converged. This prevents partial deletion from
    # ever being represented as complete.
    deletion.completed_at = None
    session.flush()
    return deletion


def mark_deletion_failed(
    session: Session,
    account_id: UUID,
    *,
    failure_code: str,
) -> AccountDeletion:
    """Record a retryable cleanup failure without storing exception prose."""
    deletion = _deletion_for_update(session, account_id)
    if deletion is None:
        raise DeletionNotAcceptedError(
            "Cannot record deletion failure before the tombstone is accepted."
        )

    account = _account_for_update(session, account_id)
    if account is not None:
        _enforce_fail_closed(session, account, deletion)

    if deletion.status == AccountDeletionStatus.COMPLETED.value:
        session.flush()
        return deletion

    normalized = failure_code.strip().upper()
    if _FAILURE_CODE.fullmatch(normalized) is None:
        normalized = "DELETION_CLEANUP_FAILED"

    deletion.status = AccountDeletionStatus.FAILED.value
    deletion.completed_at = None
    deletion.failed_at = now()
    deletion.last_failure_code = normalized
    session.flush()
    return deletion
