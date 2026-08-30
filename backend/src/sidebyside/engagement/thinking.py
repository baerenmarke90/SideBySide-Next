"""Content-free `Ich denke an dich` command and projection helper."""

from __future__ import annotations

from datetime import timedelta
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.dialects import postgresql
from sqlalchemy.orm import Session

from sidebyside.authorization import AuthorizationContext
from sidebyside.core import clock
from sidebyside.core.errors import NotFoundError, RateLimitedError
from sidebyside.core.ids import new_id
from sidebyside.domain.events import DomainEvent, EventType, PublicEventPayload
from sidebyside.engagement.models import (
    Notification,
    NotificationKind,
    ThinkingOfYouRequest,
)
from sidebyside.outbox import service as outbox_service
from sidebyside.outbox.models import OutboxEvent
from sidebyside.relationship.models import Membership, MembershipStatus

COOLDOWN_SECONDS = 60
PARTNER_NOT_AVAILABLE = "PARTNER_NOT_AVAILABLE"
THINKING_OF_YOU_COOLDOWN = "THINKING_OF_YOU_COOLDOWN"


def send(
    session: Session,
    context: AuthorizationContext,
    *,
    client_request_id: UUID,
) -> ThinkingOfYouRequest:
    """Accept one idempotent content-free partner nudge."""
    existing = _existing_request(session, context, client_request_id)
    if existing is not None:
        return existing

    # Serialize new signals for one sender/Space so concurrent request IDs
    # cannot both pass the rolling cooldown check.
    sender_membership = session.execute(
        select(Membership)
        .where(
            Membership.space_id == context.space_id,
            Membership.account_id == context.account_id,
            Membership.status == MembershipStatus.ACTIVE.value,
        )
        .with_for_update()
    ).scalar_one_or_none()
    if sender_membership is None:
        raise NotFoundError("Partner space not available.", PARTNER_NOT_AVAILABLE)

    existing = _existing_request(session, context, client_request_id)
    if existing is not None:
        return existing

    recipient_id = session.execute(
        select(Membership.account_id)
        .where(
            Membership.space_id == context.space_id,
            Membership.status == MembershipStatus.ACTIVE.value,
            Membership.account_id != context.account_id,
        )
        .order_by(Membership.account_id)
        .limit(1)
    ).scalar_one_or_none()
    if recipient_id is None:
        raise NotFoundError("Partner not available.", PARTNER_NOT_AVAILABLE)

    current_time = clock.now()
    recent = session.execute(
        select(ThinkingOfYouRequest.id)
        .where(
            ThinkingOfYouRequest.space_id == context.space_id,
            ThinkingOfYouRequest.sender_account_id == context.account_id,
            ThinkingOfYouRequest.created_at
            > current_time - timedelta(seconds=COOLDOWN_SECONDS),
        )
        .order_by(ThinkingOfYouRequest.created_at.desc())
        .limit(1)
    ).scalar_one_or_none()
    if recent is not None:
        raise RateLimitedError(
            "Thinking-of-you is temporarily rate limited.",
            THINKING_OF_YOU_COOLDOWN,
        )

    request_id = new_id()
    event = outbox_service.record(
        session,
        DomainEvent(
            type=EventType.PARTNER_THINKING_OF_YOU,
            space_id=context.space_id,
            actor_id=context.account_id,
            subject_type="thinking_of_you",
            subject_id=request_id,
            payload=PublicEventPayload(recipient_id=recipient_id),
        ),
    )
    session.flush()

    request = ThinkingOfYouRequest(
        id=request_id,
        space_id=context.space_id,
        sender_account_id=context.account_id,
        recipient_account_id=recipient_id,
        client_request_id=client_request_id,
        source_event_id=event.id,
        created_at=current_time,
    )
    session.add(request)
    session.flush()
    return request


def project_notification(session: Session, event: OutboxEvent) -> None:
    """Project the safe signal event into one recipient Notification."""
    recipient_id = event.payload.recipient_id
    if recipient_id is None or recipient_id == event.actor_id:
        return

    active_recipient = session.execute(
        select(Membership.account_id).where(
            Membership.space_id == event.space_id,
            Membership.account_id == recipient_id,
            Membership.status == MembershipStatus.ACTIVE.value,
        )
    ).scalar_one_or_none()
    if active_recipient is None:
        return

    statement = (
        postgresql.insert(Notification)
        .values(
            space_id=event.space_id,
            recipient_account_id=recipient_id,
            source_event_id=event.id,
            kind=NotificationKind.THINKING_OF_YOU.value,
            actor_id=event.actor_id,
            target_type=None,
            target_id=None,
            created_at=event.created_at,
        )
        .on_conflict_do_nothing(
            index_elements=["recipient_account_id", "source_event_id", "kind"]
        )
    )
    session.execute(statement)


def _existing_request(
    session: Session,
    context: AuthorizationContext,
    client_request_id: UUID,
) -> ThinkingOfYouRequest | None:
    return session.execute(
        select(ThinkingOfYouRequest).where(
            ThinkingOfYouRequest.space_id == context.space_id,
            ThinkingOfYouRequest.sender_account_id == context.account_id,
            ThinkingOfYouRequest.client_request_id == client_request_id,
        )
    ).scalar_one_or_none()
