"""OIDC sign-in against a mock provider.

The Provider here is real genug: it has a Discovery-Dokument, a JWKS
and a Token-Endpoint, and it signiert seine ID Tokens with a
correct RSA key. This makes the suite exercise signature verification
tatsaechlich; and not only, that a Funktion aufgerufen was.
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
CONNECTION = "haupt"
SUBJECT = "0815-anna"


@pytest.fixture(scope="module")
def key() -> rsa.RSAPrivateKey:
    return rsa.generate_private_key(public_exponent=65537, key_size=2048)


@pytest.fixture(scope="module")
def jwks(key: rsa.RSAPrivateKey) -> dict[str, Any]:
    public = json.loads(jwt.algorithms.RSAAlgorithm.to_jwk(key.public_key()))
    public["kid"] = "schluessel-1"
    public["use"] = "sig"
    public["alg"] = "RS256"
    return {"keys": [public]}


def id_token(
    key: rsa.RSAPrivateKey,
    *,
    nonce: str,
    issuer: str = ISSUER,
    audience: str = CLIENT_ID,
    subject: str = SUBJECT,
    ablauf: timedelta = timedelta(minutes=5),
    signieren_with: rsa.RSAPrivateKey | None = None,
    request_kwargs: dict[str, Any] | None = None,
) -> str:
    now = datetime.now(UTC)
    claims: dict[str, Any] = {
        "iss": issuer,
        "sub": subject,
        "aud": audience,
        "iat": int(now.timestamp()),
        "exp": int((now + ablauf).timestamp()),
        "nonce": nonce,
        "email": "anna@example.org",
    }
    claims.update(request_kwargs or {})
    return jwt.encode(
        claims,
        signieren_with or key,
        algorithm="RS256",
        headers={"kid": "schluessel-1"},
    )


class MockProvider:
    "A mock identity provider with controllable responses."

    def __init__(self, key: rsa.RSAPrivateKey, jwks: dict[str, Any]) -> None:
        self.key = key
        self.jwks = jwks
        self.discovery_issuer = ISSUER
        self.id_token: str | None = None
        self.token_status = 200
        self.aufrufe: list[httpx.Request] = []

    def handler(self, request: httpx.Request) -> httpx.Response:
        self.aufrufe.append(request)
        path = request.url.path
        if path.endswith("/.well-known/openid-configuration"):
            return httpx.Response(
                200,
                json={
                    "issuer": self.discovery_issuer,
                    "authorization_endpoint": f"{ISSUER}/authorize",
                    "token_endpoint": f"{ISSUER}/token",
                    "jwks_uri": f"{ISSUER}/jwks",
                },
            )
        if path.endswith("/jwks"):
            return httpx.Response(200, json=self.jwks)
        if path.endswith("/token"):
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
def provider(key: rsa.RSAPrivateKey, jwks: dict[str, Any], monkeypatch) -> MockProvider:  # type: ignore[no-untyped-def]
    mock_provider = MockProvider(key, jwks)
    monkeypatch.setattr(
        oidc,
        "client",
        lambda: httpx.Client(transport=httpx.MockTransport(mock_provider.handler)),
    )

    einstellungen = Settings(
        environment="test",  # type: ignore[arg-type]
        mail_transport=MailTransport.LOG,
        oidc_connections=[
            OidcConnection(
                id=CONNECTION,
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
    return mock_provider


def started_sign_in(client, connection: str = CONNECTION, headers: dict[str, str] | None = None):  # type: ignore[no-untyped-def]
    path = "link" if headers else "start"
    response = client.post(f"/api/v1/auth/oidc/{connection}/{path}", headers=headers or {})
    assert response.status_code == 201, response.text
    return response.json()


def nonce_to(session: Session, state: str) -> str:
    anfrage = session.execute(
        select(OidcAuthRequest).where(OidcAuthRequest.state_hash == hash_token(state))
    ).scalar_one()
    return anfrage.nonce


@pytest.fixture
def anna_with_identity(session: Session):  # type: ignore[no-untyped-def]
    account = make_account(session, "Anna")
    session.add(
        AuthIdentity(
            account_id=account.id,
            provider=AuthProvider.OIDC.value,
            issuer=ISSUER,
            subject=SUBJECT,
            connection_id=CONNECTION,
        )
    )
    session.flush()
    return account


class TestBeginn:
    def test_the_address_carries_all_required_parameters(self, client, provider) -> None:  # type: ignore[no-untyped-def]
        started = started_sign_in(client)
        address = httpx.URL(started["authorizationUrl"])

        assert str(address).startswith(f"{ISSUER}/authorize")
        parameters = dict(address.params)
        assert parameters["response_type"] == "code"
        assert parameters["client_id"] == CLIENT_ID
        assert parameters["code_challenge_method"] == "S256"
        assert parameters["state"] == started["state"]
        assert parameters["nonce"]
        assert parameters["code_challenge"]

    def test_the_verifier_remains_at_server(self, client, provider) -> None:  # type: ignore[no-untyped-def]
        "the URL contains only the challenge, never the verifier."
        started = started_sign_in(client)
        parameters = dict(httpx.URL(started["authorizationUrl"]).params)
        assert "code_verifier" not in parameters

    def test_unknown_connection_is_rejected(self, client, provider) -> None:  # type: ignore[no-untyped-def]
        response = client.post("/api/v1/auth/oidc/gibt-es-nicht/start")
        assert response.status_code == 422
        assert response.json()["code"] == "OIDC_CONNECTION_UNKNOWN"

    def test_second_connection_hat_own_values(self, client, provider) -> None:  # type: ignore[no-untyped-def]
        "multiple providers coexist through configuration only."
        provider.discovery_issuer = ANDERER_ISSUER
        started = started_sign_in(client, "zweite")
        parameters = dict(httpx.URL(started["authorizationUrl"]).params)
        assert parameters["client_id"] == "andere-app"


class TestAnmeldung:
    def test_known_identity_gets_a_session_data(  # type: ignore[no-untyped-def]
        self, client, session, provider, key, anna_with_identity
    ) -> None:
        started = started_sign_in(client)
        provider.id_token = id_token(key, nonce=nonce_to(session, started["state"]))

        response = client.post(
            f"/api/v1/auth/oidc/{CONNECTION}/callback",
            json={"code": "vom-anbieter", "state": started["state"], "deviceName": "Pixel"},
        )
        assert response.status_code == 201
        access_token = response.json()["tokens"]["accessToken"]
        assert client.get("/api/v1/auth/me", headers=auth(access_token)).status_code == 200

    def test_the_response_carries_no_foreign_token(  # type: ignore[no-untyped-def]
        self, client, session, provider, key, anna_with_identity
    ) -> None:
        started = started_sign_in(client)
        provider.id_token = id_token(key, nonce=nonce_to(session, started["state"]))
        response = client.post(
            f"/api/v1/auth/oidc/{CONNECTION}/callback",
            json={"code": "vom-anbieter", "state": started["state"]},
        )
        assert "beim-anbieter" not in response.text
        assert provider.id_token not in response.text

    def test_it_is_created_exactly_a_device_session(  # type: ignore[no-untyped-def]
        self, client, session, provider, key, anna_with_identity
    ) -> None:
        "the external flow therefore ends in the central session issuance path."
        vorher = len(session.execute(select(DeviceSession)).scalars().all())
        started = started_sign_in(client)
        provider.id_token = id_token(key, nonce=nonce_to(session, started["state"]))
        client.post(
            f"/api/v1/auth/oidc/{CONNECTION}/callback",
            json={"code": "vom-anbieter", "state": started["state"]},
        )
        assert len(session.execute(select(DeviceSession)).scalars().all()) == vorher + 1

    def test_unknown_identity_legt_no_account_to(  # type: ignore[no-untyped-def]
        self, client, session, provider, key
    ) -> None:
        "otherwise to external provider would bypass the invitation boundary."
        vorher = len(session.execute(select(Account)).scalars().all())
        started = started_sign_in(client)
        provider.id_token = id_token(key, nonce=nonce_to(session, started["state"]))

        response = client.post(
            f"/api/v1/auth/oidc/{CONNECTION}/callback",
            json={"code": "vom-anbieter", "state": started["state"]},
        )
        assert response.status_code == 401
        assert response.json()["code"] == "OIDC_NO_ACCOUNT"
        assert len(session.execute(select(Account)).scalars().all()) == vorher


class TestLinking:
    def test_signed_in_account_gets_the_identity(  # type: ignore[no-untyped-def]
        self, client, session, provider, key
    ) -> None:
        account = make_account(session, "Ben")
        session.flush()
        headers = auth(sign_in(session, account))

        started = started_sign_in(client, headers=headers)
        provider.id_token = id_token(
            key, nonce=nonce_to(session, started["state"]), subject="ben-extern"
        )
        response = client.post(
            f"/api/v1/auth/oidc/{CONNECTION}/callback",
            json={"code": "vom-anbieter", "state": started["state"]},
        )
        assert response.status_code == 201

        identity = session.execute(
            select(AuthIdentity).where(AuthIdentity.subject == "ben-extern")
        ).scalar_one()
        assert identity.account_id == account.id
        assert identity.connection_id == CONNECTION

    def test_link_requires_a_sign_in(self, client, provider) -> None:  # type: ignore[no-untyped-def]
        assert client.post(f"/api/v1/auth/oidc/{CONNECTION}/link").status_code == 401


class TestRejectedTokens:
    "each validation is tested independently."

    def _attempt(self, client, session, provider, token_bauer) -> Any:  # type: ignore[no-untyped-def]
        started = started_sign_in(client)
        provider.id_token = token_bauer(nonce_to(session, started["state"]))
        return client.post(
            f"/api/v1/auth/oidc/{CONNECTION}/callback",
            json={"code": "vom-anbieter", "state": started["state"]},
        )

    def test_wrong_issuer(self, client, session, provider, key, anna_with_identity) -> None:  # type: ignore[no-untyped-def]
        response = self._attempt(
            client,
            session,
            provider,
            lambda nonce: id_token(key, nonce=nonce, issuer=ANDERER_ISSUER),
        )
        assert response.status_code == 422
        assert response.json()["code"] == "OIDC_TOKEN_INVALID"

    def test_wrong_audience(self, client, session, provider, key, anna_with_identity) -> None:  # type: ignore[no-untyped-def]
        response = self._attempt(
            client,
            session,
            provider,
            lambda nonce: id_token(key, nonce=nonce, audience="eine-andere-app"),
        )
        assert response.status_code == 422

    def test_foreign_signature(self, client, session, provider, anna_with_identity) -> None:  # type: ignore[no-untyped-def]
        foreign = rsa.generate_private_key(public_exponent=65537, key_size=2048)
        response = self._attempt(
            client,
            session,
            provider,
            lambda nonce: id_token(foreign, nonce=nonce, signieren_with=foreign),
        )
        assert response.status_code == 422

    def test_expired_token(self, client, session, provider, key, anna_with_identity) -> None:  # type: ignore[no-untyped-def]
        response = self._attempt(
            client,
            session,
            provider,
            lambda nonce: id_token(key, nonce=nonce, ablauf=timedelta(minutes=-5)),
        )
        assert response.status_code == 422

    def test_wrong_nonce(self, client, session, provider, key, anna_with_identity) -> None:  # type: ignore[no-untyped-def]
        "without this binding, a token captured elsewhere could be replayed."
        response = self._attempt(
            client, session, provider, lambda nonce: id_token(key, nonce="etwas-anderes")
        )
        assert response.status_code == 422

    def test_foreign_azp(self, client, session, provider, key, anna_with_identity) -> None:  # type: ignore[no-untyped-def]
        response = self._attempt(
            client,
            session,
            provider,
            lambda nonce: id_token(key, nonce=nonce, request_kwargs={"azp": "wer-anders"}),
        )
        assert response.status_code == 422

    def test_empty_subject(self, client, session, provider, key, anna_with_identity) -> None:  # type: ignore[no-untyped-def]
        response = self._attempt(
            client, session, provider, lambda nonce: id_token(key, nonce=nonce, subject="  ")
        )
        assert response.status_code == 422

    def test_no_id_token_in_the_response(
        self, client, session, provider, anna_with_identity
    ) -> None:  # type: ignore[no-untyped-def]
        response = self._attempt(client, session, provider, lambda nonce: None)
        assert response.status_code == 422

    def test_token_endpoint_responds_with_error(  # type: ignore[no-untyped-def]
        self, client, session, provider, key, anna_with_identity
    ) -> None:
        provider.token_status = 400
        response = self._attempt(
            client, session, provider, lambda nonce: id_token(key, nonce=nonce)
        )
        assert response.status_code == 422
        assert "invalid_grant" not in response.text


class TestState:
    def test_unknown_state(self, client, provider) -> None:  # type: ignore[no-untyped-def]
        response = client.post(
            f"/api/v1/auth/oidc/{CONNECTION}/callback",
            json={"code": "x", "state": "nie-vergeben"},
        )
        assert response.status_code == 422
        assert response.json()["code"] == "OIDC_STATE_INVALID"

    def test_state_applies_exactly_einmal(  # type: ignore[no-untyped-def]
        self, client, session, provider, key, anna_with_identity
    ) -> None:
        started = started_sign_in(client)
        provider.id_token = id_token(key, nonce=nonce_to(session, started["state"]))
        body = {"code": "vom-anbieter", "state": started["state"]}

        assert client.post(f"/api/v1/auth/oidc/{CONNECTION}/callback", json=body).status_code == 201
        second = client.post(f"/api/v1/auth/oidc/{CONNECTION}/callback", json=body)
        assert second.status_code == 422
        assert second.json()["code"] == "OIDC_STATE_INVALID"

    def test_expired_state(self, client, session, provider, key, anna_with_identity) -> None:  # type: ignore[no-untyped-def]
        started = started_sign_in(client)
        anfrage = session.execute(
            select(OidcAuthRequest).where(
                OidcAuthRequest.state_hash == hash_token(started["state"])
            )
        ).scalar_one()
        provider.id_token = id_token(key, nonce=anfrage.nonce)
        anfrage.expires_at = datetime.now(UTC) - timedelta(minutes=1)
        session.flush()

        response = client.post(
            f"/api/v1/auth/oidc/{CONNECTION}/callback",
            json={"code": "x", "state": started["state"]},
        )
        assert response.status_code == 422

    def test_state_the_other_connection(  # type: ignore[no-untyped-def]
        self, client, session, provider, key, anna_with_identity
    ) -> None:
        "a state belongs to exactly one connection."
        started = started_sign_in(client)
        provider.discovery_issuer = ANDERER_ISSUER
        response = client.post(
            "/api/v1/auth/oidc/zweite/callback",
            json={"code": "x", "state": started["state"]},
        )
        assert response.status_code == 422
        assert response.json()["code"] == "OIDC_STATE_INVALID"


class TestProviderFailures:
    def test_discovery_names_a_other_issuer(self, client, provider) -> None:  # type: ignore[no-untyped-def]
        "otherwise a document at the expected URL could point to foreign endpoints."
        provider.discovery_issuer = ANDERER_ISSUER
        response = client.post(f"/api/v1/auth/oidc/{CONNECTION}/start")
        assert response.status_code == 422
        assert response.json()["code"] == "OIDC_PROVIDER_UNREACHABLE"


class TestAufraeumen:
    def test_the_maintenance_job_cleans_up_consumed_attempts(  # type: ignore[no-untyped-def]
        self, client, session, provider, key, anna_with_identity
    ) -> None:
        started = started_sign_in(client)
        provider.id_token = id_token(key, nonce=nonce_to(session, started["state"]))
        client.post(
            f"/api/v1/auth/oidc/{CONNECTION}/callback",
            json={"code": "vom-anbieter", "state": started["state"]},
        )

        assert oidc.prune_auth_requests(session) == 1
        session.flush()
        assert session.execute(select(OidcAuthRequest)).scalars().all() == []
