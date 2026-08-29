"""The shared timeline.

Story is a derived read model over Memory, Milestone, and shared HeartMoments
only. There is no Story table: under M2-D11 it would become a second domain
source of truth that would need to be synchronized after every delete,
privacy transition, and retention rule, exactly where a row could otherwise
survive after it no longer exists in the domain.
"""

from __future__ import annotations

from sidebyside.story.service import (
    StoryKind,
    StoryOrder,
    StoryPageResult,
    StoryRow,
    read_timeline,
)

__all__ = [
    "StoryKind",
    "StoryOrder",
    "StoryPageResult",
    "StoryRow",
    "read_timeline",
]
