"""Fachlogik fuer nahestehende Personen und wichtige Termine.

Jede Liste und jeder Detailzugriff beginnt beim zentralen Owner-/Privacy-
Guard. Private Zeilen fallen damit in SQL heraus und nicht erst in der
Serialisierung.

Die Regeln, die ueber die reine Sichtbarkeit hinausgehen, stehen an genau
zwei Stellen: als Constraint im Schema und - damit der Client eine
verstaendliche Antwort bekommt statt eines Datenbankfehlers - als Pruefung
hier davor.
"""

from __future__ import annotations

from collections.abc import Sequence
from datetime import date
from enum import Enum
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session
from sqlalchemy.orm.exc import StaleDataError

from sidebyside.authorization import (
    AuthorizationContext,
    PrivacyClass,
    readable,
    require_readable,
    require_writable,
)
from sidebyside.core.errors import ConflictError, ErrorCode, ValidationError
from sidebyside.people.models import (
    UNKNOWN_BIRTH_YEAR,
    ContentVisibility,
    DateRepeat,
    ImportantDate,
    ImportantDatePayload,
    ImportantDateType,
    PersonRelationship,
    RelatedPerson,
    RelatedPersonPayload,
    privacy_for,
)


class PeopleErrorCode:
    DISPLAY_NAME_REQUIRED = "RELATED_PERSON_DISPLAY_NAME_REQUIRED"
    BIRTHDAY_REQUIRED = "RELATED_PERSON_BIRTHDAY_REQUIRED"
    HAS_SHARED_DATES = "RELATED_PERSON_HAS_SHARED_DATES"
    LABEL_REQUIRED = "IMPORTANT_DATE_LABEL_REQUIRED"
    MORE_OPEN_THAN_PERSON = "IMPORTANT_DATE_MORE_OPEN_THAN_PERSON"


class RelatedPersonDeletePolicy(str, Enum):
    PRESERVE = "preserve"
    CASCADE = "cascade"


def _clean_text(value: str, code: str) -> str:
    cleaned = value.strip()
    if not cleaned:
        raise ValidationError("The value must not be empty.", code)
    return cleaned


def normalize_birthday(birthday: date | None, *, year_known: bool) -> date | None:
    """Den Geburtstag in die Form bringen, die gespeichert wird.

    Ohne bekanntes Jahr bekommt das Datum das Platzhalterjahr. Der Wert
    bleibt damit ein `DATE` und laesst sich mit jedem anderen Geburtstag
    vergleichen; dass sein Jahr nichts bedeutet, sagt `birthdayYearKnown`.

    Ein bekanntes Jahr ohne Datum ist keine unvollstaendige Angabe, die
    still zurechtgebogen wird - es ist ein Widerspruch und wird abgelehnt.
    """
    if birthday is None:
        if year_known:
            raise ValidationError(
                "A known birth year needs a birthday.",
                PeopleErrorCode.BIRTHDAY_REQUIRED,
            )
        return None
    if year_known:
        return birthday
    return birthday.replace(year=UNKNOWN_BIRTH_YEAR)


def list_persons(session: Session, context: AuthorizationContext) -> Sequence[RelatedPerson]:
    return (
        session.execute(
            readable(RelatedPerson, context).order_by(
                RelatedPerson.relationship, RelatedPerson.created_at, RelatedPerson.id
            )
        )
        .scalars()
        .all()
    )


def get_person(
    session: Session, context: AuthorizationContext, person_id: UUID | str
) -> RelatedPerson:
    return require_readable(session, RelatedPerson, context, person_id)


def create_person(
    session: Session,
    context: AuthorizationContext,
    *,
    display_name: str,
    relationship: PersonRelationship,
    birthday: date | None,
    birthday_year_known: bool,
    visibility: ContentVisibility,
) -> RelatedPerson:
    person = RelatedPerson(
        space_id=context.space_id,
        owner_id=context.account_id,
        privacy_class=privacy_for(visibility).value,
        relationship=relationship.value,
        birthday=normalize_birthday(birthday, year_known=birthday_year_known),
        birthday_year_known=birthday_year_known,
        payload=RelatedPersonPayload(
            display_name=_clean_text(display_name, PeopleErrorCode.DISPLAY_NAME_REQUIRED)
        ),
    )
    session.add(person)
    session.flush()
    return person


def _shared_dates_of(session: Session, person: RelatedPerson) -> int:
    """Wie viele geteilte Termine an dieser Person haengen.

    Gezaehlt wird ohne Guard, und das ist hier richtig: `SPACE_SHARED`
    sieht ohnehin der ganze Space. Private Termine des Partners bleiben
    ungezaehlt - sie bleiben auch nach einer Verschaerfung erlaubt, und
    eine Ablehnung ihretwegen waere die Auskunft, dass es sie gibt.
    """
    return int(
        session.execute(
            select(func.count())
            .select_from(ImportantDate)
            .where(
                ImportantDate.related_person_id == person.id,
                ImportantDate.privacy_class == PrivacyClass.SPACE_SHARED.value,
            )
        ).scalar_one()
    )


def update_person(
    session: Session,
    context: AuthorizationContext,
    person_id: UUID | str,
    *,
    expected_version: int,
    display_name: str,
    relationship: PersonRelationship,
    birthday: date | None,
    birthday_year_known: bool,
    visibility: ContentVisibility,
) -> RelatedPerson:
    person = require_writable(session, RelatedPerson, context, person_id)
    _ensure_expected_version(person.version, expected_version, "related person")

    privacy = privacy_for(visibility)
    if (
        privacy is PrivacyClass.OWNER_ONLY
        and person.privacy_class != privacy.value
        and _shared_dates_of(session, person)
    ):
        # Kein stilles Umklassifizieren fremder Zeilen: die geteilten
        # Termine an dieser Person werden zuerst vom jeweiligen Eigentuemer
        # verschaerft oder entfernt.
        raise ConflictError(
            "Shared important dates still refer to this person.",
            PeopleErrorCode.HAS_SHARED_DATES,
        )

    person.privacy_class = privacy.value
    person.relationship = relationship.value
    person.birthday = normalize_birthday(birthday, year_known=birthday_year_known)
    person.birthday_year_known = birthday_year_known
    person.payload = RelatedPersonPayload(
        display_name=_clean_text(display_name, PeopleErrorCode.DISPLAY_NAME_REQUIRED)
    )
    _flush(session)
    return person


def delete_person(
    session: Session,
    context: AuthorizationContext,
    person_id: UUID | str,
    *,
    expected_version: int,
    delete_policy: RelatedPersonDeletePolicy,
) -> None:
    """Eine Person mit expliziter, privacy-sicherer Terminbehandlung loeschen.

    Die Person wird vor der Versionspruefung per ``FOR UPDATE`` gesperrt.
    Dadurch koennen parallele FK-Verknuepfungen nicht zwischen der Auswahl
    der Termine und dem Loeschen der Person sichtbar werden.

    ``preserve`` loest alle verknuepften Termine - einschliesslich privater
    Partnertermine - von der Person. Die Termine werden absichtlich ohne
    Privacy-Guard geladen: der Aufrufer erhaelt weder Zeilen noch Anzahl oder
    Metadaten, die Mutation muss aber fuer alle Verknuepfungen gelten.

    ``cascade`` behaelt die bestehende DB-Cascade bewusst bei.
    """
    person = require_writable(session, RelatedPerson, context, person_id)
    session.refresh(person, with_for_update=True)
    _ensure_expected_version(person.version, expected_version, "related person")

    if delete_policy is RelatedPersonDeletePolicy.PRESERVE:
        linked_dates = (
            session.execute(
                select(ImportantDate)
                .where(
                    ImportantDate.space_id == context.space_id,
                    ImportantDate.related_person_id == person.id,
                )
                .with_for_update()
            )
            .scalars()
            .all()
        )
        for important_date in linked_dates:
            important_date.related_person_id = None
            important_date.related_person_privacy_class = None
        _flush(session)

    session.delete(person)
    _flush(session)


def _person_link(
    session: Session,
    context: AuthorizationContext,
    related_person_id: UUID | str | None,
    privacy: PrivacyClass,
) -> tuple[UUID | None, str | None]:
    """Die Person eines Termins aufloesen und ihre Klasse mitnehmen.

    Ueber den Guard: wer eine Person nicht lesen darf, kann auch keinen
    Termin an sie haengen - und erfaehrt aus der Antwort nicht, ob es sie
    gibt.
    """
    if related_person_id is None:
        return None, None

    person = require_readable(session, RelatedPerson, context, related_person_id)
    if (
        person.privacy_class == PrivacyClass.OWNER_ONLY.value
        and privacy is not PrivacyClass.OWNER_ONLY
    ):
        raise ValidationError(
            "An important date must not be more visible than its related person.",
            PeopleErrorCode.MORE_OPEN_THAN_PERSON,
        )
    return person.id, person.privacy_class


def list_dates(
    session: Session,
    context: AuthorizationContext,
    *,
    related_person_id: UUID | str | None = None,
) -> Sequence[ImportantDate]:
    statement = readable(ImportantDate, context)
    if related_person_id is not None:
        person = require_readable(session, RelatedPerson, context, related_person_id)
        statement = statement.where(ImportantDate.related_person_id == person.id)
    return session.execute(statement.order_by(ImportantDate.date, ImportantDate.id)).scalars().all()


def get_date(session: Session, context: AuthorizationContext, date_id: UUID | str) -> ImportantDate:
    return require_readable(session, ImportantDate, context, date_id)


def create_date(
    session: Session,
    context: AuthorizationContext,
    *,
    label: str,
    date_type: ImportantDateType,
    day: date,
    repeats: DateRepeat,
    visibility: ContentVisibility,
    related_person_id: UUID | str | None = None,
) -> ImportantDate:
    privacy = privacy_for(visibility)
    person_id, person_privacy = _person_link(session, context, related_person_id, privacy)

    important_date = ImportantDate(
        space_id=context.space_id,
        owner_id=context.account_id,
        privacy_class=privacy.value,
        related_person_id=person_id,
        related_person_privacy_class=person_privacy,
        type=date_type.value,
        date=day,
        repeats=repeats.value,
        payload=ImportantDatePayload(label=_clean_text(label, PeopleErrorCode.LABEL_REQUIRED)),
    )
    session.add(important_date)
    session.flush()
    return important_date


def update_date(
    session: Session,
    context: AuthorizationContext,
    date_id: UUID | str,
    *,
    expected_version: int,
    label: str,
    date_type: ImportantDateType,
    day: date,
    repeats: DateRepeat,
    visibility: ContentVisibility,
    related_person_id: UUID | str | None = None,
) -> ImportantDate:
    important_date = require_writable(session, ImportantDate, context, date_id)
    _ensure_expected_version(important_date.version, expected_version, "important date")

    privacy = privacy_for(visibility)
    person_id, person_privacy = _person_link(session, context, related_person_id, privacy)

    important_date.privacy_class = privacy.value
    important_date.related_person_id = person_id
    important_date.related_person_privacy_class = person_privacy
    important_date.type = date_type.value
    important_date.date = day
    important_date.repeats = repeats.value
    important_date.payload = ImportantDatePayload(
        label=_clean_text(label, PeopleErrorCode.LABEL_REQUIRED)
    )
    _flush(session)
    return important_date


def delete_date(
    session: Session,
    context: AuthorizationContext,
    date_id: UUID | str,
    *,
    expected_version: int,
) -> None:
    important_date = require_writable(session, ImportantDate, context, date_id)
    _ensure_expected_version(important_date.version, expected_version, "important date")
    session.delete(important_date)
    _flush(session)


def _ensure_expected_version(current: int, expected: int, subject: str) -> None:
    if current != expected:
        raise ConflictError(
            f"The {subject} was changed by someone else.",
            ErrorCode.VERSION_CONFLICT,
        )


def _flush(session: Session) -> None:
    try:
        session.flush()
    except StaleDataError as stale:
        raise ConflictError(
            "The resource was changed by someone else.",
            ErrorCode.VERSION_CONFLICT,
        ) from stale
