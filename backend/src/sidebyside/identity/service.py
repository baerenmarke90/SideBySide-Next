"""Accounts und ihre Adressen."""

from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from sidebyside.core.clock import now
from sidebyside.core.errors import ConflictError, ValidationError
from sidebyside.identity.models import (
    Account,
    AccountEmail,
    AuthIdentity,
    AuthProvider,
    WebAuthnCredential,
)

MAX_DISPLAY_NAME = 120


class AccountErrorCode:
    EMAIL_INVALID = "EMAIL_INVALID"
    EMAIL_TAKEN = "EMAIL_ALREADY_REGISTERED"
    DISPLAY_NAME_REQUIRED = "DISPLAY_NAME_REQUIRED"
    OIDC_IDENTITY_INVALID = "OIDC_IDENTITY_INVALID"
    PASSKEY_INVALID = "PASSKEY_INVALID"


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


def create_oidc_account(
    session: Session,
    *,
    display_name: str,
    verified_email: str | None = None,
) -> Account:
    """Ein Konto fuer ein bereits verifiziertes OIDC-Onboarding anlegen.

    OIDC braucht weder ein lokales Passwort noch eine lokale AuthIdentity.
    Eine E-Mail-Adresse ist nur zusaetzliche, optionale Profildaten. Sie wird
    verworfen, wenn der Claim unbrauchbar oder die Adresse bereits vergeben
    ist. Insbesondere wird darueber niemals ein bestehendes Konto gesucht
    und uebernommen.
    """
    name = (display_name or "").strip() or "Partner"
    konto = Account(display_name=name[:MAX_DISPLAY_NAME])
    session.add(konto)
    session.flush()

    if verified_email:
        try:
            adresse = validate_email(verified_email)
        except ValidationError:
            adresse = ""
        if adresse and find_by_email(session, adresse) is None:
            session.add(
                AccountEmail(
                    account_id=konto.id,
                    email=adresse,
                    verified_at=now(),
                    is_primary=True,
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


def oidc_identity(session: Session, *, issuer: str, subject: str) -> AuthIdentity | None:
    """Eine OIDC-Identitaet anhand des vom Standard definierten Paars finden."""
    return session.execute(
        select(AuthIdentity).where(
            AuthIdentity.provider == AuthProvider.OIDC.value,
            AuthIdentity.issuer == issuer.strip(),
            AuthIdentity.subject == subject,
        )
    ).scalar_one_or_none()


def add_oidc_identity(
    session: Session,
    account: Account,
    *,
    issuer: str,
    subject: str,
    connection_id: str,
) -> AuthIdentity:
    """Eine verifizierte externe Identitaet mit ihrer Verbindung speichern.

    Diese Funktion prueft kein OIDC-Token. Der aufrufende Adapter darf sie
    erst nach Discovery, Signatur- und Claim-Pruefung verwenden.
    """
    issuer_value = issuer.strip()
    connection_value = connection_id.strip()
    if not issuer_value or not subject.strip() or not connection_value:
        raise ValidationError(
            "Issuer, subject and connection ID are required.",
            AccountErrorCode.OIDC_IDENTITY_INVALID,
        )
    if len(issuer_value) > 512 or len(subject) > 512 or len(connection_value) > 128:
        raise ValidationError(
            "OIDC identity metadata is too long.", AccountErrorCode.OIDC_IDENTITY_INVALID
        )

    identity = AuthIdentity(
        account_id=account.id,
        provider=AuthProvider.OIDC.value,
        issuer=issuer_value,
        subject=subject,
        connection_id=connection_value,
    )
    session.add(identity)
    session.flush()
    return identity


def store_webauthn_credential(
    session: Session,
    account: Account,
    *,
    credential_id: bytes,
    public_key: bytes,
    sign_count: int = 0,
    transports: list[str] | None = None,
    name: str = "",
    is_discoverable: bool = True,
    backup_eligible: bool = False,
    backup_state: bool = False,
) -> WebAuthnCredential:
    """Das Ergebnis einer bereits verifizierten Registration Ceremony speichern."""
    if not credential_id or not public_key or sign_count < 0:
        raise ValidationError(
            "Credential ID, public key and a valid sign count are required.",
            AccountErrorCode.PASSKEY_INVALID,
        )
    credential = WebAuthnCredential(
        account_id=account.id,
        credential_id=credential_id,
        public_key=public_key,
        sign_count=sign_count,
        transports=list(transports or []),
        name=name.strip()[:120],
        is_discoverable=is_discoverable,
        backup_eligible=backup_eligible,
        backup_state=backup_state,
    )
    session.add(credential)
    session.flush()
    return credential


def webauthn_credential(session: Session, credential_id: bytes) -> WebAuthnCredential | None:
    return session.execute(
        select(WebAuthnCredential).where(WebAuthnCredential.credential_id == credential_id)
    ).scalar_one_or_none()
