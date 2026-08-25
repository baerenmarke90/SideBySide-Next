"""PostgreSQL-/HTTP-Abnahme fuer den ersten M2-Memory-Runtime-Slice."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any
from uuid import UUID

import pytest
from sqlalchemy import select, text
from sqlalchemy.orm import Session

from sidebyside.outbox.models import OutboxEvent
from sidebyside.relationship import service as relationship_service
from tests.conftest import auth, make_account, make_space, requires_database, sign_in

pytestmark = [pytest.mark.integration, requires_database]


def memories_path(space_id: object) -> str:
    return f"/api/v1/spaces/{space_id}/memories"


def memory_body(
    *,
    title: str = "Unser erster Urlaub",
    body: str = "Ein geschuetzter Erinnerungstext.",
    happened_on: str | None = "2025-06-13",
) -> dict[str, Any]:
    return {"title": title, "body": body, "happenedOn": happened_on}


def if_match(token: str, version: int) -> dict[str, str]:
    return {**auth(token), "If-Match": f'"{version}"'}


@pytest.fixture
def paar(session: Session):  # type: ignore[no-untyped-def]
    anna = make_account(session, "Anna")
    ben = make_account(session, "Ben")
    fremd = make_account(session, "Fremd")

    space = make_space(session, anna)
    relationship_service.add_member(session, space.id, ben)
    fremder_space = make_space(session, fremd)
    session.flush()

    return {
        "anna": anna,
        "ben": ben,
        "fremd": fremd,
        "space": space,
        "fremder_space": fremder_space,
        "token_a": sign_in(session, anna),
        "token_b": sign_in(session, ben),
        "token_fremd": sign_in(session, fremd),
    }


def create_memory(client, paar, *, token_key: str = "token_a", **overrides):  # type: ignore[no-untyped-def]
    return client.post(
        memories_path(paar["space"].id),
        json=memory_body(**overrides),
        headers=auth(paar[token_key]),
    )


class TestCrudUndOwnership:
    def test_create_get_update_delete_als_autor(self, client, paar) -> None:  # type: ignore[no-untyped-def]
        created = create_memory(client, paar)
        assert created.status_code == 201
        body = created.json()
        assert UUID(body["id"]).version == 7
        assert body["spaceId"] == str(paar["space"].id)
        assert body["authorId"] == str(paar["anna"].id)
        assert body["author"]["displayName"] == "Anna"
        assert body["title"] == "Unser erster Urlaub"
        assert body["body"] == "Ein geschuetzter Erinnerungstext."
        assert body["happenedOn"] == "2025-06-13"
        assert body["capabilities"] == {
            "canEdit": True,
            "canDelete": True,
            "canComment": True,
        }
        assert "attachments" not in body
        assert created.headers["ETag"] == '"1"'

        detail = client.get(
            f"{memories_path(paar['space'].id)}/{body['id']}",
            headers=auth(paar["token_a"]),
        )
        assert detail.status_code == 200
        assert detail.headers["ETag"] == '"1"'

        updated = client.patch(
            f"{memories_path(paar['space'].id)}/{body['id']}",
            json={"title": "  Urlaub am Meer  ", "happenedOn": None},
            headers=if_match(paar["token_a"], 1),
        )
        assert updated.status_code == 200
        assert updated.json()["title"] == "Urlaub am Meer"
        assert updated.json()["body"] == body["body"]
        assert updated.json()["happenedOn"] is None
        assert updated.json()["version"] == 2
        assert updated.headers["ETag"] == '"2"'

        deleted = client.delete(
            f"{memories_path(paar['space'].id)}/{body['id']}",
            headers=if_match(paar["token_a"], 2),
        )
        assert deleted.status_code == 204

        missing = client.get(
            f"{memories_path(paar['space'].id)}/{body['id']}",
            headers=auth(paar["token_a"]),
        )
        assert missing.status_code == 404
        assert missing.json()["code"] == "RESOURCE_NOT_FOUND"

    def test_partner_darf_lesen_aber_nicht_schreiben(self, client, paar) -> None:  # type: ignore[no-untyped-def]
        memory = create_memory(client, paar).json()

        detail = client.get(
            f"{memories_path(paar['space'].id)}/{memory['id']}",
            headers=auth(paar["token_b"]),
        )
        assert detail.status_code == 200
        assert detail.json()["capabilities"] == {
            "canEdit": False,
            "canDelete": False,
            "canComment": True,
        }

        listing = client.get(
            memories_path(paar["space"].id),
            headers=auth(paar["token_b"]),
        )
        assert listing.status_code == 200
        assert [item["id"] for item in listing.json()["items"]] == [memory["id"]]

        update = client.patch(
            f"{memories_path(paar['space'].id)}/{memory['id']}",
            json={"title": "Partner-Aenderung"},
            headers=if_match(paar["token_b"], memory["version"]),
        )
        assert update.status_code == 403
        assert update.json()["code"] == "NOT_RESOURCE_OWNER"

        delete = client.delete(
            f"{memories_path(paar['space'].id)}/{memory['id']}",
            headers=if_match(paar["token_b"], memory["version"]),
        )
        assert delete.status_code == 403
        assert delete.json()["code"] == "NOT_RESOURCE_OWNER"

    def test_author_id_kann_nicht_ueberschrieben_werden(self, client, paar) -> None:  # type: ignore[no-untyped-def]
        memory = create_memory(client, paar).json()
        response = client.patch(
            f"{memories_path(paar['space'].id)}/{memory['id']}",
            json={"authorId": str(paar["ben"].id)},
            headers=if_match(paar["token_a"], memory["version"]),
        )
        assert response.status_code == 422

        detail = client.get(
            f"{memories_path(paar['space'].id)}/{memory['id']}",
            headers=auth(paar["token_a"]),
        )
        assert detail.json()["authorId"] == str(paar["anna"].id)

    def test_stale_update_und_delete_liefern_m2_conflict_code(self, client, paar) -> None:  # type: ignore[no-untyped-def]
        memory = create_memory(client, paar).json()
        first = client.patch(
            f"{memories_path(paar['space'].id)}/{memory['id']}",
            json={"body": "Neue Fassung"},
            headers=if_match(paar["token_a"], 1),
        )
        assert first.status_code == 200
        assert first.json()["version"] == 2

        stale_update = client.patch(
            f"{memories_path(paar['space'].id)}/{memory['id']}",
            json={"body": "Veraltete Fassung"},
            headers=if_match(paar["token_a"], 1),
        )
        assert stale_update.status_code == 409
        assert stale_update.json()["code"] == "RESOURCE_VERSION_CONFLICT"

        stale_delete = client.delete(
            f"{memories_path(paar['space'].id)}/{memory['id']}",
            headers=if_match(paar["token_a"], 1),
        )
        assert stale_delete.status_code == 409
        assert stale_delete.json()["code"] == "RESOURCE_VERSION_CONFLICT"


class TestTenantUndAuthentifizierung:
    def test_fremder_space_und_fremde_resource_id_bleiben_404(self, client, paar) -> None:  # type: ignore[no-untyped-def]
        memory = create_memory(client, paar).json()

        no_membership = client.get(
            f"{memories_path(paar['space'].id)}/{memory['id']}",
            headers=auth(paar["token_fremd"]),
        )
        assert no_membership.status_code == 404
        assert no_membership.json()["code"] == "SPACE_NOT_FOUND"

        foreign_id = client.get(
            f"{memories_path(paar['fremder_space'].id)}/{memory['id']}",
            headers=auth(paar["token_fremd"]),
        )
        assert foreign_id.status_code == 404
        assert foreign_id.json()["code"] == "RESOURCE_NOT_FOUND"

    def test_anonym_bleibt_401(self, client, paar) -> None:  # type: ignore[no-untyped-def]
        response = client.get(memories_path(paar["space"].id))
        assert response.status_code == 401
        assert response.json()["code"] == "AUTHENTICATION_REQUIRED"


class TestPagination:
    def test_cursor_hat_keine_duplikate_und_ist_integritaetsgeschuetzt(self, client, paar) -> None:  # type: ignore[no-untyped-def]
        created_ids = {
            create_memory(client, paar, title=f"Memory {index}").json()["id"] for index in range(3)
        }

        first = client.get(
            f"{memories_path(paar['space'].id)}?limit=2",
            headers=auth(paar["token_a"]),
        )
        assert first.status_code == 200
        first_body = first.json()
        assert len(first_body["items"]) == 2
        assert first_body["hasMore"] is True
        assert first_body["nextCursor"]

        second = client.get(
            memories_path(paar["space"].id),
            params={"limit": 2, "cursor": first_body["nextCursor"]},
            headers=auth(paar["token_a"]),
        )
        assert second.status_code == 200
        second_body = second.json()
        page_ids = {item["id"] for item in first_body["items"] + second_body["items"]}
        assert page_ids == created_ids
        assert second_body["hasMore"] is False
        assert second_body["nextCursor"] is None

        cursor = first_body["nextCursor"]
        tampered = cursor[:-1] + ("A" if cursor[-1] != "A" else "B")
        invalid = client.get(
            memories_path(paar["space"].id),
            params={"cursor": tampered},
            headers=auth(paar["token_a"]),
        )
        assert invalid.status_code == 400
        assert invalid.json()["code"] == "INVALID_CURSOR"

    def test_cursor_ist_an_filter_gebunden(self, client, paar) -> None:  # type: ignore[no-untyped-def]
        for index in range(2):
            create_memory(client, paar, title=f"2025-{index}", happened_on="2025-01-01")
        first = client.get(
            memories_path(paar["space"].id),
            params={"year": 2025, "limit": 1},
            headers=auth(paar["token_a"]),
        ).json()

        wrong_filter = client.get(
            memories_path(paar["space"].id),
            params={"year": 2026, "cursor": first["nextCursor"]},
            headers=auth(paar["token_a"]),
        )
        assert wrong_filter.status_code == 400
        assert wrong_filter.json()["code"] == "INVALID_CURSOR"

    def test_year_verwendet_happened_on_und_created_at_fallback(self, client, paar) -> None:  # type: ignore[no-untyped-def]
        current_year = datetime.now(UTC).year
        past_year = current_year - 1
        old = create_memory(
            client,
            paar,
            title="Alt",
            happened_on=f"{past_year}-12-31",
        ).json()
        current = create_memory(client, paar, title="Ohne Datum", happened_on=None).json()

        past = client.get(
            memories_path(paar["space"].id),
            params={"year": past_year},
            headers=auth(paar["token_a"]),
        )
        assert [item["id"] for item in past.json()["items"]] == [old["id"]]

        current_response = client.get(
            memories_path(paar["space"].id),
            params={"year": current_year},
            headers=auth(paar["token_a"]),
        )
        assert current["id"] in {item["id"] for item in current_response.json()["items"]}


class TestProtectedPayloadUndOutbox:
    def test_schema_hat_keine_klartextspalten(self, session: Session) -> None:
        columns = set(
            session.execute(
                text(
                    "SELECT column_name FROM information_schema.columns "
                    "WHERE table_name = 'memories'"
                )
            ).scalars()
        )
        assert {"payload", "crypto_version", "space_id", "owner_id", "version"} <= columns
        assert "title" not in columns
        assert "body" not in columns

    def test_create_update_delete_events_enthalten_keinen_klartext(
        self, client, paar, session
    ) -> None:  # type: ignore[no-untyped-def]
        title = "CANARY_MEMORY_TITLE_71"
        body = "CANARY_MEMORY_BODY_71"
        memory = create_memory(client, paar, title=title, body=body).json()
        updated = client.patch(
            f"{memories_path(paar['space'].id)}/{memory['id']}",
            json={"body": "CANARY_UPDATED_BODY_71"},
            headers=if_match(paar["token_a"], 1),
        ).json()
        response = client.delete(
            f"{memories_path(paar['space'].id)}/{memory['id']}",
            headers=if_match(paar["token_a"], updated["version"]),
        )
        assert response.status_code == 204

        events = list(
            session.execute(
                select(OutboxEvent)
                .where(OutboxEvent.subject_id == UUID(memory["id"]))
                .order_by(OutboxEvent.created_at, OutboxEvent.id)
            ).scalars()
        )
        assert {event.event_type for event in events} == {
            "MEMORY_CREATED",
            "MEMORY_UPDATED",
            "MEMORY_DELETED",
        }
        assert {event.resource_version for event in events} == {1, 2}
        for event in events:
            serialized = str(event.payload.model_dump(exclude_none=True))
            assert serialized == "{}"
            assert title not in serialized
            assert body not in serialized
            assert "CANARY_UPDATED_BODY_71" not in serialized
