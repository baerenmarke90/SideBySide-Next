"""Inhaltsfreier Notification-Hook fuer COMMENT_CREATED.

Kein Push-Provider in M2-S6. Diese Grenze uebersetzt eine Outbox-Zeile in
einen generischen Zustellauftrag. Die Outbox-ID ist der stabile
Idempotency-Key: falls der externe Versand erfolgreich war, aber der Worker
vor `mark_processed` stirbt, bekommt der Retry exakt denselben Schluessel.
"""

from __future__ import annotations

from typing import Protocol
from uuid import UUID

from sidebyside.domain.events import EventType
from sidebyside.outbox import service as outbox_service
from sidebyside.outbox.models import OutboxEvent


class CommentNotificationSink(Protocol):
    def send_comment_notification(
        self,
        *,
        idempotency_key: str,
        recipient_id: UUID,
        target_type: str,
        target_id: UUID,
    ) -> None: ...


def deliver(event: OutboxEvent, sink: CommentNotificationSink) -> bool:
    """Eine Comment-Notification zustellen, falls die Zeile dafuer bestimmt ist.

    Rueckgabe `False` bedeutet: anderes Event, nicht von diesem Consumer
    verarbeitet. Fehler des Sinks werden nicht verschluckt; der aufrufende
    Outbox-Worker markiert die Zeile dann als fehlgeschlagen und versucht sie
    spaeter mit derselben Event-ID erneut.
    """
    if event.event_type != EventType.COMMENT_CREATED.value:
        return False

    payload = event.payload
    if payload.recipient_id is None or payload.target_type is None or payload.target_id is None:
        raise ValueError("COMMENT_CREATED event is missing safe notification references")

    sink.send_comment_notification(
        idempotency_key=str(event.id),
        recipient_id=payload.recipient_id,
        target_type=payload.target_type,
        target_id=payload.target_id,
    )
    outbox_service.mark_processed(event)
    return True
