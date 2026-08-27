"""OpenID Connect authorization code flow with PKCE.

An ID token is a claim by an external server about a person. It becomes a
trusted identity only after five properties have been verified:

- the **signature**, against a key from the issuer's JWKS;
- the **issuer**, against both configuration and the self-identifying discovery
  document;
- the **audience**, so a token issued for another application is rejected;
- the **nonce**, binding the token to exactly this authentication request;
- the **state**, binding the return to exactly this browser flow.

If any check is omitted the rest cannot restore the trust chain. These checks
therefore live here rather than in individual endpoints, and every provider
uses the same path. Pocket ID is an ordinary configured connection rather than
a special case.
"""

from __future__ import annotations

import base64
import hashlib
import logging
import secrets
from dataclasses import dataclass
from datetime import timedelta
from typing import TYPE_CHECKING, Any, cast
from urllib.parse import urlencode, urlsplit
from uuid import UUID

import httpx
import jwt
from sqlalchemy import delete, or_, select

if TYPE_CHECKING:
    from sqlalchemy import CursorResult
from sqlalchemy.orm import Session

from sidebyside.auth import rate_limit, sessions
from sidebyside.auth.sessions import IssuedTokens
from sidebyside.auth.tokens import generate_token, hash_token
from sidebyside.config import OidcConnection, get_settings
from sidebyside.core.clock import now
from sidebyside.core.errors import ErrorCode, UnauthenticatedError, ValidationError
from sidebyside.identity import service as accounts
from sidebyside.identity.models import Account, OidcAuthRequest
from sidebyside.relationship import invitations
from sidebyside.relationship.invitations import InvitationErrorCode

log = logging.getLogger(__name__)

AUTH_REQUEST_LIFETIME = timedelta(minutes=10)
"""Lifetime of a started authentication request.

Long enough for provider sign-in including a two-factor step, but short enough
that an abandoned row does not become permanent state.
"""

ACTION_OIDC_START = "oidc_start"

OIDC_START = rate_limit.Limit(attempts=60, window=timedelta(minutes=15))
"""Limit how many authentication flows may start per connection.

Every start creates a row. Without a limit, the anonymous start endpoint would
be a simple way to fill the table before any session exists.
"""

ALLOWED_ALGORITHMS = ("RS256", "RS384", "RS512", "ES256", "ES384", "PS256", "PS384", "PS512")
"""Accepted asymmetric signing algorithms only.

``none`` and HMAC algorithms are excluded. With ``HS256`` the signing key would
be the client secret, confusing confidentiality with authenticity.
"""

HTTP_TIMEOUT = 10.0


class OidcErrorCode:
    UNKNOWN_CONNECTION = "OIDC_CONNECTION_UNKNOWN"
    INVALID_STATE = "OIDC_STATE_INVALID"
    PROVIDER_UNREACHABLE = "OIDC_PROVIDER_UNREACHABLE"
    INVALID_TOKEN = "OIDC_TOKEN_INVALID"
    NO_ACCOUNT = "OIDC_NO_ACCOUNT"


@dataclass(frozen=True)
class Discovery:
    """Endpoints declared by the provider discovery document."""

    issuer: str
    authorization_endpoint: str
    token_endpoint: str
    jwks_uri: str


@dataclass(frozen=True)
class StartedFlow:
    """Values the client needs to send the user to the provider."""

    authorization_url: str
    state: str


@dataclass(frozen=True)
class SignedIn:
    account: Account
    tokens: IssuedTokens


def client() -> httpx.Client:
    """Return the outbound HTTP client.

    Keeping construction in one function lets tests substitute a transport
    without coupling domain logic to it.
    """
    return httpx.Client(timeout=HTTP_TIMEOUT, follow_redirects=False)


def connection(connection_id: str) -> OidcConnection:
    configured = get_settings().oidc_connection(connection_id)
    if configured is None:
        raise ValidationError(
            "This sign-in method is not available.", OidcErrorCode.UNKNOWN_CONNECTION
        )
    return configured


def _get_json(url: str, *, kind: str) -> dict[str, Any]:
    try:
        with client() as http:
            response = http.get(url)
            response.raise_for_status()
            content: dict[str, Any] = response.json()
    except (httpx.HTTPError, ValueError) as error:
        log.warning("oidc request failed", extra={"kind": kind})
        raise ValidationError(
            "The sign-in provider is currently unavailable.",
            OidcErrorCode.PROVIDER_UNREACHABLE,
        ) from error
    return content


def _https_discovery_endpoint(value: object, *, connection_id: str, field: str) -> str:
    """Accept a provider-declared endpoint only when it is an HTTPS URL."""
    endpoint = str(value)
    try:
        parsed = urlsplit(endpoint)
    except ValueError as error:
        log.warning(
            "oidc discovery endpoint invalid",
            extra={"connection": connection_id, "field": field},
        )
        raise ValidationError(
            "The sign-in provider is currently unavailable.",
            OidcErrorCode.PROVIDER_UNREACHABLE,
        ) from error

    if parsed.scheme != "https" or parsed.hostname is None:
        log.warning(
            "oidc discovery endpoint is not https",
            extra={"connection": connection_id, "field": field},
        )
        raise ValidationError(
            "The sign-in provider is currently unavailable.",
            OidcErrorCode.PROVIDER_UNREACHABLE,
        )
    return endpoint


def discover(configured: OidcConnection) -> Discovery:
    """Fetch discovery metadata and verify that the document identifies itself."""
    document = _get_json(f"{configured.issuer}/.well-known/openid-configuration", kind="discovery")
    discovered_issuer = str(document.get("issuer", "")).rstrip("/")
    if discovered_issuer != configured.issuer:
        log.warning("oidc discovery issuer mismatch", extra={"connection": configured.id})
        raise ValidationError(
            "The sign-in provider is currently unavailable.",
            OidcErrorCode.PROVIDER_UNREACHABLE,
        )

    try:
        authorization_endpoint = _https_discovery_endpoint(
            document["authorization_endpoint"],
            connection_id=configured.id,
            field="authorization_endpoint",
        )
        token_endpoint = _https_discovery_endpoint(
            document["token_endpoint"],
            connection_id=configured.id,
            field="token_endpoint",
        )
        jwks_uri = _https_discovery_endpoint(
            document["jwks_uri"],
            connection_id=configured.id,
            field="jwks_uri",
        )
    except KeyError as missing:
        raise ValidationError(
            "The sign-in provider is currently unavailable.",
            OidcErrorCode.PROVIDER_UNREACHABLE,
        ) from missing

    return Discovery(
        issuer=discovered_issuer,
        authorization_endpoint=authorization_endpoint,
        token_endpoint=token_endpoint,
        jwks_uri=jwks_uri,
    )


def _challenge(verifier: str) -> str:
    """Return the S256 challenge for a PKCE verifier."""
    digest = hashlib.sha256(verifier.encode("ascii")).digest()
    return base64.urlsafe_b64encode(digest).decode("ascii").rstrip("=")


def start(
    session: Session,
    connection_id: str,
    *,
    account_id: UUID | None = None,
    invitation_token: str | None = None,
) -> StartedFlow:
    """Start an OIDC authentication flow.

    State, nonce, and PKCE verifier are created here and persisted server-side.
    The client receives only state, which is the value that returns with the
    browser.

    When ``account_id`` is set, the callback links the external identity to
    exactly that already-authenticated account. An optional invitation token is
    bound to the short-lived request only as a hash; it appears neither in the
    provider URL nor as plaintext in the database.
    """
    configured = connection(connection_id)
    rate_limit.check(session, ACTION_OIDC_START, configured.id, OIDC_START)
    rate_limit.record_attempt(session, ACTION_OIDC_START, configured.id)

    discovery = discover(configured)

    state = generate_token()
    nonce = generate_token()
    verifier = secrets.token_urlsafe(64)

    session.add(
        OidcAuthRequest(
            connection_id=configured.id,
            state_hash=hash_token(state),
            nonce=nonce,
            code_verifier=verifier,
            redirect_uri=configured.redirect_uri,
            account_id=account_id,
            invitation_token_hash=(hash_token(invitation_token) if invitation_token else None),
            expires_at=now() + AUTH_REQUEST_LIFETIME,
        )
    )
    session.flush()

    parameters = {
        "response_type": "code",
        "client_id": configured.client_id,
        "redirect_uri": configured.redirect_uri,
        "scope": configured.scopes,
        "state": state,
        "nonce": nonce,
        "code_challenge": _challenge(verifier),
        "code_challenge_method": "S256",
    }
    separator = "&" if "?" in discovery.authorization_endpoint else "?"
    return StartedFlow(
        authorization_url=(f"{discovery.authorization_endpoint}{separator}{urlencode(parameters)}"),
        state=state,
    )


def _open_request(session: Session, connection_id: str, state: str) -> OidcAuthRequest:
    """Find and consume the started authentication request for a state value."""
    invalid = ValidationError(
        "This sign-in attempt is no longer valid.", OidcErrorCode.INVALID_STATE
    )
    if not state:
        raise invalid

    request = session.execute(
        select(OidcAuthRequest)
        .where(OidcAuthRequest.state_hash == hash_token(state))
        .with_for_update()
    ).scalar_one_or_none()

    current_time = now()
    if (
        request is None
        or request.connection_id != connection_id
        or request.consumed_at is not None
        or request.expires_at <= current_time
    ):
        raise invalid

    request.consumed_at = current_time
    session.flush()
    return request


def _exchange_code(
    configured: OidcConnection,
    discovery: Discovery,
    *,
    code: str,
    request: OidcAuthRequest,
) -> dict[str, Any]:
    data = {
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": request.redirect_uri,
        "client_id": configured.client_id,
        "code_verifier": request.code_verifier,
    }
    if configured.client_secret is not None:
        data["client_secret"] = configured.client_secret.get_secret_value()

    try:
        with client() as http:
            response = http.post(discovery.token_endpoint, data=data)
            response.raise_for_status()
            content: dict[str, Any] = response.json()
    except (httpx.HTTPError, ValueError) as error:
        log.warning("oidc token exchange failed", extra={"connection": configured.id})
        raise ValidationError(
            "This sign-in attempt is no longer valid.", OidcErrorCode.INVALID_TOKEN
        ) from error
    return content


def _audience_is_trusted(claims: dict[str, Any], client_id: str) -> bool:
    """Trust only this connection's own client ID as audience."""
    raw_audience = claims.get("aud")
    if isinstance(raw_audience, str):
        audiences = [raw_audience]
    elif (
        isinstance(raw_audience, list)
        and raw_audience
        and all(isinstance(value, str) for value in raw_audience)
    ):
        audiences = raw_audience
    else:
        return False

    if any(audience != client_id for audience in audiences):
        return False

    azp = claims.get("azp")
    if len(audiences) > 1 and azp != client_id:
        return False
    return azp is None or azp == client_id


def _verified_claims(
    configured: OidcConnection,
    discovery: Discovery,
    *,
    id_token: str,
    nonce: str,
) -> dict[str, Any]:
    """Verify the ID-token signature and required claims."""
    invalid = ValidationError(
        "This sign-in attempt is no longer valid.", OidcErrorCode.INVALID_TOKEN
    )
    if not id_token:
        raise invalid

    key_set = jwt.PyJWKSet.from_dict(_get_json(discovery.jwks_uri, kind="jwks"))
    try:
        header = jwt.get_unverified_header(id_token)
        key = _matching_key(key_set, header.get("kid"))
        claims: dict[str, Any] = jwt.decode(
            id_token,
            key=key.key,
            algorithms=list(ALLOWED_ALGORITHMS),
            audience=configured.client_id,
            issuer=discovery.issuer,
            options={"require": ["exp", "iat", "iss", "aud", "sub"]},
        )
    except (jwt.PyJWTError, KeyError, ValueError) as error:
        log.info("oidc id token rejected", extra={"connection": configured.id})
        raise invalid from error

    if claims.get("nonce") != nonce:
        log.info("oidc nonce mismatch", extra={"connection": configured.id})
        raise invalid

    if not _audience_is_trusted(claims, configured.client_id):
        log.info("oidc audience rejected", extra={"connection": configured.id})
        raise invalid

    if not str(claims.get("sub", "")).strip():
        raise invalid

    return claims


def _matching_key(key_set: jwt.PyJWKSet, kid: str | None) -> jwt.PyJWK:
    if kid is not None:
        for key in key_set.keys:
            if key.key_id == kid:
                return key
        raise KeyError("unknown kid")
    if len(key_set.keys) != 1:
        raise KeyError("missing kid with multiple keys")
    return key_set.keys[0]


def _display_name(claims: dict[str, Any]) -> str:
    """Derive a display name from claims without inventing a required claim."""
    for key in ("name", "preferred_username", "given_name"):
        value = claims.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    return str(claims["sub"]).strip()


def _verified_email(claims: dict[str, Any]) -> str | None:
    """Accept only an address the provider explicitly marks as verified."""
    value = claims.get("email")
    if claims.get("email_verified") is True and isinstance(value, str) and value.strip():
        return value.strip()
    return None


def _onboard_with_invitation(
    session: Session,
    *,
    request: OidcAuthRequest,
    claims: dict[str, Any],
    issuer: str,
    subject: str,
    connection_id: str,
) -> Account:
    """Atomically create account, OIDC identity, and membership from an invitation."""
    if request.invitation_token_hash is None:
        raise UnauthenticatedError(
            "This identity is not linked to an account.", OidcErrorCode.NO_ACCOUNT
        )

    def create_account() -> Account:
        account = accounts.create_oidc_account(
            session,
            display_name=_display_name(claims),
            verified_email=_verified_email(claims),
        )
        identity = accounts.add_oidc_identity(
            session,
            account,
            issuer=issuer,
            subject=subject,
            connection_id=connection_id,
        )
        identity.last_used_at = now()
        return account

    try:
        account, _ = invitations.accept_with_new_account(
            session, request.invitation_token_hash, create_account
        )
    except ValidationError as error:
        if error.code == InvitationErrorCode.INVALID:
            raise UnauthenticatedError(
                "This identity is not linked to an account.", OidcErrorCode.NO_ACCOUNT
            ) from error
        raise
    return account


def complete(
    session: Session,
    connection_id: str,
    *,
    code: str,
    state: str,
    device_name: str = "",
    platform: str = "",
) -> SignedIn:
    """Complete the callback from the provider.

    The result is always a normal ``DeviceSession``. Token creation has no
    separate path for external authentication.
    """
    configured = connection(connection_id)
    request = _open_request(session, configured.id, state)
    discovery = discover(configured)

    response = _exchange_code(configured, discovery, code=code, request=request)
    claims = _verified_claims(
        configured,
        discovery,
        id_token=str(response.get("id_token", "")),
        nonce=request.nonce,
    )
    subject = str(claims["sub"])

    identity = accounts.oidc_identity(session, issuer=discovery.issuer, subject=subject)
    if identity is not None:
        account = session.get(Account, identity.account_id)
    elif request.account_id is not None:
        account = session.get(Account, request.account_id)
        if account is not None:
            accounts.add_oidc_identity(
                session,
                account,
                issuer=discovery.issuer,
                subject=subject,
                connection_id=configured.id,
            )
    elif request.invitation_token_hash is not None:
        account = _onboard_with_invitation(
            session,
            request=request,
            claims=claims,
            issuer=discovery.issuer,
            subject=subject,
            connection_id=configured.id,
        )
    else:
        account = None

    if account is None or not account.is_active:
        raise UnauthenticatedError(
            "This identity is not linked to an account.", OidcErrorCode.NO_ACCOUNT
        )

    if identity is not None:
        identity.last_used_at = now()

    rate_limit.clear(session, ACTION_OIDC_START, configured.id)
    _, issued = sessions.start_session(session, account, device_name=device_name, platform=platform)
    session.flush()
    return SignedIn(account=account, tokens=issued)


def prune_auth_requests(session: Session) -> int:
    """Remove expired and consumed authentication requests."""
    cutoff = now()
    result = cast(
        "CursorResult[Any]",
        session.execute(
            delete(OidcAuthRequest).where(
                or_(
                    OidcAuthRequest.expires_at < cutoff,
                    OidcAuthRequest.consumed_at.is_not(None),
                )
            )
        ),
    )
    return int(result.rowcount or 0)


__all__ = [
    "ALLOWED_ALGORITHMS",
    "ErrorCode",
    "OidcErrorCode",
    "SignedIn",
    "StartedFlow",
    "complete",
    "connection",
    "discover",
    "prune_auth_requests",
    "start",
]
