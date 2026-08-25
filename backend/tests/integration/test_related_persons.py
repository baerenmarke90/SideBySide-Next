"""HTTP-Matrix fuer RelatedPerson und ImportantDate."""

from __future__ import annotations

from datetime import date
from typing import Any
from uuid import UUID, uuid4

import pytest
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from sidebyside.relationship import service as relationship_service
from tests.conftest import auth, make_account, make_space, requires_database, sign_in

pytestmark = [pytest.mark.integration, requires_database]


def persons_path(space_id: object) -> str:
    return f"/api/v1/spaces/{space_id}/related-persons"


def dates_path(space_id: object) -> str:
    return f"/api/v1/spaces/{space_id}/important-dates"


def person_body(
    *,
    display_name: str = "Lisa",
    relationship: str = "CHILD",
    birthday: str | None = "2016-02-29",
    birthday_year_known: bool = True,
    visibility: str = "SHARED",
) -> dict[str, Any]:
    return {
        "displayName": display_name,
        "relationship": relationship,
        "birthday": birthday,
        "birthdayYearKnown": birthday_year_known,
        "visibility": visibility,
    }


def date_body(
    *,
    label: str = "Lisas Geburtstag",
    date_type: str = "BIRTHDAY",
    day: str = "2016-02-29",
    repeats: str = "ANNUALLY",
    visibility: str = "SHARED",
    related_person_id: object | None = None,
) -> dict[str, Any]:
    body: dict[str, Any] = {
        "label": label,
        "type": date_type,
        "date": day,
        "repeats": repeats,
        "visibility": visibility,
    }
    if related_person_id is not None:
        body["relatedPersonId"] = str(related_person_id)
    return body


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


def create_person(client, paar, *, token_key: str = "token_a", **overrides):  # type: ignore[no-untyped-def]
    return client.post(
        persons_path(paar["space"].id),
        json=person_body(**overrides),
        headers=auth(paar[token_key]),
    )


def create_date(client, paar, *, token_key: str = "token_a", **overrides):  # type: ignore[no-untyped-def]
    return client.post(
        dates_path(paar["space"].id),
        json=date_body(**overrides),
        headers=auth(paar[token_key]),
    )


def if_match(token: str, version: int) -> dict[str, str]:
    return {**auth(token), "If-Match": f'"{version}"'}


class TestRelatedPerson:
    def test_anlegen_liefert_uuidv7_und_etag(self, client, paar) -> None:  # type: ignore[no-untyped-def]
        response = create_person(client, paar)
        assert response.status_code == 201
        body = response.json()
        assert UUID(body["id"]).version == 7
        assert body["displayName"] == "Lisa"
        assert body["relationship"] == "CHILD"
        assert body["visibility"] == "SHARED"
        assert response.headers["ETag"] == '"1"'

    def test_partner_sieht_geteilte_person(self, client, paar) -> None:  # type: ignore[no-untyped-def]
        person = create_person(client, paar).json()
        response = client.get(
            f"{persons_path(paar['space'].id)}/{person['id']}",
            headers=auth(paar["token_b"]),
        )
        assert response.status_code == 200
        assert response.json()["displayName"] == "Lisa"

    def test_private_person_bleibt_fuer_den_partner_unsichtbar(self, client, paar) -> None:  # type: ignore[no-untyped-def]
        person = create_person(client, paar, visibility="PRIVATE").json()

        detail = client.get(
            f"{persons_path(paar['space'].id)}/{person['id']}",
            headers=auth(paar["token_b"]),
        )
        assert detail.status_code == 404
        assert detail.json()["code"] == "RELATED_PERSON_NOT_FOUND"

        liste = client.get(persons_path(paar["space"].id), headers=auth(paar["token_b"]))
        assert liste.status_code == 200
        assert liste.json() == []

    def test_partner_darf_geteilte_person_nicht_aendern(self, client, paar) -> None:  # type: ignore[no-untyped-def]
        person = create_person(client, paar).json()
        response = client.put(
            f"{persons_path(paar['space'].id)}/{person['id']}",
            json=person_body(display_name="Umbenannt"),
            headers=if_match(paar["token_b"], person["version"]),
        )
        assert response.status_code == 403
        assert response.json()["code"] == "NOT_RESOURCE_OWNER"

    def test_veralteter_stand_wird_abgelehnt(self, client, paar) -> None:  # type: ignore[no-untyped-def]
        person = create_person(client, paar).json()
        erste = client.put(
            f"{persons_path(paar['space'].id)}/{person['id']}",
            json=person_body(display_name="Lisa Marie"),
            headers=if_match(paar["token_a"], person["version"]),
        )
        assert erste.status_code == 200

        zweite = client.put(
            f"{persons_path(paar['space'].id)}/{person['id']}",
            json=person_body(display_name="Noch mal anders"),
            headers=if_match(paar["token_a"], person["version"]),
        )
        assert zweite.status_code == 409
        assert zweite.json()["code"] == "VERSION_CONFLICT"

    def test_fremder_space_bleibt_404(self, client, paar) -> None:  # type: ignore[no-untyped-def]
        person = create_person(client, paar).json()
        response = client.get(
            f"{persons_path(paar['space'].id)}/{person['id']}",
            headers=auth(paar["token_fremd"]),
        )
        assert response.status_code == 404
        assert response.json()["code"] == "SPACE_NOT_FOUND"

    def test_anonym_bleibt_401(self, client, paar) -> None:  # type: ignore[no-untyped-def]
        response = client.get(persons_path(paar["space"].id))
        assert response.status_code == 401
        assert response.json()["code"] == "AUTHENTICATION_REQUIRED"

    def test_unbekannte_beziehung_wird_abgelehnt(self, client, paar) -> None:  # type: ignore[no-untyped-def]
        response = create_person(client, paar, relationship="COLLEAGUE")
        assert response.status_code == 422

    def test_leerer_anzeigename_wird_abgelehnt(self, client, paar) -> None:  # type: ignore[no-untyped-def]
        response = create_person(client, paar, display_name="   ")
        assert response.status_code == 422


class TestGeburtstagOhneJahr:
    def test_unbekanntes_jahr_wird_normalisiert(self, client, paar) -> None:  # type: ignore[no-untyped-def]
        response = create_person(
            client,
            paar,
            birthday="2016-02-29",
            birthday_year_known=False,
        )
        assert response.status_code == 201
        body = response.json()
        assert body["birthday"] == "1904-02-29"
        assert body["birthdayYearKnown"] is False

    def test_bekanntes_jahr_bleibt_stehen(self, client, paar) -> None:  # type: ignore[no-untyped-def]
        body = create_person(client, paar, birthday="2016-02-29").json()
        assert body["birthday"] == "2016-02-29"
        assert body["birthdayYearKnown"] is True

    def test_bekanntes_jahr_ohne_datum_ist_ein_widerspruch(self, client, paar) -> None:  # type: ignore[no-untyped-def]
        response = create_person(client, paar, birthday=None, birthday_year_known=True)
        assert response.status_code == 422
        assert response.json()["code"] == "RELATED_PERSON_BIRTHDAY_REQUIRED"

    def test_kein_geburtstag_ist_erlaubt(self, client, paar) -> None:  # type: ignore[no-untyped-def]
        response = create_person(client, paar, birthday=None, birthday_year_known=False)
        assert response.status_code == 201
        assert response.json()["birthday"] is None


class TestImportantDate:
    def test_termin_ohne_person_ist_erlaubt(self, client, paar) -> None:  # type: ignore[no-untyped-def]
        response = create_date(
            client,
            paar,
            label="Unser Jahrestag",
            date_type="ANNIVERSARY",
            day="2020-06-13",
        )
        assert response.status_code == 201
        assert response.json()["relatedPersonId"] is None

    def test_termin_haengt_an_der_person(self, client, paar) -> None:  # type: ignore[no-untyped-def]
        person = create_person(client, paar).json()
        response = create_date(client, paar, related_person_id=person["id"])
        assert response.status_code == 201
        assert response.json()["relatedPersonId"] == person["id"]

        gefiltert = client.get(
            f"{dates_path(paar['space'].id)}?relatedPersonId={person['id']}",
            headers=auth(paar["token_b"]),
        )
        assert gefiltert.status_code == 200
        assert [eintrag["id"] for eintrag in gefiltert.json()] == [response.json()["id"]]

    def test_person_aus_fremdem_space_bleibt_404(self, client, paar, session) -> None:  # type: ignore[no-untyped-def]
        fremde_person = client.post(
            persons_path(paar["fremder_space"].id),
            json=person_body(display_name="Fremdes Kind"),
            headers=auth(paar["token_fremd"]),
        ).json()

        response = create_date(client, paar, related_person_id=fremde_person["id"])
        assert response.status_code == 404
        assert response.json()["code"] == "RELATED_PERSON_NOT_FOUND"

    def test_unbekannte_person_bleibt_404(self, client, paar) -> None:  # type: ignore[no-untyped-def]
        response = create_date(client, paar, related_person_id=uuid4())
        assert response.status_code == 404
        assert response.json()["code"] == "RELATED_PERSON_NOT_FOUND"

    def test_privater_termin_bleibt_fuer_den_partner_unsichtbar(self, client, paar) -> None:  # type: ignore[no-untyped-def]
        angelegt = create_date(client, paar, visibility="PRIVATE").json()

        detail = client.get(
            f"{dates_path(paar['space'].id)}/{angelegt['id']}",
            headers=auth(paar["token_b"]),
        )
        assert detail.status_code == 404
        assert detail.json()["code"] == "IMPORTANT_DATE_NOT_FOUND"

        liste = client.get(dates_path(paar["space"].id), headers=auth(paar["token_b"]))
        assert liste.json() == []

    def test_filter_auf_die_private_person_des_partners_bleibt_404(self, client, paar) -> None:  # type: ignore[no-untyped-def]
        """Auch eine Trefferzahl von null waere eine Auskunft ueber die Person."""
        person = create_person(client, paar, visibility="PRIVATE").json()
        response = client.get(
            f"{dates_path(paar['space'].id)}?relatedPersonId={person['id']}",
            headers=auth(paar["token_b"]),
        )
        assert response.status_code == 404
        assert response.json()["code"] == "RELATED_PERSON_NOT_FOUND"

    def test_unbekannter_typ_wird_abgelehnt(self, client, paar) -> None:  # type: ignore[no-untyped-def]
        assert create_date(client, paar, date_type="FUNERAL").status_code == 422

    def test_unbekannte_wiederholung_wird_abgelehnt(self, client, paar) -> None:  # type: ignore[no-untyped-def]
        assert create_date(client, paar, repeats="WEEKLY").status_code == 422


class TestTerminNieOffenerAlsSeinePerson:
    def test_geteilter_termin_an_privater_person_wird_abgelehnt(self, client, paar) -> None:  # type: ignore[no-untyped-def]
        person = create_person(client, paar, visibility="PRIVATE").json()
        response = create_date(
            client,
            paar,
            related_person_id=person["id"],
            visibility="SHARED",
        )
        assert response.status_code == 422
        assert response.json()["code"] == "IMPORTANT_DATE_MORE_OPEN_THAN_PERSON"

    def test_privater_termin_an_privater_person_ist_erlaubt(self, client, paar) -> None:  # type: ignore[no-untyped-def]
        person = create_person(client, paar, visibility="PRIVATE").json()
        response = create_date(
            client,
            paar,
            related_person_id=person["id"],
            visibility="PRIVATE",
        )
        assert response.status_code == 201

    def test_oeffnen_eines_termins_wird_abgelehnt(self, client, paar) -> None:  # type: ignore[no-untyped-def]
        person = create_person(client, paar, visibility="PRIVATE").json()
        termin = create_date(
            client,
            paar,
            related_person_id=person["id"],
            visibility="PRIVATE",
        ).json()

        response = client.put(
            f"{dates_path(paar['space'].id)}/{termin['id']}",
            json=date_body(related_person_id=person["id"], visibility="SHARED"),
            headers=if_match(paar["token_a"], termin["version"]),
        )
        assert response.status_code == 422
        assert response.json()["code"] == "IMPORTANT_DATE_MORE_OPEN_THAN_PERSON"

    def test_person_mit_geteilten_terminen_wird_nicht_still_privat(self, client, paar) -> None:  # type: ignore[no-untyped-def]
        person = create_person(client, paar).json()
        create_date(client, paar, related_person_id=person["id"], visibility="SHARED")

        response = client.put(
            f"{persons_path(paar['space'].id)}/{person['id']}",
            json=person_body(visibility="PRIVATE"),
            headers=if_match(paar["token_a"], person["version"]),
        )
        assert response.status_code == 409
        assert response.json()["code"] == "RELATED_PERSON_HAS_SHARED_DATES"

    def test_privater_termin_des_partners_haelt_die_verschaerfung_nicht_auf(  # type: ignore[no-untyped-def]
        self, client, paar
    ) -> None:
        person = create_person(client, paar).json()
        create_date(
            client,
            paar,
            token_key="token_b",
            related_person_id=person["id"],
            visibility="PRIVATE",
        )

        response = client.put(
            f"{persons_path(paar['space'].id)}/{person['id']}",
            json=person_body(visibility="PRIVATE"),
            headers=if_match(paar["token_a"], person["version"]),
        )
        assert response.status_code == 200
        assert response.json()["visibility"] == "PRIVATE"

    def test_datenbank_haelt_die_regel_auch_ohne_die_fachlogik(self, session, paar) -> None:  # type: ignore[no-untyped-def]
        """Die Regel ist ein Schemafakt, nicht nur eine Servicepruefung."""
        from sidebyside.core.ids import new_id
        from sidebyside.people.models import RelatedPerson, RelatedPersonPayload

        person = RelatedPerson(
            space_id=paar["space"].id,
            owner_id=paar["anna"].id,
            privacy_class="OWNER_ONLY",
            relationship="CHILD",
            birthday=None,
            birthday_year_known=False,
            payload=RelatedPersonPayload(display_name="Lisa"),
        )
        session.add(person)
        session.flush()

        with pytest.raises(IntegrityError) as fehler:
            session.execute(
                text(
                    "INSERT INTO important_dates (id, space_id, owner_id, privacy_class, "
                    "related_person_id, related_person_privacy_class, type, date, repeats, "
                    "crypto_version, payload, version) "
                    "VALUES (:id, :space_id, :owner_id, 'SPACE_SHARED', :person_id, "
                    "'OWNER_ONLY', 'BIRTHDAY', :day, 'ANNUALLY', 0, '{\"label\": \"x\"}', 1)"
                ),
                {
                    "id": new_id(),
                    "space_id": paar["space"].id,
                    "owner_id": paar["anna"].id,
                    "person_id": person.id,
                    "day": date(2016, 2, 29),
                },
            )
        assert "never_more_open_than_its_person" in str(fehler.value)
        session.rollback()

    def test_geloeschte_person_nimmt_ihre_termine_mit(self, client, paar) -> None:  # type: ignore[no-untyped-def]
        person = create_person(client, paar).json()
        eigener = create_date(client, paar, related_person_id=person["id"]).json()
        fremder = create_date(
            client,
            paar,
            token_key="token_b",
            related_person_id=person["id"],
            visibility="PRIVATE",
            label="Meine Notiz",
        ).json()

        geloescht = client.delete(
            f"{persons_path(paar['space'].id)}/{person['id']}?deletePolicy=cascade",
            headers=if_match(paar["token_a"], person["version"]),
        )
        assert geloescht.status_code == 204

        assert (
            client.get(
                f"{dates_path(paar['space'].id)}/{eigener['id']}",
                headers=auth(paar["token_a"]),
            ).status_code
            == 404
        )
        assert (
            client.get(
                f"{dates_path(paar['space'].id)}/{fremder['id']}",
                headers=auth(paar["token_b"]),
            ).status_code
            == 404
        )
