"""Fachlogik fuer M2-Kommentare.

Kommentare besitzen keine eigene fachliche Sichtbarkeit. Sie erben die
Erreichbarkeit ihres Parents; die Comment-Zeile ist deshalb zwar
SPACE_SHARED, wird aber niemals ohne erneute Parent-Autorisierung gelesen
oder geaendert.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any, Literal, cast
from uuid import UUID

from sqlalchemy import and_, delete, or_, select
from sqlalchemy.orm import Session
from sqlalchemy.orm.exc import StaleDataError

from sidebyside.authorization import (
    AuthorizationContext,
    ContentVisibility,
    PrivacyClass,
    require_readable,
    require_writable,
    visibility_of,
)
from sidebyside.comments.models import Comment, CommentPayload, CommentTarget
from sidebyside.core import cursor as cursor_codec
from sidebyside.core.errors import ConflictError, ErrorCode, NotFoundError, ValidationError
from sidebyside.core.ids import parse_id
from sidebyside.domain.events import DomainEvent, EventType, PublicEventPayload
from sidebyside.heart_moments.models import HeartMoment
from sidebyside.memories.models import Memory
from sidebyside.milestones.models import Milestone
from sidebyside.outbox import service as outbox_service

_COMMENT_SUBJECT_TYPE = "comment"


@dataclass(frozen=True)
class CommentPageResult:
    items: list[Comment]
    next_cursor: str | None
    has_more: bool


@dataclass(frozen=True)
class CommentParent:
    target_type: CommentTarget
    target_id: UUID
    owner_id: UUID


def _target_not_available() -> NotFoundError:
    return NotFoundError("Comment target not available.", ErrorCode.COMMENT_TARGET_NOT_AVAILABLE)


def _normalize_body(value: str) -> str:
    cleaned = value.strip()
    if not cleaned:
        raise ValidationError("Comment body must not be blank.", "COMMENT_BODY_REQUIRED")
    return cleaned


def _identifier(value: UUID | str) -> UUID:
    parsed = value if isinstance(value, UUID) else parse_id(value)
    if parsed is None:
        raise _target_not_available()
    return parsed


def _flush(session: Session) -> None:
    try:
        session.flush()
    except StaleDataError as error:
        raise ConflictError(
            "The resource was changed since it was loaded.",
            ErrorCode.RESOURCE_VERSION_CONFLICT,
        ) from error


def _ensure_expected_version(comment: Comment, expected_version: int) -> None:
    if comment.version != expected_version:
        raise ConflictError(
            "The resource was changed since it was loaded.",
            ErrorCode.RESOURCE_VERSION_CONFLICT,
        )


def _memory_parent(
    session: Session,
    context: AuthorizationContext,
    target_id: UUID,
    *,
    lock_for_comment_create: bool,
) -> CommentParent:
    if lock_for_comment_create:
        statement = (
            select(Memory)
            .where(
                Memory.id == target_id,
                Memory.space_id == context.space_id,
                Memory.privacy_class == PrivacyClass.SPACE_SHARED.value,
            )
            .with_for_update(read=True)
        )
        memory = session.execute(statement).scalar_one_or_none()
        if memory is None:
            raise _target_not_available()
    else:
        try:
            memory = require_readable(session, Memory, context, target_id)
        except NotFoundError as error:
            raise _target_not_available() from error
    return CommentParent(CommentTarget.MEMORY, memory.id, memory.owner_id)


def _milestone_parent(
    session: Session,
    context: AuthorizationContext,
    target_id: UUID,
    *,
    lock_for_comment_create: bool,
) -> CommentParent:
    if lock_for_comment_create:
        statement = (
            select(Milestone)
            .where(
                Milestone.id == target_id,
                Milestone.space_id == context.space_id,
                Milestone.privacy_class == PrivacyClass.SPACE_SHARED.value,
            )
            .with_for_update(read=True)
        )
        milestone = session.execute(statement).scalar_one_or_none()
        if milestone is None:
            raise _target_not_available()
    else:
        try:
            milestone = require_readable(session, Milestone, context, target_id)
        except NotFoundError as error:
            raise _target_not_available() from error
    return CommentParent(CommentTarget.MILESTONE, milestone.id, milestone.owner_id)


def _heart_moment_parent(
    session: Session,
    context: AuthorizationContext,
    target_id: UUID,
    *,
    lock_for_comment_create: bool,
) -> CommentParent:
    if lock_for_comment_create:
        statement = (
            select(HeartMoment)
            .where(
                HeartMoment.id == target_id,
                HeartMoment.space_id == context.space_id,
                HeartMoment.privacy_class == PrivacyClass.SPACE_SHARED.value,
            )
            .with_for_update(read=True)
        )
        heart_moment = session.execute(statement).scalar_one_or_none()
        if heart_moment is None:
            raise _target_not_available()
    else:
        try:
            heart_moment = require_readable(session, HeartMoment, context, target_id)
        except NotFoundError as error:
            raise _target_not_available() from error
        if visibility_of(heart_moment.privacy_class) is not ContentVisibility.SHARED:
            raise _target_not_available()
    return CommentParent(CommentTarget.HEART_MOMENT, heart_moment.id, heart_moment.owner_id)


def resolve_parent(
    session: Session,
    context: AuthorizationContext,
    target_type: CommentTarget,
    target_id: UUID | str,
    *,
    lock_for_comment_create: bool = False,
) -> CommentParent:
    identifier = _identifier(target_id)
    if target_type is CommentTarget.MEMORY:
        return _memory_parent(
            session,
            context,
            identifier,
            lock_for_comment_create=lock_for_comment_create,
        )
    if target_type is CommentTarget.HEART_MOMENT:
        return _heart_moment_parent(
            session,
            context,
            identifier,
            lock_for_comment_create=lock_for_comment_create,
        )
    return _milestone_parent(
        session,
        context,
        identifier,
        lock_for_comment_create=lock_for_comment_create,
    )


def _record_created(
    session: Session,
    comment: Comment,
    *,
    recipient_id: UUID,
) -> None:
    outbox_service.record(
        session,
        DomainEvent(
            type=EventType.COMMENT_CREATED,
            space_id=comment.space_id,
            actor_id=comment.owner_id,
            subject_type=_COMMENT_SUBJECT_TYPE,
            subject_id=comment.id,
            resource_version=comment.version,
            payload=PublicEventPayload(
                target_type=cast(
                    Literal["MEMORY", "HEART_MOMENT", "MILESTONE"], comment.target_type
                ),
                target_id=comment.target_id,
                recipient_id=recipient_id,
            ),
        ),
    )


def create_comment(
    session: Session,
    context: AuthorizationContext,
    *,
    target_type: CommentTarget,
    target_id: UUID | str,
    body: str,
) -> Comment:
    parent = resolve_parent(
        session,
        context,
        target_type,
        target_id,
        lock_for_comment_create=True,
    )
    comment = Comment(
        space_id=context.space_id,
        owner_id=context.account_id,
        privacy_class=PrivacyClass.SPACE_SHARED.value,
        target_type=parent.target_type.value,
        target_id=parent.target_id,
        payload=CommentPayload(body=_normalize_body(body)),
    )
    session.add(comment)
    _flush(session)
    if parent.owner_id != context.account_id:
        _record_created(session, comment, recipient_id=parent.owner_id)
        _flush(session)
    return comment


def _require_comment_parent(
    session: Session,
    context: AuthorizationContext,
    comment: Comment,
) -> CommentParent:
    try:
        target_type = CommentTarget(comment.target_type)
    except ValueError as error:
        raise _target_not_available() from error
    return resolve_parent(session, context, target_type, comment.target_id)


def update_comment(
    session: Session,
    context: AuthorizationContext,
    comment_id: UUID | str,
    *,
    expected_version: int,
    body: str,
) -> Comment:
    comment = require_writable(session, Comment, context, comment_id)
    _require_comment_parent(session, context, comment)
    _ensure_expected_version(comment, expected_version)
    comment.payload = CommentPayload(body=_normalize_body(body))
    _flush(session)
    return comment


def delete_comment(
    session: Session,
    context: AuthorizationContext,
    comment_id: UUID | str,
    *,
    expected_version: int,
) -> None:
    comment = require_writable(session, Comment, context, comment_id)
    _require_comment_parent(session, context, comment)
    _ensure_expected_version(comment, expected_version)
    session.delete(comment)
    _flush(session)


def _cursor_binding(
    context: AuthorizationContext,
    target_type: CommentTarget,
    target_id: UUID,
) -> dict[str, Any]:
    return {
        "collection": "comments",
        "spaceId": str(context.space_id),
        "targetType": target_type.value,
        "targetId": str(target_id),
    }


def _encode_cursor(
    *,
    context: AuthorizationContext,
    target_type: CommentTarget,
    target_id: UUID,
    created_at: datetime,
    comment_id: UUID,
) -> str:
    return cursor_codec.encode(
        binding=_cursor_binding(context, target_type, target_id),
        position={
            "createdAt": created_at.astimezone(UTC).isoformat().replace("+00:00", "Z"),
            "id": str(comment_id),
        },
    )


def _decode_cursor(
    token: str,
    *,
    context: AuthorizationContext,
    target_type: CommentTarget,
    target_id: UUID,
) -> tuple[datetime, UUID]:
    position = cursor_codec.decode(
        token,
        binding=_cursor_binding(context, target_type, target_id),
    )
    created_raw = position.get("createdAt")
    comment_raw = position.get("id")
    if not isinstance(created_raw, str) or not isinstance(comment_raw, str):
        raise cursor_codec.invalid_cursor()
    try:
        created_at = datetime.fromisoformat(created_raw.replace("Z", "+00:00"))
        comment_id = UUID(comment_raw)
    except ValueError as error:
        raise cursor_codec.invalid_cursor() from error
    if created_at.tzinfo is None:
        raise cursor_codec.invalid_cursor()
    return created_at.astimezone(UTC), comment_id


def list_comments(
    session: Session,
    context: AuthorizationContext,
    *,
    target_type: CommentTarget,
    target_id: UUID | str,
    cursor: str | None,
    limit: int,
) -> CommentPageResult:
    parent = resolve_parent(session, context, target_type, target_id)
    statement = select(Comment).where(
        Comment.space_id == context.space_id,
        Comment.target_type == parent.target_type.value,
        Comment.target_id == parent.target_id,
    )
    if cursor is not None:
        created_at, comment_id = _decode_cursor(
            cursor,
            context=context,
            target_type=target_type,
            target_id=parent.target_id,
        )
        statement = statement.where(
            or_(
                Comment.created_at < created_at,
                and_(Comment.created_at == created_at, Comment.id < comment_id),
            )
        )
    rows = list(
        session.execute(
            statement.order_by(Comment.created_at.desc(), Comment.id.desc()).limit(limit + 1)
        ).scalars()
    )
    has_more = len(rows) > limit
    items = rows[:limit]
    next_cursor = None
    if has_more and items:
        last = items[-1]
        next_cursor = _encode_cursor(
            context=context,
            target_type=target_type,
            target_id=parent.target_id,
            created_at=last.created_at,
            comment_id=last.id,
        )
    return CommentPageResult(items=items, next_cursor=next_cursor, has_more=has_more)


def delete_for_parent(
    session: Session,
    *,
    space_id: UUID,
    target_type: CommentTarget,
    target_id: UUID,
) -> None:
    """Abhaengige Comments innerhalb der laufenden Parent-Transaktion loeschen."""
    session.execute(
        delete(Comment).where(
            Comment.space_id == space_id,
            Comment.target_type == target_type.value,
            Comment.target_id == target_id,
        )
    )
