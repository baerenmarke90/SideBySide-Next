"""HTTP-Vertrag fuer M2-Kommentare."""

from __future__ import annotations

from datetime import datetime
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Path, Query, Response, status
from pydantic import ConfigDict, field_validator

from sidebyside.api.concurrency import IfMatchVersion, etag_for
from sidebyside.api.deps import Authorization, DbSession
from sidebyside.api.errors import problem_responses
from sidebyside.api.schema import ApiModel, AuthorSummary
from sidebyside.comments import service
from sidebyside.comments.models import Comment, CommentTarget
from sidebyside.identity.models import Account

router = APIRouter(tags=["comments"])

ETAG_HEADERS = {
    "ETag": {
        "description": "Version der Ressource fuer den naechsten If-Match-Schreibzugriff.",
        "schema": {"type": "string"},
    }
}


class CommentCreate(ApiModel):
    model_config = ConfigDict(extra="forbid")

    body: str

    @field_validator("body")
    @classmethod
    def _body_not_blank(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("must not be blank")
        return cleaned


class CommentUpdate(CommentCreate):
    pass


class CommentDetail(ApiModel):
    id: UUID
    space_id: UUID
    author_id: UUID
    body: str
    version: int
    created_at: datetime
    updated_at: datetime
    author: AuthorSummary


class CommentPage(ApiModel):
    items: list[CommentDetail]
    next_cursor: str | None
    has_more: bool


def _detail(session: DbSession, comment: Comment) -> CommentDetail:
    author = session.get(Account, comment.owner_id)
    if author is None:
        raise RuntimeError("Comment author disappeared despite foreign key protection.")
    return CommentDetail(
        id=comment.id,
        space_id=comment.space_id,
        author_id=comment.owner_id,
        body=comment.payload.body,
        version=comment.version,
        created_at=comment.created_at,
        updated_at=comment.updated_at,
        author=AuthorSummary(id=author.id, display_name=author.display_name),
    )


def _create(
    session: DbSession,
    authorization: Authorization,
    response: Response,
    body: CommentCreate,
    target_type: CommentTarget,
    target_id: str,
) -> CommentDetail:
    comment = service.create_comment(
        session,
        authorization,
        target_type=target_type,
        target_id=target_id,
        body=body.body,
    )
    response.headers["ETag"] = etag_for(comment.version)
    return _detail(session, comment)


def _list(
    session: DbSession,
    authorization: Authorization,
    target_type: CommentTarget,
    target_id: str,
    cursor: str | None,
    limit: int,
) -> CommentPage:
    page = service.list_comments(
        session,
        authorization,
        target_type=target_type,
        target_id=target_id,
        cursor=cursor,
        limit=limit,
    )
    return CommentPage(
        items=[_detail(session, comment) for comment in page.items],
        next_cursor=page.next_cursor,
        has_more=page.has_more,
    )


@router.post(
    "/spaces/{spaceId}/memories/{memoryId}/comments",
    response_model=CommentDetail,
    status_code=status.HTTP_201_CREATED,
    operation_id="createMemoryComment",
    responses={201: {"headers": ETAG_HEADERS}, **problem_responses(401, 404, 422)},
)
def create_memory_comment(
    authorization: Authorization,
    session: DbSession,
    response: Response,
    body: CommentCreate,
    memory_id: Annotated[str, Path(alias="memoryId")],
) -> CommentDetail:
    return _create(session, authorization, response, body, CommentTarget.MEMORY, memory_id)


@router.get(
    "/spaces/{spaceId}/memories/{memoryId}/comments",
    response_model=CommentPage,
    operation_id="listMemoryComments",
    responses=problem_responses(400, 401, 404, 422),
)
def list_memory_comments(
    authorization: Authorization,
    session: DbSession,
    memory_id: Annotated[str, Path(alias="memoryId")],
    cursor: Annotated[str | None, Query()] = None,
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
) -> CommentPage:
    return _list(session, authorization, CommentTarget.MEMORY, memory_id, cursor, limit)


@router.post(
    "/spaces/{spaceId}/heart-moments/{heartMomentId}/comments",
    response_model=CommentDetail,
    status_code=status.HTTP_201_CREATED,
    operation_id="createHeartMomentComment",
    responses={201: {"headers": ETAG_HEADERS}, **problem_responses(401, 404, 422)},
)
def create_heart_moment_comment(
    authorization: Authorization,
    session: DbSession,
    response: Response,
    body: CommentCreate,
    heart_moment_id: Annotated[str, Path(alias="heartMomentId")],
) -> CommentDetail:
    return _create(
        session,
        authorization,
        response,
        body,
        CommentTarget.HEART_MOMENT,
        heart_moment_id,
    )


@router.get(
    "/spaces/{spaceId}/heart-moments/{heartMomentId}/comments",
    response_model=CommentPage,
    operation_id="listHeartMomentComments",
    responses=problem_responses(400, 401, 404, 422),
)
def list_heart_moment_comments(
    authorization: Authorization,
    session: DbSession,
    heart_moment_id: Annotated[str, Path(alias="heartMomentId")],
    cursor: Annotated[str | None, Query()] = None,
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
) -> CommentPage:
    return _list(
        session,
        authorization,
        CommentTarget.HEART_MOMENT,
        heart_moment_id,
        cursor,
        limit,
    )


@router.post(
    "/spaces/{spaceId}/milestones/{milestoneId}/comments",
    response_model=CommentDetail,
    status_code=status.HTTP_201_CREATED,
    operation_id="createMilestoneComment",
    responses={201: {"headers": ETAG_HEADERS}, **problem_responses(401, 404, 422)},
)
def create_milestone_comment(
    authorization: Authorization,
    session: DbSession,
    response: Response,
    body: CommentCreate,
    milestone_id: Annotated[str, Path(alias="milestoneId")],
) -> CommentDetail:
    return _create(
        session,
        authorization,
        response,
        body,
        CommentTarget.MILESTONE,
        milestone_id,
    )


@router.get(
    "/spaces/{spaceId}/milestones/{milestoneId}/comments",
    response_model=CommentPage,
    operation_id="listMilestoneComments",
    responses=problem_responses(400, 401, 404, 422),
)
def list_milestone_comments(
    authorization: Authorization,
    session: DbSession,
    milestone_id: Annotated[str, Path(alias="milestoneId")],
    cursor: Annotated[str | None, Query()] = None,
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
) -> CommentPage:
    return _list(
        session,
        authorization,
        CommentTarget.MILESTONE,
        milestone_id,
        cursor,
        limit,
    )


@router.patch(
    "/spaces/{spaceId}/comments/{commentId}",
    response_model=CommentDetail,
    operation_id="updateComment",
    responses={
        200: {"headers": ETAG_HEADERS},
        **problem_responses(401, 403, 404, 409, 422),
    },
)
def update_comment(
    authorization: Authorization,
    session: DbSession,
    response: Response,
    body: CommentUpdate,
    expected_version: IfMatchVersion,
    comment_id: Annotated[str, Path(alias="commentId")],
) -> CommentDetail:
    comment = service.update_comment(
        session,
        authorization,
        comment_id,
        expected_version=expected_version,
        body=body.body,
    )
    response.headers["ETag"] = etag_for(comment.version)
    return _detail(session, comment)


@router.delete(
    "/spaces/{spaceId}/comments/{commentId}",
    status_code=status.HTTP_204_NO_CONTENT,
    response_class=Response,
    operation_id="deleteComment",
    responses=problem_responses(401, 403, 404, 409, 422),
)
def delete_comment(
    authorization: Authorization,
    session: DbSession,
    expected_version: IfMatchVersion,
    comment_id: Annotated[str, Path(alias="commentId")],
) -> Response:
    service.delete_comment(
        session,
        authorization,
        comment_id,
        expected_version=expected_version,
    )
    return Response(status_code=status.HTTP_204_NO_CONTENT)
