"""Kurzlebige Einmal-Tokens fuer Cloud-Authentifizierungsablaeufe.

E-Mail-Verifikation, Magic Link und Account Recovery haben absichtlich
getrennte Tabellen und getrennte Ausgabefunktionen. Ein Token kann dadurch
nie versehentlich in einem anderen Ablauf akzeptiert werden. Persistiert
wird ausschliesslich sein SHA-256-Hash; der Klartext existiert nur im
Rueckgabewert der Ausgabefunktion.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import timedelta
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from sidebyside.auth.tokens import generate_token, hash_token
from sidebyside.core.clock import now
from sidebyside.core.errors import ValidationError
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


class ActionTokenErrorCode:
    INVALID = "ACTION_TOKEN_INVALID"


@dataclass(frozen=True)
class IssuedActionToken:
    token: str
    """Der Klartext. Er wird nicht am Modell und nicht in Logs abgelegt."""


def issue_email_verification(
    session: Session, account_email_id: UUID
) -> tuple[EmailVerificationToken, IssuedActionToken]:
    token = generate_token(ACTION_TOKEN_BYTES)
    model = EmailVerificationToken(
        account_email_id=account_email_id,
        token_hash=hash_token(token),
        expires_at=now() + EMAIL_VERIFICATION_LIFETIME,
    )
    session.add(model)
    session.flush()
    return model, IssuedActionToken(token)


def issue_magic_link(
    session: Session, account_email_id: UUID
) -> tuple[MagicLinkToken, IssuedActionToken]:
    token = generate_token(ACTION_TOKEN_BYTES)
    model = MagicLinkToken(
        account_email_id=account_email_id,
        token_hash=hash_token(token),
        expires_at=now() + MAGIC_LINK_LIFETIME,
    )
    session.add(model)
    session.flush()
    return model, IssuedActionToken(token)


def issue_account_recovery(
    session: Session, account_id: UUID
) -> tuple[AccountRecoveryToken, IssuedActionToken]:
    token = generate_token(ACTION_TOKEN_BYTES)
    model = AccountRecoveryToken(
        account_id=account_id,
        token_hash=hash_token(token),
        expires_at=now() + ACCOUNT_RECOVERY_LIFETIME,
    )
    session.add(model)
    session.flush()
    return model, IssuedActionToken(token)


def _consume[TokenModel: OneTimeTokenMixin](
    session: Session, model_type: type[TokenModel], token: str
) -> TokenModel:
    invalid = ValidationError(
        "This authentication token is no longer valid.", ActionTokenErrorCode.INVALID
    )
    if not token:
        raise invalid

    model = session.execute(
        select(model_type).where(model_type.token_hash == hash_token(token)).with_for_update()
    ).scalar_one_or_none()
    current_time = now()
    if model is None or not model.is_open(current_time):
        raise invalid

    model.consumed_at = current_time
    session.flush()
    return model


def consume_email_verification(session: Session, token: str) -> EmailVerificationToken:
    return _consume(session, EmailVerificationToken, token)


def consume_magic_link(session: Session, token: str) -> MagicLinkToken:
    return _consume(session, MagicLinkToken, token)


def consume_account_recovery(session: Session, token: str) -> AccountRecoveryToken:
    return _consume(session, AccountRecoveryToken, token)


def revoke(session: Session, model: OneTimeTokenMixin) -> None:
    """Einen noch offenen Token unbrauchbar machen."""
    if model.consumed_at is None and model.revoked_at is None:
        model.revoked_at = now()
        session.flush()
