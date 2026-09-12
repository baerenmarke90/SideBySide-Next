"""Bounded read models for relationship-native games.

Games are consumers of existing product domains. This module deliberately
reuses authoritative authorization and attachment bindings instead of creating
a second Memory or media model.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, date
from uuid import UUID

from sqlalchemy.orm import Session

from sidebyside.attachments.binding import MemoryAttachment
from sidebyside.attachments.models import Attachment, AttachmentStatus, MediaType
from sidebyside.authorization import AuthorizationContext, readable
from sidebyside.memories.models import Memory

MAX_MEMORY_CANDIDATES = 24
"""Maximum useful candidate pool returned to one local sofa-mode round client.

The query is not based on a Story page. It scans the authorized photo-backed
Memory set until this many usable candidates have been collected, so sparse
state cannot be inferred merely from one paginated timeline page.
"""


@dataclass(frozen=True)
class MemoryCandidate:
    memory_id: UUID
    title: str
    effective_date: date
    image_attachment_id: UUID


def read_memory_candidates(
    session: Session,
    context: AuthorizationContext,
    *,
    limit: int = MAX_MEMORY_CANDIDATES,
) -> list[MemoryCandidate]:
    """Return bounded, shared photo-backed Memories eligible for #863.

    Eligibility intentionally stays narrow for the first playable grammar:
    - the Memory must already be readable through the authoritative visibility
      predicate for the active Space;
    - one bound attachment must be a READY image in that same Space;
    - the stored Memory title must be non-blank.

    Only the first eligible image in gallery order is returned for each Memory.
    Attachment bytes remain protected by the existing attachment read path; the
    candidate response exposes only the existing attachment identifier.
    """
    if limit <= 0:
        return []

    statement = (
        readable(Memory, context)
        .add_columns(
            Attachment.id.label("attachment_id"),
            MemoryAttachment.position.label("attachment_position"),
        )
        .join(MemoryAttachment, MemoryAttachment.memory_id == Memory.id)
        .join(Attachment, Attachment.id == MemoryAttachment.attachment_id)
        .where(
            Attachment.space_id == context.space_id,
            Attachment.status == AttachmentStatus.READY.value,
            Attachment.media_type == MediaType.IMAGE.value,
        )
        .order_by(
            Memory.created_at.desc(),
            Memory.id.desc(),
            MemoryAttachment.position.asc(),
            Attachment.id.asc(),
        )
    )

    candidates: list[MemoryCandidate] = []
    seen_memories: set[UUID] = set()
    rows = session.execute(statement).yield_per(100)
    for memory, attachment_id, _attachment_position in rows:
        if memory.id in seen_memories:
            continue
        seen_memories.add(memory.id)

        title = memory.payload.title.strip()
        if not title:
            continue

        created_at = memory.created_at
        if created_at.tzinfo is None:
            created_at = created_at.replace(tzinfo=UTC)
        effective_date = memory.happened_on or created_at.astimezone(UTC).date()
        candidates.append(
            MemoryCandidate(
                memory_id=memory.id,
                title=title,
                effective_date=effective_date,
                image_attachment_id=attachment_id,
            )
        )
        if len(candidates) >= limit:
            break

    return candidates
