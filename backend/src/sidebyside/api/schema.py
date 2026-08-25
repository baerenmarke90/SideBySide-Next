"""Serialisierungsgrenze.

Nach außen camelCase, intern snake_case. Die Umsetzung geschieht hier und
nicht durch Umbenennen im Domain-Code - sonst trägt die Fachlogik eine
Darstellungsentscheidung mit sich herum.
"""

from __future__ import annotations

from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field
from pydantic.json_schema import SkipJsonSchema


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


class AuthorSummary(ApiModel):
    """Gemeinsame Autorprojektion fuer M2-Ressourcen."""

    id: UUID
    display_name: str
    profile_attachment_id: UUID | SkipJsonSchema[None] = Field(
        default=None,
        exclude_if=lambda value: value is None,
    )


class ResourceCapabilities(ApiModel):
    """UX-Hinweise; die Autorisierung bleibt serverseitig massgeblich."""

    can_edit: bool
    can_delete: bool
    can_comment: bool
