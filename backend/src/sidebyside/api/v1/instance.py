"""Minimal public instance capability state.

Unauthenticated clients need to distinguish planned maintenance and disabled
registration from an ordinary connectivity failure. This endpoint deliberately
exposes only the public effective state and no privileged configuration.
"""

from __future__ import annotations

from typing import Literal

from fastapi import APIRouter

from sidebyside.administration import service as administration
from sidebyside.api.deps import DbSession
from sidebyside.api.schema import ApiModel

router = APIRouter(tags=["instance"])


class InstanceAccessStatus(ApiModel):
    maintenance_mode: bool
    registration_available: bool
    registration_unavailable_reason: Literal["maintenance", "administrator"] | None


@router.get("/instance/status", response_model=InstanceAccessStatus)
def instance_status(session: DbSession) -> InstanceAccessStatus:
    """Return the minimum public state required by login/onboarding clients."""
    state = administration.get_access_state(session)
    reason: Literal["maintenance", "administrator"] | None = None
    if state.maintenance_mode:
        reason = "maintenance"
    elif not state.registration_enabled:
        reason = "administrator"

    return InstanceAccessStatus(
        maintenance_mode=state.maintenance_mode,
        registration_available=state.effective_registration_enabled,
        registration_unavailable_reason=reason,
    )
