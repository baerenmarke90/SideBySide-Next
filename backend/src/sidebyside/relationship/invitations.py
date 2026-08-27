"""Invitations.

    Account A creates a Space
    → issue invitation
    → one-time token
    → partner opens the link
    → sign in or register
    → accept
    → membership

The token is returned only once and only its hash is persisted.
"""

from __future__ import annotations

from collections.abc import Callable, Sequence
from dataclasses import dataclass
from datetime import timedelta
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from sidebyside.auth.tokens import generate_token, hash_token
from sidebyside.core.clock import now
from sidebyside.core.errors import ConflictError, NotFoundError, ValidationError
from sidebyside.identity.models import Account
from sidebyside.relationship import service
from sidebyside.relationship.models import (
    MAX_ACTIVE_PARTNERS,
    Invitation,
    Membership,
)

INVITATION_LIFETIME = timedelta(days=14)
INVITATION_TOKEN_BYTES = 32


class InvitationErrorCode:
    NOT_FOUND = "INVITATION_NOT_FOUND"
    INVALID = "INVITATION_INVALID"
    SPACE_FULL = "SPACE_FULL"
    ALREADY_MEMBER = "ACCOUNT_ALREADY_MEMBER"
    SELF_INVITE = "CANNOT_ACCEPT_OWN_INVITATION"


@dataclass(frozen=True)
class IssuedInvitation:
    invitation: Invitation
    token: str
    """Plaintext token. It exists only here and in the creator response."""


def create(session: Session, space_id: UUID, created_by: Account) -> IssuedInvitation:
    """Create an invitation.

    If the Space is already full, no invitation is created. Otherwise somebody
    could send a link that only disappoints when opened.
    """
    if len(service.active_memberships(session, space_id)) >= MAX_ACTIVE_PARTNERS:
        raise ConflictError("This space already has two partners.", InvitationErrorCode.SPACE_FULL)

    token = generate_token(INVITATION_TOKEN_BYTES)
    invitation = Invitation(
        space_id=space_id,
        created_by=created_by.id,
        token_hash=hash_token(token),
        expires_at=now() + INVITATION_LIFETIME,
    )
    session.add(invitation)
    session.flush()
    return IssuedInvitation(invitation=invitation, token=token)


def list_open(session: Session, space_id: UUID) -> Sequence[Invitation]:
    current_time = now()
    invitations = (
        session.execute(
            select(Invitation)
            .where(Invitation.space_id == space_id)
            .order_by(Invitation.created_at.desc())
        )
        .scalars()
        .all()
    )
    return [invitation for invitation in invitations if invitation.is_open(current_time)]


def revoke(session: Session, space_id: UUID, invitation_id: UUID) -> Invitation:
    """Revoke an invitation.

    Lookup is scoped to the Space: an invitation ID alone must never grant
    access, including access to revoke it.
    """
    invitation = session.execute(
        select(Invitation).where(
            Invitation.id == invitation_id,
            Invitation.space_id == space_id,
        )
    ).scalar_one_or_none()

    if invitation is None:
        raise NotFoundError("Invitation not found.", InvitationErrorCode.NOT_FOUND)

    if invitation.revoked_at is None and invitation.accepted_at is None:
        invitation.revoked_at = now()
        session.flush()
    return invitation


def _invalid() -> ValidationError:
    return ValidationError("This invitation is no longer valid.", InvitationErrorCode.INVALID)


def _open_for_update(session: Session, token_hash: str) -> Invitation:
    """Load an open invitation under a row lock.

    Internal callers also work only with the hash. This avoids carrying or
    storing a plaintext token through additional layers.
    """
    if not token_hash:
        raise _invalid()

    invitation = session.execute(
        select(Invitation).where(Invitation.token_hash == token_hash).with_for_update()
    ).scalar_one_or_none()

    if invitation is None or not invitation.is_open(now()):
        raise _invalid()
    return invitation


def _accept_open(session: Session, invitation: Invitation, account: Account) -> Membership:
    """Accept an already locked, open invitation at the domain layer."""
    if not invitation.is_open(now()):
        raise _invalid()

    # The creator cannot accept their own invitation. Otherwise a mistaken
    # click consumes the invitation and leaves the partner with a dead link.
    if invitation.created_by == account.id:
        raise ValidationError(
            "You cannot accept your own invitation.", InvitationErrorCode.SELF_INVITE
        )

    # add_member checks the upper bound and existing membership. If it fails,
    # the invitation remains open because the failure is not caused by it.
    membership = service.add_member(session, invitation.space_id, account)

    invitation.accepted_at = now()
    invitation.accepted_by = account.id
    session.flush()
    return membership


def accept(session: Session, token: str, account: Account) -> Membership:
    """Accept an invitation.

    Every failure - unknown, expired, revoked, already used - yields the same
    message. Distinguishing them would disclose which tokens exist.

    The row is loaded under lock. If two attempts accept the same invitation
    concurrently, the second waits for the first and then observes
    `accepted_at` instead of both succeeding.
    """
    if not token:
        raise _invalid()
    invitation = _open_for_update(session, hash_token(token))
    return _accept_open(session, invitation, account)


def accept_with_new_account(
    session: Session,
    token_hash: str,
    account_factory: Callable[[], Account],
) -> tuple[Account, Membership]:
    """Accept an invitation and create the account only while holding the lock.

    This path is intended for onboarding flows where the account does not yet
    exist. The order matters: first lock and revalidate the invitation, only
    then may the caller create the account. Two concurrent callbacks for the
    same invitation therefore cannot create two accounts.
    """
    invitation = _open_for_update(session, token_hash)
    account = account_factory()
    return account, _accept_open(session, invitation, account)
