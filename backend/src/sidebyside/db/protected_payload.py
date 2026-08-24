"""SQLAlchemy-Persistenzgrenze für schützenswerte Fachinhalte."""

from __future__ import annotations

from typing import Any

from sqlalchemy.dialects import postgresql
from sqlalchemy.engine import Dialect
from sqlalchemy.types import TypeDecorator

from sidebyside.domain.payload import ProtectedPayload


class ProtectedPayloadJSON[PayloadT: ProtectedPayload](TypeDecorator[PayloadT]):
    """JSONB-Spalte, die ausschließlich einen konkreten ProtectedPayload bindet.

    Ein rohes Dictionary kann damit nicht versehentlich als sensibler Inhalt
    persistiert werden. Die konkrete Payload-Klasse ist Teil der Spaltendefinition
    und übernimmt beim Lesen wieder die strikte Pydantic-Validierung.
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
                f"{self.payload_type.__name__} erforderlich; rohe oder fremde Payload abgewiesen"
            )
        return value.seal()

    def process_result_value(self, value: dict[str, Any] | None, dialect: Dialect) -> PayloadT:
        del dialect
        if value is None:
            raise ValueError("Geschützte Payload fehlt in einer nicht-nullbaren Persistenzspalte")
        return self.payload_type.unseal(value)
