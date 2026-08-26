"""PostgreSQL-/HTTP-Abnahme fuer den Plan-Teil von M3-S2.

Hier steht alles, was ein Plan fuer sich allein kann: Direct Create nach
M3-D30, CRUD, der Statusautomat aus M3-D04 mit seinen Datumsinvarianten
und die Plan-Zeilen der Delete-Matrix aus M3-D05.

Was zwei Aggregate beruehrt - Konvertierung, Completion eines source
Plans, `return-to-wish` - steht in `test_wish_to_plan`.
"""

from __future__ import annotations

from datetime import timedelta
from typing import Any
from uuid import UUID, uuid4

import pytest
from sqlalchemy import select, text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from sidebyside.core.clock import today_in
from sidebyside.outbox.models import OutboxEvent
from sidebyside.plans.models import Plan, PlanStatus
from sidebyside.relationship import service as relationship_service
from tests.conftest import auth, make_account, make_space, requires_database, sign_in

pytestmark = [pytest.mark.integration, requires_database]

GEHEIM = "Ein Plan, der nicht in Ereignisse gehoert."

# Die Zeitzone des Testkontos. `experiencedOn` wird an ihrem Kalendertag
# gemessen, nicht an UTC - siehe M3-D04.
ZONE = "Europe/Berlin"


def heute() -> str:
    return today_in(ZONE).isoformat()


def gestern() -> str:
    return (today_in(ZONE) - timedelta(days=1)).isoformat()


def morgen() -> str:
    return (today_in(ZONE) + timedelta(days=1)).isoformat()


def path(space_id: object) -> str:
    return f"/api/v1/spaces/{space_id}/plans"


def body(
    *,
    title: str = "Wochenende in Kopenhagen",
    description: str | None = "Mit dem Zug hin.",
) -> dict[str, Any]:
    return {"title": title, "description": description}


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
    relationship_service.add_member(session, fremder_space.id, ben)
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


def erstelle(  # type: ignore[no-untyped-def]
    client,
    paar,
    *,
    token_key: str = "token_a",
    **overrides,
):
    return client.post(
        path(paar["space"].id), json=body(**overrides), headers=auth(paar[token_key])
    )


def aktion(  # type: ignore[no-untyped-def]
    client,
    paar,
    plan_id: str,
    name: str,
    version: int,
    json: dict[str, Any] | None = None,
):
    return client.post(
        f"{path(paar['space'].id)}/{plan_id}/{name}",
        json=json if json is not None else {},
        headers=if_match(paar["token_a"], version),
    )


class TestDirectCreate:
    """M3-D30: ein Plan darf ohne Wish entstehen."""

    def test_ein_direkter_plan_beginnt_als_idee_ohne_termine(  # type: ignore[no-untyped-def]
        self,
        client,
        paar,
    ) -> None:
        angelegt = erstelle(client, paar)
        assert angelegt.status_code == 201
        p = angelegt.json()
        assert UUID(p["id"]).version == 7
        assert p["title"] == "Wochenende in Kopenhagen"
        assert p["description"] == "Mit dem Zug hin."
        assert p["status"] == "IDEA"
        assert p["sourceWishId"] is None
        assert p["plannedStart"] is None
        assert p["plannedEnd"] is None
        assert p["experiencedOn"] is None
        assert p["createdBy"] == str(paar["anna"].id)
        assert p["capabilities"] == {"canEdit": True, "canDelete": True, "canComment": False}
        assert angelegt.headers["ETag"] == '"1"'

    @pytest.mark.parametrize(
        "feld",
        ["status", "sourceWishId", "plannedStart", "plannedEnd", "experiencedOn", "createdBy"],
    )
    def test_kein_serverseitiges_feld_kommt_aus_dem_request(  # type: ignore[no-untyped-def]
        self,
        client,
        paar,
        feld: str,
    ) -> None:
        werte = {
            "status": "COMPLETED",
            "sourceWishId": str(uuid4()),
            "plannedStart": "2026-09-01T18:00:00Z",
            "plannedEnd": "2026-09-02T18:00:00Z",
            "experiencedOn": gestern(),
            "createdBy": str(uuid4()),
        }
        antwort = client.post(
            path(paar["space"].id),
            json={**body(), feld: werte[feld]},
            headers=auth(paar["token_a"]),
        )
        assert antwort.status_code == 422

    def test_leerer_titel_wird_abgewiesen(  # type: ignore[no-untyped-def]
        self,
        client,
        paar,
    ) -> None:
        assert erstelle(client, paar, title="   ").status_code == 422


class TestCrud:
    def test_lesen_aendern_loeschen(self, client, paar) -> None:  # type: ignore[no-untyped-def]
        p = erstelle(client, paar).json()

        gelesen = client.get(f"{path(paar['space'].id)}/{p['id']}", headers=auth(paar["token_a"]))
        assert gelesen.status_code == 200
        assert gelesen.headers["ETag"] == '"1"'

        geaendert = client.patch(
            f"{path(paar['space'].id)}/{p['id']}",
            json={"title": "  Kopenhagen im Herbst  ", "description": None},
            headers=if_match(paar["token_a"], 1),
        )
        assert geaendert.status_code == 200
        assert geaendert.json()["title"] == "Kopenhagen im Herbst"
        assert geaendert.json()["description"] is None

        geloescht = client.delete(
            f"{path(paar['space'].id)}/{p['id']}", headers=if_match(paar["token_a"], 2)
        )
        assert geloescht.status_code == 204
        danach = client.get(f"{path(paar['space'].id)}/{p['id']}", headers=auth(paar["token_a"]))
        assert danach.status_code == 404
        assert danach.json()["code"] == "PLAN_NOT_FOUND"

    def test_der_partner_darf_aendern_und_createdby_bleibt(  # type: ignore[no-untyped-def]
        self,
        client,
        paar,
    ) -> None:
        """M3-D01 gilt fuer Plan wie fuer Wish."""
        p = erstelle(client, paar).json()
        geaendert = client.patch(
            f"{path(paar['space'].id)}/{p['id']}",
            json={"title": "Von Ben umbenannt"},
            headers=if_match(paar["token_b"], 1),
        )
        assert geaendert.status_code == 200
        assert geaendert.json()["createdBy"] == str(paar["anna"].id)

    def test_patch_kann_den_status_nicht_setzen(  # type: ignore[no-untyped-def]
        self,
        client,
        paar,
    ) -> None:
        p = erstelle(client, paar).json()
        for verboten in ({"status": "COMPLETED"}, {"plannedStart": "2026-09-01T18:00:00Z"}):
            antwort = client.patch(
                f"{path(paar['space'].id)}/{p['id']}",
                json=verboten,
                headers=if_match(paar["token_a"], 1),
            )
            assert antwort.status_code == 422

    def test_die_liste_filtert_nach_status(  # type: ignore[no-untyped-def]
        self,
        client,
        paar,
    ) -> None:
        idee = erstelle(client, paar, title="Idee").json()
        geplant = erstelle(client, paar, title="Geplant").json()
        aktion(client, paar, geplant["id"], "schedule", 1, {"plannedStart": "2026-09-01T18:00:00Z"})

        ideen = client.get(
            f"{path(paar['space'].id)}?status=IDEA", headers=auth(paar["token_a"])
        ).json()
        assert [e["id"] for e in ideen["items"]] == [idee["id"]]

        plaene = client.get(
            f"{path(paar['space'].id)}?status=PLANNED", headers=auth(paar["token_a"])
        ).json()
        assert [e["id"] for e in plaene["items"]] == [geplant["id"]]

    def test_der_cursor_gilt_nur_in_seinem_space(  # type: ignore[no-untyped-def]
        self,
        client,
        paar,
    ) -> None:
        erstelle(client, paar, title="Erster")
        erstelle(client, paar, title="Zweiter")
        seite = client.get(
            f"{path(paar['space'].id)}?limit=1", headers=auth(paar["token_a"])
        ).json()

        antwort = client.get(
            f"{path(paar['fremder_space'].id)}?limit=1&cursor={seite['nextCursor']}",
            headers=auth(paar["token_b"]),
        )
        assert antwort.status_code == 400
        assert antwort.json()["code"] == "INVALID_CURSOR"


class TestSchedule:
    def test_idee_wird_durch_terminierung_geplant(  # type: ignore[no-untyped-def]
        self,
        client,
        paar,
    ) -> None:
        p = erstelle(client, paar).json()
        antwort = aktion(
            client,
            paar,
            p["id"],
            "schedule",
            1,
            {"plannedStart": "2026-09-01T18:00:00Z", "plannedEnd": "2026-09-03T12:00:00Z"},
        )
        assert antwort.status_code == 200
        geplant = antwort.json()
        assert geplant["status"] == "PLANNED"
        assert geplant["plannedStart"] == "2026-09-01T18:00:00Z"
        assert geplant["plannedEnd"] == "2026-09-03T12:00:00Z"
        assert geplant["version"] == 2
        assert antwort.headers["ETag"] == '"2"'

    def test_ein_ende_ist_optional(self, client, paar) -> None:  # type: ignore[no-untyped-def]
        p = erstelle(client, paar).json()
        antwort = aktion(
            client, paar, p["id"], "schedule", 1, {"plannedStart": "2026-09-01T18:00:00Z"}
        )
        assert antwort.status_code == 200
        assert antwort.json()["plannedEnd"] is None

    def test_erneutes_terminieren_aendert_nur_die_termine(  # type: ignore[no-untyped-def]
        self,
        client,
        paar,
    ) -> None:
        """`PLANNED -> PLANNED` ist kein Statuswechsel, sondern eine Korrektur."""
        p = erstelle(client, paar).json()
        aktion(client, paar, p["id"], "schedule", 1, {"plannedStart": "2026-09-01T18:00:00Z"})

        antwort = aktion(
            client, paar, p["id"], "schedule", 2, {"plannedStart": "2026-09-08T18:00:00Z"}
        )
        assert antwort.status_code == 200
        assert antwort.json()["status"] == "PLANNED"
        assert antwort.json()["plannedStart"] == "2026-09-08T18:00:00Z"
        assert antwort.json()["version"] == 3

    def test_ein_ende_vor_dem_anfang_wird_abgewiesen(  # type: ignore[no-untyped-def]
        self,
        client,
        paar,
    ) -> None:
        p = erstelle(client, paar).json()
        antwort = aktion(
            client,
            paar,
            p["id"],
            "schedule",
            1,
            {"plannedStart": "2026-09-03T18:00:00Z", "plannedEnd": "2026-09-01T12:00:00Z"},
        )
        assert antwort.status_code == 422
        assert antwort.json()["code"] == "PLAN_DATE_RANGE_INVALID"

    def test_ohne_anfang_wird_nicht_terminiert(  # type: ignore[no-untyped-def]
        self,
        client,
        paar,
    ) -> None:
        p = erstelle(client, paar).json()
        antwort = aktion(client, paar, p["id"], "schedule", 1, {})
        assert antwort.status_code == 422

    def test_ein_abgeschlossener_plan_wird_nicht_mehr_terminiert(  # type: ignore[no-untyped-def]
        self,
        client,
        paar,
    ) -> None:
        p = erstelle(client, paar).json()
        aktion(client, paar, p["id"], "complete", 1, {"experiencedOn": gestern()})

        antwort = aktion(
            client, paar, p["id"], "schedule", 2, {"plannedStart": "2026-09-01T18:00:00Z"}
        )
        assert antwort.status_code == 409
        assert antwort.json()["code"] == "PLAN_STATUS_TRANSITION_INVALID"

    def test_veraltete_version_wird_abgewiesen(  # type: ignore[no-untyped-def]
        self,
        client,
        paar,
    ) -> None:
        p = erstelle(client, paar).json()
        aktion(client, paar, p["id"], "schedule", 1, {"plannedStart": "2026-09-01T18:00:00Z"})

        antwort = aktion(
            client, paar, p["id"], "schedule", 1, {"plannedStart": "2026-09-08T18:00:00Z"}
        )
        assert antwort.status_code == 409
        assert antwort.json()["code"] == "RESOURCE_VERSION_CONFLICT"


class TestUnschedule:
    def test_die_termine_werden_verworfen(  # type: ignore[no-untyped-def]
        self,
        client,
        paar,
    ) -> None:
        p = erstelle(client, paar).json()
        aktion(
            client,
            paar,
            p["id"],
            "schedule",
            1,
            {"plannedStart": "2026-09-01T18:00:00Z", "plannedEnd": "2026-09-03T12:00:00Z"},
        )

        antwort = aktion(client, paar, p["id"], "unschedule", 2)
        assert antwort.status_code == 200
        zurueck = antwort.json()
        assert zurueck["status"] == "IDEA"
        assert zurueck["plannedStart"] is None
        assert zurueck["plannedEnd"] is None

    def test_eine_idee_wird_nicht_entterminiert(  # type: ignore[no-untyped-def]
        self,
        client,
        paar,
    ) -> None:
        p = erstelle(client, paar).json()
        antwort = aktion(client, paar, p["id"], "unschedule", 1)
        assert antwort.status_code == 409
        assert antwort.json()["code"] == "PLAN_STATUS_TRANSITION_INVALID"

    def test_ein_abgeschlossener_plan_wird_nicht_entterminiert(  # type: ignore[no-untyped-def]
        self,
        client,
        paar,
    ) -> None:
        p = erstelle(client, paar).json()
        aktion(client, paar, p["id"], "schedule", 1, {"plannedStart": "2026-09-01T18:00:00Z"})
        aktion(client, paar, p["id"], "complete", 2, {"experiencedOn": gestern()})

        antwort = aktion(client, paar, p["id"], "unschedule", 3)
        assert antwort.status_code == 409
        assert antwort.json()["code"] == "PLAN_STATUS_TRANSITION_INVALID"


class TestComplete:
    def test_aus_einer_idee_heraus_erlaubt(  # type: ignore[no-untyped-def]
        self,
        client,
        paar,
    ) -> None:
        """Nicht alles Gemeinsame wird vorher geplant (M3-D04)."""
        p = erstelle(client, paar).json()
        antwort = aktion(client, paar, p["id"], "complete", 1, {"experiencedOn": gestern()})
        assert antwort.status_code == 200
        fertig = antwort.json()
        assert fertig["status"] == "COMPLETED"
        assert fertig["experiencedOn"] == gestern()
        assert fertig["plannedStart"] is None

    def test_aus_einem_termin_heraus_erhaelt_die_planzeiten(  # type: ignore[no-untyped-def]
        self,
        client,
        paar,
    ) -> None:
        p = erstelle(client, paar).json()
        aktion(
            client,
            paar,
            p["id"],
            "schedule",
            1,
            {"plannedStart": "2026-09-01T18:00:00Z", "plannedEnd": "2026-09-03T12:00:00Z"},
        )

        antwort = aktion(client, paar, p["id"], "complete", 2, {"experiencedOn": gestern()})
        assert antwort.status_code == 200
        fertig = antwort.json()
        assert fertig["status"] == "COMPLETED"
        # Historie, nicht Aufraeumen: der Termin bleibt lesbar.
        assert fertig["plannedStart"] == "2026-09-01T18:00:00Z"
        assert fertig["plannedEnd"] == "2026-09-03T12:00:00Z"

    def test_heute_ist_erlaubt(self, client, paar) -> None:  # type: ignore[no-untyped-def]
        p = erstelle(client, paar).json()
        antwort = aktion(client, paar, p["id"], "complete", 1, {"experiencedOn": heute()})
        assert antwort.status_code == 200

    def test_ein_zukuenftiger_tag_wird_abgewiesen(  # type: ignore[no-untyped-def]
        self,
        client,
        paar,
    ) -> None:
        p = erstelle(client, paar).json()
        antwort = aktion(client, paar, p["id"], "complete", 1, {"experiencedOn": morgen()})
        assert antwort.status_code == 422
        assert antwort.json()["code"] == "PLAN_EXPERIENCED_ON_IN_FUTURE"

    def test_ohne_tag_wird_nicht_abgeschlossen(  # type: ignore[no-untyped-def]
        self,
        client,
        paar,
    ) -> None:
        p = erstelle(client, paar).json()
        antwort = aktion(client, paar, p["id"], "complete", 1, {})
        assert antwort.status_code == 422

    def test_abgeschlossen_ist_terminal(self, client, paar) -> None:  # type: ignore[no-untyped-def]
        p = erstelle(client, paar).json()
        aktion(client, paar, p["id"], "complete", 1, {"experiencedOn": gestern()})

        antwort = aktion(client, paar, p["id"], "complete", 2, {"experiencedOn": gestern()})
        assert antwort.status_code == 409
        assert antwort.json()["code"] == "PLAN_STATUS_TRANSITION_INVALID"

    def test_ein_direkter_plan_erzeugt_keinen_wish(  # type: ignore[no-untyped-def]
        self,
        client,
        paar,
        session,
    ) -> None:
        from sidebyside.wishes.models import Wish

        p = erstelle(client, paar).json()
        aktion(client, paar, p["id"], "complete", 1, {"experiencedOn": gestern()})

        assert list(session.execute(select(Wish)).scalars()) == []


class TestKorrekturAmAbgeschlossenenPlan:
    def test_der_erlebte_tag_darf_korrigiert_werden(  # type: ignore[no-untyped-def]
        self,
        client,
        paar,
    ) -> None:
        p = erstelle(client, paar).json()
        aktion(client, paar, p["id"], "complete", 1, {"experiencedOn": heute()})

        antwort = client.patch(
            f"{path(paar['space'].id)}/{p['id']}",
            json={"experiencedOn": gestern()},
            headers=if_match(paar["token_a"], 2),
        )
        assert antwort.status_code == 200
        assert antwort.json()["experiencedOn"] == gestern()
        # Eine Korrektur ist keine Rueckoeffnung.
        assert antwort.json()["status"] == "COMPLETED"

    def test_auch_die_korrektur_darf_nicht_in_die_zukunft(  # type: ignore[no-untyped-def]
        self,
        client,
        paar,
    ) -> None:
        p = erstelle(client, paar).json()
        aktion(client, paar, p["id"], "complete", 1, {"experiencedOn": gestern()})

        antwort = client.patch(
            f"{path(paar['space'].id)}/{p['id']}",
            json={"experiencedOn": morgen()},
            headers=if_match(paar["token_a"], 2),
        )
        assert antwort.status_code == 422
        assert antwort.json()["code"] == "PLAN_EXPERIENCED_ON_IN_FUTURE"

    def test_ein_offener_plan_traegt_keinen_erlebten_tag(  # type: ignore[no-untyped-def]
        self,
        client,
        paar,
    ) -> None:
        """Sonst waere das PATCH ein vorweggenommener Abschluss."""
        p = erstelle(client, paar).json()
        antwort = client.patch(
            f"{path(paar['space'].id)}/{p['id']}",
            json={"experiencedOn": gestern()},
            headers=if_match(paar["token_a"], 1),
        )
        assert antwort.status_code == 409
        assert antwort.json()["code"] == "PLAN_STATUS_TRANSITION_INVALID"

    def test_der_erlebte_tag_kann_nicht_geleert_werden(  # type: ignore[no-untyped-def]
        self,
        client,
        paar,
    ) -> None:
        p = erstelle(client, paar).json()
        aktion(client, paar, p["id"], "complete", 1, {"experiencedOn": gestern()})

        antwort = client.patch(
            f"{path(paar['space'].id)}/{p['id']}",
            json={"experiencedOn": None},
            headers=if_match(paar["token_a"], 2),
        )
        assert antwort.status_code == 422


class TestDatenbankgrenzen:
    """Die Invarianten aus M3-D04 stehen auch im Schema, nicht nur im Dienst."""

    @pytest.mark.parametrize(
        ("sql", "grund"),
        [
            (
                "UPDATE plans SET planned_end = now() WHERE id = :id",
                "ein Ende ohne Anfang",
            ),
            (
                "UPDATE plans SET planned_start = now(), "
                "planned_end = now() - interval '1 day' WHERE id = :id",
                "ein Ende vor dem Anfang",
            ),
            (
                "UPDATE plans SET status = 'PLANNED' WHERE id = :id",
                "geplant ohne Anfang",
            ),
            (
                "UPDATE plans SET status = 'COMPLETED' WHERE id = :id",
                "abgeschlossen ohne erlebten Tag",
            ),
            (
                "UPDATE plans SET planned_start = now() WHERE id = :id",
                "eine Idee mit Termin",
            ),
        ],
    )
    def test_verletzte_invariante_wird_abgewiesen(  # type: ignore[no-untyped-def]
        self,
        client,
        paar,
        session,
        sql: str,
        grund: str,
    ) -> None:
        p = erstelle(client, paar).json()
        with pytest.raises(IntegrityError), session.begin_nested():
            session.execute(text(sql), {"id": p["id"]})

    def test_ein_erfundener_status_wird_abgewiesen(  # type: ignore[no-untyped-def]
        self,
        client,
        paar,
        session,
    ) -> None:
        p = erstelle(client, paar).json()
        with pytest.raises(IntegrityError), session.begin_nested():
            session.execute(
                text("UPDATE plans SET status = 'ERFUNDEN' WHERE id = :id"), {"id": p["id"]}
            )


class TestMandant:
    def test_ein_fremder_sieht_den_space_nicht(  # type: ignore[no-untyped-def]
        self,
        client,
        paar,
    ) -> None:
        erstelle(client, paar)
        antwort = client.get(path(paar["space"].id), headers=auth(paar["token_fremd"]))
        assert antwort.status_code == 404
        assert antwort.json()["code"] == "SPACE_NOT_FOUND"

    def test_eine_id_aus_dem_anderen_space_bleibt_unsichtbar(  # type: ignore[no-untyped-def]
        self,
        client,
        paar,
    ) -> None:
        p = erstelle(client, paar).json()
        gelesen = client.get(
            f"{path(paar['fremder_space'].id)}/{p['id']}", headers=auth(paar["token_b"])
        )
        assert gelesen.status_code == 404
        assert gelesen.json()["code"] == "PLAN_NOT_FOUND"

    def test_eine_fremde_lifecycle_aktion_aendert_nichts(  # type: ignore[no-untyped-def]
        self,
        client,
        paar,
        session,
    ) -> None:
        p = erstelle(client, paar).json()
        antwort = client.post(
            f"{path(paar['fremder_space'].id)}/{p['id']}/complete",
            json={"experiencedOn": gestern()},
            headers=if_match(paar["token_b"], 1),
        )
        assert antwort.status_code == 404

        session.expire_all()
        assert session.get(Plan, UUID(p["id"])).status == PlanStatus.IDEA.value


class TestEreignisse:
    def test_events_enthalten_keinen_plantext(  # type: ignore[no-untyped-def]
        self,
        client,
        paar,
        session,
    ) -> None:
        p = erstelle(client, paar, title=GEHEIM, description=GEHEIM).json()
        aktion(client, paar, p["id"], "schedule", 1, {"plannedStart": "2026-09-01T18:00:00Z"})
        aktion(client, paar, p["id"], "unschedule", 2)
        aktion(client, paar, p["id"], "complete", 3, {"experiencedOn": gestern()})
        client.delete(f"{path(paar['space'].id)}/{p['id']}", headers=if_match(paar["token_a"], 4))

        zeilen = list(
            session.execute(select(OutboxEvent).where(OutboxEvent.subject_type == "plan")).scalars()
        )
        assert [z.event_type for z in zeilen] == [
            "PLAN_CREATED",
            "PLAN_UPDATED",
            "PLAN_UPDATED",
            "PLAN_COMPLETED",
            "PLAN_DELETED",
        ]
        for zeile in zeilen:
            roh = repr(zeile.payload.model_dump())
            assert GEHEIM not in roh
            assert zeile.resource_version is not None

    def test_eine_abgewiesene_aktion_erzeugt_kein_ereignis(  # type: ignore[no-untyped-def]
        self,
        client,
        paar,
        session,
    ) -> None:
        p = erstelle(client, paar).json()
        aktion(client, paar, p["id"], "complete", 1, {"experiencedOn": morgen()})

        zeilen = list(
            session.execute(select(OutboxEvent).where(OutboxEvent.subject_type == "plan")).scalars()
        )
        assert [z.event_type for z in zeilen] == ["PLAN_CREATED"]
