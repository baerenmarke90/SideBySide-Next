"""Echte PostgreSQL-Races fuer das Loeschen einer nahestehenden Person."""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from threading import Event
from time import sleep
from typing import Any
from uuid import UUID

import pytest
from sqlalchemy import select

from sidebyside.people.models import RelatedPerson
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
        token_a = sign_in(session, anna)
        space_id = space.id

    response = client.post(
        f"/api/v1/spaces/{space_id}/related-persons",
        json={
            "displayName": "Lisa",
            "relationship": "CHILD",
            "birthday": "2016-02-29",
            "birthdayYearKnown": True,
            "visibility": "SHARED",
        },
        headers=auth(token_a),
    )
    assert response.status_code == 201
    person = response.json()
    return client, maker, space_id, token_a, UUID(person["id"]), person["version"]


def _attempt_delete(client, path: str, headers: dict[str, str], started: Event) -> Any:  # type: ignore[no-untyped-def]
    started.set()
    return client.delete(path, headers=headers)


def test_delete_gegen_parallelen_delete_antwortet_404_statt_500(
    production_client,
) -> None:  # type: ignore[no-untyped-def]
    """Die Zeile verschwindet zwischen Guard-Abfrage und Sperre.

    Genau in diesem Fenster stand frueher ein ``session.refresh(...,
    with_for_update=True)``. Es endete auf einer geloeschten Zeile im
    Datenbankfehler und damit in einem 500 - einer Antwort, die es sonst
    fuer keine Abwesenheit gibt und die deshalb selbst schon eine Auskunft
    waere.
    """
    client, maker, space_id, token_a, person_id, version = _setup(production_client)

    # Der Blocker haelt die Zeile und loescht sie, committet aber noch
    # nicht. Der Guard des Requests liest unter READ COMMITTED weiterhin
    # die alte Zeile; erst die Sperre laeuft in die Wartezeit.
    blocker = maker()
    transaction = blocker.begin()
    person = blocker.execute(
        select(RelatedPerson).where(RelatedPerson.id == person_id).with_for_update()
    ).scalar_one()
    blocker.delete(person)
    blocker.flush()

    path = (
        f"/api/v1/spaces/{space_id}/related-persons/{person_id}?deletePolicy=preserve"
    )
    headers = {**auth(token_a), "If-Match": f'"{version}"'}

    started = Event()
    try:
        with ThreadPoolExecutor(max_workers=1) as pool:
            future = pool.submit(_attempt_delete, client, path, headers, started)
            assert started.wait(timeout=2)
            # Solange die exklusive Sperre steht, darf der Request nicht
            # fertig werden - er wartet nachweislich auf sie.
            sleep(0.2)
            assert not future.done()

            transaction.commit()
            response = future.result(timeout=5)
    finally:
        if transaction.is_active:
            transaction.rollback()
        blocker.close()

    assert response.status_code == 404
    assert response.json()["code"] == "RELATED_PERSON_NOT_FOUND"

    with maker() as verify:
        assert (
            verify.execute(
                select(RelatedPerson).where(RelatedPerson.id == person_id)
            ).scalar_one_or_none()
            is None
        )
