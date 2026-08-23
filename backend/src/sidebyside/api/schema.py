"""Serialisierungsgrenze.

Nach außen camelCase, intern snake_case. Die Umsetzung geschieht hier und
nicht durch Umbenennen im Domain-Code - sonst trägt die Fachlogik eine
Darstellungsentscheidung mit sich herum.
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict


def to_camel(value: str) -> str:
    kopf, *rest = value.split("_")
    return kopf + "".join(teil.capitalize() for teil in rest)


class ApiModel(BaseModel):
    """Basis aller Modelle, die die API verlassen oder betreten."""

    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
        from_attributes=True,
    )
