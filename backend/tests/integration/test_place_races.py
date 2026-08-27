"""Nebenlaeufigkeit rund um Place-Delete und Plan-Zuordnung.

Die kanonische Sperrreihenfolge im M3-Kern ist `Place -> Wish -> Plan`.
Der Plan wird immer zuletzt gesperrt. Wuerde eine Operation den Ort nach
dem Plan sperren, koennten sich zwei Requests gegenseitig blockieren -
und PostgreSQL beendete einen davon mit einem Deadlock, also mit einem
500 fuer einen fachlich voellig normalen Vorgang.

Geprueft wird deshalb beides: dass nebenlaeufige Aufrufe zu einem
zulaessigen Ergebnis kommen, und dass der Endzustand nie einen Plan
zeigt, der auf einen geloeschten Ort verweist.
"""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from threading import Barrier
from uuid import UUID

import pytest
from sqlalchemy import select

from sidebyside.authorization import AuthorizationContext
from sidebyside.core.errors import DomainError
from sidebyside.places import service as place_service
from sidebyside.places.models import Place
from sidebyside.plans import service as plan_service
from sidebyside.plans.models import Plan
from sidebyside.relationship import service as relationship_service
from tests.conftest import auth, make_account, make_space, requires_database, sign_in

pytestmark = [pytest.mark.integration, requires_database]


def _setup(production_client):  # type: ignore[no-untyped-def]
    client, maker = production_client
    with maker.begin() as session:
        anna = make_account(session, "Anna")
        ben = make_account(session, "Ben")
        space = make_space(session, anna)
        relationship_service.add_member(session, space.id, ben)
        token = sign_in(session, anna)
        space_id = space.id
        anna_id = anna.id
        ben_id = ben.id

    ort = client.post(
        f"/api/v1/spaces/{space_id}/places",
        json={"name": "Unser Cafe", "latitude": 52.520008, "longitude": 13.404954},
        headers=auth(token),
    )
    assert ort.status_code == 201
    plan = client.post(
        f"/api/v1/spaces/{space_id}/plans",
        json={"title": "Abendessen"},
        headers=auth(token),
    )
    assert plan.status_code == 201

    return {
        "maker": maker,
        "space_id": space_id,
        "anna": AuthorizationContext(account_id=anna_id, space_id=space_id),
        "ben": AuthorizationContext(account_id=ben_id, space_id=space_id),
        "place_id": UUID(ort.json()["id"]),
        "plan_id": UUID(plan.json()["id"]),
    }


def _ergebnis(fn):  # type: ignore[no-untyped-def]
    try:
        return fn()
    except DomainError as error:
        return error.code


def _gleichzeitig(erste, zweite):  # type: ignore[no-untyped-def]
    tor = Barrier(2, timeout=10)

    def lauf(fn):  # type: ignore[no-untyped-def]
        tor.wait()
        return _ergebnis(fn)

    with ThreadPoolExecutor(max_workers=2) as pool:
        a = pool.submit(lauf, erste)
        b = pool.submit(lauf, zweite)
        return a.result(timeout=20), b.result(timeout=20)


def test_place_delete_gegen_plan_zuordnung_endet_konsistent(production_client) -> None:  # type: ignore[no-untyped-def]
    """Der Fall, der bei umgekehrter Sperrreihenfolge ein Deadlock waere.

    Der eine Request loescht den Ort und sperrt dafuer Ort und dann Plan.
    Der andere haengt den Plan an genau diesen Ort und sperrt dafuer
    ebenfalls erst den Ort, dann den Plan. Gleiche Reihenfolge, also
    wartet einer - statt dass beide aufeinander warten.
    """
    welt = _setup(production_client)
    maker = welt["maker"]

    def loeschen():  # type: ignore[no-untyped-def]
        with maker.begin() as session:
            place_service.delete_place(session, welt["anna"], welt["place_id"], expected_version=1)
            return "DELETED"

    def zuordnen():  # type: ignore[no-untyped-def]
        with maker.begin() as session:
            plan_service.update_plan(
                session,
                welt["ben"],
                welt["plan_id"],
                expected_version=1,
                changed_fields=frozenset({"place_id"}),
                title=None,
                description=None,
                place_id=welt["place_id"],
                experienced_on=None,
            )
            return "ASSIGNED"

    ergebnisse = set(_gleichzeitig(loeschen, zuordnen))

    with maker() as pruefung:
        ort = pruefung.get(Place, welt["place_id"])
        plan = pruefung.get(Plan, welt["plan_id"])

    # Kein Deadlock und kein 500: beide Seiten melden ein fachliches
    # Ergebnis.
    assert ergebnisse <= {"DELETED", "ASSIGNED", "PLACE_NOT_FOUND", "RESOURCE_VERSION_CONFLICT"}

    if ort is None:
        # Der Ort ist weg. Dann darf kein Plan mehr auf ihn zeigen -
        # unabhaengig davon, ob die Zuordnung vorher oder nachher kam.
        assert plan.place_id is None
    else:
        assert "ASSIGNED" in ergebnisse
        assert plan.place_id == welt["place_id"]


def test_zwei_plans_duerfen_denselben_ort_gleichzeitig_belegen(production_client) -> None:  # type: ignore[no-untyped-def]
    """Die Lesesperre auf dem Ort haelt die Existenz, nicht das Schreibrecht.

    Mit `FOR UPDATE` statt `FOR SHARE` wuerde hier einer der beiden
    unnoetig warten - und bei vielen Plans an einem beliebten Ort waere
    das eine Serialisierung ohne fachlichen Grund.
    """
    welt = _setup(production_client)
    maker = welt["maker"]

    with maker.begin() as session:
        zweiter = plan_service.create_plan(
            session, welt["anna"], title="Fruehstueck", description=None, place_id=None
        )
        zweiter_id = zweiter.id

    def zuordnen(plan_id):  # type: ignore[no-untyped-def]
        with maker.begin() as session:
            plan_service.update_plan(
                session,
                welt["anna"],
                plan_id,
                expected_version=1,
                changed_fields=frozenset({"place_id"}),
                title=None,
                description=None,
                place_id=welt["place_id"],
                experienced_on=None,
            )
            return "ASSIGNED"

    ergebnisse = _gleichzeitig(
        lambda: zuordnen(welt["plan_id"]),
        lambda: zuordnen(zweiter_id),
    )
    assert set(ergebnisse) == {"ASSIGNED"}

    with maker() as pruefung:
        plaene = list(pruefung.execute(select(Plan)).scalars())
    assert {p.place_id for p in plaene} == {welt["place_id"]}


def test_ein_geloeschter_ort_wird_nicht_mehr_zugeordnet(production_client) -> None:  # type: ignore[no-untyped-def]
    """Erzwungene Reihenfolge: der Delete gewinnt, die Zuordnung wartet."""
    welt = _setup(production_client)
    maker = welt["maker"]

    blocker = maker()
    transaktion = blocker.begin()
    ort = blocker.execute(
        select(Place).where(Place.id == welt["place_id"]).with_for_update()
    ).scalar_one()
    blocker.delete(ort)
    blocker.flush()

    def zuordnen():  # type: ignore[no-untyped-def]
        with maker.begin() as session:
            plan_service.update_plan(
                session,
                welt["ben"],
                welt["plan_id"],
                expected_version=1,
                changed_fields=frozenset({"place_id"}),
                title=None,
                description=None,
                place_id=welt["place_id"],
                experienced_on=None,
            )
            return "ASSIGNED"

    try:
        with ThreadPoolExecutor(max_workers=1) as pool:
            future = pool.submit(_ergebnis, zuordnen)
            transaktion.commit()
            assert future.result(timeout=10) == "PLACE_NOT_FOUND"
    finally:
        if transaktion.is_active:
            transaktion.rollback()
        blocker.close()

    with maker() as pruefung:
        assert pruefung.get(Plan, welt["plan_id"]).place_id is None
