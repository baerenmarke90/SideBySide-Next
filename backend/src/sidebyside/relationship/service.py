"""Membership and access to a Space.

This module contains the product's central security invariant. Every access to
Space data goes through `require_membership` BEFORE any resource is loaded.

There is no data access based only on a resource ID.
"""

from __future__ import annotations

from collections.abc import Sequence
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from sidebyside.core.clock import now
from sidebyside.core.errors import ConflictError, NotFoundError
from sidebyside.identity.models import Account
from sidebyside.relationship.models import (
    MAX_ACTIVE_PARTNERS,
    Membership,
    MembershipRole,
    MembershipStatus,
    Space,
    SpaceProfile,
)


class SpaceErrorCode:
    NOT_FOUND = "SPACE_NOT_FOUND"
    FULL = "SPACE_FULL"
    ALREADY_MEMBER = "ACCOUNT_ALREADY_MEMBER"


def require_membership(session: Session, account: Account, space_id: UUID) -> Membership:
    """Return the active membership, or 404.

    Deliberately use NotFoundError rather than ForbiddenError because a 403
    confirms that the Space exists. Someone probing foreign IDs must not learn
    which ones exist. To the caller, another Space is indistinguishable from
    one that does not exist.

    An ended membership follows the same path: after leaving the Space, an
    account no longer sees its content.
    """
    membership = session.execute(
        select(Membership).where(
            Membership.account_id == account.id,
            Membership.space_id == space_id,
            Membership.status == MembershipStatus.ACTIVE.value,
        )
    ).scalar_one_or_none()

    if membership is None:
        raise NotFoundError("Space not found.", SpaceErrorCode.NOT_FOUND)

    return membership


def _ensure_partner_profile(session: Session, space_id: UUID, account_id: UUID) -> None:
    """Couple profile lifecycle to membership lifecycle.

    Keep the import local so the Relationship and Profiles domains do not
    create a cyclic module initialization dependency.
    """
    from sidebyside.profiles.service import ensure_profile

    ensure_profile(session, space_id, account_id)


def create_space(session: Session, founder: Account) -> Space:
    """Create a Space and add the founder as a partner."""
    space = Space()
    session.add(space)
    session.flush()

    session.add(SpaceProfile(space_id=space.id))
    session.add(
        Membership(
            space_id=space.id,
            account_id=founder.id,
            role=MembershipRole.PARTNER.value,
            status=MembershipStatus.ACTIVE.value,
            joined_at=now(),
        )
    )
    session.flush()
    _ensure_partner_profile(session, space.id, founder.id)
    return space


def active_memberships(session: Session, space_id: UUID) -> Sequence[Membership]:
    return (
        session.execute(
            select(Membership).where(
                Membership.space_id == space_id,
                Membership.status == MembershipStatus.ACTIVE.value,
            )
        )
        .scalars()
        .all()
    )


def add_member(session: Session, space_id: UUID, account: Account) -> Membership:
    """Add an account to a Space.

    The upper bound is enforced here rather than only when accepting an
    invitation. A couple Space has at most two active partners, and that rule
    must not depend on the path through which somebody joins.

    The Space row serializes the check and mutation until commit, so two
    different invitations cannot claim the final free slot concurrently.
    """
    space = session.execute(
        select(Space).where(Space.id == space_id).with_for_update()
    ).scalar_one_or_none()
    if space is None:
        raise NotFoundError("Space not found.", SpaceErrorCode.NOT_FOUND)

    existing = session.execute(
        select(Membership).where(
            Membership.space_id == space_id,
            Membership.account_id == account.id,
        )
    ).scalar_one_or_none()

    if existing is not None and existing.is_active:
        raise ConflictError("Account is already a member.", SpaceErrorCode.ALREADY_MEMBER)

    if len(active_memberships(session, space_id)) >= MAX_ACTIVE_PARTNERS:
        raise ConflictError("This space already has two partners.", SpaceErrorCode.FULL)

    if existing is not None:
        # Reactivate an earlier ended membership rather than creating a
        # duplicate, preserving uniqueness per Space and account.
        existing.status = MembershipStatus.ACTIVE.value
        existing.joined_at = now()
        existing.ended_at = None
        session.flush()
        _ensure_partner_profile(session, space_id, account.id)
        return existing

    membership = Membership(
        space_id=space_id,
        account_id=account.id,
        role=MembershipRole.PARTNER.value,
        status=MembershipStatus.ACTIVE.value,
        joined_at=now(),
    )
    session.add(membership)
    session.flush()
    _ensure_partner_profile(session, space_id, account.id)
    return membership


def end_membership(membership: Membership, *, removed: bool = False) -> None:
    """End a membership without deleting it.

    Deleting it would make it impossible to determine later who created
    content.
    """
    membership.status = MembershipStatus.REMOVED.value if removed else MembershipStatus.LEFT.value
    membership.ended_at = now()


def partner_of(session: Session, space_id: UUID, account: Account) -> Account | None:
    """Return the other active partner, if one exists."""
    members = active_memberships(session, space_id)
    for membership in members:
        if membership.account_id != account.id:
            return session.get(Account, membership.account_id)
    return None
