"""Unit coverage for the deployment-time demo bootstrap command."""

from __future__ import annotations

import sys
from collections.abc import Iterator
from contextlib import contextmanager
from datetime import date
from types import SimpleNamespace
from typing import Any
from uuid import uuid4

from scripts import demo_space
from sidebyside.config import Environment
from sidebyside.demo.service import DemoSeedResult


def test_ensure_skips_non_demo_deployment(monkeypatch: Any) -> None:
    monkeypatch.setattr(
        demo_space,
        "get_settings",
        lambda: SimpleNamespace(environment=Environment.DEVELOPMENT, demo_mode=False),
    )
    monkeypatch.setattr(sys, "argv", ["demo_space", "ensure"])

    def fail_if_database_is_opened() -> None:
        raise AssertionError("ensure must not open the database outside demo mode")

    monkeypatch.setattr(demo_space, "unit_of_work", fail_if_database_is_opened)

    assert demo_space.main() == 0


def test_ensure_bootstraps_demo_with_ephemeral_passwords(monkeypatch: Any) -> None:
    reference_date = date(2026, 8, 24)
    session = object()
    captured: dict[str, object] = {}

    monkeypatch.setattr(
        demo_space,
        "get_settings",
        lambda: SimpleNamespace(environment=Environment.DEMO, demo_mode=True),
    )
    monkeypatch.delenv(demo_space.LEA_PASSWORD_ENV, raising=False)
    monkeypatch.delenv(demo_space.ALEX_PASSWORD_ENV, raising=False)
    monkeypatch.setattr(
        sys,
        "argv",
        ["demo_space", "ensure", "--reference-date", reference_date.isoformat()],
    )

    @contextmanager
    def fake_unit_of_work() -> Iterator[object]:
        yield session

    def fake_create_demo_space(
        received_session: object,
        *,
        environment: Environment,
        lea_password: str,
        alex_password: str,
        reference_date: date,
    ) -> DemoSeedResult:
        captured.update(
            session=received_session,
            environment=environment,
            lea_password=lea_password,
            alex_password=alex_password,
            reference_date=reference_date,
        )
        return DemoSeedResult(
            lea_id=uuid4(),
            alex_id=uuid4(),
            space_id=uuid4(),
            reference_date=reference_date,
            created=True,
        )

    monkeypatch.setattr(demo_space, "unit_of_work", fake_unit_of_work)
    monkeypatch.setattr(demo_space, "create_demo_space", fake_create_demo_space)

    assert demo_space.main() == 0
    assert captured["session"] is session
    assert captured["environment"] is Environment.DEMO
    assert captured["reference_date"] == reference_date

    lea_password = captured["lea_password"]
    alex_password = captured["alex_password"]
    assert isinstance(lea_password, str)
    assert isinstance(alex_password, str)
    assert len(lea_password) >= 32
    assert len(alex_password) >= 32
    assert lea_password != alex_password
