"""Nebenlaeufigkeit rund um typisierte Content-Relations.

M3-D26 legt die Sperrreihenfolge fest: erst der Parent, dann das Target.
Jeder Test hier prueft beides - dass zwei gleichzeitige Requests zu einem
fachlichen Ergebnis kommen statt zu einem Deadlock oder 500, und dass der
Endzustand keine der Zusicherungen aus M3-D09 verletzt.

Der wichtigste Fall ist der letzte: Relation-Create gegen den
Privacy-Wechsel eines HeartMoments. Es gibt genau zwei zulaessige
Endzustaende - gemeinsam mit Relation oder privat ohne Relation. Der
dritte, privat mit Relation, waere ein Beweis der Existenz eines privaten
Inhalts fuer den Partner, und er darf in keiner Verschraenkung entstehen.
"""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from datetime import date
from threading import Barrier
from uuid import UUID

import pytest
from sqlalchemy import func, select

from sidebyside.authorization import AuthorizationContext, ContentVisibility
from sidebyside.core.errors import DomainError
from sidebyside.heart_moments import service as heart_moment_service
from sidebyside.heart_moments.models import HeartMoment
from sidebyside.memories.models import Memory
from sidebyside.places import service as place_service
from sidebyside.places.models import Place
from sidebyside.relations import service as relation_service
from sidebyside.relations.models import PlaceHeartMoment, PlaceMemory
from sidebyside.relationship import service as relationship_service
from tests.conftest import auth, make_account, make_space, requires_database, sign_in

pytestmark = [pytest.mark.integration, requires_database]

HEUTE = date(2026, 8, 27)


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

    kopf = auth(token)
    ort = client.post(
        f"/api/v1/spaces/{space_id}/places", json={"name": "Unser Cafe"}, headers=kopf
    )
    assert ort.status_code == 201
    erinnerung = client.post(
        f"/api/v1/spaces/{space_id}/memories",
        json={"title": "Erster Abend", "body": "Es regnete."},
        headers=kopf,
    )
    assert erinnerung.status_code == 201
    moment = client.post(
        f"/api/v1/spaces/{space_id}/heart-moments",
        json={
            "text": "Danke fuer heute.",
            "emotion": "LOVED",
            "visibility": "SHARED",
            "happenedOn": HEUTE.isoformat(),
        },
        headers=kopf,
    )
    assert moment.status_code == 201

    return {
        "maker": maker,
        "space_id": space_id,
        "anna": AuthorizationContext(account_id=anna_id, space_id=space_id),
        "ben": AuthorizationContext(account_id=ben_id, space_id=space_id),
        "place_id": UUID(ort.json()["id"]),
        "memory_id": UUID(erinnerung.json()["id"]),
        "heart_moment_id": UUID(moment.json()["id"]),
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


def _zaehle(maker, modell) -> int:  # type: ignore[no-untyped-def]
    with maker() as session:
        return session.execute(select(func.count()).select_from(modell)).scalar_one()


def test_parent_delete_gegen_relation_create(production_client) -> None:  # type: ignore[no-untyped-def]
    """Der Ort verschwindet, waehrend jemand daran verknuepft.

    Beide Seiten sperren den Ort zuerst. Einer wartet also, statt dass
    beide aufeinander warten. Danach revalidiert der Wartende - und findet
    entweder den Ort nicht mehr oder verknuepft an einem Ort, der noch da
    ist. Eine verwaiste Join-Zeile entsteht in keiner Reihenfolge.
    """
    welt = _setup(production_client)
    maker = welt["maker"]

    def loeschen():  # type: ignore[no-untyped-def]
        with maker.begin() as session:
            place_service.delete_place(session, welt["anna"], welt["place_id"], expected_version=1)
            return "DELETED"

    def verknuepfen():  # type: ignore[no-untyped-def]
        with maker.begin() as session:
            relation_service.link(
                session,
                welt["ben"],
                welt["place_id"],
                welt["memory_id"],
                relation_service.PLACE_MEMORIES,
            )
            return "LINKED"

    ergebnisse = set(_gleichzeitig(loeschen, verknuepfen))
    assert ergebnisse <= {"DELETED", "LINKED", "PLACE_NOT_FOUND", "RESOURCE_VERSION_CONFLICT"}

    with maker() as pruefung:
        ort = pruefung.get(Place, welt["place_id"])
        erinnerung = pruefung.get(Memory, welt["memory_id"])

    # Die Erinnerung ueberlebt in jedem Fall - sie ist ein Original.
    assert erinnerung is not None

    if ort is None:
        assert _zaehle(maker, PlaceMemory) == 0
    else:
        assert "LINKED" in ergebnisse
        assert _zaehle(maker, PlaceMemory) == 1


def test_target_delete_gegen_relation_create(production_client) -> None:  # type: ignore[no-untyped-def]
    """Das Ziel verschwindet, waehrend jemand darauf verweist.

    Der Create haelt das Ziel mit `FOR SHARE`; das Loeschen braucht die
    exklusive Sperre und wartet. Kommt es zuerst durch, findet der Create
    danach nichts mehr und antwortet 404 - nicht mit einem
    Fremdschluesselfehler aus der Datenbank.
    """
    welt = _setup(production_client)
    maker = welt["maker"]

    def loeschen():  # type: ignore[no-untyped-def]
        with maker.begin() as session:
            from sidebyside.memories import service as memory_service

            memory_service.delete_memory(
                session, welt["anna"], welt["memory_id"], expected_version=1
            )
            return "DELETED"

    def verknuepfen():  # type: ignore[no-untyped-def]
        with maker.begin() as session:
            relation_service.link(
                session,
                welt["ben"],
                welt["place_id"],
                welt["memory_id"],
                relation_service.PLACE_MEMORIES,
            )
            return "LINKED"

    ergebnisse = set(_gleichzeitig(loeschen, verknuepfen))
    assert ergebnisse <= {
        "DELETED",
        "LINKED",
        "RELATION_TARGET_NOT_FOUND",
        "RESOURCE_VERSION_CONFLICT",
    }

    with maker() as pruefung:
        erinnerung = pruefung.get(Memory, welt["memory_id"])

    if erinnerung is None:
        assert _zaehle(maker, PlaceMemory) == 0
    else:
        assert _zaehle(maker, PlaceMemory) == 1


def test_zwei_gleiche_creates_erzeugen_eine_zeile(production_client) -> None:  # type: ignore[no-untyped-def]
    """Beide Partner tippen gleichzeitig auf denselben Knopf.

    Kein Konflikt, kein Fehler, eine Zeile. Das leistet der
    Primaerschluessel zusammen mit `ON CONFLICT DO NOTHING` - ein
    vorheriges `SELECT` haette genau hier die Luecke.
    """
    welt = _setup(production_client)
    maker = welt["maker"]

    def verknuepfen(kontext):  # type: ignore[no-untyped-def]
        def lauf():  # type: ignore[no-untyped-def]
            with maker.begin() as session:
                relation_service.link(
                    session,
                    kontext,
                    welt["place_id"],
                    welt["memory_id"],
                    relation_service.PLACE_MEMORIES,
                )
                return "LINKED"

        return lauf

    ergebnisse = set(_gleichzeitig(verknuepfen(welt["anna"]), verknuepfen(welt["ben"])))
    assert ergebnisse == {"LINKED"}
    assert _zaehle(maker, PlaceMemory) == 1


def test_privacy_wechsel_gegen_relation_create_laesst_keinen_leak(  # type: ignore[no-untyped-def]
    production_client,
) -> None:
    """Der Fall, um den es in diesem Slice geht (M3-D09, M3-D26).

    Zwei zulaessige Endzustaende, und nur zwei:

    - der Moment ist gemeinsam und die Relation existiert;
    - der Moment ist privat und die Relation existiert nicht.

    Der dritte - privat mit Relation - waere fuer den Partner ein Beweis,
    dass es den Moment gibt, obwohl er ihn nicht lesen darf. Er darf in
    keiner Verschraenkung der beiden Transaktionen entstehen.
    """
    welt = _setup(production_client)
    maker = welt["maker"]

    def privat_schalten():  # type: ignore[no-untyped-def]
        with maker.begin() as session:
            heart_moment_service.change_visibility(
                session,
                welt["anna"],
                welt["heart_moment_id"],
                expected_version=1,
                visibility=ContentVisibility.PRIVATE,
            )
            return "PRIVATE"

    def verknuepfen():  # type: ignore[no-untyped-def]
        with maker.begin() as session:
            relation_service.link(
                session,
                welt["ben"],
                welt["place_id"],
                welt["heart_moment_id"],
                relation_service.PLACE_HEART_MOMENTS,
            )
            return "LINKED"

    ergebnisse = set(_gleichzeitig(privat_schalten, verknuepfen))

    # Kein Deadlock, kein Constraintfehler nach aussen: beide Seiten
    # melden ein fachliches Ergebnis.
    assert ergebnisse <= {
        "PRIVATE",
        "LINKED",
        "RELATION_TARGET_NOT_FOUND",
        "RESOURCE_VERSION_CONFLICT",
    }

    with maker() as pruefung:
        moment = pruefung.get(HeartMoment, welt["heart_moment_id"])
        assert moment is not None
        privat = moment.privacy_class == "OWNER_ONLY"

    relationen = _zaehle(maker, PlaceHeartMoment)

    if privat:
        assert relationen == 0, "privater Moment mit gemeinsamer Relation - genau der Leak"
    else:
        assert relationen == 1


def test_privacy_wechsel_gegen_create_in_umgekehrter_reihenfolge(  # type: ignore[no-untyped-def]
    production_client,
) -> None:
    """Dieselbe Zusicherung, wenn die Relation schon existiert.

    Hier ist die Join-Zeile vor dem Rennen da. Der Wechsel muss sie
    entfernen, waehrend ein zweiter Create sie gleichzeitig wiederherzu-
    stellen versucht. Auch das darf nicht in "privat mit Relation" enden.
    """
    welt = _setup(production_client)
    maker = welt["maker"]

    with maker.begin() as session:
        relation_service.link(
            session,
            welt["anna"],
            welt["place_id"],
            welt["heart_moment_id"],
            relation_service.PLACE_HEART_MOMENTS,
        )
    assert _zaehle(maker, PlaceHeartMoment) == 1

    def privat_schalten():  # type: ignore[no-untyped-def]
        with maker.begin() as session:
            heart_moment_service.change_visibility(
                session,
                welt["anna"],
                welt["heart_moment_id"],
                expected_version=1,
                visibility=ContentVisibility.PRIVATE,
            )
            return "PRIVATE"

    def erneut_verknuepfen():  # type: ignore[no-untyped-def]
        with maker.begin() as session:
            relation_service.link(
                session,
                welt["ben"],
                welt["place_id"],
                welt["heart_moment_id"],
                relation_service.PLACE_HEART_MOMENTS,
            )
            return "LINKED"

    ergebnisse = set(_gleichzeitig(privat_schalten, erneut_verknuepfen))
    assert ergebnisse <= {
        "PRIVATE",
        "LINKED",
        "RELATION_TARGET_NOT_FOUND",
        "RESOURCE_VERSION_CONFLICT",
    }

    with maker() as pruefung:
        moment = pruefung.get(HeartMoment, welt["heart_moment_id"])
        assert moment is not None
        privat = moment.privacy_class == "OWNER_ONLY"

    if privat:
        assert _zaehle(maker, PlaceHeartMoment) == 0
