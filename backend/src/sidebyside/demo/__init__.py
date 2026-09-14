"""Canonical, opt-in demo data for development and visual QA."""

from __future__ import annotations

from datetime import date

from sqlalchemy.orm import Session

from sidebyside.config import Environment
from sidebyside.core import clock
from sidebyside.demo.finalize import ensure_story_structure
from sidebyside.demo.presentation import normalize_demo_content
from sidebyside.demo.reminders import ensure_reminder_examples
from sidebyside.demo.service import DemoSeedResult
from sidebyside.demo.service import create_demo_space as _create_demo_space
from sidebyside.demo.service import reset_demo_space as _reset_demo_space
from sidebyside.demo.wish_detective import ensure_wish_detective_examples
from sidebyside.entitlements import service as entitlement_service
from sidebyside.entitlements.models import (
    Capability,
    EntitlementSourceType,
    EntitlementStatus,
    EntitlementTier,
)

_DEMO_GAMES_ENTITLEMENT_REFERENCE = "canonical-demo-games"


def _ensure_games_entitlement(session: Session, result: DemoSeedResult) -> None:
    """Keep the canonical demo playable through the normalized Premium boundary."""
    instant = clock.now()
    entitlement_service.record_grant(
        session,
        space_id=result.space_id,
        account_id=result.lea_id,
        source_type=EntitlementSourceType.TEST_FIXTURE,
        status=EntitlementStatus.ACTIVE,
        tier=EntitlementTier.PREMIUM,
        effective_from=instant,
        effective_until=None,
        external_reference=_DEMO_GAMES_ENTITLEMENT_REFERENCE,
        source_event_at=instant,
        capabilities=[Capability.GAMES_COUPLE.value],
        metadata={"fixture": "canonical_demo_games"},
    )


def _ensure_product_examples(
    session: Session,
    result: DemoSeedResult,
    *,
    reference_date: date,
) -> None:
    normalize_demo_content(session, result)
    if result.created:
        ensure_story_structure(session, result)
    ensure_reminder_examples(session, result, reference_date=reference_date)
    ensure_wish_detective_examples(
        session,
        space_id=result.space_id,
        lea_id=result.lea_id,
        alex_id=result.alex_id,
    )
    _ensure_games_entitlement(session, result)


def create_demo_space(
    session: Session,
    *,
    environment: Environment,
    lea_password: str,
    alex_password: str,
    reference_date: date,
) -> DemoSeedResult:
    """Create the complete canonical demo dataset, including stable product examples."""
    result = _create_demo_space(
        session,
        environment=environment,
        lea_password=lea_password,
        alex_password=alex_password,
        reference_date=reference_date,
    )
    _ensure_product_examples(session, result, reference_date=reference_date)
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
    _ensure_product_examples(session, result, reference_date=reference_date)
    return result


__all__ = ["DemoSeedResult", "create_demo_space", "reset_demo_space"]
