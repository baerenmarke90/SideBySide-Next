"""Binding-aware media cleanup for accepted Account deletions.

Attachment rows are technically OWNER_ONLY even when their binding points at a
retained SPACE_SHARED parent. Account deletion therefore cannot bulk-delete
media by ``owner_id`` alone. This module treats ownership only as the candidate
set, resolves every current binding, and delegates physical deletion to the
existing retry-safe attachment lifecycle.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from sidebyside.attachments import binding, service
from sidebyside.attachments.models import Attachment, AttachmentStatus
from sidebyside.authorization import PrivacyClass
from sidebyside.heart_moments.models import HeartMoment
from sidebyside.identity.deletion import DeletionNotAcceptedError, mark_deletion_failed
from sidebyside.identity.deletion_models import AccountDeletion, AccountDeletionStatus
from sidebyside.identity.models import Account
from sidebyside.memories.models import Memory
from sidebyside.people.models import RelatedPerson

MEDIA_CLEANUP_FAILURE_CODE = "MEDIA_CLEANUP_FAILED"
MEDIA_PARENT_INCONSISTENT_CODE = "MEDIA_PARENT_INCONSISTENT"


class _Disposition(StrEnum):
    RETAIN_SHARED = "RETAIN_SHARED"
    DELETE = "DELETE"
    INCONSISTENT = "INCONSISTENT"


@dataclass(frozen=True)
class AccountMediaCleanupResult:
    """Non-sensitive counters from one idempotent Account media pass."""

    retained_shared: int = 0
    purged: int = 0
    purge_failures: int = 0
    inconsistent_bindings: int = 0

    @property
    def converged(self) -> bool:
        return self.purge_failures == 0 and self.inconsistent_bindings == 0


def _account_for_update(session: Session, account_id: UUID) -> Account | None:
    return session.execute(
        select(Account).where(Account.id == account_id).with_for_update()
    ).scalar_one_or_none()


def _deletion_for_update(session: Session, account_id: UUID) -> AccountDeletion | None:
    return session.execute(
        select(AccountDeletion).where(AccountDeletion.account_id == account_id).with_for_update()
    ).scalar_one_or_none()


def _private_resource_disposition(
    session: Session,
    *,
    model: type[Memory] | type[HeartMoment] | type[RelatedPerson],
    parent_id: UUID,
    account_id: UUID,
    attachment_space_id: UUID,
) -> _Disposition:
    row = session.execute(
        select(model.space_id, model.owner_id, model.privacy_class).where(model.id == parent_id)
    ).one_or_none()
    if row is None:
        # A relation whose parent disappeared should normally have cascaded or
        # become NULL. Treat it as deletable rather than inventing retention.
        return _Disposition.DELETE

    parent_space_id, parent_owner_id, privacy_class = row
    if parent_space_id != attachment_space_id:
        # Never guess across tenant boundaries. A corrupted cross-space binding
        # requires operator attention rather than deleting another tenant's
        # referenced media or retaining a private blob silently.
        return _Disposition.INCONSISTENT
    if privacy_class == PrivacyClass.SPACE_SHARED.value:
        return _Disposition.RETAIN_SHARED
    if parent_owner_id == account_id and privacy_class == PrivacyClass.OWNER_ONLY.value:
        # Core cleanup is expected to remove this parent first. If it is still
        # present, do not fight its FK from the media phase or partially erase
        # the resource. Surface a bounded retryable lifecycle failure instead.
        return _Disposition.INCONSISTENT
    return _Disposition.INCONSISTENT


def _disposition(
    session: Session,
    attachment: Attachment,
    *,
    account_id: UUID,
) -> _Disposition:
    parent = binding.parent_of(session, attachment.id)
    if parent is None:
        return _Disposition.DELETE

    parent_type, parent_id = parent
    if parent_type == "ACCOUNT_PROFILE":
        # Account avatars are active identity state, never retained history. A
        # binding to a different Account would violate the normal upload/bind
        # invariants, so fail closed instead of deleting that Account's avatar.
        return _Disposition.DELETE if parent_id == account_id else _Disposition.INCONSISTENT
    if parent_type == "MEMORY":
        return _private_resource_disposition(
            session,
            model=Memory,
            parent_id=parent_id,
            account_id=account_id,
            attachment_space_id=attachment.space_id,
        )
    if parent_type == "HEART_MOMENT":
        return _private_resource_disposition(
            session,
            model=HeartMoment,
            parent_id=parent_id,
            account_id=account_id,
            attachment_space_id=attachment.space_id,
        )
    if parent_type == "RELATED_PERSON":
        return _private_resource_disposition(
            session,
            model=RelatedPerson,
            parent_id=parent_id,
            account_id=account_id,
            attachment_space_id=attachment.space_id,
        )
    return _Disposition.INCONSISTENT


def apply_account_media_cleanup(
    session: Session,
    account_id: UUID,
) -> AccountMediaCleanupResult:
    """Converge media owned by one already accepted/deactivated Account.

    The Account tombstone and fail-closed phase must already be committed.
    Shared-parent media remains untouched. Unbound uploads and Account-profile
    media are immediately hidden and purged through the existing
    ``DELETING``/``DELETE_FAILED`` lifecycle. Storage failures never reactivate
    the Account and remain retryable.
    """
    account = _account_for_update(session, account_id)
    if account is None:
        # Future final retention may hard-delete the pseudonymous Account row.
        # Replaying an older journal entry must then remain idempotent.
        return AccountMediaCleanupResult()

    deletion = _deletion_for_update(session, account_id)
    if deletion is None or account.disabled_at is None:
        raise DeletionNotAcceptedError(
            "Account media cleanup requires a committed fail-closed deletion tombstone."
        )

    candidates = list(
        session.execute(
            select(Attachment)
            .where(Attachment.owner_id == account_id)
            .order_by(Attachment.id)
            .with_for_update()
        ).scalars()
    )

    retained_shared = 0
    purged = 0
    purge_failures = 0
    inconsistent_bindings = 0

    for attachment in candidates:
        disposition = _disposition(session, attachment, account_id=account_id)
        if disposition is _Disposition.RETAIN_SHARED:
            retained_shared += 1
            continue
        if disposition is _Disposition.INCONSISTENT:
            inconsistent_bindings += 1
            continue

        if attachment.status not in {
            AttachmentStatus.DELETING.value,
            AttachmentStatus.DELETE_FAILED.value,
        }:
            service.mark_for_deletion(session, attachment)
        if service.purge(session, attachment):
            purged += 1
        else:
            purge_failures += 1

    if purge_failures or inconsistent_bindings:
        mark_deletion_failed(
            session,
            account_id,
            failure_code=(
                MEDIA_PARENT_INCONSISTENT_CODE
                if inconsistent_bindings
                else MEDIA_CLEANUP_FAILURE_CODE
            ),
        )
    elif deletion.status == AccountDeletionStatus.FAILED.value and deletion.last_failure_code in {
        MEDIA_CLEANUP_FAILURE_CODE,
        MEDIA_PARENT_INCONSISTENT_CODE,
    }:
        # Allow a direct retry of this slice to converge without requiring a
        # second journal acceptance. Never clear failures owned by another
        # lifecycle slice.
        deletion.status = AccountDeletionStatus.PENDING.value
        deletion.failed_at = None
        deletion.last_failure_code = None
        deletion.completed_at = None

    session.flush()
    return AccountMediaCleanupResult(
        retained_shared=retained_shared,
        purged=purged,
        purge_failures=purge_failures,
        inconsistent_bindings=inconsistent_bindings,
    )
