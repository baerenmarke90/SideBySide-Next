"""PostgreSQL/HTTP acceptance tests for the M3-S3 place slice.

The Schwerpunkt is on drei Zusicherungen from M3-D06 until M3-D08.

Coordinates are a Couple, liegen in ihren Grenzen and are on sechs
Nachkommastellen persistiert. It exists no Deduplizierung: zwei Places with
demselben Namen remain zwei Places. And a Place-Delete entfernt exactly the
Ort; Plans, the on it zeigen, verlieren the Zuordnung and remain
bestehen.
"""

from __future__ import annotations

from decimal import Decimal
from typing import Any
from uuid import UUID, uuid4

import pytest
from sqlalchemy import select, text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from sidebyside.outbox.models import OutboxEvent
from sidebyside.places.models import Place
from sidebyside.plans.models import Plan
from sidebyside.relationship import service as relationship_service
from tests.conftest import auth, make_account, make_space, requires_database, sign_in

pytestmark = [pytest.mark.integration, requires_database]

# Intentionally echte Werte in Testdaten; the Punkt mehrerer Tests is, that
# exactly it nirgends auftauchen, where it not hingehoeren.
BERLIN_LAT = 52.520008
BERLIN_LON = 13.404954
SECRET_ADDRESS = "Eine Adresse, die nicht in Ereignisse gehoert."


def path(space_id: object) -> str:
    return f"/api/v1/spaces/{space_id}/places"


def body(
    *,
    name: str = "Unser Cafe",
    description: str | None = "Ecktisch am Fenster.",
    address: str | None = "Beispielstrasse 1",
    latitude: float | None = BERLIN_LAT,
    longitude: float | None = BERLIN_LON,
) -> dict[str, Any]:
    """A create request body.

    `description` and `address` are weggelassen instead of on `null`
    gesetzt; during Create unterscheidet the Contract the both not and
    rejects an explicit `null` (as with Memory and Milestone).
    The Coordinates are the bewusste Gegenfall: it duerfen ausdruecklich
    `null` be, weil it a Couple bilden and a Client it oft as Couple
    fuehrt.
    """
    gesendet: dict[str, Any] = {"name": name, "latitude": latitude, "longitude": longitude}
    if description is not None:
        gesendet["description"] = description
    if address is not None:
        gesendet["address"] = address
    return gesendet


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


def create_place(  # type: ignore[no-untyped-def]
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
        created = create_place(client, couple)
        assert created.status_code == 201
        o = created.json()
        assert UUID(o["id"]).version == 7
        assert o["name"] == "Unser Cafe"
        assert o["description"] == "Ecktisch am Fenster."
        assert o["address"] == "Beispielstrasse 1"
        assert o["latitude"] == BERLIN_LAT
        assert o["longitude"] == BERLIN_LON
        assert o["createdBy"] == str(couple["anna"].id)
        assert o["capabilities"] == {"canEdit": True, "canDelete": True, "canComment": False}
        assert "privacyClass" not in o
        assert created.headers["ETag"] == '"1"'

        updated = client.patch(
            f"{path(couple['space'].id)}/{o['id']}",
            json={"name": "  Unser Stammcafe  ", "description": None},
            headers=if_match(couple["token_a"], 1),
        )
        assert updated.status_code == 200
        assert updated.json()["name"] == "Unser Stammcafe"
        assert updated.json()["description"] is None
        # Unberuehrte Felder remain stehen.
        assert updated.json()["latitude"] == BERLIN_LAT

        deleted = client.delete(
            f"{path(couple['space'].id)}/{o['id']}", headers=if_match(couple["token_a"], 2)
        )
        assert deleted.status_code == 204
        danach = client.get(
            f"{path(couple['space'].id)}/{o['id']}", headers=auth(couple["token_a"])
        )
        assert danach.status_code == 404
        assert danach.json()["code"] == "PLACE_NOT_FOUND"

    def test_the_partner_may_change_and_createdby_remains(  # type: ignore[no-untyped-def]
        self,
        client,
        couple,
    ) -> None:
        "M3-D01 applies to Place, Wish, and Plan alike."
        o = create_place(client, couple).json()
        updated = client.patch(
            f"{path(couple['space'].id)}/{o['id']}",
            json={"name": "Von Ben umbenannt"},
            headers=if_match(couple["token_b"], 1),
        )
        assert updated.status_code == 200
        assert updated.json()["createdBy"] == str(couple["anna"].id)

    def test_empty_name_is_rejected(  # type: ignore[no-untyped-def]
        self,
        client,
        couple,
    ) -> None:
        assert create_place(client, couple, name="   ").status_code == 422

    def test_stale_version_is_rejected(  # type: ignore[no-untyped-def]
        self,
        client,
        couple,
    ) -> None:
        o = create_place(client, couple).json()
        client.patch(
            f"{path(couple['space'].id)}/{o['id']}",
            json={"name": "Erste Aenderung"},
            headers=if_match(couple["token_a"], 1),
        )
        second = client.patch(
            f"{path(couple['space'].id)}/{o['id']}",
            json={"name": "Zweite Aenderung"},
            headers=if_match(couple["token_a"], 1),
        )
        assert second.status_code == 409
        assert second.json()["code"] == "RESOURCE_VERSION_CONFLICT"

    def test_the_list_shows_neueste_first(  # type: ignore[no-untyped-def]
        self,
        client,
        couple,
    ) -> None:
        erster = create_place(client, couple, name="Erster").json()
        zweiter = create_place(client, couple, name="Zweiter").json()
        seite = client.get(path(couple["space"].id), headers=auth(couple["token_a"])).json()
        assert [e["id"] for e in seite["items"]] == [zweiter["id"], erster["id"]]

    def test_the_cursor_applies_only_in_its_space(  # type: ignore[no-untyped-def]
        self,
        client,
        couple,
    ) -> None:
        create_place(client, couple, name="Erster")
        create_place(client, couple, name="Zweiter")
        seite = client.get(
            f"{path(couple['space'].id)}?limit=1", headers=auth(couple["token_a"])
        ).json()
        response = client.get(
            f"{path(couple['fremder_space'].id)}?limit=1&cursor={seite['nextCursor']}",
            headers=auth(couple["token_b"]),
        )
        assert response.status_code == 400
        assert response.json()["code"] == "INVALID_CURSOR"


class TestKoordinaten:
    "M3-D06: both or no, in ihren Grenzen, sechs Nachkommastellen."

    def test_a_place_without_coordinates_is_valid(  # type: ignore[no-untyped-def]
        self,
        client,
        couple,
    ) -> None:
        "Many places belonging to a couple are only a name and nothing else."
        response = create_place(
            client, couple, latitude=None, longitude=None, address=None, description=None
        )
        assert response.status_code == 201
        assert response.json()["latitude"] is None
        assert response.json()["longitude"] is None
        assert response.json()["address"] is None

    def test_a_explicit_null_couple_is_erlaubt(  # type: ignore[no-untyped-def]
        self,
        client,
        couple,
    ) -> None:
        """A client that treats the coordinates as a pair sends both values.

        For `description` and `address` applies the not: there weist the
        The create contract rejects an explicit `null`, as with Memory and
        Milestone therefore.
        """
        response = client.post(
            path(couple["space"].id),
            json={"name": "Nur ein Name", "latitude": None, "longitude": None},
            headers=auth(couple["token_a"]),
        )
        assert response.status_code == 201

        with_null_text = client.post(
            path(couple["space"].id),
            json={"name": "Nur ein Name", "address": None},
            headers=auth(couple["token_a"]),
        )
        assert with_null_text.status_code == 422

    def test_a_address_without_coordinates_is_valid(  # type: ignore[no-untyped-def]
        self,
        client,
        couple,
    ) -> None:
        response = create_place(client, couple, latitude=None, longitude=None)
        assert response.status_code == 201
        assert response.json()["address"] == "Beispielstrasse 1"

    def test_coordinates_without_address_are_valid(  # type: ignore[no-untyped-def]
        self,
        client,
        couple,
    ) -> None:
        response = create_place(client, couple, address=None)
        assert response.status_code == 201
        assert response.json()["latitude"] == BERLIN_LAT

    @pytest.mark.parametrize("fehlend", ["latitude", "longitude"])
    def test_a_halbe_coordinate_is_rejected(  # type: ignore[no-untyped-def]
        self,
        client,
        couple,
        missing: str,
    ) -> None:
        response = create_place(client, couple, **{missing: None})
        assert response.status_code == 422
        assert response.json()["code"] == "PLACE_COORDINATE_PAIR_REQUIRED"

    @pytest.mark.parametrize(
        ("latitude", "longitude", "code"),
        [
            (90.000001, 0.0, "PLACE_LATITUDE_INVALID"),
            (-90.000001, 0.0, "PLACE_LATITUDE_INVALID"),
            (0.0, 180.000001, "PLACE_LONGITUDE_INVALID"),
            (0.0, -180.000001, "PLACE_LONGITUDE_INVALID"),
        ],
    )
    def test_values_outside_the_grenzen(  # type: ignore[no-untyped-def]
        self,
        client,
        couple,
        latitude,
        longitude,
        code,
    ) -> None:
        response = create_place(client, couple, latitude=latitude, longitude=longitude)
        assert response.status_code == 422
        assert response.json()["code"] == code

    @pytest.mark.parametrize(
        ("latitude", "longitude"),
        [(90.0, 180.0), (-90.0, -180.0), (0.0, 0.0)],
    )
    def test_the_boundary_values_selbst_are_valid(  # type: ignore[no-untyped-def]
        self,
        client,
        couple,
        latitude,
        longitude,
    ) -> None:
        response = create_place(client, couple, latitude=latitude, longitude=longitude)
        assert response.status_code == 201
        assert response.json()["latitude"] == latitude
        assert response.json()["longitude"] == longitude

    def test_more_stellen_werden_on_sechs_gerundet(  # type: ignore[no-untyped-def]
        self,
        client,
        couple,
        session,
    ) -> None:
        """A Sensor liefert more; stored are sechs Stellen.

        Abweisen would be here wrong; the Client has nothing wrong gemacht.
        """
        response = create_place(client, couple, latitude=52.5200081234, longitude=13.4049544321)
        assert response.status_code == 201
        assert response.json()["latitude"] == 52.520008
        assert response.json()["longitude"] == 13.404954

        row = session.get(Place, UUID(response.json()["id"]))
        assert row.latitude == Decimal("52.520008")
        assert row.longitude == Decimal("13.404954")

    def test_coordinates_koennen_nachgetragen_werden(  # type: ignore[no-untyped-def]
        self,
        client,
        couple,
    ) -> None:
        o = create_place(client, couple, latitude=None, longitude=None).json()
        response = client.patch(
            f"{path(couple['space'].id)}/{o['id']}",
            json={"latitude": BERLIN_LAT, "longitude": BERLIN_LON},
            headers=if_match(couple["token_a"], 1),
        )
        assert response.status_code == 200
        assert response.json()["latitude"] == BERLIN_LAT

    def test_coordinates_can_be_removed_again(  # type: ignore[no-untyped-def]
        self,
        client,
        couple,
    ) -> None:
        o = create_place(client, couple).json()
        response = client.patch(
            f"{path(couple['space'].id)}/{o['id']}",
            json={"latitude": None, "longitude": None},
            headers=if_match(couple["token_a"], 1),
        )
        assert response.status_code == 200
        assert response.json()["latitude"] is None
        assert response.json()["longitude"] is None

    def test_a_patch_on_only_a_coordinate_is_rejected(  # type: ignore[no-untyped-def]
        self,
        client,
        couple,
    ) -> None:
        "Otherwise PATCH would provide a path to a partial coordinate."
        o = create_place(client, couple).json()
        response = client.patch(
            f"{path(couple['space'].id)}/{o['id']}",
            json={"latitude": None},
            headers=if_match(couple["token_a"], 1),
        )
        assert response.status_code == 422
        assert response.json()["code"] == "PLACE_COORDINATE_PAIR_REQUIRED"

    @pytest.mark.parametrize(
        "sql",
        [
            "UPDATE places SET latitude = 10.0, longitude = NULL WHERE id = :id",
            "UPDATE places SET latitude = 91.0 WHERE id = :id",
            "UPDATE places SET longitude = 181.0 WHERE id = :id",
        ],
    )
    def test_the_database_keeps_the_invariants_auch_without_the_dienst(
        self, client, couple, session, sql: str
    ) -> None:  # type: ignore[no-untyped-def]
        o = create_place(client, couple).json()
        with pytest.raises(IntegrityError), session.begin_nested():
            session.execute(text(sql), {"id": o["id"]})


class TestKeineDeduplizierung:
    "M3-D07: zwei same Places are zwei Places."

    def test_derselbe_name_and_same_coordinates_create_zwei_places(  # type: ignore[no-untyped-def]
        self,
        client,
        couple,
    ) -> None:
        erster = create_place(client, couple).json()
        zweiter = create_place(client, couple).json()
        assert erster["id"] != zweiter["id"]

        seite = client.get(path(couple["space"].id), headers=auth(couple["token_a"])).json()
        assert len(seite["items"]) == 2


class TestPlanZuordnung:
    "M3-D08/D31: `Plan.placeId` is the einzige Plan/Place-Wahrheit."

    def _plan(self, client, couple, **felder):  # type: ignore[no-untyped-def]
        return client.post(
            f"/api/v1/spaces/{couple['space'].id}/plans",
            json={"title": "Abendessen", **felder},
            headers=auth(couple["token_a"]),
        )

    def test_a_plan_can_directly_with_place_entstehen(  # type: ignore[no-untyped-def]
        self,
        client,
        couple,
    ) -> None:
        o = create_place(client, couple).json()
        plan = self._plan(client, couple, placeId=o["id"])
        assert plan.status_code == 201
        assert plan.json()["placeId"] == o["id"]

    def test_the_place_can_later_gesetzt_and_cleared_werden(  # type: ignore[no-untyped-def]
        self,
        client,
        couple,
    ) -> None:
        o = create_place(client, couple).json()
        plan = self._plan(client, couple).json()
        assert plan["placeId"] is None

        gesetzt = client.patch(
            f"/api/v1/spaces/{couple['space'].id}/plans/{plan['id']}",
            json={"placeId": o["id"]},
            headers=if_match(couple["token_a"], 1),
        )
        assert gesetzt.status_code == 200
        assert gesetzt.json()["placeId"] == o["id"]

        cleared = client.patch(
            f"/api/v1/spaces/{couple['space'].id}/plans/{plan['id']}",
            json={"placeId": None},
            headers=if_match(couple["token_a"], 2),
        )
        assert cleared.status_code == 200
        assert cleared.json()["placeId"] is None

    def test_place_from_foreign_space_remains_invisible(  # type: ignore[no-untyped-def]
        self,
        client,
        couple,
        session,
    ) -> None:
        foreign_place = client.post(
            path(couple["fremder_space"].id), json=body(), headers=auth(couple["token_b"])
        ).json()

        response = self._plan(client, couple, placeId=foreign_place["id"])
        assert response.status_code == 404
        assert response.json()["code"] == "PLACE_NOT_FOUND"
        assert list(session.execute(select(Plan)).scalars()) == []

    def test_a_unknown_and_a_foreign_id_klingen_gleich(  # type: ignore[no-untyped-def]
        self,
        client,
        couple,
    ) -> None:
        foreign_place = client.post(
            path(couple["fremder_space"].id), json=body(), headers=auth(couple["token_b"])
        ).json()
        unknown = self._plan(client, couple, placeId=str(uuid4()))
        foreign = self._plan(client, couple, placeId=foreign_place["id"])
        assert unknown.status_code == foreign.status_code == 404
        assert unknown.json() == foreign.json()

    def test_a_konvertierung_may_the_place_gleich_mitgeben(  # type: ignore[no-untyped-def]
        self,
        client,
        couple,
    ) -> None:
        o = create_place(client, couple).json()
        wish = client.post(
            f"/api/v1/spaces/{couple['space'].id}/wishes",
            json={"title": "Essen gehen"},
            headers=auth(couple["token_a"]),
        ).json()

        response = client.post(
            f"/api/v1/spaces/{couple['space'].id}/wishes/{wish['id']}/plan",
            json={"placeId": o["id"]},
            headers=if_match(couple["token_a"], 1),
        )
        assert response.status_code == 201
        assert response.json()["plan"]["placeId"] == o["id"]


class TestDelete:
    "M3-D06, Abschnitt 9: the Ort works, the Originale remain."

    def test_the_plan_survives_its_place_and_gets_a_new_version(
        self, client, couple, session
    ) -> None:  # type: ignore[no-untyped-def]
        o = create_place(client, couple).json()
        plan = client.post(
            f"/api/v1/spaces/{couple['space'].id}/plans",
            json={"title": "Abendessen", "placeId": o["id"]},
            headers=auth(couple["token_a"]),
        ).json()
        assert plan["version"] == 1

        removed = client.delete(
            f"{path(couple['space'].id)}/{o['id']}", headers=if_match(couple["token_a"], 1)
        )
        assert removed.status_code == 204

        danach = client.get(
            f"/api/v1/spaces/{couple['space'].id}/plans/{plan['id']}",
            headers=auth(couple["token_a"]),
        ).json()
        assert danach["placeId"] is None
        assert danach["title"] == "Abendessen"
        # The Plan has itself changed; and sagt the therefore.
        assert danach["version"] == 2

    def test_a_client_with_altem_stand_gets_a_konflikt(  # type: ignore[no-untyped-def]
        self,
        client,
        couple,
    ) -> None:
        """The eigentliche Reason for the neue Version.

        A stilles `ON DELETE SET NULL` would the Ort under the Partner
        wegziehen, without that be naechster Schreibzugriff each auffiele.
        """
        o = create_place(client, couple).json()
        plan = client.post(
            f"/api/v1/spaces/{couple['space'].id}/plans",
            json={"title": "Abendessen", "placeId": o["id"]},
            headers=auth(couple["token_a"]),
        ).json()

        client.delete(
            f"{path(couple['space'].id)}/{o['id']}", headers=if_match(couple["token_a"], 1)
        )

        response = client.patch(
            f"/api/v1/spaces/{couple['space'].id}/plans/{plan['id']}",
            json={"title": "Mit altem Stand"},
            headers=if_match(couple["token_b"], 1),
        )
        assert response.status_code == 409
        assert response.json()["code"] == "RESOURCE_VERSION_CONFLICT"

    def test_mehrere_plans_werden_all_cleared(  # type: ignore[no-untyped-def]
        self,
        client,
        couple,
        session,
    ) -> None:
        o = create_place(client, couple).json()
        for title in ("Erster", "Zweiter", "Dritter"):
            client.post(
                f"/api/v1/spaces/{couple['space'].id}/plans",
                json={"title": title, "placeId": o["id"]},
                headers=auth(couple["token_a"]),
            )

        client.delete(
            f"{path(couple['space'].id)}/{o['id']}", headers=if_match(couple["token_a"], 1)
        )

        session.expire_all()
        plans = list(session.execute(select(Plan)).scalars())
        assert len(plans) == 3
        assert all(p.place_id is None for p in plans)

    def test_a_plan_without_place_remains_unberuehrt(  # type: ignore[no-untyped-def]
        self,
        client,
        couple,
    ) -> None:
        o = create_place(client, couple).json()
        without_place = client.post(
            f"/api/v1/spaces/{couple['space'].id}/plans",
            json={"title": "Ohne Ort"},
            headers=auth(couple["token_a"]),
        ).json()

        client.delete(
            f"{path(couple['space'].id)}/{o['id']}", headers=if_match(couple["token_a"], 1)
        )

        danach = client.get(
            f"/api/v1/spaces/{couple['space'].id}/plans/{without_place['id']}",
            headers=auth(couple["token_a"]),
        ).json()
        assert danach["version"] == 1

    def test_the_database_allows_no_plan_on_a_deleted_place_zeigen(
        self, client, couple, session
    ) -> None:  # type: ignore[no-untyped-def]
        "The foreign key is the boundary if the service ever fails."
        o = create_place(client, couple).json()
        client.post(
            f"/api/v1/spaces/{couple['space'].id}/plans",
            json={"title": "Abendessen", "placeId": o["id"]},
            headers=auth(couple["token_a"]),
        )

        session.execute(text("DELETE FROM places WHERE id = :id"), {"id": o["id"]})
        session.flush()
        session.expire_all()

        plan = session.execute(select(Plan)).scalar_one()
        assert plan.place_id is None
        assert plan.space_id == couple["space"].id


class TestMandant:
    def test_a_foreign_sees_the_space_not(  # type: ignore[no-untyped-def]
        self,
        client,
        couple,
    ) -> None:
        create_place(client, couple)
        response = client.get(path(couple["space"].id), headers=auth(couple["token_fremd"]))
        assert response.status_code == 404
        assert response.json()["code"] == "SPACE_NOT_FOUND"

    def test_id_from_other_space_remains_invisible(  # type: ignore[no-untyped-def]
        self,
        client,
        couple,
    ) -> None:
        o = create_place(client, couple).json()
        gelesen = client.get(
            f"{path(couple['fremder_space'].id)}/{o['id']}", headers=auth(couple["token_b"])
        )
        assert gelesen.status_code == 404
        assert gelesen.json()["code"] == "PLACE_NOT_FOUND"

    def test_a_foreign_write_attempt_changes_nothing(  # type: ignore[no-untyped-def]
        self,
        client,
        couple,
        session,
    ) -> None:
        o = create_place(client, couple).json()
        response = client.patch(
            f"{path(couple['fremder_space'].id)}/{o['id']}",
            json={"name": "Uebernommen"},
            headers=if_match(couple["token_b"], 1),
        )
        assert response.status_code == 404

        session.expire_all()
        assert session.get(Place, UUID(o["id"])).payload.name == "Unser Cafe"


class TestPrivacy:
    def test_events_enthalten_weder_address_noch_coordinates(  # type: ignore[no-untyped-def]
        self,
        client,
        couple,
        session,
    ) -> None:
        o = create_place(client, couple, address=SECRET_ADDRESS).json()
        client.patch(
            f"{path(couple['space'].id)}/{o['id']}",
            json={"name": "Neu benannt"},
            headers=if_match(couple["token_a"], 1),
        )
        client.delete(
            f"{path(couple['space'].id)}/{o['id']}", headers=if_match(couple["token_a"], 2)
        )

        rows = list(
            session.execute(
                select(OutboxEvent).where(OutboxEvent.subject_type == "place")
            ).scalars()
        )
        assert [z.event_type for z in rows] == [
            "PLACE_CREATED",
            "PLACE_UPDATED",
            "PLACE_DELETED",
        ]
        for row in rows:
            raw = repr(row.payload.model_dump())
            assert SECRET_ADDRESS not in raw
            assert "52.520008" not in raw
            assert "13.404954" not in raw
            assert row.resource_version is not None

    def test_a_error_response_names_no_coordinate(  # type: ignore[no-untyped-def]
        self,
        client,
        couple,
    ) -> None:
        response = create_place(client, couple, latitude=95.123456)
        assert response.status_code == 422
        assert "95.123456" not in response.text
