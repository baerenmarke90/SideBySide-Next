"""Der Wish->Plan-Lifecycle aus M3-D02, M3-D03 und M3-D05.

Alles hier beruehrt zwei Aggregate gleichzeitig. Der wiederkehrende
Nachweis ist deshalb nicht "die Operation tut etwas", sondern "sie
hinterlaesst keinen halben Lifecycle": kein zweiter Plan, kein `PLANNED`
Wish ohne Plan, kein abgeschlossener Plan neben einem offenen Wish.
"""

from __future__ import annotations

from datetime import timedelta
from typing import Any
from uuid import UUID, uuid4

import pytest
from sqlalchemy import select
from sqlalchemy.orm import Session

from sidebyside.core.clock import today_in
from sidebyside.outbox.models import OutboxEvent
from sidebyside.plans.models import Plan, PlanStatus
from sidebyside.relationship import service as relationship_service
from sidebyside.wishes.models import Wish, WishStatus
from tests.conftest import auth, make_account, make_space, requires_database, sign_in

pytestmark = [pytest.mark.integration, requires_database]

ZONE = "Europe/Berlin"


def gestern() -> str:
    return (today_in(ZONE) - timedelta(days=1)).isoformat()


def wishes(space_id: object) -> str:
    return f"/api/v1/spaces/{space_id}/wishes"


def plans(space_id: object) -> str:
    return f"/api/v1/spaces/{space_id}/plans"


def if_match(token: str, version: int) -> dict[str, str]:
    return {**auth(token), "If-Match": f'"{version}"'}


@pytest.fixture
def paar(session: Session):  # type: ignore[no-untyped-def]
    anna = make_account(session, "Anna")
    ben = make_account(session, "Ben")
    space = make_space(session, anna)
    relationship_service.add_member(session, space.id, ben)
    session.flush()
    return {
        "anna": anna,
        "ben": ben,
        "space": space,
        "token_a": sign_in(session, anna),
        "token_b": sign_in(session, ben),
    }


def wunsch(  # type: ignore[no-untyped-def]
    client,
    paar,
    *,
    titel: str = "Nordlichter sehen",
) -> dict[str, Any]:
    antwort = client.post(
        wishes(paar["space"].id), json={"title": titel}, headers=auth(paar["token_a"])
    )
    assert antwort.status_code == 201
    return antwort.json()


def konvertiere(  # type: ignore[no-untyped-def]
    client, paar, wish_id: str, *, version: int = 1, token_key: str = "token_a", **felder
):
    return client.post(
        f"{wishes(paar['space'].id)}/{wish_id}/plan",
        json=dict(felder),
        headers=if_match(paar[token_key], version),
    )


def aktion(  # type: ignore[no-untyped-def]
    client,
    paar,
    plan_id: str,
    name: str,
    version: int,
    json: dict[str, Any] | None = None,
    token_key: str = "token_a",
):
    return client.post(
        f"{plans(paar['space'].id)}/{plan_id}/{name}",
        json=json if json is not None else {},
        headers=if_match(paar[token_key], version),
    )


class TestPflichtnachweis:
    def test_wunsch_wird_plan_wird_abgeschlossen(  # type: ignore[no-untyped-def]
        self,
        client,
        paar,
        session,
    ) -> None:
        """Der Pflichtflow aus dem M3 Delivery Plan, Abschnitt 5.

        ```text
        Wish Create -> Convert -> genau ein Plan -> Complete
        -> Wish + Plan konsistent COMPLETED
        ```
        """
        w = wunsch(client, paar)
        assert w["status"] == "OPEN"

        konvertiert = konvertiere(client, paar, w["id"])
        assert konvertiert.status_code == 201
        plan = konvertiert.json()["plan"]
        assert konvertiert.json()["wish"]["status"] == "PLANNED"
        assert plan["status"] == "IDEA"
        assert plan["sourceWishId"] == w["id"]

        # Genau ein Plan - nicht "mindestens einer".
        assert len(list(session.execute(select(Plan)).scalars())) == 1

        fertig = aktion(client, paar, plan["id"], "complete", 1, {"experiencedOn": gestern()})
        assert fertig.status_code == 200
        assert fertig.json()["status"] == "COMPLETED"

        session.expire_all()
        wish_zeile = session.get(Wish, UUID(w["id"]))
        plan_zeile = session.get(Plan, UUID(plan["id"]))
        assert wish_zeile.status == WishStatus.COMPLETED.value
        assert plan_zeile.status == PlanStatus.COMPLETED.value


class TestKonvertierung:
    def test_der_plan_uebernimmt_ohne_eigenen_titel_den_des_wunsches(  # type: ignore[no-untyped-def]
        self,
        client,
        paar,
    ) -> None:
        w = wunsch(client, paar, titel="Polarlichter")
        plan = konvertiere(client, paar, w["id"]).json()["plan"]
        assert plan["title"] == "Polarlichter"
        assert plan["description"] is None

    def test_ein_eigener_titel_gewinnt(self, client, paar) -> None:  # type: ignore[no-untyped-def]
        w = wunsch(client, paar)
        plan = konvertiere(
            client, paar, w["id"], title="Tromsoe im Februar", description="Sechs Naechte."
        ).json()["plan"]
        assert plan["title"] == "Tromsoe im Februar"
        assert plan["description"] == "Sechs Naechte."

    def test_wunsch_und_plan_laufen_danach_getrennt(  # type: ignore[no-untyped-def]
        self,
        client,
        paar,
    ) -> None:
        """M3-D01: eine Umbenennung synchronisiert nicht in die Gegenrichtung."""
        w = wunsch(client, paar)
        plan = konvertiere(client, paar, w["id"]).json()["plan"]

        client.patch(
            f"{wishes(paar['space'].id)}/{w['id']}",
            json={"title": "Ganz anderer Wunsch"},
            headers=if_match(paar["token_a"], 2),
        )
        gelesen = client.get(
            f"{plans(paar['space'].id)}/{plan['id']}", headers=auth(paar["token_a"])
        ).json()
        assert gelesen["title"] == "Nordlichter sehen"

    def test_der_partner_darf_konvertieren(  # type: ignore[no-untyped-def]
        self,
        client,
        paar,
    ) -> None:
        w = wunsch(client, paar)
        antwort = konvertiere(client, paar, w["id"], token_key="token_b")
        assert antwort.status_code == 201
        # Der Plan wird Ben zugeschrieben, der Wish bleibt bei Anna.
        assert antwort.json()["plan"]["createdBy"] == str(paar["ben"].id)
        assert antwort.json()["wish"]["createdBy"] == str(paar["anna"].id)

    @pytest.mark.parametrize("feld", ["sourceWishId", "status", "plannedStart", "experiencedOn"])
    def test_kein_serverseitiges_feld_kommt_aus_dem_request(  # type: ignore[no-untyped-def]
        self,
        client,
        paar,
        feld: str,
    ) -> None:
        w = wunsch(client, paar)
        werte = {
            "sourceWishId": str(uuid4()),
            "status": "COMPLETED",
            "plannedStart": "2026-09-01T18:00:00Z",
            "experiencedOn": gestern(),
        }
        antwort = konvertiere(client, paar, w["id"], **{feld: werte[feld]})
        assert antwort.status_code == 422

    def test_ein_veralteter_wunsch_erzeugt_keinen_plan(  # type: ignore[no-untyped-def]
        self,
        client,
        paar,
        session,
    ) -> None:
        w = wunsch(client, paar)
        client.patch(
            f"{wishes(paar['space'].id)}/{w['id']}",
            json={"title": "Inzwischen umbenannt"},
            headers=if_match(paar["token_a"], 1),
        )

        antwort = konvertiere(client, paar, w["id"], version=1)
        assert antwort.status_code == 409
        assert antwort.json()["code"] == "RESOURCE_VERSION_CONFLICT"
        assert list(session.execute(select(Plan)).scalars()) == []

    def test_ein_abgeschlossener_wunsch_wird_nicht_erneut_konvertiert(  # type: ignore[no-untyped-def]
        self,
        client,
        paar,
    ) -> None:
        w = wunsch(client, paar)
        plan = konvertiere(client, paar, w["id"]).json()["plan"]
        aktion(client, paar, plan["id"], "complete", 1, {"experiencedOn": gestern()})

        antwort = konvertiere(client, paar, w["id"], version=3)
        assert antwort.status_code == 409
        assert antwort.json()["code"] == "WISH_ALREADY_COMPLETED"

    def test_ein_fremder_wunsch_bleibt_unsichtbar(  # type: ignore[no-untyped-def]
        self,
        client,
        paar,
    ) -> None:
        antwort = konvertiere(client, paar, str(uuid4()))
        assert antwort.status_code == 404
        assert antwort.json()["code"] == "WISH_NOT_FOUND"


class TestIdempotenz:
    def test_ein_erneuter_aufruf_liefert_denselben_plan(  # type: ignore[no-untyped-def]
        self,
        client,
        paar,
        session,
    ) -> None:
        """Der Client hat die erste Antwort verloren und fragt noch einmal."""
        w = wunsch(client, paar)
        erster = konvertiere(client, paar, w["id"])
        assert erster.status_code == 201

        # Bewusst mit der *alten* Wish-Version: genau die haelt ein Client
        # in der Hand, dessen Antwort unterwegs verlorenging.
        zweiter = konvertiere(client, paar, w["id"], version=1)
        assert zweiter.status_code == 200
        assert zweiter.json()["plan"]["id"] == erster.json()["plan"]["id"]

        assert len(list(session.execute(select(Plan)).scalars())) == 1

    def test_ein_abweichender_retry_ueberschreibt_nichts(  # type: ignore[no-untyped-def]
        self,
        client,
        paar,
    ) -> None:
        w = wunsch(client, paar)
        erster = konvertiere(client, paar, w["id"], title="Erster Titel")

        zweiter = konvertiere(client, paar, w["id"], version=1, title="Anderer Titel")
        assert zweiter.status_code == 200
        assert zweiter.json()["plan"]["title"] == "Erster Titel"
        assert zweiter.json()["plan"]["version"] == erster.json()["plan"]["version"]

    def test_der_retry_erzeugt_kein_zweites_ereignis(  # type: ignore[no-untyped-def]
        self,
        client,
        paar,
        session,
    ) -> None:
        w = wunsch(client, paar)
        konvertiere(client, paar, w["id"])
        konvertiere(client, paar, w["id"], version=1)

        typen = [
            z.event_type
            for z in session.execute(
                select(OutboxEvent).where(
                    OutboxEvent.event_type.in_(["PLAN_CREATED", "WISH_PLANNED"])
                )
            ).scalars()
        ]
        assert typen == ["PLAN_CREATED", "WISH_PLANNED"]


class TestSourceCompletion:
    def test_plan_und_wunsch_werden_zusammen_abgeschlossen(  # type: ignore[no-untyped-def]
        self,
        client,
        paar,
        session,
    ) -> None:
        w = wunsch(client, paar)
        plan = konvertiere(client, paar, w["id"]).json()["plan"]

        aktion(client, paar, plan["id"], "complete", 1, {"experiencedOn": gestern()})

        session.expire_all()
        assert session.get(Wish, UUID(w["id"])).status == WishStatus.COMPLETED.value

    def test_beide_mutationen_liegen_in_einem_commit(  # type: ignore[no-untyped-def]
        self,
        client,
        paar,
        session,
    ) -> None:
        """Die Ereignisse belegen die Reihenfolge und die gemeinsame Grenze."""
        w = wunsch(client, paar)
        plan = konvertiere(client, paar, w["id"]).json()["plan"]
        aktion(client, paar, plan["id"], "complete", 1, {"experiencedOn": gestern()})

        typen = [
            z.event_type
            for z in session.execute(
                select(OutboxEvent).where(
                    OutboxEvent.event_type.in_(["PLAN_COMPLETED", "WISH_COMPLETED"])
                )
            ).scalars()
        ]
        assert typen == ["PLAN_COMPLETED", "WISH_COMPLETED"]

    def test_ein_zukuenftiger_tag_laesst_auch_den_wunsch_unberuehrt(  # type: ignore[no-untyped-def]
        self,
        client,
        paar,
        session,
    ) -> None:
        w = wunsch(client, paar)
        plan = konvertiere(client, paar, w["id"]).json()["plan"]

        morgen = (today_in(ZONE) + timedelta(days=1)).isoformat()
        antwort = aktion(client, paar, plan["id"], "complete", 1, {"experiencedOn": morgen})
        assert antwort.status_code == 422

        session.expire_all()
        assert session.get(Wish, UUID(w["id"])).status == WishStatus.PLANNED.value
        assert session.get(Plan, UUID(plan["id"])).status == PlanStatus.IDEA.value


class TestReturnToWish:
    def test_der_wunsch_wird_wieder_geoeffnet_und_der_plan_verschwindet(  # type: ignore[no-untyped-def]
        self,
        client,
        paar,
        session,
    ) -> None:
        w = wunsch(client, paar)
        plan = konvertiere(client, paar, w["id"]).json()["plan"]

        antwort = aktion(client, paar, plan["id"], "return-to-wish", 1)
        assert antwort.status_code == 200
        zurueck = antwort.json()
        assert zurueck["wish"]["status"] == "OPEN"
        assert zurueck["removedPlanId"] == plan["id"]

        session.expire_all()
        assert session.get(Plan, UUID(plan["id"])) is None
        gelesen = client.get(
            f"{plans(paar['space'].id)}/{plan['id']}", headers=auth(paar["token_a"])
        )
        assert gelesen.status_code == 404

    def test_auch_aus_dem_terminierten_zustand(  # type: ignore[no-untyped-def]
        self,
        client,
        paar,
    ) -> None:
        w = wunsch(client, paar)
        plan = konvertiere(client, paar, w["id"]).json()["plan"]
        aktion(client, paar, plan["id"], "schedule", 1, {"plannedStart": "2026-09-01T18:00:00Z"})

        antwort = aktion(client, paar, plan["id"], "return-to-wish", 2)
        assert antwort.status_code == 200
        assert antwort.json()["wish"]["status"] == "OPEN"

    def test_der_plantext_wird_nicht_in_den_wunsch_zurueckkopiert(  # type: ignore[no-untyped-def]
        self,
        client,
        paar,
    ) -> None:
        """M3-D03: keine stille Ueberschreibung divergierter Payloads."""
        w = wunsch(client, paar, titel="Urspruenglicher Wunsch")
        plan = konvertiere(client, paar, w["id"], title="Inzwischen ganz anders").json()["plan"]

        zurueck = aktion(client, paar, plan["id"], "return-to-wish", 1).json()
        assert zurueck["wish"]["title"] == "Urspruenglicher Wunsch"

    def test_danach_darf_erneut_konvertiert_werden(  # type: ignore[no-untyped-def]
        self,
        client,
        paar,
        session,
    ) -> None:
        """`UNIQUE(source_wish_id)` darf den Wunsch nicht dauerhaft blockieren."""
        w = wunsch(client, paar)
        erster = konvertiere(client, paar, w["id"]).json()["plan"]
        aktion(client, paar, erster["id"], "return-to-wish", 1)

        zweiter = konvertiere(client, paar, w["id"], version=3)
        assert zweiter.status_code == 201
        assert zweiter.json()["plan"]["id"] != erster["id"]
        assert len(list(session.execute(select(Plan)).scalars())) == 1

    def test_ein_direkter_plan_kann_nicht_zurueckgefuehrt_werden(  # type: ignore[no-untyped-def]
        self,
        client,
        paar,
    ) -> None:
        direkt = client.post(
            plans(paar["space"].id),
            json={"title": "Ohne Wunsch entstanden"},
            headers=auth(paar["token_a"]),
        ).json()

        antwort = aktion(client, paar, direkt["id"], "return-to-wish", 1)
        assert antwort.status_code == 409
        assert antwort.json()["code"] == "PLAN_SOURCE_WISH_REQUIRED"

    def test_ein_abgeschlossener_plan_kann_nicht_zurueckgefuehrt_werden(  # type: ignore[no-untyped-def]
        self,
        client,
        paar,
    ) -> None:
        w = wunsch(client, paar)
        plan = konvertiere(client, paar, w["id"]).json()["plan"]
        aktion(client, paar, plan["id"], "complete", 1, {"experiencedOn": gestern()})

        antwort = aktion(client, paar, plan["id"], "return-to-wish", 2)
        assert antwort.status_code == 409
        assert antwort.json()["code"] == "PLAN_STATUS_TRANSITION_INVALID"

    def test_eine_veraltete_version_fuehrt_nichts_zurueck(  # type: ignore[no-untyped-def]
        self,
        client,
        paar,
        session,
    ) -> None:
        w = wunsch(client, paar)
        plan = konvertiere(client, paar, w["id"]).json()["plan"]

        antwort = aktion(client, paar, plan["id"], "return-to-wish", 99)
        assert antwort.status_code == 409
        assert antwort.json()["code"] == "RESOURCE_VERSION_CONFLICT"

        session.expire_all()
        assert session.get(Plan, UUID(plan["id"])) is not None
        assert session.get(Wish, UUID(w["id"])).status == WishStatus.PLANNED.value

    def test_die_ereignisse_benennen_beide_folgen(  # type: ignore[no-untyped-def]
        self,
        client,
        paar,
        session,
    ) -> None:
        w = wunsch(client, paar)
        plan = konvertiere(client, paar, w["id"]).json()["plan"]
        aktion(client, paar, plan["id"], "return-to-wish", 1, token_key="token_b")

        letzte = list(
            session.execute(
                select(OutboxEvent).where(
                    OutboxEvent.event_type.in_(["PLAN_DELETED", "WISH_REOPENED"])
                )
            ).scalars()
        )
        assert [z.event_type for z in letzte] == ["PLAN_DELETED", "WISH_REOPENED"]
        assert all(z.actor_id == paar["ben"].id for z in letzte)


class TestPlanDeleteMatrix:
    """Die Plan-Zeilen aus M3-D05."""

    def test_ein_offener_source_plan_wird_nicht_geloescht(  # type: ignore[no-untyped-def]
        self,
        client,
        paar,
        session,
    ) -> None:
        w = wunsch(client, paar)
        plan = konvertiere(client, paar, w["id"]).json()["plan"]

        antwort = client.delete(
            f"{plans(paar['space'].id)}/{plan['id']}", headers=if_match(paar["token_a"], 1)
        )
        assert antwort.status_code == 409
        assert antwort.json()["code"] == "PLAN_HAS_SOURCE_WISH"

        session.expire_all()
        assert session.get(Plan, UUID(plan["id"])) is not None

    def test_ein_terminierter_source_plan_wird_nicht_geloescht(  # type: ignore[no-untyped-def]
        self,
        client,
        paar,
    ) -> None:
        w = wunsch(client, paar)
        plan = konvertiere(client, paar, w["id"]).json()["plan"]
        aktion(client, paar, plan["id"], "schedule", 1, {"plannedStart": "2026-09-01T18:00:00Z"})

        antwort = client.delete(
            f"{plans(paar['space'].id)}/{plan['id']}", headers=if_match(paar["token_a"], 2)
        )
        assert antwort.status_code == 409
        assert antwort.json()["code"] == "PLAN_HAS_SOURCE_WISH"

    def test_ein_abgeschlossener_source_plan_darf_geloescht_werden(  # type: ignore[no-untyped-def]
        self,
        client,
        paar,
        session,
    ) -> None:
        w = wunsch(client, paar)
        plan = konvertiere(client, paar, w["id"]).json()["plan"]
        aktion(client, paar, plan["id"], "complete", 1, {"experiencedOn": gestern()})

        antwort = client.delete(
            f"{plans(paar['space'].id)}/{plan['id']}", headers=if_match(paar["token_a"], 2)
        )
        assert antwort.status_code == 204

        # Keine Cascade in die Gegenrichtung: der Wunsch bleibt stehen.
        session.expire_all()
        assert session.get(Wish, UUID(w["id"])).status == WishStatus.COMPLETED.value

    def test_die_faehigkeiten_spiegeln_die_matrix(  # type: ignore[no-untyped-def]
        self,
        client,
        paar,
    ) -> None:
        w = wunsch(client, paar)
        plan = konvertiere(client, paar, w["id"]).json()["plan"]
        assert plan["capabilities"]["canDelete"] is False

        abgeschlossen = aktion(
            client, paar, plan["id"], "complete", 1, {"experiencedOn": gestern()}
        ).json()
        assert abgeschlossen["capabilities"]["canDelete"] is True
