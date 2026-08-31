"""Public demo persona selection stays isolated behind explicit demo mode."""

from __future__ import annotations

from datetime import date

import pytest

from sidebyside.api.v1 import demo as demo_api
from sidebyside.config import Environment, Settings
from sidebyside.demo.service import LEA_NAME, create_demo_space
from tests.conftest import requires_database

pytestmark = [pytest.mark.integration, requires_database]

REFERENCE_DATE = date(2026, 8, 24)
DEMO_PASSWORD = "canonical-demo-entry-test-password"


def _seed(session, *, environment: Environment = Environment.TEST):  # type: ignore[no-untyped-def]
    return create_demo_space(
        session,
        environment=environment,
        lea_password=DEMO_PASSWORD,
        alex_password=DEMO_PASSWORD,
        reference_date=REFERENCE_DATE,
    )


def test_demo_environment_can_create_canonical_seed(session) -> None:  # type: ignore[no-untyped-def]
    result = _seed(session, environment=Environment.DEMO)

    assert result.created is True


def test_demo_entry_is_hidden_when_demo_mode_is_disabled(
    client,
    session,
    monkeypatch: pytest.MonkeyPatch,
) -> None:  # type: ignore[no-untyped-def]
    _seed(session)
    monkeypatch.setattr(demo_api, "get_settings", lambda: Settings())

    response = client.post("/api/v1/demo/entry", json={"persona": "LEA"})

    assert response.status_code == 404


def test_demo_entry_issues_one_time_proof_for_selected_persona(
    client,
    session,
    monkeypatch: pytest.MonkeyPatch,
) -> None:  # type: ignore[no-untyped-def]
    _seed(session)
    monkeypatch.setattr(
        demo_api,
        "get_settings",
        lambda: Settings.model_validate({"demo_mode": True}),
    )

    entry = client.post("/api/v1/demo/entry", json={"persona": "LEA"})

    assert entry.status_code == 200
    assert entry.headers["cache-control"] == "no-store"
    token = entry.json()["token"]
    assert token

    consumed = client.post(
        "/api/v1/auth/magic-link/consume",
        json={"token": token, "deviceName": "Demo test", "platform": "web"},
    )
    assert consumed.status_code == 201
    assert consumed.json()["account"]["displayName"] == LEA_NAME

    repeated = client.post(
        "/api/v1/auth/magic-link/consume",
        json={"token": token, "deviceName": "Demo test", "platform": "web"},
    )
    assert repeated.status_code == 422


def test_demo_entry_is_not_published_in_product_openapi(client) -> None:  # type: ignore[no-untyped-def]
    document = client.get("/openapi.json").json()

    assert "/api/v1/demo/entry" not in document["paths"]
