"""Persistence and value ranges for M2 attachments."""

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
    """Authoritative internal states from M2-D05.

    ``PROCESSING``, as exposed to clients, is not an additional internal state;
    it is a public projection of the state machine.
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
    """File information retained without promoting it to server metadata.

    ``original_name`` exists only for support and is never used for paths,
    authorization, or content type (Media Pipeline, section 5).

    ``captured_at`` and ``orientation`` form the M2-D14 allowlist. Everything
    else is discarded during ingest. They remain inside the protected payload
    rather than columns so capture time does not accidentally become sortable,
    indexable server metadata.
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
    """An uploaded file and its lifecycle state.

    Storage key is deliberately not persisted. It is derived from space and
    attachment ID by ``media.build_storage_key``; a column would create a
    second source of truth that could drift, and the contract never exposes it.
    """

    __tablename__ = "attachments"

    privacy_absence: ClassVar[ResourceAbsence] = ResourceAbsence(
        "Attachment not found.", "RESOURCE_NOT_FOUND"
    )

    status: Mapped[str] = mapped_column(String(16), nullable=False)
    media_type: Mapped[str] = mapped_column(String(16), nullable=False)

    # Values declared by the client. Used only for preliminary checks; later
    # validation decides from the actual stored object.
    declared_mime_type: Mapped[str] = mapped_column(String(128), nullable=False)
    declared_size: Mapped[int] = mapped_column(BigInteger, nullable=False)

    # Values established by the server. Only these are exposed and used for
    # final limit validation.
    mime_type: Mapped[str | None] = mapped_column(String(128))
    size: Mapped[int | None] = mapped_column(BigInteger)
    width: Mapped[int | None] = mapped_column(Integer)
    height: Mapped[int | None] = mapped_column(Integer)
    duration_seconds: Mapped[int | None] = mapped_column(Integer)

    has_thumbnail: Mapped[bool] = mapped_column(
        nullable=False, default=False, server_default=sql_text("false")
    )

    # Stable non-sensitive reason. Never parser text, which could contain file
    # content.
    failure_code: Mapped[str | None] = mapped_column(String(64))

    ready_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    failed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    # Last server-observed upload activity, used by M2-D12 UPLOADING retention.
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
        # An unbound attachment belongs to its owner. Parent binding is handled
        # by the media integration slice; until then it has no shared path.
        CheckConstraint("privacy_class = 'OWNER_ONLY'", name="privacy_is_owner_only"),
        CheckConstraint("crypto_version >= 0", name="crypto_version_is_non_negative"),
        CheckConstraint("declared_size >= 0", name="declared_size_is_non_negative"),
        CheckConstraint("size IS NULL OR size >= 0", name="size_is_non_negative"),
        # READY without readyAt would have no binding window and would never be
        # collected by cleanup.
        CheckConstraint(
            "status <> 'READY' OR ready_at IS NOT NULL",
            name="ready_has_ready_at",
        ),
        Index("ix_attachments_owner_id", "owner_id"),
        # Cleanup searches by state and age rather than by space.
        Index("ix_attachments_status_created_at", "status", "created_at"),
        Index("ix_attachments_status_ready_at", "status", "ready_at"),
    )
