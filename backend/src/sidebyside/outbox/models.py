"""Transactional Outbox.

Fachliche Änderung und Ereignis werden in einer Transaktion geschrieben:

    BEGIN
      INSERT/UPDATE  Domain-Objekt
      INSERT         outbox_event
    COMMIT

Damit kann kein Ereignis verlorengehen, weil die Zustellung nach dem Commit
scheiterte, und keine Benachrichtigung zu einer Änderung entstehen, die
zurückgerollt wurde. Ein Worker liest die Tabelle und stellt zu.
"""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from sqlalchemy import CheckConstraint, DateTime, Index, Integer, String, Text, func
from sqlalchemy.dialects import postgresql
from sqlalchemy.orm import Mapped, mapped_column

from sidebyside.db.base import Base
from sidebyside.db.mixins import IdMixin
from sidebyside.domain.events import PublicEventPayload
from sidebyside.outbox.payload import PublicEventPayloadJSON


class OutboxEvent(IdMixin, Base):
    __tablename__ = "outbox_events"

    event_type: Mapped[str] = mapped_column(String(64), nullable=False)
    space_id: Mapped[UUID] = mapped_column(postgresql.UUID(as_uuid=True), nullable=False)
    actor_id: Mapped[UUID | None] = mapped_column(postgresql.UUID(as_uuid=True))
    subject_type: Mapped[str] = mapped_column(String(64), nullable=False)
    subject_id: Mapped[UUID] = mapped_column(postgresql.UUID(as_uuid=True), nullable=False)
    # M2-D16: letzte/neue Ressourcen-Version im sicheren Envelope. Historische
    # Nicht-M2-Ereignisse duerfen NULL bleiben.
    resource_version: Mapped[int | None] = mapped_column(Integer)

    # Nur Verweise und unkritische Merkmale - siehe domain/events.py.
    payload: Mapped[PublicEventPayload] = mapped_column(
        PublicEventPayloadJSON(), nullable=False, default=PublicEventPayload
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    processed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    attempts: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    last_error: Mapped[str | None] = mapped_column(Text)

    __table_args__ = (
        CheckConstraint(
            "resource_version IS NULL OR resource_version >= 1",
            name="resource_version_is_positive",
        ),
        # Der Worker sucht ausschließlich unverarbeitete Zeilen. Ein
        # Teilindex haelt ihn klein, auch wenn die Tabelle waechst.
        Index(
            "ix_outbox_events_unprocessed",
            "created_at",
            postgresql_where=processed_at.is_(None),
        ),
    )