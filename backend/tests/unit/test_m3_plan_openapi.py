"""Der Plan-Slice muss den in M3-D02 bis M3-D05 und M3-D30 entschiedenen
Vertrag spiegeln.

Wie beim Wish leben mehrere Entscheidungen ausschliesslich in der Form des
Vertrags: dass `status`, `sourceWishId` und die Termine nicht aus einem
Request kommen, dass jede Lifecycle-Operation `If-Match` verlangt, und dass
die Konvertierung zwei Erfolgsantworten hat statt einer.
"""

from __future__ import annotations

from sidebyside.main import create_app

COLLECTION = "/api/v1/spaces/{spaceId}/plans"
DETAIL = "/api/v1/spaces/{spaceId}/plans/{planId}"
CONVERT = "/api/v1/spaces/{spaceId}/wishes/{wishId}/plan"
LIFECYCLE = (
    f"{DETAIL}/schedule",
    f"{DETAIL}/unschedule",
    f"{DETAIL}/complete",
    f"{DETAIL}/return-to-wish",
)


def _schema() -> dict[str, object]:
    return create_app().openapi()


def _paths() -> dict[str, dict[str, dict]]:
    return _schema()["paths"]  # type: ignore[index,return-value]


def _components() -> dict[str, dict]:
    return _schema()["components"]["schemas"]  # type: ignore[index,return-value]


def test_plan_routes_have_frozen_operation_ids() -> None:
    paths = _paths()
    assert paths[COLLECTION]["post"]["operationId"] == "createPlan"
    assert paths[COLLECTION]["get"]["operationId"] == "listPlans"
    assert paths[DETAIL]["get"]["operationId"] == "getPlan"
    assert paths[DETAIL]["patch"]["operationId"] == "updatePlan"
    assert paths[DETAIL]["delete"]["operationId"] == "deletePlan"
    assert paths[f"{DETAIL}/schedule"]["post"]["operationId"] == "schedulePlan"
    assert paths[f"{DETAIL}/unschedule"]["post"]["operationId"] == "unschedulePlan"
    assert paths[f"{DETAIL}/complete"]["post"]["operationId"] == "completePlan"
    assert paths[f"{DETAIL}/return-to-wish"]["post"]["operationId"] == "returnPlanToWish"
    assert paths[CONVERT]["post"]["operationId"] == "convertWishToPlan"


def test_the_decided_wish_and_plan_surface_is_now_complete() -> None:
    """M3-D02 nennt sechs Wish- und neun Plan-Operationen.

    M3-S1 hatte die Konvertierung ausgelassen, weil es keinen Plan gab.
    Mit diesem Slice ist die Flaeche vollstaendig - und der Test haelt sie
    fest, damit keine Operation still dazukommt oder verschwindet.
    """
    wish_paths = {pfad for pfad in _paths() if "/wishes" in pfad}
    plan_paths = {pfad for pfad in _paths() if "/plans" in pfad}
    assert wish_paths == {
        "/api/v1/spaces/{spaceId}/wishes",
        "/api/v1/spaces/{spaceId}/wishes/{wishId}",
        CONVERT,
    }
    assert plan_paths == {COLLECTION, DETAIL, *LIFECYCLE}


def test_every_lifecycle_operation_requires_if_match() -> None:
    """Auch `unschedule` und `return-to-wish` - sie haben keinen Body,
    aber sehr wohl eine Wirkung."""
    paths = _paths()
    versioniert = [
        (DETAIL, "patch"),
        (DETAIL, "delete"),
        (CONVERT, "post"),
        *((pfad, "post") for pfad in LIFECYCLE),
    ]
    for pfad, methode in versioniert:
        parameter = {p["name"]: p for p in paths[pfad][methode].get("parameters", [])}
        assert "If-Match" in parameter, f"{methode.upper()} {pfad}"
        assert parameter["If-Match"]["required"] is True


def test_create_does_not_require_if_match() -> None:
    namen = {p["name"] for p in _paths()[COLLECTION]["post"].get("parameters", [])}
    assert "If-Match" not in namen


def test_no_request_body_accepts_server_owned_fields() -> None:
    """M3-D04/D30: Status, Herkunft und Termine kommen nicht vom Client."""
    verboten = {
        "status",
        "sourceWishId",
        "createdBy",
        "spaceId",
        "version",
        "id",
        "createdAt",
        "updatedAt",
    }
    for name in ("PlanCreate", "PlanUpdate", "WishToPlan"):
        schema = _components()[name]
        assert set(schema["properties"]) & verboten == set(), name
        assert schema.get("additionalProperties") is False, name


def test_only_schedule_accepts_planned_dates() -> None:
    """`plannedStart`/`plannedEnd` gehoeren der Terminierung, nicht dem PATCH."""
    assert set(_components()["PlanSchedule"]["properties"]) == {"plannedStart", "plannedEnd"}
    assert _components()["PlanSchedule"]["required"] == ["plannedStart"]
    for name in ("PlanCreate", "PlanUpdate", "WishToPlan"):
        assert "plannedStart" not in _components()[name]["properties"], name
        assert "plannedEnd" not in _components()[name]["properties"], name


def test_only_complete_and_patch_carry_the_experienced_day() -> None:
    assert set(_components()["PlanComplete"]["properties"]) == {"experiencedOn"}
    assert _components()["PlanComplete"]["required"] == ["experiencedOn"]
    # Die Korrektur am abgeschlossenen Plan (M3-D04).
    assert "experiencedOn" in _components()["PlanUpdate"]["properties"]
    assert "experiencedOn" not in _components()["PlanCreate"]["properties"]


def test_direct_create_needs_only_a_title() -> None:
    schema = _components()["PlanCreate"]
    assert set(schema["properties"]) == {"title", "description"}
    assert schema["required"] == ["title"]


def test_conversion_carries_no_required_field() -> None:
    """Ohne eigenen Titel uebernimmt der Plan den des Wishes."""
    schema = _components()["WishToPlan"]
    assert set(schema["properties"]) == {"title", "description"}
    assert "required" not in schema


def test_conversion_documents_both_success_answers() -> None:
    """Der idempotente Retry ist Teil des Vertrags, kein Zufall.

    Ein Client, der nur 201 kennt, wuerde die 200-Antwort als Fehler
    behandeln - und genau dann einen zweiten Plan anlegen wollen.
    """
    antworten = _paths()[CONVERT]["post"]["responses"]
    assert "201" in antworten
    assert "200" in antworten
    assert "409" in antworten


def test_conversion_returns_both_resources() -> None:
    schema = _components()["WishToPlanResponse"]
    assert set(schema["properties"]) == {"wish", "plan"}


def test_return_to_wish_answers_with_the_wish_and_the_removed_id() -> None:
    """Der Plan ist danach weg; eine Plan-Darstellung waere eine Luege."""
    schema = _components()["PlanReturnToWishResponse"]
    assert set(schema["properties"]) == {"wish", "removedPlanId"}


def test_detail_exposes_lifecycle_state_read_only() -> None:
    schema = _components()["PlanDetail"]
    assert {
        "status",
        "sourceWishId",
        "plannedStart",
        "plannedEnd",
        "experiencedOn",
        "createdBy",
        "capabilities",
    } <= set(schema["properties"])
    assert set(_components()["PlanStatus"]["enum"]) == {"IDEA", "PLANNED", "COMPLETED"}


def test_list_filters_by_status_and_not_by_free_text() -> None:
    parameter = {p["name"] for p in _paths()[COLLECTION]["get"].get("parameters", [])}
    assert {"status", "cursor", "limit"} <= parameter
    assert "q" not in parameter


def test_no_place_surface_leaked_into_this_slice() -> None:
    """`placeId` ist M3-S3.

    M3-D02 und M3-D30 nennen das Feld bereits. Es steht hier trotzdem
    nicht im Vertrag: ohne Place-Domaene gaebe es nichts, worauf es zeigen
    koennte, und ein Vertrag mit einem unbenutzbaren Feld verspricht eine
    Zuordnung, die der Server nicht herstellen kann.
    """
    for name in ("PlanCreate", "PlanUpdate", "WishToPlan", "PlanDetail"):
        assert "placeId" not in _components()[name]["properties"], name
