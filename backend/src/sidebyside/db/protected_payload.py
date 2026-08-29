"""SQLAlchemy persistence boundary for protected domain content."""

from __future__ import annotations

from typing import Any

from sqlalchemy.dialects import postgresql
from sqlalchemy.engine import Dialect
from sqlalchemy.types import TypeDecorator

from sidebyside.domain.payload import ProtectedPayload


class ProtectedPayloadJSON[PayloadT: ProtectedPayload](TypeDecorator[PayloadT]):
    """JSONB column bound exclusively to one concrete ProtectedPayload type.

    A raw dictionary therefore cannot accidentally be persisted as sensitive
    content. The concrete payload class is part of the column definition and
    restores strict Pydantic validation when reading.
    """

    impl = postgresql.JSONB
    cache_ok = True
    should_evaluate_none = True

    def __init__(self, payload_type: type[PayloadT]) -> None:
        super().__init__()
        self.payload_type = payload_type

    @property
    def python_type(self) -> type[PayloadT]:
        return self.payload_type

    def process_bind_param(self, value: PayloadT | None, dialect: Dialect) -> dict[str, Any]:
        del dialect
        if type(value) is not self.payload_type:
            raise TypeError(
                f"{self.payload_type.__name__} required; raw or foreign payload rejected"
            )
        return value.seal()

    def process_result_value(self, value: dict[str, Any] | None, dialect: Dialect) -> PayloadT:
        del dialect
        if value is None:
            raise ValueError("Protected payload is missing from a non-null persistence column")
        return self.payload_type.unseal(value)
