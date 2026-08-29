"""Persistence for typed M3 content relations.

A relation has no owner and no privacy class of its own. It is not content,
but a statement about two content objects, and its visibility is derived from
both sides. Therefore none of these tables carries `PrivateResourceMixin`: a
third source of truth beside parent and target would be exactly where the
three could diverge.

What these tables carry instead is `space_id`, once and shared by both foreign
keys. A cross-space relation is therefore not merely forbidden but impossible
to express (M3-D08).
"""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, ForeignKeyConstraint, Index, func
from sqlalchemy.dialects import postgresql
from sqlalchemy.orm import Mapped, mapped_column

from sidebyside.authorization import PrivacyClass, privacy_class_type
from sidebyside.db.base import Base


class _RelationColumns:
    """Columns shared by every relation join table."""

    place_id: Mapped[UUID] = mapped_column(postgresql.UUID(as_uuid=True), primary_key=True)
    space_id: Mapped[UUID] = mapped_column(postgresql.UUID(as_uuid=True), nullable=False)
    created_by: Mapped[UUID] = mapped_column(
        postgresql.UUID(as_uuid=True),
        ForeignKey("accounts.id", ondelete="CASCADE"),
        nullable=False,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    """When the relation was created.

    There is no `updated_at`: a relation either exists or does not. There is
    nothing to update and therefore no version. A second `PUT` for the same
    relation is not a conflict but the same final state (M3-D26).
    """


class PlaceMemory(_RelationColumns, Base):
    """A memory that took place at a location."""

    __tablename__ = "place_memories"

    memory_id: Mapped[UUID] = mapped_column(postgresql.UUID(as_uuid=True), primary_key=True)

    __table_args__ = (
        ForeignKeyConstraint(
            ["place_id", "space_id"],
            ["places.id", "places.space_id"],
            name="fk_place_memories_place_id_places",
            ondelete="CASCADE",
        ),
        ForeignKeyConstraint(
            ["memory_id", "space_id"],
            ["memories.id", "memories.space_id"],
            name="fk_place_memories_memory_id_memories",
            ondelete="CASCADE",
        ),
        Index("ix_place_memories_memory_id", "memory_id"),
        Index("ix_place_memories_space_id", "space_id"),
        Index("ix_place_memories_place_id_created_at", "place_id", "created_at", "memory_id"),
    )


class PlaceMilestone(_RelationColumns, Base):
    """A milestone that took place at a location."""

    __tablename__ = "place_milestones"

    milestone_id: Mapped[UUID] = mapped_column(postgresql.UUID(as_uuid=True), primary_key=True)

    __table_args__ = (
        ForeignKeyConstraint(
            ["place_id", "space_id"],
            ["places.id", "places.space_id"],
            name="fk_place_milestones_place_id_places",
            ondelete="CASCADE",
        ),
        ForeignKeyConstraint(
            ["milestone_id", "space_id"],
            ["milestones.id", "milestones.space_id"],
            name="fk_place_milestones_milestone_id_milestones",
            ondelete="CASCADE",
        ),
        Index("ix_place_milestones_milestone_id", "milestone_id"),
        Index("ix_place_milestones_space_id", "space_id"),
        Index(
            "ix_place_milestones_place_id_created_at",
            "place_id",
            "created_at",
            "milestone_id",
        ),
    )


class PlaceHeartMoment(_RelationColumns, Base):
    """A shared HeartMoment that took place at a location.

    This is the only relation whose validity depends on target state: only
    `SHARED` HeartMoments may be linked (M3-D09).

    This condition is not enforced only in the service. `target_privacy_class`
    participates in the foreign key, the foreign key cascades updates, and a
    CHECK pins the column to `SPACE_SHARED`. If a HeartMoment changes to
    `OWNER_ONLY` without first removing its relations, the transaction fails.

    The service removes them in the same transaction and therefore never runs
    into that constraint. The constraint is the safety rail for code paths
    that do not exist yet.
    """

    __tablename__ = "place_heart_moments"

    heart_moment_id: Mapped[UUID] = mapped_column(postgresql.UUID(as_uuid=True), primary_key=True)
    target_privacy_class: Mapped[str] = mapped_column(
        privacy_class_type(),
        nullable=False,
        default=PrivacyClass.SPACE_SHARED.value,
    )

    __table_args__ = (
        CheckConstraint(
            "target_privacy_class = 'SPACE_SHARED'",
            name="relation_target_is_shared",
        ),
        ForeignKeyConstraint(
            ["place_id", "space_id"],
            ["places.id", "places.space_id"],
            name="fk_place_heart_moments_place_id_places",
            ondelete="CASCADE",
        ),
        ForeignKeyConstraint(
            ["heart_moment_id", "space_id", "target_privacy_class"],
            ["heart_moments.id", "heart_moments.space_id", "heart_moments.privacy_class"],
            name="fk_place_heart_moments_heart_moment_id_heart_moments",
            ondelete="CASCADE",
            onupdate="CASCADE",
        ),
        Index("ix_place_heart_moments_heart_moment_id", "heart_moment_id"),
        Index("ix_place_heart_moments_space_id", "space_id"),
        Index(
            "ix_place_heart_moments_place_id_created_at",
            "place_id",
            "created_at",
            "heart_moment_id",
        ),
    )
