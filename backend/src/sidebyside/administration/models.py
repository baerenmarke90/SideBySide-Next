"""Persistence for instance-wide application administration state."""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from uuid import UUID

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    SmallInteger,
    String,
    func,
)
from sqlalchemy.dialects import postgresql
from sqlalchemy.orm import Mapped, mapped_column

from sidebyside.db.base import Base
from sidebyside.db.mixins import IdMixin, TimestampMixin, VersionMixin


class AdministrationSetting(StrEnum):
    """Auditable instance-wide boolean settings."""

    REGISTRATION_ENABLED = "registration_enabled"
    MAINTENANCE_MODE = "maintenance_mode"


class InstanceAdministrationSettings(TimestampMixin, VersionMixin, Base):
    """Singleton application-administration state.

    These settings are runtime product state. They are intentionally separate
    from deployment secrets and environment configuration.
    """

    __tablename__ = "instance_administration_settings"

    singleton_key: Mapped[int] = mapped_column(SmallInteger, primary_key=True, default=1)
    registration_enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    maintenance_mode: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    __table_args__ = (
        CheckConstraint(
            "singleton_key = 1",
            name="singleton_key_is_one",
        ),
    )


class InstanceAdministrationEvent(IdMixin, Base):
    """Narrow audit history for privileged instance-setting changes."""

    __tablename__ = "instance_administration_events"

    actor_id: Mapped[UUID | None] = mapped_column(
        postgresql.UUID(as_uuid=True),
        ForeignKey("accounts.id", ondelete="SET NULL"),
    )
    setting: Mapped[str] = mapped_column(String(64), nullable=False)
    previous_value: Mapped[bool] = mapped_column(Boolean, nullable=False)
    new_value: Mapped[bool] = mapped_column(Boolean, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    __table_args__ = (
        CheckConstraint(
            "setting IN ('registration_enabled', 'maintenance_mode')",
            name="setting_valid",
        ),
        Index("ix_instance_administration_events_created_at", "created_at"),
    )
