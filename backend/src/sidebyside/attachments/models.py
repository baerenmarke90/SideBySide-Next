"""Persistenz und Wertebereiche fuer M2-Attachments."""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from typing import ClassVar

from sqlalchemy import BigInteger, CheckConstraint, DateTime, Index, Integer, SmallInteger, String
from sqlalchemy import text as sql_text
from sqlalchemy.orm import Mapped, mapped_column

from sidebyside.authorization import PrivateResourceMixin, ResourceAbsence
from sidebyside.db.base import Base
from sidebyside.db.mixins import IdMixin, TimestampMixin, VersionMixin
from sidebyside.db.protected_payload import ProtectedPayloadJSON
from sidebyside.domain.payload import CRYPTO_VERSION_PLAINTEXT, ProtectedPayload


class AttachmentStatus(StrEnum):
    """Die verbindlichen internen Zustaende aus M2-D05.

    `PROCESSING`, wie Clients es sehen, steht hier nicht: die oeffentliche
    Darstellung ist eine Projektion und kein zusaetzlicher Zustand.
    """

    PENDING = "PENDING"
    UPLOADING = "UPLOADING"
    VALIDATING = "VALIDATING"
    READY = "READY"
    FAILED = "FAILED"
    DELETING = "DELETING"
    DELETE_FAILED = "DELETE_FAILED"


class MediaType(StrEnum):
    IMAGE = "IMAGE"
    VIDEO = "VIDEO"


class AttachmentPayload(ProtectedPayload):
    """Was der Server ueber die Datei behaelt, ohne es zu Metadaten zu machen.

    `original_name` ist reine Support-Information und wird nie fuer Pfad,
    Autorisierung oder Content-Type herangezogen (Media-Pipeline, Abschnitt 5).

    `captured_at` und `orientation` sind die Allowlist aus M2-D14: alles
    Uebrige wird beim Ingest verworfen. Sie liegen hier und nicht in Spalten,
    damit ein Aufnahmezeitpunkt nicht unversehens zu einem sortierbaren,
    indizierbaren Metadatum wird.
    """

    original_name: str
    captured_at: datetime | None = None
    orientation: int | None = None


class Attachment(
    IdMixin,
    TimestampMixin,
    VersionMixin,
    PrivateResourceMixin,
    Base,
):
    """Eine hochgeladene Datei mit ihrem Lebenszyklus.

    Der Storage Key steht bewusst nicht in einer Spalte. Er ergibt sich aus
    Space und Attachment-ID (`media.build_storage_key`); eine Spalte waere
    eine zweite Wahrheit, die von der ersten abweichen koennte - und der
    Vertrag verbietet ohnehin, ihn nach aussen zu geben.
    """

    __tablename__ = "attachments"

    privacy_absence: ClassVar[ResourceAbsence] = ResourceAbsence(
        "Attachment not found.", "RESOURCE_NOT_FOUND"
    )

    status: Mapped[str] = mapped_column(String(16), nullable=False)
    media_type: Mapped[str] = mapped_column(String(16), nullable=False)

    # Was der Client angekuendigt hat. Ausschliesslich fuer die
    # Vorabpruefung; die Validierung entscheidet spaeter am echten Objekt.
    declared_mime_type: Mapped[str] = mapped_column(String(128), nullable=False)
    declared_size: Mapped[int] = mapped_column(BigInteger, nullable=False)

    # Was der Server selbst festgestellt hat. Erst diese Werte gehen nach
    # aussen und in die Limitpruefung.
    mime_type: Mapped[str | None] = mapped_column(String(128))
    size: Mapped[int | None] = mapped_column(BigInteger)
    width: Mapped[int | None] = mapped_column(Integer)
    height: Mapped[int | None] = mapped_column(Integer)
    duration_seconds: Mapped[int | None] = mapped_column(Integer)

    has_thumbnail: Mapped[bool] = mapped_column(
        nullable=False, default=False, server_default=sql_text("false")
    )

    # Stabiler, nicht sensitiver Grund. Nie ein Parserfehlertext: der
    # koennte Dateiinhalt enthalten.
    failure_code: Mapped[str | None] = mapped_column(String(64))

    ready_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    failed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    # Letzte serverbekannte Aktivitaet am Upload - Grundlage der
    # UPLOADING-Retention aus M2-D12.
    uploaded_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    crypto_version: Mapped[int] = mapped_column(
        SmallInteger,
        nullable=False,
        default=CRYPTO_VERSION_PLAINTEXT,
        server_default=sql_text("0"),
    )
    payload: Mapped[AttachmentPayload] = mapped_column(
        ProtectedPayloadJSON(AttachmentPayload),
        nullable=False,
    )

    __table_args__ = (
        CheckConstraint(
            "status IN (" + ", ".join(f"'{status.value}'" for status in AttachmentStatus) + ")",
            name="status_is_known",
        ),
        CheckConstraint(
            "media_type IN (" + ", ".join(f"'{kind.value}'" for kind in MediaType) + ")",
            name="media_type_is_known",
        ),
        # Ein ungebundenes Attachment gehoert seinem Owner. Die Bindung an
        # einen Parent kommt im Media-Integrationsslice; bis dahin gibt es
        # keinen Weg, auf dem ein Attachment gemeinsam werden koennte.
        CheckConstraint("privacy_class = 'OWNER_ONLY'", name="privacy_is_owner_only"),
        CheckConstraint("crypto_version >= 0", name="crypto_version_is_non_negative"),
        CheckConstraint("declared_size >= 0", name="declared_size_is_non_negative"),
        CheckConstraint("size IS NULL OR size >= 0", name="size_is_non_negative"),
        # READY ohne readyAt waere ein Attachment ohne Bindungsfenster - es
        # wuerde vom Cleanup nie erfasst.
        CheckConstraint(
            "status <> 'READY' OR ready_at IS NOT NULL",
            name="ready_has_ready_at",
        ),
        Index("ix_attachments_owner_id", "owner_id"),
        # Der Cleanup sucht nach Zustand und Alter, nicht nach Space.
        Index("ix_attachments_status_created_at", "status", "created_at"),
        Index("ix_attachments_status_ready_at", "status", "ready_at"),
    )
