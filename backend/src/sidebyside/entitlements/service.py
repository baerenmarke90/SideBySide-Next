"""Centralized entitlement and capability evaluation service."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from sidebyside.core import clock
from sidebyside.entitlements.models import (
    Capability,
    EntitlementGrant,
    EntitlementSourceType,
    EntitlementStatus,
    EntitlementTier,
)

GRACE_PERIOD_DAYS = 14
ALL_PREMIUM_CAPABILITIES = [c.value for c in Capability]


@dataclass(frozen=True)
class EffectiveEntitlement:
    """Calculated commercial entitlement state for a Space."""

    space_id: UUID
    tier: EntitlementTier
    status: EntitlementStatus
    effective_until: datetime | None
    is_in_grace_period: bool
    capabilities: list[str] = field(default_factory=list)


def evaluate_grant_validity(
    grant: EntitlementGrant,
    at: datetime,
) -> tuple[bool, bool, EntitlementStatus]:
    """Evaluate whether a single grant is currently active or in grace period.

    Returns ``(is_effective, is_in_grace_period, effective_status)``.
    """
    if grant.status == EntitlementStatus.REVOKED.value:
        return False, False, EntitlementStatus.REVOKED

    if grant.status == EntitlementStatus.EXPIRED.value:
        return False, False, EntitlementStatus.EXPIRED

    if grant.effective_from > at:
        return False, False, EntitlementStatus(grant.status)

    if grant.status == EntitlementStatus.GRANDFATHERED.value:
        if grant.effective_until is None or at <= grant.effective_until:
            return True, False, EntitlementStatus.GRANDFATHERED
        return False, False, EntitlementStatus.EXPIRED

    if grant.status == EntitlementStatus.TRIAL.value:
        if grant.effective_until is None or at <= grant.effective_until:
            return True, False, EntitlementStatus.TRIAL
        return False, False, EntitlementStatus.EXPIRED

    if grant.status == EntitlementStatus.ACTIVE.value:
        if grant.effective_until is None or at <= grant.effective_until:
            return True, False, EntitlementStatus.ACTIVE
        grace_limit = grant.effective_until + timedelta(days=GRACE_PERIOD_DAYS)
        if at <= grace_limit:
            return True, True, EntitlementStatus.GRACE_PERIOD
        return False, False, EntitlementStatus.EXPIRED

    if grant.status == EntitlementStatus.GRACE_PERIOD.value:
        if grant.effective_until is None:
            return True, True, EntitlementStatus.GRACE_PERIOD
        grace_limit = grant.effective_until + timedelta(days=GRACE_PERIOD_DAYS)
        if at <= grace_limit:
            return True, True, EntitlementStatus.GRACE_PERIOD
        return False, False, EntitlementStatus.EXPIRED

    return False, False, EntitlementStatus.EXPIRED


def get_effective_space_entitlement(
    session: Session,
    space_id: UUID,
    at: datetime | None = None,
) -> EffectiveEntitlement:
    """Resolve the effective entitlement state for the given Space.

    Precedence order for multiple grants on the same space:
    1. An active Premium grant (ACTIVE, GRANDFATHERED, TRIAL)
    2. A Premium grant in 14-day GRACE_PERIOD
    3. Fallback to Free/Core baseline (EXPIRED or no grants)
    """
    current_time = clock.ensure_utc(at) if at is not None else clock.now()

    grants = (
        session.execute(
            select(EntitlementGrant)
            .where(EntitlementGrant.space_id == space_id)
            .order_by(EntitlementGrant.created_at.desc())
        )
        .scalars()
        .all()
    )

    if not grants:
        return EffectiveEntitlement(
            space_id=space_id,
            tier=EntitlementTier.FREE,
            status=EntitlementStatus.EXPIRED,
            effective_until=None,
            is_in_grace_period=False,
            capabilities=[],
        )

    # First check for full active/grandfathered/trial Premium grant
    for grant in grants:
        if grant.tier != EntitlementTier.PREMIUM.value:
            continue
        is_effective, in_grace, effective_status = evaluate_grant_validity(grant, current_time)
        if is_effective and not in_grace:
            capabilities = (
                list(grant.capabilities)
                if grant.capabilities is not None
                else list(ALL_PREMIUM_CAPABILITIES)
            )
            return EffectiveEntitlement(
                space_id=space_id,
                tier=EntitlementTier.PREMIUM,
                status=effective_status,
                effective_until=grant.effective_until,
                is_in_grace_period=False,
                capabilities=capabilities,
            )

    # Next check for Premium grant in Grace Period
    for grant in grants:
        if grant.tier != EntitlementTier.PREMIUM.value:
            continue
        is_effective, in_grace, effective_status = evaluate_grant_validity(grant, current_time)
        if is_effective and in_grace:
            capabilities = (
                list(grant.capabilities)
                if grant.capabilities is not None
                else list(ALL_PREMIUM_CAPABILITIES)
            )
            return EffectiveEntitlement(
                space_id=space_id,
                tier=EntitlementTier.PREMIUM,
                status=EntitlementStatus.GRACE_PERIOD,
                effective_until=grant.effective_until,
                is_in_grace_period=True,
                capabilities=capabilities,
            )

    # No active or grace grant found; return latest status
    latest_grant = grants[0]
    latest_status = (
        EntitlementStatus(latest_grant.status)
        if latest_grant.status == EntitlementStatus.REVOKED.value
        else EntitlementStatus.EXPIRED
    )
    return EffectiveEntitlement(
        space_id=space_id,
        tier=EntitlementTier.FREE,
        status=latest_status,
        effective_until=latest_grant.effective_until,
        is_in_grace_period=False,
        capabilities=[],
    )


def has_capability(
    session: Session,
    space_id: UUID,
    capability: str | Capability,
    at: datetime | None = None,
) -> bool:
    """Check if the given Space holds the specified capability."""
    cap_str = capability.value if isinstance(capability, Capability) else str(capability)
    entitlement = get_effective_space_entitlement(session, space_id, at=at)
    return cap_str in entitlement.capabilities


def record_grant(
    session: Session,
    *,
    space_id: UUID,
    source_type: EntitlementSourceType | str,
    status: EntitlementStatus | str,
    tier: EntitlementTier | str = EntitlementTier.PREMIUM,
    effective_from: datetime,
    effective_until: datetime | None = None,
    account_id: UUID | None = None,
    external_reference: str | None = None,
    capabilities: list[str] | None = None,
    metadata: dict[str, Any] | None = None,
) -> EntitlementGrant:
    """Idempotently record or update an entitlement grant."""
    source_str = (
        source_type.value if isinstance(source_type, EntitlementSourceType) else str(source_type)
    )
    status_str = status.value if isinstance(status, EntitlementStatus) else str(status)
    tier_str = tier.value if isinstance(tier, EntitlementTier) else str(tier)

    existing: EntitlementGrant | None = None
    if external_reference is not None:
        existing = (
            session.execute(
                select(EntitlementGrant).where(
                    EntitlementGrant.space_id == space_id,
                    EntitlementGrant.source_type == source_str,
                    EntitlementGrant.external_reference == external_reference,
                )
            )
            .scalars()
            .first()
        )

    if existing is not None:
        existing.status = status_str
        existing.tier = tier_str
        existing.effective_from = effective_from
        existing.effective_until = effective_until
        existing.capabilities = capabilities
        if account_id is not None:
            existing.account_id = account_id
        if metadata is not None:
            existing.metadata_ = metadata
        session.flush()
        return existing

    grant = EntitlementGrant(
        space_id=space_id,
        account_id=account_id,
        source_type=source_str,
        external_reference=external_reference,
        status=status_str,
        tier=tier_str,
        effective_from=effective_from,
        effective_until=effective_until,
        capabilities=capabilities,
        metadata_=metadata or {},
    )
    session.add(grant)
    session.flush()
    return grant


def revoke_grant(
    session: Session,
    grant_id: UUID,
    *,
    reason: str = "revoked",
) -> EntitlementGrant | None:
    """Revoke an active grant (e.g. after a refund or chargeback)."""
    grant = session.get(EntitlementGrant, grant_id)
    if grant is None:
        return None

    grant.status = EntitlementStatus.REVOKED.value
    meta = dict(grant.metadata_ or {})
    meta["revocation_reason"] = reason
    meta["revoked_at"] = clock.now().isoformat()
    grant.metadata_ = meta
    session.flush()
    return grant
