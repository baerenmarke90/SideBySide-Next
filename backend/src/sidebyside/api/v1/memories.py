"""HTTP-Vertrag fuer den ersten M2-Runtime-Slice: Memory CRUD."""

from __future__ import annotations

from datetime import date, datetime
from typing import Annotated, Self
from uuid import UUID

from fastapi import APIRouter, Path, Query, Response, status
from pydantic import field_validator, model_validator

from sidebyside.api.concurrency import IfMatchVersion, etag_for
from sidebyside.api.deps import Authorization, DbSession
from sidebyside.api.errors import problem_responses
from sidebyside.api.schema import ApiModel
from sidebyside.identity.models import Account
from sidebyside.memories import service
from sidebyside.memories.models import Memory

router = APIRouter(tags=["memories"])

ETAG_HEADERS = {
    "ETag": {
        "description": "Version der Ressource fuer den naechsten If-Match-Schreibzugriff.",
        "schema": {"type": "string"},
    }
}


class MemoryCreate(ApiModel):
    title: str
    body: str
    happened_on: date | None = None

    @field_validator("title")
    @classmethod
    def _title_not_blank(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("must not be blank")
        return cleaned


class MemoryUpdate(ApiModel):
    title: str | None = None
    body: str | None = None
    happened_on: date | None = None

    @model_validator(mode="after")
    def _validate_patch(self) -> Self:
        if not self.model_fields_set:
            raise ValueError("at least one field must be supplied")
        if "title" in self.model_fields_set:
            if self.title is None or not self.title.strip():
                raise ValueError("title must not be null or blank")
            self.title = self.title.strip()
        if "body" in self.model_fields_set and self.body is None:
            raise ValueError("body must not be null")
        return self


class AuthorSummary(ApiModel):
    id: UUID
    display_name: str
    profile_attachment_id: UUID | None = None


class ResourceCapabilities(ApiModel):
    can_edit: bool
    can_delete: bool
    can_comment: bool


class MemoryDetail(ApiModel):
    id: UUID
    space_id: UUID
    author_id: UUID
    title: str
    body: str
    happened_on: date | None
    version: int
    created_at: datetime
    updated_at: datetime
    author: AuthorSummary
    capabilities: ResourceCapabilities


class MemoryPage(ApiModel):
    items: list[MemoryDetail]
    next_cursor: str | None
    has_more: bool


def _memory_detail(session: DbSession, authorization: Authorization, memory: Memory) -> MemoryDetail:
    author = session.get(Account, memory.owner_id)
    if author is None:
        raise RuntimeError("Memory author disappeared despite foreign key protection.")
    is_author = memory.owner_id == authorization.account_id
    return MemoryDetail(
        id=memory.id,
        space_id=memory.space_id,
        author_id=memory.owner_id,
        title=memory.payload.title,
        body=memory.payload.body,
        happened_on=memory.happened_on,
        version=memory.version,
        created_at=memory.created_at,
        updated_at=memory.updated_at,
        author=AuthorSummary(id=author.id, display_name=author.display_name),
        capabilities=ResourceCapabilities(
            can_edit=is_author,
            can_delete=is_author,
            can_comment=True,
        ),
    )


@router.post(
    "/spaces/{spaceId}/memories",
    response_model=MemoryDetail,
    status_code=status.HTTP_201_CREATED,
    operation_id="createMemory",
    responses={201: {"headers": ETAG_HEADERS}, **problem_responses(401, 404, 422)},
)
def create_memory(
    authorization: Authorization,
    session: DbSession,
    response: Response,
    body: MemoryCreate,
) -> MemoryDetail:
    memory = service.create_memory(
        session,
        authorization,
        title=body.title,
        body=body.body,
        happened_on=body.happened_on,
    )
    response.headers["ETag"] = etag_for(memory.version)
    return _memory_detail(session, authorization, memory)


@router.get(
    "/spaces/{spaceId}/memories",
    response_model=MemoryPage,
    operation_id="listMemories",
    responses=problem_responses(400, 401, 404, 422),
)
def list_memories(
    authorization: Authorization,
    session: DbSession,
    cursor: Annotated[str | None, Query()] = None,
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
    year: Annotated[int | None, Query(ge=1900, le=2100)] = None,
) -> MemoryPage:
    page = service.list_memories(
        session,
        authorization,
        cursor=cursor,
        limit=limit,
        year=year,
    )
    return MemoryPage(
        items=[_memory_detail(session, authorization, memory) for memory in page.items],
        next_cursor=page.next_cursor,
        has_more=page.has_more,
    )


@router.get(
    "/spaces/{spaceId}/memories/{memoryId}",
    response_model=MemoryDetail,
    operation_id="getMemory",
    responses={200: {"headers": ETAG_HEADERS}, **problem_responses(401, 404)},
)
def get_memory(
    authorization: Authorization,
    session: DbSession,
    response: Response,
    memory_id: Annotated[str, Path(alias="memoryId")],
) -> MemoryDetail:
    memory = service.get_memory(session, authorization, memory_id)
    response.headers["ETag"] = etag_for(memory.version)
    return _memory_detail(session, authorization, memory)


@router.patch(
    "/spaces/{spaceId}/memories/{memoryId}",
    response_model=MemoryDetail,
    operation_id="updateMemory",
    responses={
        200: {"headers": ETAG_HEADERS},
        **problem_responses(401, 403, 404, 409, 422),
    },
)
def update_memory(
    authorization: Authorization,
    session: DbSession,
    response: Response,
    body: MemoryUpdate,
    expected_version: IfMatchVersion,
    memory_id: Annotated[str, Path(alias="memoryId")],
) -> MemoryDetail:
    memory = service.update_memory(
        session,
        authorization,
        memory_id,
        expected_version=expected_version,
        changed_fields=frozenset(body.model_fields_set),
        title=body.title,
        body=body.body,
        happened_on=body.happened_on,
    )
    response.headers["ETag"] = etag_for(memory.version)
    return _memory_detail(session, authorization, memory)


@router.delete(
    "/spaces/{spaceId}/memories/{memoryId}",
    status_code=status.HTTP_204_NO_CONTENT,
    response_class=Response,
    operation_id="deleteMemory",
    responses=problem_responses(401, 403, 404, 409, 422),
)
def delete_memory(
    authorization: Authorization,
    session: DbSession,
    expected_version: IfMatchVersion,
    memory_id: Annotated[str, Path(alias="memoryId")],
) -> Response:
    service.delete_memory(
        session,
        authorization,
        memory_id,
        expected_version=expected_version,
    )
    return Response(status_code=status.HTTP_204_NO_CONTENT)
