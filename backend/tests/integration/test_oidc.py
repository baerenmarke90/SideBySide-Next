"""OIDC-Anmeldung gegen einen nachgebauten Anbieter.

Der Anbieter hier ist echt genug: er hat ein Discovery-Dokument, ein JWKS
und einen Token-Endpunkt, und er signiert seine ID Tokens mit einem
richtigen RSA-Schluessel. Damit prueft die Suite die Signaturpruefung
tatsaechlich - und nicht nur, dass eine Funktion aufgerufen wurde.
"""

from __future__ import annotations

import json
from datetime import UTC, datetime, timedelta
from typing import Any

import httpx
import jwt
import pytest
from cryptography.hazmat.primitives.asymmetric import rsa
from sqlalchemy import select
from sqlalchemy.orm import Session

from sidebyside.auth import oidc
from sidebyside.auth.tokens import hash_token
from sidebyside.config import MailTransport, OidcConnection, Settings
from sidebyside.identity.models import (
    Account,
    AuthIdentity,
    AuthProvider,
    DeviceSession,
    OidcAuthRequest,
)
from tests.conftest import auth, make_account, requires_database, sign_in

pytestmark = [pytest.mark.integration, requires_database]

ISSUER = "https://id.example"
ANDERER_ISSUER = "https://fremd.example"
CLIENT_ID = "sidebyside"
VERBINDUNG = "haupt"
SUBJECT = "0815-anna"


@pytest.fixture(scope="module")
def schluessel() -> rsa.RSAPrivateKey:
    return rsa.generate_private_key(public_exponent=65537, key_size=2048)


@pytest.fixture(scope="module")
def jwks(schluessel: rsa.RSAPrivateKey) -> dict[str, Any]:
    oeffentlich = json.loads(jwt.algorithms.RSAAlgorithm.to_jwk(schluessel.public_key()))
    oeffentlich["kid"] = "schluessel-1"
    oeffentlich["use"] = "sig"
    oeffentlich["alg"] = "RS256"
    return {"keys": [oeffentlich]}


def id_token(
    schluessel: rsa.RSAPrivateKey,
    *,
    nonce: str,
    issuer: str = ISSUER,
    audience: str = CLIENT_ID,
    subject: str = SUBJECT,
    ablauf: timedelta = timedelta(minutes=5),
    signieren_mit: rsa.RSAPrivateKey | None = None,
    zusatz: dict[str, Any] | None = None,
) -> str:
    jetzt = datetime.now(UTC)
    claims: dict[str, Any] = {
        "iss": issuer,
        "sub": subject,
        "aud": audience,
        "iat": int(jetzt.timestamp()),
        "exp": int((jetzt + ablauf).timestamp()),
        "nonce": nonce,
        "email": "anna@example.org",
    }
    claims.update(zusatz or {})
    return jwt.encode(
        claims,
        signieren_mit or schluessel,
        algorithm="RS256",
        headers={"kid": "schluessel-1"},
    )


class Anbieter:
    """Ein nachgebauter Identitaetsanbieter mit steuerbaren Antworten."""

    def __init__(self, schluessel: rsa.RSAPrivateKey, jwks: dict[str, Any]) -> None:
        self.schluessel = schluessel
        self.jwks = jwks
        self.discovery_issuer = ISSUER
        self.id_token: str | None = None
        self.token_status = 200
        self.aufrufe: list[httpx.Request] = []

    def handler(self, request: httpx.Request) -> httpx.Response:
        self.aufrufe.append(request)
        pfad = request.url.path
        if pfad.endswith("/.well-known/openid-configuration"):
            return httpx.Response(
                200,
                json={
                    "issuer": self.discovery_issuer,
                    "authorization_endpoint": f"{ISSUER}/authorize",
                    "token_endpoint": f"{ISSUER}/token",
                    "jwks_uri": f"{ISSUER}/jwks",
                },
            )
        if pfad.endswith("/jwks"):
            return httpx.Response(200, json=self.jwks)
        if pfad.endswith("/token"):
            if self.token_status != 200:
                return httpx.Response(self.token_status, json={"error": "invalid_grant"})
            return httpx.Response(
                200,
                json={
                    "access_token": "beim-anbieter",
                    "token_type": "Bearer",
                    "id_token": self.id_token,
                },
            )
        return httpx.Response(404)


@pytest.fixture
def anbieter(schluessel: rsa.RSAPrivateKey, jwks: dict[str, Any], monkeypatch) -> Anbieter:  # type: ignore[no-untyped-def]
    gegenstelle = Anbieter(schluessel, jwks)
    monkeypatch.setattr(
        oidc,
        "client",
        lambda: httpx.Client(transport=httpx.MockTransport(gegenstelle.handler)),
    )

    einstellungen = Settings(
        environment="test",  # type: ignore[arg-type]
        mail_transport=MailTransport.LOG,
        oidc_connections=[
            OidcConnection(
                id=VERBINDUNG,
                issuer=ISSUER,
                client_id=CLIENT_ID,
                client_secret="geheim",  # type: ignore[arg-type]
                redirect_uri="https://app.example/oidc",
            ),
            OidcConnection(
                id="zweite",
                issuer=ANDERER_ISSUER,
                client_id="andere-app",
                redirect_uri="https://app.example/oidc-2",
            ),
        ],
    )
    monkeypatch.setattr(oidc, "get_settings", lambda: einstellungen)
    return gegenstelle


def begonnene_anmeldung(client, verbindung: str = VERBINDUNG, kopf: dict[str, str] | None = None):  # type: ignore[no-untyped-def]
    pfad = "link" if kopf else "start"
    antwort = client.post(f"/api/v1/auth/oidc/{verbindung}/{pfad}", headers=kopf or {})
    assert antwort.status_code == 201, antwort.text
    return antwort.json()


def nonce_zu(session: Session, state: str) -> str:
    anfrage = session.execute(
        select(OidcAuthRequest).where(OidcAuthRequest.state_hash == hash_token(state))
    ).scalar_one()
    return anfrage.nonce


@pytest.fixture
def anna_mit_identitaet(session: Session):  # type: ignore[no-untyped-def]
    konto = make_account(session, "Anna")
    session.add(
        AuthIdentity(
            account_id=konto.id,
            provider=AuthProvider.OIDC.value,
            issuer=ISSUER,
            subject=SUBJECT,
            connection_id=VERBINDUNG,
        )
    )
    session.flush()
    return konto


class TestBeginn:
    def test_die_adresse_traegt_alle_pflichtparameter(self, client, anbieter) -> None:  # type: ignore[no-untyped-def]
        begonnen = begonnene_anmeldung(client)
        adresse = httpx.URL(begonnen["authorizationUrl"])

        assert str(adresse).startswith(f"{ISSUER}/authorize")
        parameter = dict(adresse.params)
        assert parameter["response_type"] == "code"
        assert parameter["client_id"] == CLIENT_ID
        assert parameter["code_challenge_method"] == "S256"
        assert parameter["state"] == begonnen["state"]
        assert parameter["nonce"]
        assert parameter["code_challenge"]

    def test_der_verifier_bleibt_beim_server(self, client, anbieter) -> None:  # type: ignore[no-untyped-def]
        """In der Adresse steht nur die Challenge, nie der Verifier."""
        begonnen = begonnene_anmeldung(client)
        parameter = dict(httpx.URL(begonnen["authorizationUrl"]).params)
        assert "code_verifier" not in parameter

    def test_unbekannte_verbindung_wird_abgewiesen(self, client, anbieter) -> None:  # type: ignore[no-untyped-def]
        antwort = client.post("/api/v1/auth/oidc/gibt-es-nicht/start")
        assert antwort.status_code == 422
        assert antwort.json()["code"] == "OIDC_CONNECTION_UNKNOWN"

    def test_zweite_verbindung_hat_eigene_werte(self, client, anbieter) -> None:  # type: ignore[no-untyped-def]
        """Mehrere Anbieter nebeneinander, nur ueber Konfiguration."""
        anbieter.discovery_issuer = ANDERER_ISSUER
        begonnen = begonnene_anmeldung(client, "zweite")
        parameter = dict(httpx.URL(begonnen["authorizationUrl"]).params)
        assert parameter["client_id"] == "andere-app"


class TestAnmeldung:
    def test_bekannte_identitaet_bekommt_eine_sitzung(  # type: ignore[no-untyped-def]
        self, client, session, anbieter, schluessel, anna_mit_identitaet
    ) -> None:
        begonnen = begonnene_anmeldung(client)
        anbieter.id_token = id_token(schluessel, nonce=nonce_zu(session, begonnen["state"]))

        antwort = client.post(
            f"/api/v1/auth/oidc/{VERBINDUNG}/callback",
            json={"code": "vom-anbieter", "state": begonnen["state"], "deviceName": "Pixel"},
        )
        assert antwort.status_code == 201
        zugang = antwort.json()["tokens"]["accessToken"]
        assert client.get("/api/v1/auth/me", headers=auth(zugang)).status_code == 200

    def test_die_antwort_traegt_keine_fremden_token(  # type: ignore[no-untyped-def]
        self, client, session, anbieter, schluessel, anna_mit_identitaet
    ) -> None:
        begonnen = begonnene_anmeldung(client)
        anbieter.id_token = id_token(schluessel, nonce=nonce_zu(session, begonnen["state"]))
        antwort = client.post(
            f"/api/v1/auth/oidc/{VERBINDUNG}/callback",
            json={"code": "vom-anbieter", "state": begonnen["state"]},
        )
        assert "beim-anbieter" not in antwort.text
        assert anbieter.id_token not in antwort.text

    def test_es_entsteht_genau_eine_geraetesitzung(  # type: ignore[no-untyped-def]
        self, client, session, anbieter, schluessel, anna_mit_identitaet
    ) -> None:
        """Auch der externe Weg endet in der zentralen Sitzungsausgabe."""
        vorher = len(session.execute(select(DeviceSession)).scalars().all())
        begonnen = begonnene_anmeldung(client)
        anbieter.id_token = id_token(schluessel, nonce=nonce_zu(session, begonnen["state"]))
        client.post(
            f"/api/v1/auth/oidc/{VERBINDUNG}/callback",
            json={"code": "vom-anbieter", "state": begonnen["state"]},
        )
        assert len(session.execute(select(DeviceSession)).scalars().all()) == vorher + 1

    def test_unbekannte_identitaet_legt_kein_konto_an(  # type: ignore[no-untyped-def]
        self, client, session, anbieter, schluessel
    ) -> None:
        """Sonst umginge ein externer Anbieter die Einladungsgrenze."""
        vorher = len(session.execute(select(Account)).scalars().all())
        begonnen = begonnene_anmeldung(client)
        anbieter.id_token = id_token(schluessel, nonce=nonce_zu(session, begonnen["state"]))

        antwort = client.post(
            f"/api/v1/auth/oidc/{VERBINDUNG}/callback",
            json={"code": "vom-anbieter", "state": begonnen["state"]},
        )
        assert antwort.status_code == 401
        assert antwort.json()["code"] == "OIDC_NO_ACCOUNT"
        assert len(session.execute(select(Account)).scalars().all()) == vorher


class TestVerknuepfen:
    def test_angemeldetes_konto_bekommt_die_identitaet(  # type: ignore[no-untyped-def]
        self, client, session, anbieter, schluessel
    ) -> None:
        konto = make_account(session, "Ben")
        session.flush()
        kopf = auth(sign_in(session, konto))

        begonnen = begonnene_anmeldung(client, kopf=kopf)
        anbieter.id_token = id_token(
            schluessel, nonce=nonce_zu(session, begonnen["state"]), subject="ben-extern"
        )
        antwort = client.post(
            f"/api/v1/auth/oidc/{VERBINDUNG}/callback",
            json={"code": "vom-anbieter", "state": begonnen["state"]},
        )
        assert antwort.status_code == 201

        identitaet = session.execute(
            select(AuthIdentity).where(AuthIdentity.subject == "ben-extern")
        ).scalar_one()
        assert identitaet.account_id == konto.id
        assert identitaet.connection_id == VERBINDUNG

    def test_verknuepfen_braucht_eine_anmeldung(self, client, anbieter) -> None:  # type: ignore[no-untyped-def]
        assert client.post(f"/api/v1/auth/oidc/{VERBINDUNG}/link").status_code == 401


class TestAbgelehnteToken:
    """Jede einzelne Pruefung, jeweils fuer sich."""

    def _versuch(self, client, session, anbieter, token_bauer) -> Any:  # type: ignore[no-untyped-def]
        begonnen = begonnene_anmeldung(client)
        anbieter.id_token = token_bauer(nonce_zu(session, begonnen["state"]))
        return client.post(
            f"/api/v1/auth/oidc/{VERBINDUNG}/callback",
            json={"code": "vom-anbieter", "state": begonnen["state"]},
        )

    def test_falscher_issuer(
        self, client, session, anbieter, schluessel, anna_mit_identitaet
    ) -> None:  # type: ignore[no-untyped-def]
        antwort = self._versuch(
            client,
            session,
            anbieter,
            lambda nonce: id_token(schluessel, nonce=nonce, issuer=ANDERER_ISSUER),
        )
        assert antwort.status_code == 422
        assert antwort.json()["code"] == "OIDC_TOKEN_INVALID"

    def test_falsche_audience(
        self, client, session, anbieter, schluessel, anna_mit_identitaet
    ) -> None:  # type: ignore[no-untyped-def]
        antwort = self._versuch(
            client,
            session,
            anbieter,
            lambda nonce: id_token(schluessel, nonce=nonce, audience="eine-andere-app"),
        )
        assert antwort.status_code == 422

    def test_fremde_signatur(self, client, session, anbieter, anna_mit_identitaet) -> None:  # type: ignore[no-untyped-def]
        fremder = rsa.generate_private_key(public_exponent=65537, key_size=2048)
        antwort = self._versuch(
            client,
            session,
            anbieter,
            lambda nonce: id_token(fremder, nonce=nonce, signieren_mit=fremder),
        )
        assert antwort.status_code == 422

    def test_abgelaufenes_token(
        self, client, session, anbieter, schluessel, anna_mit_identitaet
    ) -> None:  # type: ignore[no-untyped-def]
        antwort = self._versuch(
            client,
            session,
            anbieter,
            lambda nonce: id_token(schluessel, nonce=nonce, ablauf=timedelta(minutes=-5)),
        )
        assert antwort.status_code == 422

    def test_falsche_nonce(
        self, client, session, anbieter, schluessel, anna_mit_identitaet
    ) -> None:  # type: ignore[no-untyped-def]
        """Ohne diese Bindung liesse sich ein anderswo erbeutetes Token einspielen."""
        antwort = self._versuch(
            client, session, anbieter, lambda nonce: id_token(schluessel, nonce="etwas-anderes")
        )
        assert antwort.status_code == 422

    def test_fremdes_azp(self, client, session, anbieter, schluessel, anna_mit_identitaet) -> None:  # type: ignore[no-untyped-def]
        antwort = self._versuch(
            client,
            session,
            anbieter,
            lambda nonce: id_token(schluessel, nonce=nonce, zusatz={"azp": "wer-anders"}),
        )
        assert antwort.status_code == 422

    def test_leeres_subject(
        self, client, session, anbieter, schluessel, anna_mit_identitaet
    ) -> None:  # type: ignore[no-untyped-def]
        antwort = self._versuch(
            client, session, anbieter, lambda nonce: id_token(schluessel, nonce=nonce, subject="  ")
        )
        assert antwort.status_code == 422

    def test_kein_id_token_in_der_antwort(
        self, client, session, anbieter, anna_mit_identitaet
    ) -> None:  # type: ignore[no-untyped-def]
        antwort = self._versuch(client, session, anbieter, lambda nonce: None)
        assert antwort.status_code == 422

    def test_token_endpunkt_antwortet_mit_fehler(  # type: ignore[no-untyped-def]
        self, client, session, anbieter, schluessel, anna_mit_identitaet
    ) -> None:
        anbieter.token_status = 400
        antwort = self._versuch(
            client, session, anbieter, lambda nonce: id_token(schluessel, nonce=nonce)
        )
        assert antwort.status_code == 422
        assert "invalid_grant" not in antwort.text


class TestState:
    def test_unbekannter_state(self, client, anbieter) -> None:  # type: ignore[no-untyped-def]
        antwort = client.post(
            f"/api/v1/auth/oidc/{VERBINDUNG}/callback",
            json={"code": "x", "state": "nie-vergeben"},
        )
        assert antwort.status_code == 422
        assert antwort.json()["code"] == "OIDC_STATE_INVALID"

    def test_state_gilt_genau_einmal(  # type: ignore[no-untyped-def]
        self, client, session, anbieter, schluessel, anna_mit_identitaet
    ) -> None:
        begonnen = begonnene_anmeldung(client)
        anbieter.id_token = id_token(schluessel, nonce=nonce_zu(session, begonnen["state"]))
        rumpf = {"code": "vom-anbieter", "state": begonnen["state"]}

        assert (
            client.post(f"/api/v1/auth/oidc/{VERBINDUNG}/callback", json=rumpf).status_code == 201
        )
        zweite = client.post(f"/api/v1/auth/oidc/{VERBINDUNG}/callback", json=rumpf)
        assert zweite.status_code == 422
        assert zweite.json()["code"] == "OIDC_STATE_INVALID"

    def test_abgelaufener_state(
        self, client, session, anbieter, schluessel, anna_mit_identitaet
    ) -> None:  # type: ignore[no-untyped-def]
        begonnen = begonnene_anmeldung(client)
        anfrage = session.execute(
            select(OidcAuthRequest).where(
                OidcAuthRequest.state_hash == hash_token(begonnen["state"])
            )
        ).scalar_one()
        anbieter.id_token = id_token(schluessel, nonce=anfrage.nonce)
        anfrage.expires_at = datetime.now(UTC) - timedelta(minutes=1)
        session.flush()

        antwort = client.post(
            f"/api/v1/auth/oidc/{VERBINDUNG}/callback",
            json={"code": "x", "state": begonnen["state"]},
        )
        assert antwort.status_code == 422

    def test_state_der_anderen_verbindung(  # type: ignore[no-untyped-def]
        self, client, session, anbieter, schluessel, anna_mit_identitaet
    ) -> None:
        """Ein State gehoert zu genau einer Verbindung."""
        begonnen = begonnene_anmeldung(client)
        anbieter.discovery_issuer = ANDERER_ISSUER
        antwort = client.post(
            "/api/v1/auth/oidc/zweite/callback",
            json={"code": "x", "state": begonnen["state"]},
        )
        assert antwort.status_code == 422
        assert antwort.json()["code"] == "OIDC_STATE_INVALID"


class TestAnbieterAntwortetFalsch:
    def test_discovery_nennt_einen_anderen_issuer(self, client, anbieter) -> None:  # type: ignore[no-untyped-def]
        """Sonst zeigte ein Dokument unter erwarteter Adresse auf fremde Endpunkte."""
        anbieter.discovery_issuer = ANDERER_ISSUER
        antwort = client.post(f"/api/v1/auth/oidc/{VERBINDUNG}/start")
        assert antwort.status_code == 422
        assert antwort.json()["code"] == "OIDC_PROVIDER_UNREACHABLE"


class TestAufraeumen:
    def test_der_wartungsjob_raeumt_verbrauchte_versuche(  # type: ignore[no-untyped-def]
        self, client, session, anbieter, schluessel, anna_mit_identitaet
    ) -> None:
        begonnen = begonnene_anmeldung(client)
        anbieter.id_token = id_token(schluessel, nonce=nonce_zu(session, begonnen["state"]))
        client.post(
            f"/api/v1/auth/oidc/{VERBINDUNG}/callback",
            json={"code": "vom-anbieter", "state": begonnen["state"]},
        )

        assert oidc.prune_auth_requests(session) == 1
        session.flush()
        assert session.execute(select(OidcAuthRequest)).scalars().all() == []
