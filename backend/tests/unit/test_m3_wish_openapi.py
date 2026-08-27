"""The Wish slice must mirror the contract decided in M3-D01/D02/D05.

The contract is more than formality here. Two decisions exist exclusively in
its shape: `status` is not a field a client writes, and `createdBy` is
attribution rather than an ACL. A request schema that allowed either would
bypass the Wish-to-Plan contract before any service is invoked.
"""

from __future__ import annotations

from sidebyside.main import create_app

COLLECTION = "/api/v1/spaces/{spaceId}/wishes"
DETAIL = "/api/v1/spaces/{spaceId}/wishes/{wishId}"


def _schema() -> dict[str, object]:
    return create_app().openapi()


def _paths() -> dict[str, dict[str, dict]]:
    return _schema()["paths"]  # type: ignore[index,return-value]


def _components() -> dict[str, dict]:
    return _schema()["components"]["schemas"]  # type: ignore[index,return-value]


def test_wish_routes_have_frozen_operation_ids() -> None:
    paths = _paths()
    assert paths[COLLECTION]["post"]["operationId"] == "createWish"
    assert paths[COLLECTION]["get"]["operationId"] == "listWishes"
    assert paths[DETAIL]["get"]["operationId"] == "getWish"
    assert paths[DETAIL]["patch"]["operationId"] == "updateWish"
    assert paths[DETAIL]["delete"]["operationId"] == "deleteWish"


def test_the_contract_carries_exactly_the_decided_wish_surface() -> None:
    """M3-D02 names six Wish operations.

    Five arrived with M3-S1; the sixth, `POST .../wishes/{wishId}/plan`, arrived
    with M3-S2. This test only counts it; `test_m3_plan_openapi` verifies its
    shape because it creates a Plan.
    """
    wish_paths = {path for path in _paths() if "/wishes" in path}
    assert wish_paths == {COLLECTION, DETAIL, f"{DETAIL}/plan"}


def test_no_wish_operation_sets_the_status_directly() -> None:
    """Wish status has no dedicated route and must not gain one.

    Every status transition is tied to a Plan operation (M3-D02/D03/D04). A
    route such as `/wishes/{wishId}/complete` would be exactly the direct path
    excluded by the contract.
    """
    wish_paths = {path for path in _paths() if "/wishes" in path}
    for forbidden in ("complete", "plan-status", "status", "reopen"):
        assert not any(path.endswith(f"/{forbidden}") for path in wish_paths), forbidden


def test_mutations_require_if_match() -> None:
    detail = _paths()[DETAIL]
    for method in ("patch", "delete"):
        names = {parameter["name"] for parameter in detail[method].get("parameters", [])}
        assert "If-Match" in names
        required = next(
            parameter
            for parameter in detail[method]["parameters"]
            if parameter["name"] == "If-Match"
        )
        assert required["required"] is True


def test_create_does_not_require_if_match() -> None:
    """A Wish that does not exist yet has no version to compare."""
    names = {parameter["name"] for parameter in _paths()[COLLECTION]["post"].get("parameters", [])}
    assert "If-Match" not in names


def test_no_request_body_accepts_status_or_ownership() -> None:
    """M3-D01/D02: status and attribution come from the server, not the client."""
    forbidden = {"status", "createdBy", "spaceId", "version", "id", "createdAt", "updatedAt"}
    for name in ("WishCreate", "WishUpdate"):
        schema = _components()[name]
        assert set(schema["properties"]) & forbidden == set()
        # Do not silently discard extra fields; otherwise a client could
        # believe that it successfully set the status.
        assert schema.get("additionalProperties") is False


def test_create_requires_only_a_title() -> None:
    schema = _components()["WishCreate"]
    assert set(schema["properties"]) == {"title"}
    assert schema["required"] == ["title"]


def test_update_offers_only_the_title() -> None:
    """There is no field through which PATCH could set the status."""
    assert set(_components()["WishUpdate"]["properties"]) == {"title"}


def test_detail_exposes_status_and_attribution_read_only() -> None:
    schema = _components()["WishDetail"]
    assert {"status", "createdBy", "creator", "capabilities"} <= set(schema["properties"])
    assert set(_components()["WishStatus"]["enum"]) == {"OPEN", "PLANNED", "COMPLETED"}


def test_detail_carries_no_wish_body() -> None:
    """A Wish has only a title in M3; `body` belongs to the Plan."""
    assert "body" not in _components()["WishDetail"]["properties"]


def test_list_filters_by_status_and_not_by_free_text() -> None:
    """Full-text search is M4-A and explicitly not part of M3."""
    parameters = {p["name"] for p in _paths()[COLLECTION]["get"].get("parameters", [])}
    assert {"status", "cursor", "limit"} <= parameters
    assert "q" not in parameters


def test_conflict_is_a_documented_answer_for_every_versioned_write() -> None:
    """For Wish, 409 means more than a version conflict.

    The M3-D05 delete matrix later uses the same status. Both cases must be in
    the contract or a client would treat the response as an unexpected error.
    """
    detail = _paths()[DETAIL]
    assert "409" in detail["patch"]["responses"]
    assert "409" in detail["delete"]["responses"]
