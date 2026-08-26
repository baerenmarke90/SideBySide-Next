"""Echte PostgreSQL-Races und Rollbacks im Wish->Plan-Lifecycle.

Die Zusicherung aus M3-D02 ist scharf formuliert: *kein* Race darf einen
`PLANNED` Wish ohne originaeren Plan oder einen zweiten originaeren Plan
hinterlassen. Genau das wird hier nachgestellt - nicht mit Mocks, sondern
mit nebenlaeufigen Transaktionen gegen dieselbe Datenbank.

Jeder Test prueft zwei Dinge: dass beide Aufrufe ein *zulaessiges*
Ergebnis melden, und dass der Endzustand einer der erlaubten ist. Nur das
erste zu pruefen wuerde einen halben Lifecycle durchgehen lassen, solange
die Fehlermeldungen plausibel klingen.
"""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from datetime import timedelta
from threading import Barrier
from uuid import UUID

import pytest
from sqlalchemy import select

from sidebyside.authorization import AuthorizationContext
from sidebyside.core.clock import today_in
from sidebyside.core.errors import DomainError
from sidebyside.identity.models import Account
from sidebyside.plans import service as plan_service
from sidebyside.plans.models import Plan, PlanStatus
from sidebyside.relationship import service as relationship_service
from sidebyside.wishes import service as wish_service
from sidebyside.wishes.models import Wish, WishStatus
from tests.conftest import auth, make_account, make_space, requires_database, sign_in

pytestmark = [pytest.mark.integration, requires_database]

ZONE = "Europe/Berlin"


def _gestern() -> object:
    return today_in(ZONE) - timedelta(days=1)


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

    antwort = client.post(
        f"/api/v1/spaces/{space_id}/wishes",
        json={"title": "Nordlichter sehen"},
        headers=auth(token),
    )
    assert antwort.status_code == 201
    return {
        "client": client,
        "maker": maker,
        "space_id": space_id,
        "anna": AuthorizationContext(account_id=anna_id, space_id=space_id),
        "ben": AuthorizationContext(account_id=ben_id, space_id=space_id),
        "wish_id": UUID(antwort.json()["id"]),
    }


def _token(welt) -> str:  # type: ignore[no-untyped-def]
    """Einen frischen Access Token fuer den HTTP-Pfad ausstellen."""
    with welt["maker"].begin() as session:
        account = session.get(Account, welt["anna"].account_id)
        return sign_in(session, account)


def _ergebnis(fn):  # type: ignore[no-untyped-def]
    """Einen Dienstaufruf auf sein fachliches Ergebnis reduzieren."""
    try:
        return fn()
    except DomainError as error:
        return error.code


def _gleichzeitig(erste, zweite):  # type: ignore[no-untyped-def]
    """Zwei Aufrufe so dicht wie moeglich zusammen starten."""
    tor = Barrier(2, timeout=10)

    def lauf(fn):  # type: ignore[no-untyped-def]
        tor.wait()
        return _ergebnis(fn)

    with ThreadPoolExecutor(max_workers=2) as pool:
        a = pool.submit(lauf, erste)
        b = pool.submit(lauf, zweite)
        return a.result(timeout=20), b.result(timeout=20)


class TestParallelerConvert:
    def test_zwei_gleichzeitige_konvertierungen_erzeugen_genau_einen_plan(
        self, production_client
    ) -> None:  # type: ignore[no-untyped-def]
        welt = _setup(production_client)
        maker = welt["maker"]

        def konvertieren(context: AuthorizationContext):  # type: ignore[no-untyped-def]
            with maker.begin() as session:
                ergebnis = plan_service.convert_wish_to_plan(
                    session,
                    context,
                    welt["wish_id"],
                    expected_version=1,
                    title=None,
                    description=None,
                )
                return "CREATED" if ergebnis.created else f"RETRY:{ergebnis.plan.id}"

        erste, zweite = _gleichzeitig(
            lambda: konvertieren(welt["anna"]),
            lambda: konvertieren(welt["ben"]),
        )

        # Einer erzeugt, der andere bekommt denselben Plan idempotent
        # zurueck. Zwei `CREATED` waeren zwei Plans.
        assert sorted([erste.split(":")[0], zweite.split(":")[0]]) == ["CREATED", "RETRY"]

        with maker() as pruefung:
            plaene = list(pruefung.execute(select(Plan)).scalars())
            wish = pruefung.get(Wish, welt["wish_id"])
        assert len(plaene) == 1
        assert plaene[0].source_wish_id == welt["wish_id"]
        assert wish.status == WishStatus.PLANNED.value

    def test_ein_wartender_convert_bekommt_den_fertigen_plan(self, production_client) -> None:  # type: ignore[no-untyped-def]
        """Derselbe Fall, diesmal mit erzwungener Reihenfolge.

        Ein Blocker haelt die Wish-Sperre, waehrend der Convert schon
        laeuft. Er darf erst durchkommen, wenn die Sperre faellt - und muss
        dann den bereits erzeugten Plan sehen, nicht einen zweiten anlegen.
        """
        welt = _setup(production_client)
        maker = welt["maker"]

        blocker = maker()
        transaktion = blocker.begin()
        wish = blocker.execute(
            select(Wish).where(Wish.id == welt["wish_id"]).with_for_update()
        ).scalar_one()
        # Der Blocker konvertiert selbst - unter der eigenen Sperre.
        plan = Plan(
            space_id=welt["space_id"],
            owner_id=welt["anna"].account_id,
            privacy_class="SPACE_SHARED",
            status=PlanStatus.IDEA.value,
            source_wish_id=wish.id,
            payload=plan_service.PlanPayload(title="Vom Blocker"),
        )
        blocker.add(plan)
        wish.status = WishStatus.PLANNED.value
        blocker.flush()
        blockierter_plan = plan.id

        def konvertieren():  # type: ignore[no-untyped-def]
            with maker.begin() as session:
                ergebnis = plan_service.convert_wish_to_plan(
                    session,
                    welt["ben"],
                    welt["wish_id"],
                    expected_version=1,
                    title=None,
                    description=None,
                )
                return "CREATED" if ergebnis.created else str(ergebnis.plan.id)

        try:
            with ThreadPoolExecutor(max_workers=1) as pool:
                future = pool.submit(_ergebnis, konvertieren)
                transaktion.commit()
                assert future.result(timeout=10) == str(blockierter_plan)
        finally:
            if transaktion.is_active:
                transaktion.rollback()
            blocker.close()

        with maker() as pruefung:
            assert len(list(pruefung.execute(select(Plan)).scalars())) == 1


class TestRollback:
    def test_ein_fehler_nach_dem_plan_insert_hinterlaesst_keinen_plan(
        self, production_client, monkeypatch
    ) -> None:  # type: ignore[no-untyped-def]
        """Der Bruchpunkt liegt genau zwischen den beiden Mutationen.

        Der Plan ist eingefuegt, die Wish-Transition noch nicht gelaufen.
        Bleibt davon irgendetwas stehen, gaebe es einen originaeren Plan an
        einem Wish, der weiter `OPEN` ist.
        """
        welt = _setup(production_client)
        client = welt["client"]

        def kaputt(*args: object, **kwargs: object) -> None:
            raise RuntimeError("Bruch zwischen Plan-Insert und Wish-Transition")

        monkeypatch.setattr(wish_service, "plan_created", kaputt)

        token = _token(welt)
        antwort = client.post(
            f"/api/v1/spaces/{welt['space_id']}/wishes/{welt['wish_id']}/plan",
            json={},
            headers={"Authorization": f"Bearer {token}", "If-Match": '"1"'},
        )
        assert antwort.status_code == 500

        with welt["maker"]() as pruefung:
            assert list(pruefung.execute(select(Plan)).scalars()) == []
            assert pruefung.get(Wish, welt["wish_id"]).status == WishStatus.OPEN.value

    def test_ein_fehler_nach_der_plan_completion_hinterlaesst_nichts(
        self, production_client, monkeypatch
    ) -> None:  # type: ignore[no-untyped-def]
        welt = _setup(production_client)
        maker = welt["maker"]

        with maker.begin() as session:
            ergebnis = plan_service.convert_wish_to_plan(
                session,
                welt["anna"],
                welt["wish_id"],
                expected_version=1,
                title=None,
                description=None,
            )
            plan_id = ergebnis.plan.id

        def kaputt(*args: object, **kwargs: object) -> None:
            raise RuntimeError("Bruch zwischen Plan- und Wish-Completion")

        monkeypatch.setattr(wish_service, "plan_completed", kaputt)

        with pytest.raises(RuntimeError), maker.begin() as session:
            plan_service.complete_plan(
                session,
                welt["anna"],
                plan_id,
                expected_version=1,
                experienced_on=_gestern(),
            )

        with maker() as pruefung:
            plan = pruefung.get(Plan, plan_id)
            wish = pruefung.get(Wish, welt["wish_id"])
        assert plan.status == PlanStatus.IDEA.value
        assert plan.experienced_on is None
        assert wish.status == WishStatus.PLANNED.value


class TestDeleteGegenLifecycle:
    def test_delete_wish_gegen_convert_endet_konsistent(self, production_client) -> None:  # type: ignore[no-untyped-def]
        welt = _setup(production_client)
        maker = welt["maker"]

        def loeschen():  # type: ignore[no-untyped-def]
            with maker.begin() as session:
                wish_service.delete_wish(session, welt["anna"], welt["wish_id"], expected_version=1)
                return "DELETED"

        def konvertieren():  # type: ignore[no-untyped-def]
            with maker.begin() as session:
                plan_service.convert_wish_to_plan(
                    session,
                    welt["ben"],
                    welt["wish_id"],
                    expected_version=1,
                    title=None,
                    description=None,
                )
                return "CONVERTED"

        ergebnisse = set(_gleichzeitig(loeschen, konvertieren))

        with maker() as pruefung:
            wish = pruefung.get(Wish, welt["wish_id"])
            plaene = list(pruefung.execute(select(Plan)).scalars())

        if wish is None:
            # Der Delete war zuerst da. Dann darf es keinen Plan geben,
            # der auf einen nicht mehr existierenden Wish zeigt.
            assert plaene == []
            assert ergebnisse == {"DELETED", "WISH_NOT_FOUND"}
        else:
            # Der Convert war zuerst da. Dann haelt der Wish seinen Plan
            # fest, und der Delete ist gescheitert - und zwar schon an der
            # Version: der Convert hat den Wish auf 2 gehoben, der Delete
            # kam mit 1. Die Versionspruefung steht vor der Delete-Matrix,
            # damit ein veralteter Stand keine fachliche Auskunft ueber den
            # inzwischen entstandenen Plan erzeugt.
            assert wish.status == WishStatus.PLANNED.value
            assert len(plaene) == 1
            assert ergebnisse == {"CONVERTED", "RESOURCE_VERSION_CONFLICT"}

    def test_complete_gegen_return_hinterlaesst_keinen_halben_lifecycle(
        self, production_client
    ) -> None:  # type: ignore[no-untyped-def]
        welt = _setup(production_client)
        maker = welt["maker"]

        with maker.begin() as session:
            ergebnis = plan_service.convert_wish_to_plan(
                session,
                welt["anna"],
                welt["wish_id"],
                expected_version=1,
                title=None,
                description=None,
            )
            plan_id = ergebnis.plan.id

        def abschliessen():  # type: ignore[no-untyped-def]
            with maker.begin() as session:
                plan_service.complete_plan(
                    session,
                    welt["anna"],
                    plan_id,
                    expected_version=1,
                    experienced_on=_gestern(),
                )
                return "COMPLETED"

        def zurueckfuehren():  # type: ignore[no-untyped-def]
            with maker.begin() as session:
                plan_service.return_to_wish(session, welt["ben"], plan_id, expected_version=1)
                return "RETURNED"

        ergebnisse = set(_gleichzeitig(abschliessen, zurueckfuehren))

        with maker() as pruefung:
            plan = pruefung.get(Plan, plan_id)
            wish = pruefung.get(Wish, welt["wish_id"])

        if plan is None:
            # Zurueckgefuehrt: der Wunsch ist wieder offen, und niemand hat
            # nebenbei einen abgeschlossenen Plan hinterlassen.
            assert wish.status == WishStatus.OPEN.value
            assert "RETURNED" in ergebnisse
        else:
            # Abgeschlossen: beide Seiten stehen konsistent auf COMPLETED.
            assert plan.status == PlanStatus.COMPLETED.value
            assert wish.status == WishStatus.COMPLETED.value
            assert "COMPLETED" in ergebnisse

        # In keinem Fall bleibt ein abgeschlossener Plan neben einem
        # offenen Wunsch stehen.
        assert not (plan is not None and wish.status == WishStatus.OPEN.value)
