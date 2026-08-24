"""Outbox-Ereignisse dürfen nur explizit freigegebene Metadaten tragen."""

from __future__ import annotations

import pytest
from pydantic import ValidationError
from sqlalchemy.dialects import postgresql

from sidebyside.core.ids import new_id
from sidebyside.domain.events import DomainEvent, EventType, PublicEventPayload
from sidebyside.domain.payload import ProtectedPayload
from sidebyside.outbox.payload import PublicEventPayloadJSON


class PrivateContent(ProtectedPayload):
    title: str
    body: str


class SneakyEventPayload(PublicEventPayload):
    body: str


def _event(payload: object) -> DomainEvent:
    return DomainEvent.model_validate(
        {
            "type": EventType.MEMORY_CREATED,
            "space_id": new_id(),
            "subject_type": "memory",
            "subject_id": new_id(),
            "payload": payload,
        }
    )


def test_erlaubte_metadaten_sind_typisiert() -> None:
    event = _event({"has_attachment": True})
    assert event.payload == PublicEventPayload(has_attachment=True)


@pytest.mark.parametrize("field", ["title", "body", "text", "content", "location"])
def test_unbekannte_klartextfelder_werden_abgewiesen(field: str) -> None:
    with pytest.raises(ValidationError):
        _event({field: "privater Klartext"})


def test_protected_payload_kann_nicht_outbox_payload_werden() -> None:
    with pytest.raises(ValidationError):
        _event(PrivateContent(title="Überraschung", body="Geheim"))


def test_rohes_dictionary_wird_auch_an_outbox_db_grenze_abgewiesen() -> None:
    storage = PublicEventPayloadJSON()
    with pytest.raises(TypeError, match="PublicEventPayload erforderlich"):
        storage.process_bind_param(  # type: ignore[arg-type]
            {"body": "privater Klartext"}, postgresql.dialect()
        )


def test_erweiterte_payload_unterklasse_umgeht_allowlist_nicht() -> None:
    storage = PublicEventPayloadJSON()
    with pytest.raises(TypeError, match="PublicEventPayload erforderlich"):
        storage.process_bind_param(
            SneakyEventPayload(body="privater Klartext"), postgresql.dialect()
        )
