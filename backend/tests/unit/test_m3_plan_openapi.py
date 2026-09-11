"""Verify the Plan slice reflects the current shared scheduling contract."""

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
    wish_paths = {path for path in _paths() if "/wishes" in path}
    plan_paths = {path for path in _paths() if "/plans" in path}
    assert wish_paths == {
        "/api/v1/spaces/{spaceId}/wishes",
        "/api/v1/spaces/{spaceId}/wishes/{wishId}",
        CONVERT,
    }
    assert plan_paths == {COLLECTION, DETAIL, *LIFECYCLE}


def test_every_lifecycle_operation_requires_if_match() -> None:
    paths = _paths()
    versioned = [
        (DETAIL, "patch"),
        (DETAIL, "delete"),
        (CONVERT, "post"),
        *((path, "post") for path in LIFECYCLE),
    ]
    for path, method in versioned:
        parameters = {p["name"]: p for p in paths[path][method].get("parameters", [])}
        assert "If-Match" in parameters, f"{method.upper()} {path}"
        assert parameters["If-Match"]["required"] is True


def test_create_does_not_require_if_match() -> None:
    names = {p["name"] for p in _paths()[COLLECTION]["post"].get("parameters", [])}
    assert "If-Match" not in names


def test_no_request_body_accepts_server_owned_fields() -> None:
    forbidden = {
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
        assert set(schema["properties"]) & forbidden == set(), name
        assert schema.get("additionalProperties") is False, name


def test_schedule_contract_distinguishes_calendar_date_from_instant() -> None:
    schedule = _components()["PlanSchedule"]
    assert set(schedule["properties"]) == {"plannedOn", "plannedStart", "plannedEnd"}
    assert "required" not in schedule
    assert schedule["properties"]["plannedOn"]["format"] == "date"
    assert schedule["properties"]["plannedStart"]["format"] == "date-time"
    assert schedule["properties"]["plannedEnd"]["format"] == "date-time"

    # Create and Wish conversion may carry the same nested schedule atomically;
    # PATCH stays lifecycle-neutral and raw schedule fields never leak outward.
    assert "schedule" in _components()["PlanCreate"]["properties"]
    assert "schedule" in _components()["WishToPlan"]["properties"]
    assert "schedule" not in _components()["PlanUpdate"]["properties"]
    for name in ("PlanCreate", "PlanUpdate", "WishToPlan"):
        assert "plannedOn" not in _components()[name]["properties"], name
        assert "plannedStart" not in _components()[name]["properties"], name
        assert "plannedEnd" not in _components()[name]["properties"], name


def test_only_complete_and_patch_carry_the_experienced_day() -> None:
    assert set(_components()["PlanComplete"]["properties"]) == {"experiencedOn"}
    assert _components()["PlanComplete"]["required"] == ["experiencedOn"]
    assert "experiencedOn" in _components()["PlanUpdate"]["properties"]
    assert "experiencedOn" not in _components()["PlanCreate"]["properties"]


def test_direct_create_needs_only_a_title() -> None:
    schema = _components()["PlanCreate"]
    assert set(schema["properties"]) == {"title", "description", "placeId", "schedule"}
    assert schema["required"] == ["title"]


def test_conversion_carries_no_required_field() -> None:
    schema = _components()["WishToPlan"]
    assert set(schema["properties"]) == {"title", "description", "placeId", "schedule"}
    assert "required" not in schema


def test_conversion_documents_both_success_answers() -> None:
    responses = _paths()[CONVERT]["post"]["responses"]
    assert "201" in responses
    assert "200" in responses
    assert "409" in responses


def test_conversion_returns_both_resources() -> None:
    schema = _components()["WishToPlanResponse"]
    assert set(schema["properties"]) == {"wish", "plan"}


def test_return_to_wish_answers_with_the_wish_and_the_removed_id() -> None:
    schema = _components()["PlanReturnToWishResponse"]
    assert set(schema["properties"]) == {"wish", "removedPlanId"}


def test_detail_exposes_lifecycle_state_read_only() -> None:
    schema = _components()["PlanDetail"]
    assert {
        "status",
        "sourceWishId",
        "plannedOn",
        "plannedStart",
        "plannedEnd",
        "experiencedOn",
        "createdBy",
        "capabilities",
    } <= set(schema["properties"])
    assert schema["properties"]["plannedOn"]["anyOf"][0]["format"] == "date"
    assert set(_components()["PlanStatus"]["enum"]) == {"IDEA", "PLANNED", "COMPLETED"}


def test_list_filters_by_status_and_not_by_free_text() -> None:
    parameters = {p["name"] for p in _paths()[COLLECTION]["get"].get("parameters", [])}
    assert {"status", "cursor", "limit"} <= parameters
    assert "q" not in parameters
