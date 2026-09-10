"""Account+Space isolation and persistence tests for Dashboard preferences."""

from __future__ import annotations

import pytest
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from sidebyside.authorization import PrivacyClass
from sidebyside.dashboard.models import DashboardModulePreference
from sidebyside.dashboard.preferences import DashboardModuleKey
from sidebyside.plans.models import Plan, PlanPayload, PlanStatus
from sidebyside.relationship import service as relationship_service
from tests.conftest import auth, make_account, make_space, requires_database, sign_in

pytestmark = [pytest.mark.integration, requires_database]


@pytest.fixture
def couple(session: Session):  # type: ignore[no-untyped-def]
    anna = make_account(session, "Anna")
    ben = make_account(session, "Ben")
    outsider = make_account(session, "Outsider")
    space = make_space(session, anna)
    relationship_service.add_member(session, space.id, ben)
    foreign_space = make_space(session, outsider)
    second_anna_space = make_space(session, anna)
    session.flush()
    return {
        "anna": anna,
        "ben": ben,
        "outsider": outsider,
        "space": space,
        "foreign_space": foreign_space,
        "second_anna_space": second_anna_space,
        "token_a": sign_in(session, anna),
        "token_b": sign_in(session, ben),
        "token_outsider": sign_in(session, outsider),
    }


def _preferences(client, space_id, token):  # type: ignore[no-untyped-def]
    return client.get(
        f"/api/v1/spaces/{space_id}/dashboard/preferences",
        headers=auth(token),
    )


def _set_limit(client, space_id, token, item_limit):  # type: ignore[no-untyped-def]
    return client.patch(
        f"/api/v1/spaces/{space_id}/dashboard/preferences/{DashboardModuleKey.UPCOMING.value}",
        json={"itemLimit": item_limit},
        headers=auth(token),
    )


def test_missing_override_returns_effective_default_without_creating_row(
    client,
    session: Session,
    couple,
) -> None:  # type: ignore[no-untyped-def]
    response = _preferences(client, couple["space"].id, couple["token_a"])

    assert response.status_code == 200, response.text
    assert response.headers["cache-control"] == "private, no-store"
    assert response.json() == {
        "items": [{"moduleKey": "upcoming", "itemLimit": 2}],
    }
    assert session.scalar(select(func.count()).select_from(DashboardModulePreference)) == 0


@pytest.mark.parametrize("item_limit", [1, 2, 3])
def test_each_allowed_limit_persists_and_reloads(
    client,
    session: Session,
    couple,
    item_limit: int,
) -> None:  # type: ignore[no-untyped-def]
    updated = _set_limit(client, couple["space"].id, couple["token_a"], item_limit)

    assert updated.status_code == 200, updated.text
    assert updated.headers["cache-control"] == "private, no-store"
    assert updated.json() == {
        "moduleKey": "upcoming",
        "itemLimit": item_limit,
    }
    session.expire_all()
    reloaded = _preferences(client, couple["space"].id, couple["token_a"])
    assert reloaded.json()["items"] == [{"moduleKey": "upcoming", "itemLimit": item_limit}]


@pytest.mark.parametrize("item_limit", [0, 4, -1, 1.5, None, "many"])
def test_invalid_item_limits_are_rejected_without_persistence(
    client,
    session: Session,
    couple,
    item_limit: object,
) -> None:  # type: ignore[no-untyped-def]
    response = _set_limit(client, couple["space"].id, couple["token_a"], item_limit)

    assert response.status_code == 422
    assert response.json()["code"] == "VALIDATION_FAILED"
    assert session.scalar(select(func.count()).select_from(DashboardModulePreference)) == 0


def test_unknown_module_and_unsupported_facets_fail_closed(
    client,
    session: Session,
    couple,
) -> None:  # type: ignore[no-untyped-def]
    unknown = client.patch(
        f"/api/v1/spaces/{couple['space'].id}/dashboard/preferences/not-a-module",
        json={"itemLimit": 2},
        headers=auth(couple["token_a"]),
    )
    unsupported_facet = client.patch(
        f"/api/v1/spaces/{couple['space'].id}/dashboard/preferences/upcoming",
        json={"itemLimit": 2, "visible": False},
        headers=auth(couple["token_a"]),
    )

    assert unknown.status_code == 404
    assert unknown.json()["code"] == "DASHBOARD_MODULE_NOT_FOUND"
    assert unsupported_facet.status_code == 422
    assert session.scalar(select(func.count()).select_from(DashboardModulePreference)) == 0


def test_preferences_are_independent_per_partner_and_space(
    client,
    couple,
) -> None:  # type: ignore[no-untyped-def]
    assert _set_limit(client, couple["space"].id, couple["token_a"], 1).status_code == 200
    assert (
        _set_limit(
            client,
            couple["second_anna_space"].id,
            couple["token_a"],
            3,
        ).status_code
        == 200
    )

    anna_primary = _preferences(client, couple["space"].id, couple["token_a"])
    ben_primary = _preferences(client, couple["space"].id, couple["token_b"])
    anna_secondary = _preferences(
        client,
        couple["second_anna_space"].id,
        couple["token_a"],
    )

    assert anna_primary.json()["items"][0]["itemLimit"] == 1
    assert ben_primary.json()["items"][0]["itemLimit"] == 2
    assert anna_secondary.json()["items"][0]["itemLimit"] == 3


def test_membership_guard_hides_preferences_from_outsiders(
    client,
    couple,
) -> None:  # type: ignore[no-untyped-def]
    denied_read = _preferences(client, couple["space"].id, couple["token_outsider"])
    denied_write = _set_limit(
        client,
        couple["space"].id,
        couple["token_outsider"],
        1,
    )

    assert denied_read.status_code == 404
    assert denied_write.status_code == 404


def test_repeated_updates_upsert_one_row_and_preserve_inert_visibility(
    client,
    session: Session,
    couple,
) -> None:  # type: ignore[no-untyped-def]
    first = _set_limit(client, couple["space"].id, couple["token_a"], 1)
    second = _set_limit(client, couple["space"].id, couple["token_a"], 3)

    assert first.status_code == 200
    assert second.status_code == 200
    rows = session.scalars(select(DashboardModulePreference)).all()
    assert len(rows) == 1
    assert rows[0].item_limit == 3
    assert rows[0].visible is None


def test_preference_update_does_not_mutate_dashboard_or_planning_data(
    client,
    session: Session,
    couple,
) -> None:  # type: ignore[no-untyped-def]
    plan = Plan(
        space_id=couple["space"].id,
        source_wish_id=None,
        status=PlanStatus.IDEA.value,
        owner_id=couple["anna"].id,
        privacy_class=PrivacyClass.SPACE_SHARED.value,
        payload=PlanPayload(title="Shared plan"),
    )
    session.add(plan)
    session.flush()
    before = client.get(
        f"/api/v1/spaces/{couple['space'].id}/dashboard",
        headers=auth(couple["token_a"]),
    ).json()

    updated = _set_limit(client, couple["space"].id, couple["token_a"], 1)
    after = client.get(
        f"/api/v1/spaces/{couple['space'].id}/dashboard",
        headers=auth(couple["token_a"]),
    ).json()

    assert updated.status_code == 200
    assert after == before
    session.refresh(plan)
    assert plan.payload.title == "Shared plan"
