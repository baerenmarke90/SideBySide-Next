"""PostgreSQL/HTTP acceptance tests for the M4-A shared Dashboard."""

from __future__ import annotations

from datetime import UTC, date, datetime

import pytest
from sqlalchemy import select
from sqlalchemy.orm import Session

from sidebyside.authorization import PrivacyClass
from sidebyside.core.ids import new_id
from sidebyside.dashboard import service as dashboard_service
from sidebyside.heart_moments.models import HeartEmotion, HeartMoment, HeartMomentPayload
from sidebyside.memories.models import Memory, MemoryPayload
from sidebyside.milestones.models import Milestone, MilestonePayload
from sidebyside.people.models import (
    DateRepeat,
    ImportantDate,
    ImportantDatePayload,
    ImportantDateType,
    PersonRelationship,
    RelatedPerson,
    RelatedPersonPayload,
)
from sidebyside.plans.models import Plan, PlanPayload, PlanStatus
from sidebyside.relationship import service as relationship_service
from sidebyside.relationship.models import SpaceProfile
from tests.conftest import auth, make_account, make_space, requires_database, sign_in

pytestmark = [pytest.mark.integration, requires_database]

FIXED_NOW = datetime(2026, 8, 30, 12, 0, tzinfo=UTC)


@pytest.fixture
def couple(session: Session):  # type: ignore[no-untyped-def]
    anna = make_account(session, "Anna")
    ben = make_account(session, "Ben")
    outsider = make_account(session, "Outsider")
    space = make_space(session, anna)
    relationship_service.add_member(session, space.id, ben)
    foreign_space = make_space(session, outsider)
    session.flush()
    return {
        "anna": anna,
        "ben": ben,
        "outsider": outsider,
        "space": space,
        "foreign_space": foreign_space,
        "token_a": sign_in(session, anna),
    }


def _resource(couple, owner_id, *, private: bool = False):  # type: ignore[no-untyped-def]
    return {
        "space_id": couple["space"].id,
        "owner_id": owner_id,
        "privacy_class": (
            PrivacyClass.OWNER_ONLY.value if private else PrivacyClass.SPACE_SHARED.value
        ),
    }


def _dashboard(client, couple):  # type: ignore[no-untyped-def]
    return client.get(
        f"/api/v1/spaces/{couple['space'].id}/dashboard",
        headers=auth(couple["token_a"]),
    )


def _freeze(monkeypatch, at: datetime = FIXED_NOW) -> None:  # type: ignore[no-untyped-def]
    monkeypatch.setattr(dashboard_service.clock, "now", lambda: at)


def test_dashboard_is_shared_only_and_private_no_store(
    client, session: Session, couple, monkeypatch
) -> None:  # type: ignore[no-untyped-def]
    _freeze(monkeypatch)
    shared_heart = HeartMoment(
        **_resource(couple, couple["anna"].id),
        happened_on=date(2025, 8, 30),
        payload=HeartMomentPayload(text="Shared retrospective", emotion=HeartEmotion.LOVED),
    )
    private_heart = HeartMoment(
        **_resource(couple, couple["anna"].id, private=True),
        happened_on=date(2025, 8, 30),
        payload=HeartMomentPayload(text="Private retrospective", emotion=HeartEmotion.GRATEFUL),
    )
    private_person = RelatedPerson(
        **_resource(couple, couple["anna"].id, private=True),
        relationship=PersonRelationship.FRIEND.value,
        birthday=date(1904, 8, 31),
        birthday_year_known=False,
        payload=RelatedPersonPayload(display_name="Private birthday"),
    )
    foreign_memory = Memory(
        space_id=couple["foreign_space"].id,
        owner_id=couple["outsider"].id,
        privacy_class=PrivacyClass.SPACE_SHARED.value,
        happened_on=date(2025, 8, 30),
        payload=MemoryPayload(title="Foreign memory", body="Must never appear"),
    )
    session.add_all([shared_heart, private_heart, private_person, foreign_memory])
    session.flush()

    response = _dashboard(client, couple)
    assert response.status_code == 200, response.text
    assert response.headers["cache-control"] == "private, no-store"
    body = response.json()

    assert body["space"]["spaceId"] == str(couple["space"].id)
    assert body["space"]["partner"] == {
        "id": str(couple["ben"].id),
        "displayName": "Ben",
    }
    assert body["retrospective"]["id"] == str(shared_heart.id)

    visible_ids = {
        item["id"] for section in (body["upcoming"], body["recentShared"]) for item in section
    }
    visible_ids.add(body["retrospective"]["id"])
    assert str(private_heart.id) not in visible_ids
    assert str(private_person.id) not in visible_ids
    assert str(foreign_memory.id) not in visible_ids
    assert set(body) == {
        "space",
        "relationshipDuration",
        "retrospective",
        "upcoming",
        "recentShared",
    }


def test_relationship_duration_uses_callers_calendar_day_and_can_be_disabled(
    client, session: Session, couple, monkeypatch
) -> None:  # type: ignore[no-untyped-def]
    couple["anna"].timezone = "Pacific/Honolulu"
    profile = session.execute(
        select(SpaceProfile).where(SpaceProfile.space_id == couple["space"].id)
    ).scalar_one()
    profile.relationship_started_on = date(2026, 8, 29)
    profile.show_relationship_duration = True
    session.flush()

    _freeze(monkeypatch, datetime(2026, 8, 30, 0, 30, tzinfo=UTC))
    first = _dashboard(client, couple)
    assert first.status_code == 200
    assert first.json()["relationshipDuration"]["daysTogether"] == 0
    assert first.json()["relationshipDuration"]["startedOn"] == "2026-08-29"

    profile.show_relationship_duration = False
    session.flush()
    second = _dashboard(client, couple)
    assert second.status_code == 200
    assert second.json()["relationshipDuration"] is None


def test_retrospective_uses_exact_date_and_most_recent_prior_year(
    client, session: Session, couple, monkeypatch
) -> None:  # type: ignore[no-untyped-def]
    _freeze(monkeypatch)
    older = Memory(
        **_resource(couple, couple["anna"].id),
        happened_on=date(2024, 8, 30),
        payload=MemoryPayload(title="Older", body="Older"),
    )
    expected = Milestone(
        **_resource(couple, couple["anna"].id),
        happened_on=date(2025, 8, 30),
        payload=MilestonePayload(title="Expected"),
    )
    wrong_day = Memory(
        **_resource(couple, couple["anna"].id),
        happened_on=date(2025, 8, 29),
        payload=MemoryPayload(title="Wrong day", body="Wrong day"),
    )
    private_same_day = HeartMoment(
        **_resource(couple, couple["anna"].id, private=True),
        happened_on=date(2025, 8, 30),
        payload=HeartMomentPayload(text="Private", emotion=HeartEmotion.SEEN),
    )
    session.add_all([older, expected, wrong_day, private_same_day])
    session.flush()

    response = _dashboard(client, couple)
    assert response.status_code == 200
    retrospective = response.json()["retrospective"]
    assert retrospective["type"] == "MILESTONE"
    assert retrospective["id"] == str(expected.id)
    assert retrospective["occurredOn"] == "2025-08-30"


def test_upcoming_combines_existing_date_sources_in_deterministic_order(
    client, session: Session, couple, monkeypatch
) -> None:  # type: ignore[no-untyped-def]
    _freeze(monkeypatch)
    profile = session.execute(
        select(SpaceProfile).where(SpaceProfile.space_id == couple["space"].id)
    ).scalar_one()
    profile.relationship_started_on = date(2020, 9, 2)

    plan = Plan(
        **_resource(couple, couple["anna"].id),
        status=PlanStatus.PLANNED.value,
        planned_start=datetime(2026, 8, 30, 18, 0, tzinfo=UTC),
        payload=PlanPayload(title="Tonight"),
    )
    important = ImportantDate(
        **_resource(couple, couple["anna"].id),
        related_person_id=None,
        related_person_privacy_class=None,
        type=ImportantDateType.ANNIVERSARY.value,
        date=date(2020, 8, 31),
        repeats=DateRepeat.ANNUALLY.value,
        payload=ImportantDatePayload(label="Tomorrow"),
    )
    birthday_id = new_id()
    birthday = RelatedPerson(
        id=birthday_id,
        **_resource(couple, couple["anna"].id),
        relationship=PersonRelationship.FRIEND.value,
        birthday=date(1904, 9, 1),
        birthday_year_known=False,
        payload=RelatedPersonPayload(display_name="Birthday"),
    )
    private_date = ImportantDate(
        **_resource(couple, couple["anna"].id, private=True),
        related_person_id=None,
        related_person_privacy_class=None,
        type=ImportantDateType.CUSTOM.value,
        date=date(2026, 8, 30),
        repeats=DateRepeat.NONE.value,
        payload=ImportantDatePayload(label="Private today"),
    )
    session.add_all([plan, important, birthday, private_date])
    session.flush()

    person_date = ImportantDate(
        **_resource(couple, couple["anna"].id),
        related_person_id=birthday_id,
        related_person_privacy_class=PrivacyClass.SPACE_SHARED.value,
        type=ImportantDateType.CUSTOM.value,
        date=date(2026, 8, 31),
        repeats=DateRepeat.NONE.value,
        payload=ImportantDatePayload(label="Person anniversary"),
    )
    session.add(person_date)
    session.flush()

    response = _dashboard(client, couple)
    assert response.status_code == 200
    upcoming = response.json()["upcoming"]
    # Only couple-level items appear: PLAN, IMPORTANT_DATE (related_person_id=None), ANNIVERSARY.
    # Third-party birthdays and ImportantDates assigned to a RelatedPerson are
    # excluded from Wir/Today (#617).
    assert [item["type"] for item in upcoming] == [
        "PLAN",
        "IMPORTANT_DATE",
        "ANNIVERSARY",
    ]
    assert str(birthday.id) not in {item["id"] for item in upcoming}
    assert str(person_date.id) not in {item["id"] for item in upcoming}
    assert str(private_date.id) not in {item["id"] for item in upcoming}


def test_upcoming_excludes_third_party_dates_from_couple_context(
    client, session: Session, couple, monkeypatch
) -> None:  # type: ignore[no-untyped-def]
    _freeze(monkeypatch)

    # 1. Shared plan + upcoming RelatedPerson birthday:
    # Plan can be primary context; third-party birthday does not appear in upcoming.
    plan = Plan(
        **_resource(couple, couple["anna"].id),
        status=PlanStatus.PLANNED.value,
        planned_start=datetime(2026, 9, 5, 19, 0, tzinfo=UTC),
        payload=PlanPayload(title="Our anniversary dinner"),
    )
    birthday_id = new_id()
    person = RelatedPerson(
        id=birthday_id,
        **_resource(couple, couple["anna"].id),
        relationship=PersonRelationship.FRIEND.value,
        birthday=date(1904, 9, 1),
        birthday_year_known=False,
        payload=RelatedPersonPayload(display_name="Birthday"),
    )
    person_date = ImportantDate(
        **_resource(couple, couple["anna"].id),
        related_person_id=birthday_id,
        related_person_privacy_class=PrivacyClass.SPACE_SHARED.value,
        type=ImportantDateType.CUSTOM.value,
        date=date(2026, 8, 31),
        repeats=DateRepeat.NONE.value,
        payload=ImportantDatePayload(label="Person anniversary"),
    )
    session.add_all([plan, person])
    session.flush()
    session.add(person_date)
    session.flush()

    res = _dashboard(client, couple)
    assert res.status_code == 200
    upcoming_items = res.json()["upcoming"]
    assert len(upcoming_items) == 1
    assert upcoming_items[0]["id"] == str(plan.id)
    assert upcoming_items[0]["type"] == "PLAN"

    # 2. Only third-party birthdays exist:
    # upcoming is empty -> no forced primary context.
    session.delete(plan)
    session.flush()

    res_empty = _dashboard(client, couple)
    assert res_empty.status_code == 200
    assert res_empty.json()["upcoming"] == []

    # 3. Own relationship anniversary: remains eligible
    profile = session.execute(
        select(SpaceProfile).where(SpaceProfile.space_id == couple["space"].id)
    ).scalar_one()
    profile.relationship_started_on = date(2022, 9, 10)
    session.flush()

    res_anniversary = _dashboard(client, couple)
    assert res_anniversary.status_code == 200
    anniv_upcoming = res_anniversary.json()["upcoming"]
    assert len(anniv_upcoming) == 1
    assert anniv_upcoming[0]["type"] == "ANNIVERSARY"

    # 4. Couple-specific ImportantDate (related_person_id is None): remains eligible
    couple_date = ImportantDate(
        **_resource(couple, couple["anna"].id),
        related_person_id=None,
        related_person_privacy_class=None,
        type=ImportantDateType.ANNIVERSARY.value,
        date=date(2026, 9, 8),
        repeats=DateRepeat.NONE.value,
        payload=ImportantDatePayload(label="First Apartment"),
    )
    session.add(couple_date)
    session.flush()

    res_couple_date = _dashboard(client, couple)
    assert res_couple_date.status_code == 200
    types = [item["type"] for item in res_couple_date.json()["upcoming"]]
    assert types == ["IMPORTANT_DATE", "ANNIVERSARY"]
    assert res_couple_date.json()["upcoming"][0]["id"] == str(couple_date.id)

    # 5. Private / foreign person or date data: no leaks
    foreign_person = RelatedPerson(
        space_id=couple["foreign_space"].id,
        owner_id=couple["outsider"].id,
        privacy_class=PrivacyClass.SPACE_SHARED.value,
        relationship=PersonRelationship.FRIEND.value,
        birthday=date(1904, 9, 5),
        birthday_year_known=False,
        payload=RelatedPersonPayload(display_name="Foreign Friend"),
    )
    foreign_date = ImportantDate(
        space_id=couple["foreign_space"].id,
        owner_id=couple["outsider"].id,
        privacy_class=PrivacyClass.SPACE_SHARED.value,
        related_person_id=None,
        related_person_privacy_class=None,
        type=ImportantDateType.ANNIVERSARY.value,
        date=date(2026, 9, 7),
        repeats=DateRepeat.NONE.value,
        payload=ImportantDatePayload(label="Foreign Couple Date"),
    )
    session.add_all([foreign_person, foreign_date])
    session.flush()

    res_no_leaks = _dashboard(client, couple)
    assert res_no_leaks.status_code == 200
    ids = {item["id"] for item in res_no_leaks.json()["upcoming"]}
    assert str(foreign_person.id) not in ids
    assert str(foreign_date.id) not in ids


def test_recognition_fields_are_bounded(client, session: Session, couple, monkeypatch) -> None:  # type: ignore[no-untyped-def]
    _freeze(monkeypatch)
    memory = Memory(
        **_resource(couple, couple["anna"].id),
        happened_on=date(2026, 8, 30),
        payload=MemoryPayload(title="x" * 300, body="Body stays out of Dashboard"),
    )
    session.add(memory)
    session.flush()

    response = _dashboard(client, couple)
    assert response.status_code == 200
    item = next(entry for entry in response.json()["recentShared"] if entry["id"] == str(memory.id))
    assert item["titleOrText"] == "x" * dashboard_service.MAX_RECOGNITION_TEXT
    assert "Body stays out" not in response.text
