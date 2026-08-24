"""Passkeys: Registrierung und Anmeldung gegen einen virtuellen Authenticator.

Der Authenticator in `tests/support/authenticator.py` signiert mit einem
echten P-256-Schluessel. Damit prueft diese Suite die Signatur-, Flag- und
Zaehlerpruefung wirklich - und nicht nur, dass eine Bibliothek aufgerufen
wurde.
"""

from __future__ import annotations

from typing import Any

import pytest
from cryptography.hazmat.primitives.asymmetric import ec
from sqlalchemy import select
from sqlalchemy.orm import Session

from sidebyside.auth import passkeys
from sidebyside.identity.models import DeviceSession, WebAuthnChallenge, WebAuthnCredential
from tests.conftest import auth, make_account, requires_database, sign_in
from tests.support.authenticator import VirtualAuthenticator

pytestmark = [pytest.mark.integration, requires_database]

REGISTRIERUNG_START = "/api/v1/auth/passkeys/registration/start"
REGISTRIERUNG_ENDE = "/api/v1/auth/passkeys/registration/finish"
ANMELDUNG_START = "/api/v1/auth/passkeys/authentication/start"
ANMELDUNG_ENDE = "/api/v1/auth/passkeys/authentication/finish"


@pytest.fixture
def geraet() -> VirtualAuthenticator:
    return VirtualAuthenticator()


@pytest.fixture
def anna(session: Session):  # type: ignore[no-untyped-def]
    konto = make_account(session, "Anna")
    session.flush()
    return {"konto": konto, "kopf": auth(sign_in(session, konto))}


def registriere(client, anna, geraet: VirtualAuthenticator, **zusatz: Any):  # type: ignore[no-untyped-def]
    optionen = client.post(REGISTRIERUNG_START, headers=anna["kopf"]).json()
    antwort = geraet.register(optionen, **zusatz)
    return client.post(
        REGISTRIERUNG_ENDE,
        json={"credential": antwort, "name": "Mein Telefon"},
        headers=anna["kopf"],
    )


def melde_an(client, geraet: VirtualAuthenticator, **zusatz: Any):  # type: ignore[no-untyped-def]
    optionen = client.post(ANMELDUNG_START).json()
    antwort = geraet.authenticate(optionen, **zusatz)
    return client.post(ANMELDUNG_ENDE, json={"credential": antwort, "deviceName": "Pixel"})


class TestRegistrierung:
    def test_ein_passkey_entsteht(self, client, session, anna, geraet) -> None:  # type: ignore[no-untyped-def]
        antwort = registriere(client, anna, geraet)
        assert antwort.status_code == 201, antwort.text
        assert antwort.json()["name"] == "Mein Telefon"

        gespeichert = session.execute(select(WebAuthnCredential)).scalars().all()
        assert len(gespeichert) == 1
        assert gespeichert[0].credential_id == geraet.credential_id
        assert gespeichert[0].account_id == anna["konto"].id

    def test_der_private_schluessel_erreicht_den_server_nie(
        self, client, session, anna, geraet
    ) -> None:  # type: ignore[no-untyped-def]
        registriere(client, anna, geraet)
        gespeichert = session.execute(select(WebAuthnCredential)).scalars().one()

        geheim = geraet.schluessel.private_numbers().private_value.to_bytes(32, "big")
        assert geheim not in gespeichert.public_key

    def test_ohne_anmeldung_kein_beginn(self, client) -> None:  # type: ignore[no-untyped-def]
        assert client.post(REGISTRIERUNG_START).status_code == 401

    def test_die_optionen_nennen_die_bekannten_credentials(self, client, anna, geraet) -> None:  # type: ignore[no-untyped-def]
        """Damit derselbe Authenticator nicht zweimal registriert wird."""
        registriere(client, anna, geraet)
        optionen = client.post(REGISTRIERUNG_START, headers=anna["kopf"]).json()
        assert len(optionen["excludeCredentials"]) == 1

    def test_falsche_herkunft_wird_abgewiesen(self, client, anna, geraet) -> None:  # type: ignore[no-untyped-def]
        antwort = registriere(client, anna, geraet, origin="https://boese.example")
        assert antwort.status_code == 422
        assert antwort.json()["code"] == "PASSKEY_CEREMONY_INVALID"

    def test_falsche_rp_id_wird_abgewiesen(self, client, anna, geraet) -> None:  # type: ignore[no-untyped-def]
        antwort = registriere(client, anna, geraet, rp_id="boese.example")
        assert antwort.status_code == 422

    def test_ohne_begonnene_ceremony_geht_nichts(self, client, anna, geraet) -> None:  # type: ignore[no-untyped-def]
        optionen = client.post(REGISTRIERUNG_START, headers=anna["kopf"]).json()
        antwort = geraet.register(optionen)
        assert (
            client.post(
                REGISTRIERUNG_ENDE, json={"credential": antwort}, headers=anna["kopf"]
            ).status_code
            == 201
        )
        # Die Challenge ist verbraucht; dieselbe Antwort gilt kein zweites Mal.
        zweite = client.post(REGISTRIERUNG_ENDE, json={"credential": antwort}, headers=anna["kopf"])
        assert zweite.status_code == 422

    def test_dieselbe_credential_id_nur_einmal(self, client, session, anna, geraet) -> None:  # type: ignore[no-untyped-def]
        """Credential-IDs sind global eindeutig - auch ueber Konten hinweg."""
        registriere(client, anna, geraet)

        ben = make_account(session, "Ben")
        session.flush()
        anderer = {"konto": ben, "kopf": auth(sign_in(session, ben))}
        antwort = registriere(client, anderer, geraet)
        assert antwort.status_code == 422


class TestAnmeldung:
    def test_mit_dem_passkey_anmelden(self, client, anna, geraet) -> None:  # type: ignore[no-untyped-def]
        registriere(client, anna, geraet)
        antwort = melde_an(client, geraet)
        assert antwort.status_code == 201, antwort.text

        zugang = antwort.json()["tokens"]["accessToken"]
        assert client.get("/api/v1/auth/me", headers=auth(zugang)).status_code == 200

    def test_es_entsteht_genau_eine_geraetesitzung(self, client, session, anna, geraet) -> None:  # type: ignore[no-untyped-def]
        registriere(client, anna, geraet)
        vorher = len(session.execute(select(DeviceSession)).scalars().all())
        melde_an(client, geraet)
        assert len(session.execute(select(DeviceSession)).scalars().all()) == vorher + 1

    def test_unbekanntes_credential_wird_abgewiesen(self, client, anna, geraet) -> None:  # type: ignore[no-untyped-def]
        registriere(client, anna, geraet)
        fremdes = VirtualAuthenticator()
        antwort = melde_an(client, fremdes)
        assert antwort.status_code == 422
        assert antwort.json()["code"] == "PASSKEY_CEREMONY_INVALID"

    def test_fremde_signatur_wird_abgewiesen(self, client, anna, geraet) -> None:  # type: ignore[no-untyped-def]
        registriere(client, anna, geraet)
        fremder_schluessel = ec.generate_private_key(ec.SECP256R1())
        antwort = melde_an(client, geraet, signieren_mit=fremder_schluessel)
        assert antwort.status_code == 422

    def test_falsche_herkunft_wird_abgewiesen(self, client, anna, geraet) -> None:  # type: ignore[no-untyped-def]
        registriere(client, anna, geraet)
        antwort = melde_an(client, geraet, origin="https://boese.example")
        assert antwort.status_code == 422

    def test_falsche_rp_id_wird_abgewiesen(self, client, anna, geraet) -> None:  # type: ignore[no-untyped-def]
        registriere(client, anna, geraet)
        antwort = melde_an(client, geraet, rp_id="boese.example")
        assert antwort.status_code == 422

    def test_fremde_challenge_wird_abgewiesen(self, client, anna, geraet) -> None:  # type: ignore[no-untyped-def]
        """Eine Assertion gilt fuer genau die Ceremony, die sie angefordert hat."""
        registriere(client, anna, geraet)
        client.post(ANMELDUNG_START)
        erfunden = geraet.authenticate({"challenge": "ZXR3YXMtYW5kZXJlcw"})
        antwort = client.post(ANMELDUNG_ENDE, json={"credential": erfunden})
        assert antwort.status_code == 422

    def test_die_antwort_gilt_genau_einmal(self, client, anna, geraet) -> None:  # type: ignore[no-untyped-def]
        registriere(client, anna, geraet)
        optionen = client.post(ANMELDUNG_START).json()
        assertion = geraet.authenticate(optionen)

        assert client.post(ANMELDUNG_ENDE, json={"credential": assertion}).status_code == 201
        zweite = client.post(ANMELDUNG_ENDE, json={"credential": assertion})
        assert zweite.status_code == 422


class TestSignaturzaehler:
    def test_der_zaehler_wird_fortgeschrieben(self, client, session, anna, geraet) -> None:  # type: ignore[no-untyped-def]
        registriere(client, anna, geraet)
        melde_an(client, geraet)

        session.expire_all()
        gespeichert = session.execute(select(WebAuthnCredential)).scalars().one()
        assert gespeichert.sign_count == geraet.sign_count
        assert gespeichert.last_used_at is not None

    def test_ein_stehengebliebener_zaehler_deutet_auf_eine_kopie(
        self, client, anna, geraet
    ) -> None:  # type: ignore[no-untyped-def]
        registriere(client, anna, geraet)
        melde_an(client, geraet)
        melde_an(client, geraet)

        antwort = melde_an(client, geraet, zaehler_erhoehen=False)
        assert antwort.status_code == 422
        assert antwort.json()["code"] == "PASSKEY_CEREMONY_INVALID"

    def test_ein_geraet_ohne_zaehler_bleibt_erlaubt(self, client, anna) -> None:  # type: ignore[no-untyped-def]
        """Viele Passkeys zaehlen gar nicht; ein Verbot sperrte sie alle aus."""
        stumm = VirtualAuthenticator()
        registriere(client, anna, stumm)

        for _ in range(3):
            antwort = melde_an(client, stumm, zaehler_erhoehen=False)
            assert antwort.status_code == 201

    def test_auffindbarkeit_zeigt_sich_erst_bei_der_anmeldung(
        self, client, session, anna, geraet
    ) -> None:  # type: ignore[no-untyped-def]
        """Die Registrierung kann sie nur wuenschen, nicht belegen."""
        registriere(client, anna, geraet)
        session.expire_all()
        assert session.execute(select(WebAuthnCredential)).scalars().one().is_discoverable is False

        melde_an(client, geraet)
        session.expire_all()
        assert session.execute(select(WebAuthnCredential)).scalars().one().is_discoverable is True


class TestCeremonyZustand:
    def test_der_start_verraet_keine_konten(self, client, anna, geraet) -> None:  # type: ignore[no-untyped-def]
        """Die Anmeldung beginnt ohne Kontobezug und ohne Kandidatenliste."""
        registriere(client, anna, geraet)
        optionen = client.post(ANMELDUNG_START).json()
        assert not optionen.get("allowCredentials")
        assert "Anna" not in str(optionen)

    def test_der_wartungsjob_raeumt_verbrauchte_challenges(
        self, client, session, anna, geraet
    ) -> None:  # type: ignore[no-untyped-def]
        registriere(client, anna, geraet)
        melde_an(client, geraet)

        assert passkeys.prune_challenges(session) == 2
        session.flush()
        assert session.execute(select(WebAuthnChallenge)).scalars().all() == []
