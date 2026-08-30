"""PostgreSQL/HTTP evidence for M4-B Activity and in-app Notifications."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from sidebyside.authorization import AuthorizationContext, ContentVisibility, PrivacyClass
from sidebyside.comments import service as comment_service
from sidebyside.comments.models import CommentTarget
from sidebyside.domain.events import DomainEvent, EventType, PublicEventPayload
from sidebyside.engagement import service
from sidebyside.engagement.models import Activity, ActivityKind, Notification, NotificationKind
from sidebyside.heart_moments.models import HeartEmotion, HeartMoment, HeartMomentPayload
from sidebyside.memories.models import Memory, MemoryPayload
from sidebyside.outbox import service as outbox_service
from sidebyside.outbox.models import OutboxEvent
from sidebyside.relationship import service as relationship_service
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


def _shared_memory(session: Session, couple, *, owner=None, title: str = "Memory"):  # type: ignore[no-untyped-def]
    owner = owner or couple["anna"]
    memory = Memory(
        space_id=couple["space"].id,
        owner_id=owner.id,
        privacy_class=PrivacyClass.SPACE_SHARED.value,
        payload=MemoryPayload(title=title, body="Protected body"),
    )
    session.add(memory)
    session.flush()
    return memory


def _event(
    session: Session,
    couple,
    event_type: EventType,
    subject,
    *,
    actor=None,
    payload: PublicEventPayload | None = None,
) -> OutboxEvent:  # type: ignore[no-untyped-def]
    actor = actor or couple["anna"]
    outbox_service.record(
        session,
        DomainEvent(
            type=event_type,
            space_id=couple["space"].id,
            actor_id=actor.id,
            subject_type=subject.__class__.__name__.upper(),
            subject_id=subject.id,
            resource_version=getattr(subject, "version", None),
            payload=payload or PublicEventPayload(),
        ),
    )
    session.flush()
    return session.execute(
        select(OutboxEvent)
        .where(
            OutboxEvent.event_type == event_type.value,
            OutboxEvent.subject_id == subject.id,
        )
        .order_by(OutboxEvent.created_at.desc(), OutboxEvent.id.desc())
        .limit(1)
    ).scalar_one()


def test_projection_replay_is_idempotent_and_copies_no_protected_text(
    session: Session, couple
) -> None:  # type: ignore[no-untyped-def]
    memory = _shared_memory(session, couple, title="Recognition only")
    event = _event(session, couple, EventType.MEMORY_CREATED, memory)

    service.project_event(session, event)
    service.project_event(session, event)
    session.flush()

    rows = session.execute(
        select(Activity).where(Activity.source_event_id == event.id)
    ).scalars().all()
    assert len(rows) == 1
    activity = rows[0]
    assert activity.kind == ActivityKind.MEMORY_CREATED.value
    assert activity.target_id == memory.id
    assert not hasattr(activity, "payload")
    assert not hasattr(activity, "title")
    assert not hasattr(activity, "body")


def test_private_heart_moment_never_projects_activity(session: Session, couple) -> None:  # type: ignore[no-untyped-def]
    heart_moment = HeartMoment(
        space_id=couple["space"].id,
        owner_id=couple["anna"].id,
        privacy_class=PrivacyClass.OWNER_ONLY.value,
        happened_on=NOW.date(),
        payload=HeartMomentPayload(text="Private text", emotion=HeartEmotion.LOVED),
    )
    session.add(heart_moment)
    session.flush()
    event = _event(
        session,
        couple,
        EventType.HEART_MOMENT_CREATED,
        heart_moment,
        payload=PublicEventPayload(visibility=ContentVisibility.PRIVATE),
    )

    service.project_event(session, event)
    session.flush()

    count = session.execute(
        select(func.count(Activity.id)).where(Activity.source_event_id == event.id)
    ).scalar_one()
    assert count == 0


def test_comment_notifies_only_other_authorized_partner_and_replay_is_idempotent(
    session: Session, couple
) -> None:  # type: ignore[no-untyped-def]
    memory = _shared_memory(session, couple, owner=couple["anna"])
    ben_context = AuthorizationContext(
        account_id=couple["ben"].id,
        space_id=couple["space"].id,
    )
    comment = comment_service.create_comment(
        session,
        ben_context,
        target_type=CommentTarget.MEMORY,
        target_id=memory.id,
        body="Private relationship prose must stay out of the projection.",
    )
    event = session.execute(
        select(OutboxEvent).where(
            OutboxEvent.event_type == EventType.COMMENT_CREATED.value,
            OutboxEvent.subject_id == comment.id,
        )
    ).scalar_one()

    service.project_event(session, event)
    service.project_event(session, event)
    session.flush()

    notifications = session.execute(
        select(Notification).where(Notification.source_event_id == event.id)
    ).scalars().all()
    assert len(notifications) == 1
    notification = notifications[0]
    assert notification.recipient_account_id == couple["anna"].id
    assert notification.recipient_account_id != couple["ben"].id
    assert notification.kind == NotificationKind.COMMENT_CREATED.value
    assert notification.target_id == memory.id
    assert not hasattr(notification, "payload")
    assert not hasattr(notification, "body")


def test_later_privacy_transition_suppresses_stale_activity_immediately(
    client, session: Session, couple
) -> None:  # type: ignore[no-untyped-def]
    heart_moment = HeartMoment(
        space_id=couple["space"].id,
        owner_id=couple["anna"].id,
        privacy_class=PrivacyClass.SPACE_SHARED.value,
        happened_on=NOW.date(),
        payload=HeartMomentPayload(text="Shared first", emotion=HeartEmotion.SEEN),
    )
    session.add(heart_moment)
    session.flush()
    event = _event(
        session,
        couple,
        EventType.HEART_MOMENT_CREATED,
        heart_moment,
        payload=PublicEventPayload(visibility=ContentVisibility.SHARED),
    )
    service.project_event(session, event)
    session.flush()

    before = client.get(
        f"/api/v1/spaces/{couple['space'].id}/activity",
        headers=auth(couple["ben_token"]),
    )
    assert before.status_code == 200
    assert str(heart_moment.id) in {item["targetId"] for item in before.json()["items"]}

    heart_moment.privacy_class = PrivacyClass.OWNER_ONLY.value
    session.flush()

    after = client.get(
        f"/api/v1/spaces/{couple['space'].id}/activity",
        headers=auth(couple["ben_token"]),
    )
    assert after.status_code == 200
    assert str(heart_moment.id) not in {item["targetId"] for item in after.json()["items"]}


def test_activity_cursor_is_bound_to_account_and_space(client, session: Session, couple) -> None:  # type: ignore[no-untyped-def]
    memory = _shared_memory(session, couple)
    for offset in range(3):
        session.add(
            Activity(
                space_id=couple["space"].id,
                source_event_id=uuid4(),
                kind=ActivityKind.MEMORY_CREATED.value,
                actor_id=couple["anna"].id,
                target_type="MEMORY",
                target_id=memory.id,
                occurred_at=NOW - timedelta(minutes=offset),
            )
        )
    session.flush()

    first = client.get(
        f"/api/v1/spaces/{couple['space'].id}/activity?limit=1",
        headers=auth(couple["anna_token"]),
    )
    assert first.status_code == 200
    body = first.json()
    assert body["hasMore"] is True
    assert body["nextCursor"] is not None

    partner_reuse = client.get(
        f"/api/v1/spaces/{couple['space'].id}/activity",
        params={"cursor": body["nextCursor"]},
        headers=auth(couple["ben_token"]),
    )
    assert partner_reuse.status_code == 400
    assert partner_reuse.json()["code"] == "INVALID_CURSOR"

    foreign_reuse = client.get(
        f"/api/v1/spaces/{couple['foreign_space'].id}/activity",
        params={"cursor": body["nextCursor"]},
        headers=auth(couple["outsider_token"]),
    )
    assert foreign_reuse.status_code == 400
    assert foreign_reuse.json()["code"] == "INVALID_CURSOR"


def test_notification_read_is_idempotent_and_foreign_account_gets_404(
    client, session: Session, couple, monkeypatch
) -> None:  # type: ignore[no-untyped-def]
    memory = _shared_memory(session, couple)
    notification = Notification(
        space_id=couple["space"].id,
        recipient_account_id=couple["anna"].id,
        source_event_id=uuid4(),
        kind=NotificationKind.COMMENT_CREATED.value,
        actor_id=couple["ben"].id,
        target_type="MEMORY",
        target_id=memory.id,
        created_at=NOW,
    )
    session.add(notification)
    session.flush()
    read_at = NOW + timedelta(minutes=1)
    monkeypatch.setattr(service.clock, "now", lambda: read_at)

    path = f"/api/v1/spaces/{couple['space'].id}/notifications/{notification.id}/read"
    first = client.post(path, headers=auth(couple["anna_token"]))
    second = client.post(path, headers=auth(couple["anna_token"]))
    assert first.status_code == second.status_code == 200
    assert first.json()["readAt"] == second.json()["readAt"]

    foreign = client.post(path, headers=auth(couple["ben_token"]))
    assert foreign.status_code == 404
    assert foreign.json()["code"] == "NOTIFICATION_NOT_FOUND"


def test_mark_all_uses_cutoff_and_unread_count_ignores_later_rows(
    client, session: Session, couple, monkeypatch
) -> None:  # type: ignore[no-untyped-def]
    memory = _shared_memory(session, couple)
    old = Notification(
        space_id=couple["space"].id,
        recipient_account_id=couple["anna"].id,
        source_event_id=uuid4(),
        kind=NotificationKind.COMMENT_CREATED.value,
        actor_id=couple["ben"].id,
        target_type="MEMORY",
        target_id=memory.id,
        created_at=NOW - timedelta(minutes=1),
    )
    session.add(old)
    session.flush()
    monkeypatch.setattr(service.clock, "now", lambda: NOW)

    response = client.post(
        f"/api/v1/spaces/{couple['space'].id}/notifications/read-all",
        headers=auth(couple["anna_token"]),
    )
    assert response.status_code == 200
    assert response.json()["updated"] == 1

    later = Notification(
        space_id=couple["space"].id,
        recipient_account_id=couple["anna"].id,
        source_event_id=uuid4(),
        kind=NotificationKind.COMMENT_CREATED.value,
        actor_id=couple["ben"].id,
        target_type="MEMORY",
        target_id=memory.id,
        created_at=NOW + timedelta(seconds=1),
    )
    session.add(later)
    session.flush()

    count = client.get(
        f"/api/v1/spaces/{couple['space'].id}/notifications/unread-count",
        headers=auth(couple["anna_token"]),
    )
    assert count.status_code == 200
    assert count.json()["unreadCount"] == 1


def test_deleted_target_disappears_from_notification_list_and_count(
    client, session: Session, couple
) -> None:  # type: ignore[no-untyped-def]
    memory = _shared_memory(session, couple)
    notification = Notification(
        space_id=couple["space"].id,
        recipient_account_id=couple["anna"].id,
        source_event_id=uuid4(),
        kind=NotificationKind.COMMENT_CREATED.value,
        actor_id=couple["ben"].id,
        target_type="MEMORY",
        target_id=memory.id,
        created_at=NOW,
    )
    session.add(notification)
    session.flush()

    before = client.get(
        f"/api/v1/spaces/{couple['space'].id}/notifications/unread-count",
        headers=auth(couple["anna_token"]),
    )
    assert before.status_code == 200
    assert before.json()["unreadCount"] == 1

    session.delete(memory)
    session.flush()

    after = client.get(
        f"/api/v1/spaces/{couple['space'].id}/notifications",
        headers=auth(couple["anna_token"]),
    )
    assert after.status_code == 200
    assert after.json()["items"] == []

    count = client.get(
        f"/api/v1/spaces/{couple['space'].id}/notifications/unread-count",
        headers=auth(couple["anna_token"]),
    )
    assert count.status_code == 200
    assert count.json()["unreadCount"] == 0
