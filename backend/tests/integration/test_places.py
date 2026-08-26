"""PostgreSQL-/HTTP-Abnahme fuer den M3-S3-Place-Slice.

Der Schwerpunkt liegt auf drei Zusicherungen aus M3-D06 bis M3-D08.

Koordinaten sind ein Paar, liegen in ihren Grenzen und werden auf sechs
Nachkommastellen persistiert. Es gibt keine Deduplizierung: zwei Orte mit
demselben Namen bleiben zwei Orte. Und ein Place-Delete entfernt genau den
Ort - Plans, die auf ihn zeigen, verlieren die Zuordnung und bleiben
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

# Bewusst echte Werte in Testdaten - der Punkt mehrerer Tests ist, dass
# genau sie nirgends auftauchen, wo sie nicht hingehoeren.
BERLIN_LAT = 52.520008
BERLIN_LON = 13.404954
GEHEIME_ADRESSE = "Eine Adresse, die nicht in Ereignisse gehoert."


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
    """Ein Create-Body.

    `description` und `address` werden weggelassen statt auf `null`
    gesetzt - beim Anlegen unterscheidet der Vertrag die beiden nicht und
    weist ein ausdrueckliches `null` ab (wie bei Memory und Milestone).
    Die Koordinaten sind der bewusste Gegenfall: sie duerfen ausdruecklich
    `null` sein, weil sie ein Paar bilden und ein Client sie oft als Paar
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


class TestCrud:
    def test_anlegen_lesen_aendern_loeschen(  # type: ignore[no-untyped-def]
        self,
        client,
        paar,
    ) -> None:
        angelegt = erstelle(client, paar)
        assert angelegt.status_code == 201
        o = angelegt.json()
        assert UUID(o["id"]).version == 7
        assert o["name"] == "Unser Cafe"
        assert o["description"] == "Ecktisch am Fenster."
        assert o["address"] == "Beispielstrasse 1"
        assert o["latitude"] == BERLIN_LAT
        assert o["longitude"] == BERLIN_LON
        assert o["createdBy"] == str(paar["anna"].id)
        assert o["capabilities"] == {"canEdit": True, "canDelete": True, "canComment": False}
        assert "privacyClass" not in o
        assert angelegt.headers["ETag"] == '"1"'

        geaendert = client.patch(
            f"{path(paar['space'].id)}/{o['id']}",
            json={"name": "  Unser Stammcafe  ", "description": None},
            headers=if_match(paar["token_a"], 1),
        )
        assert geaendert.status_code == 200
        assert geaendert.json()["name"] == "Unser Stammcafe"
        assert geaendert.json()["description"] is None
        # Unberuehrte Felder bleiben stehen.
        assert geaendert.json()["latitude"] == BERLIN_LAT

        geloescht = client.delete(
            f"{path(paar['space'].id)}/{o['id']}", headers=if_match(paar["token_a"], 2)
        )
        assert geloescht.status_code == 204
        danach = client.get(f"{path(paar['space'].id)}/{o['id']}", headers=auth(paar["token_a"]))
        assert danach.status_code == 404
        assert danach.json()["code"] == "PLACE_NOT_FOUND"

    def test_der_partner_darf_aendern_und_createdby_bleibt(  # type: ignore[no-untyped-def]
        self,
        client,
        paar,
    ) -> None:
        """M3-D01 gilt fuer Place wie fuer Wish und Plan."""
        o = erstelle(client, paar).json()
        geaendert = client.patch(
            f"{path(paar['space'].id)}/{o['id']}",
            json={"name": "Von Ben umbenannt"},
            headers=if_match(paar["token_b"], 1),
        )
        assert geaendert.status_code == 200
        assert geaendert.json()["createdBy"] == str(paar["anna"].id)

    def test_leerer_name_wird_abgewiesen(  # type: ignore[no-untyped-def]
        self,
        client,
        paar,
    ) -> None:
        assert erstelle(client, paar, name="   ").status_code == 422

    def test_veraltete_version_wird_abgewiesen(  # type: ignore[no-untyped-def]
        self,
        client,
        paar,
    ) -> None:
        o = erstelle(client, paar).json()
        client.patch(
            f"{path(paar['space'].id)}/{o['id']}",
            json={"name": "Erste Aenderung"},
            headers=if_match(paar["token_a"], 1),
        )
        zweite = client.patch(
            f"{path(paar['space'].id)}/{o['id']}",
            json={"name": "Zweite Aenderung"},
            headers=if_match(paar["token_a"], 1),
        )
        assert zweite.status_code == 409
        assert zweite.json()["code"] == "RESOURCE_VERSION_CONFLICT"

    def test_die_liste_zeigt_neueste_zuerst(  # type: ignore[no-untyped-def]
        self,
        client,
        paar,
    ) -> None:
        erster = erstelle(client, paar, name="Erster").json()
        zweiter = erstelle(client, paar, name="Zweiter").json()
        seite = client.get(path(paar["space"].id), headers=auth(paar["token_a"])).json()
        assert [e["id"] for e in seite["items"]] == [zweiter["id"], erster["id"]]

    def test_der_cursor_gilt_nur_in_seinem_space(  # type: ignore[no-untyped-def]
        self,
        client,
        paar,
    ) -> None:
        erstelle(client, paar, name="Erster")
        erstelle(client, paar, name="Zweiter")
        seite = client.get(
            f"{path(paar['space'].id)}?limit=1", headers=auth(paar["token_a"])
        ).json()
        antwort = client.get(
            f"{path(paar['fremder_space'].id)}?limit=1&cursor={seite['nextCursor']}",
            headers=auth(paar["token_b"]),
        )
        assert antwort.status_code == 400
        assert antwort.json()["code"] == "INVALID_CURSOR"


class TestKoordinaten:
    """M3-D06: beide oder keine, in ihren Grenzen, sechs Nachkommastellen."""

    def test_ein_ort_ohne_koordinaten_ist_gueltig(  # type: ignore[no-untyped-def]
        self,
        client,
        paar,
    ) -> None:
        """Viele Orte eines Paares sind ein Name und sonst nichts."""
        antwort = erstelle(
            client, paar, latitude=None, longitude=None, address=None, description=None
        )
        assert antwort.status_code == 201
        assert antwort.json()["latitude"] is None
        assert antwort.json()["longitude"] is None
        assert antwort.json()["address"] is None

    def test_ein_ausdrueckliches_null_paar_ist_erlaubt(  # type: ignore[no-untyped-def]
        self,
        client,
        paar,
    ) -> None:
        """Ein Client, der die Koordinaten als Paar fuehrt, sendet beide.

        Fuer `description` und `address` gilt das nicht: dort weist der
        Create-Vertrag ein ausdrueckliches `null` ab, wie bei Memory und
        Milestone auch.
        """
        antwort = client.post(
            path(paar["space"].id),
            json={"name": "Nur ein Name", "latitude": None, "longitude": None},
            headers=auth(paar["token_a"]),
        )
        assert antwort.status_code == 201

        mit_null_text = client.post(
            path(paar["space"].id),
            json={"name": "Nur ein Name", "address": None},
            headers=auth(paar["token_a"]),
        )
        assert mit_null_text.status_code == 422

    def test_eine_adresse_ohne_koordinaten_ist_gueltig(  # type: ignore[no-untyped-def]
        self,
        client,
        paar,
    ) -> None:
        antwort = erstelle(client, paar, latitude=None, longitude=None)
        assert antwort.status_code == 201
        assert antwort.json()["address"] == "Beispielstrasse 1"

    def test_koordinaten_ohne_adresse_sind_gueltig(  # type: ignore[no-untyped-def]
        self,
        client,
        paar,
    ) -> None:
        antwort = erstelle(client, paar, address=None)
        assert antwort.status_code == 201
        assert antwort.json()["latitude"] == BERLIN_LAT

    @pytest.mark.parametrize("fehlend", ["latitude", "longitude"])
    def test_eine_halbe_koordinate_wird_abgewiesen(  # type: ignore[no-untyped-def]
        self,
        client,
        paar,
        fehlend: str,
    ) -> None:
        antwort = erstelle(client, paar, **{fehlend: None})
        assert antwort.status_code == 422
        assert antwort.json()["code"] == "PLACE_COORDINATE_PAIR_REQUIRED"

    @pytest.mark.parametrize(
        ("latitude", "longitude", "code"),
        [
            (90.000001, 0.0, "PLACE_LATITUDE_INVALID"),
            (-90.000001, 0.0, "PLACE_LATITUDE_INVALID"),
            (0.0, 180.000001, "PLACE_LONGITUDE_INVALID"),
            (0.0, -180.000001, "PLACE_LONGITUDE_INVALID"),
        ],
    )
    def test_werte_ausserhalb_der_grenzen(  # type: ignore[no-untyped-def]
        self,
        client,
        paar,
        latitude,
        longitude,
        code,
    ) -> None:
        antwort = erstelle(client, paar, latitude=latitude, longitude=longitude)
        assert antwort.status_code == 422
        assert antwort.json()["code"] == code

    @pytest.mark.parametrize(
        ("latitude", "longitude"),
        [(90.0, 180.0), (-90.0, -180.0), (0.0, 0.0)],
    )
    def test_die_grenzwerte_selbst_sind_gueltig(  # type: ignore[no-untyped-def]
        self,
        client,
        paar,
        latitude,
        longitude,
    ) -> None:
        antwort = erstelle(client, paar, latitude=latitude, longitude=longitude)
        assert antwort.status_code == 201
        assert antwort.json()["latitude"] == latitude
        assert antwort.json()["longitude"] == longitude

    def test_mehr_stellen_werden_auf_sechs_gerundet(  # type: ignore[no-untyped-def]
        self,
        client,
        paar,
        session,
    ) -> None:
        """Ein Sensor liefert mehr; gespeichert werden sechs Stellen.

        Abweisen waere hier falsch - der Client hat nichts falsch gemacht.
        """
        antwort = erstelle(client, paar, latitude=52.5200081234, longitude=13.4049544321)
        assert antwort.status_code == 201
        assert antwort.json()["latitude"] == 52.520008
        assert antwort.json()["longitude"] == 13.404954

        zeile = session.get(Place, UUID(antwort.json()["id"]))
        assert zeile.latitude == Decimal("52.520008")
        assert zeile.longitude == Decimal("13.404954")

    def test_koordinaten_koennen_nachgetragen_werden(  # type: ignore[no-untyped-def]
        self,
        client,
        paar,
    ) -> None:
        o = erstelle(client, paar, latitude=None, longitude=None).json()
        antwort = client.patch(
            f"{path(paar['space'].id)}/{o['id']}",
            json={"latitude": BERLIN_LAT, "longitude": BERLIN_LON},
            headers=if_match(paar["token_a"], 1),
        )
        assert antwort.status_code == 200
        assert antwort.json()["latitude"] == BERLIN_LAT

    def test_koordinaten_koennen_wieder_entfernt_werden(  # type: ignore[no-untyped-def]
        self,
        client,
        paar,
    ) -> None:
        o = erstelle(client, paar).json()
        antwort = client.patch(
            f"{path(paar['space'].id)}/{o['id']}",
            json={"latitude": None, "longitude": None},
            headers=if_match(paar["token_a"], 1),
        )
        assert antwort.status_code == 200
        assert antwort.json()["latitude"] is None
        assert antwort.json()["longitude"] is None

    def test_ein_patch_auf_nur_eine_koordinate_wird_abgewiesen(  # type: ignore[no-untyped-def]
        self,
        client,
        paar,
    ) -> None:
        """Sonst waere das PATCH der Weg zur halben Koordinate."""
        o = erstelle(client, paar).json()
        antwort = client.patch(
            f"{path(paar['space'].id)}/{o['id']}",
            json={"latitude": None},
            headers=if_match(paar["token_a"], 1),
        )
        assert antwort.status_code == 422
        assert antwort.json()["code"] == "PLACE_COORDINATE_PAIR_REQUIRED"

    @pytest.mark.parametrize(
        "sql",
        [
            "UPDATE places SET latitude = 10.0, longitude = NULL WHERE id = :id",
            "UPDATE places SET latitude = 91.0 WHERE id = :id",
            "UPDATE places SET longitude = 181.0 WHERE id = :id",
        ],
    )
    def test_die_datenbank_haelt_die_invarianten_auch_ohne_den_dienst(
        self, client, paar, session, sql: str
    ) -> None:  # type: ignore[no-untyped-def]
        o = erstelle(client, paar).json()
        with pytest.raises(IntegrityError), session.begin_nested():
            session.execute(text(sql), {"id": o["id"]})


class TestKeineDeduplizierung:
    """M3-D07: zwei gleiche Orte sind zwei Orte."""

    def test_derselbe_name_und_dieselben_koordinaten_erzeugen_zwei_orte(  # type: ignore[no-untyped-def]
        self,
        client,
        paar,
    ) -> None:
        erster = erstelle(client, paar).json()
        zweiter = erstelle(client, paar).json()
        assert erster["id"] != zweiter["id"]

        seite = client.get(path(paar["space"].id), headers=auth(paar["token_a"])).json()
        assert len(seite["items"]) == 2


class TestPlanZuordnung:
    """M3-D08/D31: `Plan.placeId` ist die einzige Plan/Place-Wahrheit."""

    def _plan(self, client, paar, **felder):  # type: ignore[no-untyped-def]
        return client.post(
            f"/api/v1/spaces/{paar['space'].id}/plans",
            json={"title": "Abendessen", **felder},
            headers=auth(paar["token_a"]),
        )

    def test_ein_plan_kann_direkt_mit_ort_entstehen(  # type: ignore[no-untyped-def]
        self,
        client,
        paar,
    ) -> None:
        o = erstelle(client, paar).json()
        plan = self._plan(client, paar, placeId=o["id"])
        assert plan.status_code == 201
        assert plan.json()["placeId"] == o["id"]

    def test_der_ort_kann_nachtraeglich_gesetzt_und_geloest_werden(  # type: ignore[no-untyped-def]
        self,
        client,
        paar,
    ) -> None:
        o = erstelle(client, paar).json()
        plan = self._plan(client, paar).json()
        assert plan["placeId"] is None

        gesetzt = client.patch(
            f"/api/v1/spaces/{paar['space'].id}/plans/{plan['id']}",
            json={"placeId": o["id"]},
            headers=if_match(paar["token_a"], 1),
        )
        assert gesetzt.status_code == 200
        assert gesetzt.json()["placeId"] == o["id"]

        geloest = client.patch(
            f"/api/v1/spaces/{paar['space'].id}/plans/{plan['id']}",
            json={"placeId": None},
            headers=if_match(paar["token_a"], 2),
        )
        assert geloest.status_code == 200
        assert geloest.json()["placeId"] is None

    def test_ein_ort_aus_einem_fremden_space_bleibt_unsichtbar(  # type: ignore[no-untyped-def]
        self,
        client,
        paar,
        session,
    ) -> None:
        fremder_ort = client.post(
            path(paar["fremder_space"].id), json=body(), headers=auth(paar["token_b"])
        ).json()

        antwort = self._plan(client, paar, placeId=fremder_ort["id"])
        assert antwort.status_code == 404
        assert antwort.json()["code"] == "PLACE_NOT_FOUND"
        assert list(session.execute(select(Plan)).scalars()) == []

    def test_eine_unbekannte_und_eine_fremde_id_klingen_gleich(  # type: ignore[no-untyped-def]
        self,
        client,
        paar,
    ) -> None:
        fremder_ort = client.post(
            path(paar["fremder_space"].id), json=body(), headers=auth(paar["token_b"])
        ).json()
        unbekannt = self._plan(client, paar, placeId=str(uuid4()))
        fremd = self._plan(client, paar, placeId=fremder_ort["id"])
        assert unbekannt.status_code == fremd.status_code == 404
        assert unbekannt.json() == fremd.json()

    def test_eine_konvertierung_darf_den_ort_gleich_mitgeben(  # type: ignore[no-untyped-def]
        self,
        client,
        paar,
    ) -> None:
        o = erstelle(client, paar).json()
        wunsch = client.post(
            f"/api/v1/spaces/{paar['space'].id}/wishes",
            json={"title": "Essen gehen"},
            headers=auth(paar["token_a"]),
        ).json()

        antwort = client.post(
            f"/api/v1/spaces/{paar['space'].id}/wishes/{wunsch['id']}/plan",
            json={"placeId": o["id"]},
            headers=if_match(paar["token_a"], 1),
        )
        assert antwort.status_code == 201
        assert antwort.json()["plan"]["placeId"] == o["id"]


class TestDelete:
    """M3-D06, Abschnitt 9: der Ort geht, die Originale bleiben."""

    def test_der_plan_ueberlebt_seinen_ort_und_bekommt_eine_neue_version(
        self, client, paar, session
    ) -> None:  # type: ignore[no-untyped-def]
        o = erstelle(client, paar).json()
        plan = client.post(
            f"/api/v1/spaces/{paar['space'].id}/plans",
            json={"title": "Abendessen", "placeId": o["id"]},
            headers=auth(paar["token_a"]),
        ).json()
        assert plan["version"] == 1

        entfernt = client.delete(
            f"{path(paar['space'].id)}/{o['id']}", headers=if_match(paar["token_a"], 1)
        )
        assert entfernt.status_code == 204

        danach = client.get(
            f"/api/v1/spaces/{paar['space'].id}/plans/{plan['id']}", headers=auth(paar["token_a"])
        ).json()
        assert danach["placeId"] is None
        assert danach["title"] == "Abendessen"
        # Der Plan hat sich geaendert - und sagt das auch.
        assert danach["version"] == 2

    def test_ein_client_mit_altem_stand_bekommt_einen_konflikt(  # type: ignore[no-untyped-def]
        self,
        client,
        paar,
    ) -> None:
        """Der eigentliche Grund fuer die neue Version.

        Ein stilles `ON DELETE SET NULL` wuerde den Ort unter dem Partner
        wegziehen, ohne dass sein naechster Schreibzugriff je auffiele.
        """
        o = erstelle(client, paar).json()
        plan = client.post(
            f"/api/v1/spaces/{paar['space'].id}/plans",
            json={"title": "Abendessen", "placeId": o["id"]},
            headers=auth(paar["token_a"]),
        ).json()

        client.delete(f"{path(paar['space'].id)}/{o['id']}", headers=if_match(paar["token_a"], 1))

        antwort = client.patch(
            f"/api/v1/spaces/{paar['space'].id}/plans/{plan['id']}",
            json={"title": "Mit altem Stand"},
            headers=if_match(paar["token_b"], 1),
        )
        assert antwort.status_code == 409
        assert antwort.json()["code"] == "RESOURCE_VERSION_CONFLICT"

    def test_mehrere_plans_werden_alle_geloest(  # type: ignore[no-untyped-def]
        self,
        client,
        paar,
        session,
    ) -> None:
        o = erstelle(client, paar).json()
        for titel in ("Erster", "Zweiter", "Dritter"):
            client.post(
                f"/api/v1/spaces/{paar['space'].id}/plans",
                json={"title": titel, "placeId": o["id"]},
                headers=auth(paar["token_a"]),
            )

        client.delete(f"{path(paar['space'].id)}/{o['id']}", headers=if_match(paar["token_a"], 1))

        session.expire_all()
        plaene = list(session.execute(select(Plan)).scalars())
        assert len(plaene) == 3
        assert all(p.place_id is None for p in plaene)

    def test_ein_plan_ohne_ort_bleibt_unberuehrt(  # type: ignore[no-untyped-def]
        self,
        client,
        paar,
    ) -> None:
        o = erstelle(client, paar).json()
        ohne_ort = client.post(
            f"/api/v1/spaces/{paar['space'].id}/plans",
            json={"title": "Ohne Ort"},
            headers=auth(paar["token_a"]),
        ).json()

        client.delete(f"{path(paar['space'].id)}/{o['id']}", headers=if_match(paar["token_a"], 1))

        danach = client.get(
            f"/api/v1/spaces/{paar['space'].id}/plans/{ohne_ort['id']}",
            headers=auth(paar["token_a"]),
        ).json()
        assert danach["version"] == 1

    def test_die_datenbank_laesst_keinen_plan_auf_einen_geloeschten_ort_zeigen(
        self, client, paar, session
    ) -> None:  # type: ignore[no-untyped-def]
        """Der Fremdschluessel als Grenze, falls der Dienst einmal ausfaellt."""
        o = erstelle(client, paar).json()
        client.post(
            f"/api/v1/spaces/{paar['space'].id}/plans",
            json={"title": "Abendessen", "placeId": o["id"]},
            headers=auth(paar["token_a"]),
        )

        session.execute(text("DELETE FROM places WHERE id = :id"), {"id": o["id"]})
        session.flush()
        session.expire_all()

        plan = session.execute(select(Plan)).scalar_one()
        assert plan.place_id is None
        assert plan.space_id == paar["space"].id


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
        o = erstelle(client, paar).json()
        gelesen = client.get(
            f"{path(paar['fremder_space'].id)}/{o['id']}", headers=auth(paar["token_b"])
        )
        assert gelesen.status_code == 404
        assert gelesen.json()["code"] == "PLACE_NOT_FOUND"

    def test_ein_fremdschreibversuch_aendert_nichts(  # type: ignore[no-untyped-def]
        self,
        client,
        paar,
        session,
    ) -> None:
        o = erstelle(client, paar).json()
        antwort = client.patch(
            f"{path(paar['fremder_space'].id)}/{o['id']}",
            json={"name": "Uebernommen"},
            headers=if_match(paar["token_b"], 1),
        )
        assert antwort.status_code == 404

        session.expire_all()
        assert session.get(Place, UUID(o["id"])).payload.name == "Unser Cafe"


class TestPrivacy:
    def test_events_enthalten_weder_adresse_noch_koordinaten(  # type: ignore[no-untyped-def]
        self,
        client,
        paar,
        session,
    ) -> None:
        o = erstelle(client, paar, address=GEHEIME_ADRESSE).json()
        client.patch(
            f"{path(paar['space'].id)}/{o['id']}",
            json={"name": "Neu benannt"},
            headers=if_match(paar["token_a"], 1),
        )
        client.delete(f"{path(paar['space'].id)}/{o['id']}", headers=if_match(paar["token_a"], 2))

        zeilen = list(
            session.execute(
                select(OutboxEvent).where(OutboxEvent.subject_type == "place")
            ).scalars()
        )
        assert [z.event_type for z in zeilen] == [
            "PLACE_CREATED",
            "PLACE_UPDATED",
            "PLACE_DELETED",
        ]
        for zeile in zeilen:
            roh = repr(zeile.payload.model_dump())
            assert GEHEIME_ADRESSE not in roh
            assert "52.520008" not in roh
            assert "13.404954" not in roh
            assert zeile.resource_version is not None

    def test_eine_fehlerantwort_nennt_keine_koordinate(  # type: ignore[no-untyped-def]
        self,
        client,
        paar,
    ) -> None:
        antwort = erstelle(client, paar, latitude=95.123456)
        assert antwort.status_code == 422
        assert "95.123456" not in antwort.text
