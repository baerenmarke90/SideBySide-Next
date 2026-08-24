"""Das Beziehungsprofil eines Space lesen, schreiben und dabei nichts verlieren.

Drei Dinge werden hier ueber HTTP bewiesen:

1. Ein Schreibzugriff braucht die Version, die der Aufrufer gelesen hat.
   Stimmt sie nicht mehr, gibt es 409 statt eines stillen Ueberschreibens.
2. Zwei gleichzeitige Schreibzugriffe koennen sich nicht gegenseitig
   ueberholen - genau einer gewinnt, und der andere erfaehrt es.
3. Die sichtbare Beziehungsdauer wechselt am Ort der lesenden Person, nicht
   um Mitternacht UTC.

Geprueft wird ueber HTTP mit echten Token. Ein Direktaufruf des Dienstes
ueberspringt genau den Weg, auf dem eine Pruefung vergessen werden kann.
"""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, date, datetime
from threading import Barrier
from typing import Any

import pytest
from sqlalchemy import select
from sqlalchemy.orm import Session

from sidebyside.core.ids import new_id
from sidebyside.relationship import service
from sidebyside.relationship.models import SpaceProfile
from tests.conftest import auth, make_account, make_space, requires_database, sign_in

pytestmark = [pytest.mark.integration, requires_database]


def profil_pfad(space_id: object) -> str:
    return f"/api/v1/spaces/{space_id}/profile"


def rumpf(
    *,
    started_on: str | None = "2022-05-17",
    anzeigen: bool = True,
    modus: str = "YEARS_MONTHS",
) -> dict[str, Any]:
    return {
        "relationshipStartedOn": started_on,
        "showRelationshipDuration": anzeigen,
        "durationDisplayMode": modus,
    }


def if_match(version: object) -> dict[str, str]:
    return {"If-Match": f'"{version}"'}


@pytest.fixture
def paar(session: Session):  # type: ignore[no-untyped-def]
    """Zwei Partner in einem Space und ein Fremder mit eigenem Space."""
    anna = make_account(session, "Anna")
    ben = make_account(session, "Ben")
    fremd = make_account(session, "Fremde Person")

    space = make_space(session, anna)
    service.add_member(session, space.id, ben)
    fremder_space = make_space(session, fremd)
    session.flush()

    return {
        "space": space,
        "fremder_space": fremder_space,
        "token_a": sign_in(session, anna),
        "token_b": sign_in(session, ben),
        "token_fremd": sign_in(session, fremd),
        "anna": anna,
        "ben": ben,
    }


def gespeichertes_profil(session: Session, space_id: object) -> SpaceProfile:
    profil = session.execute(
        select(SpaceProfile).where(SpaceProfile.space_id == space_id)
    ).scalar_one()
    session.refresh(profil)
    return profil


class TestLesen:
    def test_ein_neuer_space_hat_ein_profil_mit_standardwerten(self, client, paar) -> None:  # type: ignore[no-untyped-def]
        antwort = client.get(profil_pfad(paar["space"].id), headers=auth(paar["token_a"]))
        assert antwort.status_code == 200
        assert antwort.json() == {
            "spaceId": str(paar["space"].id),
            "version": 1,
            "relationshipStartedOn": None,
            "showRelationshipDuration": True,
            "durationDisplayMode": "YEARS_MONTHS",
            "relationshipDays": None,
            "relationshipYears": None,
            "relationshipMonths": None,
        }

    def test_die_version_steht_auch_als_etag_im_kopf(self, client, paar) -> None:  # type: ignore[no-untyped-def]
        """Ohne die Version im Kopf muesste ein Client sie aus dem Rumpf
        heraussuchen, um ueberhaupt schreiben zu koennen."""
        antwort = client.get(profil_pfad(paar["space"].id), headers=auth(paar["token_a"]))
        assert antwort.headers["ETag"] == '"1"'

    def test_beide_partner_sehen_dasselbe_profil(self, client, paar) -> None:  # type: ignore[no-untyped-def]
        von_a = client.get(profil_pfad(paar["space"].id), headers=auth(paar["token_a"]))
        von_b = client.get(profil_pfad(paar["space"].id), headers=auth(paar["token_b"]))
        assert von_a.json() == von_b.json()


class TestSchreiben:
    def test_erfolgreicher_update(self, client, session, paar) -> None:  # type: ignore[no-untyped-def]
        antwort = client.put(
            profil_pfad(paar["space"].id),
            json=rumpf(started_on="2022-05-17", anzeigen=True, modus="DAYS"),
            headers={**auth(paar["token_a"]), **if_match(1)},
        )

        assert antwort.status_code == 200
        koerper = antwort.json()
        assert koerper["relationshipStartedOn"] == "2022-05-17"
        assert koerper["showRelationshipDuration"] is True
        assert koerper["durationDisplayMode"] == "DAYS"
        assert koerper["version"] == 2
        assert antwort.headers["ETag"] == '"2"'

        gespeichert = gespeichertes_profil(session, paar["space"].id)
        assert gespeichert.relationship_started_on == date(2022, 5, 17)
        assert gespeichert.duration_display_mode == "DAYS"
        assert gespeichert.version == 2

    def test_der_naechste_lesezugriff_zeigt_den_neuen_stand(self, client, paar) -> None:  # type: ignore[no-untyped-def]
        client.put(
            profil_pfad(paar["space"].id),
            json=rumpf(started_on="2022-05-17"),
            headers={**auth(paar["token_a"]), **if_match(1)},
        )
        gelesen = client.get(profil_pfad(paar["space"].id), headers=auth(paar["token_a"]))
        assert gelesen.json()["relationshipStartedOn"] == "2022-05-17"
        assert gelesen.json()["version"] == 2

    def test_auch_der_partner_darf_schreiben(self, client, paar) -> None:  # type: ignore[no-untyped-def]
        """Das Profil gehoert dem Space, nicht der Person, die ihn angelegt hat."""
        antwort = client.put(
            profil_pfad(paar["space"].id),
            json=rumpf(started_on="2020-01-01"),
            headers={**auth(paar["token_b"]), **if_match(1)},
        )
        assert antwort.status_code == 200

    def test_nacheinander_mit_der_jeweils_neuen_version(self, client, paar) -> None:  # type: ignore[no-untyped-def]
        erste = client.put(
            profil_pfad(paar["space"].id),
            json=rumpf(started_on="2022-05-17"),
            headers={**auth(paar["token_a"]), **if_match(1)},
        )
        zweite = client.put(
            profil_pfad(paar["space"].id),
            json=rumpf(started_on="2021-04-16"),
            headers={**auth(paar["token_b"]), **if_match(erste.json()["version"])},
        )
        assert zweite.status_code == 200
        assert zweite.json()["version"] == 3
        assert zweite.json()["relationshipStartedOn"] == "2021-04-16"

    def test_null_loescht_den_beziehungsbeginn(self, client, session, paar) -> None:  # type: ignore[no-untyped-def]
        client.put(
            profil_pfad(paar["space"].id),
            json=rumpf(started_on="2022-05-17"),
            headers={**auth(paar["token_a"]), **if_match(1)},
        )
        geleert = client.put(
            profil_pfad(paar["space"].id),
            json=rumpf(started_on=None),
            headers={**auth(paar["token_a"]), **if_match(2)},
        )
        assert geleert.status_code == 200
        assert geleert.json()["relationshipStartedOn"] is None
        assert gespeichertes_profil(session, paar["space"].id).relationship_started_on is None

    def test_abgeschaltete_anzeige_schickt_die_dauer_nicht_mit(self, client, paar) -> None:  # type: ignore[no-untyped-def]
        """Ein Wert, den der Client ausblenden soll, ist trotzdem
        uebertragen worden."""
        antwort = client.put(
            profil_pfad(paar["space"].id),
            json=rumpf(started_on="2022-05-17", anzeigen=False),
            headers={**auth(paar["token_a"]), **if_match(1)},
        )
        koerper = antwort.json()
        assert koerper["showRelationshipDuration"] is False
        assert koerper["relationshipDays"] is None
        assert koerper["relationshipYears"] is None
        assert koerper["relationshipMonths"] is None

    def test_ein_unveraenderter_schreibzugriff_zaehlt_die_version_nicht_hoch(
        self, client, paar
    ) -> None:  # type: ignore[no-untyped-def]
        """Ohne Aenderung gibt es kein Update - und damit auch keine neue
        Version, die ein anderer Client umsonst nachladen muesste."""
        erste = client.put(
            profil_pfad(paar["space"].id),
            json=rumpf(started_on="2022-05-17"),
            headers={**auth(paar["token_a"]), **if_match(1)},
        )
        zweite = client.put(
            profil_pfad(paar["space"].id),
            json=rumpf(started_on="2022-05-17"),
            headers={**auth(paar["token_a"]), **if_match(2)},
        )
        assert erste.json()["version"] == zweite.json()["version"] == 2


class TestVersionskonflikt:
    def test_veraltete_version_ergibt_409(self, client, paar) -> None:  # type: ignore[no-untyped-def]
        client.put(
            profil_pfad(paar["space"].id),
            json=rumpf(started_on="2022-05-17"),
            headers={**auth(paar["token_a"]), **if_match(1)},
        )

        veraltet = client.put(
            profil_pfad(paar["space"].id),
            json=rumpf(started_on="1999-01-01"),
            headers={**auth(paar["token_b"]), **if_match(1)},
        )

        assert veraltet.status_code == 409
        assert veraltet.json() == {
            "type": "conflict",
            "title": "Conflict",
            "status": 409,
            "detail": "The space profile was changed by someone else.",
            "code": "VERSION_CONFLICT",
        }

    def test_der_konflikt_aendert_nichts(self, client, session, paar) -> None:  # type: ignore[no-untyped-def]
        client.put(
            profil_pfad(paar["space"].id),
            json=rumpf(started_on="2022-05-17"),
            headers={**auth(paar["token_a"]), **if_match(1)},
        )
        client.put(
            profil_pfad(paar["space"].id),
            json=rumpf(started_on="1999-01-01", modus="DAYS"),
            headers={**auth(paar["token_b"]), **if_match(1)},
        )

        gespeichert = gespeichertes_profil(session, paar["space"].id)
        assert gespeichert.relationship_started_on == date(2022, 5, 17)
        assert gespeichert.duration_display_mode == "YEARS_MONTHS"
        assert gespeichert.version == 2

    def test_eine_zu_hohe_version_ergibt_ebenfalls_409(self, client, paar) -> None:  # type: ignore[no-untyped-def]
        antwort = client.put(
            profil_pfad(paar["space"].id),
            json=rumpf(),
            headers={**auth(paar["token_a"]), **if_match(99)},
        )
        assert antwort.status_code == 409

    def test_ohne_if_match_wird_nicht_geschrieben(self, client, session, paar) -> None:  # type: ignore[no-untyped-def]
        """Der Kopf ist Pflicht - im Vertrag wie im Verhalten.

        Ein fehlender Kopf ist sonst der Weg, auf dem ein Client den
        Konfliktschutz versehentlich abschaltet.
        """
        antwort = client.put(
            profil_pfad(paar["space"].id),
            json=rumpf(started_on="1999-01-01"),
            headers=auth(paar["token_a"]),
        )
        assert antwort.status_code == 422
        assert antwort.json()["code"] == "VALIDATION_FAILED"
        assert "if-match" in antwort.json()["detail"].lower()
        assert gespeichertes_profil(session, paar["space"].id).relationship_started_on is None

    @pytest.mark.parametrize(
        "wert",
        ["*", 'W/"1"', "abc", "1.0", "-1", '"1", "2"', '""', " ", "1 2"],
    )
    def test_unbrauchbares_if_match_wird_abgewiesen(self, client, paar, wert: str) -> None:  # type: ignore[no-untyped-def]
        """`*` und schwache Validatoren wuerden den Konfliktschutz aufheben."""
        antwort = client.put(
            profil_pfad(paar["space"].id),
            json=rumpf(),
            headers={**auth(paar["token_a"]), "If-Match": wert},
        )
        assert antwort.status_code == 422
        assert antwort.json()["code"] == "IF_MATCH_MALFORMED"

    def test_if_match_ohne_anfuehrungszeichen_wird_akzeptiert(self, client, paar) -> None:  # type: ignore[no-untyped-def]
        """Beide Schreibweisen kommen in freier Wildbahn vor."""
        antwort = client.put(
            profil_pfad(paar["space"].id),
            json=rumpf(),
            headers={**auth(paar["token_a"]), "If-Match": "1"},
        )
        assert antwort.status_code == 200


class TestWettlauf:
    def test_zwei_gleichzeitige_updates_ueberschreiben_sich_nicht(self, production_client) -> None:  # type: ignore[no-untyped-def]
        """Kein Lost Update: genau einer gewinnt, der andere bekommt 409."""
        client, macher = production_client
        with macher() as vorbereitung:
            anna = make_account(vorbereitung, "Anna Wettlauf")
            space = make_space(vorbereitung, anna)
            ben = make_account(vorbereitung, "Ben Wettlauf")
            service.add_member(vorbereitung, space.id, ben)
            token_a = sign_in(vorbereitung, anna)
            token_b = sign_in(vorbereitung, ben)
            space_id = space.id
            vorbereitung.commit()

        start = Barrier(2)

        def schreiben(daten: tuple[str, str]):  # type: ignore[no-untyped-def]
            token, beginn = daten
            start.wait(timeout=5)
            return client.put(
                profil_pfad(space_id),
                json=rumpf(started_on=beginn),
                headers={**auth(token), **if_match(1)},
            )

        with ThreadPoolExecutor(max_workers=2) as pool:
            antworten = list(
                pool.map(schreiben, [(token_a, "2022-05-17"), (token_b, "2019-09-08")])
            )

        assert sorted(antwort.status_code for antwort in antworten) == [200, 409]

        gewinner = next(antwort for antwort in antworten if antwort.status_code == 200)
        verlierer = next(antwort for antwort in antworten if antwort.status_code == 409)
        assert verlierer.json()["code"] == "VERSION_CONFLICT"

        with macher() as pruefer:
            gespeichert = pruefer.execute(
                select(SpaceProfile).where(SpaceProfile.space_id == space_id)
            ).scalar_one()
            # Genau eine Aenderung ist angekommen. Waere die zweite still
            # durchgelaufen, stuende hier Version 3 oder der andere Wert.
            assert gespeichert.version == 2
            assert gespeichert.relationship_started_on is not None
            assert (
                gespeichert.relationship_started_on.isoformat()
                == gewinner.json()["relationshipStartedOn"]
            )


class TestValidierung:
    def test_ein_beginn_in_der_zukunft_wird_abgewiesen(self, client, paar) -> None:  # type: ignore[no-untyped-def]
        antwort = client.put(
            profil_pfad(paar["space"].id),
            json=rumpf(started_on="2099-01-01"),
            headers={**auth(paar["token_a"]), **if_match(1)},
        )
        assert antwort.status_code == 422
        assert antwort.json()["code"] == "RELATIONSHIP_START_IN_FUTURE"

    def test_eine_verrutschte_jahreszahl_wird_abgewiesen(self, client, paar) -> None:  # type: ignore[no-untyped-def]
        antwort = client.put(
            profil_pfad(paar["space"].id),
            json=rumpf(started_on="0202-05-17"),
            headers={**auth(paar["token_a"]), **if_match(1)},
        )
        assert antwort.status_code == 422
        assert antwort.json()["code"] == "RELATIONSHIP_START_TOO_EARLY"

    @pytest.mark.parametrize(
        "koerper",
        [
            {"relationshipStartedOn": None, "showRelationshipDuration": True},
            {"relationshipStartedOn": None, "durationDisplayMode": "DAYS"},
            {"showRelationshipDuration": True, "durationDisplayMode": "DAYS"},
        ],
    )
    def test_ein_unvollstaendiger_rumpf_wird_abgewiesen(self, client, paar, koerper) -> None:  # type: ignore[no-untyped-def]
        """PUT ersetzt vollstaendig. Ein weggelassenes Feld waere nicht von
        "auf leer setzen" zu unterscheiden."""
        antwort = client.put(
            profil_pfad(paar["space"].id),
            json=koerper,
            headers={**auth(paar["token_a"]), **if_match(1)},
        )
        assert antwort.status_code == 422

    @pytest.mark.parametrize("modus", ["MONTHS", "years_months", "", "DAYS "])
    def test_ein_unbekannter_anzeigemodus_wird_abgewiesen(self, client, paar, modus: str) -> None:  # type: ignore[no-untyped-def]
        antwort = client.put(
            profil_pfad(paar["space"].id),
            json=rumpf(modus=modus),
            headers={**auth(paar["token_a"]), **if_match(1)},
        )
        assert antwort.status_code == 422
        assert antwort.json()["code"] == "VALIDATION_FAILED"

    @pytest.mark.parametrize(
        "beginn", ["2022-13-40", "17.05.2022", "2022-05-17T10:00:00Z", "heute"]
    )
    def test_ein_unbrauchbares_datum_wird_abgewiesen(self, client, paar, beginn: str) -> None:  # type: ignore[no-untyped-def]
        antwort = client.put(
            profil_pfad(paar["space"].id),
            json=rumpf(started_on=beginn),
            headers={**auth(paar["token_a"]), **if_match(1)},
        )
        assert antwort.status_code == 422


class TestFremderZugriff:
    def test_fremder_kann_das_profil_nicht_lesen(self, client, paar) -> None:  # type: ignore[no-untyped-def]
        antwort = client.get(profil_pfad(paar["space"].id), headers=auth(paar["token_fremd"]))
        assert antwort.status_code == 404
        assert antwort.json()["code"] == "SPACE_NOT_FOUND"

    def test_fremder_kann_das_profil_nicht_schreiben(self, client, session, paar) -> None:  # type: ignore[no-untyped-def]
        antwort = client.put(
            profil_pfad(paar["space"].id),
            json=rumpf(started_on="1999-01-01"),
            headers={**auth(paar["token_fremd"]), **if_match(1)},
        )
        assert antwort.status_code == 404
        assert antwort.json()["code"] == "SPACE_NOT_FOUND"
        assert gespeichertes_profil(session, paar["space"].id).relationship_started_on is None

    def test_der_guard_kommt_vor_jeder_anderen_pruefung(self, client, paar) -> None:  # type: ignore[no-untyped-def]
        """Ein 422 wegen fehlendem If-Match wuerde verraten, dass der Space
        existiert - und die Mitgliedschaftspruefung stuende hinter einer
        Formpruefung."""
        antwort = client.put(
            profil_pfad(paar["space"].id),
            json={"unsinn": True},
            headers=auth(paar["token_fremd"]),
        )
        assert antwort.status_code == 404

    def test_fremder_space_ist_von_einem_erfundenen_nicht_zu_unterscheiden(
        self, client, paar
    ) -> None:  # type: ignore[no-untyped-def]
        echt = client.get(profil_pfad(paar["space"].id), headers=auth(paar["token_fremd"]))
        erfunden = client.get(profil_pfad(new_id()), headers=auth(paar["token_fremd"]))
        assert echt.status_code == erfunden.status_code == 404
        assert echt.json() == erfunden.json()

    def test_wer_gegangen_ist_schreibt_nicht_mehr(self, client, session, paar) -> None:  # type: ignore[no-untyped-def]
        mitgliedschaft = service.require_membership(session, paar["ben"], paar["space"].id)
        service.end_membership(mitgliedschaft)
        session.flush()

        antwort = client.put(
            profil_pfad(paar["space"].id),
            json=rumpf(),
            headers={**auth(paar["token_b"]), **if_match(1)},
        )
        assert antwort.status_code == 404

    @pytest.mark.parametrize("boese", ["nicht-echt", "12345", "' OR 1=1 --", "../../etc/passwd"])
    def test_fehlgeformte_id_ergibt_404(self, client, paar, boese: str) -> None:  # type: ignore[no-untyped-def]
        antwort = client.put(
            profil_pfad(boese),
            json=rumpf(),
            headers={**auth(paar["token_a"]), **if_match(1)},
        )
        assert antwort.status_code == 404


class TestAnonymerZugriff:
    def test_lesen_ohne_token(self, client, paar) -> None:  # type: ignore[no-untyped-def]
        assert client.get(profil_pfad(paar["space"].id)).status_code == 401

    def test_schreiben_ohne_token(self, client, session, paar) -> None:  # type: ignore[no-untyped-def]
        antwort = client.put(
            profil_pfad(paar["space"].id),
            json=rumpf(started_on="1999-01-01"),
            headers=if_match(1),
        )
        assert antwort.status_code == 401
        assert gespeichertes_profil(session, paar["space"].id).relationship_started_on is None

    @pytest.mark.parametrize(
        "kopf",
        [{"Authorization": "Bearer nicht-echt"}, {"Authorization": "Basic abc"}, {}],
    )
    def test_unbrauchbarer_kopf(self, client, paar, kopf) -> None:  # type: ignore[no-untyped-def]
        antwort = client.put(
            profil_pfad(paar["space"].id),
            json=rumpf(),
            headers={**kopf, **if_match(1)},
        )
        assert antwort.status_code == 401


def frieren(monkeypatch, zeitpunkt: datetime) -> None:
    """Nur den Kalendertag einfrieren, nicht die Sitzungsablaeufe.

    `today_in` schlaegt `now` beim Aufruf im clock-Modul nach; `auth.sessions`
    hat sich die Funktion beim Import geholt. Ein in die Zukunft gestellter
    Kalendertag laesst Zugangstoken deshalb unberuehrt gueltig - sonst
    liefen diese Tests an einem 401 auf, das mit Zeitzonen nichts zu tun hat.
    """
    from sidebyside.core import clock

    monkeypatch.setattr(clock, "now", lambda: zeitpunkt)


def mit_beginn(session: Session, space_id: object, beginn: date) -> None:
    profil = gespeichertes_profil(session, space_id)
    profil.relationship_started_on = beginn
    session.flush()


class TestZeitzone:
    """Der Tageswechsel gehoert an den Ort der lesenden Person.

    Bezugspunkt aller Faelle ist der 25.08.2025 als Beziehungsbeginn. Der
    erste Jahrestag faellt damit auf den 25.08.2026 - und der tritt in
    Auckland Stunden vor und in Los Angeles Stunden nach dem UTC-Tageswechsel
    ein.
    """

    def test_westlich_von_utc_ist_der_jahrestag_noch_nicht_erreicht(
        self, client, session, paar, monkeypatch
    ) -> None:  # type: ignore[no-untyped-def]
        """05:00 UTC am 25.08. ist in Los Angeles noch der 24.08.

        Gegen `today_utc()` gerechnet stuende hier faelschlich ein Jahr.
        """
        paar["anna"].timezone = "America/Los_Angeles"
        mit_beginn(session, paar["space"].id, date(2025, 8, 25))
        frieren(monkeypatch, datetime(2026, 8, 25, 5, 0, tzinfo=UTC))

        koerper = client.get(profil_pfad(paar["space"].id), headers=auth(paar["token_a"])).json()
        assert (koerper["relationshipYears"], koerper["relationshipMonths"]) == (0, 11)
        assert koerper["relationshipDays"] == 364

    def test_oestlich_von_utc_ist_der_jahrestag_schon_da(
        self, client, session, paar, monkeypatch
    ) -> None:  # type: ignore[no-untyped-def]
        """12:30 UTC am 24.08. ist in Auckland bereits der 25.08."""
        paar["anna"].timezone = "Pacific/Auckland"
        mit_beginn(session, paar["space"].id, date(2025, 8, 25))
        frieren(monkeypatch, datetime(2026, 8, 24, 12, 30, tzinfo=UTC))

        koerper = client.get(profil_pfad(paar["space"].id), headers=auth(paar["token_a"])).json()
        assert (koerper["relationshipYears"], koerper["relationshipMonths"]) == (1, 0)
        assert koerper["relationshipDays"] == 365

    def test_derselbe_zeitpunkt_ergibt_je_nach_ort_verschiedene_tage(
        self, client, session, paar, monkeypatch
    ) -> None:  # type: ignore[no-untyped-def]
        """Zwei Partner an zwei Orten sehen ihren jeweils eigenen Tag."""
        paar["anna"].timezone = "Pacific/Auckland"
        paar["ben"].timezone = "America/Los_Angeles"
        mit_beginn(session, paar["space"].id, date(2025, 8, 25))
        frieren(monkeypatch, datetime(2026, 8, 24, 12, 30, tzinfo=UTC))

        pfad = profil_pfad(paar["space"].id)
        von_anna = client.get(pfad, headers=auth(paar["token_a"])).json()
        von_ben = client.get(pfad, headers=auth(paar["token_b"])).json()

        assert von_anna["relationshipDays"] == 365
        assert von_ben["relationshipDays"] == 364

    def test_der_jahrestag_wechselt_an_der_ortszeit_mitternacht(
        self, client, session, paar, monkeypatch
    ) -> None:  # type: ignore[no-untyped-def]
        """Berlin steht im Mai auf UTC+2. Zwischen 21:30 und 22:30 UTC
        liegt dort der Jahreswechsel der Beziehung."""
        paar["anna"].timezone = "Europe/Berlin"
        mit_beginn(session, paar["space"].id, date(2022, 5, 17))
        pfad = profil_pfad(paar["space"].id)

        frieren(monkeypatch, datetime(2026, 5, 16, 21, 30, tzinfo=UTC))
        davor = client.get(pfad, headers=auth(paar["token_a"])).json()
        assert (davor["relationshipYears"], davor["relationshipMonths"]) == (3, 11)

        frieren(monkeypatch, datetime(2026, 5, 16, 22, 30, tzinfo=UTC))
        danach = client.get(pfad, headers=auth(paar["token_a"])).json()
        assert (danach["relationshipYears"], danach["relationshipMonths"]) == (4, 0)

    def test_auch_die_space_ansicht_rechnet_in_der_ortszeit(
        self, client, session, paar, monkeypatch
    ) -> None:  # type: ignore[no-untyped-def]
        """Derselbe Wert darf nicht davon abhaengen, ueber welchen Endpunkt
        er gelesen wird."""
        paar["anna"].timezone = "Pacific/Auckland"
        mit_beginn(session, paar["space"].id, date(2025, 8, 25))
        frieren(monkeypatch, datetime(2026, 8, 24, 12, 30, tzinfo=UTC))

        space_ansicht = client.get(
            f"/api/v1/spaces/{paar['space'].id}", headers=auth(paar["token_a"])
        ).json()
        assert space_ansicht["relationshipYears"] == 1
        assert space_ansicht["relationshipDays"] == 365

    def test_eine_unbrauchbare_zeitzone_beendet_die_anfrage_nicht(
        self, client, session, paar, monkeypatch
    ) -> None:  # type: ignore[no-untyped-def]
        """`Account.timezone` ist ein freies Textfeld. Ein unbrauchbarer
        Wert faellt auf UTC zurueck, statt die Antwort zu verlieren."""
        paar["anna"].timezone = "Nicht/Echt"
        mit_beginn(session, paar["space"].id, date(2025, 8, 25))
        frieren(monkeypatch, datetime(2026, 8, 24, 12, 30, tzinfo=UTC))

        antwort = client.get(profil_pfad(paar["space"].id), headers=auth(paar["token_a"]))
        assert antwort.status_code == 200
        assert antwort.json()["relationshipDays"] == 364

    def test_heute_am_eigenen_ort_ist_kein_zukuenftiges_datum(
        self, client, paar, monkeypatch
    ) -> None:  # type: ignore[no-untyped-def]
        """In Auckland ist der 25.08. bereits angebrochen, in UTC nicht.

        Gegen den UTC-Tag geprueft waere dieser Beginn faelschlich Zukunft.
        """
        paar["anna"].timezone = "Pacific/Auckland"
        frieren(monkeypatch, datetime(2026, 8, 24, 12, 30, tzinfo=UTC))

        antwort = client.put(
            profil_pfad(paar["space"].id),
            json=rumpf(started_on="2026-08-25"),
            headers={**auth(paar["token_a"]), **if_match(1)},
        )
        assert antwort.status_code == 200
        assert antwort.json()["relationshipStartedOn"] == "2026-08-25"
        assert antwort.json()["relationshipDays"] == 0

    def test_morgen_am_eigenen_ort_bleibt_zukunft(self, client, paar, monkeypatch) -> None:  # type: ignore[no-untyped-def]
        """In Los Angeles ist noch der 24.08., obwohl UTC schon weiter ist."""
        paar["anna"].timezone = "America/Los_Angeles"
        frieren(monkeypatch, datetime(2026, 8, 25, 5, 0, tzinfo=UTC))

        antwort = client.put(
            profil_pfad(paar["space"].id),
            json=rumpf(started_on="2026-08-25"),
            headers={**auth(paar["token_a"]), **if_match(1)},
        )
        assert antwort.status_code == 422
        assert antwort.json()["code"] == "RELATIONSHIP_START_IN_FUTURE"
