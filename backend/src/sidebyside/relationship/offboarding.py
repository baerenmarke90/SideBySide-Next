"""Server-authoritative self-exit from one relationship Space."""

from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from sidebyside.authorization.retention import (
    OwnerOnlyCleanupResult,
    hard_delete_owner_only_in_space,
)
from sidebyside.config import Environment, get_settings
from sidebyside.core.clock import now
from sidebyside.core.errors import ForbiddenError, NotFoundError
from sidebyside.identity.models import Account
from sidebyside.relationship import service
from sidebyside.relationship.models import Invitation, Membership, MembershipStatus


class SpaceOffboardingErrorCode:
    DEMO_FORBIDDEN = "SPACE_OFFBOARDING_DEMO_FORBIDDEN"


@dataclass(frozen=True, slots=True)
class LeaveSpaceResult:
    """Non-sensitive state after one idempotent self-exit attempt."""

    membership: Membership
    changed: bool
    revoked_invitations: int
    owner_only_cleanup: OwnerOnlyCleanupResult


def _ensure_self_exit_allowed() -> None:
    settings = get_settings()
    if settings.environment is Environment.DEMO or settings.demo_mode:
        raise ForbiddenError(
            "Demo relationships are managed by the Demo environment and cannot be "
            "ended through the self-service Space flow.",
            SpaceOffboardingErrorCode.DEMO_FORBIDDEN,
        )


def _membership_for_update(
    session: Session,
    *,
    account_id: UUID,
    space_id: UUID,
) -> Membership:
    """Take the exclusive side of the central Membership lifecycle barrier."""
    membership = session.execute(
        select(Membership)
        .where(
            Membership.account_id == account_id,
            Membership.space_id == space_id,
        )
        .with_for_update()
    ).scalar_one_or_none()
    if membership is None:
        raise NotFoundError("Space not found.", service.SpaceErrorCode.NOT_FOUND)
    return membership


def _revoke_open_invitations(session: Session, space_id: UUID) -> int:
    """Revoke invitations after the Space lifecycle row is locked.

    Invitation acceptance also locks Space before Invitation. Once self-exit
    owns the Space row, no stale token can cross the transition while these
    invitation rows are being revoked.
    """
    current_time = now()
    invitations = (
        session.execute(
            select(Invitation)
            .where(Invitation.space_id == space_id)
            .order_by(Invitation.id)
            .with_for_update()
        )
        .scalars()
        .all()
    )
    revoked = 0
    for invitation in invitations:
        if invitation.is_open(current_time):
            invitation.revoked_at = current_time
            revoked += 1
    return revoked


def leave_space(session: Session, account: Account, space_id: UUID) -> LeaveSpaceResult:
    """End only the caller's Membership in one Space.

    The caller's Membership is locked first because ordinary tenant requests
    hold a shared lock on that same row for their transaction. This guarantees
    that an already-authorized write finishes before `LEFT` becomes durable and
    that a later request cannot pass authorization. The Space row is then
    locked to serialize joining/invitations with the history transition.

    A caller who already left receives the same safe historical result without
    creating another lifecycle. A caller that never belonged to the Space
    receives the same privacy-safe 404 used by normal tenant access.

    Space-scoped OWNER_ONLY database rows are removed in the acceptance
    transaction so a successful response cannot strand readable private state.
    Binding-aware attachment/media convergence remains a separate retry-safe
    slice; attachments are deliberately excluded by the shared retention helper.
    """
    _ensure_self_exit_allowed()
    membership = _membership_for_update(
        session,
        account_id=account.id,
        space_id=space_id,
    )

    if membership.status != MembershipStatus.ACTIVE.value:
        return LeaveSpaceResult(
            membership=membership,
            changed=False,
            revoked_invitations=0,
            owner_only_cleanup=OwnerOnlyCleanupResult(total=0, by_table={}),
        )

    service.lock_space(session, space_id)
    service.end_membership(membership)
    revoked = _revoke_open_invitations(session, space_id)
    cleanup = hard_delete_owner_only_in_space(session, account.id, space_id)
    session.flush()
    return LeaveSpaceResult(
        membership=membership,
        changed=True,
        revoked_invitations=revoked,
        owner_only_cleanup=cleanup,
    )
