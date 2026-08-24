"""WebAuthn: Passkeys registrieren und mit ihnen anmelden.

Die kryptografische Arbeit macht `py_webauthn`. Was hier steht, ist die
Frage, die keine Bibliothek beantworten kann: **welche** Challenge, fuer
**welches** Konto, mit **welcher** erwarteten Herkunft - und was mit dem
Signaturzaehler geschieht.

Der private Schluessel liegt im Authenticator. Der Server sieht ihn nie;
er speichert Credential-ID, oeffentlichen Schluessel und Zaehler.
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from datetime import timedelta
from typing import TYPE_CHECKING, Any, cast
from uuid import UUID

import webauthn
from sqlalchemy import delete, or_, select

if TYPE_CHECKING:
    from sqlalchemy import CursorResult
from sqlalchemy.orm import Session
from webauthn.helpers import base64url_to_bytes, options_to_json
from webauthn.helpers.exceptions import (
    InvalidAuthenticationResponse,
    InvalidRegistrationResponse,
)
from webauthn.helpers.structs import (
    AuthenticatorSelectionCriteria,
    CredentialDeviceType,
    PublicKeyCredentialDescriptor,
    ResidentKeyRequirement,
    UserVerificationRequirement,
)

from sidebyside.auth import sessions
from sidebyside.auth.sessions import IssuedTokens
from sidebyside.config import get_settings
from sidebyside.core.clock import now
from sidebyside.core.errors import UnauthenticatedError, ValidationError
from sidebyside.identity.models import (
    Account,
    WebAuthnChallenge,
    WebAuthnCredential,
)

log = logging.getLogger(__name__)

CHALLENGE_LIFETIME = timedelta(minutes=5)
"""So lange, wie eine Ceremony am Geraet dauern darf - nicht laenger."""

REGISTRATION = "REGISTRATION"
AUTHENTICATION = "AUTHENTICATION"

MAX_CREDENTIAL_NAME = 120


class PasskeyErrorCode:
    CEREMONY_INVALID = "PASSKEY_CEREMONY_INVALID"
    CREDENTIAL_UNKNOWN = "PASSKEY_UNKNOWN"


@dataclass(frozen=True)
class SignedIn:
    account: Account
    tokens: IssuedTokens


def _invalid() -> ValidationError:
    """Eine Antwort fuer jeden Fehlschlag einer Ceremony.

    Herkunft, RP ID, Challenge, Signatur und User Verification sind
    verschiedene Fehler und ergeben dieselbe Auskunft: keine.
    """
    return ValidationError(
        "This passkey ceremony is no longer valid.", PasskeyErrorCode.CEREMONY_INVALID
    )


def _issue_challenge(
    session: Session, *, purpose: str, account_id: UUID | None
) -> WebAuthnChallenge:
    eintrag = WebAuthnChallenge(
        purpose=purpose,
        challenge=webauthn.helpers.generate_challenge(),
        account_id=account_id,
        expires_at=now() + CHALLENGE_LIFETIME,
    )
    session.add(eintrag)
    session.flush()
    return eintrag


def _consume_challenge(
    session: Session, *, purpose: str, account_id: UUID | None
) -> WebAuthnChallenge:
    """Die juengste offene Challenge dieses Zwecks nehmen und verbrauchen.

    Verbraucht wird in jedem Fall - auch wenn die Pruefung danach
    scheitert. Sonst liesse sich dieselbe Challenge beliebig oft
    durchprobieren.
    """
    jetzt = now()
    bedingungen = [
        WebAuthnChallenge.purpose == purpose,
        WebAuthnChallenge.consumed_at.is_(None),
        WebAuthnChallenge.expires_at > jetzt,
    ]
    if account_id is not None:
        bedingungen.append(WebAuthnChallenge.account_id == account_id)

    eintrag = session.execute(
        select(WebAuthnChallenge)
        .where(*bedingungen)
        .order_by(WebAuthnChallenge.created_at.desc())
        .limit(1)
        .with_for_update()
    ).scalar_one_or_none()
    if eintrag is None:
        raise _invalid()

    eintrag.consumed_at = jetzt
    session.flush()
    return eintrag


def start_registration(session: Session, account: Account) -> dict[str, Any]:
    """Die Registrierung eines Passkeys beginnen.

    Immer aus einer bestehenden Anmeldung heraus: ein Passkey ist ein
    zusaetzlicher Zugang zu einem Konto, das es schon gibt.
    """
    settings = get_settings()
    eintrag = _issue_challenge(session, purpose=REGISTRATION, account_id=account.id)

    vorhandene = (
        session.execute(
            select(WebAuthnCredential).where(WebAuthnCredential.account_id == account.id)
        )
        .scalars()
        .all()
    )

    optionen = webauthn.generate_registration_options(
        rp_id=settings.relying_party_id,
        rp_name=settings.webauthn_rp_name,
        # Die Konto-ID, nicht die Adresse: ein Handle, das der
        # Authenticator speichert, soll keine Kontaktangabe sein.
        user_id=account.id.bytes,
        user_name=account.display_name or str(account.id),
        user_display_name=account.display_name,
        challenge=eintrag.challenge,
        # Ein bereits registrierter Authenticator soll nicht ein zweites
        # Credential fuer dasselbe Konto anlegen.
        exclude_credentials=[
            PublicKeyCredentialDescriptor(id=vorhanden.credential_id) for vorhanden in vorhandene
        ],
        authenticator_selection=AuthenticatorSelectionCriteria(
            resident_key=ResidentKeyRequirement.PREFERRED,
            user_verification=UserVerificationRequirement.PREFERRED,
        ),
    )
    optionen_json: dict[str, Any] = json.loads(options_to_json(optionen))
    return optionen_json


def finish_registration(
    session: Session, account: Account, *, credential: dict[str, Any], name: str = ""
) -> WebAuthnCredential:
    settings = get_settings()
    eintrag = _consume_challenge(session, purpose=REGISTRATION, account_id=account.id)

    try:
        geprueft = webauthn.verify_registration_response(
            credential=credential,
            expected_challenge=eintrag.challenge,
            expected_origin=settings.relying_party_origins,
            expected_rp_id=settings.relying_party_id,
            require_user_verification=False,
        )
    except (InvalidRegistrationResponse, ValueError, KeyError) as fehler:
        log.info("passkey registration rejected")
        raise _invalid() from fehler

    if _credential_by_id(session, geprueft.credential_id) is not None:
        # Global eindeutig: dieselbe Credential-ID darf nicht zweimal
        # existieren, auch nicht bei zwei Konten.
        raise _invalid()

    passkey = WebAuthnCredential(
        account_id=account.id,
        credential_id=geprueft.credential_id,
        public_key=geprueft.credential_public_key,
        sign_count=geprueft.sign_count,
        aaguid=_aaguid(geprueft.aaguid),
        transports=_transports(credential),
        name=name.strip()[:MAX_CREDENTIAL_NAME],
        # Ob ein Credential auffindbar ist, sagt die Registrierung nicht -
        # `residentKey` ist ein Wunsch, keine Zusage. Es zeigt sich erst
        # bei einer Anmeldung ohne Kandidatenliste; dort wird es gesetzt.
        is_discoverable=False,
        backup_eligible=geprueft.credential_device_type == CredentialDeviceType.MULTI_DEVICE,
        backup_state=bool(geprueft.credential_backed_up),
    )
    session.add(passkey)
    session.flush()
    return passkey


def _transports(credential: dict[str, Any]) -> list[str]:
    """Die vom Client gemeldeten Transportwege, so weit sie brauchbar sind."""
    gemeldet = credential.get("transports")
    if not isinstance(gemeldet, list):
        return []
    return [str(weg)[:32] for weg in gemeldet if isinstance(weg, str)]


def _aaguid(wert: str | None) -> UUID | None:
    if not wert:
        return None
    try:
        return UUID(wert)
    except ValueError:
        return None


def _credential_by_id(session: Session, credential_id: bytes) -> WebAuthnCredential | None:
    return session.execute(
        select(WebAuthnCredential).where(WebAuthnCredential.credential_id == credential_id)
    ).scalar_one_or_none()


def start_authentication(session: Session) -> dict[str, Any]:
    """Eine Anmeldung mit Passkey beginnen.

    Ohne Kontobezug: der Authenticator waehlt selbst, welches auffindbare
    Credential er anbietet. Ein Endpunkt, der zu einer Adresse die
    passenden Credentials nennt, waere ein Verzeichnis der Konten.
    """
    settings = get_settings()
    eintrag = _issue_challenge(session, purpose=AUTHENTICATION, account_id=None)
    optionen = webauthn.generate_authentication_options(
        rp_id=settings.relying_party_id,
        challenge=eintrag.challenge,
        user_verification=UserVerificationRequirement.PREFERRED,
    )
    optionen_json: dict[str, Any] = json.loads(options_to_json(optionen))
    return optionen_json


def finish_authentication(
    session: Session,
    *,
    credential: dict[str, Any],
    device_name: str = "",
    platform: str = "",
) -> SignedIn:
    settings = get_settings()
    eintrag = _consume_challenge(session, purpose=AUTHENTICATION, account_id=None)

    try:
        rohe_id = base64url_to_bytes(str(credential["rawId"]))
    except (KeyError, ValueError, TypeError) as fehler:
        raise _invalid() from fehler

    passkey = _credential_by_id(session, rohe_id)
    if passkey is None:
        # Ein unbekanntes Credential und eine falsche Signatur ergeben
        # dieselbe Antwort.
        raise _invalid()

    try:
        geprueft = webauthn.verify_authentication_response(
            credential=credential,
            expected_challenge=eintrag.challenge,
            expected_rp_id=settings.relying_party_id,
            expected_origin=settings.relying_party_origins,
            credential_public_key=passkey.public_key,
            credential_current_sign_count=passkey.sign_count,
            require_user_verification=False,
        )
    except (InvalidAuthenticationResponse, ValueError, KeyError) as fehler:
        log.info("passkey authentication rejected")
        raise _invalid() from fehler

    # Der Signaturzaehler wird oben mitgeprueft: `credential_current_sign_count`
    # laesst die Bibliothek eine Assertion ablehnen, deren Zaehler nicht
    # weitergelaufen ist - der Hinweis auf eine Kopie des Authenticators.
    # Zaehlt ein Geraet gar nicht, bleiben beide Werte 0 und das ist
    # erlaubt; viele Passkeys tun das, und ein Verbot sperrte sie alle aus.
    # Beide Faelle sind in `test_passkeys.py::TestSignaturzaehler` festgehalten.
    konto = session.get(Account, passkey.account_id)
    if konto is None or not konto.is_active:
        raise UnauthenticatedError("Authentication required.", PasskeyErrorCode.CREDENTIAL_UNKNOWN)

    passkey.sign_count = geprueft.new_sign_count
    passkey.last_used_at = now()
    # Diese Anmeldung lief ohne Kandidatenliste - der Authenticator hat das
    # Credential also selbst gefunden. Damit ist belegt, was die
    # Registrierung nur wuenschen konnte.
    passkey.is_discoverable = True
    passkey.backup_state = bool(getattr(geprueft, "credential_backed_up", passkey.backup_state))

    _, ausgestellt = sessions.start_session(
        session, konto, device_name=device_name, platform=platform
    )
    session.flush()
    return SignedIn(account=konto, tokens=ausgestellt)


def prune_challenges(session: Session) -> int:
    """Abgelaufene und verbrauchte Challenges entfernen. Fuer den Wartungsjob."""
    ergebnis = cast(
        "CursorResult[Any]",
        session.execute(
            delete(WebAuthnChallenge).where(
                or_(
                    WebAuthnChallenge.expires_at < now(),
                    WebAuthnChallenge.consumed_at.is_not(None),
                )
            )
        ),
    )
    return int(ergebnis.rowcount or 0)
