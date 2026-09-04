"""Centralized batch resolution of AuthorSummary projections."""

from __future__ import annotations

from collections.abc import Iterable
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from sidebyside.api.schema import AuthorSummary
from sidebyside.attachments.binding import AccountProfileAttachment
from sidebyside.identity.models import Account


def resolve_author_summaries(
    session: Session,
    account_ids: Iterable[UUID],
) -> dict[UUID, AuthorSummary]:
    """Batch-resolve AuthorSummary projections with profile_attachment_id in a single query.

    Performs a single SQL outer join between Account and AccountProfileAttachment,
    preventing N+1 queries across list, timeline, and activity endpoints.
    """
    ids = set(account_ids)
    if not ids:
        return {}

    statement = (
        select(Account, AccountProfileAttachment.attachment_id)
        .outerjoin(
            AccountProfileAttachment,
            AccountProfileAttachment.account_id == Account.id,
        )
        .where(Account.id.in_(ids))
    )
    rows = session.execute(statement).all()
    return {
        account.id: AuthorSummary(
            id=account.id,
            display_name=account.display_name,
            profile_attachment_id=attachment_id,
        )
        for account, attachment_id in rows
    }


def resolve_author_summary(
    session: Session,
    account_id: UUID,
    *,
    resource: str = "Author",
) -> AuthorSummary:
    """Resolve a single AuthorSummary projection with profile_attachment_id."""
    summaries = resolve_author_summaries(session, (account_id,))
    summary = summaries.get(account_id)
    if summary is None:
        raise RuntimeError(f"{resource} disappeared despite foreign key protection.")
    return summary
