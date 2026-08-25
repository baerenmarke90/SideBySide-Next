"""Der Milestone-Slice muss den in #70 freigegebenen Vertrag spiegeln."""

from __future__ import annotations

import json
from pathlib import Path

from sidebyside.main import create_app

COLLECTION = "/api/v1/spaces/{spaceId}/milestones"
DETAIL = "/api/v1/spaces/{spaceId}/milestones/{milestoneId}"
CONTRACT = Path(__file__).parents[3] / "docs" / "m2" / "API-CONTRACT.json"


def _schema() -> dict[str, object]:
    return create_app().openapi()


def test_milestone_routes_have_frozen_operation_ids() -> None:
    paths = _schema()["paths"]  # type: ignore[index]
    assert paths[COLLECTION]["post"]["operationId"] == "createMilestone"
    assert paths[COLLECTION]["get"]["operationId"] == "listMilestones"
    assert paths[DETAIL]["get"]["operationId"] == "getMilestone"
    assert paths[DETAIL]["patch"]["operationId"] == "updateMilestone"
    assert paths[DETAIL]["delete"]["operationId"] == "deleteMilestone"


def test_mutations_require_if_match() -> None:
    detail = _schema()["paths"][DETAIL]  # type: ignore[index]
    for method in ("patch", "delete"):
        parameters = detail[method]["parameters"]
        if_match = next(parameter for parameter in parameters if parameter["name"] == "If-Match")
        assert if_match["required"] is True


def test_write_dtos_match_the_contract() -> None:
    components = _schema()["components"]["schemas"]  # type: ignore[index]
    contract = json.loads(CONTRACT.read_text(encoding="utf-8"))

    create = components["MilestoneCreate"]
    assert set(create["properties"]) == set(contract["clientWriteFields"]["MilestoneCreate"])
    # Titel und Datum sind Pflicht, der Body nicht.
    assert set(create["required"]) == {"title", "happenedOn"}
    assert create["additionalProperties"] is False

    update = components["MilestoneUpdate"]
    assert set(update["properties"]) == set(contract["clientWriteFields"]["MilestoneUpdate"])
    assert update["additionalProperties"] is False


def test_list_exposes_the_agreed_query_parameters() -> None:
    namen = {
        parameter["name"]
        for parameter in _schema()["paths"][COLLECTION]["get"]["parameters"]  # type: ignore[index]
    }
    assert {"cursor", "limit", "year"} <= namen
    assert "q" not in namen


def test_privacy_class_is_never_a_client_field() -> None:
    components = _schema()["components"]["schemas"]  # type: ignore[index]
    for name in ("MilestoneCreate", "MilestoneUpdate", "MilestoneDetail"):
        assert "privacyClass" not in components[name]["properties"]


def test_milestone_detail_does_not_pretend_attachments_exist() -> None:
    """Abschnitt 12 der Media-Pipeline: fuer Milestone in M2 nicht vorgesehen."""
    detail = _schema()["components"]["schemas"]["MilestoneDetail"]  # type: ignore[index]
    assert "attachments" not in detail["properties"]
    assert "attachment" not in detail["properties"]
