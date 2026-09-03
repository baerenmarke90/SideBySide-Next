"""HTTP contract for the derived M4-A Dashboard."""

from __future__ import annotations

from datetime import date, datetime
from uuid import UUID

from fastapi import APIRouter, Response

from sidebyside.api.deps import Authorization, DbSession
from sidebyside.api.errors import problem_responses
from sidebyside.api.schema import ApiModel
from sidebyside.dashboard import service
from sidebyside.dashboard.service import DashboardItemType
from sidebyside.relationship.models import DurationDisplayMode

router = APIRouter(tags=["dashboard"])


class DashboardPartner(ApiModel):
    id: UUID
    display_name: str


class DashboardSpaceSummary(ApiModel):
    space_id: UUID
    partner: DashboardPartner | None


class DashboardRelationshipDuration(ApiModel):
    started_on: date
    days_together: int
    display_mode: DurationDisplayMode


class DashboardItem(ApiModel):
    type: DashboardItemType
    id: UUID
    title_or_text: str | None
    occurred_on: date | None
    scheduled_at: datetime | None
    created_at: datetime | None
    preview_attachment_id: UUID | None = None


class DashboardView(ApiModel):
    space: DashboardSpaceSummary
    relationship_duration: DashboardRelationshipDuration | None
    retrospective: DashboardItem | None
    upcoming: list[DashboardItem]
    recent_shared: list[DashboardItem]


@router.get(
    "/spaces/{spaceId}/dashboard",
    response_model=DashboardView,
    operation_id="getDashboard",
    responses=problem_responses(401, 404, 422),
)
def get_dashboard(
    authorization: Authorization,
    session: DbSession,
    response: Response,
) -> DashboardView:
    """Return the shared-only relationship overview for one Space."""
    view = service.read_dashboard(session, authorization)
    response.headers["Cache-Control"] = "private, no-store"
    return DashboardView(
        space=DashboardSpaceSummary(
            space_id=view.space_id,
            partner=(
                DashboardPartner(id=view.partner.id, display_name=view.partner.display_name)
                if view.partner is not None
                else None
            ),
        ),
        relationship_duration=(
            DashboardRelationshipDuration(
                started_on=view.relationship_duration.started_on,
                days_together=view.relationship_duration.days_together,
                display_mode=view.relationship_duration.display_mode,
            )
            if view.relationship_duration is not None
            else None
        ),
        retrospective=_project_item(view.retrospective) if view.retrospective is not None else None,
        upcoming=[_project_item(item) for item in view.upcoming],
        recent_shared=[_project_item(item) for item in view.recent_shared],
    )


def _project_item(item: service.DashboardItem) -> DashboardItem:
    return DashboardItem(
        type=item.type,
        id=item.id,
        title_or_text=item.title_or_text,
        occurred_on=item.occurred_on,
        scheduled_at=item.scheduled_at,
        created_at=item.created_at,
        preview_attachment_id=item.preview_attachment_id,
    )
