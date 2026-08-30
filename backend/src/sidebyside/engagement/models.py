"""Minimized M4-B Activity and in-app Notification projections."""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from uuid import UUID

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    String,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects import postgresql
from sqlalchemy.orm import Mapped, mapped_column

from sidebyside.db.base import Base
from sidebyside.db.mixins import IdMixin


class ActivityKind(StrEnum):
    MEMORY_CREATED = "MEMORY_CREATED"
    MILESTONE_CREATED = "MILESTONE_CREATED"
    HEART_MOMENT_CREATED = "HEART_MOMENT_CREATED"
    WISH_CREATED = "WISH_CREATED"
    PLAN_CREATED = "PLAN_CREATED"
    PLAN_COMPLETED = "PLAN_COMPLETED"
    PLACE_CREATED = "PLACE_CREATED"
    CHAPTER_CREATED = "CHAPTER_CREATED"
    COLLECTION_CREATED = "COLLECTION_CREATED"
    COMMENT_CREATED = "COMMENT_CREATED"


class NotificationKind(StrEnum):
    COMMENT_CREATED = "COMMENT_CREATED"


class EngagementTarget(StrEnum):
    MEMORY = "MEMORY"
    HEART_MOMENT = "HEART_MOMENT"
    MILESTONE = "MILESTONE"
    WISH = "WISH"
    PLAN = "PLAN"
    PLACE = "PLACE"
    CHAPTER = "CHAPTER"
    COLLECTION = "COLLECTION"


_ACTIVITY_KIND_VALUES = ", ".join(f"'{value.value}'" for value in ActivityKind)
_NOTIFICATION_KIND_VALUES = ", ".join(f"'{value.value}'" for value in NotificationKind)
_TARGET_VALUES = ", ".join(f"'{value.value}'" for value in EngagementTarget)


class Activity(IdMixin, Base):
    """A shared-space event containing references only, never protected text."""

    __tablename__ = "activities"

    space_id: Mapped[UUID] = mapped_column(
        postgresql.UUID(as_uuid=True),
        ForeignKey("spaces.id", ondelete="CASCADE"),
        nullable=False,
    )
    source_event_id: Mapped[UUID] = mapped_column(postgresql.UUID(as_uuid=True), nullable=False)
    kind: Mapped[str] = mapped_column(String(64), nullable=False)
    actor_id: Mapped[UUID | None] = mapped_column(
        postgresql.UUID(as_uuid=True),
        ForeignKey("accounts.id", ondelete="SET NULL"),
    )
    target_type: Mapped[str | None] = mapped_column(String(32))
    target_id: Mapped[UUID | None] = mapped_column(postgresql.UUID(as_uuid=True))
    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    __table_args__ = (
        CheckConstraint(f"kind IN ({_ACTIVITY_KIND_VALUES})", name="activity_kind_allowed"),
        CheckConstraint(
            f"target_type IS NULL OR target_type IN ({_TARGET_VALUES})",
            name="activity_target_type_allowed",
        ),
        CheckConstraint(
            "(target_type IS NULL) = (target_id IS NULL)",
            name="activity_target_reference_complete",
        ),
        UniqueConstraint("source_event_id", "kind", name="uq_activities_source_event_kind"),
        Index("ix_activities_space_occurred_id", "space_id", "occurred_at", "id"),
    )


class Notification(IdMixin, Base):
    """Recipient-scoped in-app state with no copied relationship plaintext."""

    __tablename__ = "notifications"

    space_id: Mapped[UUID] = mapped_column(
        postgresql.UUID(as_uuid=True),
        ForeignKey("spaces.id", ondelete="CASCADE"),
        nullable=False,
    )
    recipient_account_id: Mapped[UUID] = mapped_column(
        postgresql.UUID(as_uuid=True),
        ForeignKey("accounts.id", ondelete="CASCADE"),
        nullable=False,
    )
    source_event_id: Mapped[UUID] = mapped_column(postgresql.UUID(as_uuid=True), nullable=False)
    kind: Mapped[str] = mapped_column(String(64), nullable=False)
    actor_id: Mapped[UUID | None] = mapped_column(
        postgresql.UUID(as_uuid=True),
        ForeignKey("accounts.id", ondelete="SET NULL"),
    )
    target_type: Mapped[str | None] = mapped_column(String(32))
    target_id: Mapped[UUID | None] = mapped_column(postgresql.UUID(as_uuid=True))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    read_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    __table_args__ = (
        CheckConstraint(
            f"kind IN ({_NOTIFICATION_KIND_VALUES})",
            name="notification_kind_allowed",
        ),
        CheckConstraint(
            f"target_type IS NULL OR target_type IN ({_TARGET_VALUES})",
            name="notification_target_type_allowed",
        ),
        CheckConstraint(
            "(target_type IS NULL) = (target_id IS NULL)",
            name="notification_target_reference_complete",
        ),
        UniqueConstraint(
            "recipient_account_id",
            "source_event_id",
            "kind",
            name="uq_notifications_recipient_source_kind",
        ),
        Index(
            "ix_notifications_recipient_space_created_id",
            "recipient_account_id",
            "space_id",
            "created_at",
            "id",
        ),
        Index(
            "ix_notifications_recipient_space_unread",
            "recipient_account_id",
            "space_id",
            "created_at",
            postgresql_where=read_at.is_(None),
        ),
    )
