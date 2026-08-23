"""Accounts und ihre Adressen."""

from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from sidebyside.core.errors import ConflictError, ValidationError
from sidebyside.identity.models import Account, AccountEmail, AuthIdentity, AuthProvider

MAX_DISPLAY_NAME = 120


class AccountErrorCode:
    EMAIL_INVALID = "EMAIL_INVALID"
    EMAIL_TAKEN = "EMAIL_ALREADY_REGISTERED"
    DISPLAY_NAME_REQUIRED = "DISPLAY_NAME_REQUIRED"


def normalize_email(email: str) -> str:
    """Klein geschrieben und ohne Rand.

    Sonst waeren "A@b.de" und "a@b.de " zwei Adressen, und die
    Eindeutigkeit haette ein Loch. Die Datenbank haelt mit einer
    Check-Bedingung dagegen.
    """
    return (email or "").strip().lower()


def validate_email(email: str) -> str:
    """Eine bewusst grobe Pruefung.

    Ob eine Adresse wirklich existiert, klaert nur ein Versand dorthin.
    Eine strenge Mustererkennung weist erfahrungsgemaess vor allem gueltige
    Sonderfaelle ab.
    """
    normalisiert = normalize_email(email)
    lokal, at, domain = normalisiert.partition("@")
    if not at or not lokal or "." not in domain or domain.startswith("."):
        raise ValidationError("Enter a valid email address.", AccountErrorCode.EMAIL_INVALID)
    if len(normalisiert) > 320:
        raise ValidationError("Enter a valid email address.", AccountErrorCode.EMAIL_INVALID)
    return normalisiert


def find_by_email(session: Session, email: str) -> Account | None:
    return session.execute(
        select(Account)
        .join(AccountEmail, AccountEmail.account_id == Account.id)
        .where(AccountEmail.email == normalize_email(email))
    ).scalar_one_or_none()


def account_count(session: Session) -> int:
    return session.execute(select(func.count()).select_from(Account)).scalar_one()


def create_account(
    session: Session, *, display_name: str, email: str, password_hash: str
) -> Account:
    """Einen Account mit lokaler Anmeldung anlegen."""
    name = (display_name or "").strip()
    if not name:
        raise ValidationError("A display name is required.", AccountErrorCode.DISPLAY_NAME_REQUIRED)

    adresse = validate_email(email)
    if find_by_email(session, adresse) is not None:
        raise ConflictError(
            "This email address is already registered.", AccountErrorCode.EMAIL_TAKEN
        )

    konto = Account(display_name=name[:MAX_DISPLAY_NAME])
    session.add(konto)
    session.flush()

    session.add(AccountEmail(account_id=konto.id, email=adresse, is_primary=True))
    session.add(
        AuthIdentity(
            account_id=konto.id,
            provider=AuthProvider.LOCAL_PASSWORD.value,
            subject=adresse,
            secret_hash=password_hash,
        )
    )
    session.flush()
    return konto


def local_identity(session: Session, account: Account) -> AuthIdentity | None:
    return session.execute(
        select(AuthIdentity).where(
            AuthIdentity.account_id == account.id,
            AuthIdentity.provider == AuthProvider.LOCAL_PASSWORD.value,
        )
    ).scalar_one_or_none()
