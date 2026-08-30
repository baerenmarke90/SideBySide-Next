"""Regression tests for PostgreSQL M4 Search index metadata."""

from __future__ import annotations

from typing import Any

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
    model: Any,
    index_name: str,
) -> None:
    table = model.__table__
    index = next(index for index in table.indexes if index.name == index_name)

    ddl = str(CreateIndex(index).compile(dialect=postgresql.dialect()))

    assert " USING gin ((" in ddl, ddl
