"""HTTP contract for the derived M4-A Dashboard."""

from __future__ import annotations

from datetime import date, datetime
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Path, Response
from pydantic import ConfigDict

from sidebyside.api.deps import Authorization, DbSession
from sidebyside.api.errors import problem_responses
from sidebyside.api.schema import ApiModel
from sidebyside.dashboard import preferences, service
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
    keepsake: DashboardItem | None
    upcoming: list[DashboardItem]
    recent_shared: list[DashboardItem]
    thinking_of_you_available_at: datetime | None


class DashboardModulePreferenceUpdate(ApiModel):
    model_config = ConfigDict(extra="forbid")

    item_limit: preferences.DashboardItemLimit


class DashboardModulePreferenceView(ApiModel):
    module_key: str
    item_limit: preferences.DashboardItemLimit


class DashboardModulePreferenceList(ApiModel):
    items: list[DashboardModulePreferenceView]


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
        keepsake=_project_item(view.keepsake) if view.keepsake is not None else None,
        upcoming=[_project_item(item) for item in view.upcoming],
        recent_shared=[_project_item(item) for item in view.recent_shared],
        thinking_of_you_available_at=view.thinking_of_you_available_at,
    )


@router.get(
    "/spaces/{spaceId}/dashboard/preferences",
    response_model=DashboardModulePreferenceList,
    operation_id="listDashboardModulePreferences",
    responses=problem_responses(401, 404),
)
def list_dashboard_module_preferences(
    authorization: Authorization,
    session: DbSession,
    response: Response,
) -> DashboardModulePreferenceList:
    """Return the current account's effective Dashboard preferences."""
    states = preferences.read_module_preferences(
        session,
        account_id=authorization.account_id,
        space_id=authorization.space_id,
    )
    response.headers["Cache-Control"] = "private, no-store"
    return DashboardModulePreferenceList(
        items=[
            DashboardModulePreferenceView(
                module_key=state.key.value,
                item_limit=state.item_limit,
            )
            for state in states
        ]
    )


@router.patch(
    "/spaces/{spaceId}/dashboard/preferences/{moduleKey}",
    response_model=DashboardModulePreferenceView,
    operation_id="updateDashboardModulePreference",
    responses=problem_responses(401, 404, 422),
)
def update_dashboard_module_preference(
    authorization: Authorization,
    session: DbSession,
    response: Response,
    body: DashboardModulePreferenceUpdate,
    module_key: Annotated[str, Path(alias="moduleKey")],
) -> DashboardModulePreferenceView:
    """Set one private per-account Dashboard item-limit override."""
    state = preferences.set_module_item_limit(
        session,
        account_id=authorization.account_id,
        space_id=authorization.space_id,
        module_key=module_key,
        item_limit=body.item_limit,
    )
    response.headers["Cache-Control"] = "private, no-store"
    return DashboardModulePreferenceView(
        module_key=state.key.value,
        item_limit=state.item_limit,
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
