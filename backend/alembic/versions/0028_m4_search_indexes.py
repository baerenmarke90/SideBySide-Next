"""M4-A PostgreSQL full-text search indexes.

Revision ID: 0028
Revises: 0027
Create Date: 2026-08-30

Search indexes are derived directly from the existing ProtectedPayload JSONB
columns. No copied plaintext search document is introduced. They are created
concurrently so upgrading a non-empty installation does not take a blocking
write lock for the duration of each index build.
"""

from __future__ import annotations

from alembic import op

revision = "0028"
down_revision = "0027"
branch_labels = None
depends_on = None


_INDEXES: tuple[tuple[str, str, str], ...] = (
    (
        "ix_memories_search_fts",
        "memories",
        "setweight(to_tsvector('simple', coalesce(payload->>'title', '')), 'A') || "
        "setweight(to_tsvector('simple', coalesce(payload->>'body', '')), 'B')",
    ),
    (
        "ix_heart_moments_search_fts",
        "heart_moments",
        "setweight(to_tsvector('simple', coalesce(payload->>'text', '')), 'A')",
    ),
    (
        "ix_milestones_search_fts",
        "milestones",
        "setweight(to_tsvector('simple', coalesce(payload->>'title', '')), 'A') || "
        "setweight(to_tsvector('simple', coalesce(payload->>'body', '')), 'B')",
    ),
    (
        "ix_wishes_search_fts",
        "wishes",
        "setweight(to_tsvector('simple', coalesce(payload->>'title', '')), 'A')",
    ),
    (
        "ix_plans_search_fts",
        "plans",
        "setweight(to_tsvector('simple', coalesce(payload->>'title', '')), 'A') || "
        "setweight(to_tsvector('simple', coalesce(payload->>'description', '')), 'B')",
    ),
    (
        "ix_places_search_fts",
        "places",
        "setweight(to_tsvector('simple', coalesce(payload->>'name', '')), 'A') || "
        "setweight(to_tsvector('simple', coalesce(payload->>'description', '')), 'B') || "
        "setweight(to_tsvector('simple', coalesce(payload->>'address', '')), 'B')",
    ),
    (
        "ix_chapters_search_fts",
        "chapters",
        "setweight(to_tsvector('simple', coalesce(payload->>'title', '')), 'A') || "
        "setweight(to_tsvector('simple', coalesce(payload->>'description', '')), 'B')",
    ),
    (
        "ix_collections_search_fts",
        "collections",
        "setweight(to_tsvector('simple', coalesce(payload->>'title', '')), 'A')",
    ),
    (
        "ix_collection_items_search_fts",
        "collection_items",
        "setweight(to_tsvector('simple', coalesce(payload->>'title', '')), 'A')",
    ),
    (
        "ix_private_notes_search_fts",
        "private_notes",
        "setweight(to_tsvector('simple', coalesce(payload->>'title', '')), 'A') || "
        "setweight(to_tsvector('simple', coalesce(payload->>'body', '')), 'B')",
    ),
    (
        "ix_gift_ideas_search_fts",
        "gift_ideas",
        "setweight(to_tsvector('simple', coalesce(payload->>'title', '')), 'A') || "
        "setweight(to_tsvector('simple', coalesce(payload->>'description', '')), 'B') || "
        "setweight(to_tsvector('simple', coalesce(payload->>'recipient', '')), 'B') || "
        "setweight(to_tsvector('simple', coalesce(payload->>'occasion', '')), 'B') || "
        "setweight(to_tsvector('simple', coalesce(payload->>'price_text', '')), 'B')",
    ),
    (
        "ix_private_collections_search_fts",
        "private_collections",
        "setweight(to_tsvector('simple', coalesce(payload->>'title', '')), 'A')",
    ),
    (
        "ix_private_collection_items_search_fts",
        "private_collection_items",
        "setweight(to_tsvector('simple', coalesce(payload->>'title', '')), 'A')",
    ),
)


def upgrade() -> None:
    # CREATE INDEX CONCURRENTLY is intentionally outside Alembic's migration
    # transaction. Each statement is resumable after an interrupted rollout:
    # IF NOT EXISTS handles indexes already completed by a previous attempt.
    # Runtime integration tests verify the resulting definitions, so the
    # resumability guard is not used as a substitute for schema validation.
    with op.get_context().autocommit_block():
        for name, table, expression in _INDEXES:
            op.execute(
                f"CREATE INDEX CONCURRENTLY IF NOT EXISTS {name} "
                f"ON {table} USING gin (({expression}))"
            )


def downgrade() -> None:
    with op.get_context().autocommit_block():
        for name, _table, _expression in reversed(_INDEXES):
            op.execute(f"DROP INDEX CONCURRENTLY IF EXISTS {name}")
