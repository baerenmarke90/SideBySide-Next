"""Eine minimale Ressource, an der sich die Autorisierung pruefen laesst.

Bewusst keine Fachdomaene. Die Autorisierungsgrundlage soll fuer beliebige
spaetere Domaenen gelten, und ein Test, der an HeartMoments haengt, wuerde
sie an deren Fachlichkeit binden - und nebenbei M2-Code entstehen lassen,
der noch nicht freigegeben ist.

Die Sonde traegt deshalb genau das, was die Autorisierung braucht: die drei
Spalten aus `PrivateResourceMixin` und ein Textfeld, an dem ein Leck
sichtbar wuerde.

Die Tabelle haengt an `Base.metadata`, weil ihre Fremdschluessel auf
`spaces` und `accounts` zeigen. Sie entsteht ausschliesslich ueber
`create_all` in der Testvorrichtung: `alembic/env.py` importiert nur
produktive Modelle, die Sonde erscheint also in keiner Migration und in
keiner Produktionsdatenbank.
"""

from __future__ import annotations

from typing import ClassVar

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from sidebyside.authorization import PrivateResourceMixin, ResourceAbsence
from sidebyside.db.base import Base
from sidebyside.db.mixins import IdMixin, TimestampMixin


class PrivacyProbe(IdMixin, TimestampMixin, PrivateResourceMixin, Base):
    __tablename__ = "privacy_probes"

    privacy_absence: ClassVar[ResourceAbsence] = ResourceAbsence(
        "Probe not found.", "PRIVACY_PROBE_NOT_FOUND"
    )

    label: Mapped[str] = mapped_column(String(64), nullable=False)
