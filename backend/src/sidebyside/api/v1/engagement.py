"""HTTP contract for M4-B Activity, Notifications, and partner nudges."""

from __future__ import annotations

from datetime import datetime
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Path, Query, Response
from fastapi import status as http_status
from pydantic import ConfigDict

from sidebyside.api.deps import Authorization, DbSession
from sidebyside.api.errors import problem_responses
from sidebyside.api.schema import ApiModel
from sidebyside.engagement import service, thinking
from sidebyside.engagement.models import (
    Activity,
    ActivityKind,
    EngagementTarget,
    Notification,
    NotificationKind,
)

router = APIRouter(tags=["activity", "notifications"])


class ActivityItem(ApiModel):
    id: UUID
    source_event_id: UUID
    kind: ActivityKind
    actor_id: UUID | None
    target_type: EngagementTarget | None
    target_id: UUID | None
    occurred_at: datetime
    created_at: datetime


class ActivityPage(ApiModel):
    items: list[ActivityItem]
    next_cursor: str | None
    has_more: bool


class NotificationItem(ApiModel):
    id: UUID
    source_event_id: UUID
    kind: NotificationKind
    actor_id: UUID | None
    target_type: EngagementTarget | None
    target_id: UUID | None
    created_at: datetime
    read_at: datetime | None


class NotificationPage(ApiModel):
    items: list[NotificationItem]
    next_cursor: str | None
    has_more: bool


class NotificationUnreadCount(ApiModel):
    unread_count: int


class NotificationsReadAllResult(ApiModel):
    read_through: datetime
    updated: int


class ThinkingOfYouCreate(ApiModel):
    model_config = ConfigDict(extra="forbid")

    client_request_id: UUID


class ThinkingOfYouAccepted(ApiModel):
    client_request_id: UUID


@router.get(
    "/spaces/{spaceId}/activity",
    response_model=ActivityPage,
    operation_id="getActivity",
    responses=problem_responses(400, 401, 404, 422),
)
def get_activity(
    authorization: Authorization,
    session: DbSession,
    response: Response,
    cursor: Annotated[str | None, Query()] = None,
    limit: Annotated[int, Query(ge=1, le=service.MAX_LIMIT)] = service.DEFAULT_LIMIT,
) -> ActivityPage:
    page = service.read_activity(
        session,
        authorization,
        cursor=cursor,
        limit=limit,
    )
    response.headers["Cache-Control"] = "private, no-store"
    return ActivityPage(
        items=[_activity_item(item) for item in page.items],
        next_cursor=page.next_cursor,
        has_more=page.has_more,
    )


@router.get(
    "/spaces/{spaceId}/notifications",
    response_model=NotificationPage,
    operation_id="getNotifications",
    responses=problem_responses(400, 401, 404, 422),
)
def get_notifications(
    authorization: Authorization,
    session: DbSession,
    response: Response,
    cursor: Annotated[str | None, Query()] = None,
    limit: Annotated[int, Query(ge=1, le=service.MAX_LIMIT)] = service.DEFAULT_LIMIT,
) -> NotificationPage:
    page = service.read_notifications(
        session,
        authorization,
        cursor=cursor,
        limit=limit,
    )
    response.headers["Cache-Control"] = "private, no-store"
    return NotificationPage(
        items=[_notification_item(item) for item in page.items],
        next_cursor=page.next_cursor,
        has_more=page.has_more,
    )


@router.get(
    "/spaces/{spaceId}/notifications/unread-count",
    response_model=NotificationUnreadCount,
    operation_id="getNotificationUnreadCount",
    responses=problem_responses(401, 404, 422),
)
def get_notification_unread_count(
    authorization: Authorization,
    session: DbSession,
    response: Response,
) -> NotificationUnreadCount:
    response.headers["Cache-Control"] = "private, no-store"
    return NotificationUnreadCount(unread_count=service.unread_count(session, authorization))


@router.post(
    "/spaces/{spaceId}/notifications/{notificationId}/read",
    response_model=NotificationItem,
    operation_id="markNotificationRead",
    responses=problem_responses(401, 404, 422),
)
def mark_notification_read(
    authorization: Authorization,
    session: DbSession,
    response: Response,
    notification_id: Annotated[UUID, Path(alias="notificationId")],
) -> NotificationItem:
    notification = service.mark_notification_read(
        session,
        authorization,
        notification_id,
    )
    response.headers["Cache-Control"] = "private, no-store"
    return _notification_item(notification)


@router.post(
    "/spaces/{spaceId}/notifications/read-all",
    response_model=NotificationsReadAllResult,
    operation_id="markAllNotificationsRead",
    responses=problem_responses(401, 404, 422),
)
def mark_all_notifications_read(
    authorization: Authorization,
    session: DbSession,
    response: Response,
) -> NotificationsReadAllResult:
    result = service.mark_all_notifications_read(session, authorization)
    response.headers["Cache-Control"] = "private, no-store"
    return NotificationsReadAllResult(
        read_through=result.read_through,
        updated=result.updated,
    )


@router.post(
    "/spaces/{spaceId}/thinking-of-you",
    response_model=ThinkingOfYouAccepted,
    status_code=http_status.HTTP_202_ACCEPTED,
    operation_id="sendThinkingOfYou",
    responses=problem_responses(401, 404, 422, 429),
)
def send_thinking_of_you(
    authorization: Authorization,
    session: DbSession,
    response: Response,
    body: ThinkingOfYouCreate,
) -> ThinkingOfYouAccepted:
    request = thinking.send(
        session,
        authorization,
        client_request_id=body.client_request_id,
    )
    response.headers["Cache-Control"] = "private, no-store"
    return ThinkingOfYouAccepted(client_request_id=request.client_request_id)


def _activity_item(item: Activity) -> ActivityItem:
    return ActivityItem(
        id=item.id,
        source_event_id=item.source_event_id,
        kind=ActivityKind(item.kind),
        actor_id=item.actor_id,
        target_type=EngagementTarget(item.target_type) if item.target_type is not None else None,
        target_id=item.target_id,
        occurred_at=item.occurred_at,
        created_at=item.created_at,
    )


def _notification_item(item: Notification) -> NotificationItem:
    return NotificationItem(
        id=item.id,
        source_event_id=item.source_event_id,
        kind=NotificationKind(item.kind),
        actor_id=item.actor_id,
        target_type=EngagementTarget(item.target_type) if item.target_type is not None else None,
        target_id=item.target_id,
        created_at=item.created_at,
        read_at=item.read_at,
    )
