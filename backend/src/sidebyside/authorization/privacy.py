"""Privacy-Klassen - die Sprache, in der eine Domaene ihre Sichtbarkeit sagt.

Der Tenant Guard beantwortet die Frage "gehoert dieser Account zu diesem
Space?". Fuer private Inhalte reicht das nicht: der Partner ist Mitglied
desselben Space und trotzdem kein berechtigter Leser. Diese Datei traegt
die zweite Frage - "welche Klasse hat diese Ressource, und was folgt daraus
fuer genau diesen Account?".

Es gibt keine implizite oeffentliche Klasse. Eine Ressource ohne Klasse
laesst sich nicht speichern.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from uuid import UUID

from sqlalchemy import Enum as SqlEnum

from sidebyside.core.errors import NotFoundError


class PrivacyClass(StrEnum):
    """Die Klassen aus der Spezifikation, Abschnitt 7.

    Vollstaendig aufgefuehrt, damit der Begriff im Code derselbe ist wie in
    der Spezifikation und in docs/PRIVACY-MODEL.md. Aufgefuehrt heisst
    aber nicht durchsetzbar: erzwingbar ist nur, wofuer es eine Regel und
    eine Speicherform gibt.
    """

    SPACE_SHARED = "SPACE_SHARED"
    OWNER_ONLY = "OWNER_ONLY"
    TEMPORARY_SHARED = "TEMPORARY_SHARED"
    EPHEMERAL_CONTEXT = "EPHEMERAL_CONTEXT"
    SYSTEM_METADATA = "SYSTEM_METADATA"


class ContentVisibility(StrEnum):
    """Die fachliche Sichtbarkeit aus Abschnitt 15 der Spezifikation.

    Der Request nennt sie, nicht die Privacy-Klasse: `privacyClass` ist
    eine serverseitige Ableitung und kein Feld, das ein Client setzen kann.

    Sie steht hier und nicht in einer Domaene, weil sie keiner gehoert:
    RelatedPerson, ImportantDate und HeartMoment sprechen dieselbe
    Sichtbarkeit. Laege sie bei der ersten Domaene, die sie brauchte,
    importierten alle spaeteren aus einem fremden Fachmodul.
    """

    SHARED = "SHARED"
    PRIVATE = "PRIVATE"


def privacy_for(visibility: ContentVisibility) -> PrivacyClass:
    """Die Privacy-Klasse folgt der fachlichen Sichtbarkeit, nicht dem Request."""
    if visibility is ContentVisibility.SHARED:
        return PrivacyClass.SPACE_SHARED
    return PrivacyClass.OWNER_ONLY


def visibility_of(privacy_class: str) -> ContentVisibility:
    if privacy_class == PrivacyClass.SPACE_SHARED.value:
        return ContentVisibility.SHARED
    return ContentVisibility.PRIVATE


ENFORCEABLE_PRIVACY_CLASSES: tuple[PrivacyClass, ...] = (
    PrivacyClass.SPACE_SHARED,
    PrivacyClass.OWNER_ONLY,
)
"""Klassen, fuer die der Server heute eine Abfrageregel besitzt.

Eine Klasse, die der Server nicht durchsetzen kann, darf auch nicht in der
Datenbank stehen. Sonst gaebe es Zeilen, deren Schutz niemand einloest -
und der spaetere Zusatz einer Regel entschiede rueckwirkend ueber
bestehende Daten.

Eine Klasse aufzunehmen bedeutet deshalb drei Dinge zusammen: eine Regel in
`authorization.rules`, ein Eintrag hier und eine Migration, die den
Wertebereich der bestehenden Tabellen erweitert.
"""


def privacy_class_type() -> SqlEnum:
    """Der Spaltentyp fuer `privacy_class`.

    Kein freier Text: die Datenbank laesst nur Klassen zu, die der Server
    auch durchsetzt. `native_enum=False` haelt den Wert als VARCHAR mit
    CHECK - ein neuer Wert braucht dann eine gewoehnliche Migration statt
    einer Typaenderung, die PostgreSQL nur eingeschraenkt zurueckdrehen
    kann.
    """
    return SqlEnum(
        *(klasse.value for klasse in ENFORCEABLE_PRIVACY_CLASSES),
        name="privacy_class",
        native_enum=False,
        create_constraint=True,
        validate_strings=True,
    )


@dataclass(frozen=True)
class AuthorizationContext:
    """Wer fragt, und in welchem Space.

    Entsteht ausschliesslich aus einem bereits geprueften Tenant Context.
    Beide Werte stammen vom Server: der Account aus dem Bearer Token, der
    Space aus der geprueften Mitgliedschaft. Nichts davon kommt aus dem
    Request-Body.
    """

    account_id: UUID
    space_id: UUID


@dataclass(frozen=True)
class ResourceAbsence:
    """Wie eine Domaene klingt, wenn es die Ressource fuer den Frager nicht gibt.

    Genau eine Antwort fuer drei verschiedene Ursachen: die ID ist
    fehlgeformt, die Ressource existiert nicht, oder sie existiert und geht
    diesen Account nichts an. Waeren es drei Antworten, waere die
    Fehlerantwort eine Existenzauskunft.
    """

    detail: str
    code: str

    def error(self) -> NotFoundError:
        return NotFoundError(self.detail, self.code)


class AuthorizationErrorCode:
    RESOURCE_NOT_FOUND = "RESOURCE_NOT_FOUND"
    NOT_RESOURCE_OWNER = "NOT_RESOURCE_OWNER"


DEFAULT_ABSENCE = ResourceAbsence("Resource not found.", AuthorizationErrorCode.RESOURCE_NOT_FOUND)
"""Fallback fuer Domaenen, die keinen eigenen Text gesetzt haben."""
