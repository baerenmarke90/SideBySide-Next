"""Regression tests for PostgreSQL M4 Search index metadata."""

from __future__ import annotations

import pytest
from sqlalchemy.dialects import postgresql
from sqlalchemy.schema import CreateIndex

from sidebyside.chapters.models import Chapter
from sidebyside.gift_ideas.models import GiftIdea
from sidebyside.memories.models import Memory
from sidebyside.milestones.models import Milestone
from sidebyside.places.models import Place
from sidebyside.plans.models import Plan
from sidebyside.private_notes.models import PrivateNote


@pytest.mark.parametrize(
    ("model", "index_name"),
    (
        (Memory, "ix_memories_search_fts"),
        (Milestone, "ix_milestones_search_fts"),
        (Plan, "ix_plans_search_fts"),
        (Place, "ix_places_search_fts"),
        (Chapter, "ix_chapters_search_fts"),
        (PrivateNote, "ix_private_notes_search_fts"),
        (GiftIdea, "ix_gift_ideas_search_fts"),
    ),
)
def test_compound_search_index_metadata_uses_postgresql_expression_parentheses(
    model: type[object],
    index_name: str,
) -> None:
    index = next(index for index in model.__table__.indexes if index.name == index_name)  # type: ignore[attr-defined]

    ddl = str(CreateIndex(index).compile(dialect=postgresql.dialect()))

    assert " USING gin ((" in ddl, ddl
