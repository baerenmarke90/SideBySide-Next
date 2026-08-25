"""Fachlogik fuer M2-Memories.

Der Service erzwingt Tenant-/Owner-Grenzen vor jeder Ressourcenmutation,
haelt ProtectedPayload aus Cursor und Events heraus und koppelt Domainzustand
mit der Transactional Outbox in derselben Request-Transaktion.
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
from dataclasses import dataclass
from datetime import UTC, date, datetime
from typing import Any
from uuid import UUID

from sqlalchemy import and_, or_
from sqlalchemy.orm import Session
from sqlalchemy.orm.exc import StaleDataError

from sidebyside.authorization import (
    AuthorizationContext,
    readable,
    require_readable,
    require_writable,
)
from sidebyside.config import get_settings
from sidebyside.core.errors import BadRequestError, ConflictError, ErrorCode, ValidationError
from sidebyside.domain.events import DomainEvent, EventType, PublicEventPayload
from sidebyside.memories.models import Memory, MemoryPayload, shared_privacy
from sidebyside.outbox import service as outbox_service

_MEMORY_SUBJECT_TYPE = "memory"
_CURSOR_VERSION = 1


@dataclass(frozen=True)
class MemoryPageResult:
    items: list[Memory]
    next_cursor: str | None
    has_more: bool


def _normalize_title(value: str) -> str:
    cleaned = value.strip()
    if not cleaned:
        raise ValidationError("Memory title must not be blank.", "MEMORY_TITLE_REQUIRED")
    return cleaned


def _flush(session: Session) -> None:
    try:
        session.flush()
    except StaleDataError as error:
        raise ConflictError(
            "The resource was changed since it was loaded.",
            ErrorCode.RESOURCE_VERSION_CONFLICT,
        ) from error


def _ensure_expected_version(memory: Memory, expected_version: int) -> None:
    if memory.version != expected_version:
        raise ConflictError(
            "The resource was changed since it was loaded.",
            ErrorCode.RESOURCE_VERSION_CONFLICT,
        )


def _record(session: Session, memory: Memory, actor_id: UUID, event_type: EventType) -> None:
    outbox_service.record(
        session,
        DomainEvent(
            type=event_type,
            space_id=memory.space_id,
            actor_id=actor_id,
            subject_type=_MEMORY_SUBJECT_TYPE,
            subject_id=memory.id,
            resource_version=memory.version,
            payload=PublicEventPayload(),
        ),
    )


def create_memory(
    session: Session,
    context: AuthorizationContext,
    *,
    title: str,
    body: str,
    happened_on: date | None,
) -> Memory:
    memory = Memory(
        space_id=context.space_id,
        owner_id=context.account_id,
        privacy_class=shared_privacy(),
        happened_on=happened_on,
        payload=MemoryPayload(title=_normalize_title(title), body=body),
    )
    session.add(memory)
    _flush(session)
    _record(session, memory, context.account_id, EventType.MEMORY_CREATED)
    _flush(session)
    return memory


def get_memory(
    session: Session,
    context: AuthorizationContext,
    memory_id: UUID | str,
) -> Memory:
    return require_readable(session, Memory, context, memory_id)


def update_memory(
    session: Session,
    context: AuthorizationContext,
    memory_id: UUID | str,
    *,
    expected_version: int,
    changed_fields: frozenset[str],
    title: str | None,
    body: str | None,
    happened_on: date | None,
) -> Memory:
    memory = require_writable(session, Memory, context, memory_id)
    _ensure_expected_version(memory, expected_version)

    next_title = memory.payload.title
    next_body = memory.payload.body
    if "title" in changed_fields:
        assert title is not None
        next_title = _normalize_title(title)
    if "body" in changed_fields:
        assert body is not None
        next_body = body
    if "happened_on" in changed_fields:
        memory.happened_on = happened_on

    if "title" in changed_fields or "body" in changed_fields:
        memory.payload = MemoryPayload(title=next_title, body=next_body)

    _flush(session)
    _record(session, memory, context.account_id, EventType.MEMORY_UPDATED)
    _flush(session)
    return memory


def delete_memory(
    session: Session,
    context: AuthorizationContext,
    memory_id: UUID | str,
    *,
    expected_version: int,
) -> None:
    memory = require_writable(session, Memory, context, memory_id)
    _ensure_expected_version(memory, expected_version)
    actor_id = context.account_id
    session.delete(memory)
    _flush(session)
    _record(session, memory, actor_id, EventType.MEMORY_DELETED)
    _flush(session)


def _cursor_signing_key() -> bytes:
    return get_settings().cursor_signing_secret


def _b64encode(value: bytes) -> str:
    return base64.urlsafe_b64encode(value).rstrip(b"=").decode("ascii")


def _b64decode(value: str) -> bytes:
    padding = "=" * (-len(value) % 4)
    return base64.urlsafe_b64decode(value + padding)


def _encode_cursor(
    *,
    context: AuthorizationContext,
    year: int | None,
    created_at: datetime,
    memory_id: UUID,
) -> str:
    payload = {
        "v": _CURSOR_VERSION,
        "spaceId": str(context.space_id),
        "year": year,
        "createdAt": created_at.astimezone(UTC).isoformat().replace("+00:00", "Z"),
        "id": str(memory_id),
    }
    raw = json.dumps(payload, separators=(",", ":"), sort_keys=True).encode("utf-8")
    signature = hmac.new(_cursor_signing_key(), raw, hashlib.sha256).digest()
    return f"{_b64encode(raw)}.{_b64encode(signature)}"


def _invalid_cursor() -> BadRequestError:
    return BadRequestError("The cursor is invalid for this request.", ErrorCode.INVALID_CURSOR)


def _decode_cursor(
    token: str,
    *,
    context: AuthorizationContext,
    year: int | None,
) -> tuple[datetime, UUID]:
    try:
        raw_part, signature_part = token.split(".", 1)
        raw = _b64decode(raw_part)
        supplied_signature = _b64decode(signature_part)
        expected_signature = hmac.new(_cursor_signing_key(), raw, hashlib.sha256).digest()
        if not hmac.compare_digest(supplied_signature, expected_signature):
            raise _invalid_cursor()
        payload: dict[str, Any] = json.loads(raw.decode("utf-8"))
        if (
            payload.get("v") != _CURSOR_VERSION
            or payload.get("spaceId") != str(context.space_id)
            or payload.get("year") != year
        ):
            raise _invalid_cursor()
        created_raw = payload["createdAt"]
        memory_raw = payload["id"]
        if not isinstance(created_raw, str) or not isinstance(memory_raw, str):
            raise _invalid_cursor()
        created_at = datetime.fromisoformat(created_raw.replace("Z", "+00:00"))
        if created_at.tzinfo is None:
            raise _invalid_cursor()
        memory_id = UUID(memory_raw)
    except BadRequestError:
        raise
    except (ValueError, KeyError, TypeError, UnicodeDecodeError) as error:
        raise _invalid_cursor() from error
    return created_at.astimezone(UTC), memory_id


def _apply_year_filter(statement: Any, year: int | None) -> Any:
    if year is None:
        return statement
    day_start = date(year, 1, 1)
    day_end = date(year + 1, 1, 1)
    time_start = datetime(year, 1, 1, tzinfo=UTC)
    time_end = datetime(year + 1, 1, 1, tzinfo=UTC)
    return statement.where(
        or_(
            and_(Memory.happened_on >= day_start, Memory.happened_on < day_end),
            and_(
                Memory.happened_on.is_(None),
                Memory.created_at >= time_start,
                Memory.created_at < time_end,
            ),
        )
    )


def list_memories(
    session: Session,
    context: AuthorizationContext,
    *,
    cursor: str | None,
    limit: int,
    year: int | None,
) -> MemoryPageResult:
    statement = _apply_year_filter(readable(Memory, context), year)
    if cursor is not None:
        created_at, memory_id = _decode_cursor(cursor, context=context, year=year)
        statement = statement.where(
            or_(
                Memory.created_at < created_at,
                and_(Memory.created_at == created_at, Memory.id < memory_id),
            )
        )

    statement = statement.order_by(Memory.created_at.desc(), Memory.id.desc()).limit(limit + 1)
    rows = list(session.execute(statement).scalars().all())
    has_more = len(rows) > limit
    items = rows[:limit]
    next_cursor = None
    if has_more and items:
        last = items[-1]
        next_cursor = _encode_cursor(
            context=context,
            year=year,
            created_at=last.created_at,
            memory_id=last.id,
        )
    return MemoryPageResult(items=items, next_cursor=next_cursor, has_more=has_more)
