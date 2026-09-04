"""PostgreSQL/HTTP acceptance tests for the story timeline.

The timeline is where all four M2 types converge, making a privacy failure
particularly costly: a private HeartMoment in a shared list cannot be undone.
These tests therefore verify the absence of private rows from both directions:
neither the partner nor the owner may see them here.
"""

from __future__ import annotations

import pytest
from sqlalchemy import text
from sqlalchemy.orm import Session

from sidebyside.relationship import service as relationship_service
from tests.conftest import auth, make_account, make_space, requires_database, sign_in

pytestmark = [pytest.mark.integration, requires_database]


@pytest.fixture
def couple(session: Session):  # type: ignore[no-untyped-def]
    anna = make_account(session, "Anna")
    ben = make_account(session, "Ben")
    outsider = make_account(session, "Fremd")
    space = make_space(session, anna)
    relationship_service.add_member(session, space.id, ben)
    beta = make_space(session, outsider)
    session.flush()
    return {
        "anna": anna,
        "ben": ben,
        "space": space,
        "beta": beta,
        "token_a": sign_in(session, anna),
        "token_b": sign_in(session, ben),
        "token_f": sign_in(session, outsider),
    }


def base_path(space_id: object) -> str:
    return f"/api/v1/spaces/{space_id}"


def memory(client, couple, *, title="M", happened_on="2025-06-13", token=None):  # type: ignore[no-untyped-def]
    payload = {"title": title, "body": "B"}
    if happened_on is not None:
        payload["happenedOn"] = happened_on
    response = client.post(
        f"{base_path(couple['space'].id)}/memories",
        json=payload,
        headers=auth(token or couple["token_a"]),
    )
    assert response.status_code == 201, response.text
    return response.json()


def milestone(client, couple, *, title="MS", happened_on="2025-06-13", token=None):  # type: ignore[no-untyped-def]
    response = client.post(
        f"{base_path(couple['space'].id)}/milestones",
        json={"title": title, "happenedOn": happened_on},
        headers=auth(token or couple["token_a"]),
    )
    assert response.status_code == 201, response.text
    return response.json()


def heart_moment(client, couple, *, visibility="SHARED", happened_on="2025-06-13", token=None):  # type: ignore[no-untyped-def]
    response = client.post(
        f"{base_path(couple['space'].id)}/heart-moments",
        json={
            "text": "Danke",
            "emotion": "LOVED",
            "visibility": visibility,
            "happenedOn": happened_on,
        },
        headers=auth(token or couple["token_a"]),
    )
    assert response.status_code == 201, response.text
    return response.json()


def timeline(client, couple, *, token=None, **parameters):  # type: ignore[no-untyped-def]
    response = client.get(
        f"{base_path(couple['space'].id)}/timeline",
        params=parameters,
        headers=auth(token or couple["token_a"]),
    )
    return response


def ids(response) -> list[str]:  # type: ignore[no-untyped-def]
    keys = {"MEMORY": "memory", "HEART_MOMENT": "heartMoment", "MILESTONE": "milestone"}
    return [item[keys[item["kind"]]]["id"] for item in response.json()["items"]]


class TestPrivacy:
    def test_private_heart_moment_is_absent_for_partner(self, client, couple) -> None:  # type: ignore[no-untyped-def]
        private = heart_moment(client, couple, visibility="PRIVATE")
        assert private["id"] not in ids(timeline(client, couple, token=couple["token_b"]))

    def test_private_heart_moment_is_also_absent_for_owner(self, client, couple) -> None:  # type: ignore[no-untyped-def]
        """M2-D22: the story is shared content, not a personal history.

        The owner sees a private entry in their own list, but not here.
        Otherwise one route would expose two different result sets.
        """
        private = heart_moment(client, couple, visibility="PRIVATE")
        assert private["id"] not in ids(timeline(client, couple, token=couple["token_a"]))

    def test_owner_finds_entry_in_own_list(self, client, couple) -> None:  # type: ignore[no-untyped-def]
        private = heart_moment(client, couple, visibility="PRIVATE")
        response = client.get(
            f"{base_path(couple['space'].id)}/heart-moments",
            params={"visibility": "PRIVATE"},
            headers=auth(couple["token_a"]),
        )
        assert [item["id"] for item in response.json()["items"]] == [private["id"]]

    def test_switch_to_private_removes_item(self, client, couple) -> None:  # type: ignore[no-untyped-def]
        shared = heart_moment(client, couple, visibility="SHARED")
        assert shared["id"] in ids(timeline(client, couple))

        client.patch(
            f"{base_path(couple['space'].id)}/heart-moments/{shared['id']}/visibility",
            json={"visibility": "PRIVATE"},
            headers={**auth(couple["token_a"]), "If-Match": f'"{shared["version"]}"'},
        )
        assert shared["id"] not in ids(timeline(client, couple))
        assert shared["id"] not in ids(timeline(client, couple, token=couple["token_b"]))

    def test_foreign_space_returns_nothing(self, client, couple) -> None:  # type: ignore[no-untyped-def]
        memory(client, couple)
        response = client.get(
            f"{base_path(couple['beta'].id)}/timeline",
            headers=auth(couple["token_a"]),
        )
        assert response.status_code == 404

    def test_visibility_is_not_a_parameter(self, client, couple) -> None:  # type: ignore[no-untyped-def]
        """M2-D22: a supplied value must not silently become a filter."""
        heart_moment(client, couple, visibility="PRIVATE")
        response = timeline(client, couple, visibility="PRIVATE")
        assert ids(response) == []


class TestSorting:
    def test_effective_date_falls_back_to_created_at(self, client, couple) -> None:  # type: ignore[no-untyped-def]
        """M2-D08: a memory without happenedOn must not disappear."""
        without_date = memory(client, couple, happened_on=None)
        items = timeline(client, couple).json()["items"]
        matching = [item for item in items if item["memory"]["id"] == without_date["id"]]
        assert len(matching) == 1
        assert matching[0]["effectiveDate"] == without_date["createdAt"][:10]

    def test_descending_is_default(self, client, couple) -> None:  # type: ignore[no-untyped-def]
        older = memory(client, couple, title="alt", happened_on="2024-01-01")
        newer = memory(client, couple, title="neu", happened_on="2026-01-01")
        assert ids(timeline(client, couple))[:2] == [newer["id"], older["id"]]

    def test_ascending_reverses_complete_key(self, client, couple) -> None:  # type: ignore[no-untyped-def]
        older = memory(client, couple, title="alt", happened_on="2024-01-01")
        newer = memory(client, couple, title="neu", happened_on="2026-01-01")
        assert ids(timeline(client, couple, order="ASC"))[:2] == [older["id"], newer["id"]]

    def test_kind_rank_decides_on_identical_timestamp(self, client, couple, session) -> None:  # type: ignore[no-untyped-def]
        """MEMORY=1, HEART_MOMENT=2, MILESTONE=3 (M2-D08).

        The rank applies only when both `effectiveDate` and `createdAt` are
        identical. Entries created in sequence have different timestamps, so
        this test forces a collision to exercise the actual tie-breaker.
        """
        m = memory(client, couple, happened_on="2025-06-13")
        h = heart_moment(client, couple, happened_on="2025-06-13")
        ms = milestone(client, couple, happened_on="2025-06-13")

        same_timestamp = "2025-06-13 08:00:00+00"
        for table, item in (
            ("memories", m),
            ("heart_moments", h),
            ("milestones", ms),
        ):
            session.execute(
                text(f"UPDATE {table} SET created_at = :value WHERE id = :id"),
                {"value": same_timestamp, "id": item["id"]},
            )
        session.flush()

        assert ids(timeline(client, couple, order="ASC")) == [m["id"], h["id"], ms["id"]]
        assert ids(timeline(client, couple)) == [ms["id"], h["id"], m["id"]]

    def test_id_breaks_final_tie(self, client, couple, session) -> None:  # type: ignore[no-untyped-def]
        """Equal values in the first three keys and the same item type."""
        first = memory(client, couple, happened_on="2025-06-13")
        second = memory(client, couple, happened_on="2025-06-13")
        session.execute(
            text("UPDATE memories SET created_at = :value WHERE id IN (:a, :b)"),
            {"value": "2025-06-13 08:00:00+00", "a": first["id"], "b": second["id"]},
        )
        session.flush()

        ascending = ids(timeline(client, couple, order="ASC"))
        assert ascending == sorted([first["id"], second["id"]])
        assert ids(timeline(client, couple)) == list(reversed(ascending))


class TestFilter:
    def test_type_narrows_result_set(self, client, couple) -> None:  # type: ignore[no-untyped-def]
        m = memory(client, couple)
        milestone(client, couple)
        assert ids(timeline(client, couple, type=["MEMORY"])) == [m["id"]]

    def test_type_is_repeatable(self, client, couple) -> None:  # type: ignore[no-untyped-def]
        m = memory(client, couple)
        ms = milestone(client, couple)
        heart_moment(client, couple)
        assert set(ids(timeline(client, couple, type=["MEMORY", "MILESTONE"]))) == {
            m["id"],
            ms["id"],
        }

    def test_year_filters_on_effective_date(self, client, couple) -> None:  # type: ignore[no-untyped-def]
        older = memory(client, couple, happened_on="2024-05-05")
        memory(client, couple, happened_on="2026-05-05")
        assert ids(timeline(client, couple, year=2024)) == [older["id"]]

    def test_year_outside_range_is_rejected(self, client, couple) -> None:  # type: ignore[no-untyped-def]
        assert timeline(client, couple, year=1800).status_code == 422


class TestPagination:
    def test_pages_have_no_gaps_or_duplicates(self, client, couple) -> None:  # type: ignore[no-untyped-def]
        expected = [memory(client, couple, title=f"M{i}")["id"] for i in range(5)]
        expected += [milestone(client, couple, title=f"MS{i}")["id"] for i in range(4)]

        collected: list[str] = []
        cursor = None
        for _ in range(10):
            response = timeline(client, couple, limit=2, **({"cursor": cursor} if cursor else {}))
            collected += ids(response)
            cursor = response.json()["nextCursor"]
            if cursor is None:
                break
        assert sorted(collected) == sorted(expected)
        assert len(collected) == len(set(collected))

    def test_limit_may_change_between_pages(self, client, couple) -> None:  # type: ignore[no-untyped-def]
        """The cursor is independent of the page size."""
        for i in range(6):
            memory(client, couple, title=f"M{i}")
        first = timeline(client, couple, limit=2)
        second = timeline(client, couple, limit=4, cursor=first.json()["nextCursor"])
        assert set(ids(first)) & set(ids(second)) == set()
        assert len(ids(second)) == 4

    def test_cursor_from_different_filter_is_rejected(self, client, couple) -> None:  # type: ignore[no-untyped-def]
        for i in range(4):
            memory(client, couple, title=f"M{i}")
        cursor = timeline(client, couple, limit=2).json()["nextCursor"]
        response = timeline(client, couple, limit=2, cursor=cursor, type=["MEMORY"])
        assert response.status_code == 400
        assert response.json()["code"] == "INVALID_CURSOR"

    def test_cursor_from_different_direction_is_rejected(self, client, couple) -> None:  # type: ignore[no-untyped-def]
        for i in range(4):
            memory(client, couple, title=f"M{i}")
        cursor = timeline(client, couple, limit=2).json()["nextCursor"]
        assert timeline(client, couple, limit=2, cursor=cursor, order="ASC").status_code == 400

    def test_tampered_cursor_is_rejected(self, client, couple) -> None:  # type: ignore[no-untyped-def]
        for i in range(4):
            memory(client, couple, title=f"M{i}")
        cursor = timeline(client, couple, limit=2).json()["nextCursor"]
        response = timeline(client, couple, limit=2, cursor=cursor[:-2] + "xy")
        assert response.status_code == 400
        assert "spaceId" not in response.text


class TestProjection:
    def test_memory_includes_author_and_gallery(self, client, couple) -> None:  # type: ignore[no-untyped-def]
        memory(client, couple)
        item = timeline(client, couple).json()["items"][0]
        assert item["kind"] == "MEMORY"
        assert item["memory"]["author"]["displayName"] == "Anna"
        assert item["memory"]["attachments"] == []

    def test_capabilities_follow_author_rule(self, client, couple) -> None:  # type: ignore[no-untyped-def]
        memory(client, couple, token=couple["token_a"])
        for_author = timeline(client, couple, token=couple["token_a"]).json()["items"][0]
        for_partner = timeline(client, couple, token=couple["token_b"]).json()["items"][0]
        assert for_author["memory"]["capabilities"]["canEdit"] is True
        assert for_partner["memory"]["capabilities"]["canEdit"] is False

    def test_memory_body_is_not_in_list(self, client, couple) -> None:  # type: ignore[no-untyped-def]
        """The card needs a heading, not the complete text."""
        memory(client, couple)
        assert "body" not in timeline(client, couple).json()["items"][0]["memory"]


class TestAvailableYears:
    def test_available_years_are_kind_aware_and_ordered_descending(self, client, couple) -> None:  # type: ignore[no-untyped-def]
        # Memory 2024 + Milestone 2026
        memory(client, couple, title="Mem 2024", happened_on="2024-05-10")
        milestone(client, couple, title="Mile 2026", happened_on="2026-07-20")

        # 1. Alle Inhalte -> [2026, 2024]
        res_all = timeline(client, couple)
        assert res_all.status_code == 200
        assert res_all.json()["availableYears"] == [2026, 2024]

        # 2. kind=MILESTONE -> [2026]
        res_milestone = timeline(client, couple, type=["MILESTONE"])
        assert res_milestone.status_code == 200
        assert res_milestone.json()["availableYears"] == [2026]

        # 3. kind=MEMORY -> [2024]
        res_memory = timeline(client, couple, type=["MEMORY"])
        assert res_memory.status_code == 200
        assert res_memory.json()["availableYears"] == [2024]

    def test_available_years_ignores_active_year_filter_so_deep_links_recover(
        self, client, couple
    ) -> None:  # type: ignore[no-untyped-def]
        milestone(client, couple, title="Mile 2026", happened_on="2026-07-20")

        # Deep link ?type=MILESTONE&year=1997
        res = timeline(client, couple, type=["MILESTONE"], year=1997)
        assert res.status_code == 200
        data = res.json()
        assert data["items"] == []
        # Crucial #618 requirement: availableYears still contains 2026!
        assert data["availableYears"] == [2026]

    def test_available_years_preserves_older_years_across_pagination(self, client, couple) -> None:  # type: ignore[no-untyped-def]
        memory(client, couple, title="Mem 2023", happened_on="2023-01-01")
        memory(client, couple, title="Mem 2025", happened_on="2025-01-01")
        memory(client, couple, title="Mem 2026", happened_on="2026-01-01")

        # First page with limit=1 only returns 1 item, but availableYears has all 3
        res = timeline(client, couple, limit=1)
        assert res.status_code == 200
        data = res.json()
        assert len(data["items"]) == 1
        assert data["hasMore"] is True
        assert data["availableYears"] == [2026, 2025, 2023]

    def test_private_heart_moment_does_not_leak_year(self, client, couple) -> None:  # type: ignore[no-untyped-def]
        # Partner creates a private heart moment in 2022
        heart_moment(
            client, couple, visibility="PRIVATE", happened_on="2022-03-15", token=couple["token_b"]
        )
        # Shared memory in 2025
        memory(client, couple, title="Shared 2025", happened_on="2025-01-01")

        # Token A (Anna) timeline must NOT show 2022 in availableYears
        res = timeline(client, couple, token=couple["token_a"])
        assert res.status_code == 200
        assert 2022 not in res.json()["availableYears"]
        assert res.json()["availableYears"] == [2025]
