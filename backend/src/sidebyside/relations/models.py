"""Persistenz fuer typisierte M3-Content-Relations.

Eine Relation hat keinen eigenen Eigentuemer und keine eigene
Privacy-Klasse. Sie ist kein Inhalt, sondern eine Aussage ueber zwei
Inhalte, und ihre Sichtbarkeit ist die der beiden Seiten. Deshalb traegt
keine dieser Tabellen `PrivateResourceMixin`: eine dritte Wahrheitsquelle
neben Parent und Target waere genau die Stelle, an der die drei
auseinanderlaufen.

Was die Tabellen stattdessen tragen, ist `space_id` - einmal, gemeinsam
fuer beide Fremdschluessel. Eine Relation ueber Spacegrenzen hinweg ist
damit nicht verboten, sondern nicht formulierbar (M3-D08).
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
    """Die gemeinsame Spaltenform aller Join-Tabellen."""

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
    """Wann die Verknuepfung entstand.

    Kein `updated_at`: eine Relation existiert oder existiert nicht. Es
    gibt nichts an ihr zu aendern, und deshalb auch keine Version - ein
    zweites `PUT` derselben Relation ist kein Konflikt, sondern derselbe
    Endzustand (M3-D26).
    """


class PlaceMemory(_RelationColumns, Base):
    """Eine Erinnerung, die an einem Ort stattgefunden hat."""

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
    """Ein Meilenstein, der an einem Ort stattgefunden hat."""

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
    """Ein gemeinsamer HeartMoment, der an einem Ort stattgefunden hat.

    Die einzige Relation, deren Zulaessigkeit vom Zustand des Ziels
    abhaengt: nur `SHARED` HeartMoments duerfen verknuepft sein (M3-D09).

    Diese Bedingung steht nicht nur im Dienst. `target_privacy_class`
    gehoert zum Fremdschluessel, der Fremdschluessel kaskadiert Updates,
    und ein CHECK nagelt die Spalte auf `SPACE_SHARED` fest. Wechselt ein
    HeartMoment auf `OWNER_ONLY`, ohne dass seine Relationen zuvor
    entfernt wurden, bricht die Transaktion ab.

    Der Dienst entfernt sie in derselben Transaktion und laeuft nie
    dagegen. Der Riegel ist fuer den Codepfad, den es noch nicht gibt.
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
