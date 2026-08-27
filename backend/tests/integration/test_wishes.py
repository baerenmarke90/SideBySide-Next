"""PostgreSQL/HTTP acceptance tests for the M3-S1 wish slice.

Zwei Schwerpunkte, and it are the eigentliche Fachlichkeit this Slices.

M3-D01: a Wish belongs to the couple. Unlike Memory and Milestone
may the Partner it aendern and loeschen, without it geschrieben to haben -
`createdBy` is Attribution and no ACL. The Proof is deshalb not
"Anna may", sondern "Ben may, and `createdBy` remains nevertheless Anna".

M3-D02/D04: the Wish-Status folgt exclusively the Wish->Plan-Contract.
The Proof dafuer is a Negativer: it exists no Path, through the a
gewoehnlicher Request the Status moves. The Kanten itself; Convert,
Completion, Return; stehen in `test_wish_to_plan`.
"""

from __future__ import annotations

from typing import Any
from uuid import UUID, uuid4

import pytest
from sqlalchemy import select, text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from sidebyside.outbox.models import OutboxEvent
from sidebyside.relationship import service as relationship_service
from sidebyside.wishes.models import Wish, WishStatus
from tests.conftest import auth, make_account, make_space, requires_database, sign_in

pytestmark = [pytest.mark.integration, requires_database]

GEHEIM = "Ein Wunsch, der nicht in Ereignisse gehoert."


def path(space_id: object) -> str:
    return f"/api/v1/spaces/{space_id}/wishes"


def body(*, title: str = "Nordlichter sehen") -> dict[str, Any]:
    return {"title": title}


def if_match(token: str, version: int) -> dict[str, str]:
    return {**auth(token), "If-Match": f'"{version}"'}


@pytest.fixture
def couple(session: Session):  # type: ignore[no-untyped-def]
    anna = make_account(session, "Anna")
    ben = make_account(session, "Ben")
    foreign = make_account(session, "Fremd")
    space = make_space(session, anna)
    relationship_service.add_member(session, space.id, ben)
    foreign_space = make_space(session, foreign)
    # Ben is intentionally a member of both spaces. This lets the cursor binding
    # itself tested are, instead of beforehand to the Membership to end.
    relationship_service.add_member(session, foreign_space.id, ben)
    session.flush()
    return {
        "anna": anna,
        "ben": ben,
        "space": space,
        "fremder_space": foreign_space,
        "token_a": sign_in(session, anna),
        "token_b": sign_in(session, ben),
        "token_fremd": sign_in(session, foreign),
    }


def erstelle(  # type: ignore[no-untyped-def]
    client,
    couple,
    *,
    token_key: str = "token_a",
    **overrides,
):
    return client.post(
        path(couple["space"].id), json=body(**overrides), headers=auth(couple[token_key])
    )


class TestCrud:
    def test_anlegen_lesen_change_delete(  # type: ignore[no-untyped-def]
        self,
        client,
        couple,
    ) -> None:
        angelegt = erstelle(client, couple)
        assert angelegt.status_code == 201
        w = angelegt.json()
        assert UUID(w["id"]).version == 7
        assert w["title"] == "Nordlichter sehen"
        assert w["status"] == "OPEN"
        assert w["createdBy"] == str(couple["anna"].id)
        assert w["creator"]["displayName"] == "Anna"
        assert w["capabilities"] == {"canEdit": True, "canDelete": True, "canComment": False}
        assert "privacyClass" not in w
        assert angelegt.headers["ETag"] == '"1"'

        gelesen = client.get(
            f"{path(couple['space'].id)}/{w['id']}", headers=auth(couple["token_a"])
        )
        assert gelesen.status_code == 200
        assert gelesen.headers["ETag"] == '"1"'

        updated = client.patch(
            f"{path(couple['space'].id)}/{w['id']}",
            json={"title": "  Nordlichter in Tromsoe sehen  "},
            headers=if_match(couple["token_a"], 1),
        )
        assert updated.status_code == 200
        assert updated.json()["title"] == "Nordlichter in Tromsoe sehen"
        assert updated.json()["version"] == 2
        assert updated.headers["ETag"] == '"2"'

        deleted = client.delete(
            f"{path(couple['space'].id)}/{w['id']}", headers=if_match(couple["token_a"], 2)
        )
        assert deleted.status_code == 204
        danach = client.get(
            f"{path(couple['space'].id)}/{w['id']}", headers=auth(couple["token_a"])
        )
        assert danach.status_code == 404
        assert danach.json()["code"] == "WISH_NOT_FOUND"

    def test_empty_title_is_rejected(  # type: ignore[no-untyped-def]
        self,
        client,
        couple,
    ) -> None:
        assert erstelle(client, couple, title="   ").status_code == 422

    def test_list_shows_neueste_first(self, client, couple) -> None:  # type: ignore[no-untyped-def]
        erster = erstelle(client, couple, title="Erster").json()
        zweiter = erstelle(client, couple, title="Zweiter").json()

        seite = client.get(path(couple["space"].id), headers=auth(couple["token_a"])).json()
        assert [entry["id"] for entry in seite["items"]] == [zweiter["id"], erster["id"]]
        assert seite["hasMore"] is False
        assert seite["nextCursor"] is None

    def test_the_seite_continues_via_the_cursor_weiter(  # type: ignore[no-untyped-def]
        self,
        client,
        couple,
    ) -> None:
        erster = erstelle(client, couple, title="Erster").json()
        zweiter = erstelle(client, couple, title="Zweiter").json()

        first_seite = client.get(
            f"{path(couple['space'].id)}?limit=1", headers=auth(couple["token_a"])
        ).json()
        assert [entry["id"] for entry in first_seite["items"]] == [zweiter["id"]]
        assert first_seite["hasMore"] is True

        second_seite = client.get(
            f"{path(couple['space'].id)}?limit=1&cursor={first_seite['nextCursor']}",
            headers=auth(couple["token_a"]),
        ).json()
        assert [entry["id"] for entry in second_seite["items"]] == [erster["id"]]
        assert second_seite["hasMore"] is False

    def test_the_status_filter_matches_only_existing_states(  # type: ignore[no-untyped-def]
        self,
        client,
        couple,
    ) -> None:
        erstelle(client, couple)

        offen = client.get(
            f"{path(couple['space'].id)}?status=OPEN", headers=auth(couple["token_a"])
        ).json()
        assert len(offen["items"]) == 1

        # Without Konvertierung exists it no geplanten Wish.
        planned = client.get(
            f"{path(couple['space'].id)}?status=PLANNED", headers=auth(couple["token_a"])
        ).json()
        assert planned["items"] == []

    def test_a_unknown_status_is_no_filter_sondern_a_error(  # type: ignore[no-untyped-def]
        self,
        client,
        couple,
    ) -> None:
        "otherwise a typo would silently produce to unfiltered list."
        response = client.get(
            f"{path(couple['space'].id)}?status=ERFUNDEN", headers=auth(couple["token_a"])
        )
        assert response.status_code == 422


class TestGemeinsamesSchreiben:
    "M3-D01: both Partner, not only the Creator."

    def test_the_partner_may_change_and_createdby_remains(  # type: ignore[no-untyped-def]
        self,
        client,
        couple,
    ) -> None:
        w = erstelle(client, couple).json()

        updated = client.patch(
            f"{path(couple['space'].id)}/{w['id']}",
            json={"title": "Nordlichter im Winter sehen"},
            headers=if_match(couple["token_b"], 1),
        )
        assert updated.status_code == 200
        # Attribution, no ACL: Ben has geschrieben, Anna remains Creator.
        assert updated.json()["createdBy"] == str(couple["anna"].id)
        assert updated.json()["creator"]["displayName"] == "Anna"

    def test_the_partner_may_delete(self, client, couple) -> None:  # type: ignore[no-untyped-def]
        w = erstelle(client, couple).json()
        response = client.delete(
            f"{path(couple['space'].id)}/{w['id']}", headers=if_match(couple["token_b"], 1)
        )
        assert response.status_code == 204

    def test_the_partner_sees_same_capabilities(  # type: ignore[no-untyped-def]
        self,
        client,
        couple,
    ) -> None:
        "A `canEdit: false` would be here a falsche Disclosure to the UI."
        w = erstelle(client, couple).json()
        gelesen = client.get(
            f"{path(couple['space'].id)}/{w['id']}", headers=auth(couple["token_b"])
        ).json()
        assert gelesen["capabilities"] == {
            "canEdit": True,
            "canDelete": True,
            "canComment": False,
        }

    def test_memory_remains_trotzdem_author_only(  # type: ignore[no-untyped-def]
        self,
        client,
        couple,
    ) -> None:
        """The countercheck for the new write rule.

        Collaborative write is a property of the M3 planning domains,
        no neue Voreinstellung. Would be it a, haette this Slice
        stillschweigend the Memory-Regel from Abschnitt 14 the
        Spezifikation aufgeweicht.
        """
        memory = client.post(
            f"/api/v1/spaces/{couple['space'].id}/memories",
            json={"title": "Nur von Anna", "body": "Text", "happenedOn": "2025-06-13"},
            headers=auth(couple["token_a"]),
        ).json()

        response = client.patch(
            f"/api/v1/spaces/{couple['space'].id}/memories/{memory['id']}",
            json={"title": "Von Ben geaendert"},
            headers=if_match(couple["token_b"], 1),
        )
        assert response.status_code == 403


class TestStatus:
    "M3-D02/D04: no path bypasses the Wish-to-Plan contract."

    def test_a_new_wish_is_offen(  # type: ignore[no-untyped-def]
        self,
        client,
        couple,
        session,
    ) -> None:
        w = erstelle(client, couple).json()
        row = session.get(Wish, UUID(w["id"]))
        assert row.status == WishStatus.OPEN.value

    def test_create_can_the_status_not_mitschicken(  # type: ignore[no-untyped-def]
        self,
        client,
        couple,
    ) -> None:
        response = client.post(
            path(couple["space"].id),
            json={"title": "Direkt geplant", "status": "PLANNED"},
            headers=auth(couple["token_a"]),
        )
        assert response.status_code == 422

    def test_patch_can_the_status_not_setzen(  # type: ignore[no-untyped-def]
        self,
        client,
        couple,
        session,
    ) -> None:
        w = erstelle(client, couple).json()

        response = client.patch(
            f"{path(couple['space'].id)}/{w['id']}",
            json={"status": "COMPLETED"},
            headers=if_match(couple["token_a"], 1),
        )
        assert response.status_code == 422

        session.expire_all()
        assert session.get(Wish, UUID(w["id"])).status == WishStatus.OPEN.value

    def test_auch_title_plus_status_geht_not_durch(  # type: ignore[no-untyped-def]
        self,
        client,
        couple,
        session,
    ) -> None:
        "A valid field must not carry a forbidden value."
        w = erstelle(client, couple).json()

        response = client.patch(
            f"{path(couple['space'].id)}/{w['id']}",
            json={"title": "Neuer Titel", "status": "COMPLETED"},
            headers=if_match(couple["token_a"], 1),
        )
        assert response.status_code == 422

        session.expire_all()
        row = session.get(Wish, UUID(w["id"]))
        assert row.status == WishStatus.OPEN.value
        assert row.payload.title == "Nordlichter sehen"

    def test_a_title_correction_allows_the_status_stehen(  # type: ignore[no-untyped-def]
        self,
        client,
        couple,
    ) -> None:
        w = erstelle(client, couple).json()
        updated = client.patch(
            f"{path(couple['space'].id)}/{w['id']}",
            json={"title": "Andere Formulierung"},
            headers=if_match(couple["token_a"], 1),
        )
        assert updated.json()["status"] == "OPEN"

    def test_the_database_allows_no_invented_status_to(  # type: ignore[no-untyped-def]
        self,
        client,
        couple,
        session,
    ) -> None:
        """the final boundary is enforced by the schema, not only by the service.

        Absichtlich as rohes SQL: through the ORM catches schon the
        Spaltentyp the Wert ab. Tested are soll here aber the CHECK in
        PostgreSQL; it is it, the therefore a Wartungsskript or a
        spaetere Migration aufhaelt.
        """
        w = erstelle(client, couple).json()
        # The Savepoint catches the Failure: without it bliebe the
        # Testtransaktion after the verletzten CHECK unusable.
        with pytest.raises(IntegrityError), session.begin_nested():
            session.execute(
                text("UPDATE wishes SET status = 'ERFUNDEN' WHERE id = :id"),
                {"id": w["id"]},
            )


class TestDeleteMatrix:
    """The Wish-Rows from M3-D05; now with real Plans.

    The drei erreichbaren Zustaende entstehen through the regulaeren Path:
    Convert makes `PLANNED`, Plan-Completion makes `COMPLETED`. Only the
    both Rows, the a widerspruechlichen State beschreiben,
    must it from Hand herstellen; it sollen laut Contract gar not
    entstehen can, and the Response darauf is nevertheless festgelegt.

    The complete conversion and completion paths are covered in
    `test_wish_to_plan`; here interessiert only, what `DELETE Wish` daraus
    makes.
    """

    def _konvertiere(self, client, couple, wish_id: str, version: int = 1) -> dict[str, Any]:
        response = client.post(
            f"{path(couple['space'].id)}/{wish_id}/plan",
            json={},
            headers=if_match(couple["token_a"], version),
        )
        assert response.status_code == 201
        return response.json()["plan"]

    def _schliesse_ab(self, client, couple, plan_id: str, version: int = 1) -> None:
        response = client.post(
            f"/api/v1/spaces/{couple['space'].id}/plans/{plan_id}/complete",
            json={"experiencedOn": "2026-08-20"},
            headers=if_match(couple["token_a"], version),
        )
        assert response.status_code == 200

    def test_offen_without_plan_may_deleted_werden(  # type: ignore[no-untyped-def]
        self,
        client,
        couple,
    ) -> None:
        w = erstelle(client, couple).json()
        response = client.delete(
            f"{path(couple['space'].id)}/{w['id']}", headers=if_match(couple["token_a"], 1)
        )
        assert response.status_code == 204

    def test_planned_with_plan_is_blockiert(  # type: ignore[no-untyped-def]
        self,
        client,
        couple,
        session,
    ) -> None:
        w = erstelle(client, couple).json()
        self._konvertiere(client, couple, w["id"])

        response = client.delete(
            f"{path(couple['space'].id)}/{w['id']}", headers=if_match(couple["token_a"], 2)
        )
        assert response.status_code == 409
        assert response.json()["code"] == "WISH_HAS_ACTIVE_PLAN"

        session.expire_all()
        assert session.get(Wish, UUID(w["id"])) is not None

    def test_completed_with_plan_is_blockiert(  # type: ignore[no-untyped-def]
        self,
        client,
        couple,
    ) -> None:
        w = erstelle(client, couple).json()
        plan = self._konvertiere(client, couple, w["id"])
        self._schliesse_ab(client, couple, plan["id"])

        response = client.delete(
            f"{path(couple['space'].id)}/{w['id']}", headers=if_match(couple["token_a"], 3)
        )
        assert response.status_code == 409
        assert response.json()["code"] == "WISH_HAS_COMPLETED_PLAN"

    def test_completed_without_plan_may_deleted_werden(  # type: ignore[no-untyped-def]
        self,
        client,
        couple,
    ) -> None:
        """The complete Cleanup of a completed Lifecycle.

        Erst the completed Plan, then the verbleibende completed Wish. It
        exists intentionally no Cascade, the the in a Schritt taete.
        """
        w = erstelle(client, couple).json()
        plan = self._konvertiere(client, couple, w["id"])
        self._schliesse_ab(client, couple, plan["id"])

        entfernt = client.delete(
            f"/api/v1/spaces/{couple['space'].id}/plans/{plan['id']}",
            headers=if_match(couple["token_a"], 2),
        )
        assert entfernt.status_code == 204

        # The Wish survives the Plan and remains completed.
        verbleibend = client.get(
            f"{path(couple['space'].id)}/{w['id']}", headers=auth(couple["token_a"])
        ).json()
        assert verbleibend["status"] == "COMPLETED"

        response = client.delete(
            f"{path(couple['space'].id)}/{w['id']}", headers=if_match(couple["token_a"], 3)
        )
        assert response.status_code == 204

    def test_planned_without_plan_is_a_widerspruch(  # type: ignore[no-untyped-def]
        self,
        client,
        couple,
        session,
    ) -> None:
        "A state that must not exist still must not produce a 500 response."
        w = erstelle(client, couple).json()
        row = session.get(Wish, UUID(w["id"]))
        row.status = WishStatus.PLANNED.value
        session.flush()

        response = client.delete(
            f"{path(couple['space'].id)}/{w['id']}",
            headers=if_match(couple["token_a"], row.version),
        )
        assert response.status_code == 409
        assert response.json()["code"] == "WISH_PLAN_STATE_CONFLICT"

    def test_offen_with_plan_is_a_widerspruch(  # type: ignore[no-untyped-def]
        self,
        client,
        couple,
        session,
    ) -> None:
        w = erstelle(client, couple).json()
        self._konvertiere(client, couple, w["id"])

        row = session.get(Wish, UUID(w["id"]))
        row.status = WishStatus.OPEN.value
        session.flush()

        response = client.delete(
            f"{path(couple['space'].id)}/{w['id']}",
            headers=if_match(couple["token_a"], row.version),
        )
        assert response.status_code == 409
        assert response.json()["code"] == "WISH_PLAN_STATE_CONFLICT"

    def test_planned_reports_the_auch_in_the_capabilities(  # type: ignore[no-untyped-def]
        self,
        client,
        couple,
    ) -> None:
        w = erstelle(client, couple).json()
        self._konvertiere(client, couple, w["id"])

        gelesen = client.get(
            f"{path(couple['space'].id)}/{w['id']}", headers=auth(couple["token_a"])
        ).json()
        assert gelesen["status"] == "PLANNED"
        assert gelesen["capabilities"]["canDelete"] is False
        # The Titel remains editable: it is a Inhaltsupdate, no
        # Statusmutation (M3-D02).
        assert gelesen["capabilities"]["canEdit"] is True

    def test_the_version_check_runs_before_the_status_check(  # type: ignore[no-untyped-def]
        self,
        client,
        couple,
    ) -> None:
        "a stale version must not reveal domain state."
        w = erstelle(client, couple).json()
        self._konvertiere(client, couple, w["id"])

        response = client.delete(
            f"{path(couple['space'].id)}/{w['id']}", headers=if_match(couple["token_a"], 99)
        )
        assert response.status_code == 409
        assert response.json()["code"] == "RESOURCE_VERSION_CONFLICT"

    def test_the_database_keeps_the_wish_under_its_plan_fest(  # type: ignore[no-untyped-def]
        self,
        client,
        couple,
        session,
    ) -> None:
        """the final boundary is enforced by the foreign key, not only by the service.

        The Service weist the Fall beforehand with 409 ab. Fails it once from -
        a Wartungsskript, a spaetere Migration -, verhindert the
        zusammengesetzte Foreign key nevertheless, that a Plan without
        its Wish zurueckbleibt.
        """
        w = erstelle(client, couple).json()
        self._konvertiere(client, couple, w["id"])

        with pytest.raises(IntegrityError), session.begin_nested():
            session.execute(text("DELETE FROM wishes WHERE id = :id"), {"id": w["id"]})


class TestNebenlaeufigkeit:
    def test_stale_version_is_rejected(  # type: ignore[no-untyped-def]
        self,
        client,
        couple,
    ) -> None:
        w = erstelle(client, couple).json()
        client.patch(
            f"{path(couple['space'].id)}/{w['id']}",
            json={"title": "Erste Aenderung"},
            headers=if_match(couple["token_a"], 1),
        )

        second = client.patch(
            f"{path(couple['space'].id)}/{w['id']}",
            json={"title": "Zweite Aenderung"},
            headers=if_match(couple["token_a"], 1),
        )
        assert second.status_code == 409
        assert second.json()["code"] == "RESOURCE_VERSION_CONFLICT"

    def test_beide_partner_teilen_sich_same_version(  # type: ignore[no-untyped-def]
        self,
        client,
        couple,
    ) -> None:
        "shared writes do not create separate version histories."
        w = erstelle(client, couple).json()
        client.patch(
            f"{path(couple['space'].id)}/{w['id']}",
            json={"title": "Von Anna"},
            headers=if_match(couple["token_a"], 1),
        )

        bens_attempt = client.patch(
            f"{path(couple['space'].id)}/{w['id']}",
            json={"title": "Von Ben"},
            headers=if_match(couple["token_b"], 1),
        )
        assert bens_attempt.status_code == 409

    def test_delete_without_if_match_is_not_ausgefuehrt(  # type: ignore[no-untyped-def]
        self,
        client,
        couple,
    ) -> None:
        w = erstelle(client, couple).json()
        response = client.delete(
            f"{path(couple['space'].id)}/{w['id']}", headers=auth(couple["token_a"])
        )
        assert response.status_code == 422
        assert (
            client.get(
                f"{path(couple['space'].id)}/{w['id']}", headers=auth(couple["token_a"])
            ).status_code
            == 200
        )


class TestMandant:
    def test_a_foreign_sees_the_space_not(  # type: ignore[no-untyped-def]
        self,
        client,
        couple,
    ) -> None:
        erstelle(client, couple)
        response = client.get(path(couple["space"].id), headers=auth(couple["token_fremd"]))
        assert response.status_code == 404
        assert response.json()["code"] == "SPACE_NOT_FOUND"

    def test_a_id_aus_dem_other_space_remains_unsichtbar(  # type: ignore[no-untyped-def]
        self,
        client,
        couple,
    ) -> None:
        "Ben is in both Spaces; the ID trennt it, not the Membership."
        w = erstelle(client, couple).json()

        gelesen = client.get(
            f"{path(couple['fremder_space'].id)}/{w['id']}", headers=auth(couple["token_b"])
        )
        assert gelesen.status_code == 404
        assert gelesen.json()["code"] == "WISH_NOT_FOUND"

    def test_a_foreign_write_attempt_changes_nothing(  # type: ignore[no-untyped-def]
        self,
        client,
        couple,
        session,
    ) -> None:
        w = erstelle(client, couple).json()

        response = client.patch(
            f"{path(couple['fremder_space'].id)}/{w['id']}",
            json={"title": "Uebernommen"},
            headers=if_match(couple["token_b"], 1),
        )
        assert response.status_code == 404

        session.expire_all()
        assert session.get(Wish, UUID(w["id"])).payload.title == "Nordlichter sehen"

    def test_the_list_the_other_space_remains_leer(  # type: ignore[no-untyped-def]
        self,
        client,
        couple,
    ) -> None:
        erstelle(client, couple)
        seite = client.get(path(couple["fremder_space"].id), headers=auth(couple["token_b"])).json()
        assert seite["items"] == []

    def test_a_cursor_applies_only_in_its_space(  # type: ignore[no-untyped-def]
        self,
        client,
        couple,
    ) -> None:
        erstelle(client, couple, title="Erster")
        erstelle(client, couple, title="Zweiter")
        seite = client.get(
            f"{path(couple['space'].id)}?limit=1", headers=auth(couple["token_a"])
        ).json()

        response = client.get(
            f"{path(couple['fremder_space'].id)}?limit=1&cursor={seite['nextCursor']}",
            headers=auth(couple["token_b"]),
        )
        assert response.status_code == 400
        assert response.json()["code"] == "INVALID_CURSOR"

    def test_a_cursor_applies_only_for_its_filter(  # type: ignore[no-untyped-def]
        self,
        client,
        couple,
    ) -> None:
        erstelle(client, couple, title="Erster")
        erstelle(client, couple, title="Zweiter")
        seite = client.get(
            f"{path(couple['space'].id)}?limit=1&status=OPEN", headers=auth(couple["token_a"])
        ).json()

        response = client.get(
            f"{path(couple['space'].id)}?limit=1&cursor={seite['nextCursor']}",
            headers=auth(couple["token_a"]),
        )
        assert response.status_code == 400

    def test_a_invented_id_and_a_malformed_klingen_gleich(  # type: ignore[no-untyped-def]
        self,
        client,
        couple,
    ) -> None:
        unknown = client.get(
            f"{path(couple['space'].id)}/{uuid4()}", headers=auth(couple["token_a"])
        )
        malformed = client.get(
            f"{path(couple['space'].id)}/nicht-echt", headers=auth(couple["token_a"])
        )
        assert unknown.status_code == malformed.status_code == 404
        assert unknown.json() == malformed.json()


class TestEreignisse:
    def test_events_enthalten_no_wunschtitel(  # type: ignore[no-untyped-def]
        self,
        client,
        couple,
        session,
    ) -> None:
        w = erstelle(client, couple, title=GEHEIM).json()
        client.patch(
            f"{path(couple['space'].id)}/{w['id']}",
            json={"title": "Neu formuliert"},
            headers=if_match(couple["token_a"], 1),
        )
        client.delete(
            f"{path(couple['space'].id)}/{w['id']}", headers=if_match(couple["token_a"], 2)
        )

        rows = list(
            session.execute(select(OutboxEvent).where(OutboxEvent.subject_type == "wish")).scalars()
        )
        assert [z.event_type for z in rows] == [
            "WISH_CREATED",
            "WISH_UPDATED",
            "WISH_DELETED",
        ]
        for row in rows:
            raw = repr(row.payload.model_dump())
            assert GEHEIM not in raw
            assert "Neu formuliert" not in raw
            assert row.resource_version is not None

    def test_the_event_names_the_actor_and_not_the_creator(self, client, couple, session) -> None:  # type: ignore[no-untyped-def]
        "Audit after M3-D01: who changed has, not wem it zugeschrieben is."
        w = erstelle(client, couple).json()
        client.patch(
            f"{path(couple['space'].id)}/{w['id']}",
            json={"title": "Von Ben"},
            headers=if_match(couple["token_b"], 1),
        )

        change = session.execute(
            select(OutboxEvent).where(OutboxEvent.event_type == "WISH_UPDATED")
        ).scalar_one()
        assert change.actor_id == couple["ben"].id

    def test_a_abgewiesener_schreibversuch_creates_no_event(self, client, couple, session) -> None:  # type: ignore[no-untyped-def]
        w = erstelle(client, couple).json()
        client.patch(
            f"{path(couple['space'].id)}/{w['id']}",
            json={"title": "Kollision"},
            headers=if_match(couple["token_a"], 99),
        )

        rows = list(
            session.execute(select(OutboxEvent).where(OutboxEvent.subject_type == "wish")).scalars()
        )
        assert [z.event_type for z in rows] == ["WISH_CREATED"]
