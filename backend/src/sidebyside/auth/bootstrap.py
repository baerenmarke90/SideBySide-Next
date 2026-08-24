"""Einmalige und atomare Inbetriebnahme einer Self-Hosted-Instanz."""

from __future__ import annotations

from secrets import compare_digest

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from sidebyside.core.clock import now
from sidebyside.core.errors import ForbiddenError
from sidebyside.identity import service as accounts
from sidebyside.identity.models import Account, InstanceBootstrapState

# Transaktionsweite PostgreSQL-Sperre fuer genau diese eine globale
# Invariante. Sie funktioniert bereits, bevor die Singleton-Zeile existiert.
_BOOTSTRAP_LOCK_KEY = 0x534253424F4F54
_SINGLETON_KEY = 1


class BootstrapErrorCode:
    INVALID = "BOOTSTRAP_INVALID"
    CLOSED = "REGISTRATION_REQUIRES_INVITATION"


def claim(
    session: Session,
    *,
    presented_token: str | None,
    configured_token: str | None,
) -> InstanceBootstrapState:
    """Den einmaligen Bootstrap innerhalb der laufenden Transaktion greifen."""
    session.execute(select(func.pg_advisory_xact_lock(_BOOTSTRAP_LOCK_KEY))).scalar_one()

    state = session.get(InstanceBootstrapState, _SINGLETON_KEY)
    if state is None:
        state = InstanceBootstrapState(singleton_key=_SINGLETON_KEY)
        session.add(state)
        session.flush()

    # Fail closed fuer aktualisierte Installationen, deren Account schon vor
    # Einfuehrung des Bootstrap-Zustands existierte.
    if state.completed_at is not None or accounts.account_count(session) > 0:
        raise ForbiddenError(
            "Registration on this instance requires an invitation.",
            BootstrapErrorCode.CLOSED,
        )

    if (
        configured_token is None
        or presented_token is None
        or not compare_digest(presented_token, configured_token)
    ):
        raise ForbiddenError(
            "A valid bootstrap proof is required for initial registration.",
            BootstrapErrorCode.INVALID,
        )

    return state


def complete(state: InstanceBootstrapState, account: Account) -> None:
    state.completed_at = now()
    state.completed_by = account.id
