"""Der Attachment-Slice muss den in #70 freigegebenen Vertrag spiegeln."""

from __future__ import annotations

import json
from pathlib import Path

from sidebyside.main import create_app

COLLECTION = "/api/v1/spaces/{spaceId}/attachments"
DETAIL = "/api/v1/spaces/{spaceId}/attachments/{attachmentId}"
CONTENT = f"{DETAIL}/content"
FINALIZE = f"{DETAIL}/finalize"
READ_ACCESS = f"{DETAIL}/read-access"

CONTRACT = Path(__file__).parents[3] / "docs" / "m2" / "API-CONTRACT.json"


def _schema() -> dict[str, object]:
    return create_app().openapi()


def test_attachment_routes_have_frozen_operation_ids() -> None:
    paths = _schema()["paths"]  # type: ignore[index]
    assert paths[COLLECTION]["post"]["operationId"] == "createAttachmentUpload"
    assert paths[CONTENT]["put"]["operationId"] == "uploadAttachmentContent"
    assert paths[FINALIZE]["post"]["operationId"] == "finalizeAttachmentUpload"
    assert paths[DETAIL]["get"]["operationId"] == "getAttachment"
    assert paths[READ_ACCESS]["post"]["operationId"] == "createAttachmentReadAccess"
    assert paths[DETAIL]["delete"]["operationId"] == "deleteAttachment"


def test_delete_requires_if_match() -> None:
    parameters = _schema()["paths"][DETAIL]["delete"]["parameters"]  # type: ignore[index]
    if_match = next(parameter for parameter in parameters if parameter["name"] == "If-Match")
    assert if_match["in"] == "header"
    assert if_match["required"] is True


def test_the_detail_exposes_only_contracted_public_fields() -> None:
    schema = _schema()
    detail = schema["components"]["schemas"]["AttachmentDetail"]  # type: ignore[index]
    contract = json.loads(CONTRACT.read_text(encoding="utf-8"))

    erlaubt = set(contract["attachmentPublicFields"]) | {"hasThumbnail"}
    assert set(detail["properties"]) <= erlaubt
    assert set(contract["attachmentPublicFields"]) - {"durationSeconds"} <= set(
        detail["properties"]
    )


def test_storage_internals_are_not_fields_anywhere_in_the_schema() -> None:
    """Storage Keys, Buckets und Pfade sind keine Clientfelder.

    Geprueft werden Feldnamen, nicht der Rohtext: `privacyClass` kommt in
    Beschreibungen vor - und zwar genau dort, wo steht, dass es keines ist.
    """
    components = _schema()["components"]["schemas"]  # type: ignore[index]
    contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
    verboten = set(contract["attachmentForbiddenClientFields"])

    for name, definition in components.items():
        felder = set(definition.get("properties") or {})
        ueberschneidung = felder & verboten
        assert not ueberschneidung, f"{name}: {sorted(ueberschneidung)}"


def test_read_request_accepts_the_unbound_variant() -> None:
    """M2-D24."""
    components = _schema()["components"]["schemas"]  # type: ignore[index]
    request = components["AttachmentReadRequest"]
    parent_type = request["properties"]["parentType"]
    werte = set(parent_type.get("enum") or [])
    assert werte == {"MEMORY", "HEART_MOMENT", "NONE"}
    assert request["additionalProperties"] is False


def test_the_manifest_lists_the_same_variants() -> None:
    contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
    varianten = {eintrag["parentType"] for eintrag in contract["attachmentReadRequestVariants"]}
    assert varianten == {"MEMORY", "HEART_MOMENT", "NONE"}
    ungebunden = next(
        eintrag
        for eintrag in contract["attachmentReadRequestVariants"]
        if eintrag["parentType"] == "NONE"
    )
    assert ungebunden["requiresParentId"] is False


def test_upload_create_only_accepts_the_contracted_fields() -> None:
    components = _schema()["components"]["schemas"]  # type: ignore[index]
    contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
    create = components["AttachmentUploadCreate"]
    assert set(create["properties"]) == set(contract["clientWriteFields"]["AttachmentUploadCreate"])
    assert create["additionalProperties"] is False
