"""Current Account state checks for asynchronous side-effect boundaries."""

from __future__ import annotations

from collections.abc import Iterable
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from sidebyside.identity.models import Account
from sidebyside.relationship.models import Membership, MembershipStatus


def lock_enabled_accounts(
    session: Session,
    account_ids: Iterable[UUID],
) -> dict[UUID, Account] | None:
    """Lock Accounts in deterministic order and reject deleted/disabled state.

    Account-deletion acceptance locks the same Account row. Holding these locks
    through a worker transaction therefore gives provider/DB side effects a
    strict ordering relative to the irreversible acceptance boundary: either
    the side effect commits first, or deletion acceptance commits first and the
    worker observes the disabled Account and becomes a no-op.
    """
    identifiers = sorted(set(account_ids))
    if not identifiers:
        return {}
    accounts = list(
        session.execute(
            select(Account)
            .where(Account.id.in_(identifiers))
            .order_by(Account.id)
            .with_for_update()
        ).scalars()
    )
    if len(accounts) != len(identifiers) or any(
        account.disabled_at is not None for account in accounts
    ):
        return None
    return {account.id: account for account in accounts}


def has_active_membership(
    session: Session,
    *,
    account_id: UUID,
    space_id: UUID,
) -> bool:
    """Return whether an already enabled Account still has live Space access."""
    return (
        session.execute(
            select(Membership.id).where(
                Membership.space_id == space_id,
                Membership.account_id == account_id,
                Membership.status == MembershipStatus.ACTIVE.value,
            )
        ).scalar_one_or_none()
        is not None
    )
