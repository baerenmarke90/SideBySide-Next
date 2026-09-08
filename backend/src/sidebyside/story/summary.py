"""Authorized aggregate views over the shared Story query."""

from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy import func, select, union_all
from sqlalchemy.orm import Session

from sidebyside.authorization import AuthorizationContext
from sidebyside.story.service import StoryKind, _KIND_RANK, _leg


@dataclass(frozen=True)
class SharedStoryCounts:
    memories: int
    heart_moments: int
    milestones: int


def read_shared_story_counts(
    session: Session,
    context: AuthorizationContext,
) -> SharedStoryCounts:
    """Count the three shared Story kinds without materializing Story rows.

    The aggregate deliberately reuses the same authorized union legs as the
    Timeline. In particular, OWNER_ONLY HeartMoments are filtered in ``_leg``
    before the aggregate sees them, so both active partners receive identical
    shared-story counts and private rows cannot influence totals.
    """
    combined = union_all(
        *(_leg(kind, context, year=None) for kind in StoryKind)
    ).subquery("shared_story_counts")
    rows = session.execute(
        select(combined.c.kind_rank, func.count())
        .group_by(combined.c.kind_rank)
        .order_by(combined.c.kind_rank)
    ).all()
    counts = {int(kind_rank): int(count) for kind_rank, count in rows}
    return SharedStoryCounts(
        memories=counts.get(_KIND_RANK[StoryKind.MEMORY], 0),
        heart_moments=counts.get(_KIND_RANK[StoryKind.HEART_MOMENT], 0),
        milestones=counts.get(_KIND_RANK[StoryKind.MILESTONE], 0),
    )
