"""Write events to the outbox and claim them for delivery."""

from __future__ import annotations

from collections.abc import Sequence

from sqlalchemy import select
from sqlalchemy.orm import Session

from sidebyside.core.clock import now
from sidebyside.domain.events import DomainEvent
from sidebyside.outbox.models import OutboxEvent


def record(session: Session, event: DomainEvent) -> OutboxEvent:
    """Record an event for the current transaction.

    Deliberately does not commit: the event belongs in the same transaction as
    the domain mutation. Committing here would break that guarantee.
    """
    row = OutboxEvent(
        event_type=event.type.value,
        space_id=event.space_id,
        actor_id=event.actor_id,
        subject_type=event.subject_type,
        subject_id=event.subject_id,
        resource_version=event.resource_version,
        payload=event.payload,
    )
    session.add(row)
    return row


def claim_unprocessed(session: Session, limit: int = 50) -> Sequence[OutboxEvent]:
    """Claim unprocessed events for delivery.

    `FOR UPDATE SKIP LOCKED` ensures two workers never claim the same row and
    neither waits for the other. Without it, delivery would either duplicate
    or the second worker would block.
    """
    stmt = (
        select(OutboxEvent)
        .where(OutboxEvent.processed_at.is_(None))
        .order_by(OutboxEvent.created_at)
        .limit(limit)
        .with_for_update(skip_locked=True)
    )
    return session.execute(stmt).scalars().all()


def mark_processed(event: OutboxEvent) -> None:
    event.processed_at = now()
    event.last_error = None


def mark_failed(event: OutboxEvent, error: str) -> None:
    """Record a failed delivery without completing the row.

    `processed_at` remains empty so the event is retried. The message is
    truncated so an excessively long error cannot make the row unbounded.
    """
    event.attempts += 1
    event.last_error = error[:2000]
