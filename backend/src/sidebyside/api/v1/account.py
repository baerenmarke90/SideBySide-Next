"""Authenticated Account-level actions."""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from fastapi import APIRouter, status

from sidebyside.api.deps import CurrentAccount
from sidebyside.api.errors import problem_responses
from sidebyside.api.schema import ApiModel
from sidebyside.identity.deletion_models import AccountDeletionStatus
from sidebyside.identity.deletion_self_service import accept_self_deletion

router = APIRouter(prefix="/account", tags=["account"])


class AccountDeletionRequest(ApiModel):
    """Explicit destructive confirmation; the target is always the caller."""

    confirmation: Literal["DELETE_ACCOUNT"]


class AccountDeletionAccepted(ApiModel):
    """Safe client state after irreversible deletion acceptance."""

    accepted_at: datetime
    status: AccountDeletionStatus


@router.post(
    "/deletion",
    response_model=AccountDeletionAccepted,
    status_code=status.HTTP_202_ACCEPTED,
    responses=problem_responses(401, 403, 422, 503),
    summary="Delete the authenticated Account",
)
def delete_own_account(
    payload: AccountDeletionRequest,
    account: CurrentAccount,
) -> AccountDeletionAccepted:
    """Accept deletion for the authenticated Account only.

    No Account identifier is accepted from the client, so this route cannot be
    repurposed into a cross-account deletion primitive. Once the external
    tombstone and fail-closed state commit, cleanup continues through the
    existing worker even if the client disconnects.
    """
    del payload  # Pydantic already enforced the exact confirmation literal.
    result = accept_self_deletion(account.id)
    return AccountDeletionAccepted(
        accepted_at=result.accepted_at,
        status=result.status,
    )
