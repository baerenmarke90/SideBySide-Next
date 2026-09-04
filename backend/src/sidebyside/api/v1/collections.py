"""HTTP contract for shared M3 Collections."""

from __future__ import annotations

from datetime import datetime
from typing import Annotated, Self
from uuid import UUID

from fastapi import APIRouter, Path, Query, Response, status
from pydantic import ConfigDict, field_validator, model_validator
from pydantic.json_schema import SkipJsonSchema

from sidebyside.api.concurrency import IfMatchVersion, etag_for
from sidebyside.api.deps import Authorization, DbSession
from sidebyside.api.errors import problem_responses
from sidebyside.api.schema import ApiModel, AuthorSummary, ResourceCapabilities
from sidebyside.collections import service
from sidebyside.collections.models import Collection, CollectionItem
from sidebyside.identity.models import Account

router = APIRouter(tags=["collections"])

ETAG_HEADERS = {
    "ETag": {
        "description": "Resource version to use for the next If-Match write request.",
        "schema": {"type": "string"},
    }
}


class CollectionCreate(ApiModel):
    model_config = ConfigDict(extra="forbid")

    title: str

    @field_validator("title")
    @classmethod
    def _title_not_blank(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("must not be blank")
        return cleaned


class CollectionUpdate(ApiModel):
    model_config = ConfigDict(extra="forbid")

    title: str | SkipJsonSchema[None] = None

    @model_validator(mode="after")
    def _validate_patch(self) -> Self:
        if not self.model_fields_set:
            raise ValueError("at least one field must be supplied")
        if "title" in self.model_fields_set:
            if self.title is None or not self.title.strip():
                raise ValueError("title must not be null or blank")
            self.title = self.title.strip()
        return self


class CollectionItemCreate(ApiModel):
    model_config = ConfigDict(extra="forbid")

    title: str
    completed: bool = False

    @field_validator("title")
    @classmethod
    def _title_not_blank(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("must not be blank")
        return cleaned


class CollectionItemUpdate(ApiModel):
    model_config = ConfigDict(extra="forbid")

    title: str | SkipJsonSchema[None] = None
    completed: bool | SkipJsonSchema[None] = None

    @model_validator(mode="after")
    def _validate_patch(self) -> Self:
        if not self.model_fields_set:
            raise ValueError("at least one field must be supplied")
        if "title" in self.model_fields_set:
            if self.title is None or not self.title.strip():
                raise ValueError("title must not be null or blank")
            self.title = self.title.strip()
        if "completed" in self.model_fields_set and self.completed is None:
            raise ValueError("completed must not be null")
        return self


class CollectionOrder(ApiModel):
    model_config = ConfigDict(extra="forbid")

    item_ids: list[UUID]


class CollectionItemDetail(ApiModel):
    id: UUID
    collection_id: UUID
    created_by: UUID
    title: str
    completed: bool
    position: int
    version: int
    created_at: datetime
    updated_at: datetime
    creator: AuthorSummary
    capabilities: ResourceCapabilities


class CollectionDetail(ApiModel):
    id: UUID
    space_id: UUID
    created_by: UUID
    title: str
    version: int
    created_at: datetime
    updated_at: datetime
    creator: AuthorSummary
    capabilities: ResourceCapabilities
    items: list[CollectionItemDetail]


class CollectionPage(ApiModel):
    items: list[CollectionDetail]
    next_cursor: str | None
    has_more: bool


def _creator(session: DbSession, account_id: UUID, *, resource: str) -> AuthorSummary:
    creator = session.get(Account, account_id)
    if creator is None:
        raise RuntimeError(f"{resource} creator disappeared despite foreign key protection.")
    return AuthorSummary(id=creator.id, display_name=creator.display_name)


def collection_item_detail(session: DbSession, item: CollectionItem) -> CollectionItemDetail:
    return CollectionItemDetail(
        id=item.id,
        collection_id=item.collection_id,
        created_by=item.created_by,
        title=item.payload.title,
        completed=item.completed,
        position=item.position,
        version=item.version,
        created_at=item.created_at,
        updated_at=item.updated_at,
        creator=_creator(session, item.created_by, resource="Collection Item"),
        capabilities=ResourceCapabilities(
            can_edit=True,
            can_delete=True,
            can_comment=False,
        ),
    )


def collection_detail(session: DbSession, collection: Collection) -> CollectionDetail:
    return CollectionDetail(
        id=collection.id,
        space_id=collection.space_id,
        created_by=collection.owner_id,
        title=collection.payload.title,
        version=collection.version,
        created_at=collection.created_at,
        updated_at=collection.updated_at,
        creator=_creator(session, collection.owner_id, resource="Collection"),
        capabilities=ResourceCapabilities(
            can_edit=True,
            can_delete=True,
            can_comment=False,
        ),
        items=[
            collection_item_detail(session, item)
            for item in service.list_items(session, collection)
        ],
    )


@router.post(
    "/spaces/{spaceId}/collections",
    response_model=CollectionDetail,
    status_code=status.HTTP_201_CREATED,
    operation_id="createCollection",
    responses={201: {"headers": ETAG_HEADERS}, **problem_responses(401, 404, 422)},
)
def create_collection(
    authorization: Authorization,
    session: DbSession,
    response: Response,
    body: CollectionCreate,
) -> CollectionDetail:
    collection = service.create_collection(
        session,
        authorization,
        title=body.title,
    )
    response.headers["ETag"] = etag_for(collection.version)
    return collection_detail(session, collection)


@router.get(
    "/spaces/{spaceId}/collections",
    response_model=CollectionPage,
    operation_id="listCollections",
    responses=problem_responses(400, 401, 404, 422),
)
def list_collections(
    authorization: Authorization,
    session: DbSession,
    cursor: Annotated[str | None, Query()] = None,
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
) -> CollectionPage:
    page = service.list_collections(session, authorization, cursor=cursor, limit=limit)
    return CollectionPage(
        items=[collection_detail(session, collection) for collection in page.items],
        next_cursor=page.next_cursor,
        has_more=page.has_more,
    )


@router.get(
    "/spaces/{spaceId}/collections/{collectionId}",
    response_model=CollectionDetail,
    operation_id="getCollection",
    responses={200: {"headers": ETAG_HEADERS}, **problem_responses(401, 404)},
)
def get_collection(
    authorization: Authorization,
    session: DbSession,
    response: Response,
    collection_id: Annotated[str, Path(alias="collectionId")],
) -> CollectionDetail:
    collection = service.get_collection(session, authorization, collection_id)
    response.headers["ETag"] = etag_for(collection.version)
    return collection_detail(session, collection)


@router.patch(
    "/spaces/{spaceId}/collections/{collectionId}",
    response_model=CollectionDetail,
    operation_id="updateCollection",
    responses={200: {"headers": ETAG_HEADERS}, **problem_responses(401, 404, 409, 422)},
)
def update_collection(
    authorization: Authorization,
    session: DbSession,
    response: Response,
    body: CollectionUpdate,
    expected_version: IfMatchVersion,
    collection_id: Annotated[str, Path(alias="collectionId")],
) -> CollectionDetail:
    collection = service.update_collection(
        session,
        authorization,
        collection_id,
        expected_version=expected_version,
        changed_fields=frozenset(body.model_fields_set),
        title=body.title,
    )
    response.headers["ETag"] = etag_for(collection.version)
    return collection_detail(session, collection)


@router.delete(
    "/spaces/{spaceId}/collections/{collectionId}",
    status_code=status.HTTP_204_NO_CONTENT,
    response_class=Response,
    operation_id="deleteCollection",
    responses=problem_responses(401, 404, 409, 422),
)
def delete_collection(
    authorization: Authorization,
    session: DbSession,
    expected_version: IfMatchVersion,
    collection_id: Annotated[str, Path(alias="collectionId")],
) -> Response:
    service.delete_collection(
        session,
        authorization,
        collection_id,
        expected_version=expected_version,
    )
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post(
    "/spaces/{spaceId}/collections/{collectionId}/items",
    response_model=CollectionItemDetail,
    status_code=status.HTTP_201_CREATED,
    operation_id="createCollectionItem",
    responses={201: {"headers": ETAG_HEADERS}, **problem_responses(401, 404, 422)},
)
def create_collection_item(
    authorization: Authorization,
    session: DbSession,
    response: Response,
    body: CollectionItemCreate,
    collection_id: Annotated[str, Path(alias="collectionId")],
) -> CollectionItemDetail:
    item = service.create_item(
        session,
        authorization,
        collection_id,
        title=body.title,
        completed=body.completed,
    )
    response.headers["ETag"] = etag_for(item.version)
    return collection_item_detail(session, item)


@router.patch(
    "/spaces/{spaceId}/collections/{collectionId}/items/{itemId}",
    response_model=CollectionItemDetail,
    operation_id="updateCollectionItem",
    responses={200: {"headers": ETAG_HEADERS}, **problem_responses(401, 404, 409, 422)},
)
def update_collection_item(
    authorization: Authorization,
    session: DbSession,
    response: Response,
    body: CollectionItemUpdate,
    expected_version: IfMatchVersion,
    collection_id: Annotated[str, Path(alias="collectionId")],
    item_id: Annotated[str, Path(alias="itemId")],
) -> CollectionItemDetail:
    item = service.update_item(
        session,
        authorization,
        collection_id,
        item_id,
        expected_version=expected_version,
        changed_fields=frozenset(body.model_fields_set),
        title=body.title,
        completed=body.completed,
    )
    response.headers["ETag"] = etag_for(item.version)
    return collection_item_detail(session, item)


@router.delete(
    "/spaces/{spaceId}/collections/{collectionId}/items/{itemId}",
    status_code=status.HTTP_204_NO_CONTENT,
    response_class=Response,
    operation_id="deleteCollectionItem",
    responses=problem_responses(401, 404, 409, 422),
)
def delete_collection_item(
    authorization: Authorization,
    session: DbSession,
    expected_version: IfMatchVersion,
    collection_id: Annotated[str, Path(alias="collectionId")],
    item_id: Annotated[str, Path(alias="itemId")],
) -> Response:
    service.delete_item(
        session,
        authorization,
        collection_id,
        item_id,
        expected_version=expected_version,
    )
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.put(
    "/spaces/{spaceId}/collections/{collectionId}/order",
    response_model=CollectionDetail,
    operation_id="reorderCollectionItems",
    responses={200: {"headers": ETAG_HEADERS}, **problem_responses(401, 404, 409, 422)},
)
def reorder_collection_items(
    authorization: Authorization,
    session: DbSession,
    response: Response,
    body: CollectionOrder,
    expected_version: IfMatchVersion,
    collection_id: Annotated[str, Path(alias="collectionId")],
) -> CollectionDetail:
    collection = service.reorder_items(
        session,
        authorization,
        collection_id,
        expected_version=expected_version,
        item_ids=body.item_ids,
    )
    response.headers["ETag"] = etag_for(collection.version)
    return collection_detail(session, collection)
