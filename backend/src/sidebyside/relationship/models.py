"""Space und Membership - das Mandantenmodell.

    Account A ──┐
                ├── Membership ── Space
    Account B ──┘

Der Space ist der private gemeinsame Raum eines Paares. Jeder gemeinsame
Datensatz gehoert genau einem Space.
"""

from __future__ import annotations

from datetime import date, datetime
from enum import StrEnum
from uuid import UUID

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Date,
    DateTime,
    ForeignKey,
    Index,
    String,
    UniqueConstraint,
)
from sqlalchemy.dialects import postgresql
from sqlalchemy.orm import Mapped, mapped_column, relationship

from sidebyside.db.base import Base
from sidebyside.db.mixins import IdMixin, TimestampMixin, VersionMixin

MAX_ACTIVE_PARTNERS = 2
"""Ein normaler Paar-Space hat hoechstens zwei aktive Partner."""


class MembershipStatus(StrEnum):
    ACTIVE = "ACTIVE"
    LEFT = "LEFT"
    REMOVED = "REMOVED"


class MembershipRole(StrEnum):
    PARTNER = "PARTNER"


class DurationDisplayMode(StrEnum):
    """Wie die gemeinsame Zeit dargestellt wird."""

    YEARS_MONTHS = "YEARS_MONTHS"
    DAYS = "DAYS"


class Space(IdMixin, TimestampMixin, Base):
    __tablename__ = "spaces"

    memberships: Mapped[list[Membership]] = relationship(
        back_populates="space", cascade="all, delete-orphan"
    )
    profile: Mapped[SpaceProfile | None] = relationship(
        back_populates="space", cascade="all, delete-orphan", uselist=False
    )


class Membership(IdMixin, TimestampMixin, Base):
    """Die Zugehoerigkeit eines Accounts zu einem Space.

    Sie ist der einzige Weg, ueber den ein Account an Space-Daten kommt.
    Eine beendete Mitgliedschaft wird nicht geloescht, sondern auf LEFT oder
    REMOVED gesetzt - sonst waere spaeter nicht mehr nachvollziehbar, wer
    einen Inhalt angelegt hat.
    """

    __tablename__ = "memberships"

    space_id: Mapped[UUID] = mapped_column(
        postgresql.UUID(as_uuid=True),
        ForeignKey("spaces.id", ondelete="CASCADE"),
        nullable=False,
    )
    account_id: Mapped[UUID] = mapped_column(
        postgresql.UUID(as_uuid=True),
        ForeignKey("accounts.id", ondelete="CASCADE"),
        nullable=False,
    )

    role: Mapped[str] = mapped_column(
        String(16), nullable=False, default=MembershipRole.PARTNER.value
    )
    status: Mapped[str] = mapped_column(
        String(16), nullable=False, default=MembershipStatus.ACTIVE.value
    )

    joined_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    ended_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    space: Mapped[Space] = relationship(back_populates="memberships")

    __table_args__ = (
        # Ein Account ist je Space hoechstens einmal Mitglied. Zwei Zeilen
        # waeren zwei Wahrheiten darueber, ob jemand Zugriff hat.
        UniqueConstraint("space_id", "account_id", name="uq_memberships_space_id_account_id"),
        CheckConstraint("status IN ('ACTIVE', 'LEFT', 'REMOVED')", name="status_is_known"),
        CheckConstraint("role IN ('PARTNER')", name="role_is_known"),
        # Der Guard fragt bei jeder Anfrage nach genau dieser Kombination.
        Index("ix_memberships_account_id_space_id_status", "account_id", "space_id", "status"),
    )

    @property
    def is_active(self) -> bool:
        return self.status == MembershipStatus.ACTIVE.value


class SpaceProfile(IdMixin, TimestampMixin, VersionMixin, Base):
    """Beziehungsbezogene Angaben zum Space."""

    __tablename__ = "space_profiles"

    space_id: Mapped[UUID] = mapped_column(
        postgresql.UUID(as_uuid=True),
        ForeignKey("spaces.id", ondelete="CASCADE"),
        nullable=False,
    )

    # Ein fachlicher Tag, kein Zeitpunkt: der Beginn einer Beziehung hat
    # keine Uhrzeit.
    relationship_started_on: Mapped[date | None] = mapped_column(Date)
    show_relationship_duration: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    duration_display_mode: Mapped[str] = mapped_column(
        String(16), nullable=False, default=DurationDisplayMode.YEARS_MONTHS.value
    )

    space: Mapped[Space] = relationship(back_populates="profile")

    __table_args__ = (
        UniqueConstraint("space_id", name="uq_space_profiles_space_id"),
        CheckConstraint(
            "duration_display_mode IN ('YEARS_MONTHS', 'DAYS')",
            name="duration_display_mode_is_known",
        ),
    )


class Invitation(IdMixin, TimestampMixin, Base):
    """Eine Einladung in einen Space.

    Der Token steht nur gehasht hier. Wer die Datenbank liest, kann damit
    keinem fremden Space beitreten.

    Angenommen wird genau einmal: `accepted_at` ist die Sperre. Zusammen mit
    einer Zeilensperre beim Annehmen verhindert das, dass zwei gleichzeitige
    Versuche beide durchgehen.
    """

    __tablename__ = "invitations"

    space_id: Mapped[UUID] = mapped_column(
        postgresql.UUID(as_uuid=True),
        ForeignKey("spaces.id", ondelete="CASCADE"),
        nullable=False,
    )
    created_by: Mapped[UUID] = mapped_column(
        postgresql.UUID(as_uuid=True),
        ForeignKey("accounts.id", ondelete="CASCADE"),
        nullable=False,
    )

    token_hash: Mapped[str] = mapped_column(String(64), nullable=False)

    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    accepted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    accepted_by: Mapped[UUID | None] = mapped_column(
        postgresql.UUID(as_uuid=True), ForeignKey("accounts.id", ondelete="SET NULL")
    )
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    __table_args__ = (
        UniqueConstraint("token_hash", name="uq_invitations_token_hash"),
        Index("ix_invitations_space_id", "space_id"),
    )

    def is_open(self, at: datetime) -> bool:
        """Offen heisst: nicht angenommen, nicht widerrufen, nicht abgelaufen."""
        return self.accepted_at is None and self.revoked_at is None and self.expires_at > at
