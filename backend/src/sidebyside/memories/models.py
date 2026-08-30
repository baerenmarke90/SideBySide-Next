"""Persistence for shared M2 memories."""

from __future__ import annotations

from datetime import date
from typing import ClassVar

from sqlalchemy import CheckConstraint, Date, Index, SmallInteger, UniqueConstraint, text
from sqlalchemy.orm import Mapped, mapped_column

from sidebyside.authorization import PrivacyClass, PrivateResourceMixin, ResourceAbsence
from sidebyside.db.base import Base
from sidebyside.db.mixins import IdMixin, TimestampMixin, VersionMixin
from sidebyside.db.protected_payload import ProtectedPayloadJSON
from sidebyside.domain.payload import CRYPTO_VERSION_PLAINTEXT, ProtectedPayload


class MemoryPayload(ProtectedPayload):
    """Protected content of a memory.

    Title and body deliberately share the same ``ProtectedPayload`` boundary.
    Sorting, tenant isolation, and authorization must not depend on their
    plaintext.
    """

    title: str
    body: str


class Memory(
    IdMixin,
    TimestampMixin,
    VersionMixin,
    PrivateResourceMixin,
    Base,
):
    """A memory readable by both active partners and editable by its author."""

    __tablename__ = "memories"

    privacy_absence: ClassVar[ResourceAbsence] = ResourceAbsence(
        "Memory not found.", "RESOURCE_NOT_FOUND"
    )

    happened_on: Mapped[date | None] = mapped_column(Date)
    crypto_version: Mapped[int] = mapped_column(
        SmallInteger,
        nullable=False,
        default=CRYPTO_VERSION_PLAINTEXT,
        server_default=text("0"),
    )
    payload: Mapped[MemoryPayload] = mapped_column(
        ProtectedPayloadJSON(MemoryPayload),
        nullable=False,
    )

    __table_args__ = (
        CheckConstraint("privacy_class = 'SPACE_SHARED'", name="privacy_is_space_shared"),
        CheckConstraint("crypto_version >= 0", name="crypto_version_is_non_negative"),
        # Supports the composite foreign key used by place-memory relations.
        # Without this pair, a relation row could not constrain both resource
        # ID and space, leaving same-space enforcement only to service code.
        UniqueConstraint("id", "space_id", name="uq_memories_id_space_id"),
        Index("ix_memories_owner_id", "owner_id"),
        Index("ix_memories_space_id_created_at_id", "space_id", "created_at", "id"),
        Index("ix_memories_space_id_happened_on", "space_id", "happened_on"),
        Index(
            "ix_memories_search_fts",
            text(
                "setweight(to_tsvector('simple', coalesce(payload->>'title', '')), 'A') || "
                "setweight(to_tsvector('simple', coalesce(payload->>'body', '')), 'B')"
            ),
            postgresql_using="gin",
        ),
    )


def shared_privacy() -> PrivacyClass:
    """Memories are always shared space content in M2."""
    return PrivacyClass.SPACE_SHARED
