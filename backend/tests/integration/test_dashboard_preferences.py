"""Tenant and persistence acceptance tests for Dashboard module preferences."""

from __future__ import annotations

import pytest
from sqlalchemy.orm import Session

from sidebyside.dashboard.preferences import DashboardModuleKey
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
    session.flush()
    return {
        "anna": anna,
        "ben": ben,
        "outsider": outsider,
        "space": space,
        "foreign_space": foreign_space,
        "token_a": sign_in(session, anna),
        "token_b": sign_in(session, ben),
        "token_outsider": sign_in(session, outsider),
    }


def _preferences(client, space_id, token):  # type: ignore[no-untyped-def]
    return client.get(
        f"/api/v1/spaces/{space_id}/dashboard/preferences",
        headers=auth(token),
    )


def _set_visibility(client, space_id, token, *, visible: bool):  # type: ignore[no-untyped-def]
    key = DashboardModuleKey.SHARED_STORY_SUMMARY.value
    return client.put(
        f"/api/v1/spaces/{space_id}/dashboard/preferences/{key}",
        json={"visible": visible},
        headers=auth(token),
    )


def test_dashboard_preference_defaults_enabled_and_is_private_per_partner(
    client,
    couple,
) -> None:  # type: ignore[no-untyped-def]
    initial_a = _preferences(client, couple["space"].id, couple["token_a"])
    initial_b = _preferences(client, couple["space"].id, couple["token_b"])
    assert initial_a.status_code == 200, initial_a.text
    assert initial_b.status_code == 200, initial_b.text
    expected_default = {"items": [{"moduleKey": "SHARED_STORY_SUMMARY", "visible": True}]}
    assert initial_a.json() == expected_default
    assert initial_b.json() == expected_default

    hidden = _set_visibility(
        client,
        couple["space"].id,
        couple["token_a"],
        visible=False,
    )
    assert hidden.status_code == 200, hidden.text
    assert hidden.json() == {"moduleKey": "SHARED_STORY_SUMMARY", "visible": False}

    reloaded_a = _preferences(client, couple["space"].id, couple["token_a"])
    unaffected_b = _preferences(client, couple["space"].id, couple["token_b"])
    assert reloaded_a.json()["items"][0]["visible"] is False
    assert unaffected_b.json()["items"][0]["visible"] is True

    shown = _set_visibility(
        client,
        couple["space"].id,
        couple["token_a"],
        visible=True,
    )
    assert shown.status_code == 200
    assert (
        _preferences(client, couple["space"].id, couple["token_a"]).json()["items"][0]["visible"]
        is True
    )


def test_dashboard_preference_is_tenant_guarded_and_unknown_keys_fail_closed(
    client,
    couple,
) -> None:  # type: ignore[no-untyped-def]
    denied = _preferences(client, couple["space"].id, couple["token_outsider"])
    assert denied.status_code == 404

    unknown = client.put(
        f"/api/v1/spaces/{couple['space'].id}/dashboard/preferences/NOT_A_MODULE",
        json={"visible": False},
        headers=auth(couple["token_a"]),
    )
    assert unknown.status_code == 422

    foreign_default = _preferences(
        client,
        couple["foreign_space"].id,
        couple["token_outsider"],
    )
    assert foreign_default.status_code == 200
    assert foreign_default.json()["items"][0]["visible"] is True
