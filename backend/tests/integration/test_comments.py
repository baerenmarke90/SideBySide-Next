"""PostgreSQL-/HTTP-Abnahme fuer M2-Kommentare."""

from __future__ import annotations

from uuid import UUID, uuid4

import pytest
from sqlalchemy import select
from sqlalchemy.orm import Session

from sidebyside.comments.models import Comment
from sidebyside.comments.notifications import deliver
from sidebyside.outbox.models import OutboxEvent
from sidebyside.relationship import service as relationship_service
from tests.conftest import auth, make_account, make_space, requires_database, sign_in

pytestmark = [pytest.mark.integration, requires_database]

GEHEIM = "Kommentartext-darf-nicht-ins-event"


@pytest.fixture
def paar(session: Session):  # type: ignore[no-untyped-def]
    anna = make_account(session, "Anna")
    ben = make_account(session, "Ben")
    fremd = make_account(session, "Fremd")
    space = make_space(session, anna)
    relationship_service.add_member(session, space.id, ben)
    beta = make_space(session, fremd)
    relationship_service.add_member(session, beta.id, ben)
    session.flush()
    return {
        "anna": anna,
        "ben": ben,
        "space": space,
        "beta": beta,
        "token_a": sign_in(session, anna),
        "token_b": sign_in(session, ben),
        "token_f": sign_in(session, fremd),
    }


def basis(space_id: object) -> str:
    return f"/api/v1/spaces/{space_id}"


def memory(client, paar, *, token: str | None = None):  # type: ignore[no-untyped-def]
    return client.post(
        f"{basis(paar['space'].id)}/memories",
        json={"title": "M", "body": "B", "happenedOn": "2025-06-13"},
        headers=auth(token or paar["token_a"]),
    ).json()


def milestone(client, paar):  # type: ignore[no-untyped-def]
    return client.post(
        f"{basis(paar['space'].id)}/milestones",
        json={"title": "Meilenstein", "happenedOn": "2025-06-13"},
        headers=auth(paar["token_a"]),
    ).json()


def heart(client, paar, visibility: str = "SHARED"):  # type: ignore[no-untyped-def]
    return client.post(
        f"{basis(paar['space'].id)}/heart-moments",
        json={
            "text": "Herz",
            "emotion": "LOVED",
            "visibility": visibility,
            "happenedOn": "2025-06-13",
        },
        headers=auth(paar["token_a"]),
    ).json()


def comment_path(space_id: object, parent: str, parent_id: str) -> str:
    return f"{basis(space_id)}/{parent}/{parent_id}/comments"


def if_match(token: str, version: int) -> dict[str, str]:
    return {**auth(token), "If-Match": f'"{version}"'}


@pytest.mark.parametrize(
    ("factory", "segment"),
    [(memory, "memories"), (milestone, "milestones"), (heart, "heart-moments")],
)
def test_beide_partner_kommentieren_shared_targets(client, paar, factory, segment) -> None:  # type: ignore[no-untyped-def]
    parent = factory(client, paar)
    path = comment_path(paar["space"].id, segment, parent["id"])

    angelegt = client.post(path, json={"body": "  Hallo  "}, headers=auth(paar["token_b"]))
    assert angelegt.status_code == 201
    payload = angelegt.json()
    assert UUID(payload["id"]).version == 7
    assert payload["body"] == "Hallo"
    assert payload["authorId"] == str(paar["ben"].id)
    assert payload["version"] == 1
    assert angelegt.headers["ETag"] == '"1"'

    liste = client.get(path, headers=auth(paar["token_a"]))
    assert [entry["id"] for entry in liste.json()["items"]] == [payload["id"]]


def test_private_heart_moment_akzeptiert_keine_comments(client, paar) -> None:  # type: ignore[no-untyped-def]
    private = heart(client, paar, "PRIVATE")
    path = comment_path(paar["space"].id, "heart-moments", private["id"])

    for token in (paar["token_a"], paar["token_b"]):
        response = client.post(path, json={"body": "Nein"}, headers=auth(token))
        assert response.status_code == 404
        assert response.json()["code"] == "COMMENT_TARGET_NOT_AVAILABLE"


def test_cross_space_target_erzeugt_weder_comment_noch_event(client, paar, session) -> None:  # type: ignore[no-untyped-def]
    m = memory(client, paar)
    response = client.post(
        comment_path(paar["beta"].id, "memories", m["id"]),
        json={"body": GEHEIM},
        headers=auth(paar["token_b"]),
    )
    assert response.status_code == 404
    assert session.execute(select(Comment)).scalars().all() == []
    assert (
        session.execute(select(OutboxEvent).where(OutboxEvent.event_type == "COMMENT_CREATED"))
        .scalars()
        .all()
        == []
    )


def test_nur_comment_autor_darf_update_und_delete(client, paar) -> None:  # type: ignore[no-untyped-def]
    m = memory(client, paar)
    path = comment_path(paar["space"].id, "memories", m["id"])
    c = client.post(path, json={"body": "Erste"}, headers=auth(paar["token_b"])).json()
    detail = f"{basis(paar['space'].id)}/comments/{c['id']}"

    denied = client.patch(
        detail,
        json={"body": "Fremd"},
        headers=if_match(paar["token_a"], 1),
    )
    assert denied.status_code == 403

    updated = client.patch(
        detail,
        json={"body": "Neu"},
        headers=if_match(paar["token_b"], 1),
    )
    assert updated.status_code == 200
    assert updated.json()["version"] == 2

    stale = client.delete(detail, headers=if_match(paar["token_b"], 1))
    assert stale.status_code == 409
    assert stale.json()["code"] == "RESOURCE_VERSION_CONFLICT"

    deleted = client.delete(detail, headers=if_match(paar["token_b"], 2))
    assert deleted.status_code == 204


def test_cursor_ist_an_parent_und_space_gebunden(client, paar) -> None:  # type: ignore[no-untyped-def]
    first = memory(client, paar)
    second = memory(client, paar)
    first_path = comment_path(paar["space"].id, "memories", first["id"])
    second_path = comment_path(paar["space"].id, "memories", second["id"])
    for i in range(2):
        client.post(first_path, json={"body": f"C{i}"}, headers=auth(paar["token_b"]))

    page = client.get(f"{first_path}?limit=1", headers=auth(paar["token_b"])).json()
    cursor = page["nextCursor"]
    assert cursor is not None

    wrong_parent = client.get(
        f"{second_path}?limit=1&cursor={cursor}", headers=auth(paar["token_b"])
    )
    assert wrong_parent.status_code == 400
    assert wrong_parent.json()["code"] == "INVALID_CURSOR"


@pytest.mark.parametrize(
    ("factory", "segment"),
    [(memory, "memories"), (milestone, "milestones"), (heart, "heart-moments")],
)
def test_parent_delete_loescht_comments_atomar(
    client,
    paar,
    session,
    factory,
    segment,
) -> None:  # type: ignore[no-untyped-def]
    parent = factory(client, paar)
    path = comment_path(paar["space"].id, segment, parent["id"])
    comment = client.post(path, json={"body": "weg"}, headers=auth(paar["token_b"])).json()

    deleted = client.delete(
        f"{basis(paar['space'].id)}/{segment}/{parent['id']}",
        headers=if_match(paar["token_a"], 1),
    )
    assert deleted.status_code == 204
    assert session.get(Comment, UUID(comment["id"])) is None


def test_shared_to_private_loescht_comments_und_resurrected_nichts(client, paar) -> None:  # type: ignore[no-untyped-def]
    h = heart(client, paar)
    path = comment_path(paar["space"].id, "heart-moments", h["id"])
    client.post(path, json={"body": "verschwindet"}, headers=auth(paar["token_b"]))

    privacy_path = f"{basis(paar['space'].id)}/heart-moments/{h['id']}/visibility"
    private = client.patch(
        privacy_path,
        json={"visibility": "PRIVATE"},
        headers=if_match(paar["token_a"], 1),
    )
    assert private.status_code == 200

    shared = client.patch(
        privacy_path,
        json={"visibility": "SHARED"},
        headers=if_match(paar["token_a"], 2),
    )
    assert shared.status_code == 200
    listed = client.get(path, headers=auth(paar["token_a"]))
    assert listed.status_code == 200
    assert listed.json()["items"] == []


def test_comment_created_event_ist_inhaltsfrei_und_nur_fuer_fremden_parent(
    client, paar, session
) -> None:  # type: ignore[no-untyped-def]
    m = memory(client, paar)
    path = comment_path(paar["space"].id, "memories", m["id"])
    own = client.post(path, json={"body": "eigener"}, headers=auth(paar["token_a"]))
    assert own.status_code == 201
    other = client.post(path, json={"body": GEHEIM}, headers=auth(paar["token_b"]))
    assert other.status_code == 201

    events = list(
        session.execute(
            select(OutboxEvent).where(OutboxEvent.event_type == "COMMENT_CREATED")
        ).scalars()
    )
    assert len(events) == 1
    event = events[0]
    assert event.actor_id == paar["ben"].id
    assert event.payload.recipient_id == paar["anna"].id
    assert event.payload.target_type == "MEMORY"
    assert event.payload.target_id == UUID(m["id"])
    assert GEHEIM not in repr(event.payload.model_dump())


class RecordingSink:
    def __init__(self) -> None:
        self.keys: list[str] = []

    def send_comment_notification(
        self,
        *,
        idempotency_key: str,
        recipient_id: UUID,
        target_type: str,
        target_id: UUID,
    ) -> None:
        del recipient_id, target_type, target_id
        self.keys.append(idempotency_key)


class RetrySafeSink:
    def __init__(self) -> None:
        self.attempts: list[str] = []
        self.deliveries: set[str] = set()
        self.fail_after_first_delivery = True

    def send_comment_notification(
        self,
        *,
        idempotency_key: str,
        recipient_id: UUID,
        target_type: str,
        target_id: UUID,
    ) -> None:
        del recipient_id, target_type, target_id
        self.attempts.append(idempotency_key)
        self.deliveries.add(idempotency_key)
        if self.fail_after_first_delivery:
            self.fail_after_first_delivery = False
            raise RuntimeError("simulated crash after external delivery")


def test_notification_hook_nutzt_stabile_outbox_id_als_idempotency_key(
    client, paar, session
) -> None:  # type: ignore[no-untyped-def]
    m = memory(client, paar)
    path = comment_path(paar["space"].id, "memories", m["id"])
    client.post(path, json={"body": GEHEIM}, headers=auth(paar["token_b"]))
    event = session.execute(
        select(OutboxEvent).where(OutboxEvent.event_type == "COMMENT_CREATED")
    ).scalar_one()

    sink = RecordingSink()
    assert deliver(event, sink) is True
    assert sink.keys == [str(event.id)]
    assert event.processed_at is not None


def test_notification_retry_erzeugt_keine_doppelte_fachliche_zustellung(
    client, paar, session
) -> None:  # type: ignore[no-untyped-def]
    m = memory(client, paar)
    path = comment_path(paar["space"].id, "memories", m["id"])
    client.post(path, json={"body": GEHEIM}, headers=auth(paar["token_b"]))
    event = session.execute(
        select(OutboxEvent).where(OutboxEvent.event_type == "COMMENT_CREATED")
    ).scalar_one()

    key = str(event.id)
    sink = RetrySafeSink()
    with pytest.raises(RuntimeError, match="simulated crash"):
        deliver(event, sink)

    assert event.processed_at is None
    assert sink.deliveries == {key}

    assert deliver(event, sink) is True
    assert sink.attempts == [key, key]
    assert sink.deliveries == {key}
    assert event.processed_at is not None


def test_unbekannter_parent_bleibt_privacy_safe_404(client, paar) -> None:  # type: ignore[no-untyped-def]
    response = client.post(
        comment_path(paar["space"].id, "memories", str(uuid4())),
        json={"body": "x"},
        headers=auth(paar["token_a"]),
    )
    assert response.status_code == 404
    assert response.json()["code"] == "COMMENT_TARGET_NOT_AVAILABLE"
