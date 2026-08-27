"""Persistenz fuer gemeinsame M2-Milestones."""

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


class MilestonePayload(ProtectedPayload):
    """Schuetzenswerter Inhalt eines Milestones.

    Wie bei Memory: Titel und Body liegen gemeinsam hinter der
    ProtectedPayload-Grenze. Sortierung und Autorisierung duerfen von
    ihrem Klartext nicht abhaengen.
    """

    title: str
    body: str | None = None


class Milestone(
    IdMixin,
    TimestampMixin,
    VersionMixin,
    PrivateResourceMixin,
    Base,
):
    """Ein gemeinsamer Meilenstein - lesbar fuer beide, author-only editierbar.

    `happened_on` ist anders als bei Memory Pflicht: ein Meilenstein ohne
    Datum waere kein Meilenstein, und die Story sortiert danach.
    """

    __tablename__ = "milestones"

    privacy_absence: ClassVar[ResourceAbsence] = ResourceAbsence(
        "Milestone not found.", "RESOURCE_NOT_FOUND"
    )

    happened_on: Mapped[date] = mapped_column(Date, nullable=False)
    crypto_version: Mapped[int] = mapped_column(
        SmallInteger,
        nullable=False,
        default=CRYPTO_VERSION_PLAINTEXT,
        server_default=text("0"),
    )
    payload: Mapped[MilestonePayload] = mapped_column(
        ProtectedPayloadJSON(MilestonePayload),
        nullable=False,
    )

    __table_args__ = (
        CheckConstraint("privacy_class = 'SPACE_SHARED'", name="privacy_is_space_shared"),
        CheckConstraint("crypto_version >= 0", name="crypto_version_is_non_negative"),
        # Traegt den zusammengesetzten Fremdschluessel der
        # place_milestones-Relationen. Ohne dieses Paar koennte eine Join-Zeile
        # nicht gleichzeitig auf Zeile und Space zeigen - und Same-Space
        # waere wieder eine Dienstregel statt einer Schemaeigenschaft.
        UniqueConstraint("id", "space_id", name="uq_milestones_id_space_id"),
        Index("ix_milestones_owner_id", "owner_id"),
        Index("ix_milestones_space_id_created_at_id", "space_id", "created_at", "id"),
        Index("ix_milestones_space_id_happened_on", "space_id", "happened_on"),
    )


def shared_privacy() -> PrivacyClass:
    """Milestones sind immer gemeinsamer Space-Inhalt (M2-D25)."""
    return PrivacyClass.SPACE_SHARED
