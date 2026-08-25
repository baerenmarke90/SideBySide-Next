"""Die Bindung zwischen Attachment und Domainressource.

M2-D03 verlangt exklusive Ownership: ein Attachment gehoert hoechstens
einem Parent. Diese Regel steht bewusst an genau einer Stelle - hier - und
nicht in jeder Domaene, die Attachments verwendet.

Es gibt keine denormalisierte Parentspalte am Attachment. Sie waere eine
zweite Wahrheit neben den Relationen und koennte von ihnen abweichen; die
Frage "ist das gebunden?" wird stattdessen gegen die Relationen gestellt.
"""

from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID

from sqlalchemy import ForeignKey, Index, Integer, UniqueConstraint, select
from sqlalchemy.dialects import postgresql
from sqlalchemy.orm import Mapped, Session, mapped_column

from sidebyside.attachments.models import Attachment, AttachmentStatus
from sidebyside.attachments.service import binding_window_expired
from sidebyside.core.errors import ConflictError, ErrorCode
from sidebyside.db.base import Base
from sidebyside.db.mixins import IdMixin

MAX_MEMORY_ATTACHMENTS = 20
MAX_MEMORY_TOTAL_SIZE = 500 * 1024 * 1024
"""M2-D04: Kardinalitaet und Gesamtgroesse je Memory."""


class MemoryAttachment(IdMixin, Base):
    """Ein Attachment an seinem Platz in einer Memory.

    `position` ist nullbasiert und je Memory eindeutig. Die Datenbank haelt
    beides fest, damit eine Reihenfolge nicht davon abhaengt, dass die
    Fachlogik korrekt zaehlt.
    """

    __tablename__ = "memory_attachments"

    memory_id: Mapped[UUID] = mapped_column(
        postgresql.UUID(as_uuid=True),
        ForeignKey("memories.id", ondelete="CASCADE"),
        nullable=False,
    )
    attachment_id: Mapped[UUID] = mapped_column(
        postgresql.UUID(as_uuid=True),
        ForeignKey("attachments.id", ondelete="CASCADE"),
        nullable=False,
    )
    position: Mapped[int] = mapped_column(Integer, nullable=False)

    __table_args__ = (
        # Exklusive Bindung, soweit die Datenbank sie allein tragen kann:
        # dasselbe Attachment nicht zweimal und nicht in zwei Memories.
        UniqueConstraint("attachment_id", name="uq_memory_attachments_attachment"),
        UniqueConstraint("memory_id", "position", name="uq_memory_attachments_position"),
        Index("ix_memory_attachments_memory_id", "memory_id"),
    )


@dataclass(frozen=True)
class BoundAttachment:
    attachment: Attachment
    position: int


def _conflict(message: str, code: str) -> ConflictError:
    return ConflictError(message, code)


def lock_for_binding(session: Session, attachment_ids: list[UUID]) -> dict[UUID, Attachment]:
    """Die Kandidaten sperren, bevor ihr Zustand gelesen wird.

    Ohne die Sperre koennte der Cleanup zwischen Pruefung und Bindung genau
    das Attachment abraeumen, das gerade gebunden wird - und dann zeigte die
    Relation auf eine geloeschte Datei. Die Sperre serialisiert beide:
    entweder gewinnt Bind vollstaendig oder Cleanup.
    """
    if not attachment_ids:
        return {}
    zeilen = session.execute(
        select(Attachment).where(Attachment.id.in_(attachment_ids)).with_for_update()
    ).scalars()
    return {zeile.id: zeile for zeile in zeilen}


def ensure_bindable(
    attachment: Attachment | None,
    *,
    space_id: UUID,
    account_id: UUID,
) -> Attachment:
    """Darf dieses Attachment jetzt gebunden werden?

    Alle Ablehnungen ausser der Kardinalitaet laufen hier zusammen, damit
    keine Domaene eine eigene Teilmenge der Regeln formuliert.
    """
    if attachment is None or attachment.space_id != space_id:
        # Cross-Space und unbekannt enden gleich: die Existenz eines
        # fremden Attachments ist selbst schon eine Auskunft.
        raise Attachment.privacy_absence.error()
    if attachment.owner_id != account_id:
        raise Attachment.privacy_absence.error()
    if attachment.status != AttachmentStatus.READY.value:
        raise _conflict("The attachment is not ready.", ErrorCode.ATTACHMENT_NOT_READY)
    if binding_window_expired(attachment):
        raise _conflict("The attachment is not ready.", ErrorCode.ATTACHMENT_NOT_READY)
    return attachment


def parent_of(session: Session, attachment_id: UUID) -> tuple[str, UUID] | None:
    """Woran das Attachment haengt - oder nichts.

    Fragt die Relationen und nicht eine gespiegelte Spalte. Eine zweite
    Wahrheit koennte von der ersten abweichen, und dann entschiede die
    falsche ueber die Sichtbarkeit.
    """
    from sidebyside.heart_moments.models import HeartMoment

    memory_id = session.execute(
        select(MemoryAttachment.memory_id).where(MemoryAttachment.attachment_id == attachment_id)
    ).scalar_one_or_none()
    if memory_id is not None:
        return "MEMORY", memory_id

    heart_moment_id = session.execute(
        select(HeartMoment.id).where(HeartMoment.attachment_id == attachment_id)
    ).scalar_one_or_none()
    if heart_moment_id is not None:
        return "HEART_MOMENT", heart_moment_id
    return None


def ensure_unlinked(
    session: Session, attachment_id: UUID, *, allow: tuple[str, UUID] | None = None
) -> None:
    """Exklusivitaet ueber beide Parenttypen hinweg (M2-D03).

    Die Unique Constraints halten je Tabelle fest, dass ein Attachment
    nicht zweimal vorkommt. Dass es nicht *gleichzeitig* an einer Memory
    und einem HeartMoment haengt, kann keine einzelne Tabelle wissen -
    diese Pruefung laeuft deshalb unter der Sperre aus `lock_for_binding`.

    `allow` nennt die Bindung, die erhalten bleiben darf: beim Neusetzen
    einer Memory-Menge bleibt ein bereits dort gebundenes Attachment
    gebunden und ist kein Konflikt.
    """
    vorhanden = parent_of(session, attachment_id)
    if vorhanden is None or vorhanden == allow:
        return
    raise _conflict(
        "The attachment already belongs to another resource.",
        ErrorCode.ATTACHMENT_ALREADY_LINKED,
    )


def ensure_within_limits(attachments: list[Attachment]) -> None:
    if len(attachments) > MAX_MEMORY_ATTACHMENTS:
        raise _conflict(
            "The parent exceeds its attachment limit.",
            ErrorCode.ATTACHMENT_LIMIT_EXCEEDED,
        )
    gesamt = sum(attachment.size or 0 for attachment in attachments)
    if gesamt > MAX_MEMORY_TOTAL_SIZE:
        raise _conflict(
            "The parent exceeds its attachment limit.",
            ErrorCode.ATTACHMENT_LIMIT_EXCEEDED,
        )


def attachments_of_memories(
    session: Session, memory_ids: list[UUID]
) -> dict[UUID, list[BoundAttachment]]:
    """Dieselbe Galerie fuer mehrere Memories in einer Abfrage.

    Die Story laedt bis zu hundert Items pro Seite. Einzeln geladen waeren
    das hundert Abfragen fuer eine Liste - deshalb dieselbe Sortierregel
    einmal batchweise, statt sie in der Story noch einmal zu formulieren.
    """
    if not memory_ids:
        return {}
    zeilen = session.execute(
        select(MemoryAttachment, Attachment)
        .join(Attachment, Attachment.id == MemoryAttachment.attachment_id)
        .where(MemoryAttachment.memory_id.in_(memory_ids))
        .order_by(MemoryAttachment.position, MemoryAttachment.attachment_id)
    ).all()
    galerien: dict[UUID, list[BoundAttachment]] = {memory_id: [] for memory_id in memory_ids}
    for bindung, attachment in zeilen:
        galerien[bindung.memory_id].append(
            BoundAttachment(attachment=attachment, position=bindung.position)
        )
    return galerien


def attachments_of_memory(session: Session, memory_id: UUID) -> list[BoundAttachment]:
    """Die Galerie einer Memory in stabiler Reihenfolge.

    Sortiert nach `position`, danach nach Attachment-ID - der Tie-Breaker
    macht die Reihenfolge auch dann deterministisch, wenn zwei Zeilen
    dieselbe Position tragen sollten.
    """
    zeilen = session.execute(
        select(MemoryAttachment, Attachment)
        .join(Attachment, Attachment.id == MemoryAttachment.attachment_id)
        .where(MemoryAttachment.memory_id == memory_id)
        .order_by(MemoryAttachment.position, MemoryAttachment.attachment_id)
    ).all()
    return [BoundAttachment(attachment=zeile[1], position=zeile[0].position) for zeile in zeilen]
