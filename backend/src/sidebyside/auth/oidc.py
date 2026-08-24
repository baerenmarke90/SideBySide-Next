"""OpenID Connect: Authorization Code Flow mit PKCE.

Ein ID Token ist eine Behauptung eines fremden Servers ueber eine Person.
Sie wird erst zu einer Identitaet, wenn fuenf Dinge geprueft sind:

- die **Signatur**, gegen den Schluessel aus dem JWKS des Issuers,
- der **Issuer**, gegen den konfigurierten Wert und gegen das
  Discovery-Dokument, das sich selbst benennen muss,
- die **Audience**, damit ein Token fuer eine andere Anwendung hier nicht
  gilt,
- die **Nonce**, die dieses Token an genau diese Anfrage bindet,
- der **State**, der die Rueckkehr an genau diesen Browser bindet.

Faellt eine dieser Pruefungen aus, ist der Rest wertlos. Deshalb steht
keine davon im Endpunkt, sondern hier - an einer Stelle, die jeder Anbieter
durchlaeuft. Pocket ID ist damit eine gewoehnliche Verbindung und kein
Sonderfall.
"""

from __future__ import annotations

import base64
import hashlib
import logging
import secrets
from dataclasses import dataclass
from datetime import timedelta
from typing import TYPE_CHECKING, Any, cast
from urllib.parse import urlencode
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

log = logging.getLogger(__name__)

AUTH_REQUEST_LIFETIME = timedelta(minutes=10)
"""Wie lange eine begonnene Anmeldung offen bleibt.

Lang genug fuer eine Anmeldung beim Anbieter samt Zwei-Faktor-Schritt,
kurz genug, dass eine liegengebliebene Zeile nicht zum Dauerzustand wird.
"""

ACTION_OIDC_START = "oidc_start"

OIDC_START = rate_limit.Limit(attempts=60, window=timedelta(minutes=15))
"""Begrenzt, wie viele Anmeldungen je Verbindung begonnen werden koennen.

Jeder Start legt eine Zeile an. Ohne Grenze waere der Endpunkt ein
bequemer Weg, die Tabelle zu fuellen - anonym, denn eine Anmeldung beginnt
naturgemaess ohne Sitzung.
"""

ALLOWED_ALGORITHMS = ("RS256", "RS384", "RS512", "ES256", "ES384", "PS256", "PS384", "PS512")
"""Asymmetrische Verfahren, mehr nicht.

`none` und die HMAC-Verfahren sind ausgeschlossen: bei `HS256` waere der
Signaturschluessel das Client Secret, und ein Anbieter, der das anbietet,
verwechselt Vertraulichkeit mit Authentizitaet.
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
    """Die Endpunkte, die das Discovery-Dokument nennt."""

    issuer: str
    authorization_endpoint: str
    token_endpoint: str
    jwks_uri: str


@dataclass(frozen=True)
class StartedFlow:
    """Was der Client braucht, um den Nutzer zum Anbieter zu schicken."""

    authorization_url: str
    state: str


@dataclass(frozen=True)
class SignedIn:
    account: Account
    tokens: IssuedTokens


def client() -> httpx.Client:
    """Der ausgehende HTTP-Client.

    Eine eigene Funktion, damit ein Test einen Transport unterschieben
    kann, ohne dass die Fachlogik davon etwas weiss.
    """
    return httpx.Client(timeout=HTTP_TIMEOUT, follow_redirects=False)


def connection(connection_id: str) -> OidcConnection:
    verbindung = get_settings().oidc_connection(connection_id)
    if verbindung is None:
        # Dieselbe Antwort wie fuer eine fehlgeformte Kennung: welche
        # Verbindungen es gibt, ist Betriebswissen.
        raise ValidationError(
            "This sign-in method is not available.", OidcErrorCode.UNKNOWN_CONNECTION
        )
    return verbindung


def _get_json(url: str, *, was: str) -> dict[str, Any]:
    try:
        with client() as verbindung:
            antwort = verbindung.get(url)
            antwort.raise_for_status()
            inhalt: dict[str, Any] = antwort.json()
    except (httpx.HTTPError, ValueError) as fehler:
        # Ohne eigene Grenze stuende die Fehlermeldung des Anbieters - und
        # damit moeglicherweise interne Adressen - in unserer Antwort.
        log.warning("oidc request failed", extra={"kind": was})
        raise ValidationError(
            "The sign-in provider is currently unavailable.",
            OidcErrorCode.PROVIDER_UNREACHABLE,
        ) from fehler
    return inhalt


def discover(verbindung: OidcConnection) -> Discovery:
    """Das Discovery-Dokument holen und auf sich selbst pruefen.

    Der `issuer` im Dokument muss der konfigurierte sein. Ohne diese
    Pruefung koennte ein Dokument unter der erwarteten Adresse auf die
    Endpunkte eines fremden Anbieters zeigen.
    """
    dokument = _get_json(f"{verbindung.issuer}/.well-known/openid-configuration", was="discovery")
    gefunden = str(dokument.get("issuer", "")).rstrip("/")
    if gefunden != verbindung.issuer:
        log.warning("oidc discovery issuer mismatch", extra={"connection": verbindung.id})
        raise ValidationError(
            "The sign-in provider is currently unavailable.",
            OidcErrorCode.PROVIDER_UNREACHABLE,
        )

    try:
        return Discovery(
            issuer=gefunden,
            authorization_endpoint=str(dokument["authorization_endpoint"]),
            token_endpoint=str(dokument["token_endpoint"]),
            jwks_uri=str(dokument["jwks_uri"]),
        )
    except KeyError as fehlend:
        raise ValidationError(
            "The sign-in provider is currently unavailable.",
            OidcErrorCode.PROVIDER_UNREACHABLE,
        ) from fehlend


def _challenge(verifier: str) -> str:
    """Die S256-Challenge zu einem Verifier."""
    digest = hashlib.sha256(verifier.encode("ascii")).digest()
    return base64.urlsafe_b64encode(digest).decode("ascii").rstrip("=")


def start(
    session: Session,
    connection_id: str,
    *,
    account_id: UUID | None = None,
) -> StartedFlow:
    """Eine Anmeldung beginnen.

    State, Nonce und PKCE-Verifier entstehen hier und werden serverseitig
    festgehalten. Der Client bekommt nur den State - er ist das Stueck, das
    mit dem Browser zurueckkommt.

    Ist `account_id` gesetzt, verknuepft der Rueckweg die externe
    Identitaet mit genau diesem bereits angemeldeten Konto.
    """
    verbindung = connection(connection_id)
    rate_limit.check(session, ACTION_OIDC_START, verbindung.id, OIDC_START)
    rate_limit.record_attempt(session, ACTION_OIDC_START, verbindung.id)

    dokument = discover(verbindung)

    state = generate_token()
    nonce = generate_token()
    verifier = secrets.token_urlsafe(64)

    session.add(
        OidcAuthRequest(
            connection_id=verbindung.id,
            state_hash=hash_token(state),
            nonce=nonce,
            code_verifier=verifier,
            redirect_uri=verbindung.redirect_uri,
            account_id=account_id,
            expires_at=now() + AUTH_REQUEST_LIFETIME,
        )
    )
    session.flush()

    parameter = {
        "response_type": "code",
        "client_id": verbindung.client_id,
        "redirect_uri": verbindung.redirect_uri,
        "scope": verbindung.scopes,
        "state": state,
        "nonce": nonce,
        "code_challenge": _challenge(verifier),
        "code_challenge_method": "S256",
    }
    trenner = "&" if "?" in dokument.authorization_endpoint else "?"
    return StartedFlow(
        authorization_url=f"{dokument.authorization_endpoint}{trenner}{urlencode(parameter)}",
        state=state,
    )


def _open_request(session: Session, connection_id: str, state: str) -> OidcAuthRequest:
    """Die begonnene Anmeldung zu einem State finden und verbrauchen.

    Unbekannt, abgelaufen, bereits verbraucht und zu einer anderen
    Verbindung gehoerend enden in derselben Antwort.
    """
    ungueltig = ValidationError(
        "This sign-in attempt is no longer valid.", OidcErrorCode.INVALID_STATE
    )
    if not state:
        raise ungueltig

    anfrage = session.execute(
        select(OidcAuthRequest)
        .where(OidcAuthRequest.state_hash == hash_token(state))
        .with_for_update()
    ).scalar_one_or_none()

    jetzt = now()
    if (
        anfrage is None
        or anfrage.connection_id != connection_id
        or anfrage.consumed_at is not None
        or anfrage.expires_at <= jetzt
    ):
        raise ungueltig

    anfrage.consumed_at = jetzt
    session.flush()
    return anfrage


def _exchange_code(
    verbindung: OidcConnection, dokument: Discovery, *, code: str, anfrage: OidcAuthRequest
) -> dict[str, Any]:
    daten = {
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": anfrage.redirect_uri,
        "client_id": verbindung.client_id,
        "code_verifier": anfrage.code_verifier,
    }
    if verbindung.client_secret is not None:
        daten["client_secret"] = verbindung.client_secret.get_secret_value()

    try:
        with client() as http:
            antwort = http.post(dokument.token_endpoint, data=daten)
            antwort.raise_for_status()
            inhalt: dict[str, Any] = antwort.json()
    except (httpx.HTTPError, ValueError) as fehler:
        # Der Fehlertext des Anbieters bleibt draussen: er kann das Client
        # Secret oder interne Adressen enthalten.
        log.warning("oidc token exchange failed", extra={"connection": verbindung.id})
        raise ValidationError(
            "This sign-in attempt is no longer valid.", OidcErrorCode.INVALID_TOKEN
        ) from fehler
    return inhalt


def _verified_claims(
    verbindung: OidcConnection,
    dokument: Discovery,
    *,
    id_token: str,
    nonce: str,
) -> dict[str, Any]:
    """Die Signatur- und Claim-Pruefung des ID Tokens."""
    ungueltig = ValidationError(
        "This sign-in attempt is no longer valid.", OidcErrorCode.INVALID_TOKEN
    )
    if not id_token:
        raise ungueltig

    schluesselsatz = jwt.PyJWKSet.from_dict(_get_json(dokument.jwks_uri, was="jwks"))
    try:
        kopf = jwt.get_unverified_header(id_token)
        schluessel = _matching_key(schluesselsatz, kopf.get("kid"))
        claims: dict[str, Any] = jwt.decode(
            id_token,
            key=schluessel.key,
            algorithms=list(ALLOWED_ALGORITHMS),
            audience=verbindung.client_id,
            issuer=dokument.issuer,
            options={"require": ["exp", "iat", "iss", "aud", "sub"]},
        )
    except (jwt.PyJWTError, KeyError, ValueError) as fehler:
        log.info("oidc id token rejected", extra={"connection": verbindung.id})
        raise ungueltig from fehler

    # Die Nonce bindet dieses Token an genau die Anfrage, die es angestossen
    # hat. Ohne sie liesse sich ein anderswo erbeutetes Token einspielen.
    if claims.get("nonce") != nonce:
        log.info("oidc nonce mismatch", extra={"connection": verbindung.id})
        raise ungueltig

    # Bei mehreren Audiences benennt azp den eigentlichen Empfaenger.
    azp = claims.get("azp")
    if azp is not None and azp != verbindung.client_id:
        raise ungueltig

    if not str(claims.get("sub", "")).strip():
        raise ungueltig

    return claims


def _matching_key(schluesselsatz: jwt.PyJWKSet, kid: str | None) -> jwt.PyJWK:
    if kid is not None:
        for schluessel in schluesselsatz.keys:
            if schluessel.key_id == kid:
                return schluessel
        raise KeyError("kid unbekannt")
    if len(schluesselsatz.keys) != 1:
        # Ohne kid und mit mehreren Schluesseln waere die Auswahl geraten.
        raise KeyError("kein kid und mehrere Schluessel")
    return schluesselsatz.keys[0]


def complete(
    session: Session,
    connection_id: str,
    *,
    code: str,
    state: str,
    device_name: str = "",
    platform: str = "",
) -> SignedIn:
    """Den Rueckweg vom Anbieter abschliessen.

    Am Ende steht immer eine gewoehnliche `DeviceSession`. Es gibt keinen
    zweiten Ort, an dem Tokens entstehen - auch nicht fuer externe
    Anmeldungen.
    """
    verbindung = connection(connection_id)
    anfrage = _open_request(session, verbindung.id, state)
    dokument = discover(verbindung)

    antwort = _exchange_code(verbindung, dokument, code=code, anfrage=anfrage)
    claims = _verified_claims(
        verbindung,
        dokument,
        id_token=str(antwort.get("id_token", "")),
        nonce=anfrage.nonce,
    )
    subject = str(claims["sub"])

    identitaet = accounts.oidc_identity(session, issuer=dokument.issuer, subject=subject)
    if identitaet is not None:
        konto = session.get(Account, identitaet.account_id)
    elif anfrage.account_id is not None:
        konto = session.get(Account, anfrage.account_id)
        if konto is not None:
            accounts.add_oidc_identity(
                session,
                konto,
                issuer=dokument.issuer,
                subject=subject,
                connection_id=verbindung.id,
            )
    else:
        # Kein Konto, keine Verknuepfung: hier entsteht keines. Die
        # Registrierung bleibt an Bootstrap und Einladung gebunden, und ein
        # externer Anbieter darf diese Grenze nicht umgehen.
        konto = None

    if konto is None or not konto.is_active:
        raise UnauthenticatedError(
            "This identity is not linked to an account.", OidcErrorCode.NO_ACCOUNT
        )

    if identitaet is not None:
        identitaet.last_used_at = now()

    rate_limit.clear(session, ACTION_OIDC_START, verbindung.id)
    _, ausgestellt = sessions.start_session(
        session, konto, device_name=device_name, platform=platform
    )
    session.flush()
    return SignedIn(account=konto, tokens=ausgestellt)


def prune_auth_requests(session: Session) -> int:
    """Abgelaufene und verbrauchte Anmeldeversuche entfernen.

    Fuer den Wartungsjob. Der Code Verifier ist ein kurzlebiges Geheimnis;
    er soll nicht laenger stehen, als der Ablauf ihn braucht.
    """
    grenze = now()
    # session.execute ist allgemein typisiert; ein DELETE liefert ein
    # CursorResult mit rowcount.
    ergebnis = cast(
        "CursorResult[Any]",
        session.execute(
            delete(OidcAuthRequest).where(
                or_(
                    OidcAuthRequest.expires_at < grenze,
                    OidcAuthRequest.consumed_at.is_not(None),
                )
            )
        ),
    )
    return int(ergebnis.rowcount or 0)


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
