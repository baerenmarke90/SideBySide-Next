"""Persistenz fuer gemeinsame M3-Places."""

from __future__ import annotations

from decimal import Decimal
from typing import ClassVar

from sqlalchemy import CheckConstraint, Index, Numeric, SmallInteger, UniqueConstraint, text
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

COORDINATE_PLACES = 6
"""Nachkommastellen, die persistiert werden (M3-D06).

Sechs Stellen sind rund elf Zentimeter. Mehr waere keine Genauigkeit,
sondern nur eine praezisere Aussage darueber, wo zwei Menschen waren -
und genau die soll nicht ungefragt entstehen.
"""

LATITUDE_LIMIT = Decimal(90)
LONGITUDE_LIMIT = Decimal(180)


class PlacePayload(ProtectedPayload):
    """Der schuetzenswerte Textinhalt eines Places.

    Name, Beschreibung und Adresse liegen hinter der Grenze. Die
    Koordinaten liegen nach M3-D06 ausdruecklich daneben als typisierte
    Spalten - fuer Validierung und spaetere Kartenfunktionen. Ihre
    Klassifizierung aendert das nicht: sie bleiben sensibler Inhalt und
    gehoeren in kein Log, kein Event und kein Metriklabel.
    """

    name: str
    description: str | None = None
    address: str | None = None


class Place(
    IdMixin,
    TimestampMixin,
    VersionMixin,
    PrivateResourceMixin,
    Base,
):
    """Ein gemeinsamer Ort.

    Ein Place darf ohne Koordinaten existieren - viele Orte eines Paares
    sind ein Name und sonst nichts. Es gibt keine Deduplizierung: zwei
    Orte mit demselben Namen sind zwei Orte, und sie ungefragt
    zusammenzufuehren waere eine Datenaenderung, die niemand angefordert
    hat (M3-D07).
    """

    __tablename__ = "places"

    privacy_absence: ClassVar[ResourceAbsence] = ResourceAbsence(
        "Place not found.", "PLACE_NOT_FOUND"
    )
    shared_write: ClassVar[SharedWrite] = SharedWrite.COLLABORATIVE

    # 90.000000 braucht acht Stellen, 180.000000 neun. Numeric und nicht
    # Float: eine Koordinate ist eine Dezimalzahl mit fester Genauigkeit,
    # und binaere Rundung wuerde sie bei jedem Schreiben leicht verschieben.
    latitude: Mapped[Decimal | None] = mapped_column(Numeric(8, COORDINATE_PLACES))
    longitude: Mapped[Decimal | None] = mapped_column(Numeric(9, COORDINATE_PLACES))

    crypto_version: Mapped[int] = mapped_column(
        SmallInteger,
        nullable=False,
        default=CRYPTO_VERSION_PLAINTEXT,
        server_default=text("0"),
    )
    payload: Mapped[PlacePayload] = mapped_column(
        ProtectedPayloadJSON(PlacePayload),
        nullable=False,
    )

    __table_args__ = (
        CheckConstraint("privacy_class = 'SPACE_SHARED'", name="privacy_is_space_shared"),
        CheckConstraint("crypto_version >= 0", name="crypto_version_is_non_negative"),
        # Beide oder keine (M3-D06). Eine halbe Koordinate ist kein Ort,
        # sondern ein Breitengrad - und die Karte spraenge irgendwohin.
        CheckConstraint(
            "(latitude IS NULL) = (longitude IS NULL)",
            name="coordinates_are_a_pair",
        ),
        CheckConstraint(
            "latitude IS NULL OR (latitude >= -90 AND latitude <= 90)",
            name="latitude_within_range",
        ),
        CheckConstraint(
            "longitude IS NULL OR (longitude >= -180 AND longitude <= 180)",
            name="longitude_within_range",
        ),
        # Traegt den zusammengesetzten Fremdschluessel von `plans`, wie
        # `wishes` ihn fuer `source_wish_id` traegt.
        UniqueConstraint("id", "space_id", name="uq_places_id_space_id"),
        Index("ix_places_owner_id", "owner_id"),
        Index("ix_places_space_id_created_at_id", "space_id", "created_at", "id"),
    )


def shared_privacy() -> PrivacyClass:
    """Ein Place ist immer gemeinsamer Space-Inhalt (M3-D06)."""
    return PrivacyClass.SPACE_SHARED
