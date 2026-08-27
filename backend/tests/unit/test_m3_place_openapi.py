"""Der Place-Slice muss den in M3-D06 bis M3-D08 entschiedenen Vertrag
spiegeln.

Zwei Zusicherungen leben ausschliesslich in der Form des Vertrags: dass
Koordinaten nur als Paar existieren koennen, und dass M3 keine
Kartenfunktion verspricht - kein Geocoding, keine Providerdaten, keine
Umkreissuche.
"""

from __future__ import annotations

from sidebyside.main import create_app

COLLECTION = "/api/v1/spaces/{spaceId}/places"
DETAIL = "/api/v1/spaces/{spaceId}/places/{placeId}"


def _schema() -> dict[str, object]:
    return create_app().openapi()


def _paths() -> dict[str, dict[str, dict]]:
    return _schema()["paths"]  # type: ignore[index,return-value]


def _components() -> dict[str, dict]:
    return _schema()["components"]["schemas"]  # type: ignore[index,return-value]


def test_place_routes_have_frozen_operation_ids() -> None:
    paths = _paths()
    assert paths[COLLECTION]["post"]["operationId"] == "createPlace"
    assert paths[COLLECTION]["get"]["operationId"] == "listPlaces"
    assert paths[DETAIL]["get"]["operationId"] == "getPlace"
    assert paths[DETAIL]["patch"]["operationId"] == "updatePlace"
    assert paths[DETAIL]["delete"]["operationId"] == "deletePlace"


def test_the_place_surface_is_exactly_crud() -> None:
    """Die typisierten Relationen aus M3-D08 sind M3-S4.

    `places/{placeId}/memories` und die beiden Geschwister fehlen hier
    absichtlich - es gibt noch keine Join-Tabelle, die sie fuellen wuerde.
    """
    assert {pfad for pfad in _paths() if "/places" in pfad} == {COLLECTION, DETAIL}


def test_mutations_require_if_match() -> None:
    detail = _paths()[DETAIL]
    for methode in ("patch", "delete"):
        parameter = {p["name"]: p for p in detail[methode].get("parameters", [])}
        assert "If-Match" in parameter
        assert parameter["If-Match"]["required"] is True


def test_no_request_body_accepts_server_owned_fields() -> None:
    verboten = {"createdBy", "spaceId", "version", "id", "createdAt", "updatedAt", "privacyClass"}
    for name in ("PlaceCreate", "PlaceUpdate"):
        schema = _components()[name]
        assert set(schema["properties"]) & verboten == set(), name
        assert schema.get("additionalProperties") is False, name


def test_create_needs_only_a_name() -> None:
    """Ein Ort ohne Koordinaten ist voll gueltig (M3-D06)."""
    schema = _components()["PlaceCreate"]
    assert set(schema["properties"]) == {"name", "description", "address", "latitude", "longitude"}
    assert schema["required"] == ["name"]


def test_coordinates_are_numbers_and_nullable_in_the_patch() -> None:
    """Nur so laesst sich ein Ort wieder auf reinen Namen zuruecksetzen."""
    update = _components()["PlaceUpdate"]["properties"]
    for feld in ("latitude", "longitude"):
        typen = {option.get("type") for option in update[feld].get("anyOf", [])}
        assert "number" in typen, feld
        assert "null" in typen, feld


def test_detail_exposes_the_stored_coordinates() -> None:
    schema = _components()["PlaceDetail"]
    assert {"name", "description", "address", "latitude", "longitude", "createdBy"} <= set(
        schema["properties"]
    )


def test_the_contract_promises_no_map_feature() -> None:
    """M3 ist Domain plus gespeicherte Ortsdaten - keine Kartenansicht.

    Kein Geocoding, keine Provider-IDs, keine Umkreissuche und keine
    Sortierung nach Distanz. Alles davon waere ein Providerthema mit
    eigener Reuse-Pruefung und liegt in M7/M8.
    """
    place_schemas = {
        name: schema for name, schema in _components().items() if name.startswith("Place")
    }
    verboten = {
        "provider",
        "providerId",
        "placeId_external",
        "mapUrl",
        "geocoded",
        "formattedAddress",
        "distance",
        "radius",
    }
    for name, schema in place_schemas.items():
        assert set(schema.get("properties", {})) & verboten == set(), name

    parameter = {p["name"] for p in _paths()[COLLECTION]["get"].get("parameters", [])}
    assert parameter == {"spaceId", "cursor", "limit"}


def test_the_plan_contract_now_carries_the_place() -> None:
    """Aus M3-S2 nachgezogen (M3-D08/D31).

    `placeId` ist einspaltig und kanonisch - es gibt keine
    `place_plans`-Flaeche daneben.
    """
    for name in ("PlanCreate", "WishToPlan"):
        assert "placeId" in _components()[name]["properties"], name

    update = _components()["PlanUpdate"]["properties"]["placeId"]
    typen = {option.get("type") for option in update.get("anyOf", [])}
    assert "null" in typen

    assert "placeId" in _components()["PlanDetail"]["properties"]
    assert not any("/plans/{planId}/places" in pfad for pfad in _paths())
