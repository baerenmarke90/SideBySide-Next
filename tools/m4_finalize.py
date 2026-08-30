"""Apply the bounded final M4-C-S2 completion patch.

This temporary repository script is executed once by the companion workflow and
removed before the resulting implementation commit is pushed.
"""

from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def replace_once(path: str, old: str, new: str) -> None:
    target = ROOT / path
    text = target.read_text(encoding="utf-8")
    if old not in text:
        raise RuntimeError(f"Expected patch anchor missing in {path}: {old[:80]!r}")
    target.write_text(text.replace(old, new, 1), encoding="utf-8")


def patch_people_service() -> None:
    path = "backend/src/sidebyside/people/service.py"
    replace_once(
        path,
        "from sidebyside.people.models import (\n",
        "from sidebyside.people.models import (\n",
    )
    replace_once(
        path,
        "from sidebyside.core.errors import ConflictError, ErrorCode, ValidationError\nfrom sidebyside.people.models import (\n",
        "from sidebyside.core.errors import ConflictError, ErrorCode, ValidationError\nfrom sidebyside.reminders import runtime as reminder_runtime\nfrom sidebyside.people.models import (\n",
    )
    replace_once(
        path,
        "    session.add(person)\n    session.flush()\n    return person\n",
        "    session.add(person)\n    session.flush()\n    reminder_runtime.reconcile_space(session, context.space_id)\n    return person\n",
    )
    replace_once(
        path,
        "    _flush(session)\n    return person\n\n\ndef delete_person",
        "    _flush(session)\n    reminder_runtime.reconcile_space(session, context.space_id)\n    return person\n\n\ndef delete_person",
    )
    replace_once(
        path,
        "    session.delete(person)\n    _flush(session)\n\n\ndef _person_link",
        "    session.delete(person)\n    _flush(session)\n    reminder_runtime.reconcile_space(session, context.space_id)\n\n\ndef _person_link",
    )
    replace_once(
        path,
        "    session.add(important_date)\n    session.flush()\n    return important_date\n",
        "    session.add(important_date)\n    session.flush()\n    reminder_runtime.reconcile_space(session, context.space_id)\n    return important_date\n",
    )
    replace_once(
        path,
        "    _flush(session)\n    return important_date\n\n\ndef delete_date",
        "    _flush(session)\n    reminder_runtime.reconcile_space(session, context.space_id)\n    return important_date\n\n\ndef delete_date",
    )
    replace_once(
        path,
        "    session.delete(important_date)\n    _flush(session)\n\n\ndef _ensure_expected_version",
        "    session.delete(important_date)\n    _flush(session)\n    reminder_runtime.reconcile_space(session, context.space_id)\n\n\ndef _ensure_expected_version",
    )


def patch_plan_service() -> None:
    path = "backend/src/sidebyside/plans/service.py"
    replace_once(
        path,
        "from sidebyside.plans.models import Plan, PlanPayload, PlanStatus, shared_privacy\n",
        "from sidebyside.plans.models import Plan, PlanPayload, PlanStatus, shared_privacy\nfrom sidebyside.reminders import runtime as reminder_runtime\n",
    )
    replace_once(
        path,
        "    plan.status = PlanStatus.PLANNED.value\n\n    _flush(session)\n    _record(session, plan, context.account_id, EventType.PLAN_UPDATED)\n    _flush(session)\n    return plan\n",
        "    plan.status = PlanStatus.PLANNED.value\n\n    _flush(session)\n    _record(session, plan, context.account_id, EventType.PLAN_UPDATED)\n    _flush(session)\n    reminder_runtime.reconcile_space(session, context.space_id)\n    return plan\n",
    )
    replace_once(
        path,
        "    plan.status = PlanStatus.IDEA.value\n\n    _flush(session)\n    _record(session, plan, context.account_id, EventType.PLAN_UPDATED)\n    _flush(session)\n    return plan\n",
        "    plan.status = PlanStatus.IDEA.value\n\n    _flush(session)\n    _record(session, plan, context.account_id, EventType.PLAN_UPDATED)\n    _flush(session)\n    reminder_runtime.reconcile_space(session, context.space_id)\n    return plan\n",
    )
    replace_once(
        path,
        "    if wish is not None:\n        wish_service.plan_completed(session, wish, context.account_id)\n\n    return plan, wish\n",
        "    if wish is not None:\n        wish_service.plan_completed(session, wish, context.account_id)\n\n    reminder_runtime.reconcile_space(session, context.space_id)\n    return plan, wish\n",
    )
    replace_once(
        path,
        "    wish_service.plan_returned(session, wish, actor_id)\n    return ReturnToWishResult(wish=wish, removed_plan_id=removed_plan_id)\n",
        "    wish_service.plan_returned(session, wish, actor_id)\n    reminder_runtime.reconcile_space(session, context.space_id)\n    return ReturnToWishResult(wish=wish, removed_plan_id=removed_plan_id)\n",
    )
    replace_once(
        path,
        "    _record(session, plan, actor_id, EventType.PLAN_DELETED)\n    _flush(session)\n\n\ndef convert_wish_to_plan",
        "    _record(session, plan, actor_id, EventType.PLAN_DELETED)\n    _flush(session)\n    reminder_runtime.reconcile_space(session, context.space_id)\n\n\ndef convert_wish_to_plan",
    )


def patch_relationship_profile() -> None:
    path = "backend/src/sidebyside/relationship/profile.py"
    replace_once(
        path,
        "from sidebyside.relationship.models import DurationDisplayMode, Space, SpaceProfile\n",
        "from sidebyside.relationship.models import DurationDisplayMode, Space, SpaceProfile\nfrom sidebyside.reminders import runtime as reminder_runtime\n",
    )
    replace_once(
        path,
        "    _validate_start(relationship_started_on, today)\n\n    profile.relationship_started_on = relationship_started_on\n",
        "    start_changed = profile.relationship_started_on != relationship_started_on\n    _validate_start(relationship_started_on, today)\n\n    profile.relationship_started_on = relationship_started_on\n",
    )
    replace_once(
        path,
        "        ) from stale\n\n    return profile\n",
        "        ) from stale\n\n    if start_changed:\n        reminder_runtime.reconcile_space(session, space_id)\n    return profile\n",
    )


def patch_identity_preferences() -> None:
    path = "backend/src/sidebyside/identity/preferences.py"
    replace_once(
        path,
        "from sqlalchemy.orm import Session\n\nfrom sidebyside.core.errors import ValidationError\nfrom sidebyside.identity.models import Account\n",
        "from sqlalchemy import select\nfrom sqlalchemy.orm import Session\n\nfrom sidebyside.core.errors import ValidationError\nfrom sidebyside.identity.models import Account\nfrom sidebyside.relationship.models import Membership, MembershipStatus\nfrom sidebyside.reminders import runtime as reminder_runtime\n",
    )
    replace_once(
        path,
        "    validated_zone = validate_timezone(timezone) if timezone is not None else None\n    validated_locale = normalize_locale(locale) if locale is not None else None\n\n    if validated_zone is not None:\n",
        "    validated_zone = validate_timezone(timezone) if timezone is not None else None\n    validated_locale = normalize_locale(locale) if locale is not None else None\n    timezone_changed = validated_zone is not None and validated_zone != account.timezone\n\n    if validated_zone is not None:\n",
    )
    replace_once(
        path,
        "    session.flush()\n    return account\n",
        "    session.flush()\n    if timezone_changed:\n        space_ids = session.execute(\n            select(Membership.space_id).where(\n                Membership.account_id == account.id,\n                Membership.status == MembershipStatus.ACTIVE.value,\n            )\n        ).scalars()\n        for space_id in space_ids:\n            reminder_runtime.reconcile_space(session, space_id)\n    return account\n",
    )


def patch_endpoint_matrix() -> None:
    path = "backend/tests/integration/test_endpoint_matrix.py"
    replace_once(
        path,
        "REMINDER = {\n    \"title\": \"Matrix Reminder\",\n    \"description\": \"Text\",\n    \"schedule\": {\n        \"type\": \"ANNUAL\",\n        \"month\": 6,\n        \"day\": 13,\n        \"localTime\": \"09:00:00\",\n    },\n    \"offsets\": [7, 1],\n}\n",
        "REMINDER = {\n    \"title\": \"Matrix Reminder\",\n    \"description\": \"Text\",\n    \"schedule\": {\n        \"type\": \"ANNUAL\",\n        \"month\": 6,\n        \"day\": 13,\n        \"localTime\": \"09:00:00\",\n    },\n    \"offsets\": [7, 1],\n}\nRULE_PREFERENCE = {\n    \"enabled\": True,\n    \"parameters\": {\"daysBefore\": [7, 1], \"localTime\": \"09:00:00\"},\n}\n",
    )
    replace_once(
        path,
        "    Endpoint(\n        \"PUT\",\n        \"/api/v1/spaces/{spaceId}/reminders/{reminderId}/preference\",\n        body={\"muted\": True},\n        resource_absence=\"REMINDER_NOT_FOUND\",\n    ),\n",
        "    Endpoint(\n        \"PUT\",\n        \"/api/v1/spaces/{spaceId}/reminders/{reminderId}/preference\",\n        body={\"muted\": True},\n        resource_absence=\"REMINDER_NOT_FOUND\",\n    ),\n    Endpoint(\"GET\", \"/api/v1/spaces/{spaceId}/rules\"),\n    Endpoint(\n        \"GET\",\n        \"/api/v1/spaces/{spaceId}/rules/{ruleKey}/preference\",\n    ),\n    Endpoint(\n        \"PUT\",\n        \"/api/v1/spaces/{spaceId}/rules/{ruleKey}/preference\",\n        body=RULE_PREFERENCE,\n    ),\n",
    )
    replace_once(
        path,
        "            \"reminderId\": reminder[\"id\"],\n",
        "            \"reminderId\": reminder[\"id\"],\n            \"ruleKey\": \"important_date_reminder\",\n",
    )


def write_runtime_tests() -> None:
    path = ROOT / "backend/tests/integration/test_reminder_runtime.py"
    path.write_text(
        '''"""PostgreSQL/HTTP evidence for the final M4-C Rule and occurrence runtime."""

from __future__ import annotations

from datetime import UTC, date, datetime, time, timedelta
from zoneinfo import ZoneInfo

import pytest
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from sidebyside.domain.events import EventType
from sidebyside.engagement import push, service as engagement_service
from sidebyside.engagement.models import Notification, NotificationKind, PushDelivery
from sidebyside.identity import preferences as account_preferences
from sidebyside.outbox.models import OutboxEvent
from sidebyside.relationship import profile as relationship_profile
from sidebyside.relationship import service as relationship_service
from sidebyside.relationship.models import DurationDisplayMode
from sidebyside.reminders import rules, runtime
from sidebyside.reminders.models import Reminder, ReminderSource
from sidebyside.reminders.runtime_models import OccurrenceState, ReminderOccurrence
from tests.conftest import auth, make_account, make_space, requires_database, sign_in

pytestmark = [pytest.mark.integration, requires_database]

NOW = datetime(2026, 8, 30, 12, 0, tzinfo=UTC)


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
        "anna_token": sign_in(session, anna),
        "ben_token": sign_in(session, ben),
        "outsider_token": sign_in(session, outsider),
    }


def _rule_base(couple) -> str:  # type: ignore[no-untyped-def]
    return f"/api/v1/spaces/{couple['space'].id}/rules"


def _reminder_base(couple) -> str:  # type: ignore[no-untyped-def]
    return f"/api/v1/spaces/{couple['space'].id}/reminders"


def _occurrences(session: Session, reminder_id, account_id):  # type: ignore[no-untyped-def]
    return list(
        session.execute(
            select(ReminderOccurrence)
            .where(
                ReminderOccurrence.reminder_id == reminder_id,
                ReminderOccurrence.recipient_account_id == account_id,
            )
            .order_by(ReminderOccurrence.days_before)
        ).scalars()
    )


def test_rule_catalog_defaults_validation_and_account_isolation(client, session: Session, couple) -> None:  # type: ignore[no-untyped-def]
    response = client.get(_rule_base(couple), headers=auth(couple["anna_token"]))
    assert response.status_code == 200, response.text
    assert response.headers["cache-control"] == "private, no-store"
    items = {item["ruleKey"]: item for item in response.json()["items"]}
    assert set(items) == {
        rules.IMPORTANT_DATE_RULE,
        rules.RELATED_PERSON_BIRTHDAY_RULE,
        rules.RELATIONSHIP_ANNIVERSARY_RULE,
        rules.PLAN_START_RULE,
    }
    assert items[rules.IMPORTANT_DATE_RULE]["parameters"]["daysBefore"] == [7, 1]
    assert items[rules.RELATED_PERSON_BIRTHDAY_RULE]["parameters"]["daysBefore"] == [14, 7, 1]
    assert items[rules.RELATIONSHIP_ANNIVERSARY_RULE]["parameters"]["daysBefore"] == [30, 7, 1]
    assert items[rules.PLAN_START_RULE]["parameters"]["daysBefore"] == [1, 0]

    changed = client.put(
        f"{_rule_base(couple)}/{rules.IMPORTANT_DATE_RULE}/preference",
        json={
            "enabled": False,
            "parameters": {"daysBefore": [3, 1], "localTime": "08:30:00"},
        },
        headers=auth(couple["anna_token"]),
    )
    assert changed.status_code == 200, changed.text
    assert changed.json()["enabled"] is False
    assert changed.json()["parameters"] == {
        "daysBefore": [1, 3],
        "localTime": "08:30:00",
    }

    partner = client.get(
        f"{_rule_base(couple)}/{rules.IMPORTANT_DATE_RULE}/preference",
        headers=auth(couple["ben_token"]),
    )
    assert partner.status_code == 200
    assert partner.json()["enabled"] is True
    assert partner.json()["parameters"]["daysBefore"] == [7, 1]

    invalid = client.put(
        f"{_rule_base(couple)}/{rules.IMPORTANT_DATE_RULE}/preference",
        json={"enabled": True, "parameters": {"daysBefore": [1, 1]}},
        headers=auth(couple["anna_token"]),
    )
    assert invalid.status_code == 422
    assert invalid.json()["code"] == rules.RULE_PARAMETERS_INVALID


def test_source_hooks_reconcile_idempotently_and_private_dates_never_generate(
    client, session: Session, couple, monkeypatch
) -> None:  # type: ignore[no-untyped-def]
    monkeypatch.setattr(runtime.clock, "now", lambda: NOW)
    base = f"/api/v1/spaces/{couple['space'].id}/important-dates"
    shared = client.post(
        base,
        json={
            "label": "Shared anniversary",
            "type": "ANNIVERSARY",
            "date": "2026-09-10",
            "repeats": "ANNUALLY",
            "visibility": "SHARED",
        },
        headers=auth(couple["anna_token"]),
    )
    assert shared.status_code == 201, shared.text

    generated = session.execute(
        select(Reminder).where(
            Reminder.space_id == couple["space"].id,
            Reminder.source == ReminderSource.GENERATED.value,
            Reminder.rule_key == rules.IMPORTANT_DATE_RULE,
        )
    ).scalar_one()
    assert generated.source_id is not None
    first_count = session.execute(
        select(func.count()).select_from(ReminderOccurrence).where(
            ReminderOccurrence.reminder_id == generated.id
        )
    ).scalar_one()
    assert first_count == 4

    runtime.reconcile_space(session, couple["space"].id)
    runtime.reconcile_space(session, couple["space"].id)
    assert session.execute(
        select(func.count()).select_from(Reminder).where(
            Reminder.space_id == couple["space"].id,
            Reminder.source == ReminderSource.GENERATED.value,
            Reminder.rule_key == rules.IMPORTANT_DATE_RULE,
        )
    ).scalar_one() == 1
    assert session.execute(
        select(func.count()).select_from(ReminderOccurrence).where(
            ReminderOccurrence.reminder_id == generated.id
        )
    ).scalar_one() == first_count

    tightened = client.put(
        f"{base}/{shared.json()['id']}",
        json={
            "label": "Private anniversary",
            "type": "ANNIVERSARY",
            "date": "2026-09-10",
            "repeats": "ANNUALLY",
            "visibility": "PRIVATE",
        },
        headers={
            **auth(couple["anna_token"]),
            "If-Match": f'"{shared.json()["version"]}"',
        },
    )
    assert tightened.status_code == 200, tightened.text
    assert session.execute(
        select(func.count()).select_from(Reminder).where(
            Reminder.space_id == couple["space"].id,
            Reminder.rule_key == rules.IMPORTANT_DATE_RULE,
        )
    ).scalar_one() == 0

    private = client.post(
        base,
        json={
            "label": "Owner only date",
            "type": "ANNIVERSARY",
            "date": "2026-09-12",
            "repeats": "ANNUALLY",
            "visibility": "PRIVATE",
        },
        headers=auth(couple["anna_token"]),
    )
    assert private.status_code == 201
    runtime.reconcile_space(session, couple["space"].id)
    assert session.execute(
        select(func.count()).select_from(Reminder).where(
            Reminder.space_id == couple["space"].id,
            Reminder.rule_key == rules.IMPORTANT_DATE_RULE,
        )
    ).scalar_one() == 0


def test_plan_and_relationship_source_changes_reconcile_immediately(
    client, session: Session, couple, monkeypatch
) -> None:  # type: ignore[no-untyped-def]
    monkeypatch.setattr(runtime.clock, "now", lambda: NOW)
    plan_base = f"/api/v1/spaces/{couple['space'].id}/plans"
    created = client.post(
        plan_base,
        json={"title": "Dinner"},
        headers=auth(couple["anna_token"]),
    )
    assert created.status_code == 201, created.text
    scheduled = client.post(
        f"{plan_base}/{created.json()['id']}/schedule",
        json={"plannedStart": "2026-09-05T18:00:00Z"},
        headers={
            **auth(couple["anna_token"]),
            "If-Match": f'"{created.json()["version"]}"',
        },
    )
    assert scheduled.status_code == 200, scheduled.text
    plan_reminder = session.execute(
        select(Reminder).where(
            Reminder.space_id == couple["space"].id,
            Reminder.rule_key == rules.PLAN_START_RULE,
        )
    ).scalar_one()
    assert plan_reminder.once_at == datetime(2026, 9, 5, 18, 0, tzinfo=UTC)

    unscheduled = client.post(
        f"{plan_base}/{created.json()['id']}/unschedule",
        json={},
        headers={
            **auth(couple["anna_token"]),
            "If-Match": f'"{scheduled.json()["version"]}"',
        },
    )
    assert unscheduled.status_code == 200, unscheduled.text
    assert session.execute(
        select(func.count()).select_from(Reminder).where(
            Reminder.space_id == couple["space"].id,
            Reminder.rule_key == rules.PLAN_START_RULE,
        )
    ).scalar_one() == 0

    profile = relationship_profile.load(session, couple["space"].id)
    assert profile is not None
    relationship_profile.update(
        session,
        couple["space"].id,
        expected_version=profile.version,
        relationship_started_on=date(2020, 9, 10),
        show_relationship_duration=True,
        duration_display_mode=DurationDisplayMode.YEARS_MONTHS,
        today=NOW.date(),
    )
    relationship_reminder = session.execute(
        select(Reminder).where(
            Reminder.space_id == couple["space"].id,
            Reminder.rule_key == rules.RELATIONSHIP_ANNIVERSARY_RULE,
        )
    ).scalar_one()
    assert relationship_reminder.annual_month == 9
    assert relationship_reminder.annual_day == 10


def test_time_contracts_and_timezone_replanning(client, session: Session, couple, monkeypatch) -> None:  # type: ignore[no-untyped-def]
    monkeypatch.setattr(runtime.clock, "now", lambda: NOW)
    assert runtime._annual_date(2027, 2, 29) == date(2027, 2, 28)
    berlin = ZoneInfo("Europe/Berlin")
    assert runtime._resolve_local(date(2026, 3, 29), time(2, 30), berlin) == datetime(
        2026, 3, 29, 1, 30, tzinfo=UTC
    )
    assert runtime._resolve_local(date(2026, 10, 25), time(2, 30), berlin) == datetime(
        2026, 10, 25, 0, 30, tzinfo=UTC
    )

    annual = client.post(
        _reminder_base(couple),
        json={
            "title": "Annual",
            "schedule": {
                "type": "ANNUAL",
                "month": 9,
                "day": 15,
                "localTime": "09:00:00",
            },
            "offsets": [0],
        },
        headers=auth(couple["anna_token"]),
    )
    assert annual.status_code == 201, annual.text
    annual_row = _occurrences(session, annual.json()["id"], couple["anna"].id)[0]
    before = annual_row.due_at
    generation = annual_row.generation

    account_preferences.set_preferences(session, couple["anna"], timezone="America/New_York")
    session.refresh(annual_row)
    assert annual_row.due_at != before
    assert annual_row.generation == generation + 1

    once = client.post(
        _reminder_base(couple),
        json={
            "title": "Absolute",
            "schedule": {"type": "ONCE", "at": "2026-09-20T12:00:00Z"},
            "offsets": [0],
        },
        headers=auth(couple["anna_token"]),
    )
    assert once.status_code == 201, once.text
    once_row = _occurrences(session, once.json()["id"], couple["anna"].id)[0]
    once_due = once_row.due_at
    account_preferences.set_preferences(session, couple["anna"], timezone="Asia/Tokyo")
    session.refresh(once_row)
    assert once_row.due_at == once_due


def test_due_handler_catchup_and_m4b_projection_are_idempotent(
    client, session: Session, couple, monkeypatch
) -> None:  # type: ignore[no-untyped-def]
    monkeypatch.setattr(runtime.clock, "now", lambda: NOW)
    created = client.post(
        _reminder_base(couple),
        json={
            "title": "Protected reminder prose",
            "description": "Must never enter the Outbox or PushDelivery",
            "schedule": {"type": "ONCE", "at": "2026-08-30T13:00:00Z"},
            "offsets": [0],
        },
        headers=auth(couple["anna_token"]),
    )
    assert created.status_code == 201, created.text
    occurrence = _occurrences(session, created.json()["id"], couple["anna"].id)[0]
    push.register_endpoint(
        session,
        account_id=couple["anna"].id,
        provider_key="test-provider",
        endpoint_value="endpoint://anna",
    )

    monkeypatch.setattr(runtime.clock, "now", lambda: occurrence.due_at)
    payload = {"occurrenceId": str(occurrence.id), "generation": occurrence.generation}
    runtime.handle_occurrence(session, payload)
    runtime.handle_occurrence(session, payload)
    session.flush()
    session.refresh(occurrence)
    assert occurrence.state == OccurrenceState.DELIVERED.value

    events = list(
        session.execute(
            select(OutboxEvent).where(
                OutboxEvent.event_type == EventType.REMINDER_DUE.value,
                OutboxEvent.subject_id == occurrence.reminder_id,
                OutboxEvent.payload["occurrenceId"].astext == str(occurrence.id),
            )
        ).scalars()
    )
    assert len(events) == 1
    event = events[0]
    safe_payload = event.payload.model_dump(mode="json", exclude_none=True)
    assert set(safe_payload) <= {"recipient_id", "occurrence_id", "due_at", "rule_key"}
    assert "Protected reminder prose" not in str(safe_payload)
    assert "Must never enter" not in str(safe_payload)

    engagement_service.project_event(session, event)
    engagement_service.project_event(session, event)
    session.flush()
    notifications = list(
        session.execute(
            select(Notification).where(
                Notification.source_event_id == event.id,
                Notification.kind == NotificationKind.REMINDER_DUE.value,
            )
        ).scalars()
    )
    assert len(notifications) == 1
    assert session.execute(
        select(func.count()).select_from(PushDelivery).where(
            PushDelivery.notification_id == notifications[0].id
        )
    ).scalar_one() == 1

    occurrence.state = OccurrenceState.PENDING.value
    occurrence.generation += 1
    occurrence.due_at = runtime.clock.now() - timedelta(hours=25)
    stale_payload = {"occurrenceId": str(occurrence.id), "generation": occurrence.generation}
    runtime.handle_occurrence(session, stale_payload)
    assert occurrence.state == OccurrenceState.EXPIRED.value
    assert session.execute(
        select(func.count()).select_from(OutboxEvent).where(
            OutboxEvent.event_type == EventType.REMINDER_DUE.value,
            OutboxEvent.subject_id == occurrence.reminder_id,
        )
    ).scalar_one() == 1
''',
        encoding="utf-8",
    )


def main() -> None:
    patch_people_service()
    patch_plan_service()
    patch_relationship_profile()
    patch_identity_preferences()
    patch_endpoint_matrix()
    write_runtime_tests()


if __name__ == "__main__":
    main()
