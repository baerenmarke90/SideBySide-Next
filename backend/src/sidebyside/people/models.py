"""Persistenz fuer nahestehende Personen und wichtige Termine.

Ein Kind, ein Elternteil, eine Freundin: fuer SideBySide sind das keine
Accounts. Sie melden sich nicht an, sie haben keine Sitzung und sie
bekommen keine Einladung. Sie sind ein Eintrag, den ein Partner in seinem
Space fuehrt - und damit Daten ueber Dritte, die diese Dritten nicht selbst
verwalten koennen. Deshalb steht hier weniger, als technisch moeglich
waere: Anzeigename, Art der Beziehung, ein Geburtstag. Keine Adresse,
keine Schule, keine Telefonnummer.

Der Anzeigename und das Etikett eines Termins sind der schuetzenswerte
Teil und liegen als `ProtectedPayload` getrennt von den Metadaten. Was zum
Sortieren, Verknuepfen und spaeter zum Erinnern gebraucht wird - Beziehung,
Datum, Wiederholung, Sichtbarkeit - bleibt als Spalte abfragbar.
"""

from __future__ import annotations

from datetime import date
from enum import StrEnum
from typing import ClassVar
from uuid import UUID

from pydantic import Field
from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Date,
    ForeignKeyConstraint,
    Index,
    SmallInteger,
    String,
    UniqueConstraint,
    text,
)
from sqlalchemy.dialects import postgresql
from sqlalchemy.orm import Mapped, mapped_column

from sidebyside.authorization import (
    PrivateResourceMixin,
    ResourceAbsence,
)
from sidebyside.db.base import Base
from sidebyside.db.mixins import IdMixin, TimestampMixin, VersionMixin
from sidebyside.db.protected_payload import ProtectedPayloadJSON
from sidebyside.domain.payload import CRYPTO_VERSION_PLAINTEXT, ProtectedPayload


class PersonRelationship(StrEnum):
    CHILD = "CHILD"
    PARENT = "PARENT"
    SIBLING = "SIBLING"
    FRIEND = "FRIEND"
    OTHER = "OTHER"


class ImportantDateType(StrEnum):
    BIRTHDAY = "BIRTHDAY"
    ANNIVERSARY = "ANNIVERSARY"
    CUSTOM = "CUSTOM"


class DateRepeat(StrEnum):
    """Wie oft ein Termin wiederkehrt.

    Bewusst nur zwei Werte. Eine vollstaendige Wiederholungsregel gehoert
    zur spaeteren Erinnerungslogik; ein Geburtstag und ein Jahrestag
    brauchen sie nicht.
    """

    NONE = "NONE"
    ANNUALLY = "ANNUALLY"


UNKNOWN_BIRTH_YEAR = 1904
"""Platzhalterjahr fuer einen Geburtstag ohne bekanntes Jahr.

`DATE` kennt kein Datum ohne Jahr. Statt Monat und Tag in zwei eigene
Spalten zu zerlegen - und damit jede Datumsrechnung zu verdoppeln - wird
ein festes Jahr eingesetzt und `birthday_year_known` sagt, dass es nichts
bedeutet. 1904 ist ein Schaltjahr: der 29. Februar bleibt speicherbar.

Die Datenbank erzwingt den Platzhalter, damit nicht eine zweite Stelle im
Code ein anderes Jahr waehlt und die beiden Bestaende danach nicht mehr
vergleichbar sind.
"""


class RelatedPersonPayload(ProtectedPayload):
    """Der schuetzenswerte Klartext einer nahestehenden Person."""

    display_name: str = Field(min_length=1, max_length=120)


class ImportantDatePayload(ProtectedPayload):
    """Das schuetzenswerte Etikett eines Termins."""

    label: str = Field(min_length=1, max_length=120)


class RelatedPerson(IdMixin, TimestampMixin, VersionMixin, PrivateResourceMixin, Base):
    """Eine Person im Umfeld des Paares, die selbst keinen Account hat."""

    __tablename__ = "related_persons"

    privacy_absence: ClassVar[ResourceAbsence] = ResourceAbsence(
        "Related person not found.", "RELATED_PERSON_NOT_FOUND"
    )

    relationship: Mapped[str] = mapped_column(String(16), nullable=False)
    birthday: Mapped[date | None] = mapped_column(Date)
    birthday_year_known: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, server_default=text("false")
    )
    crypto_version: Mapped[int] = mapped_column(
        SmallInteger,
        nullable=False,
        default=CRYPTO_VERSION_PLAINTEXT,
        server_default=text("0"),
    )
    payload: Mapped[RelatedPersonPayload] = mapped_column(
        ProtectedPayloadJSON(RelatedPersonPayload),
        nullable=False,
    )

    __table_args__ = (
        # Zielspalten der zusammengesetzten Fremdschluessel aus
        # `important_dates`. Ohne diese Eindeutigkeit koennte ein Termin
        # seinen Space und die Privacy-Klasse seiner Person nicht auf
        # Datenbankebene mitfuehren.
        UniqueConstraint(
            "id",
            "space_id",
            "privacy_class",
            name="uq_related_persons_person_link",
        ),
        CheckConstraint(
            "relationship IN ('CHILD', 'PARENT', 'SIBLING', 'FRIEND', 'OTHER')",
            name="relationship_is_known",
        ),
        CheckConstraint(
            "birthday IS NOT NULL OR birthday_year_known IS FALSE",
            name="known_year_needs_a_birthday",
        ),
        CheckConstraint(
            f"birthday IS NULL OR birthday_year_known IS TRUE "
            f"OR EXTRACT(YEAR FROM birthday) = {UNKNOWN_BIRTH_YEAR}",
            name="unknown_year_is_normalized",
        ),
        CheckConstraint("crypto_version >= 0", name="crypto_version_is_non_negative"),
    )


class ImportantDate(IdMixin, TimestampMixin, VersionMixin, PrivateResourceMixin, Base):
    """Ein Datum, das dem Paar wichtig ist - meist zu einer nahestehenden Person.

    `related_person_id` ist optional: der eigene Jahrestag gehoert zu
    niemandem sonst. Ist er gesetzt, fuehrt die Zeile die Privacy-Klasse
    ihrer Person als Kopie mit und beide zusammen sind ein
    Fremdschluessel. Das erledigt zwei Dinge auf einmal, die sonst zwei
    Serviceprueffungen waeren:

    - Der Space stimmt. Ein Termin kann nicht auf eine Person aus einem
      fremden Space zeigen, auch nicht durch einen Fehler in der
      Fachlogik.
    - Ein Termin ist nie offener als seine Person. Ein `SPACE_SHARED`
      Termin an einer `OWNER_ONLY` Person waere die Auskunft, dass es
      diese Person gibt - und genau die soll der private Eintrag
      verhindern.

    `ON UPDATE CASCADE` haelt die Kopie aktuell, `ON DELETE CASCADE`
    raeumt die Termine einer geloeschten Person mit ab. Ein `SET NULL`
    waere hier nicht moeglich: `space_id` ist Teil desselben
    Fremdschluessels und darf nicht leer werden.
    """

    __tablename__ = "important_dates"

    privacy_absence: ClassVar[ResourceAbsence] = ResourceAbsence(
        "Important date not found.", "IMPORTANT_DATE_NOT_FOUND"
    )

    related_person_id: Mapped[UUID | None] = mapped_column(postgresql.UUID(as_uuid=True))
    related_person_privacy_class: Mapped[str | None] = mapped_column(String(12))
    type: Mapped[str] = mapped_column(String(16), nullable=False)
    date: Mapped[date] = mapped_column(Date, nullable=False)
    repeats: Mapped[str] = mapped_column(String(16), nullable=False)
    crypto_version: Mapped[int] = mapped_column(
        SmallInteger,
        nullable=False,
        default=CRYPTO_VERSION_PLAINTEXT,
        server_default=text("0"),
    )
    payload: Mapped[ImportantDatePayload] = mapped_column(
        ProtectedPayloadJSON(ImportantDatePayload),
        nullable=False,
    )

    __table_args__ = (
        ForeignKeyConstraint(
            ["related_person_id", "space_id", "related_person_privacy_class"],
            [
                "related_persons.id",
                "related_persons.space_id",
                "related_persons.privacy_class",
            ],
            name="fk_important_dates_related_person",
            ondelete="CASCADE",
            onupdate="CASCADE",
        ),
        CheckConstraint(
            "type IN ('BIRTHDAY', 'ANNIVERSARY', 'CUSTOM')",
            name="type_is_known",
        ),
        CheckConstraint("repeats IN ('NONE', 'ANNUALLY')", name="repeats_is_known"),
        CheckConstraint(
            "(related_person_id IS NULL) = (related_person_privacy_class IS NULL)",
            name="person_link_is_complete",
        ),
        CheckConstraint(
            "related_person_privacy_class IS DISTINCT FROM 'OWNER_ONLY' "
            "OR privacy_class = 'OWNER_ONLY'",
            name="never_more_open_than_its_person",
        ),
        CheckConstraint("crypto_version >= 0", name="crypto_version_is_non_negative"),
        Index(
            "ix_important_dates_space_id_related_person_id",
            "space_id",
            "related_person_id",
        ),
        Index("ix_important_dates_space_id_date", "space_id", "date"),
        Index("ix_important_dates_owner_id", "owner_id"),
    )
