"""Domain logic for related people and important dates.

Every list and detail lookup starts at the central owner/privacy guard.
Private rows are therefore filtered in SQL rather than only during
serialization.

Rules beyond pure visibility live in exactly two places: as a schema
constraint and - so the client receives an understandable response instead
of a database error - as a corresponding check here before persistence.
"""

from __future__ import annotations

from collections.abc import Sequence
from datetime import date
from enum import StrEnum
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session
from sqlalchemy.orm.exc import StaleDataError

from sidebyside.authorization import (
    AuthorizationContext,
    ContentVisibility,
    PrivacyClass,
    privacy_for,
    readable,
    require_readable,
    require_writable,
    require_writable_locked,
)
from sidebyside.core.errors import ConflictError, ErrorCode, ValidationError
from sidebyside.people.models import (
    UNKNOWN_BIRTH_YEAR,
    DateRepeat,
    ImportantDate,
    ImportantDatePayload,
    ImportantDateType,
    PersonRelationship,
    RelatedPerson,
    RelatedPersonPayload,
)
from sidebyside.reminders import runtime as reminder_runtime


class PeopleErrorCode:
    DISPLAY_NAME_REQUIRED = "RELATED_PERSON_DISPLAY_NAME_REQUIRED"
    BIRTHDAY_REQUIRED = "RELATED_PERSON_BIRTHDAY_REQUIRED"
    HAS_SHARED_DATES = "RELATED_PERSON_HAS_SHARED_DATES"
    LABEL_REQUIRED = "IMPORTANT_DATE_LABEL_REQUIRED"
    MORE_OPEN_THAN_PERSON = "IMPORTANT_DATE_MORE_OPEN_THAN_PERSON"


class RelatedPersonDeletePolicy(StrEnum):
    PRESERVE = "preserve"
    CASCADE = "cascade"


def _clean_text(value: str, code: str) -> str:
    cleaned = value.strip()
    if not cleaned:
        raise ValidationError("The value must not be empty.", code)
    return cleaned


def normalize_birthday(birthday: date | None, *, year_known: bool) -> date | None:
    """Normalize a birthday into its persisted representation.

    Without a known year, the date receives the placeholder year. It remains
    a `DATE` and can be compared with every other birthday; whether its year
    has meaning is expressed by `birthdayYearKnown`.

    A known year without a date is not incomplete input to be silently
    repaired - it is a contradiction and is rejected.
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
    reminder_runtime.reconcile_space(session, context.space_id)
    return person


def _shared_dates_of(session: Session, person: RelatedPerson) -> int:
    """Return the number of shared important dates attached to this person.

    The query deliberately runs without a guard: the whole space can already
    see `SPACE_SHARED` rows. A partner's private dates remain uncounted - they
    are still valid after tightening visibility, and rejecting because of
    them would disclose that they exist.
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
        # Do not silently reclassify rows owned by somebody else: shared dates
        # attached to this person must first be tightened or removed by their
        # respective owners.
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
    reminder_runtime.reconcile_space(session, context.space_id)
    return person


def delete_person(
    session: Session,
    context: AuthorizationContext,
    person_id: UUID | str,
    *,
    expected_version: int,
    delete_policy: RelatedPersonDeletePolicy,
) -> None:
    """Delete a person with explicit, privacy-safe important-date handling.

    The person is locked with ``FOR UPDATE`` before the version check. This
    prevents concurrent FK links from becoming visible between selecting the
    dates and deleting the person. The lock is obtained through the guard so
    that a concurrently deleted person yields the same 404 response as any
    other absence.

    ``preserve`` detaches every linked important date - including a partner's
    private dates - from the person. The dates are deliberately loaded without
    a privacy guard: the caller receives neither rows, counts, nor metadata,
    but the mutation must apply to every link.

    ``cascade`` deliberately preserves the existing database cascade.
    """
    person = require_writable_locked(session, RelatedPerson, context, person_id)
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
    reminder_runtime.reconcile_space(session, context.space_id)


def _person_link(
    session: Session,
    context: AuthorizationContext,
    related_person_id: UUID | str | None,
    privacy: PrivacyClass,
) -> tuple[UUID | None, str | None]:
    """Resolve an important date's person and carry along its privacy class.

    Resolution goes through the guard: callers who may not read a person also
    cannot attach a date to that person, and the response does not reveal
    whether the person exists.
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
    reminder_runtime.reconcile_space(session, context.space_id)
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
    reminder_runtime.reconcile_space(session, context.space_id)
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
    reminder_runtime.reconcile_space(session, context.space_id)


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
