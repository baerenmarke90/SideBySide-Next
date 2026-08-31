"""Canonical, opt-in demo data for development and visual QA."""

from __future__ import annotations

from datetime import date

from sqlalchemy.orm import Session

from sidebyside.config import Environment
from sidebyside.demo.finalize import ensure_story_structure
from sidebyside.demo.presentation import normalize_demo_content
from sidebyside.demo.reminders import ensure_reminder_examples
from sidebyside.demo.service import DemoSeedResult
from sidebyside.demo.service import create_demo_space as _create_demo_space
from sidebyside.demo.service import reset_demo_space as _reset_demo_space


def create_demo_space(
    session: Session,
    *,
    environment: Environment,
    lea_password: str,
    alex_password: str,
    reference_date: date,
) -> DemoSeedResult:
    """Create the complete canonical demo dataset, including stable M4-C examples."""
    result = _create_demo_space(
        session,
        environment=environment,
        lea_password=lea_password,
        alex_password=alex_password,
        reference_date=reference_date,
    )
    normalize_demo_content(session, result)
    if result.created:
        ensure_story_structure(session, result)
    ensure_reminder_examples(session, result, reference_date=reference_date)
    return result


def reset_demo_space(
    session: Session,
    *,
    environment: Environment,
    reference_date: date,
) -> DemoSeedResult:
    """Reset the complete canonical demo dataset."""
    result = _reset_demo_space(
        session,
        environment=environment,
        reference_date=reference_date,
    )
    normalize_demo_content(session, result)
    ensure_story_structure(session, result)
    ensure_reminder_examples(session, result, reference_date=reference_date)
    return result


__all__ = ["DemoSeedResult", "create_demo_space", "reset_demo_space"]
