"""Die Spalten, die eine Ressource autorisierbar machen.

Ein Mixin und keine gemeinsame Tabelle. Eine Universal-Content-Tabelle
waere der bequeme Weg - und der falsche: sie zwingt fremde Domaenen in ein
gemeinsames Schema, macht jede Fremdschluesselbeziehung generisch und legt
den gesamten Bestand hinter genau eine Abfrage. Jede Domaene behaelt ihre
eigene Tabelle; gemeinsam ist nur die Form der drei Spalten und die Regel,
die darauf arbeitet.
"""

from __future__ import annotations

from typing import ClassVar, Protocol
from uuid import UUID

from sqlalchemy import ForeignKey
from sqlalchemy.dialects import postgresql
from sqlalchemy.orm import Mapped, mapped_column

from sidebyside.authorization.privacy import (
    DEFAULT_ABSENCE,
    ResourceAbsence,
    privacy_class_type,
)


class PrivateResource(Protocol):
    """Was der Guard von einem Modell braucht.

    Absichtlich strukturell: der Guard soll gegen die Form arbeiten, nicht
    gegen eine Vererbungslinie. Ein Modell, das diese vier Spalten hat,
    kann autorisiert werden - unabhaengig davon, aus welchen Mixins es
    zusammengesetzt ist.
    """

    id: Mapped[UUID]
    space_id: Mapped[UUID]
    owner_id: Mapped[UUID]
    privacy_class: Mapped[str]

    privacy_absence: ClassVar[ResourceAbsence]


class PrivateResourceMixin:
    """Space, Eigentuemer und Privacy-Klasse an einer Domaenentabelle.

    `space_id` beantwortet die Mandantenfrage, `owner_id` die
    Eigentuemerfrage, `privacy_class` sagt, welche der beiden entscheidet.
    Alle drei sind Pflicht: eine Ressource ohne Klasse waere eine Ressource
    mit stillschweigender Sichtbarkeit.

    Der Eigentuemer ist der Account, nicht die Mitgliedschaft. Eine
    beendete und spaeter wiederbelebte Mitgliedschaft darf die Zuordnung
    eines privaten Inhalts nicht verschieben.
    """

    privacy_absence: ClassVar[ResourceAbsence] = DEFAULT_ABSENCE
    """Die Antwort dieser Domaene auf "gibt es nicht, jedenfalls nicht fuer dich".

    Einmal je Domaene gesetzt statt bei jedem Aufruf uebergeben - sonst
    entstehen im Lauf der Zeit doch wieder unterschiedliche Antworten fuer
    dieselbe Ressource, und der Unterschied ist die Auskunft.
    """

    space_id: Mapped[UUID] = mapped_column(
        postgresql.UUID(as_uuid=True),
        ForeignKey("spaces.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    owner_id: Mapped[UUID] = mapped_column(
        postgresql.UUID(as_uuid=True),
        ForeignKey("accounts.id", ondelete="CASCADE"),
        nullable=False,
    )
    privacy_class: Mapped[str] = mapped_column(privacy_class_type(), nullable=False)
