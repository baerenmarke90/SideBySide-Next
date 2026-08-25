"""Der implementierte Memory-Slice muss den in #70 freigegebenen Vertrag spiegeln."""

from __future__ import annotations

from sidebyside.main import create_app


def _schema() -> dict[str, object]:
    return create_app().openapi()


def test_memory_routes_have_frozen_operation_ids() -> None:
    schema = _schema()
    paths = schema["paths"]  # type: ignore[index]
    collection = paths["/api/v1/spaces/{spaceId}/memories"]  # type: ignore[index]
    detail = paths["/api/v1/spaces/{spaceId}/memories/{memoryId}"]  # type: ignore[index]

    assert collection["post"]["operationId"] == "createMemory"
    assert collection["get"]["operationId"] == "listMemories"
    assert detail["get"]["operationId"] == "getMemory"
    assert detail["patch"]["operationId"] == "updateMemory"
    assert detail["delete"]["operationId"] == "deleteMemory"


def test_memory_mutations_require_if_match() -> None:
    schema = _schema()
    detail = schema["paths"][  # type: ignore[index]
        "/api/v1/spaces/{spaceId}/memories/{memoryId}"
    ]
    for method in ("patch", "delete"):
        parameters = detail[method]["parameters"]
        if_match = next(parameter for parameter in parameters if parameter["name"] == "If-Match")
        assert if_match["in"] == "header"
        assert if_match["required"] is True


def test_memory_write_dtos_only_expose_approved_fields() -> None:
    schema = _schema()
    components = schema["components"]["schemas"]  # type: ignore[index]

    create = components["MemoryCreate"]
    update = components["MemoryUpdate"]
    assert set(create["properties"]) == {"title", "body", "happenedOn"}
    assert set(create["required"]) == {"title", "body"}
    assert create["additionalProperties"] is False
    assert set(update["properties"]) == {"title", "body", "happenedOn"}
    assert update["additionalProperties"] is False


def test_media_free_memory_detail_does_not_pretend_attachments_exist() -> None:
    schema = _schema()
    detail = schema["components"]["schemas"]["MemoryDetail"]  # type: ignore[index]
    assert "attachments" not in detail["properties"]
    assert {"id", "spaceId", "authorId", "title", "body", "version", "capabilities"} <= set(
        detail["properties"]
    )
