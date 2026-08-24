"""Registrierung und Anmeldung mit lokalem Passwort.

Der Weg fuer Self-Hosted. Die Cloud setzt auf Magic Link und Passkey ohne
Passwortpflicht - diese kommen als eigene Anmeldewege dazu, ohne dass sich
hier etwas aendert.

## Warum Registrierung eine Einladung braucht

Eine offene Registrierung waere auf einer privaten Paar-Instanz ein
Fehler: wer die Adresse kennt, koennte sich ein Konto anlegen. Ein
Space-Beitritt gaebe das zwar noch nicht, aber ein Fremder haette einen
Fuss in der Tuer und koennte Anmeldeversuche zaehlen lassen.

Deshalb gilt:

- Ist noch kein Account vorhanden, darf sich der erste anlegen. Das ist die
  Inbetriebnahme der Instanz.
- Danach braucht jede Registrierung eine gueltige Einladung.

Wer das anders will, aendert es an dieser Stelle - bewusst und sichtbar.
"""

from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy.orm import Session

from sidebyside.auth import passwords, rate_limit, sessions
from sidebyside.auth.sessions import IssuedTokens
from sidebyside.core.errors import ErrorCode, ForbiddenError, UnauthenticatedError, ValidationError
from sidebyside.identity import service as accounts
from sidebyside.identity.models import Account
from sidebyside.relationship import invitations
from sidebyside.relationship import service as spaces

ACTION_SIGN_IN = "sign_in"
ACTION_ACCEPT = "invitation_accept"


class AuthErrorCode:
    INVALID_CREDENTIALS = "INVALID_CREDENTIALS"
    REGISTRATION_CLOSED = "REGISTRATION_REQUIRES_INVITATION"


@dataclass(frozen=True)
class SignedIn:
    account: Account
    tokens: IssuedTokens


def register(
    session: Session,
    *,
    display_name: str,
    email: str,
    password: str,
    invitation_token: str | None = None,
    device_name: str = "",
    platform: str = "",
) -> SignedIn:
    """Einen Account anlegen und sofort anmelden.

    Der erste Account der Instanz bekommt einen eigenen Space. Jeder
    weitere tritt ueber seine Einladung dem bestehenden bei.
    """
    ist_erster = accounts.account_count(session) == 0

    if not ist_erster and not invitation_token:
        raise ForbiddenError(
            "Registration on this instance requires an invitation.",
            AuthErrorCode.REGISTRATION_CLOSED,
        )

    # Das Passwort wird vor dem Anlegen geprueft. Sonst entstuende ein
    # Account, dessen Registrierung anschliessend scheitert.
    passwords.validate(password)

    if not ist_erster and invitation_token:
        rate_limit.check(session, ACTION_ACCEPT, invitation_token, rate_limit.INVITATION_ACCEPT)
        rate_limit.record_attempt(session, ACTION_ACCEPT, invitation_token)

    konto = accounts.create_account(
        session,
        display_name=display_name,
        email=email,
        password_hash=passwords.hash_password(password),
    )

    if ist_erster:
        spaces.create_space(session, konto)
    else:
        assert invitation_token is not None
        invitations.accept(session, invitation_token, konto)
        rate_limit.clear(session, ACTION_ACCEPT, invitation_token)

    _, tokens = sessions.start_session(session, konto, device_name=device_name, platform=platform)
    session.flush()
    return SignedIn(account=konto, tokens=tokens)


def sign_in(
    session: Session,
    *,
    email: str,
    password: str,
    device_name: str = "",
    platform: str = "",
) -> SignedIn:
    """Anmelden.

    Unbekannte Adresse und falsches Passwort ergeben dieselbe Antwort. Ein
    Unterschied waere eine Auskunft darueber, welche Adressen registriert
    sind - und damit ein Weg, Konten aufzuzaehlen.
    """
    adresse = accounts.normalize_email(email)
    gescheitert = UnauthenticatedError(
        "Email address or password is incorrect.", AuthErrorCode.INVALID_CREDENTIALS
    )

    # Vor der teuren Passwortpruefung, damit sie nicht als Rechenlast
    # missbraucht werden kann.
    rate_limit.check(session, ACTION_SIGN_IN, adresse, rate_limit.SIGN_IN)
    rate_limit.record_attempt(session, ACTION_SIGN_IN, adresse)

    konto = accounts.find_by_email(session, adresse)
    identitaet = accounts.local_identity(session, konto) if konto else None

    # Auch ohne Account wird einmal gerechnet. Sonst waere die Antwort bei
    # unbekannter Adresse spuerbar schneller, und aus der Laufzeit liesse
    # sich ablesen, wer registriert ist.
    hash_wert = (
        identitaet.secret_hash
        if identitaet is not None and identitaet.secret_hash
        else passwords.DUMMY_HASH
    )
    stimmt = passwords.verify_password(hash_wert, password)

    if konto is None or identitaet is None or not stimmt:
        rate_limit.preserve_attempt_after_rollback(session, ACTION_SIGN_IN, adresse)
        raise gescheitert
    if not konto.is_active:
        rate_limit.preserve_attempt_after_rollback(session, ACTION_SIGN_IN, adresse)
        raise gescheitert

    if passwords.needs_rehash(hash_wert):
        identitaet.secret_hash = passwords.hash_password(password)

    rate_limit.clear(session, ACTION_SIGN_IN, adresse)

    _, tokens = sessions.start_session(session, konto, device_name=device_name, platform=platform)
    session.flush()
    return SignedIn(account=konto, tokens=tokens)


def change_password(session: Session, account: Account, *, current: str, new: str) -> None:
    """Passwort aendern.

    Alle anderen Sitzungen werden beendet. Wer sein Passwort aendert, tut
    das oft, weil er einen Zugriff vermutet - dann darf das fremde Geraet
    nicht angemeldet bleiben.
    """
    identitaet = accounts.local_identity(session, account)
    if identitaet is None or not identitaet.secret_hash:
        raise ValidationError("This account has no password sign-in.", ErrorCode.VALIDATION_FAILED)
    if not passwords.verify_password(identitaet.secret_hash, current):
        raise UnauthenticatedError(
            "Email address or password is incorrect.", AuthErrorCode.INVALID_CREDENTIALS
        )

    identitaet.secret_hash = passwords.hash_password(new)
    sessions.revoke_all(session, account)
    session.flush()

