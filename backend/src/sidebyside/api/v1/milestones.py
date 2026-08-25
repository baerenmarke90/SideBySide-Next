"""HTTP-Vertrag fuer M2-Milestones."""

from __future__ import annotations

from datetime import date, datetime
from typing import Annotated, Self
from uuid import UUID

from fastapi import APIRouter, Path, Query, Response, status
from pydantic import ConfigDict, field_validator, model_validator

from sidebyside.api.concurrency import IfMatchVersion, etag_for
from sidebyside.api.deps import Authorization, DbSession
from sidebyside.api.errors import problem_responses
from sidebyside.api.schema import ApiModel, AuthorSummary, ResourceCapabilities
from sidebyside.identity.models import Account
from sidebyside.milestones import service
from sidebyside.milestones.models import Milestone

router = APIRouter(tags=["milestones"])

ETAG_HEADERS = {
    "ETag": {
        "description": "Version der Ressource fuer den naechsten If-Match-Schreibzugriff.",
        "schema": {"type": "string"},
    }
}


class MilestoneCreate(ApiModel):
    model_config = ConfigDict(extra="forbid")

    title: str
    body: str | None = None
    happened_on: date

    @field_validator("title")
    @classmethod
    def _title_not_blank(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("must not be blank")
        return cleaned


class MilestoneUpdate(ApiModel):
    model_config = ConfigDict(extra="forbid")

    title: str | None = None
    body: str | None = None
    happened_on: date | None = None

    @model_validator(mode="after")
    def _validate_patch(self) -> Self:
        if not self.model_fields_set:
            raise ValueError("at least one field must be supplied")
        if "title" in self.model_fields_set:
            if self.title is None or not self.title.strip():
                raise ValueError("title must not be null or blank")
            self.title = self.title.strip()
        if "happened_on" in self.model_fields_set and self.happened_on is None:
            raise ValueError("happenedOn must not be null")
        return self


class MilestoneDetail(ApiModel):
    id: UUID
    space_id: UUID
    author_id: UUID
    title: str
    body: str | None
    happened_on: date
    version: int
    created_at: datetime
    updated_at: datetime
    author: AuthorSummary
    capabilities: ResourceCapabilities


class MilestonePage(ApiModel):
    items: list[MilestoneDetail]
    next_cursor: str | None
    has_more: bool


def _milestone_detail(
    session: DbSession,
    authorization: Authorization,
    milestone: Milestone,
) -> MilestoneDetail:
    author = session.get(Account, milestone.owner_id)
    if author is None:
        raise RuntimeError("Milestone author disappeared despite foreign key protection.")
    is_author = milestone.owner_id == authorization.account_id
    return MilestoneDetail(
        id=milestone.id,
        space_id=milestone.space_id,
        author_id=milestone.owner_id,
        title=milestone.payload.title,
        body=milestone.payload.body,
        happened_on=milestone.happened_on,
        version=milestone.version,
        created_at=milestone.created_at,
        updated_at=milestone.updated_at,
        author=AuthorSummary(id=author.id, display_name=author.display_name),
        capabilities=ResourceCapabilities(
            can_edit=is_author,
            can_delete=is_author,
            can_comment=True,
        ),
    )
