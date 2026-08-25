"""PostgreSQL-Gate fuer die explizite RelatedPerson-Loeschpolicy."""

from __future__ import annotations

from typing import Any

import pytest
from sqlalchemy.orm import Session

from sidebyside.relationship import service as relationship_service
from tests.conftest import auth, make_account, make_space, requires_database, sign_in

pytestmark = [pytest.mark.integration, requires_database]


def persons_path(space_id: object) -> str:
    return f"/api/v1/spaces/{space_id}/related-persons"


def dates_path(space_id: object) -> str:
    return f"/api/v1/spaces/{space_id}/important-dates"


def person_body() -> dict[str, Any]:
    return {
        "displayName": "Lisa",
        "relationship": "CHILD",
        "birthday": "2016-02-29",
        "birthdayYearKnown": True,
        "visibility": "SHARED",
    }


def date_body(
    *,
    label: str,
    visibility: str,
    related_person_id: str | None = None,
) -> dict[str, Any]:
    body: dict[str, Any] = {
        "label": label,
        "type": "BIRTHDAY",
        "date": "2016-02-29",
        "repeats": "ANNUALLY",
        "visibility": visibility,
    }
    if related_person_id is not None:
        body["relatedPersonId"] = related_person_id
    return body


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
        "fremd": fremd,
        "space": space,
        "fremder_space": fremder_space,
        "token_a": sign_in(session, anna),
        "token_b": sign_in(session, ben),
        "token_fremd": sign_in(session, fremd),
    }


def create_person(client, paar):  # type: ignore[no-untyped-def]
    response = client.post(
        persons_path(paar["space"].id),
        json=person_body(),
        headers=auth(paar["token_a"]),
    )
    assert response.status_code == 201
    return response.json()


def create_date(
    client,
    paar,
    *,
    token_key: str,
    label: str,
    visibility: str,
    related_person_id: str | None,
):  # type: ignore[no-untyped-def]
    response = client.post(
        dates_path(paar["space"].id),
        json=date_body(
            label=label,
            visibility=visibility,
            related_person_id=related_person_id,
        ),
        headers=auth(paar[token_key]),
    )
    assert response.status_code == 201
    return response.json()


def delete_person(client, paar, person, policy: str, *, token_key: str = "token_a"):  # type: ignore[no-untyped-def]
    return client.delete(
        f"{persons_path(paar['space'].id)}/{person['id']}?deletePolicy={policy}",
        headers=if_match(paar[token_key], person["version"]),
    )


class TestPreserve:
    def test_erhaelt_alle_terminklassen_und_entfernt_nur_die_verknuepfung(
        self, client, paar
    ) -> None:  # type: ignore[no-untyped-def]
        person = create_person(client, paar)
        shared = create_date(
            client,
            paar,
            token_key="token_a",
            label="Geteilt",
            visibility="SHARED",
            related_person_id=person["id"],
        )
        own_private = create_date(
            client,
            paar,
            token_key="token_a",
            label="Privat Anna",
            visibility="PRIVATE",
            related_person_id=person["id"],
        )
        partner_private = create_date(
            client,
            paar,
            token_key="token_b",
            label="Privat Ben",
            visibility="PRIVATE",
            related_person_id=person["id"],
        )
        unrelated = create_date(
            client,
            paar,
            token_key="token_a",
            label="Ohne Bezug",
            visibility="SHARED",
            related_person_id=None,
        )

        response = delete_person(client, paar, person, "preserve")
        assert response.status_code == 204
        assert response.content == b""

        person_after = client.get(
            f"{persons_path(paar['space'].id)}/{person['id']}",
            headers=auth(paar["token_a"]),
        )
        assert person_after.status_code == 404

        for date_id, token_key in (
            (shared["id"], "token_a"),
            (own_private["id"], "token_a"),
            (partner_private["id"], "token_b"),
            (unrelated["id"], "token_a"),
        ):
            date_after = client.get(
                f"{dates_path(paar['space'].id)}/{date_id}",
                headers=auth(paar[token_key]),
            )
            assert date_after.status_code == 200
            assert date_after.json()["relatedPersonId"] is None

        assert (
            shared["version"] + 1
            == client.get(
                f"{dates_path(paar['space'].id)}/{shared['id']}",
                headers=auth(paar["token_a"]),
            ).json()["version"]
        )
        assert (
            own_private["version"] + 1
            == client.get(
                f"{dates_path(paar['space'].id)}/{own_private['id']}",
                headers=auth(paar["token_a"]),
            ).json()["version"]
        )
        assert (
            partner_private["version"] + 1
            == client.get(
                f"{dates_path(paar['space'].id)}/{partner_private['id']}",
                headers=auth(paar["token_b"]),
            ).json()["version"]
        )
        assert (
            unrelated["version"]
            == client.get(
                f"{dates_path(paar['space'].id)}/{unrelated['id']}",
                headers=auth(paar["token_a"]),
            ).json()["version"]
        )


class TestCascade:
    def test_loescht_alle_verknuepften_termine_aber_keine_unverknuepften(
        self, client, paar
    ) -> None:  # type: ignore[no-untyped-def]
        person = create_person(client, paar)
        own = create_date(
            client,
            paar,
            token_key="token_a",
            label="Anna",
            visibility="SHARED",
            related_person_id=person["id"],
        )
        partner_private = create_date(
            client,
            paar,
            token_key="token_b",
            label="Ben privat",
            visibility="PRIVATE",
            related_person_id=person["id"],
        )
        unrelated = create_date(
            client,
            paar,
            token_key="token_a",
            label="Bleibt",
            visibility="SHARED",
            related_person_id=None,
        )

        response = delete_person(client, paar, person, "cascade")
        assert response.status_code == 204
        assert response.content == b""

        assert (
            client.get(
                f"{dates_path(paar['space'].id)}/{own['id']}",
                headers=auth(paar["token_a"]),
            ).status_code
            == 404
        )
        assert (
            client.get(
                f"{dates_path(paar['space'].id)}/{partner_private['id']}",
                headers=auth(paar["token_b"]),
            ).status_code
            == 404
        )
        assert (
            client.get(
                f"{dates_path(paar['space'].id)}/{unrelated['id']}",
                headers=auth(paar["token_a"]),
            ).status_code
            == 200
        )


class TestDeletePolicyValidation:
    def test_fehlende_policy_wird_abgelehnt(self, client, paar) -> None:  # type: ignore[no-untyped-def]
        person = create_person(client, paar)
        response = client.delete(
            f"{persons_path(paar['space'].id)}/{person['id']}",
            headers=if_match(paar["token_a"], person["version"]),
        )
        assert response.status_code == 422
        assert (
            client.get(
                f"{persons_path(paar['space'].id)}/{person['id']}",
                headers=auth(paar["token_a"]),
            ).status_code
            == 200
        )

    def test_unbekannte_policy_wird_abgelehnt(self, client, paar) -> None:  # type: ignore[no-untyped-def]
        person = create_person(client, paar)
        response = delete_person(client, paar, person, "everything")
        assert response.status_code == 422

    def test_partner_darf_geteilte_person_weiterhin_nicht_loeschen(self, client, paar) -> None:  # type: ignore[no-untyped-def]
        person = create_person(client, paar)
        response = delete_person(client, paar, person, "preserve", token_key="token_b")
        assert response.status_code == 403
        assert response.json()["code"] == "NOT_RESOURCE_OWNER"

    def test_fremder_space_bleibt_404(self, client, paar) -> None:  # type: ignore[no-untyped-def]
        person = create_person(client, paar)
        response = client.delete(
            f"{persons_path(paar['fremder_space'].id)}/{person['id']}?deletePolicy=preserve",
            headers=if_match(paar["token_fremd"], person["version"]),
        )
        assert response.status_code == 404
        assert response.json()["code"] == "RELATED_PERSON_NOT_FOUND"

    def test_veraltetes_if_match_bleibt_versionskonflikt(self, client, paar) -> None:  # type: ignore[no-untyped-def]
        person = create_person(client, paar)
        updated = client.put(
            f"{persons_path(paar['space'].id)}/{person['id']}",
            json={**person_body(), "displayName": "Lisa Marie"},
            headers=if_match(paar["token_a"], person["version"]),
        )
        assert updated.status_code == 200

        response = delete_person(client, paar, person, "preserve")
        assert response.status_code == 409
        assert response.json()["code"] == "VERSION_CONFLICT"

    def test_anonym_bleibt_401(self, client, paar) -> None:  # type: ignore[no-untyped-def]
        person = create_person(client, paar)
        response = client.delete(
            f"{persons_path(paar['space'].id)}/{person['id']}?deletePolicy=preserve",
            headers={"If-Match": f'"{person["version"]}"'},
        )
        assert response.status_code == 401
        assert response.json()["code"] == "AUTHENTICATION_REQUIRED"


class TestDeletePrivacy:
    @pytest.mark.parametrize("partner_private_count", [0, 1, 3])
    def test_antwort_verraet_keine_privaten_partnertermine(
        self, client, paar, partner_private_count: int
    ) -> None:  # type: ignore[no-untyped-def]
        person = create_person(client, paar)
        for index in range(partner_private_count):
            create_date(
                client,
                paar,
                token_key="token_b",
                label=f"Partner privat {index}",
                visibility="PRIVATE",
                related_person_id=person["id"],
            )

        response = delete_person(client, paar, person, "preserve")
        assert response.status_code == 204
        assert response.content == b""
        assert "content-type" not in response.headers
        assert not any("count" in name.lower() for name in response.headers)
        assert not any("exists" in name.lower() for name in response.headers)
