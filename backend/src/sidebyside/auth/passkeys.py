"""WebAuthn passkey registration and authentication.

``py_webauthn`` performs the cryptographic work. This module answers the
questions a library cannot decide: which challenge belongs to which account,
which origin is expected, and how the signature counter is handled.

The private key remains in the authenticator. The server never sees it and
stores only credential ID, public key, and counter.
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
"""Maximum time a ceremony may take on the device."""

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
    """Return the same response for every ceremony failure.

    Origin, RP ID, challenge, signature, and user verification are distinct
    failure reasons but intentionally disclose the same information: none.
    """
    return ValidationError(
        "This passkey ceremony is no longer valid.", PasskeyErrorCode.CEREMONY_INVALID
    )


def _issue_challenge(
    session: Session, *, purpose: str, account_id: UUID | None
) -> WebAuthnChallenge:
    entry = WebAuthnChallenge(
        purpose=purpose,
        challenge=webauthn.helpers.generate_challenge(),
        account_id=account_id,
        expires_at=now() + CHALLENGE_LIFETIME,
    )
    session.add(entry)
    session.flush()
    return entry


def _consume_challenge(
    session: Session, *, purpose: str, account_id: UUID | None
) -> WebAuthnChallenge:
    """Consume the newest open challenge for this purpose.

    The challenge is consumed regardless of whether later verification
    succeeds. Otherwise the same challenge could be tried repeatedly.
    """
    current_time = now()
    conditions = [
        WebAuthnChallenge.purpose == purpose,
        WebAuthnChallenge.consumed_at.is_(None),
        WebAuthnChallenge.expires_at > current_time,
    ]
    if account_id is not None:
        conditions.append(WebAuthnChallenge.account_id == account_id)

    entry = session.execute(
        select(WebAuthnChallenge)
        .where(*conditions)
        .order_by(WebAuthnChallenge.created_at.desc())
        .limit(1)
        .with_for_update()
    ).scalar_one_or_none()
    if entry is None:
        raise _invalid()

    entry.consumed_at = current_time
    session.flush()
    return entry


def start_registration(session: Session, account: Account) -> dict[str, Any]:
    """Start passkey registration for an authenticated account.

    Registration always begins from an existing session because a passkey is an
    additional authentication method for an account that already exists.
    """
    settings = get_settings()
    entry = _issue_challenge(session, purpose=REGISTRATION, account_id=account.id)

    existing = (
        session.execute(
            select(WebAuthnCredential).where(WebAuthnCredential.account_id == account.id)
        )
        .scalars()
        .all()
    )

    options = webauthn.generate_registration_options(
        rp_id=settings.relying_party_id,
        rp_name=settings.webauthn_rp_name,
        # Use the account ID rather than an address. The handle stored by an
        # authenticator must not contain contact information.
        user_id=account.id.bytes,
        user_name=account.display_name or str(account.id),
        user_display_name=account.display_name,
        challenge=entry.challenge,
        # An already registered authenticator must not create a second
        # credential for the same account.
        exclude_credentials=[
            PublicKeyCredentialDescriptor(id=credential.credential_id) for credential in existing
        ],
        # Authentication is intentionally username-less and sends no
        # allowCredentials list. A successfully registered credential must
        # therefore be discoverable so the authenticator can select it by RP ID.
        authenticator_selection=AuthenticatorSelectionCriteria(
            resident_key=ResidentKeyRequirement.REQUIRED,
            user_verification=UserVerificationRequirement.PREFERRED,
        ),
    )
    options_json: dict[str, Any] = json.loads(options_to_json(options))
    return options_json


def finish_registration(
    session: Session, account: Account, *, credential: dict[str, Any], name: str = ""
) -> WebAuthnCredential:
    settings = get_settings()
    entry = _consume_challenge(session, purpose=REGISTRATION, account_id=account.id)

    try:
        verified = webauthn.verify_registration_response(
            credential=credential,
            expected_challenge=entry.challenge,
            expected_origin=settings.relying_party_origins,
            expected_rp_id=settings.relying_party_id,
            require_user_verification=False,
        )
    except (InvalidRegistrationResponse, ValueError, KeyError) as error:
        log.info("passkey registration rejected")
        raise _invalid() from error

    if _credential_by_id(session, verified.credential_id) is not None:
        # Credential IDs are globally unique and may not exist twice, including
        # across different accounts.
        raise _invalid()

    passkey = WebAuthnCredential(
        account_id=account.id,
        credential_id=verified.credential_id,
        public_key=verified.credential_public_key,
        sign_count=verified.sign_count,
        aaguid=_aaguid(verified.aaguid),
        transports=_transports(credential),
        name=name.strip()[:MAX_CREDENTIAL_NAME],
        # The registration request requires a resident/discoverable credential.
        # WebAuthn creation fails client-side when the authenticator cannot
        # satisfy that requirement, so every successfully verified registration
        # follows the username-less authentication contract.
        is_discoverable=True,
        backup_eligible=verified.credential_device_type == CredentialDeviceType.MULTI_DEVICE,
        backup_state=bool(verified.credential_backed_up),
    )
    session.add(passkey)
    session.flush()
    return passkey


def _transports(credential: dict[str, Any]) -> list[str]:
    """Return usable transport values reported by the client."""
    reported = credential.get("transports")
    if not isinstance(reported, list):
        return []
    return [str(transport)[:32] for transport in reported if isinstance(transport, str)]


def _aaguid(value: str | None) -> UUID | None:
    if not value:
        return None
    try:
        return UUID(value)
    except ValueError:
        return None


def _credential_by_id(session: Session, credential_id: bytes) -> WebAuthnCredential | None:
    return session.execute(
        select(WebAuthnCredential).where(WebAuthnCredential.credential_id == credential_id)
    ).scalar_one_or_none()


def start_authentication(session: Session) -> dict[str, Any]:
    """Start passkey authentication without account enumeration.

    No account is selected up front. The authenticator chooses which
    discoverable credential to offer. An endpoint that listed credentials for
    an address would become an account directory.
    """
    settings = get_settings()
    entry = _issue_challenge(session, purpose=AUTHENTICATION, account_id=None)
    options = webauthn.generate_authentication_options(
        rp_id=settings.relying_party_id,
        challenge=entry.challenge,
        user_verification=UserVerificationRequirement.PREFERRED,
    )
    options_json: dict[str, Any] = json.loads(options_to_json(options))
    return options_json


def finish_authentication(
    session: Session,
    *,
    credential: dict[str, Any],
    device_name: str = "",
    platform: str = "",
) -> SignedIn:
    settings = get_settings()
    entry = _consume_challenge(session, purpose=AUTHENTICATION, account_id=None)

    try:
        raw_id = base64url_to_bytes(str(credential["rawId"]))
    except (KeyError, ValueError, TypeError) as error:
        raise _invalid() from error

    passkey = _credential_by_id(session, raw_id)
    if passkey is None:
        # Unknown credential and invalid signature intentionally produce the
        # same response.
        raise _invalid()

    try:
        verified = webauthn.verify_authentication_response(
            credential=credential,
            expected_challenge=entry.challenge,
            expected_rp_id=settings.relying_party_id,
            expected_origin=settings.relying_party_origins,
            credential_public_key=passkey.public_key,
            credential_current_sign_count=passkey.sign_count,
            require_user_verification=False,
        )
    except (InvalidAuthenticationResponse, ValueError, KeyError) as error:
        log.info("passkey authentication rejected")
        raise _invalid() from error

    # The library verifies the signature counter above. A counter that does not
    # advance is rejected when the authenticator uses counters, which can signal
    # a cloned authenticator. Devices that do not count keep both values at zero
    # and remain valid; many passkeys behave that way.
    account = session.get(Account, passkey.account_id)
    if account is None or not account.is_active:
        raise UnauthenticatedError("Authentication required.", PasskeyErrorCode.CREDENTIAL_UNKNOWN)

    passkey.sign_count = verified.new_sign_count
    passkey.last_used_at = now()
    # Authentication has no allow-list, so successful credential selection also
    # confirms the discoverable registration contract at runtime.
    passkey.is_discoverable = True
    passkey.backup_state = bool(getattr(verified, "credential_backed_up", passkey.backup_state))

    _, issued = sessions.start_session(session, account, device_name=device_name, platform=platform)
    session.flush()
    return SignedIn(account=account, tokens=issued)


def prune_challenges(session: Session) -> int:
    """Remove expired and consumed challenges for the maintenance job."""
    result = cast(
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
    return int(result.rowcount or 0)
