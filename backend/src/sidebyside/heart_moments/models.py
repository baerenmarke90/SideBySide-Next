"""Persistenz fuer M2-HeartMoments."""

from __future__ import annotations

from datetime import date
from enum import StrEnum
from typing import ClassVar
from uuid import UUID

from sqlalchemy import (
    CheckConstraint,
    Date,
    ForeignKey,
    Index,
    SmallInteger,
    UniqueConstraint,
    text,
)
from sqlalchemy.dialects import postgresql
from sqlalchemy.orm import Mapped, mapped_column

from sidebyside.authorization import (
    ENFORCEABLE_PRIVACY_CLASSES,
    PrivateResourceMixin,
    ResourceAbsence,
)
from sidebyside.db.base import Base
from sidebyside.db.mixins import IdMixin, TimestampMixin, VersionMixin
from sidebyside.db.protected_payload import ProtectedPayloadJSON
from sidebyside.domain.payload import CRYPTO_VERSION_PLAINTEXT, ProtectedPayload


class HeartEmotion(StrEnum):
    """Die Emotionen aus dem M2-Domainvertrag.

    Ein geschlossener Wertebereich, aber kein Metadatum: der Wert lebt in
    der ProtectedPayload und nicht als eigene Spalte. Siehe M2-D06.
    """

    LOVED = "LOVED"
    SEEN = "SEEN"
    APPRECIATED = "APPRECIATED"
    SUPPORTED = "SUPPORTED"
    GRATEFUL = "GRATEFUL"
    HAPPY = "HAPPY"


class HeartMomentPayload(ProtectedPayload):
    """Schuetzenswerter Inhalt eines HeartMoments.

    `emotion` steht bewusst hier und nicht in einer Spalte. Der Wert
    beschreibt sensiblen Beziehungsinhalt und erlaubt auch ohne den Text
    private Rueckschluesse; fuer Sortierung, Tenant-Isolation und Routing
    wird er nicht gebraucht (M2-D06). Ein Filter nach Emotion ist deshalb
    nicht Teil des M2-Vertrags - er waere ohne Klartextspalte oder Index
    nicht zu haben, und beides ist genau das, was hier vermieden wird.
    """

    text: str
    emotion: HeartEmotion


class HeartMoment(
    IdMixin,
    TimestampMixin,
    VersionMixin,
    PrivateResourceMixin,
    Base,
):
    """Ein HeartMoment - je nach Sichtbarkeit gemeinsam oder owner-only.

    Anders als Memory traegt diese Tabelle beide durchsetzbaren
    Privacy-Klassen. Welche gilt, entscheidet der Owner ueber `visibility`;
    die Klasse ist die serverseitige Ableitung davon und nie ein Clientfeld.
    """

    __tablename__ = "heart_moments"

    privacy_absence: ClassVar[ResourceAbsence] = ResourceAbsence(
        "Heart moment not found.", "RESOURCE_NOT_FOUND"
    )

    happened_on: Mapped[date] = mapped_column(Date, nullable=False)

    # Hoechstens ein Attachment (M2-D03). Als Fremdschluessel und nicht als
    # Relationstabelle: die Kardinalitaet steht damit im Schema und nicht
    # in einer Regel, die jemand vergessen kann.
    attachment_id: Mapped[UUID | None] = mapped_column(
        postgresql.UUID(as_uuid=True),
        ForeignKey("attachments.id", ondelete="RESTRICT"),
    )
    crypto_version: Mapped[int] = mapped_column(
        SmallInteger,
        nullable=False,
        default=CRYPTO_VERSION_PLAINTEXT,
        server_default=text("0"),
    )
    payload: Mapped[HeartMomentPayload] = mapped_column(
        ProtectedPayloadJSON(HeartMomentPayload),
        nullable=False,
    )

    __table_args__ = (
        CheckConstraint(
            "privacy_class IN ("
            + ", ".join(f"'{privacy.value}'" for privacy in ENFORCEABLE_PRIVACY_CLASSES)
            + ")",
            name="privacy_is_enforceable",
        ),
        CheckConstraint("crypto_version >= 0", name="crypto_version_is_non_negative"),
        # Dasselbe Attachment nicht an zwei HeartMoments.
        UniqueConstraint("attachment_id", name="uq_heart_moments_attachment"),
        # Ziel des Fremdschluessels von `place_heart_moments`. Die
        # Privacy-Klasse gehoert bewusst mit hinein: nur so kann die
        # Join-Zeile den gemeinsamen Zustand ihres Ziels mitfuehren, und
        # nur so bricht ein Wechsel auf OWNER_ONLY eine vergessene
        # Relation auf, statt sie stehen zu lassen (M3-D09).
        UniqueConstraint(
            "id",
            "space_id",
            "privacy_class",
            name="uq_heart_moments_id_space_id_privacy",
        ),
        Index("ix_heart_moments_owner_id", "owner_id"),
        Index("ix_heart_moments_space_id_created_at_id", "space_id", "created_at", "id"),
        Index(
            "ix_heart_moments_space_id_privacy_class",
            "space_id",
            "privacy_class",
        ),
    )
