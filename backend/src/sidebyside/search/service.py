"""Authorized PostgreSQL full-text Search for M4-A.

Search is deliberately a derived read model. Every SQL leg constrains tenant
and privacy before ranking, and the result set contains only the fields needed
for Search presentation. No separate plaintext search document exists.
"""

from __future__ import annotations

import unicodedata
from dataclasses import dataclass
from datetime import UTC, date, datetime
from enum import StrEnum
from typing import Any
from uuid import UUID

from sqlalchemy import text
from sqlalchemy.orm import Session

from sidebyside.authorization import AuthorizationContext
from sidebyside.core import cursor as cursor_codec
from sidebyside.core.errors import ValidationError

DEFAULT_LIMIT = 25
MAX_LIMIT = 50
MIN_QUERY_LENGTH = 2
MAX_QUERY_LENGTH = 200
_EXCERPT_LENGTH = 240
_RANK_SCALE = 1_000_000
_SORT_CONTRACT = "search-v1"


class SearchKind(StrEnum):
    MEMORY = "MEMORY"
    HEART_MOMENT = "HEART_MOMENT"
    MILESTONE = "MILESTONE"
    WISH = "WISH"
    PLAN = "PLAN"
    PLACE = "PLACE"
    CHAPTER = "CHAPTER"
    COLLECTION = "COLLECTION"
    COLLECTION_ITEM = "COLLECTION_ITEM"
    PRIVATE_NOTE = "PRIVATE_NOTE"
    GIFT_IDEA = "GIFT_IDEA"
    PRIVATE_COLLECTION = "PRIVATE_COLLECTION"
    PRIVATE_COLLECTION_ITEM = "PRIVATE_COLLECTION_ITEM"


class SearchScope(StrEnum):
    SHARED = "SHARED"
    PRIVATE = "PRIVATE"


@dataclass(frozen=True)
class SearchRow:
    kind: SearchKind
    id: UUID
    parent_id: UUID | None
    scope: SearchScope
    title: str | None
    excerpt: str | None
    occurred_on: date | None
    created_at: datetime
    rank_key: int


@dataclass(frozen=True)
class SearchPageResult:
    items: list[SearchRow]
    next_cursor: str | None


@dataclass(frozen=True)
class _SearchLeg:
    kind: SearchKind
    sql: str


def normalize_query(value: str) -> str:
    """Return the canonical query used for Search and cursor binding."""
    normalized = unicodedata.normalize("NFC", value)
    normalized = " ".join(normalized.split())
    if not MIN_QUERY_LENGTH <= len(normalized) <= MAX_QUERY_LENGTH:
        raise ValidationError(
            "Search query must contain between 2 and 200 characters after normalization.",
            "SEARCH_QUERY_INVALID",
        )
    return normalized


def _vector(*weighted_fields: tuple[str, str]) -> str:
    return " || ".join(
        "setweight(to_tsvector('simple', coalesce(" + field + ", '')), '" + weight + "')"
        for field, weight in weighted_fields
    )


def _root_leg(
    *,
    kind: SearchKind,
    table_name: str,
    vector: str,
    scope: SearchScope,
    title_sql: str,
    excerpt_sql: str,
    occurred_on_sql: str = "NULL::date",
    owner_only: bool = False,
    extra_predicate: str = "TRUE",
) -> _SearchLeg:
    owner_predicate = "AND source.owner_id = :account_id" if owner_only else ""
    return _SearchLeg(
        kind=kind,
        sql=f"""
        SELECT
            '{kind.value}'::text AS kind,
            source.id AS id,
            NULL::uuid AS parent_id,
            '{scope.value}'::text AS scope,
            {title_sql} AS title,
            {excerpt_sql} AS excerpt,
            {occurred_on_sql} AS occurred_on,
            source.created_at AS created_at,
            round((ts_rank_cd({vector}, input.q) * {_RANK_SCALE})::numeric)::bigint AS rank_key
        FROM {table_name} AS source
        CROSS JOIN search_input AS input
        WHERE source.space_id = :space_id
          {owner_predicate}
          AND {extra_predicate}
          AND ({vector}) @@ input.q
        """,
    )


def _shared_item_leg() -> _SearchLeg:
    vector = _vector(("item.payload->>'title'", "A"))
    return _SearchLeg(
        kind=SearchKind.COLLECTION_ITEM,
        sql=f"""
        SELECT
            'COLLECTION_ITEM'::text AS kind,
            item.id AS id,
            parent.id AS parent_id,
            'SHARED'::text AS scope,
            item.payload->>'title' AS title,
            NULL::text AS excerpt,
            NULL::date AS occurred_on,
            item.created_at AS created_at,
            round((ts_rank_cd({vector}, input.q) * {_RANK_SCALE})::numeric)::bigint AS rank_key
        FROM collection_items AS item
        JOIN collections AS parent ON parent.id = item.collection_id
        CROSS JOIN search_input AS input
        WHERE parent.space_id = :space_id
          AND parent.privacy_class = 'SPACE_SHARED'
          AND ({vector}) @@ input.q
        """,
    )


def _private_item_leg() -> _SearchLeg:
    vector = _vector(("item.payload->>'title'", "A"))
    return _SearchLeg(
        kind=SearchKind.PRIVATE_COLLECTION_ITEM,
        sql=f"""
        SELECT
            'PRIVATE_COLLECTION_ITEM'::text AS kind,
            item.id AS id,
            parent.id AS parent_id,
            'PRIVATE'::text AS scope,
            item.payload->>'title' AS title,
            NULL::text AS excerpt,
            NULL::date AS occurred_on,
            item.created_at AS created_at,
            round((ts_rank_cd({vector}, input.q) * {_RANK_SCALE})::numeric)::bigint AS rank_key
        FROM private_collection_items AS item
        JOIN private_collections AS parent ON parent.id = item.collection_id
        CROSS JOIN search_input AS input
        WHERE parent.space_id = :space_id
          AND parent.owner_id = :account_id
          AND parent.privacy_class = 'OWNER_ONLY'
          AND ({vector}) @@ input.q
        """,
    )


def _bounded(value: str) -> str:
    return f"left(nullif({value}, ''), {_EXCERPT_LENGTH})"


_MEMORY_VECTOR = _vector(("source.payload->>'title'", "A"), ("source.payload->>'body'", "B"))
_HEART_VECTOR = _vector(("source.payload->>'text'", "A"))
_MILESTONE_VECTOR = _vector(
    ("source.payload->>'title'", "A"),
    ("source.payload->>'body'", "B"),
)
_WISH_VECTOR = _vector(("source.payload->>'title'", "A"))
_PLAN_VECTOR = _vector(
    ("source.payload->>'title'", "A"),
    ("source.payload->>'description'", "B"),
)
_PLACE_VECTOR = _vector(
    ("source.payload->>'name'", "A"),
    ("source.payload->>'description'", "B"),
    ("source.payload->>'address'", "B"),
)
_CHAPTER_VECTOR = _vector(
    ("source.payload->>'title'", "A"),
    ("source.payload->>'description'", "B"),
)
_COLLECTION_VECTOR = _vector(("source.payload->>'title'", "A"))
_PRIVATE_NOTE_VECTOR = _vector(
    ("source.payload->>'title'", "A"),
    ("source.payload->>'body'", "B"),
)
_GIFT_VECTOR = _vector(
    ("source.payload->>'title'", "A"),
    ("source.payload->>'description'", "B"),
    ("source.payload->>'recipient'", "B"),
    ("source.payload->>'occasion'", "B"),
    ("source.payload->>'price_text'", "B"),
)
_PRIVATE_COLLECTION_VECTOR = _vector(("source.payload->>'title'", "A"))


_LEGS: dict[SearchKind, tuple[_SearchLeg, ...]] = {
    SearchKind.MEMORY: (
        _root_leg(
            kind=SearchKind.MEMORY,
            table_name="memories",
            vector=_MEMORY_VECTOR,
            scope=SearchScope.SHARED,
            title_sql="source.payload->>'title'",
            excerpt_sql=_bounded("source.payload->>'body'"),
            occurred_on_sql="source.happened_on",
            extra_predicate="source.privacy_class = 'SPACE_SHARED'",
        ),
    ),
    SearchKind.HEART_MOMENT: (
        _root_leg(
            kind=SearchKind.HEART_MOMENT,
            table_name="heart_moments",
            vector=_HEART_VECTOR,
            scope=SearchScope.SHARED,
            title_sql="NULL::text",
            excerpt_sql=_bounded("source.payload->>'text'"),
            occurred_on_sql="source.happened_on",
            extra_predicate="source.privacy_class = 'SPACE_SHARED'",
        ),
        _root_leg(
            kind=SearchKind.HEART_MOMENT,
            table_name="heart_moments",
            vector=_HEART_VECTOR,
            scope=SearchScope.PRIVATE,
            title_sql="NULL::text",
            excerpt_sql=_bounded("source.payload->>'text'"),
            occurred_on_sql="source.happened_on",
            owner_only=True,
            extra_predicate="source.privacy_class = 'OWNER_ONLY'",
        ),
    ),
    SearchKind.MILESTONE: (
        _root_leg(
            kind=SearchKind.MILESTONE,
            table_name="milestones",
            vector=_MILESTONE_VECTOR,
            scope=SearchScope.SHARED,
            title_sql="source.payload->>'title'",
            excerpt_sql=_bounded("source.payload->>'body'"),
            occurred_on_sql="source.happened_on",
            extra_predicate="source.privacy_class = 'SPACE_SHARED'",
        ),
    ),
    SearchKind.WISH: (
        _root_leg(
            kind=SearchKind.WISH,
            table_name="wishes",
            vector=_WISH_VECTOR,
            scope=SearchScope.SHARED,
            title_sql="source.payload->>'title'",
            excerpt_sql="NULL::text",
            extra_predicate="source.privacy_class = 'SPACE_SHARED'",
        ),
    ),
    SearchKind.PLAN: (
        _root_leg(
            kind=SearchKind.PLAN,
            table_name="plans",
            vector=_PLAN_VECTOR,
            scope=SearchScope.SHARED,
            title_sql="source.payload->>'title'",
            excerpt_sql=_bounded("source.payload->>'description'"),
            occurred_on_sql="source.experienced_on",
            extra_predicate="source.privacy_class = 'SPACE_SHARED'",
        ),
    ),
    SearchKind.PLACE: (
        _root_leg(
            kind=SearchKind.PLACE,
            table_name="places",
            vector=_PLACE_VECTOR,
            scope=SearchScope.SHARED,
            title_sql="source.payload->>'name'",
            excerpt_sql=_bounded(
                "concat_ws(' · ', nullif(source.payload->>'description', ''), "
                "nullif(source.payload->>'address', ''))"
            ),
            extra_predicate="source.privacy_class = 'SPACE_SHARED'",
        ),
    ),
    SearchKind.CHAPTER: (
        _root_leg(
            kind=SearchKind.CHAPTER,
            table_name="chapters",
            vector=_CHAPTER_VECTOR,
            scope=SearchScope.SHARED,
            title_sql="source.payload->>'title'",
            excerpt_sql=_bounded("source.payload->>'description'"),
            occurred_on_sql="source.start_on",
            extra_predicate="source.privacy_class = 'SPACE_SHARED'",
        ),
    ),
    SearchKind.COLLECTION: (
        _root_leg(
            kind=SearchKind.COLLECTION,
            table_name="collections",
            vector=_COLLECTION_VECTOR,
            scope=SearchScope.SHARED,
            title_sql="source.payload->>'title'",
            excerpt_sql="NULL::text",
            extra_predicate="source.privacy_class = 'SPACE_SHARED'",
        ),
    ),
    SearchKind.COLLECTION_ITEM: (_shared_item_leg(),),
    SearchKind.PRIVATE_NOTE: (
        _root_leg(
            kind=SearchKind.PRIVATE_NOTE,
            table_name="private_notes",
            vector=_PRIVATE_NOTE_VECTOR,
            scope=SearchScope.PRIVATE,
            title_sql="source.payload->>'title'",
            excerpt_sql=_bounded("source.payload->>'body'"),
            owner_only=True,
            extra_predicate="source.privacy_class = 'OWNER_ONLY'",
        ),
    ),
    SearchKind.GIFT_IDEA: (
        _root_leg(
            kind=SearchKind.GIFT_IDEA,
            table_name="gift_ideas",
            vector=_GIFT_VECTOR,
            scope=SearchScope.PRIVATE,
            title_sql="source.payload->>'title'",
            excerpt_sql=_bounded(
                "concat_ws(' · ', nullif(source.payload->>'description', ''), "
                "nullif(source.payload->>'recipient', ''), "
                "nullif(source.payload->>'occasion', ''), "
                "nullif(source.payload->>'price_text', ''))"
            ),
            owner_only=True,
            extra_predicate="source.privacy_class = 'OWNER_ONLY'",
        ),
    ),
    SearchKind.PRIVATE_COLLECTION: (
        _root_leg(
            kind=SearchKind.PRIVATE_COLLECTION,
            table_name="private_collections",
            vector=_PRIVATE_COLLECTION_VECTOR,
            scope=SearchScope.PRIVATE,
            title_sql="source.payload->>'title'",
            excerpt_sql="NULL::text",
            owner_only=True,
            extra_predicate="source.privacy_class = 'OWNER_ONLY'",
        ),
    ),
    SearchKind.PRIVATE_COLLECTION_ITEM: (_private_item_leg(),),
}


def _canonical_kinds(kinds: tuple[SearchKind, ...]) -> tuple[SearchKind, ...]:
    selected = kinds or tuple(SearchKind)
    return tuple(sorted(set(selected), key=lambda kind: kind.value))


def _cursor_binding(
    context: AuthorizationContext,
    *,
    query: str,
    kinds: tuple[SearchKind, ...],
) -> dict[str, Any]:
    return {
        "collection": "search",
        "accountId": str(context.account_id),
        "spaceId": str(context.space_id),
        "query": query,
        "types": [kind.value for kind in kinds],
        "sort": _SORT_CONTRACT,
    }


def _encode_cursor(
    context: AuthorizationContext,
    *,
    query: str,
    kinds: tuple[SearchKind, ...],
    item: SearchRow,
) -> str:
    return cursor_codec.encode(
        binding=_cursor_binding(context, query=query, kinds=kinds),
        position={
            "rank": item.rank_key,
            "createdAt": item.created_at.astimezone(UTC).isoformat().replace("+00:00", "Z"),
            "type": item.kind.value,
            "id": str(item.id),
        },
    )


def _decode_cursor(
    token: str,
    context: AuthorizationContext,
    *,
    query: str,
    kinds: tuple[SearchKind, ...],
) -> tuple[int, datetime, SearchKind, UUID]:
    position = cursor_codec.decode(
        token,
        binding=_cursor_binding(context, query=query, kinds=kinds),
    )
    rank_raw = position.get("rank")
    created_at_raw = position.get("createdAt")
    kind_raw = position.get("type")
    id_raw = position.get("id")
    if isinstance(rank_raw, bool) or not isinstance(rank_raw, int):
        raise cursor_codec.invalid_cursor()
    if not all(isinstance(value, str) for value in (created_at_raw, kind_raw, id_raw)):
        raise cursor_codec.invalid_cursor()
    try:
        created_at = datetime.fromisoformat(str(created_at_raw).replace("Z", "+00:00"))
        kind = SearchKind(str(kind_raw))
        item_id = UUID(str(id_raw))
    except ValueError as error:
        raise cursor_codec.invalid_cursor() from error
    if created_at.tzinfo is None:
        raise cursor_codec.invalid_cursor()
    return rank_raw, created_at.astimezone(UTC), kind, item_id


def _cursor_predicate(position: tuple[int, datetime, SearchKind, UUID] | None) -> str:
    if position is None:
        return ""
    return """
    WHERE
        rank_key < :cursor_rank
        OR (rank_key = :cursor_rank AND created_at < :cursor_created_at)
        OR (
            rank_key = :cursor_rank
            AND created_at = :cursor_created_at
            AND kind > :cursor_kind
        )
        OR (
            rank_key = :cursor_rank
            AND created_at = :cursor_created_at
            AND kind = :cursor_kind
            AND id > :cursor_id
        )
    """


def search(
    session: Session,
    context: AuthorizationContext,
    *,
    query: str,
    kinds: tuple[SearchKind, ...] = (),
    cursor: str | None = None,
    limit: int = DEFAULT_LIMIT,
) -> SearchPageResult:
    """Return one authorized global Search page."""
    normalized_query = normalize_query(query)
    selected = _canonical_kinds(kinds)
    position = (
        _decode_cursor(cursor, context, query=normalized_query, kinds=selected)
        if cursor is not None
        else None
    )

    legs = [leg.sql for kind in selected for leg in _LEGS[kind]]
    if not legs:
        return SearchPageResult(items=[], next_cursor=None)

    statement = text(
        "WITH search_input AS ("
        "SELECT websearch_to_tsquery('simple', :query) AS q"
        "), candidates AS ("
        + " UNION ALL ".join(legs)
        + ") SELECT kind, id, parent_id, scope, title, excerpt, occurred_on, "
        "created_at, rank_key FROM candidates "
        + _cursor_predicate(position)
        + " ORDER BY rank_key DESC, created_at DESC, kind ASC, id ASC "
        "LIMIT :fetch_limit"
    )
    parameters: dict[str, Any] = {
        "query": normalized_query,
        "space_id": context.space_id,
        "account_id": context.account_id,
        "fetch_limit": limit + 1,
    }
    if position is not None:
        rank_key, created_at, kind, item_id = position
        parameters.update(
            cursor_rank=rank_key,
            cursor_created_at=created_at,
            cursor_kind=kind.value,
            cursor_id=item_id,
        )

    rows = session.execute(statement, parameters).mappings().all()
    has_more = len(rows) > limit
    items = [
        SearchRow(
            kind=SearchKind(str(row["kind"])),
            id=row["id"],
            parent_id=row["parent_id"],
            scope=SearchScope(str(row["scope"])),
            title=row["title"],
            excerpt=row["excerpt"],
            occurred_on=row["occurred_on"],
            created_at=row["created_at"],
            rank_key=int(row["rank_key"]),
        )
        for row in rows[:limit]
    ]
    next_cursor = None
    if has_more and items:
        next_cursor = _encode_cursor(
            context,
            query=normalized_query,
            kinds=selected,
            item=items[-1],
        )
    return SearchPageResult(items=items, next_cursor=next_cursor)
