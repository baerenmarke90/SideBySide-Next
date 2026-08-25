"""Der implementierte HeartMoment-Slice muss den in #70 freigegebenen Vertrag spiegeln."""

from __future__ import annotations

from sidebyside.main import create_app

COLLECTION = "/api/v1/spaces/{spaceId}/heart-moments"
DETAIL = "/api/v1/spaces/{spaceId}/heart-moments/{heartMomentId}"
VISIBILITY = "/api/v1/spaces/{spaceId}/heart-moments/{heartMomentId}/visibility"


def _schema() -> dict[str, object]:
    return create_app().openapi()


def test_heart_moment_routes_have_frozen_operation_ids() -> None:
    paths = _schema()["paths"]  # type: ignore[index]

    assert paths[COLLECTION]["post"]["operationId"] == "createHeartMoment"
    assert paths[COLLECTION]["get"]["operationId"] == "listHeartMoments"
    assert paths[DETAIL]["get"]["operationId"] == "getHeartMoment"
    assert paths[DETAIL]["patch"]["operationId"] == "updateHeartMoment"
    assert paths[DETAIL]["delete"]["operationId"] == "deleteHeartMoment"
    assert paths[VISIBILITY]["patch"]["operationId"] == "changeHeartMomentVisibility"


def test_every_heart_moment_mutation_requires_if_match() -> None:
    paths = _schema()["paths"]  # type: ignore[index]
    for route, method in ((DETAIL, "patch"), (DETAIL, "delete"), (VISIBILITY, "patch")):
        parameters = paths[route][method]["parameters"]
        if_match = next(parameter for parameter in parameters if parameter["name"] == "If-Match")
        assert if_match["in"] == "header"
        assert if_match["required"] is True


def test_list_exposes_exactly_the_agreed_query_parameters() -> None:
    paths = _schema()["paths"]  # type: ignore[index]
    namen = {parameter["name"] for parameter in paths[COLLECTION]["get"]["parameters"]}
    assert {"cursor", "limit", "visibility"} <= namen
    # `year` gehoert zu Memory und Milestone, nicht zu HeartMoment.
    assert "year" not in namen
    assert "q" not in namen


def test_write_dtos_only_expose_approved_fields() -> None:
    components = _schema()["components"]["schemas"]  # type: ignore[index]

    create = components["HeartMomentCreate"]
    assert set(create["properties"]) == {
        "text",
        "emotion",
        "visibility",
        "happenedOn",
        "attachmentId",
    }
    assert set(create["required"]) == {"text", "emotion", "visibility", "happenedOn"}
    assert create["additionalProperties"] is False

    update = components["HeartMomentUpdate"]
    assert set(update["properties"]) == {"text", "emotion", "happenedOn", "attachmentId"}
    assert update["additionalProperties"] is False

    change = components["HeartMomentVisibilityChange"]
    assert set(change["properties"]) == {"visibility"}
    assert change["additionalProperties"] is False


def test_privacy_class_is_never_a_client_field() -> None:
    """`visibility` ist die einzige fachliche Clientwahrheit (M2-D09)."""
    components = _schema()["components"]["schemas"]  # type: ignore[index]
    for name in (
        "HeartMomentCreate",
        "HeartMomentUpdate",
        "HeartMomentVisibilityChange",
        "HeartMomentDetail",
    ):
        assert "privacyClass" not in components[name]["properties"]


def test_heart_moment_detail_projects_its_single_attachment() -> None:
    """Hoechstens eines (M2-D03) - deshalb ein Feld und keine Liste."""
    components = _schema()["components"]["schemas"]  # type: ignore[index]
    detail = components["HeartMomentDetail"]
    assert "attachment" in detail["properties"]
    assert "attachments" not in detail["properties"]
    assert {"id", "spaceId", "authorId", "text", "emotion", "visibility", "version"} <= set(
        detail["properties"]
    )
