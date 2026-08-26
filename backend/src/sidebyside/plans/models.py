"""Persistenz fuer gemeinsame M3-Plans."""

from __future__ import annotations

from datetime import date, datetime
from enum import StrEnum
from typing import ClassVar
from uuid import UUID

from sqlalchemy import (
    CheckConstraint,
    Date,
    DateTime,
    ForeignKeyConstraint,
    Index,
    SmallInteger,
    UniqueConstraint,
    text,
)
from sqlalchemy import Enum as SqlEnum
from sqlalchemy.dialects import postgresql
from sqlalchemy.orm import Mapped, mapped_column

from sidebyside.authorization import (
    PrivacyClass,
    PrivateResourceMixin,
    ResourceAbsence,
    SharedWrite,
)
from sidebyside.db.base import Base
from sidebyside.db.mixins import IdMixin, TimestampMixin, VersionMixin
from sidebyside.db.protected_payload import ProtectedPayloadJSON
from sidebyside.domain.payload import CRYPTO_VERSION_PLAINTEXT, ProtectedPayload


class PlanStatus(StrEnum):
    """Der Statusautomat aus M3-D04.

    ```text
    IDEA -- schedule --> PLANNED
    IDEA -- complete --> COMPLETED
    PLANNED -- unschedule --> IDEA
    PLANNED -- complete --> COMPLETED
    ```

    `COMPLETED` ist terminal. `return-to-wish` ist keine Kante dieses
    Automaten, sondern eine eigene Operation, die den Plan entfernt.
    """

    IDEA = "IDEA"
    PLANNED = "PLANNED"
    COMPLETED = "COMPLETED"


def plan_status_type() -> SqlEnum:
    """Der Spaltentyp fuer `status` - VARCHAR mit CHECK, wie bei Wish."""
    return SqlEnum(
        *(status.value for status in PlanStatus),
        name="plan_status",
        native_enum=False,
        create_constraint=True,
        validate_strings=True,
    )


class PlanPayload(ProtectedPayload):
    """Schuetzenswerter Inhalt eines Plans.

    Titel und Beschreibung liegen gemeinsam hinter der Grenze. Termine und
    Status bleiben ausserhalb: nach ihnen wird gefiltert und sortiert, und
    das muss auch dann noch gehen, wenn der Server den Klartext nicht mehr
    besitzt.
    """

    title: str
    description: str | None = None


class Plan(
    IdMixin,
    TimestampMixin,
    VersionMixin,
    PrivateResourceMixin,
    Base,
):
    """Ein gemeinsames Vorhaben - beide lesen, beide schreiben.

    Ein Plan entsteht auf zwei Wegen: aus einem Wish (M3-D02) oder direkt
    (M3-D30). Der Unterschied steht in genau einem Feld, `source_wish_id`,
    und er entscheidet ueber Completion-Folgen, `return-to-wish` und die
    Delete-Matrix.
    """

    __tablename__ = "plans"

    privacy_absence: ClassVar[ResourceAbsence] = ResourceAbsence(
        "Plan not found.", "PLAN_NOT_FOUND"
    )
    shared_write: ClassVar[SharedWrite] = SharedWrite.COLLABORATIVE

    status: Mapped[str] = mapped_column(
        plan_status_type(),
        nullable=False,
        default=PlanStatus.IDEA.value,
        server_default=text("'IDEA'"),
    )
    source_wish_id: Mapped[UUID | None] = mapped_column(postgresql.UUID(as_uuid=True))
    """Der Wish, aus dem dieser Plan entstanden ist - oder NULL.

    Eindeutig, damit ein Wish zu keinem Zeitpunkt zwei originaere Plans
    hat. PostgreSQL laesst in einem UNIQUE beliebig viele NULL zu; Direct
    Plans stehen sich damit nicht gegenseitig im Weg.
    """

    planned_start: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    planned_end: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    experienced_on: Mapped[date | None] = mapped_column(Date)
    """Der Kalendertag des Erlebnisses - ein fachlicher Tag, keine Zeitpunkt.

    Deshalb DATE und nicht TIMESTAMPTZ: ein erlebter Tag hat keine
    Zeitzone, und als Zeitpunkt gespeichert verschoebe er sich.
    """

    crypto_version: Mapped[int] = mapped_column(
        SmallInteger,
        nullable=False,
        default=CRYPTO_VERSION_PLAINTEXT,
        server_default=text("0"),
    )
    payload: Mapped[PlanPayload] = mapped_column(
        ProtectedPayloadJSON(PlanPayload),
        nullable=False,
    )

    __table_args__ = (
        CheckConstraint("privacy_class = 'SPACE_SHARED'", name="privacy_is_space_shared"),
        CheckConstraint("crypto_version >= 0", name="crypto_version_is_non_negative"),
        # Die Datumsinvarianten aus M3-D04. Sie stehen zusaetzlich im
        # Dienst; hier sind sie die Grenze, die auch ein Wartungsskript
        # oder eine spaetere Migration nicht unterlaufen kann.
        CheckConstraint(
            "planned_end IS NULL OR planned_start IS NOT NULL",
            name="planned_end_needs_start",
        ),
        CheckConstraint(
            "planned_end IS NULL OR planned_end >= planned_start",
            name="planned_end_not_before_start",
        ),
        CheckConstraint(
            "status <> 'IDEA' OR (planned_start IS NULL AND planned_end IS NULL)",
            name="idea_has_no_schedule",
        ),
        CheckConstraint(
            "status <> 'PLANNED' OR planned_start IS NOT NULL",
            name="planned_needs_start",
        ),
        CheckConstraint(
            "status <> 'COMPLETED' OR experienced_on IS NOT NULL",
            name="completed_needs_experienced_on",
        ),
        UniqueConstraint("source_wish_id", name="uq_plans_source_wish_id"),
        # Zusammengesetzt statt nur auf `id`: so kann ein Plan nicht auf
        # einen Wish aus einem fremden Space zeigen. Weil `source_wish_id`
        # NULL sein darf und PostgreSQL einen Fremdschluessel mit NULL-
        # Anteil nicht prueft, bleibt Direct Plan Create davon unberuehrt.
        #
        # Ohne ON DELETE: ein Wish mit originaerem Plan verschwindet nicht
        # nebenbei. M3-D05 verbietet eine versteckte Cascade Wish -> Plan,
        # und der Dienst weist den Fall vorher mit einem fachlichen 409 ab.
        ForeignKeyConstraint(
            ["source_wish_id", "space_id"],
            ["wishes.id", "wishes.space_id"],
            name="fk_plans_source_wish_id_wishes",
        ),
        Index("ix_plans_owner_id", "owner_id"),
        Index("ix_plans_space_id_created_at_id", "space_id", "created_at", "id"),
        Index("ix_plans_space_id_status", "space_id", "status"),
        Index("ix_plans_space_id_planned_start", "space_id", "planned_start"),
    )


def shared_privacy() -> PrivacyClass:
    """Ein Plan ist immer gemeinsamer Space-Inhalt (M3-D01)."""
    return PrivacyClass.SPACE_SHARED
