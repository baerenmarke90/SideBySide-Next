"""Die gemeinsame Zeitleiste.

Story ist ein abgeleitetes Read Model ueber Memory, Milestone und
ausschliesslich gemeinsame HeartMoments. Es gibt keine Story-Tabelle: nach
M2-D11 waere sie eine zweite fachliche Wahrheitsquelle, die bei jedem
Delete, jedem Privacy-Wechsel und jeder Retention-Regel nachgezogen werden
muesste - und genau dort entstuende die Zeile, die es fachlich nicht mehr
gibt.
"""

from __future__ import annotations

from sidebyside.story.service import (
    StoryItem,
    StoryKind,
    StoryOrder,
    StoryPageResult,
    read_timeline,
)

__all__ = [
    "StoryItem",
    "StoryKind",
    "StoryOrder",
    "StoryPageResult",
    "read_timeline",
]
