"""Integration tests for the commercial entitlement API and couple-scoping."""

from __future__ import annotations

from datetime import timedelta

import pytest

from sidebyside.api.deps import ensure_capability
from sidebyside.core.clock import now
from sidebyside.core.errors import PremiumEntitlementRequiredError
from sidebyside.entitlements import service as entitlement_service
from sidebyside.entitlements.models import (
    Capability,
    EntitlementSourceType,
    EntitlementStatus,
    EntitlementTier,
)
from sidebyside.entitlements.service import ALL_PREMIUM_CAPABILITIES
from sidebyside.relationship.models import Membership, MembershipStatus
from tests.conftest import (
    auth,
    make_account,
    make_space,
    requires_database,
    sign_in,
)

pytestmark = [pytest.mark.integration, requires_database]


def test_entitlements_endpoint_requires_auth(client) -> None:  # type: ignore[no-untyped-def]
    response = client.get("/api/v1/spaces/01a05cf9-64c9-7273-8bfe-6252d8cefbbb/entitlements")
    assert response.status_code == 401


def test_entitlements_endpoint_enforces_tenant_isolation(client, session) -> None:  # type: ignore[no-untyped-def]
    anna = make_account(session, "Anna")
    make_space(session, anna)
    anna_token = sign_in(session, anna)

    other_account = make_account(session, "Stranger")
    other_space = make_space(session, other_account)

    # Anna cannot inspect the entitlements of other_space
    response = client.get(
        f"/api/v1/spaces/{other_space.id}/entitlements",
        headers=auth(anna_token),
    )
    assert response.status_code == 404
    assert response.json()["code"] == "SPACE_NOT_FOUND"


def test_default_space_is_free(client, session) -> None:  # type: ignore[no-untyped-def]
    anna = make_account(session, "Anna")
    space = make_space(session, anna)
    token = sign_in(session, anna)

    response = client.get(f"/api/v1/spaces/{space.id}/entitlements", headers=auth(token))
    assert response.status_code == 200
    data = response.json()
    assert data["spaceId"] == str(space.id)
    assert data["tier"] == "FREE"
    assert data["status"] == "EXPIRED"
    assert data["effectiveUntil"] is None
    assert data["isInGracePeriod"] is False
    assert data["capabilities"] == []


def test_couple_level_entitlement_shared_between_partners_without_cross_space_leak(
    client,
    session,
) -> None:  # type: ignore[no-untyped-def]
    anna = make_account(session, "Anna")
    ben = make_account(session, "Ben")
    shared_space = make_space(session, anna)

    # Ben joins the shared space
    session.add(
        Membership(
            account_id=ben.id,
            space_id=shared_space.id,
            status=MembershipStatus.ACTIVE.value,
        )
    )

    # Anna also has a separate personal/second space
    anna_solo_space = make_space(session, anna)
    session.flush()

    # Anna purchases a Premium subscription for the shared space
    current_time = now()
    entitlement_service.record_grant(
        session,
        space_id=shared_space.id,
        account_id=anna.id,
        source_type=EntitlementSourceType.GOOGLE_PLAY,
        status=EntitlementStatus.ACTIVE,
        tier=EntitlementTier.PREMIUM,
        effective_from=current_time,
        effective_until=current_time + timedelta(days=365),
    )
    session.flush()

    # Ben reads the shared space entitlements -> inherits Premium
    ben_token = sign_in(session, ben)
    ben_response = client.get(
        f"/api/v1/spaces/{shared_space.id}/entitlements",
        headers=auth(ben_token),
    )
    assert ben_response.status_code == 200
    ben_data = ben_response.json()
    assert ben_data["tier"] == "PREMIUM"
    assert ben_data["status"] == "ACTIVE"
    assert set(ben_data["capabilities"]) == set(ALL_PREMIUM_CAPABILITIES)

    # Anna queries her solo space -> stays Free (no leakage across spaces)
    anna_token = sign_in(session, anna)
    solo_response = client.get(
        f"/api/v1/spaces/{anna_solo_space.id}/entitlements",
        headers=auth(anna_token),
    )
    assert solo_response.status_code == 200
    assert solo_response.json()["tier"] == "FREE"
    assert solo_response.json()["status"] == "EXPIRED"


def test_capability_guard_and_non_destructive_downgrade(client, session) -> None:  # type: ignore[no-untyped-def]
    anna = make_account(session, "Anna")
    space = make_space(session, anna)
    token = sign_in(session, anna)
    current_time = now()

    # 1. Initially space is Free -> guarded capability raises error
    with pytest.raises(PremiumEntitlementRequiredError) as err:
        ensure_capability(session, space.id, Capability.RECAP_PDF_YEARBOOK)
    assert err.value.code == "PREMIUM_ENTITLEMENT_REQUIRED"

    # 2. Grant Premium -> guarded capability succeeds
    grant = entitlement_service.record_grant(
        session,
        space_id=space.id,
        account_id=anna.id,
        source_type=EntitlementSourceType.CLOUD_STRIPE,
        status=EntitlementStatus.ACTIVE,
        tier=EntitlementTier.PREMIUM,
        effective_from=current_time - timedelta(days=5),
        effective_until=current_time + timedelta(days=30),
    )
    session.flush()

    ensure_capability(session, space.id, Capability.RECAP_PDF_YEARBOOK)

    # Create memory while Premium is active
    post_res = client.post(
        f"/api/v1/spaces/{space.id}/memories",
        json={"title": "Our Paris Trip", "happenedOn": str(current_time.date())},
        headers=auth(token),
    )
    assert post_res.status_code == 201
    memory_id = post_res.json()["id"]

    # 3. Grant expires / transitions to EXPIRED
    grant.status = EntitlementStatus.EXPIRED.value
    grant.effective_until = current_time - timedelta(days=20)
    session.flush()

    # Guarded capability is blocked now
    with pytest.raises(PremiumEntitlementRequiredError):
        ensure_capability(session, space.id, Capability.RECAP_PDF_YEARBOOK)

    # BUT existing data is 100% readable and not lost (Non-destructive downgrade invariant)
    memories_response = client.get(f"/api/v1/spaces/{space.id}/memories", headers=auth(token))
    assert memories_response.status_code == 200
    memories = memories_response.json()["items"]
    assert len(memories) == 1
    assert memories[0]["id"] == memory_id
    assert memories[0]["title"] == "Our Paris Trip"
