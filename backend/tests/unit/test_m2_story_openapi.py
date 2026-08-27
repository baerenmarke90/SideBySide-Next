"""The Story slice must mirror the contract approved in #70.

Story is the only M2 endpoint whose response is a union. If the contract
diverges here, no client notices at runtime; it simply receives no field it
expected.
"""

from __future__ import annotations

import json
from pathlib import Path

from sidebyside.main import create_app

TIMELINE = "/api/v1/spaces/{spaceId}/timeline"
CONTRACT = Path(__file__).parents[3] / "docs" / "m2" / "API-CONTRACT.json"


def _schema() -> dict[str, object]:
    return create_app().openapi()


def _operation() -> dict[str, object]:
    return _schema()["paths"][TIMELINE]["get"]  # type: ignore[index,return-value]


def test_route_and_operation_id_are_frozen() -> None:
    assert _operation()["operationId"] == "getStoryTimeline"


def test_query_matches_manifest() -> None:
    manifest = json.loads(CONTRACT.read_text(encoding="utf-8"))
    entry = next(
        operation
        for operation in manifest["operations"]
        if operation["operationId"] == "getStoryTimeline"
    )
    names = {
        parameter["name"]
        for parameter in _operation()["parameters"]  # type: ignore[index]
        if parameter["in"] == "query"
    }
    assert names == set(entry["query"])


def test_no_visibility_parameter() -> None:
    """M2-D22: Story has no owner mode, including as a filter."""
    names = {
        parameter["name"]
        for parameter in _operation()["parameters"]  # type: ignore[index]
    }
    assert "visibility" not in names


def test_no_q_parameter() -> None:
    """M2-D08 moved full-text search to M4-A."""
    names = {
        parameter["name"]
        for parameter in _operation()["parameters"]  # type: ignore[index]
    }
    assert "q" not in names


def test_union_is_named_story_item() -> None:
    """`API-DESIGN.md` gives the type this name, so the contract must name it.

    Without its own type, OpenAPI names the union after its location
    (`StoryPageItemsInner`), and every generated client carries that name into
    the Web and Android code.
    """
    schemas = _schema()["components"]["schemas"]  # type: ignore[index]
    assert schemas["StoryPage"]["properties"]["items"]["items"] == {
        "$ref": "#/components/schemas/StoryItem"
    }
    assert "StoryPageItemsInner" not in schemas


def test_union_is_discriminated_by_kind() -> None:
    schemas = _schema()["components"]["schemas"]  # type: ignore[index]
    discriminator = schemas["StoryItem"]["discriminator"]
    assert discriminator["propertyName"] == "kind"
    assert set(discriminator["mapping"]) == {"MEMORY", "HEART_MOMENT", "MILESTONE"}


def test_story_has_no_private_variant() -> None:
    """The union has three variants; there is no private HeartMoment form."""
    schemas = _schema()["components"]["schemas"]  # type: ignore[index]
    assert "visibility" not in schemas["SharedHeartMomentSummary"]["properties"]


def test_limit_and_year_have_contract_bounds() -> None:
    parameter = {
        entry["name"]: entry
        for entry in _operation()["parameters"]  # type: ignore[index]
    }
    assert parameter["limit"]["schema"]["default"] == 50
    assert parameter["limit"]["schema"]["maximum"] == 100
    year = parameter["year"]["schema"]
    bounds = year if "minimum" in year else next(o for o in year["anyOf"] if "minimum" in o)
    assert bounds["minimum"] == 1900
    assert bounds["maximum"] == 2100
