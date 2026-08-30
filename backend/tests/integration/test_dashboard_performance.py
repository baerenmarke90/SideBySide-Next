"""Bounded-query evidence for the M4-A Dashboard read model."""

from __future__ import annotations

from datetime import UTC, date, datetime

import pytest
from sqlalchemy import event
from sqlalchemy.engine import Connection
from sqlalchemy.orm import Session

from sidebyside.authorization import AuthorizationContext, PrivacyClass
from sidebyside.dashboard import service as dashboard_service
from sidebyside.memories.models import Memory, MemoryPayload
from sidebyside.relationship import service as relationship_service
from tests.conftest import make_account, make_space, requires_database

pytestmark = [pytest.mark.integration, requires_database]

FIXED_NOW = datetime(2026, 8, 30, 12, 0, tzinfo=UTC)
MAX_DASHBOARD_SELECTS = 18


def test_dashboard_query_count_is_bounded_as_rows_grow(session: Session) -> None:
    """Dashboard uses a fixed set of domain queries rather than per-row loading."""
    anna = make_account(session, "Anna")
    ben = make_account(session, "Ben")
    space = make_space(session, anna)
    relationship_service.add_member(session, space.id, ben)

    session.add_all(
        Memory(
            space_id=space.id,
            owner_id=anna.id,
            privacy_class=PrivacyClass.SPACE_SHARED.value,
            happened_on=date(2026, 8, 30),
            payload=MemoryPayload(title=f"Memory {index}", body="Bounded query evidence"),
        )
        for index in range(40)
    )
    session.flush()

    context = AuthorizationContext(account_id=anna.id, space_id=space.id)
    bind = session.get_bind()
    selects = 0

    def count_selects(
        connection: Connection,
        cursor: object,
        statement: str,
        parameters: object,
        context: object,
        executemany: bool,
    ) -> None:
        del connection, cursor, parameters, context, executemany
        nonlocal selects
        if statement.lstrip().upper().startswith("SELECT"):
            selects += 1

    event.listen(bind, "before_cursor_execute", count_selects)
    try:
        view = dashboard_service.read_dashboard(session, context, at=FIXED_NOW)
    finally:
        event.remove(bind, "before_cursor_execute", count_selects)

    assert len(view.recent_shared) == dashboard_service.SECTION_LIMIT
    assert selects <= MAX_DASHBOARD_SELECTS
