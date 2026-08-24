"""Das SpaceProfile lesen und schreiben.

Beziehungsbezogene Angaben zum Space: seit wann, ob die gemeinsame Zeit
angezeigt wird und in welcher Form.

Geschrieben wird ausschliesslich mit Optimistic Concurrency. Zwei Partner
bearbeiten dasselbe Profil oft kurz nacheinander vom Telefon aus; ohne
Versionspruefung wuerde der zweite Schreibvorgang die Aenderung des ersten
still ueberschreiben. Der Konflikt gehoert dem Menschen vorgelegt, nicht
weggeraeumt.
"""

from __future__ import annotations

from datetime import date
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session
from sqlalchemy.orm.exc import StaleDataError

from sidebyside.core.errors import ConflictError, ErrorCode, NotFoundError, ValidationError
from sidebyside.relationship.models import DurationDisplayMode, Space, SpaceProfile
from sidebyside.relationship.service import SpaceErrorCode

EARLIEST_RELATIONSHIP_START = date(1900, 1, 1)
"""Untergrenze fuer einen Beziehungsbeginn.

Kein fachliches Verbot, sondern ein Tippfehlerfilter: aus einer verrutschten
Jahreszahl wuerden sonst sechsstellige "gemeinsame Tage".
"""


class SpaceProfileErrorCode:
    START_IN_FUTURE = "RELATIONSHIP_START_IN_FUTURE"
    START_TOO_EARLY = "RELATIONSHIP_START_TOO_EARLY"


def load(session: Session, space_id: UUID) -> SpaceProfile | None:
    """Das Profil eines Space, ohne es anzulegen.

    Ausdruecklich auf `space_id` eingeschraenkt und nicht ueber eine
    Profil-ID erreichbar: es gibt keinen Datenzugriff allein anhand einer
    Ressourcen-ID.
    """
    return session.execute(
        select(SpaceProfile).where(SpaceProfile.space_id == space_id)
    ).scalar_one_or_none()


def _locked_profile(session: Session, space_id: UUID) -> SpaceProfile:
    """Das Profil zum Schreiben holen und konkurrierende Schreiber reihen.

    Die Space-Zeile ist die Serialisierungsstelle. Ein zweiter Schreiber
    wartet hier, liest danach den bereits geschriebenen Stand und sieht
    deshalb eine hoehere Version - der 409 entsteht deterministisch und
    nicht je nach zeitlichem Zufall.

    Fehlt das Profil, wird es angelegt. `create_space` legt es normalerweise
    mit an; ein Space ohne Profil ist ein Altbestand und kein Grund, eine
    Aenderung abzulehnen.
    """
    space = session.execute(
        select(Space).where(Space.id == space_id).with_for_update()
    ).scalar_one_or_none()
    if space is None:
        raise NotFoundError("Space not found.", SpaceErrorCode.NOT_FOUND)

    profil = session.execute(
        select(SpaceProfile)
        .where(SpaceProfile.space_id == space_id)
        .execution_options(populate_existing=True)
    ).scalar_one_or_none()

    if profil is None:
        profil = SpaceProfile(space_id=space_id)
        session.add(profil)
        session.flush()

    return profil


def _validate_start(started_on: date | None, today: date) -> None:
    if started_on is None:
        return
    if started_on > today:
        raise ValidationError(
            "The relationship cannot start in the future.",
            SpaceProfileErrorCode.START_IN_FUTURE,
        )
    if started_on < EARLIEST_RELATIONSHIP_START:
        raise ValidationError(
            "The relationship start date is implausibly early.",
            SpaceProfileErrorCode.START_TOO_EARLY,
        )


def update(
    session: Session,
    space_id: UUID,
    *,
    expected_version: int,
    relationship_started_on: date | None,
    show_relationship_duration: bool,
    duration_display_mode: DurationDisplayMode,
    today: date,
) -> SpaceProfile:
    """Das Profil vollstaendig ersetzen, sofern die Version noch stimmt.

    `expected_version` ist der Stand, den der Aufrufer gelesen hat. Weicht
    er ab, hat der Partner inzwischen geschrieben: 409, und nichts wird
    veraendert.

    `today` ist der Kalendertag in der Zeitzone des Aufrufers. Er entscheidet
    darueber, ob ein Datum in der Zukunft liegt - ein Beginn "heute" ist
    westlich von UTC sonst je nach Uhrzeit unzulaessig.
    """
    profil = _locked_profile(session, space_id)

    if profil.version != expected_version:
        raise ConflictError(
            "The space profile was changed by someone else.",
            ErrorCode.VERSION_CONFLICT,
        )

    _validate_start(relationship_started_on, today)

    profil.relationship_started_on = relationship_started_on
    profil.show_relationship_duration = show_relationship_duration
    profil.duration_display_mode = duration_display_mode.value

    try:
        session.flush()
    except StaleDataError as stale:
        # Zweite, unabhaengige Absicherung. Die Versionsspalte wird beim
        # UPDATE mitgeprueft; selbst wenn die Serialisierung oben je
        # umgangen wuerde, entstuende hier kein Lost Update, sondern
        # dieselbe Antwort. Zurueckgerollt wird an der Transaktionsgrenze
        # der Anfrage, nicht hier - ein Teil-Rollback mitten im Vorgang
        # wuerde auch alles zuruecknehmen, was vorher dazugehoerte.
        raise ConflictError(
            "The space profile was changed by someone else.",
            ErrorCode.VERSION_CONFLICT,
        ) from stale

    return profil
