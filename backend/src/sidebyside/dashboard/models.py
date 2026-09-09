"""Persistence for private per-account Dashboard presentation preferences."""

from __future__ import annotations

from uuid import UUID

from sqlalchemy import Boolean, ForeignKey, Index, String, UniqueConstraint, text
from sqlalchemy.dialects import postgresql
from sqlalchemy.orm import Mapped, mapped_column

from sidebyside.db.base import Base
from sidebyside.db.mixins import IdMixin, TimestampMixin


class DashboardModulePreference(IdMixin, TimestampMixin, Base):
    """One personal visibility override for one Dashboard module in one Space."""

    __tablename__ = "dashboard_module_preferences"

    account_id: Mapped[UUID] = mapped_column(
        postgresql.UUID(as_uuid=True),
        ForeignKey("accounts.id", ondelete="CASCADE"),
        nullable=False,
    )
    space_id: Mapped[UUID] = mapped_column(
        postgresql.UUID(as_uuid=True),
        ForeignKey("spaces.id", ondelete="CASCADE"),
        nullable=False,
    )
    module_key: Mapped[str] = mapped_column(String(64), nullable=False)
    visible: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        server_default=text("true"),
    )

    __table_args__ = (
        UniqueConstraint(
            "account_id",
            "space_id",
            "module_key",
            name="uq_dashboard_module_preferences_account_space_module",
        ),
        Index(
            "ix_dashboard_module_preferences_space_account",
            "space_id",
            "account_id",
        ),
    )
