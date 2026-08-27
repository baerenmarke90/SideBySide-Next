"""Persistenz fuer gemeinsame M3-Wishes."""

from __future__ import annotations

from enum import StrEnum
from typing import ClassVar

from sqlalchemy import CheckConstraint, Index, SmallInteger, UniqueConstraint, text
from sqlalchemy import Enum as SqlEnum
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


class WishStatus(StrEnum):
    """Der Statusautomat aus M3-D02/D03/D04.

    Vollstaendig aufgefuehrt, aber in M3-S1 erreicht ein Wish nur `OPEN`:
    die beiden anderen Zustaende entstehen ausschliesslich aus dem noch
    nicht gebauten Wish->Plan-Vertrag. Die Werte stehen trotzdem schon in
    Modell und Datenbank, damit der spaetere Slice keine Statusmigration
    ueber bestehende Zeilen fahren muss.
    """

    OPEN = "OPEN"
    PLANNED = "PLANNED"
    COMPLETED = "COMPLETED"


def wish_status_type() -> SqlEnum:
    """Der Spaltentyp fuer `status`.

    Wie bei `privacy_class`: VARCHAR mit CHECK statt PostgreSQL-ENUM. Ein
    spaeterer Wert braucht dann eine gewoehnliche Migration und keine
    Typaenderung, die sich nur eingeschraenkt zurueckdrehen laesst.
    """
    return SqlEnum(
        *(status.value for status in WishStatus),
        name="wish_status",
        native_enum=False,
        create_constraint=True,
        validate_strings=True,
    )


class WishPayload(ProtectedPayload):
    """Schuetzenswerter Inhalt eines Wishes.

    Nur der Titel - ein Wish hat in M3 keinen Body. Er liegt trotzdem
    hinter der ProtectedPayload-Grenze: nach M3-D13 gehoert ein
    Wunschtitel weder in Logs noch in Eventnutzlasten, und Status,
    Sortierung und Autorisierung duerfen von seinem Klartext nicht
    abhaengen.
    """

    title: str


class Wish(
    IdMixin,
    TimestampMixin,
    VersionMixin,
    PrivateResourceMixin,
    Base,
):
    """Ein gemeinsamer Wunsch - beide lesen, beide schreiben.

    Anders als Memory und Milestone ist Wish nach M3-D01 collaborative
    write. `owner_id` traegt hier deshalb `createdBy`: Attribution und
    Audit, keine ACL.
    """

    __tablename__ = "wishes"

    privacy_absence: ClassVar[ResourceAbsence] = ResourceAbsence(
        "Wish not found.", "WISH_NOT_FOUND"
    )
    shared_write: ClassVar[SharedWrite] = SharedWrite.COLLABORATIVE

    status: Mapped[str] = mapped_column(
        wish_status_type(),
        nullable=False,
        default=WishStatus.OPEN.value,
        server_default=text("'OPEN'"),
    )
    crypto_version: Mapped[int] = mapped_column(
        SmallInteger,
        nullable=False,
        default=CRYPTO_VERSION_PLAINTEXT,
        server_default=text("0"),
    )
    payload: Mapped[WishPayload] = mapped_column(
        ProtectedPayloadJSON(WishPayload),
        nullable=False,
    )

    __table_args__ = (
        CheckConstraint("privacy_class = 'SPACE_SHARED'", name="privacy_is_space_shared"),
        CheckConstraint("crypto_version >= 0", name="crypto_version_is_non_negative"),
        # Traegt den zusammengesetzten Fremdschluessel von `plans`. Die ID
        # allein wuerde einen Plan auch auf einen Wish aus einem fremden
        # Space zeigen lassen - der Dienst verhindert das, aber die
        # Datenbank soll es ebenfalls nicht zulassen (M3-D02).
        UniqueConstraint("id", "space_id", name="uq_wishes_id_space_id"),
        Index("ix_wishes_owner_id", "owner_id"),
        Index("ix_wishes_space_id_created_at_id", "space_id", "created_at", "id"),
        Index("ix_wishes_space_id_status", "space_id", "status"),
    )


def shared_privacy() -> PrivacyClass:
    """Ein Wish ist immer gemeinsamer Space-Inhalt (M3-D01)."""
    return PrivacyClass.SPACE_SHARED
