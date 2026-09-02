"""Unit tests for the centralized entitlement and capability service."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from uuid import uuid4

from sidebyside.entitlements.models import (
    Capability,
    EntitlementGrant,
    EntitlementSourceType,
    EntitlementStatus,
    EntitlementTier,
)
from sidebyside.entitlements.service import (
    ALL_PREMIUM_CAPABILITIES,
    evaluate_grant_validity,
    get_effective_space_entitlement,
    has_capability,
    record_grant,
    revoke_grant,
)


class FakeSession:
    def __init__(self, grants: list[EntitlementGrant] | None = None) -> None:
        self._grants: list[EntitlementGrant] = grants or []

    def execute(self, statement) -> object:  # type: ignore[no-untyped-def]
        class Result:
            def __init__(self, items: list[EntitlementGrant]) -> None:
                self._items = items

            def scalars(self) -> Result:
                return self

            def all(self) -> list[EntitlementGrant]:
                return self._items

            def first(self) -> EntitlementGrant | None:
                return self._items[0] if self._items else None

        return Result(self._grants)

    def add(self, entity: EntitlementGrant) -> None:
        self._grants.append(entity)

    def get(self, entity_class: type, entity_id: object) -> EntitlementGrant | None:
        for grant in self._grants:
            if grant.id == entity_id:
                return grant
        return None

    def flush(self) -> None:
        pass


def test_free_space_defaults_to_expired_with_no_capabilities() -> None:
    space_id = uuid4()
    session = FakeSession([])
    effective = get_effective_space_entitlement(session, space_id)

    assert effective.space_id == space_id
    assert effective.tier == EntitlementTier.FREE
    assert effective.status == EntitlementStatus.EXPIRED
    assert effective.effective_until is None
    assert effective.is_in_grace_period is False
    assert effective.capabilities == []
    assert not has_capability(session, space_id, Capability.CHAPTER_RICH_PRESENTATION)


def test_active_premium_grant_provides_all_premium_capabilities() -> None:
    space_id = uuid4()
    now = datetime(2026, 9, 1, 12, 0, 0, tzinfo=UTC)
    grant = EntitlementGrant(
        id=uuid4(),
        space_id=space_id,
        source_type=EntitlementSourceType.GOOGLE_PLAY.value,
        status=EntitlementStatus.ACTIVE.value,
        tier=EntitlementTier.PREMIUM.value,
        effective_from=now - timedelta(days=1),
        effective_until=now + timedelta(days=30),
        capabilities=None,
    )
    session = FakeSession([grant])
    effective = get_effective_space_entitlement(session, space_id, at=now)

    assert effective.tier == EntitlementTier.PREMIUM
    assert effective.status == EntitlementStatus.ACTIVE
    assert effective.is_in_grace_period is False
    assert set(effective.capabilities) == set(ALL_PREMIUM_CAPABILITIES)
    assert has_capability(session, space_id, Capability.RECAP_PDF_YEARBOOK, at=now)


def test_14_day_grace_period_keeps_capabilities_active() -> None:
    space_id = uuid4()
    effective_until = datetime(2026, 9, 1, 0, 0, 0, tzinfo=UTC)
    grant = EntitlementGrant(
        id=uuid4(),
        space_id=space_id,
        source_type=EntitlementSourceType.CLOUD_STRIPE.value,
        status=EntitlementStatus.ACTIVE.value,
        tier=EntitlementTier.PREMIUM.value,
        effective_from=effective_until - timedelta(days=30),
        effective_until=effective_until,
        capabilities=None,
    )
    session = FakeSession([grant])

    # Day 5 after expiry: in grace period, capabilities active
    day_5 = effective_until + timedelta(days=5)
    effective_5 = get_effective_space_entitlement(session, space_id, at=day_5)
    assert effective_5.tier == EntitlementTier.PREMIUM
    assert effective_5.status == EntitlementStatus.GRACE_PERIOD
    assert effective_5.is_in_grace_period is True
    assert has_capability(session, space_id, Capability.STORAGE_CLOUD_QUOTA_50GB, at=day_5)

    # Day 14 after expiry: last day of grace period, still active
    day_14 = effective_until + timedelta(days=14)
    effective_14 = get_effective_space_entitlement(session, space_id, at=day_14)
    assert effective_14.is_in_grace_period is True
    assert has_capability(session, space_id, Capability.STORAGE_CLOUD_QUOTA_50GB, at=day_14)

    # Day 15 after expiry: grace period elapsed, transitions to Free/Expired
    day_15 = effective_until + timedelta(days=15)
    effective_15 = get_effective_space_entitlement(session, space_id, at=day_15)
    assert effective_15.tier == EntitlementTier.FREE
    assert effective_15.status == EntitlementStatus.EXPIRED
    assert effective_15.is_in_grace_period is False
    assert not has_capability(session, space_id, Capability.STORAGE_CLOUD_QUOTA_50GB, at=day_15)


def test_grandfathered_and_trial_grants() -> None:
    space_id = uuid4()
    now = datetime(2026, 9, 1, 12, 0, 0, tzinfo=UTC)
    grant_trial = EntitlementGrant(
        id=uuid4(),
        space_id=space_id,
        source_type=EntitlementSourceType.ADMIN_GRANT.value,
        status=EntitlementStatus.TRIAL.value,
        tier=EntitlementTier.PREMIUM.value,
        effective_from=now - timedelta(days=5),
        effective_until=now + timedelta(days=9),
    )
    session_trial = FakeSession([grant_trial])
    effective_trial = get_effective_space_entitlement(session_trial, space_id, at=now)
    assert effective_trial.tier == EntitlementTier.PREMIUM
    assert effective_trial.status == EntitlementStatus.TRIAL

    grant_gf = EntitlementGrant(
        id=uuid4(),
        space_id=space_id,
        source_type=EntitlementSourceType.ADMIN_GRANT.value,
        status=EntitlementStatus.GRANDFATHERED.value,
        tier=EntitlementTier.PREMIUM.value,
        effective_from=now - timedelta(days=100),
        effective_until=None,
    )
    session_gf = FakeSession([grant_gf])
    effective_gf = get_effective_space_entitlement(session_gf, space_id, at=now)
    assert effective_gf.tier == EntitlementTier.PREMIUM
    assert effective_gf.status == EntitlementStatus.GRANDFATHERED


def test_revoked_grant_is_not_effective() -> None:
    space_id = uuid4()
    now = datetime(2026, 9, 1, 12, 0, 0, tzinfo=UTC)
    grant = EntitlementGrant(
        id=uuid4(),
        space_id=space_id,
        source_type=EntitlementSourceType.GOOGLE_PLAY.value,
        status=EntitlementStatus.REVOKED.value,
        tier=EntitlementTier.PREMIUM.value,
        effective_from=now - timedelta(days=10),
        effective_until=now + timedelta(days=20),
    )
    session = FakeSession([grant])
    effective = get_effective_space_entitlement(session, space_id, at=now)
    assert effective.tier == EntitlementTier.FREE
    assert effective.status == EntitlementStatus.REVOKED
    assert effective.capabilities == []


def test_multiple_grants_precedence() -> None:
    space_id = uuid4()
    now = datetime(2026, 9, 1, 12, 0, 0, tzinfo=UTC)
    expired_grant = EntitlementGrant(
        id=uuid4(),
        space_id=space_id,
        source_type=EntitlementSourceType.GOOGLE_PLAY.value,
        status=EntitlementStatus.EXPIRED.value,
        tier=EntitlementTier.PREMIUM.value,
        effective_from=now - timedelta(days=60),
        effective_until=now - timedelta(days=30),
    )
    active_grant = EntitlementGrant(
        id=uuid4(),
        space_id=space_id,
        source_type=EntitlementSourceType.SELF_HOSTED_KEY.value,
        status=EntitlementStatus.ACTIVE.value,
        tier=EntitlementTier.PREMIUM.value,
        effective_from=now - timedelta(days=2),
        effective_until=now + timedelta(days=365),
    )
    session = FakeSession([expired_grant, active_grant])
    effective = get_effective_space_entitlement(session, space_id, at=now)
    assert effective.tier == EntitlementTier.PREMIUM
    assert effective.status == EntitlementStatus.ACTIVE


def test_grant_validity_future_grant() -> None:
    now = datetime(2026, 9, 1, 12, 0, 0, tzinfo=UTC)
    future_grant = EntitlementGrant(
        id=uuid4(),
        space_id=uuid4(),
        source_type=EntitlementSourceType.ADMIN_GRANT.value,
        status=EntitlementStatus.ACTIVE.value,
        tier=EntitlementTier.PREMIUM.value,
        effective_from=now + timedelta(days=5),
        effective_until=now + timedelta(days=35),
    )
    is_eff, in_grace, status = evaluate_grant_validity(future_grant, now)
    assert not is_eff
    assert not in_grace
    assert status == EntitlementStatus.ACTIVE


def test_record_and_revoke_grant() -> None:
    space_id = uuid4()
    account_id = uuid4()
    session = FakeSession([])
    now = datetime(2026, 9, 1, 12, 0, 0, tzinfo=UTC)

    grant = record_grant(
        session,
        space_id=space_id,
        account_id=account_id,
        source_type=EntitlementSourceType.GOOGLE_PLAY,
        status=EntitlementStatus.ACTIVE,
        tier=EntitlementTier.PREMIUM,
        effective_from=now,
        effective_until=now + timedelta(days=30),
        external_reference="order-12345",
    )

    assert grant.space_id == space_id
    assert grant.account_id == account_id
    assert grant.external_reference == "order-12345"
    assert grant.status == EntitlementStatus.ACTIVE.value

    # Idempotent update
    updated = record_grant(
        session,
        space_id=space_id,
        source_type=EntitlementSourceType.GOOGLE_PLAY,
        status=EntitlementStatus.ACTIVE,
        tier=EntitlementTier.PREMIUM,
        effective_from=now,
        effective_until=now + timedelta(days=60),
        external_reference="order-12345",
    )
    assert updated.id == grant.id
    assert updated.effective_until == now + timedelta(days=60)

    # Revoke
    revoked = revoke_grant(session, grant.id, reason="chargeback")
    assert revoked is not None
    assert revoked.status == EntitlementStatus.REVOKED.value
    assert revoked.metadata_["revocation_reason"] == "chargeback"
