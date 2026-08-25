"""Persistenz fuer gemeinsame M2-Memories."""

from __future__ import annotations

from datetime import date
from typing import ClassVar

from sqlalchemy import CheckConstraint, Date, Index, SmallInteger, text
from sqlalchemy.orm import Mapped, mapped_column

from sidebyside.authorization import PrivacyClass, PrivateResourceMixin, ResourceAbsence
from sidebyside.db.base import Base
from sidebyside.db.mixins import IdMixin, TimestampMixin, VersionMixin
from sidebyside.db.protected_payload import ProtectedPayloadJSON
from sidebyside.domain.payload import CRYPTO_VERSION_PLAINTEXT, ProtectedPayload


class MemoryPayload(ProtectedPayload):
    """Schuetzenswerter Inhalt einer Erinnerung.

    Titel und Text bleiben bewusst in derselben ProtectedPayload-Grenze.
    Sortierung, Tenant-Isolation und Autorisierung duerfen von ihrem Klartext
    nicht abhaengen.
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
    """Eine fuer beide aktiven Partner lesbare, author-only editierbare Memory."""

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
        Index("ix_memories_owner_id", "owner_id"),
        Index("ix_memories_space_id_created_at_id", "space_id", "created_at", "id"),
        Index("ix_memories_space_id_happened_on", "space_id", "happened_on"),
    )


def shared_privacy() -> PrivacyClass:
    """Memories sind in M2 immer gemeinsamer Space-Inhalt."""
    return PrivacyClass.SPACE_SHARED
