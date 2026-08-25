"""PostgreSQL-/HTTP-Abnahme fuer den M2-Milestone-Slice.

Schwerpunkt ist M2-D25: geteilte Lesbarkeit ist keine Schreibvollmacht.
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

GEHEIM = "Ein Text, der nicht in Ereignisse gehoert."


def path(space_id: object) -> str:
    return f"/api/v1/spaces/{space_id}/milestones"


def body(
    *,
    title: str = "Zusammengezogen",
    body_text: str | None = "Erste gemeinsame Wohnung.",
    happened_on: str = "2025-06-13",
) -> dict[str, Any]:
    return {"title": title, "body": body_text, "happenedOn": happened_on}


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
        path(paar["space"].id), json=body(**overrides), headers=auth(paar[token_key])
    )


class TestCrud:
    def test_autor_kann_anlegen_lesen_aendern_loeschen(self, client, paar) -> None:  # type: ignore[no-untyped-def]
        angelegt = erstelle(client, paar)
        assert angelegt.status_code == 201
        m = angelegt.json()
        assert UUID(m["id"]).version == 7
        assert m["title"] == "Zusammengezogen"
        assert m["body"] == "Erste gemeinsame Wohnung."
        assert m["happenedOn"] == "2025-06-13"
        assert m["authorId"] == str(paar["anna"].id)
        assert m["capabilities"] == {"canEdit": True, "canDelete": True, "canComment": True}
        assert "privacyClass" not in m
        assert angelegt.headers["ETag"] == '"1"'

        geaendert = client.patch(
            f"{path(paar['space'].id)}/{m['id']}",
            json={"title": "  In die erste Wohnung gezogen  ", "body": None},
            headers=if_match(paar["token_a"], 1),
        )
        assert geaendert.status_code == 200
        assert geaendert.json()["title"] == "In die erste Wohnung gezogen"
        assert geaendert.json()["body"] is None
        assert geaendert.json()["version"] == 2

        geloescht = client.delete(
            f"{path(paar['space'].id)}/{m['id']}", headers=if_match(paar["token_a"], 2)
        )
        assert geloescht.status_code == 204

    def test_body_ist_optional(self, client, paar) -> None:  # type: ignore[no-untyped-def]
        angelegt = client.post(
            path(paar["space"].id),
            json={"title": "Verlobt", "happenedOn": "2024-12-24"},
            headers=auth(paar["token_a"]),
        )
        assert angelegt.status_code == 201
        assert angelegt.json()["body"] is None

    def test_happened_on_ist_pflicht(self, client, paar) -> None:  # type: ignore[no-untyped-def]
        antwort = client.post(
            path(paar["space"].id),
            json={"title": "Ohne Datum"},
            headers=auth(paar["token_a"]),
        )
        assert antwort.status_code == 422

    def test_leerer_titel_wird_abgelehnt(self, client, paar) -> None:  # type: ignore[no-untyped-def]
        assert erstelle(client, paar, title="   ").status_code == 422

    def test_patch_kann_happened_on_nicht_leeren(self, client, paar) -> None:  # type: ignore[no-untyped-def]
        m = erstelle(client, paar).json()
        antwort = client.patch(
            f"{path(paar['space'].id)}/{m['id']}",
            json={"happenedOn": None},
            headers=if_match(paar["token_a"], 1),
        )
        assert antwort.status_code == 422


class TestAutorregel:
    def test_partner_liest_aber_schreibt_nicht(self, client, paar) -> None:  # type: ignore[no-untyped-def]
        """M2-D25: geteilte Lesbarkeit ist keine Schreibvollmacht."""
        m = erstelle(client, paar).json()

        gelesen = client.get(f"{path(paar['space'].id)}/{m['id']}", headers=auth(paar["token_b"]))
        assert gelesen.status_code == 200
        assert gelesen.json()["capabilities"] == {
            "canEdit": False,
            "canDelete": False,
            "canComment": True,
        }

        for antwort in (
            client.patch(
                f"{path(paar['space'].id)}/{m['id']}",
                json={"title": "Von Ben geaendert."},
                headers=if_match(paar["token_b"], 1),
            ),
            client.delete(
                f"{path(paar['space'].id)}/{m['id']}", headers=if_match(paar["token_b"], 1)
            ),
        ):
            assert antwort.status_code == 403

    def test_partner_sieht_milestones_des_anderen_in_der_liste(self, client, paar) -> None:  # type: ignore[no-untyped-def]
        von_anna = erstelle(client, paar, title="Von Anna").json()
        von_ben = erstelle(client, paar, token_key="token_b", title="Von Ben").json()

        liste = client.get(path(paar["space"].id), headers=auth(paar["token_b"]))
        assert {e["id"] for e in liste.json()["items"]} == {von_anna["id"], von_ben["id"]}

    def test_author_id_ist_nicht_setzbar(self, client, paar) -> None:  # type: ignore[no-untyped-def]
        antwort = client.post(
            path(paar["space"].id),
            json={**body(), "authorId": str(paar["ben"].id)},
            headers=auth(paar["token_a"]),
        )
        assert antwort.status_code == 422


class TestIsolation:
    def test_anonym_und_fremder_space_erreichen_nichts(self, client, paar) -> None:  # type: ignore[no-untyped-def]
        m = erstelle(client, paar).json()
        assert client.get(f"{path(paar['space'].id)}/{m['id']}").status_code == 401
        assert (
            client.get(
                f"{path(paar['space'].id)}/{m['id']}", headers=auth(paar["token_fremd"])
            ).status_code
            == 404
        )

    def test_unbekannte_und_missgeformte_id_antworten_gleich(self, client, paar) -> None:  # type: ignore[no-untyped-def]
        for kennung in (str(uuid4()), "keine-uuid"):
            antwort = client.get(
                f"{path(paar['space'].id)}/{kennung}", headers=auth(paar["token_a"])
            )
            assert antwort.status_code == 404


class TestConcurrency:
    def test_veraltetes_update_und_delete_ergeben_409(self, client, paar) -> None:  # type: ignore[no-untyped-def]
        m = erstelle(client, paar).json()
        client.patch(
            f"{path(paar['space'].id)}/{m['id']}",
            json={"title": "Erste Aenderung"},
            headers=if_match(paar["token_a"], 1),
        )
        for antwort in (
            client.patch(
                f"{path(paar['space'].id)}/{m['id']}",
                json={"title": "Zweite Aenderung"},
                headers=if_match(paar["token_a"], 1),
            ),
            client.delete(
                f"{path(paar['space'].id)}/{m['id']}", headers=if_match(paar["token_a"], 1)
            ),
        ):
            assert antwort.status_code == 409
            assert antwort.json()["code"] == "RESOURCE_VERSION_CONFLICT"


class TestPaginationUndFilter:
    def test_cursor_blaettert_vollstaendig(self, client, paar) -> None:  # type: ignore[no-untyped-def]
        erwartet = [erstelle(client, paar, title=f"M {i}").json()["id"] for i in range(5)]

        gesehen: list[str] = []
        query = "?limit=2"
        while True:
            seite = client.get(f"{path(paar['space'].id)}{query}", headers=auth(paar["token_a"]))
            gesehen.extend(e["id"] for e in seite.json()["items"])
            cursor = seite.json()["nextCursor"]
            if cursor is None:
                break
            query = f"?limit=2&cursor={cursor}"

        assert gesehen == list(reversed(erwartet))
        assert len(set(gesehen)) == len(gesehen)

    def test_jahresfilter_arbeitet_auf_happened_on(self, client, paar) -> None:  # type: ignore[no-untyped-def]
        alt = erstelle(client, paar, title="2024", happened_on="2024-03-01").json()
        neu = erstelle(client, paar, title="2025", happened_on="2025-03-01").json()

        seite = client.get(f"{path(paar['space'].id)}?year=2024", headers=auth(paar["token_a"]))
        assert [e["id"] for e in seite.json()["items"]] == [alt["id"]]
        assert neu["id"] not in seite.text

    def test_cursor_ist_an_seinen_filter_gebunden(self, client, paar) -> None:  # type: ignore[no-untyped-def]
        for i in range(3):
            erstelle(client, paar, title=f"M {i}", happened_on="2025-03-01")
        seite = client.get(f"{path(paar['space'].id)}?limit=1", headers=auth(paar["token_a"]))
        cursor = seite.json()["nextCursor"]

        antwort = client.get(
            f"{path(paar['space'].id)}?limit=1&year=2025&cursor={cursor}",
            headers=auth(paar["token_a"]),
        )
        assert antwort.status_code == 400
        assert antwort.json()["code"] == "INVALID_CURSOR"

    def test_manipulierter_cursor_wird_abgewiesen(self, client, paar) -> None:  # type: ignore[no-untyped-def]
        for i in range(3):
            erstelle(client, paar, title=f"M {i}")
        seite = client.get(f"{path(paar['space'].id)}?limit=1", headers=auth(paar["token_a"]))
        cursor = seite.json()["nextCursor"]
        nutzlast, signatur = cursor.split(".", 1)
        gefaelscht = f"{nutzlast[:-1]}{'A' if nutzlast[-1] != 'A' else 'B'}.{signatur}"

        antwort = client.get(
            f"{path(paar['space'].id)}?limit=1&cursor={gefaelscht}",
            headers=auth(paar["token_a"]),
        )
        assert antwort.status_code == 400


class TestEreignisse:
    def test_events_enthalten_keinen_inhalt(self, client, paar, session) -> None:  # type: ignore[no-untyped-def]
        m = erstelle(client, paar, body_text=GEHEIM).json()
        client.patch(
            f"{path(paar['space'].id)}/{m['id']}",
            json={"title": "Neu"},
            headers=if_match(paar["token_a"], 1),
        )
        client.delete(f"{path(paar['space'].id)}/{m['id']}", headers=if_match(paar["token_a"], 2))

        zeilen = list(
            session.execute(
                select(OutboxEvent).where(OutboxEvent.subject_type == "milestone")
            ).scalars()
        )
        assert [z.event_type for z in zeilen] == [
            "MILESTONE_CREATED",
            "MILESTONE_UPDATED",
            "MILESTONE_DELETED",
        ]
        for zeile in zeilen:
            roh = repr(zeile.payload.model_dump())
            assert GEHEIM not in roh
            assert "Zusammengezogen" not in roh
            assert zeile.resource_version is not None
