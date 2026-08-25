"""Ereignisse in die Outbox schreiben und wieder herausholen."""

from __future__ import annotations

from collections.abc import Sequence

from sqlalchemy import select
from sqlalchemy.orm import Session

from sidebyside.core.clock import now
from sidebyside.domain.events import DomainEvent
from sidebyside.outbox.models import OutboxEvent


def record(session: Session, event: DomainEvent) -> OutboxEvent:
    """Ein Ereignis vormerken.

    Bewusst ohne Commit: das Ereignis gehört in dieselbe Transaktion wie die
    fachliche Änderung. Wer hier committet, hebt die Garantie auf.
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
    """Unverarbeitete Ereignisse zur Zustellung greifen.

    `FOR UPDATE SKIP LOCKED`: zwei Worker greifen nie dieselbe Zeile, und
    keiner wartet auf den anderen. Ohne das würde entweder doppelt
    zugestellt oder der zweite Worker blockiert.
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
    """Fehlschlag vermerken, ohne die Zeile abzuschließen.

    `processed_at` bleibt leer, das Ereignis wird erneut versucht. Die
    Meldung wird gekürzt, damit ein ausufernder Fehlertext die Zeile nicht
    sprengt.
    """
    event.attempts += 1
    event.last_error = error[:2000]
