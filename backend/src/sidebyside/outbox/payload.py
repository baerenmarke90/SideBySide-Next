"""Persistenztyp für die explizit erlaubte Outbox-Metadatenklasse."""

from __future__ import annotations

from typing import Any

from sqlalchemy.dialects import postgresql
from sqlalchemy.engine import Dialect
from sqlalchemy.types import TypeDecorator

from sidebyside.domain.events import PublicEventPayload


class PublicEventPayloadJSON(TypeDecorator[PublicEventPayload]):
    """Weist rohe Dictionaries auch bei direkter ORM-Nutzung ab."""

    impl = postgresql.JSONB
    cache_ok = True
    should_evaluate_none = True

    @property
    def python_type(self) -> type[PublicEventPayload]:
        return PublicEventPayload

    def process_bind_param(
        self, value: PublicEventPayload | None, dialect: Dialect
    ) -> dict[str, Any]:
        del dialect
        if type(value) is not PublicEventPayload:
            raise TypeError("PublicEventPayload erforderlich; rohe Outbox-Payload abgewiesen")
        return value.model_dump(mode="json", exclude_none=True)

    def process_result_value(
        self, value: dict[str, Any] | None, dialect: Dialect
    ) -> PublicEventPayload:
        del dialect
        if value is None:
            raise ValueError("Outbox-Payload fehlt in einer nicht-nullbaren Spalte")
        return PublicEventPayload.model_validate(value)
