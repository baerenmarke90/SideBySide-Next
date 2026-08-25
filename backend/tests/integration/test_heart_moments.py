"""PostgreSQL-/HTTP-Abnahme fuer den M2-HeartMoment-Slice.

Schwerpunkt ist die Sichtbarkeitsgrenze: ein privater HeartMoment darf fuer
den Partner in keinem Zugriffspfad auftauchen - weder im Detail noch in der
Liste, im Cursor, im Ereignis oder in einer abweichenden Antwortform.
"""

from __future__ import annotations

from typing import Any
from uuid import UUID, uuid4

import pytest
from sqlalchemy import select
from sqlalchemy.orm import Session

from sidebyside.outbox.models import OutboxEvent
from sidebyside.relationship import service as relationship_service
from tests.conftest import auth, make_account, make_space, requires_database, sign_in

pytestmark = [pytest.mark.integration, requires_database]

GEHEIMER_TEXT = "Ein Satz, den nur ich lesen darf."


def path(space_id: object) -> str:
    return f"/api/v1/spaces/{space_id}/heart-moments"


def body(
    *,
    text: str = "Danke, dass du heute da warst.",
    emotion: str = "LOVED",
    visibility: str = "SHARED",
    happened_on: str = "2025-06-13",
) -> dict[str, Any]:
    return {
        "text": text,
        "emotion": emotion,
        "visibility": visibility,
        "happenedOn": happened_on,
    }


def if_match(token: str, version: int) -> dict[str, str]:
    return {**auth(token), "If-Match": f'"{version}"'}


@pytest.fixture
def paar(session: Session):  # type: ignore[no-untyped-def]
    anna = make_account(session, "Anna")
    ben = make_account(session, "Ben")
    fremd = make_account(session, "Fremd")

    space = make_space(session, anna)
    relationship_service.add_member(session, space.id, ben)
    fremder_space = make_space(session, fremd)
    session.flush()

    return {
        "anna": anna,
        "ben": ben,
        "space": space,
        "fremder_space": fremder_space,
        "token_a": sign_in(session, anna),
        "token_b": sign_in(session, ben),
        "token_fremd": sign_in(session, fremd),
    }


def erstelle(client, paar, *, token_key: str = "token_a", **overrides):  # type: ignore[no-untyped-def]
    return client.post(
        path(paar["space"].id),
        json=body(**overrides),
        headers=auth(paar[token_key]),
    )


class TestCrudUndOwnership:
    def test_autor_kann_anlegen_lesen_aendern_loeschen(self, client, paar) -> None:  # type: ignore[no-untyped-def]
        created = erstelle(client, paar)
        assert created.status_code == 201
        angelegt = created.json()
        assert UUID(angelegt["id"]).version == 7
        assert angelegt["authorId"] == str(paar["anna"].id)
        assert angelegt["text"] == "Danke, dass du heute da warst."
        assert angelegt["emotion"] == "LOVED"
        assert angelegt["visibility"] == "SHARED"
        assert angelegt["happenedOn"] == "2025-06-13"
        assert angelegt["capabilities"] == {
            "canEdit": True,
            "canDelete": True,
            "canComment": True,
        }
        assert "privacyClass" not in angelegt
        assert created.headers["ETag"] == '"1"'

        geaendert = client.patch(
            f"{path(paar['space'].id)}/{angelegt['id']}",
            json={"text": "  Danke fuer den ruhigen Abend.  ", "emotion": "GRATEFUL"},
            headers=if_match(paar["token_a"], 1),
        )
        assert geaendert.status_code == 200
        assert geaendert.json()["text"] == "Danke fuer den ruhigen Abend."
        assert geaendert.json()["emotion"] == "GRATEFUL"
        assert geaendert.json()["version"] == 2

        geloescht = client.delete(
            f"{path(paar['space'].id)}/{angelegt['id']}",
            headers=if_match(paar["token_a"], 2),
        )
        assert geloescht.status_code == 204
        assert geloescht.content == b""

    def test_partner_liest_gemeinsame_aber_schreibt_nicht(self, client, paar) -> None:  # type: ignore[no-untyped-def]
        angelegt = erstelle(client, paar).json()

        gelesen = client.get(
            f"{path(paar['space'].id)}/{angelegt['id']}",
            headers=auth(paar["token_b"]),
        )
        assert gelesen.status_code == 200
        assert gelesen.json()["capabilities"] == {
            "canEdit": False,
            "canDelete": False,
            "canComment": True,
        }

        for antwort in (
            client.patch(
                f"{path(paar['space'].id)}/{angelegt['id']}",
                json={"text": "Von Ben geaendert."},
                headers=if_match(paar["token_b"], 1),
            ),
            client.delete(
                f"{path(paar['space'].id)}/{angelegt['id']}",
                headers=if_match(paar["token_b"], 1),
            ),
            client.patch(
                f"{path(paar['space'].id)}/{angelegt['id']}/visibility",
                json={"visibility": "PRIVATE"},
                headers=if_match(paar["token_b"], 1),
            ),
        ):
            assert antwort.status_code == 403

    def test_anonym_und_fremder_space_erreichen_nichts(self, client, paar) -> None:  # type: ignore[no-untyped-def]
        angelegt = erstelle(client, paar).json()

        assert client.get(f"{path(paar['space'].id)}/{angelegt['id']}").status_code == 401
        assert (
            client.get(
                f"{path(paar['fremder_space'].id)}/{angelegt['id']}",
                headers=auth(paar["token_fremd"]),
            ).status_code
            == 404
        )
        assert (
            client.get(
                f"{path(paar['space'].id)}/{angelegt['id']}",
                headers=auth(paar["token_fremd"]),
            ).status_code
            == 404
        )

    def test_unbekannte_und_missgeformte_id_antworten_gleich(self, client, paar) -> None:  # type: ignore[no-untyped-def]
        for kennung in (str(uuid4()), "keine-uuid"):
            antwort = client.get(
                f"{path(paar['space'].id)}/{kennung}",
                headers=auth(paar["token_a"]),
            )
            assert antwort.status_code == 404


class TestPrivateBleibtOwnerOnly:
    def test_partner_sieht_privaten_moment_in_keinem_pfad(self, client, paar) -> None:  # type: ignore[no-untyped-def]
        privat = erstelle(client, paar, visibility="PRIVATE", text=GEHEIMER_TEXT).json()

        detail = client.get(
            f"{path(paar['space'].id)}/{privat['id']}",
            headers=auth(paar["token_b"]),
        )
        assert detail.status_code == 404
        assert GEHEIMER_TEXT not in detail.text

        for query in ("", "?visibility=PRIVATE", "?visibility=SHARED", "?limit=100"):
            liste = client.get(
                f"{path(paar['space'].id)}{query}",
                headers=auth(paar["token_b"]),
            )
            assert liste.status_code == 200
            assert liste.json()["items"] == []
            assert liste.json()["hasMore"] is False
            assert GEHEIMER_TEXT not in liste.text

    def test_partner_antwort_ist_nicht_von_nichtexistenz_unterscheidbar(self, client, paar) -> None:  # type: ignore[no-untyped-def]
        """Kein Exists-Signal: 404 hier, 404 dort, gleicher Koerper."""
        privat = erstelle(client, paar, visibility="PRIVATE").json()

        vorhanden = client.get(
            f"{path(paar['space'].id)}/{privat['id']}",
            headers=auth(paar["token_b"]),
        )
        erfunden = client.get(
            f"{path(paar['space'].id)}/{uuid4()}",
            headers=auth(paar["token_b"]),
        )
        assert vorhanden.status_code == erfunden.status_code == 404
        assert vorhanden.json() == erfunden.json()

    def test_partner_kann_privaten_moment_nicht_aendern_oder_loeschen(self, client, paar) -> None:  # type: ignore[no-untyped-def]
        """404 statt 403: ein 403 wuerde die Existenz bestaetigen."""
        privat = erstelle(client, paar, visibility="PRIVATE").json()

        for antwort in (
            client.patch(
                f"{path(paar['space'].id)}/{privat['id']}",
                json={"text": "Fremdzugriff."},
                headers=if_match(paar["token_b"], 1),
            ),
            client.delete(
                f"{path(paar['space'].id)}/{privat['id']}",
                headers=if_match(paar["token_b"], 1),
            ),
            client.patch(
                f"{path(paar['space'].id)}/{privat['id']}/visibility",
                json={"visibility": "SHARED"},
                headers=if_match(paar["token_b"], 1),
            ),
        ):
            assert antwort.status_code == 404

    def test_owner_sieht_seinen_privaten_moment(self, client, paar) -> None:  # type: ignore[no-untyped-def]
        privat = erstelle(client, paar, visibility="PRIVATE").json()

        detail = client.get(
            f"{path(paar['space'].id)}/{privat['id']}",
            headers=auth(paar["token_a"]),
        )
        assert detail.status_code == 200
        assert detail.json()["visibility"] == "PRIVATE"
        assert detail.json()["capabilities"]["canComment"] is False

        liste = client.get(
            f"{path(paar['space'].id)}?visibility=PRIVATE",
            headers=auth(paar["token_a"]),
        )
        assert [eintrag["id"] for eintrag in liste.json()["items"]] == [privat["id"]]

    def test_beide_partner_halten_getrennte_private_bestaende(self, client, paar) -> None:  # type: ignore[no-untyped-def]
        von_anna = erstelle(client, paar, visibility="PRIVATE", text="Annas Satz.").json()
        von_ben = erstelle(
            client, paar, token_key="token_b", visibility="PRIVATE", text="Bens Satz."
        ).json()

        fuer_anna = client.get(
            f"{path(paar['space'].id)}?visibility=PRIVATE",
            headers=auth(paar["token_a"]),
        )
        assert [eintrag["id"] for eintrag in fuer_anna.json()["items"]] == [von_anna["id"]]
        assert "Bens Satz." not in fuer_anna.text

        fuer_ben = client.get(
            f"{path(paar['space'].id)}?visibility=PRIVATE",
            headers=auth(paar["token_b"]),
        )
        assert [eintrag["id"] for eintrag in fuer_ben.json()["items"]] == [von_ben["id"]]
        assert "Annas Satz." not in fuer_ben.text


class TestSichtbarkeitswechsel:
    def test_shared_zu_private_entzieht_dem_partner_den_zugriff(self, client, paar) -> None:  # type: ignore[no-untyped-def]
        geteilt = erstelle(client, paar, text=GEHEIMER_TEXT).json()
        assert (
            client.get(
                f"{path(paar['space'].id)}/{geteilt['id']}",
                headers=auth(paar["token_b"]),
            ).status_code
            == 200
        )

        gewechselt = client.patch(
            f"{path(paar['space'].id)}/{geteilt['id']}/visibility",
            json={"visibility": "PRIVATE"},
            headers=if_match(paar["token_a"], 1),
        )
        assert gewechselt.status_code == 200
        assert gewechselt.json()["visibility"] == "PRIVATE"
        assert gewechselt.json()["version"] == 2
        assert gewechselt.headers["ETag"] == '"2"'

        danach = client.get(
            f"{path(paar['space'].id)}/{geteilt['id']}",
            headers=auth(paar["token_b"]),
        )
        assert danach.status_code == 404
        assert GEHEIMER_TEXT not in danach.text

        liste = client.get(path(paar["space"].id), headers=auth(paar["token_b"]))
        assert liste.json()["items"] == []

    def test_private_zu_shared_oeffnet_wieder(self, client, paar) -> None:  # type: ignore[no-untyped-def]
        privat = erstelle(client, paar, visibility="PRIVATE").json()

        gewechselt = client.patch(
            f"{path(paar['space'].id)}/{privat['id']}/visibility",
            json={"visibility": "SHARED"},
            headers=if_match(paar["token_a"], 1),
        )
        assert gewechselt.status_code == 200
        assert gewechselt.json()["visibility"] == "SHARED"

        assert (
            client.get(
                f"{path(paar['space'].id)}/{privat['id']}",
                headers=auth(paar["token_b"]),
            ).status_code
            == 200
        )

    def test_wechsel_auf_denselben_wert_aendert_nichts(self, client, paar) -> None:  # type: ignore[no-untyped-def]
        geteilt = erstelle(client, paar).json()

        antwort = client.patch(
            f"{path(paar['space'].id)}/{geteilt['id']}/visibility",
            json={"visibility": "SHARED"},
            headers=if_match(paar["token_a"], 1),
        )
        assert antwort.status_code == 200
        assert antwort.json()["version"] == 1
        assert antwort.headers["ETag"] == '"1"'

    def test_wechsel_verlangt_aktuelle_version(self, client, paar) -> None:  # type: ignore[no-untyped-def]
        geteilt = erstelle(client, paar).json()
        client.patch(
            f"{path(paar['space'].id)}/{geteilt['id']}",
            json={"text": "Zwischenstand."},
            headers=if_match(paar["token_a"], 1),
        )

        veraltet = client.patch(
            f"{path(paar['space'].id)}/{geteilt['id']}/visibility",
            json={"visibility": "PRIVATE"},
            headers=if_match(paar["token_a"], 1),
        )
        assert veraltet.status_code == 409
        assert veraltet.json()["code"] == "RESOURCE_VERSION_CONFLICT"

        unveraendert = client.get(
            f"{path(paar['space'].id)}/{geteilt['id']}",
            headers=auth(paar["token_a"]),
        )
        assert unveraendert.json()["visibility"] == "SHARED"

    def test_wechsel_ohne_if_match_wird_abgelehnt(self, client, paar) -> None:  # type: ignore[no-untyped-def]
        geteilt = erstelle(client, paar).json()
        antwort = client.patch(
            f"{path(paar['space'].id)}/{geteilt['id']}/visibility",
            json={"visibility": "PRIVATE"},
            headers=auth(paar["token_a"]),
        )
        assert antwort.status_code == 422

    def test_update_kann_die_sichtbarkeit_nicht_mitaendern(self, client, paar) -> None:  # type: ignore[no-untyped-def]
        geteilt = erstelle(client, paar).json()
        antwort = client.patch(
            f"{path(paar['space'].id)}/{geteilt['id']}",
            json={"text": "Neuer Text.", "visibility": "PRIVATE"},
            headers=if_match(paar["token_a"], 1),
        )
        assert antwort.status_code == 422

        unveraendert = client.get(
            f"{path(paar['space'].id)}/{geteilt['id']}",
            headers=auth(paar["token_a"]),
        )
        assert unveraendert.json()["visibility"] == "SHARED"
        assert unveraendert.json()["version"] == 1


class TestConcurrency:
    def test_veraltetes_update_und_delete_ergeben_409(self, client, paar) -> None:  # type: ignore[no-untyped-def]
        angelegt = erstelle(client, paar).json()
        client.patch(
            f"{path(paar['space'].id)}/{angelegt['id']}",
            json={"text": "Erste Aenderung."},
            headers=if_match(paar["token_a"], 1),
        )

        for antwort in (
            client.patch(
                f"{path(paar['space'].id)}/{angelegt['id']}",
                json={"text": "Zweite Aenderung."},
                headers=if_match(paar["token_a"], 1),
            ),
            client.delete(
                f"{path(paar['space'].id)}/{angelegt['id']}",
                headers=if_match(paar["token_a"], 1),
            ),
        ):
            assert antwort.status_code == 409
            assert antwort.json()["code"] == "RESOURCE_VERSION_CONFLICT"


class TestPagination:
    def test_cursor_blaettert_ohne_luecken_und_duplikate(self, client, paar) -> None:  # type: ignore[no-untyped-def]
        erwartet = [erstelle(client, paar, text=f"Moment {i}").json()["id"] for i in range(5)]

        gesehen: list[str] = []
        query = "?limit=2"
        while True:
            seite = client.get(f"{path(paar['space'].id)}{query}", headers=auth(paar["token_a"]))
            assert seite.status_code == 200
            gesehen.extend(eintrag["id"] for eintrag in seite.json()["items"])
            cursor = seite.json()["nextCursor"]
            if cursor is None:
                break
            query = f"?limit=2&cursor={cursor}"

        assert gesehen == list(reversed(erwartet))
        assert len(set(gesehen)) == len(gesehen)

    def test_manipulierter_cursor_wird_neutral_abgewiesen(self, client, paar) -> None:  # type: ignore[no-untyped-def]
        for i in range(3):
            erstelle(client, paar, text=f"Moment {i}")
        seite = client.get(f"{path(paar['space'].id)}?limit=1", headers=auth(paar["token_a"]))
        cursor = seite.json()["nextCursor"]
        assert cursor is not None

        nutzlast, signatur = cursor.split(".", 1)
        gefaelscht = f"{nutzlast[:-1]}{'A' if nutzlast[-1] != 'A' else 'B'}.{signatur}"
        verfaelscht = client.get(
            f"{path(paar['space'].id)}?limit=1&cursor={gefaelscht}",
            headers=auth(paar["token_a"]),
        )
        assert verfaelscht.status_code == 400
        assert verfaelscht.json()["code"] == "INVALID_CURSOR"

    def test_cursor_ist_an_seinen_filter_gebunden(self, client, paar) -> None:  # type: ignore[no-untyped-def]
        for i in range(3):
            erstelle(client, paar, text=f"Moment {i}")
        seite = client.get(f"{path(paar['space'].id)}?limit=1", headers=auth(paar["token_a"]))
        cursor = seite.json()["nextCursor"]

        gewechselt = client.get(
            f"{path(paar['space'].id)}?limit=1&visibility=SHARED&cursor={cursor}",
            headers=auth(paar["token_a"]),
        )
        assert gewechselt.status_code == 400
        assert gewechselt.json()["code"] == "INVALID_CURSOR"

    def test_cursor_eines_fremden_space_wird_abgewiesen(self, client, paar, session) -> None:  # type: ignore[no-untyped-def]
        for i in range(3):
            erstelle(client, paar, text=f"Moment {i}")
        seite = client.get(f"{path(paar['space'].id)}?limit=1", headers=auth(paar["token_a"]))
        cursor = seite.json()["nextCursor"]

        zweiter_space = make_space(session, paar["anna"])
        session.flush()

        antwort = client.get(
            f"{path(zweiter_space.id)}?limit=1&cursor={cursor}",
            headers=auth(paar["token_a"]),
        )
        assert antwort.status_code == 400
        assert antwort.json()["code"] == "INVALID_CURSOR"


class TestEreignisseLeckenNichts:
    def test_outbox_traegt_sichtbarkeit_aber_keinen_inhalt(self, client, paar, session) -> None:  # type: ignore[no-untyped-def]
        privat = erstelle(client, paar, visibility="PRIVATE", text=GEHEIMER_TEXT).json()
        client.patch(
            f"{path(paar['space'].id)}/{privat['id']}",
            json={"text": GEHEIMER_TEXT + " Nachtrag."},
            headers=if_match(paar["token_a"], 1),
        )
        client.patch(
            f"{path(paar['space'].id)}/{privat['id']}/visibility",
            json={"visibility": "SHARED"},
            headers=if_match(paar["token_a"], 2),
        )
        client.delete(
            f"{path(paar['space'].id)}/{privat['id']}",
            headers=if_match(paar["token_a"], 3),
        )

        zeilen = list(
            session.execute(
                select(OutboxEvent).where(OutboxEvent.subject_type == "heart_moment")
            ).scalars()
        )
        typen = [zeile.event_type for zeile in zeilen]
        assert typen == [
            "HEART_MOMENT_CREATED",
            "HEART_MOMENT_UPDATED",
            "HEART_MOMENT_VISIBILITY_CHANGED",
            "HEART_MOMENT_DELETED",
        ]

        sichtbarkeiten = [zeile.payload.visibility for zeile in zeilen]
        assert sichtbarkeiten == ["PRIVATE", "PRIVATE", "SHARED", "SHARED"]

        for zeile in zeilen:
            roh = repr(zeile.payload.model_dump())
            assert GEHEIMER_TEXT not in roh
            assert "LOVED" not in roh
            assert zeile.resource_version is not None

    def test_wechsel_ohne_aenderung_erzeugt_kein_ereignis(self, client, paar, session) -> None:  # type: ignore[no-untyped-def]
        geteilt = erstelle(client, paar).json()
        client.patch(
            f"{path(paar['space'].id)}/{geteilt['id']}/visibility",
            json={"visibility": "SHARED"},
            headers=if_match(paar["token_a"], 1),
        )

        typen = [
            zeile.event_type
            for zeile in session.execute(
                select(OutboxEvent).where(OutboxEvent.subject_type == "heart_moment")
            ).scalars()
        ]
        assert typen == ["HEART_MOMENT_CREATED"]
