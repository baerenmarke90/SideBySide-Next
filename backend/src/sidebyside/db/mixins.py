"""Wiederkehrende Spaltenmuster für Domain-Objekte."""

from __future__ import annotations

from datetime import datetime
from typing import Any, ClassVar
from uuid import UUID

from sqlalchemy import DateTime, Integer, func
from sqlalchemy.dialects import postgresql
from sqlalchemy.orm import Mapped, mapped_column

from sidebyside.core.ids import new_id


class IdMixin:
    """UUIDv7 als Primärschlüssel."""

    id: Mapped[UUID] = mapped_column(
        postgresql.UUID(as_uuid=True), primary_key=True, default=new_id
    )


class TimestampMixin:
    """Technische Zeitpunkte, immer zeitzonen-bewusst.

    `server_default` und `onupdate` liegen auf der Datenbank, damit auch ein
    Schreibvorgang außerhalb des ORM - eine Migration, ein Wartungsskript -
    keine leeren Zeitstempel hinterlässt.
    """

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )


class VersionMixin:
    """Optimistic Concurrency.

    SQLAlchemy zählt die Spalte bei jedem Update hoch und prüft beim
    Schreiben den gelesenen Stand. Weicht er ab, hat jemand anderes
    dazwischen geschrieben - das muss ein 409 werden und kein stilles
    Überschreiben.

    Zugleich die Vorbereitung auf späteren Offline-Sync: ohne Versionsbegriff
    lässt sich ein Konflikt nicht von einer normalen Änderung unterscheiden.
    """

    version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)

    __mapper_args__: ClassVar[dict[str, Any]] = {"version_id_col": version}
