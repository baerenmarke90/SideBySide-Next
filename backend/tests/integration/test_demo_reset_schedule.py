"""Reset timer uses the existing durable job queue and explicit demo config."""

from __future__ import annotations

from datetime import timedelta

import pytest

from sidebyside.config import Settings
from sidebyside.demo import reset as demo_reset
from sidebyside.jobs.models import JobStatus
from tests.conftest import requires_database

pytestmark = [pytest.mark.integration, requires_database]


def test_reset_timer_is_disabled_by_default(session) -> None:  # type: ignore[no-untyped-def]
    assert demo_reset.ensure_scheduled(session) is None


def test_reset_timer_schedules_exactly_one_pending_job(
    session,
    monkeypatch: pytest.MonkeyPatch,
) -> None:  # type: ignore[no-untyped-def]
    settings = Settings.model_validate(
        {
            "demo_mode": True,
            "demo_mode_reset_timer": True,
            "demo_mode_reset_interval": timedelta(minutes=30),
        }
    )
    monkeypatch.setattr(demo_reset, "get_settings", lambda: settings)

    first = demo_reset.ensure_scheduled(session)
    second = demo_reset.ensure_scheduled(session)

    assert first is not None
    assert first.kind == demo_reset.DEMO_RESET_JOB
    assert first.status == JobStatus.PENDING.value
    assert second is None
