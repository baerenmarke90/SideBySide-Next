"""Short-lived one-time tokens for cloud authentication flows.

Email verification, magic links, and account recovery deliberately use
separate tables and separate issuing functions. A token therefore cannot be
accidentally accepted by a different flow. Only its SHA-256 hash is persisted;
the plaintext exists only in the issuing function's return value.

Each flow keeps at most one live generation per subject: requesting a new link
supersedes every older open one. That is an authentication contract, not a
convenience, so it is enforced by serializing the subject rather than by
hoping two requests do not overlap. Issuing and consuming both take the same
subject lock before they read the state they are about to decide on, in the
same order, so the outcome of a race is decided by the lock rather than by
timing, and neither can resurrect a superseded proof.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import InstrumentedAttribute, Session

from sidebyside.auth.tokens import generate_token, hash_token
from sidebyside.core.clock import now
from sidebyside.core.errors import ValidationError
from sidebyside.db.locks import lock_subject
from sidebyside.identity.models import (
    AccountRecoveryToken,
    EmailVerificationToken,
    MagicLinkToken,
    OneTimeTokenMixin,
)

EMAIL_VERIFICATION_LIFETIME = timedelta(hours=24)
MAGIC_LINK_LIFETIME = timedelta(minutes=15)
ACCOUNT_RECOVERY_LIFETIME = timedelta(minutes=30)
ACTION_TOKEN_BYTES = 32

GENERATION_LOCK = "action_token_generation"
"""Namespace for the serialization boundary around one flow and subject.

The lock is subject-scoped rather than taken on the Account or AccountEmail
row, for two reasons. A row lock on the subject would also block unrelated
work on that Account for as long as the request runs, including the mail
delivery that follows issuing. And the rate-limit advisory lock is not this
boundary either: it is reserved and released inside its own short security
transaction before token work begins, so it does not span revoke-then-issue.
"""

FLOW_EMAIL_VERIFICATION = "email_verification"
FLOW_MAGIC_LINK = "magic_link"
FLOW_ACCOUNT_RECOVERY = "account_recovery"


class ActionTokenErrorCode:
    INVALID = "ACTION_TOKEN_INVALID"


@dataclass(frozen=True)
class IssuedActionToken:
    token: str
    """Plaintext token. It is stored neither on the model nor in logs."""


def _supersede_open[TokenModel: OneTimeTokenMixin](
    session: Session,
    model_type: type[TokenModel],
    subject_column: InstrumentedAttribute[UUID],
    subject_id: UUID,
    *,
    flow: str,
) -> datetime:
    """Serialize the subject and close every older open generation.

    The lock is taken before the read, because the window to close is exactly
    the one between observing "no open predecessor" and inserting a successor.
    Two requests would otherwise both observe none and both commit one, and the
    tables cannot catch that: only ``token_hash`` is unique, and a partial
    unique index cannot express "open" because expiry depends on the current
    time.

    Returns the time the generation was established, so the caller derives the
    new expiry from the same instant the predecessors were revoked.
    """
    lock_subject(session, GENERATION_LOCK, flow, str(subject_id))

    current_time = now()
    superseded = (
        session.execute(
            select(model_type).where(
                subject_column == subject_id,
                model_type.consumed_at.is_(None),
                model_type.revoked_at.is_(None),
            )
        )
        .scalars()
        .all()
    )
    for model in superseded:
        model.revoked_at = current_time
    session.flush()
    return current_time


def issue_email_verification(
    session: Session, account_email_id: UUID
) -> tuple[EmailVerificationToken, IssuedActionToken]:
    issued_at = _supersede_open(
        session,
        EmailVerificationToken,
        EmailVerificationToken.account_email_id,
        account_email_id,
        flow=FLOW_EMAIL_VERIFICATION,
    )
    token = generate_token(ACTION_TOKEN_BYTES)
    model = EmailVerificationToken(
        account_email_id=account_email_id,
        token_hash=hash_token(token),
        expires_at=issued_at + EMAIL_VERIFICATION_LIFETIME,
    )
    session.add(model)
    session.flush()
    return model, IssuedActionToken(token)


def issue_magic_link(
    session: Session, account_email_id: UUID
) -> tuple[MagicLinkToken, IssuedActionToken]:
    issued_at = _supersede_open(
        session,
        MagicLinkToken,
        MagicLinkToken.account_email_id,
        account_email_id,
        flow=FLOW_MAGIC_LINK,
    )
    token = generate_token(ACTION_TOKEN_BYTES)
    model = MagicLinkToken(
        account_email_id=account_email_id,
        token_hash=hash_token(token),
        expires_at=issued_at + MAGIC_LINK_LIFETIME,
    )
    session.add(model)
    session.flush()
    return model, IssuedActionToken(token)


def issue_account_recovery(
    session: Session, account_id: UUID
) -> tuple[AccountRecoveryToken, IssuedActionToken]:
    issued_at = _supersede_open(
        session,
        AccountRecoveryToken,
        AccountRecoveryToken.account_id,
        account_id,
        flow=FLOW_ACCOUNT_RECOVERY,
    )
    token = generate_token(ACTION_TOKEN_BYTES)
    model = AccountRecoveryToken(
        account_id=account_id,
        token_hash=hash_token(token),
        expires_at=issued_at + ACCOUNT_RECOVERY_LIFETIME,
    )
    session.add(model)
    session.flush()
    return model, IssuedActionToken(token)


def _consume[TokenModel: OneTimeTokenMixin](
    session: Session,
    model_type: type[TokenModel],
    token: str,
    *,
    subject_column: InstrumentedAttribute[UUID],
    flow: str,
) -> TokenModel:
    """Redeem a token exactly once, ordered against a competing reissue.

    The subject is read first, unlocked, purely to learn which subject to lock:
    a token never changes the subject it belongs to. The generation lock is
    then taken before the row lock, the same order issuing uses, so consuming
    and reissuing cannot deadlock and cannot interleave.

    Whichever wins the lock decides the outcome. A reissue that commits first
    has revoked this token, so the redemption fails with the ordinary invalid
    response. A redemption that commits first leaves a consumed token that the
    reissue no longer treats as an open predecessor. Neither order can reopen a
    superseded or consumed proof.
    """
    invalid = ValidationError(
        "This authentication token is no longer valid.", ActionTokenErrorCode.INVALID
    )
    if not token:
        raise invalid

    token_hash = hash_token(token)
    subject_id = session.execute(
        select(subject_column).where(model_type.token_hash == token_hash)
    ).scalar_one_or_none()
    if subject_id is None:
        raise invalid

    lock_subject(session, GENERATION_LOCK, flow, str(subject_id))

    # populate_existing discards anything already loaded for this row. Without
    # it the identity map could still answer with the state read before the
    # lock, which is exactly the state the winning transaction may have
    # replaced.
    model = session.execute(
        select(model_type)
        .where(model_type.token_hash == token_hash)
        .with_for_update()
        .execution_options(populate_existing=True)
    ).scalar_one_or_none()
    current_time = now()
    if model is None or not model.is_open(current_time):
        raise invalid

    model.consumed_at = current_time
    session.flush()
    return model


def consume_email_verification(session: Session, token: str) -> EmailVerificationToken:
    return _consume(
        session,
        EmailVerificationToken,
        token,
        subject_column=EmailVerificationToken.account_email_id,
        flow=FLOW_EMAIL_VERIFICATION,
    )


def consume_magic_link(session: Session, token: str) -> MagicLinkToken:
    return _consume(
        session,
        MagicLinkToken,
        token,
        subject_column=MagicLinkToken.account_email_id,
        flow=FLOW_MAGIC_LINK,
    )


def consume_account_recovery(session: Session, token: str) -> AccountRecoveryToken:
    return _consume(
        session,
        AccountRecoveryToken,
        token,
        subject_column=AccountRecoveryToken.account_id,
        flow=FLOW_ACCOUNT_RECOVERY,
    )


def revoke(session: Session, model: OneTimeTokenMixin) -> None:
    """Invalidate an open token."""
    if model.consumed_at is None and model.revoked_at is None:
        model.revoked_at = now()
        session.flush()
