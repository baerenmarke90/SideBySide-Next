"""Magic Link, Adressbestaetigung und Account Recovery - ueber die Endpunkte.

Drei Ablaeufe mit derselben Grundfrage: Wer eine Adresse eingibt, darf aus
der Antwort nicht ablesen, ob es sie gibt. Und ein Token aus dem einen
Ablauf darf im anderen nicht gelten.
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
    """Sammelt statt zu senden."""

    def __init__(self) -> None:
        self.nachrichten: list[MailMessage] = []

    def send(self, message: MailMessage) -> None:
        self.nachrichten.append(message)

    @property
    def letzter_token(self) -> str:
        treffer = re.search(r"token=([A-Za-z0-9_\-]+)", self.nachrichten[-1].body)
        assert treffer is not None, "Die Nachricht enthaelt keinen Link"
        return treffer.group(1)


@pytest.fixture
def postfach() -> Postfach:
    return Postfach()


@pytest.fixture
def client(session: Session, postfach: Postfach) -> Iterator[object]:  # type: ignore[override]
    """Wie der gemeinsame Client, aber mit einem Postfach statt Mailversand."""
    from fastapi.testclient import TestClient

    from sidebyside.db.session import get_session
    from sidebyside.mail import sender
    from sidebyside.main import create_app

    app = create_app()
    app.dependency_overrides[get_session] = lambda: session
    app.dependency_overrides[sender] = lambda: postfach
    yield TestClient(app, raise_server_exceptions=False)


@pytest.fixture
def anna(session: Session, client):  # type: ignore[no-untyped-def]
    """Ein registrierter Account mit Passwort."""
    from tests.conftest import TEST_BOOTSTRAP_TOKEN

    antwort = client.post(
        "/api/v1/auth/register",
        json={
            "displayName": "Anna",
            "email": ADRESSE,
            "password": GUTES_PASSWORT,
            "bootstrapToken": TEST_BOOTSTRAP_TOKEN,
        },
    )
    assert antwort.status_code == 201
    return antwort.json()


def adresse_von(session: Session) -> AccountEmail:
    eintrag = session.execute(
        select(AccountEmail).where(AccountEmail.email == ADRESSE)
    ).scalar_one()
    return eintrag


class TestMagicLink:
    def test_bekannte_adresse_bekommt_einen_link(self, client, postfach, anna) -> None:  # type: ignore[no-untyped-def]
        antwort = client.post("/api/v1/auth/magic-link/request", json={"email": ADRESSE})
        assert antwort.status_code == 202
        assert len(postfach.nachrichten) == 1
        assert postfach.nachrichten[0].to == ADRESSE
        assert "token=" in postfach.nachrichten[0].body

    def test_unbekannte_adresse_sieht_genauso_aus(self, client, postfach, anna) -> None:  # type: ignore[no-untyped-def]
        """Sonst waere dieser Endpunkt ein Verzeichnis aller Konten."""
        bekannt = client.post("/api/v1/auth/magic-link/request", json={"email": ADRESSE})
        unbekannt = client.post(
            "/api/v1/auth/magic-link/request", json={"email": "niemand@example.org"}
        )
        assert bekannt.status_code == unbekannt.status_code == 202
        assert bekannt.text == unbekannt.text
        assert [n.to for n in postfach.nachrichten] == [ADRESSE]

    def test_der_link_meldet_an(self, client, postfach, anna) -> None:  # type: ignore[no-untyped-def]
        client.post("/api/v1/auth/magic-link/request", json={"email": ADRESSE})
        antwort = client.post(
            "/api/v1/auth/magic-link/consume",
            json={"token": postfach.letzter_token, "deviceName": "Pixel"},
        )
        assert antwort.status_code == 201

        zugang = antwort.json()["tokens"]["accessToken"]
        assert client.get("/api/v1/auth/me", headers=auth(zugang)).status_code == 200

    def test_der_eingeloeste_link_bestaetigt_die_adresse(
        self, client, session, postfach, anna
    ) -> None:  # type: ignore[no-untyped-def]
        """Wer den Link im Postfach oeffnet, hat die Adresse nachgewiesen."""
        assert adresse_von(session).verified_at is None

        client.post("/api/v1/auth/magic-link/request", json={"email": ADRESSE})
        client.post("/api/v1/auth/magic-link/consume", json={"token": postfach.letzter_token})
        session.expire_all()
        assert adresse_von(session).verified_at is not None

    def test_er_gilt_genau_einmal(self, client, postfach, anna) -> None:  # type: ignore[no-untyped-def]
        client.post("/api/v1/auth/magic-link/request", json={"email": ADRESSE})
        token = postfach.letzter_token
        assert (
            client.post("/api/v1/auth/magic-link/consume", json={"token": token}).status_code == 201
        )

        zweite = client.post("/api/v1/auth/magic-link/consume", json={"token": token})
        assert zweite.status_code == 422
        assert zweite.json()["code"] == "ACTION_TOKEN_INVALID"

    def test_eine_neue_anforderung_entwertet_die_alte(self, client, postfach, anna) -> None:  # type: ignore[no-untyped-def]
        """Sonst haeufen sich gueltige Anmeldenachweise im Postfach an."""
        client.post("/api/v1/auth/magic-link/request", json={"email": ADRESSE})
        alt = postfach.letzter_token
        client.post("/api/v1/auth/magic-link/request", json={"email": ADRESSE})
        neu = postfach.letzter_token

        assert (
            client.post("/api/v1/auth/magic-link/consume", json={"token": alt}).status_code == 422
        )
        assert (
            client.post("/api/v1/auth/magic-link/consume", json={"token": neu}).status_code == 201
        )

    def test_abgelaufener_link_gilt_nicht(self, client, session, postfach, anna) -> None:  # type: ignore[no-untyped-def]
        client.post("/api/v1/auth/magic-link/request", json={"email": ADRESSE})
        token = postfach.letzter_token

        modell = session.execute(
            select(MagicLinkToken).where(MagicLinkToken.token_hash == hash_token(token))
        ).scalar_one()
        modell.expires_at = now() - timedelta(minutes=1)
        session.flush()

        assert (
            client.post("/api/v1/auth/magic-link/consume", json={"token": token}).status_code == 422
        )

    def test_unfug_gilt_nicht(self, client, anna) -> None:  # type: ignore[no-untyped-def]
        for token in ("", "nicht-echt", "x" * 200):
            assert (
                client.post("/api/v1/auth/magic-link/consume", json={"token": token}).status_code
                == 422
            )

    def test_der_klartext_steht_nicht_in_der_datenbank(
        self, client, session, postfach, anna
    ) -> None:  # type: ignore[no-untyped-def]
        client.post("/api/v1/auth/magic-link/request", json={"email": ADRESSE})
        token = postfach.letzter_token

        hashes = session.execute(select(MagicLinkToken.token_hash)).scalars().all()
        assert token not in hashes
        assert hash_token(token) in hashes

    def test_zu_viele_anforderungen_werden_gebremst(self, client, anna) -> None:  # type: ignore[no-untyped-def]
        for _ in range(rate_limit.MAGIC_LINK.attempts):
            assert (
                client.post("/api/v1/auth/magic-link/request", json={"email": ADRESSE}).status_code
                == 202
            )
        gebremst = client.post("/api/v1/auth/magic-link/request", json={"email": ADRESSE})
        assert gebremst.status_code == 429
        assert gebremst.json()["code"] == "RATE_LIMITED"

    def test_die_bremse_gilt_auch_fuer_unbekannte_adressen(self, client, anna) -> None:  # type: ignore[no-untyped-def]
        """Sonst waere der Unterschied im Verhalten selbst die Auskunft."""
        for _ in range(rate_limit.MAGIC_LINK.attempts):
            client.post("/api/v1/auth/magic-link/request", json={"email": "wer@example.org"})
        gebremst = client.post("/api/v1/auth/magic-link/request", json={"email": "wer@example.org"})
        assert gebremst.status_code == 429


class TestAdressbestaetigung:
    def test_angemeldet_anfordern_und_bestaetigen(self, client, session, postfach, anna) -> None:  # type: ignore[no-untyped-def]
        kopf = auth(anna["tokens"]["accessToken"])
        assert (
            client.post("/api/v1/auth/email/verification/request", headers=kopf).status_code == 202
        )

        antwort = client.post(
            "/api/v1/auth/email/verification/confirm",
            json={"token": postfach.letzter_token},
        )
        assert antwort.status_code == 204

        session.expire_all()
        assert adresse_von(session).verified_at is not None

    def test_ohne_anmeldung_kein_versand(self, client, postfach, anna) -> None:  # type: ignore[no-untyped-def]
        assert client.post("/api/v1/auth/email/verification/request").status_code == 401
        assert postfach.nachrichten == []

    def test_bereits_bestaetigte_adresse_bekommt_nichts(
        self, client, session, postfach, anna
    ) -> None:  # type: ignore[no-untyped-def]
        adresse_von(session).verified_at = now()
        session.flush()

        kopf = auth(anna["tokens"]["accessToken"])
        assert (
            client.post("/api/v1/auth/email/verification/request", headers=kopf).status_code == 202
        )
        assert postfach.nachrichten == []


class TestRecovery:
    def _link_anfordern(self, client, postfach) -> str:  # type: ignore[no-untyped-def]
        assert (
            client.post("/api/v1/auth/recovery/request", json={"email": ADRESSE}).status_code == 202
        )
        return postfach.letzter_token

    def test_neues_passwort_gilt_und_das_alte_nicht_mehr(self, client, postfach, anna) -> None:  # type: ignore[no-untyped-def]
        token = self._link_anfordern(client, postfach)
        antwort = client.post(
            "/api/v1/auth/recovery/consume",
            json={"token": token, "newPassword": NEUES_PASSWORT},
        )
        assert antwort.status_code == 201

        alt = client.post(
            "/api/v1/auth/sign-in", json={"email": ADRESSE, "password": GUTES_PASSWORT}
        )
        assert alt.status_code == 401
        neu = client.post(
            "/api/v1/auth/sign-in", json={"email": ADRESSE, "password": NEUES_PASSWORT}
        )
        assert neu.status_code == 200

    def test_alle_bisherigen_sitzungen_enden(self, client, postfach, anna) -> None:  # type: ignore[no-untyped-def]
        """Wer sein Passwort zuruecksetzt, vermutet oft einen fremden Zugriff."""
        alter_zugang = anna["tokens"]["accessToken"]
        assert client.get("/api/v1/auth/me", headers=auth(alter_zugang)).status_code == 200

        token = self._link_anfordern(client, postfach)
        antwort = client.post(
            "/api/v1/auth/recovery/consume",
            json={"token": token, "newPassword": NEUES_PASSWORT},
        )

        assert client.get("/api/v1/auth/me", headers=auth(alter_zugang)).status_code == 401
        neuer_zugang = antwort.json()["tokens"]["accessToken"]
        assert client.get("/api/v1/auth/me", headers=auth(neuer_zugang)).status_code == 200

    def test_unbekannte_adresse_sieht_genauso_aus(self, client, postfach, anna) -> None:  # type: ignore[no-untyped-def]
        bekannt = client.post("/api/v1/auth/recovery/request", json={"email": ADRESSE})
        unbekannt = client.post(
            "/api/v1/auth/recovery/request", json={"email": "niemand@example.org"}
        )
        assert bekannt.status_code == unbekannt.status_code == 202
        assert bekannt.text == unbekannt.text
        assert len(postfach.nachrichten) == 1

    def test_konto_ohne_passwort_bekommt_keinen_link(self, client, session, postfach) -> None:  # type: ignore[no-untyped-def]
        """Recovery richtet keinen zusaetzlichen Anmeldeweg ein."""
        konto = Account(display_name="Nur OIDC")
        session.add(konto)
        session.flush()
        session.add(AccountEmail(account_id=konto.id, email="oidc@example.org", is_primary=True))
        session.add(
            AuthIdentity(
                account_id=konto.id,
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
        assert postfach.nachrichten == []

    def test_schwaches_passwort_verbraucht_den_token_nicht(self, client, postfach, anna) -> None:  # type: ignore[no-untyped-def]
        token = self._link_anfordern(client, postfach)
        schwach = client.post(
            "/api/v1/auth/recovery/consume", json={"token": token, "newPassword": "kurz"}
        )
        assert schwach.status_code == 422

        wieder = client.post(
            "/api/v1/auth/recovery/consume",
            json={"token": token, "newPassword": NEUES_PASSWORT},
        )
        assert wieder.status_code == 201

    def test_er_gilt_genau_einmal(self, client, postfach, anna) -> None:  # type: ignore[no-untyped-def]
        token = self._link_anfordern(client, postfach)
        client.post(
            "/api/v1/auth/recovery/consume",
            json={"token": token, "newPassword": NEUES_PASSWORT},
        )
        zweite = client.post(
            "/api/v1/auth/recovery/consume",
            json={"token": token, "newPassword": "noch-ein-langes-passwort-hier"},
        )
        assert zweite.status_code == 422


class TestKeinTokenGiltImFremdenAblauf:
    """Getrennte Tabellen statt einer Pruefung: der Token wird dort nicht gesucht."""

    def test_magic_link_token_taugt_nicht_zur_wiederherstellung(
        self, client, postfach, anna
    ) -> None:  # type: ignore[no-untyped-def]
        client.post("/api/v1/auth/magic-link/request", json={"email": ADRESSE})
        token = postfach.letzter_token

        antwort = client.post(
            "/api/v1/auth/recovery/consume",
            json={"token": token, "newPassword": NEUES_PASSWORT},
        )
        assert antwort.status_code == 422

    def test_recovery_token_meldet_nicht_an(self, client, postfach, anna) -> None:  # type: ignore[no-untyped-def]
        client.post("/api/v1/auth/recovery/request", json={"email": ADRESSE})
        token = postfach.letzter_token

        assert (
            client.post("/api/v1/auth/magic-link/consume", json={"token": token}).status_code == 422
        )

    def test_verifikationstoken_meldet_nicht_an(self, client, postfach, anna) -> None:  # type: ignore[no-untyped-def]
        kopf = auth(anna["tokens"]["accessToken"])
        client.post("/api/v1/auth/email/verification/request", headers=kopf)
        token = postfach.letzter_token

        assert (
            client.post("/api/v1/auth/magic-link/consume", json={"token": token}).status_code == 422
        )

    def test_jede_art_liegt_in_ihrer_eigenen_tabelle(self, client, session, postfach, anna) -> None:  # type: ignore[no-untyped-def]
        kopf = auth(anna["tokens"]["accessToken"])
        client.post("/api/v1/auth/magic-link/request", json={"email": ADRESSE})
        client.post("/api/v1/auth/recovery/request", json={"email": ADRESSE})
        client.post("/api/v1/auth/email/verification/request", headers=kopf)

        for modell in (MagicLinkToken, AccountRecoveryToken, EmailVerificationToken):
            assert len(session.execute(select(modell)).scalars().all()) == 1


class TestSitzungsausgabe:
    def test_jeder_erfolgreiche_weg_endet_in_einer_geraetesitzung(
        self, client, session, postfach, anna
    ) -> None:  # type: ignore[no-untyped-def]
        """Es gibt keinen zweiten Ort, an dem Tokens entstehen."""
        vorher = len(session.execute(select(DeviceSession)).scalars().all())

        client.post("/api/v1/auth/magic-link/request", json={"email": ADRESSE})
        client.post("/api/v1/auth/magic-link/consume", json={"token": postfach.letzter_token})

        nachher = session.execute(select(DeviceSession)).scalars().all()
        assert len(nachher) == vorher + 1
        assert all(geraet.refresh_token_hash for geraet in nachher)
