"""Magic link, address verification, and account recovery through the endpoints.

Drei Ablaeufe with derselben Grundfrage: Who a Address eingibt, may from
the Response not ablesen, ob it it exists. And a Token from the a
Ablauf may in the other not apply.
"""

from __future__ import annotations

import re
from collections.abc import Iterator
from datetime import timedelta

import pytest
from sqlalchemy import select
from sqlalchemy.orm import Session

from sidebyside.auth import rate_limit
from sidebyside.auth.tokens import hash_token
from sidebyside.core.clock import now
from sidebyside.identity.models import (
    Account,
    AccountEmail,
    AccountRecoveryToken,
    AuthIdentity,
    AuthProvider,
    DeviceSession,
    EmailVerificationToken,
    MagicLinkToken,
)
from sidebyside.mail import MailMessage, MailSender
from tests.conftest import auth, requires_database

pytestmark = [pytest.mark.integration, requires_database]

GUTES_PASSWORT = "ein-ausreichend-langes-passwort"
NEUES_PASSWORT = "ein-anderes-ausreichend-langes-passwort"
ADRESSE = "anna@example.org"


class Postfach(MailSender):
    "Sammelt instead of to senden."

    def __init__(self) -> None:
        self.nachrichten: list[MailMessage] = []

    def send(self, message: MailMessage) -> None:
        self.nachrichten.append(message)

    @property
    def letzter_token(self) -> str:
        match = re.search(r"token=([A-Za-z0-9_\-]+)", self.nachrichten[-1].body)
        assert match is not None, "The message contains no link"
        return match.group(1)


@pytest.fixture
def mailbox() -> Postfach:
    return Postfach()


@pytest.fixture
def client(session: Session, mailbox: Postfach) -> Iterator[object]:  # type: ignore[override]
    "Like the gemeinsame Client, aber with a Postfach instead of Mailversand."
    from fastapi.testclient import TestClient

    from sidebyside.db.session import get_session
    from sidebyside.mail import sender
    from sidebyside.main import create_app

    app = create_app()
    app.dependency_overrides[get_session] = lambda: session
    app.dependency_overrides[sender] = lambda: mailbox
    yield TestClient(app, raise_server_exceptions=False)


@pytest.fixture
def anna(session: Session, client):  # type: ignore[no-untyped-def]
    "A registrierter Account with Password."
    from tests.conftest import TEST_BOOTSTRAP_TOKEN

    response = client.post(
        "/api/v1/auth/register",
        json={
            "displayName": "Anna",
            "email": ADRESSE,
            "password": GUTES_PASSWORT,
            "bootstrapToken": TEST_BOOTSTRAP_TOKEN,
        },
    )
    assert response.status_code == 201
    return response.json()


def address_von(session: Session) -> AccountEmail:
    entry = session.execute(select(AccountEmail).where(AccountEmail.email == ADRESSE)).scalar_one()
    return entry


class TestInstanzOhneMailweg:
    """`SBS_MAIL_TRANSPORT=none`: the capability is unavailable, and the response
    records that state.

    The bad counterexample would be `202 Accepted`; a confirmation for
    a Message, the niemals is created, samt verbrauchtem Rate-Limit and
    generated token in the database.
    """

    @pytest.fixture
    def client_without_mail_transport(self, session: Session, monkeypatch: pytest.MonkeyPatch):  # type: ignore[no-untyped-def]
        from fastapi.testclient import TestClient

        from sidebyside.config import MailTransport, get_settings
        from sidebyside.db.session import get_session
        from sidebyside.main import create_app

        einstellungen = get_settings().model_copy(update={"mail_transport": MailTransport.NONE})
        monkeypatch.setattr("sidebyside.config.get_settings", lambda: einstellungen)

        app = create_app()
        app.dependency_overrides[get_session] = lambda: session
        with TestClient(app) as client:
            yield client

    def test_magic_link_reports_the_missing_capability(
        self, client_without_mail_transport, anna
    ) -> None:  # type: ignore[no-untyped-def]
        response = client_without_mail_transport.post(
            "/api/v1/auth/magic-link/request", json={"email": ADRESSE}
        )
        assert response.status_code == 503
        assert response.json()["code"] == "MAIL_TRANSPORT_UNAVAILABLE"

    def test_recovery_reports_the_missing_capability(
        self, client_without_mail_transport, anna
    ) -> None:  # type: ignore[no-untyped-def]
        response = client_without_mail_transport.post(
            "/api/v1/auth/recovery/request", json={"email": ADRESSE}
        )
        assert response.status_code == 503

    def test_no_token_is_created(self, client_without_mail_transport, session, anna) -> None:  # type: ignore[no-untyped-def]
        "The Endpoint runs gar not erst to."
        client_without_mail_transport.post(
            "/api/v1/auth/magic-link/request", json={"email": ADRESSE}
        )
        assert session.execute(select(MagicLinkToken)).scalars().all() == []

    def test_password_sign_in_remains_possible(self, client_without_mail_transport, anna) -> None:  # type: ignore[no-untyped-def]
        "Without Mail transport are missing Sign-in methods, aber not the Sign-in."
        response = client_without_mail_transport.post(
            "/api/v1/auth/sign-in",
            json={"email": ADRESSE, "password": GUTES_PASSWORT, "deviceName": "Test"},
        )
        assert response.status_code == 200


class TestMagicLink:
    def test_known_address_gets_a_link(self, client, mailbox, anna) -> None:  # type: ignore[no-untyped-def]
        response = client.post("/api/v1/auth/magic-link/request", json={"email": ADRESSE})
        assert response.status_code == 202
        assert len(mailbox.nachrichten) == 1
        assert mailbox.nachrichten[0].to == ADRESSE
        assert "token=" in mailbox.nachrichten[0].body

    def test_unknown_address_sees_genauso_aus(self, client, mailbox, anna) -> None:  # type: ignore[no-untyped-def]
        "Otherwise would be this Endpoint a Verzeichnis all Accounts."
        known = client.post("/api/v1/auth/magic-link/request", json={"email": ADRESSE})
        unknown = client.post(
            "/api/v1/auth/magic-link/request", json={"email": "niemand@example.org"}
        )
        assert known.status_code == unknown.status_code == 202
        assert known.text == unknown.text
        assert [n.to for n in mailbox.nachrichten] == [ADRESSE]

    def test_the_link_reports_to(self, client, mailbox, anna) -> None:  # type: ignore[no-untyped-def]
        client.post("/api/v1/auth/magic-link/request", json={"email": ADRESSE})
        response = client.post(
            "/api/v1/auth/magic-link/consume",
            json={"token": mailbox.letzter_token, "deviceName": "Pixel"},
        )
        assert response.status_code == 201

        access_token = response.json()["tokens"]["accessToken"]
        assert client.get("/api/v1/auth/me", headers=auth(access_token)).status_code == 200

    def test_the_redeemed_link_verifies_the_address(self, client, session, mailbox, anna) -> None:  # type: ignore[no-untyped-def]
        "Who the Link in the Postfach opens, has the Address nachgewiesen."
        assert address_von(session).verified_at is None

        client.post("/api/v1/auth/magic-link/request", json={"email": ADRESSE})
        client.post("/api/v1/auth/magic-link/consume", json={"token": mailbox.letzter_token})
        session.expire_all()
        assert address_von(session).verified_at is not None

    def test_er_applies_exactly_einmal(self, client, mailbox, anna) -> None:  # type: ignore[no-untyped-def]
        client.post("/api/v1/auth/magic-link/request", json={"email": ADRESSE})
        token = mailbox.letzter_token
        assert (
            client.post("/api/v1/auth/magic-link/consume", json={"token": token}).status_code == 201
        )

        second = client.post("/api/v1/auth/magic-link/consume", json={"token": token})
        assert second.status_code == 422
        assert second.json()["code"] == "ACTION_TOKEN_INVALID"

    def test_a_new_request_invalidates_the_old(self, client, mailbox, anna) -> None:  # type: ignore[no-untyped-def]
        "Otherwise haeufen itself valid Sign-in credentials in the Postfach to."
        client.post("/api/v1/auth/magic-link/request", json={"email": ADRESSE})
        alt = mailbox.letzter_token
        client.post("/api/v1/auth/magic-link/request", json={"email": ADRESSE})
        new = mailbox.letzter_token

        assert (
            client.post("/api/v1/auth/magic-link/consume", json={"token": alt}).status_code == 422
        )
        assert (
            client.post("/api/v1/auth/magic-link/consume", json={"token": new}).status_code == 201
        )

    def test_expired_link_applies_not(self, client, session, mailbox, anna) -> None:  # type: ignore[no-untyped-def]
        client.post("/api/v1/auth/magic-link/request", json={"email": ADRESSE})
        token = mailbox.letzter_token

        modell = session.execute(
            select(MagicLinkToken).where(MagicLinkToken.token_hash == hash_token(token))
        ).scalar_one()
        modell.expires_at = now() - timedelta(minutes=1)
        session.flush()

        assert (
            client.post("/api/v1/auth/magic-link/consume", json={"token": token}).status_code == 422
        )

    def test_malformed_applies_not(self, client, anna) -> None:  # type: ignore[no-untyped-def]
        for token in ("", "nicht-echt", "x" * 200):
            assert (
                client.post("/api/v1/auth/magic-link/consume", json={"token": token}).status_code
                == 422
            )

    def test_the_plaintext_is_stored_not_in_the_database(
        self, client, session, mailbox, anna
    ) -> None:  # type: ignore[no-untyped-def]
        client.post("/api/v1/auth/magic-link/request", json={"email": ADRESSE})
        token = mailbox.letzter_token

        hashes = session.execute(select(MagicLinkToken.token_hash)).scalars().all()
        assert token not in hashes
        assert hash_token(token) in hashes

    def test_to_viele_anforderungen_werden_gebremst(self, client, anna) -> None:  # type: ignore[no-untyped-def]
        for _ in range(rate_limit.MAGIC_LINK.attempts):
            assert (
                client.post("/api/v1/auth/magic-link/request", json={"email": ADRESSE}).status_code
                == 202
            )
        gebremst = client.post("/api/v1/auth/magic-link/request", json={"email": ADRESSE})
        assert gebremst.status_code == 429
        assert gebremst.json()["code"] == "RATE_LIMITED"

    def test_the_rate_limit_applies_auch_for_unknown_addresses(self, client, anna) -> None:  # type: ignore[no-untyped-def]
        "Otherwise would be the Unterschied in the Behavior itself the Disclosure."
        for _ in range(rate_limit.MAGIC_LINK.attempts):
            client.post("/api/v1/auth/magic-link/request", json={"email": "wer@example.org"})
        gebremst = client.post("/api/v1/auth/magic-link/request", json={"email": "wer@example.org"})
        assert gebremst.status_code == 429


class TestAdressbestaetigung:
    def test_signed_in_anfordern_and_verify(self, client, session, mailbox, anna) -> None:  # type: ignore[no-untyped-def]
        headers = auth(anna["tokens"]["accessToken"])
        assert (
            client.post("/api/v1/auth/email/verification/request", headers=headers).status_code
            == 202
        )

        response = client.post(
            "/api/v1/auth/email/verification/confirm",
            json={"token": mailbox.letzter_token},
        )
        assert response.status_code == 204

        session.expire_all()
        assert address_von(session).verified_at is not None

    def test_without_sign_in_no_delivery(self, client, mailbox, anna) -> None:  # type: ignore[no-untyped-def]
        assert client.post("/api/v1/auth/email/verification/request").status_code == 401
        assert mailbox.nachrichten == []

    def test_bereits_bestaetigte_address_gets_nothing(self, client, session, mailbox, anna) -> None:  # type: ignore[no-untyped-def]
        address_von(session).verified_at = now()
        session.flush()

        headers = auth(anna["tokens"]["accessToken"])
        assert (
            client.post("/api/v1/auth/email/verification/request", headers=headers).status_code
            == 202
        )
        assert mailbox.nachrichten == []


class TestRecovery:
    def _link_anfordern(self, client, mailbox) -> str:  # type: ignore[no-untyped-def]
        assert (
            client.post("/api/v1/auth/recovery/request", json={"email": ADRESSE}).status_code == 202
        )
        return mailbox.letzter_token

    def test_new_password_applies_and_the_old_not_more(self, client, mailbox, anna) -> None:  # type: ignore[no-untyped-def]
        token = self._link_anfordern(client, mailbox)
        response = client.post(
            "/api/v1/auth/recovery/consume",
            json={"token": token, "newPassword": NEUES_PASSWORT},
        )
        assert response.status_code == 201

        alt = client.post(
            "/api/v1/auth/sign-in", json={"email": ADRESSE, "password": GUTES_PASSWORT}
        )
        assert alt.status_code == 401
        new = client.post(
            "/api/v1/auth/sign-in", json={"email": ADRESSE, "password": NEUES_PASSWORT}
        )
        assert new.status_code == 200

    def test_all_bisherigen_sessions_enden(self, client, mailbox, anna) -> None:  # type: ignore[no-untyped-def]
        "Who be Password resets, often suspects oft a foreign Access."
        old_access_token = anna["tokens"]["accessToken"]
        assert client.get("/api/v1/auth/me", headers=auth(old_access_token)).status_code == 200

        token = self._link_anfordern(client, mailbox)
        response = client.post(
            "/api/v1/auth/recovery/consume",
            json={"token": token, "newPassword": NEUES_PASSWORT},
        )

        assert client.get("/api/v1/auth/me", headers=auth(old_access_token)).status_code == 401
        new_access_token = response.json()["tokens"]["accessToken"]
        assert client.get("/api/v1/auth/me", headers=auth(new_access_token)).status_code == 200

    def test_unknown_address_sees_genauso_aus(self, client, mailbox, anna) -> None:  # type: ignore[no-untyped-def]
        known = client.post("/api/v1/auth/recovery/request", json={"email": ADRESSE})
        unknown = client.post(
            "/api/v1/auth/recovery/request", json={"email": "niemand@example.org"}
        )
        assert known.status_code == unknown.status_code == 202
        assert known.text == unknown.text
        assert len(mailbox.nachrichten) == 1

    def test_account_without_password_gets_no_link(self, client, session, mailbox) -> None:  # type: ignore[no-untyped-def]
        "Recovery richtet no additional Sign-in method a."
        account = Account(display_name="Nur OIDC")
        session.add(account)
        session.flush()
        session.add(AccountEmail(account_id=account.id, email="oidc@example.org", is_primary=True))
        session.add(
            AuthIdentity(
                account_id=account.id,
                provider=AuthProvider.OIDC.value,
                issuer="https://idp.example",
                subject="abc",
                connection_id="haupt",
            )
        )
        session.flush()

        assert (
            client.post(
                "/api/v1/auth/recovery/request", json={"email": "oidc@example.org"}
            ).status_code
            == 202
        )
        assert mailbox.nachrichten == []

    def test_weak_password_consumed_the_token_not(self, client, mailbox, anna) -> None:  # type: ignore[no-untyped-def]
        token = self._link_anfordern(client, mailbox)
        schwach = client.post(
            "/api/v1/auth/recovery/consume", json={"token": token, "newPassword": "kurz"}
        )
        assert schwach.status_code == 422

        wieder = client.post(
            "/api/v1/auth/recovery/consume",
            json={"token": token, "newPassword": NEUES_PASSWORT},
        )
        assert wieder.status_code == 201

    def test_er_applies_exactly_einmal(self, client, mailbox, anna) -> None:  # type: ignore[no-untyped-def]
        token = self._link_anfordern(client, mailbox)
        client.post(
            "/api/v1/auth/recovery/consume",
            json={"token": token, "newPassword": NEUES_PASSWORT},
        )
        second = client.post(
            "/api/v1/auth/recovery/consume",
            json={"token": token, "newPassword": "noch-ein-langes-passwort-hier"},
        )
        assert second.status_code == 422


class TestKeinTokenGiltImFremdenAblauf:
    "Separate tables instead of a check: the token is not searched there."

    def test_magic_link_token_works_not_zur_recovery(self, client, mailbox, anna) -> None:  # type: ignore[no-untyped-def]
        client.post("/api/v1/auth/magic-link/request", json={"email": ADRESSE})
        token = mailbox.letzter_token

        response = client.post(
            "/api/v1/auth/recovery/consume",
            json={"token": token, "newPassword": NEUES_PASSWORT},
        )
        assert response.status_code == 422

    def test_recovery_token_reports_not_to(self, client, mailbox, anna) -> None:  # type: ignore[no-untyped-def]
        client.post("/api/v1/auth/recovery/request", json={"email": ADRESSE})
        token = mailbox.letzter_token

        assert (
            client.post("/api/v1/auth/magic-link/consume", json={"token": token}).status_code == 422
        )

    def test_verifikationstoken_reports_not_to(self, client, mailbox, anna) -> None:  # type: ignore[no-untyped-def]
        headers = auth(anna["tokens"]["accessToken"])
        client.post("/api/v1/auth/email/verification/request", headers=headers)
        token = mailbox.letzter_token

        assert (
            client.post("/api/v1/auth/magic-link/consume", json={"token": token}).status_code == 422
        )

    def test_every_art_liegt_in_ihrer_own_table(self, client, session, mailbox, anna) -> None:  # type: ignore[no-untyped-def]
        headers = auth(anna["tokens"]["accessToken"])
        client.post("/api/v1/auth/magic-link/request", json={"email": ADRESSE})
        client.post("/api/v1/auth/recovery/request", json={"email": ADRESSE})
        client.post("/api/v1/auth/email/verification/request", headers=headers)

        for modell in (MagicLinkToken, AccountRecoveryToken, EmailVerificationToken):
            assert len(session.execute(select(modell)).scalars().all()) == 1


class TestSitzungsausgabe:
    def test_every_successful_weg_endet_in_a_device_session(
        self, client, session, mailbox, anna
    ) -> None:  # type: ignore[no-untyped-def]
        "It exists no zweiten Ort, to the Tokens entstehen."
        vorher = len(session.execute(select(DeviceSession)).scalars().all())

        client.post("/api/v1/auth/magic-link/request", json={"email": ADRESSE})
        client.post("/api/v1/auth/magic-link/consume", json={"token": mailbox.letzter_token})

        afterwards = session.execute(select(DeviceSession)).scalars().all()
        assert len(afterwards) == vorher + 1
        assert all(device.refresh_token_hash for device in afterwards)
