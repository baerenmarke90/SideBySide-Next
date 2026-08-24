"""Registrierung, Anmeldung und Missbrauchsschutz - ueber die Endpunkte."""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from threading import Barrier

import pytest
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from sidebyside.auth import passwords, rate_limit
from sidebyside.auth.tokens import hash_token
from sidebyside.identity.models import (
    Account,
    DeviceSession,
    InstanceBootstrapState,
    RateLimitEvent,
)
from tests.conftest import (
    TEST_BOOTSTRAP_TOKEN,
    auth,
    make_account,
    make_space,
    requires_database,
    sign_in,
)

pytestmark = [pytest.mark.integration, requires_database]

GUTES_PASSWORT = "ein-ausreichend-langes-passwort"


class TestRegistrierung:
    def test_erster_account_braucht_bootstrap_nachweis(self, client, session) -> None:  # type: ignore[no-untyped-def]
        antwort = client.post(
            "/api/v1/auth/register",
            json={
                "displayName": "Anna",
                "email": "Anna@Example.ORG",
                "password": GUTES_PASSWORT,
                "bootstrapToken": TEST_BOOTSTRAP_TOKEN,
            },
        )
        assert antwort.status_code == 201
        assert antwort.json()["tokens"]["accessToken"]

    def test_erster_account_ohne_bootstrap_nachweis_wird_abgewiesen(self, client, session) -> None:  # type: ignore[no-untyped-def]
        antwort = client.post(
            "/api/v1/auth/register",
            json={
                "displayName": "Fremd",
                "email": "fremd@example.org",
                "password": GUTES_PASSWORT,
            },
        )
        assert antwort.status_code == 403
        assert antwort.json()["code"] == "BOOTSTRAP_INVALID"
        assert session.execute(select(func.count()).select_from(Account)).scalar_one() == 0

    def test_falscher_bootstrap_nachweis_wird_nicht_zurueckgegeben(self, client, session) -> None:  # type: ignore[no-untyped-def]
        geheimnis = "falscher-bootstrap-nachweis-mit-genuegend-laenge"
        antwort = client.post(
            "/api/v1/auth/register",
            json={
                "displayName": "Fremd",
                "email": "fremd@example.org",
                "password": GUTES_PASSWORT,
                "bootstrapToken": geheimnis,
            },
        )
        assert antwort.status_code == 403
        assert antwort.json()["code"] == "BOOTSTRAP_INVALID"
        assert geheimnis not in antwort.text
        assert session.execute(select(func.count()).select_from(Account)).scalar_one() == 0

    def test_zweiter_account_braucht_eine_einladung(self, client, session) -> None:  # type: ignore[no-untyped-def]
        """Sonst koennte sich auf einer privaten Instanz anlegen, wer ihre
        Adresse kennt."""
        make_account(session, "Vorhanden")
        session.flush()

        antwort = client.post(
            "/api/v1/auth/register",
            json={
                "displayName": "Fremd",
                "email": "fremd@example.org",
                "password": GUTES_PASSWORT,
            },
        )
        assert antwort.status_code == 403
        assert antwort.json()["code"] == "REGISTRATION_REQUIRES_INVITATION"

    def test_mit_einladung_klappt_es(self, client, session) -> None:  # type: ignore[no-untyped-def]
        anna = make_account(session, "Anna")
        space = make_space(session, anna)
        anna_token = sign_in(session, anna)
        session.flush()

        einladung = client.post(
            f"/api/v1/spaces/{space.id}/invitations", headers=auth(anna_token)
        ).json()

        antwort = client.post(
            "/api/v1/auth/register",
            json={
                "displayName": "Ben",
                "email": "ben@example.org",
                "password": GUTES_PASSWORT,
                "invitationToken": einladung["token"],
            },
        )
        assert antwort.status_code == 201

        ben_token = antwort.json()["tokens"]["accessToken"]
        assert client.get(f"/api/v1/spaces/{space.id}", headers=auth(ben_token)).status_code == 200

    def test_adresse_wird_klein_geschrieben_abgelegt(self, client, session) -> None:  # type: ignore[no-untyped-def]
        client.post(
            "/api/v1/auth/register",
            json={
                "displayName": "Anna",
                "email": "  Anna@Example.ORG ",
                "password": GUTES_PASSWORT,
                "bootstrapToken": TEST_BOOTSTRAP_TOKEN,
            },
        )
        antwort = client.post(
            "/api/v1/auth/sign-in",
            json={"email": "anna@example.org", "password": GUTES_PASSWORT},
        )
        assert antwort.status_code == 200

    @pytest.mark.parametrize("kurz", ["", "kurz", "elfzeichen"])
    def test_zu_kurzes_passwort_wird_abgewiesen(self, client, kurz: str) -> None:  # type: ignore[no-untyped-def]
        antwort = client.post(
            "/api/v1/auth/register",
            json={
                "displayName": "Anna",
                "email": "a@example.org",
                "password": kurz,
                "bootstrapToken": TEST_BOOTSTRAP_TOKEN,
            },
        )
        assert antwort.status_code == 422
        assert antwort.json()["code"] == "PASSWORD_TOO_SHORT"

    @pytest.mark.parametrize("krumm", ["", "keine-adresse", "a@b", "@example.org", "a@.de"])
    def test_krumme_adresse_wird_abgewiesen(self, client, krumm: str) -> None:  # type: ignore[no-untyped-def]
        antwort = client.post(
            "/api/v1/auth/register",
            json={
                "displayName": "Anna",
                "email": krumm,
                "password": GUTES_PASSWORT,
                "bootstrapToken": TEST_BOOTSTRAP_TOKEN,
            },
        )
        assert antwort.status_code == 422

    def test_kein_account_ohne_gueltiges_passwort(self, client, session) -> None:  # type: ignore[no-untyped-def]
        """Sonst entstuende ein Account, dessen Registrierung scheitert."""
        from sidebyside.identity import service as accounts

        client.post(
            "/api/v1/auth/register",
            json={
                "displayName": "Anna",
                "email": "a@example.org",
                "password": "kurz",
                "bootstrapToken": TEST_BOOTSTRAP_TOKEN,
            },
        )
        assert accounts.find_by_email(session, "a@example.org") is None


class TestAnmeldung:
    @pytest.fixture
    def angemeldet(self, client, session):  # type: ignore[no-untyped-def]
        client.post(
            "/api/v1/auth/register",
            json={
                "displayName": "Anna",
                "email": "anna@example.org",
                "password": GUTES_PASSWORT,
                "bootstrapToken": TEST_BOOTSTRAP_TOKEN,
            },
        )
        return "anna@example.org"

    def test_richtige_daten(self, client, angemeldet) -> None:  # type: ignore[no-untyped-def]
        antwort = client.post(
            "/api/v1/auth/sign-in",
            json={"email": angemeldet, "password": GUTES_PASSWORT},
        )
        assert antwort.status_code == 200
        assert antwort.json()["account"]["displayName"] == "Anna"

    def test_falsches_passwort(self, client, angemeldet) -> None:  # type: ignore[no-untyped-def]
        antwort = client.post(
            "/api/v1/auth/sign-in",
            json={"email": angemeldet, "password": "etwas-ganz-anderes"},
        )
        assert antwort.status_code == 401
        assert antwort.json()["code"] == "INVALID_CREDENTIALS"

    def test_unbekannte_adresse_und_falsches_passwort_sind_ununterscheidbar(
        self, client, angemeldet
    ) -> None:  # type: ignore[no-untyped-def]
        """Ein Unterschied waere ein Weg, Konten aufzuzaehlen."""
        falsch = client.post(
            "/api/v1/auth/sign-in",
            json={"email": angemeldet, "password": "etwas-ganz-anderes"},
        )
        unbekannt = client.post(
            "/api/v1/auth/sign-in",
            json={"email": "gibt-es-nicht@example.org", "password": GUTES_PASSWORT},
        )
        assert falsch.status_code == unbekannt.status_code == 401
        assert falsch.json() == unbekannt.json()

    def test_abgeschalteter_account_kommt_nicht_hinein(self, client, session, angemeldet) -> None:  # type: ignore[no-untyped-def]
        from sidebyside.core.clock import now
        from sidebyside.identity import service as accounts

        konto = accounts.find_by_email(session, angemeldet)
        assert konto is not None
        konto.disabled_at = now()
        session.flush()

        antwort = client.post(
            "/api/v1/auth/sign-in",
            json={"email": angemeldet, "password": GUTES_PASSWORT},
        )
        assert antwort.status_code == 401


class TestSitzungsverwaltung:
    @pytest.fixture
    def sitzung(self, client):  # type: ignore[no-untyped-def]
        return client.post(
            "/api/v1/auth/register",
            json={
                "displayName": "Anna",
                "email": "anna@example.org",
                "password": GUTES_PASSWORT,
                "bootstrapToken": TEST_BOOTSTRAP_TOKEN,
            },
        ).json()

    def test_me_liefert_den_account(self, client, sitzung) -> None:  # type: ignore[no-untyped-def]
        antwort = client.get("/api/v1/auth/me", headers=auth(sitzung["tokens"]["accessToken"]))
        assert antwort.status_code == 200
        assert set(antwort.json()) == {"id", "displayName"}

    def test_erneuern_rotiert(self, client, sitzung) -> None:  # type: ignore[no-untyped-def]
        antwort = client.post(
            "/api/v1/auth/refresh",
            json={"refreshToken": sitzung["tokens"]["refreshToken"]},
        )
        assert antwort.status_code == 200
        assert antwort.json()["refreshToken"] != sitzung["tokens"]["refreshToken"]

    def test_abmelden_entwertet_den_token(self, client, sitzung) -> None:  # type: ignore[no-untyped-def]
        kopf = auth(sitzung["tokens"]["accessToken"])
        assert client.post("/api/v1/auth/sign-out", headers=kopf).status_code == 204
        assert client.get("/api/v1/auth/me", headers=kopf).status_code == 401

    def test_passwortwechsel_beendet_alle_sitzungen(self, client, sitzung) -> None:  # type: ignore[no-untyped-def]
        """Wer sein Passwort aendert, vermutet oft einen fremden Zugriff."""
        kopf = auth(sitzung["tokens"]["accessToken"])
        antwort = client.post(
            "/api/v1/auth/password",
            json={
                "currentPassword": GUTES_PASSWORT,
                "newPassword": "ein-ganz-neues-langes-passwort",
            },
            headers=kopf,
        )
        assert antwort.status_code == 204
        assert client.get("/api/v1/auth/me", headers=kopf).status_code == 401

    def test_passwortwechsel_braucht_das_alte(self, client, sitzung) -> None:  # type: ignore[no-untyped-def]
        antwort = client.post(
            "/api/v1/auth/password",
            json={
                "currentPassword": "falsch-falsch-falsch",
                "newPassword": "ein-ganz-neues-langes-passwort",
            },
            headers=auth(sitzung["tokens"]["accessToken"]),
        )
        assert antwort.status_code == 401


class TestBegrenzung:
    def test_zu_viele_versuche_werden_abgewiesen(self, client, session) -> None:  # type: ignore[no-untyped-def]
        client.post(
            "/api/v1/auth/register",
            json={
                "displayName": "Anna",
                "email": "anna@example.org",
                "password": GUTES_PASSWORT,
                "bootstrapToken": TEST_BOOTSTRAP_TOKEN,
            },
        )

        codes = []
        for _ in range(rate_limit.SIGN_IN.attempts + 2):
            codes.append(
                client.post(
                    "/api/v1/auth/sign-in",
                    json={"email": "anna@example.org", "password": "falsch-falsch"},
                ).status_code
            )

        assert 401 in codes
        assert codes[-1] == 429

    def test_enge_schleife_erfolgreicher_rotationen_wird_gebremst(self, client, session) -> None:  # type: ignore[no-untyped-def]
        """Auch der geglueckte Weg hat ein Budget - er schreibt Historie."""
        angemeldet = client.post(
            "/api/v1/auth/register",
            json={
                "displayName": "Anna",
                "email": "anna@example.org",
                "password": GUTES_PASSWORT,
                "bootstrapToken": TEST_BOOTSTRAP_TOKEN,
            },
        ).json()

        token = angemeldet["tokens"]["refreshToken"]
        for _ in range(rate_limit.REFRESH.attempts):
            antwort = client.post("/api/v1/auth/refresh", json={"refreshToken": token})
            assert antwort.status_code == 200
            token = antwort.json()["refreshToken"]

        gebremst = client.post("/api/v1/auth/refresh", json={"refreshToken": token})
        assert gebremst.status_code == 429
        assert gebremst.json()["code"] == "RATE_LIMITED"

    def test_unbekannter_refresh_token_bleibt_401(self, client, session) -> None:  # type: ignore[no-untyped-def]
        """Die Bremse darf nicht verraten, dass es die Sitzung gibt."""
        angemeldet = client.post(
            "/api/v1/auth/register",
            json={
                "displayName": "Anna",
                "email": "anna@example.org",
                "password": GUTES_PASSWORT,
                "bootstrapToken": TEST_BOOTSTRAP_TOKEN,
            },
        ).json()

        token = angemeldet["tokens"]["refreshToken"]
        for _ in range(rate_limit.REFRESH.attempts):
            token = client.post("/api/v1/auth/refresh", json={"refreshToken": token}).json()[
                "refreshToken"
            ]

        fremd = client.post("/api/v1/auth/refresh", json={"refreshToken": "nicht-von-hier"})
        assert fremd.status_code == 401
        assert fremd.json()["code"] == "AUTHENTICATION_REQUIRED"

    def test_erfolgreiche_anmeldung_raeumt_den_zaehler(self, client, session) -> None:  # type: ignore[no-untyped-def]
        """Sonst sperrten Tippfehler den rechtmaessigen Nutzer aus."""
        client.post(
            "/api/v1/auth/register",
            json={
                "displayName": "Anna",
                "email": "anna@example.org",
                "password": GUTES_PASSWORT,
                "bootstrapToken": TEST_BOOTSTRAP_TOKEN,
            },
        )
        for _ in range(5):
            client.post(
                "/api/v1/auth/sign-in",
                json={"email": "anna@example.org", "password": "falsch"},
            )

        assert (
            client.post(
                "/api/v1/auth/sign-in",
                json={"email": "anna@example.org", "password": GUTES_PASSWORT},
            ).status_code
            == 200
        )
        for _ in range(5):
            assert (
                client.post(
                    "/api/v1/auth/sign-in",
                    json={"email": "anna@example.org", "password": "falsch"},
                ).status_code
                == 401
            )

    def test_der_schluessel_steht_nur_gehasht_da(self, session: Session) -> None:
        """Wer wann einen Anmeldeversuch hatte, ist mehr Wissen, als die
        Begrenzung braucht."""
        rate_limit.record_attempt(session, "sign_in", "anna@example.org")
        session.flush()

        zeilen = session.execute(select(RateLimitEvent)).scalars().all()
        assert zeilen
        for zeile in zeilen:
            assert "anna@example.org" not in zeile.key_hash


class TestProduktiveTransaktionsgrenze:
    def test_bootstrap_nachweis_ist_nach_erfolg_dauerhaft_verbraucht(
        self, production_client
    ) -> None:  # type: ignore[no-untyped-def]
        client, maker = production_client
        erste = client.post(
            "/api/v1/auth/register",
            json={
                "displayName": "Anna",
                "email": "anna@example.org",
                "password": GUTES_PASSWORT,
                "bootstrapToken": TEST_BOOTSTRAP_TOKEN,
            },
        )
        assert erste.status_code == 201

        wiederverwendung = client.post(
            "/api/v1/auth/register",
            json={
                "displayName": "Fremd",
                "email": "fremd@example.org",
                "password": GUTES_PASSWORT,
                "bootstrapToken": TEST_BOOTSTRAP_TOKEN,
            },
        )
        assert wiederverwendung.status_code == 403
        assert wiederverwendung.json()["code"] == "REGISTRATION_REQUIRES_INVITATION"

        with maker() as committed:
            assert committed.execute(select(func.count()).select_from(Account)).scalar_one() == 1
            state = committed.get(InstanceBootstrapState, 1)
            assert state is not None
            assert state.completed_at is not None

    def test_paralleler_bootstrap_hat_genau_einen_owner(self, production_client) -> None:  # type: ignore[no-untyped-def]
        client, maker = production_client
        start = Barrier(2)

        def registrieren(index: int):  # type: ignore[no-untyped-def]
            start.wait(timeout=5)
            return client.post(
                "/api/v1/auth/register",
                json={
                    "displayName": f"Owner {index}",
                    "email": f"owner{index}@example.org",
                    "password": GUTES_PASSWORT,
                    "bootstrapToken": TEST_BOOTSTRAP_TOKEN,
                },
            )

        with ThreadPoolExecutor(max_workers=2) as pool:
            antworten = list(pool.map(registrieren, range(2)))

        assert sorted(antwort.status_code for antwort in antworten) == [201, 403]
        abgewiesen = next(antwort for antwort in antworten if antwort.status_code == 403)
        assert abgewiesen.json()["code"] == "REGISTRATION_REQUIRES_INVITATION"

        with maker() as committed:
            assert committed.execute(select(func.count()).select_from(Account)).scalar_one() == 1
            state = committed.get(InstanceBootstrapState, 1)
            assert state is not None
            assert state.completed_at is not None

    def test_fehlversuche_bleiben_nach_abgelehnten_requests_erhalten(
        self, production_client
    ) -> None:  # type: ignore[no-untyped-def]
        client, maker = production_client
        email = "anna@example.org"
        assert (
            client.post(
                "/api/v1/auth/register",
                json={
                    "displayName": "Anna",
                    "email": email,
                    "password": GUTES_PASSWORT,
                    "bootstrapToken": TEST_BOOTSTRAP_TOKEN,
                },
            ).status_code
            == 201
        )

        for _ in range(rate_limit.SIGN_IN.attempts):
            antwort = client.post(
                "/api/v1/auth/sign-in",
                json={"email": email, "password": "falsch-falsch"},
            )
            assert antwort.status_code == 401

        gesperrt = client.post(
            "/api/v1/auth/sign-in",
            json={"email": email, "password": "falsch-falsch"},
        )
        assert gesperrt.status_code == 429
        assert gesperrt.json()["code"] == "RATE_LIMITED"

        with maker() as committed:
            versuche = committed.execute(
                select(func.count())
                .select_from(RateLimitEvent)
                .where(
                    RateLimitEvent.action == "sign_in",
                    RateLimitEvent.key_hash == hash_token(email),
                )
            ).scalar_one()
        assert versuche == rate_limit.SIGN_IN.attempts

    def test_parallele_fehlversuche_verlieren_keine_zaehler(self, production_client) -> None:  # type: ignore[no-untyped-def]
        client, maker = production_client
        email = "parallel@example.org"
        assert (
            client.post(
                "/api/v1/auth/register",
                json={
                    "displayName": "Anna",
                    "email": email,
                    "password": GUTES_PASSWORT,
                    "bootstrapToken": TEST_BOOTSTRAP_TOKEN,
                },
            ).status_code
            == 201
        )

        def fehlversuch(_: int) -> int:
            return client.post(
                "/api/v1/auth/sign-in",
                json={"email": email, "password": "falsch-falsch"},
            ).status_code

        anzahl = 5
        with ThreadPoolExecutor(max_workers=anzahl) as pool:
            codes = list(pool.map(fehlversuch, range(anzahl)))

        assert codes == [401] * anzahl
        with maker() as committed:
            versuche = committed.execute(
                select(func.count())
                .select_from(RateLimitEvent)
                .where(
                    RateLimitEvent.action == "sign_in",
                    RateLimitEvent.key_hash == hash_token(email),
                )
            ).scalar_one()
        assert versuche == anzahl

    def test_refresh_replay_widerruft_die_sitzung_dauerhaft(self, production_client) -> None:  # type: ignore[no-untyped-def]
        client, maker = production_client
        registrierung = client.post(
            "/api/v1/auth/register",
            json={
                "displayName": "Anna",
                "email": "anna@example.org",
                "password": GUTES_PASSWORT,
                "bootstrapToken": TEST_BOOTSTRAP_TOKEN,
            },
        )
        assert registrierung.status_code == 201
        alter_refresh = registrierung.json()["tokens"]["refreshToken"]

        rotation = client.post(
            "/api/v1/auth/refresh",
            json={"refreshToken": alter_refresh},
        )
        assert rotation.status_code == 200
        neue_tokens = rotation.json()

        replay = client.post(
            "/api/v1/auth/refresh",
            json={"refreshToken": alter_refresh},
        )
        assert replay.status_code == 401
        assert replay.json()["code"] == "AUTHENTICATION_REQUIRED"
        assert alter_refresh not in replay.text

        assert (
            client.get(
                "/api/v1/auth/me",
                headers=auth(neue_tokens["accessToken"]),
            ).status_code
            == 401
        )
        with maker() as committed:
            device_session = committed.execute(select(DeviceSession)).scalar_one()
            assert device_session.revoked_at is not None
            assert device_session.access_token_hash is None

    def test_replay_der_aeltesten_generation_widerruft_dauerhaft(self, production_client) -> None:  # type: ignore[no-untyped-def]
        """T0 -> T1 -> T2, danach Replay von T0 ueber HTTP.

        Der produktive Lifecycle rollt die Anfrage wegen des 401 zurueck.
        Der Widerruf muss den Rollback trotzdem ueberleben, sonst bliebe die
        kompromittierte Sitzung offen.
        """
        client, maker = production_client
        registrierung = client.post(
            "/api/v1/auth/register",
            json={
                "displayName": "Anna",
                "email": "anna@example.org",
                "password": GUTES_PASSWORT,
                "bootstrapToken": TEST_BOOTSTRAP_TOKEN,
            },
        )
        assert registrierung.status_code == 201
        t0 = registrierung.json()["tokens"]["refreshToken"]

        erste = client.post("/api/v1/auth/refresh", json={"refreshToken": t0})
        assert erste.status_code == 200
        t1 = erste.json()["refreshToken"]

        zweite = client.post("/api/v1/auth/refresh", json={"refreshToken": t1})
        assert zweite.status_code == 200
        t2 = zweite.json()

        replay = client.post("/api/v1/auth/refresh", json={"refreshToken": t0})
        assert replay.status_code == 401
        assert replay.json()["code"] == "AUTHENTICATION_REQUIRED"
        assert t0 not in replay.text

        assert client.get("/api/v1/auth/me", headers=auth(t2["accessToken"])).status_code == 401
        assert (
            client.post(
                "/api/v1/auth/refresh", json={"refreshToken": t2["refreshToken"]}
            ).status_code
            == 401
        )
        with maker() as committed:
            device_session = committed.execute(select(DeviceSession)).scalar_one()
            assert device_session.revoked_at is not None
            assert device_session.access_token_hash is None

    def test_replay_einer_mittleren_generation_widerruft_dauerhaft(self, production_client) -> None:  # type: ignore[no-untyped-def]
        client, maker = production_client
        registrierung = client.post(
            "/api/v1/auth/register",
            json={
                "displayName": "Anna",
                "email": "anna@example.org",
                "password": GUTES_PASSWORT,
                "bootstrapToken": TEST_BOOTSTRAP_TOKEN,
            },
        )
        assert registrierung.status_code == 201
        t0 = registrierung.json()["tokens"]["refreshToken"]

        t1 = client.post("/api/v1/auth/refresh", json={"refreshToken": t0}).json()["refreshToken"]
        t2 = client.post("/api/v1/auth/refresh", json={"refreshToken": t1}).json()

        replay = client.post("/api/v1/auth/refresh", json={"refreshToken": t1})
        assert replay.status_code == 401
        assert t1 not in replay.text

        assert client.get("/api/v1/auth/me", headers=auth(t2["accessToken"])).status_code == 401
        with maker() as committed:
            device_session = committed.execute(select(DeviceSession)).scalar_one()
            assert device_session.revoked_at is not None

    def test_unbekannter_refresh_token_widerruft_keine_sitzung(self, production_client) -> None:  # type: ignore[no-untyped-def]
        """Sonst koennte jeder eine fremde Sitzung mit Unfug abschiessen."""
        client, maker = production_client
        registrierung = client.post(
            "/api/v1/auth/register",
            json={
                "displayName": "Anna",
                "email": "anna@example.org",
                "password": GUTES_PASSWORT,
                "bootstrapToken": TEST_BOOTSTRAP_TOKEN,
            },
        )
        assert registrierung.status_code == 201
        tokens = registrierung.json()["tokens"]

        abgewiesen = client.post("/api/v1/auth/refresh", json={"refreshToken": "gibt-es-nicht"})
        assert abgewiesen.status_code == 401

        assert client.get("/api/v1/auth/me", headers=auth(tokens["accessToken"])).status_code == 200
        with maker() as committed:
            device_session = committed.execute(select(DeviceSession)).scalar_one()
            assert device_session.revoked_at is None

    def test_parallele_refresh_rotation_hat_genau_einen_sieger(self, production_client) -> None:  # type: ignore[no-untyped-def]
        client, maker = production_client
        registrierung = client.post(
            "/api/v1/auth/register",
            json={
                "displayName": "Anna",
                "email": "anna@example.org",
                "password": GUTES_PASSWORT,
                "bootstrapToken": TEST_BOOTSTRAP_TOKEN,
            },
        )
        assert registrierung.status_code == 201
        refresh_token = registrierung.json()["tokens"]["refreshToken"]
        start = Barrier(2)

        def rotation(_: int):  # type: ignore[no-untyped-def]
            start.wait(timeout=5)
            return client.post(
                "/api/v1/auth/refresh",
                json={"refreshToken": refresh_token},
            )

        with ThreadPoolExecutor(max_workers=2) as pool:
            antworten = list(pool.map(rotation, range(2)))

        assert sorted(antwort.status_code for antwort in antworten) == [200, 401]
        erfolgreich = next(antwort for antwort in antworten if antwort.status_code == 200)
        replay = next(antwort for antwort in antworten if antwort.status_code == 401)
        assert replay.json()["code"] == "AUTHENTICATION_REQUIRED"
        assert refresh_token not in replay.text

        neue_tokens = erfolgreich.json()
        assert neue_tokens["refreshToken"] != refresh_token
        assert (
            client.get(
                "/api/v1/auth/me",
                headers=auth(neue_tokens["accessToken"]),
            ).status_code
            == 401
        )
        with maker() as committed:
            device_session = committed.execute(select(DeviceSession)).scalar_one()
            assert device_session.revoked_at is not None
            assert device_session.access_token_hash is None


class TestPasswortAbleitung:
    def test_hash_gibt_das_passwort_nicht_preis(self) -> None:
        gehasht = passwords.hash_password(GUTES_PASSWORT)
        assert GUTES_PASSWORT not in gehasht

    def test_zwei_gleiche_passwoerter_ergeben_verschiedene_hashes(self) -> None:
        """Argon2 salzt - sonst waeren gleiche Passwoerter erkennbar."""
        assert passwords.hash_password(GUTES_PASSWORT) != passwords.hash_password(GUTES_PASSWORT)

    def test_pruefung_stimmt(self) -> None:
        gehasht = passwords.hash_password(GUTES_PASSWORT)
        assert passwords.verify_password(gehasht, GUTES_PASSWORT)
        assert not passwords.verify_password(gehasht, "etwas-anderes")

    def test_kaputter_hash_wirft_nicht(self) -> None:
        assert not passwords.verify_password("kein-hash", GUTES_PASSWORT)
