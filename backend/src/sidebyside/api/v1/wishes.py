"""HTTP-Vertrag fuer M3-Wishes."""

from __future__ import annotations

from datetime import datetime
from typing import Annotated, Self
from uuid import UUID

from fastapi import APIRouter, Path, Query, Response
from fastapi import status as http_status
from pydantic import ConfigDict, field_validator, model_validator
from pydantic.json_schema import SkipJsonSchema

from sidebyside.api.concurrency import IfMatchVersion, etag_for
from sidebyside.api.deps import Authorization, DbSession
from sidebyside.api.errors import problem_responses
from sidebyside.api.schema import ApiModel, AuthorSummary, ResourceCapabilities
from sidebyside.identity.models import Account
from sidebyside.wishes import service
from sidebyside.wishes.models import Wish, WishStatus

router = APIRouter(tags=["wishes"])

ETAG_HEADERS = {
    "ETag": {
        "description": "Version der Ressource fuer den naechsten If-Match-Schreibzugriff.",
        "schema": {"type": "string"},
    }
}


class WishCreate(ApiModel):
    """Ein Wish entsteht aus genau einem Feld.

    `extra="forbid"` ist hier mehr als Hygiene: `status`, `createdBy`,
    `spaceId` und `version` sind nach M3-D01/D02 serverseitig. Ein Request,
    der sie mitschickt, wird abgewiesen und nicht stillschweigend um sie
    erleichtert - sonst glaubte der Client, er haette sie gesetzt.
    """

    model_config = ConfigDict(extra="forbid")

    title: str

    @field_validator("title")
    @classmethod
    def _title_not_blank(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("must not be blank")
        return cleaned


class WishUpdate(ApiModel):
    """Die Titelkorrektur.

    Es gibt bewusst kein `status`-Feld. Der Wish-Status folgt
    ausschliesslich dem Wish->Plan-Vertrag (M3-D02/D03/D04); ein freier
    Status-PATCH waere der Weg, an ihm vorbeizukommen.
    """

    model_config = ConfigDict(extra="forbid")

    title: str | SkipJsonSchema[None] = None

    @model_validator(mode="after")
    def _validate_patch(self) -> Self:
        if not self.model_fields_set:
            raise ValueError("at least one field must be supplied")
        if self.title is None or not self.title.strip():
            raise ValueError("title must not be null or blank")
        self.title = self.title.strip()
        return self


class WishDetail(ApiModel):
    id: UUID
    space_id: UUID
    created_by: UUID
    title: str
    status: WishStatus
    version: int
    created_at: datetime
    updated_at: datetime
    creator: AuthorSummary
    capabilities: ResourceCapabilities


class WishPage(ApiModel):
    items: list[WishDetail]
    next_cursor: str | None
    has_more: bool


def _wish_detail(
    session: DbSession,
    authorization: Authorization,
    wish: Wish,
) -> WishDetail:
    creator = session.get(Account, wish.owner_id)
    if creator is None:
        raise RuntimeError("Wish creator disappeared despite foreign key protection.")
    return WishDetail(
        id=wish.id,
        space_id=wish.space_id,
        created_by=wish.owner_id,
        title=wish.payload.title,
        status=WishStatus(wish.status),
        version=wish.version,
        created_at=wish.created_at,
        updated_at=wish.updated_at,
        creator=AuthorSummary(id=creator.id, display_name=creator.display_name),
        capabilities=ResourceCapabilities(
            # M3-D01: ein Wunsch gehoert dem Paar. `createdBy` ist
            # Attribution, keine ACL - beide duerfen ihn aendern.
            can_edit=True,
            # Ein `PLANNED` Wish wird ueber seinen Plan aufgeloest, nicht
            # geloescht (M3-D05).
            can_delete=wish.status != WishStatus.PLANNED.value,
            # Kommentare kennen Wish als Ziel nicht; M3 fuehrt sie dort
            # nicht ein.
            can_comment=False,
        ),
    )


@router.post(
    "/spaces/{spaceId}/wishes",
    response_model=WishDetail,
    status_code=http_status.HTTP_201_CREATED,
    operation_id="createWish",
    responses={201: {"headers": ETAG_HEADERS}, **problem_responses(401, 404, 422)},
)
def create_wish(
    authorization: Authorization,
    session: DbSession,
    response: Response,
    body: WishCreate,
) -> WishDetail:
    wish = service.create_wish(session, authorization, title=body.title)
    response.headers["ETag"] = etag_for(wish.version)
    return _wish_detail(session, authorization, wish)


@router.get(
    "/spaces/{spaceId}/wishes",
    response_model=WishPage,
    operation_id="listWishes",
    responses=problem_responses(400, 401, 404, 422),
)
def list_wishes(
    authorization: Authorization,
    session: DbSession,
    cursor: Annotated[str | None, Query()] = None,
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
    status: Annotated[WishStatus | None, Query()] = None,
) -> WishPage:
    page = service.list_wishes(
        session,
        authorization,
        cursor=cursor,
        limit=limit,
        status=status,
    )
    return WishPage(
        items=[_wish_detail(session, authorization, wish) for wish in page.items],
        next_cursor=page.next_cursor,
        has_more=page.has_more,
    )


@router.get(
    "/spaces/{spaceId}/wishes/{wishId}",
    response_model=WishDetail,
    operation_id="getWish",
    responses={200: {"headers": ETAG_HEADERS}, **problem_responses(401, 404)},
)
def get_wish(
    authorization: Authorization,
    session: DbSession,
    response: Response,
    wish_id: Annotated[str, Path(alias="wishId")],
) -> WishDetail:
    wish = service.get_wish(session, authorization, wish_id)
    response.headers["ETag"] = etag_for(wish.version)
    return _wish_detail(session, authorization, wish)


@router.patch(
    "/spaces/{spaceId}/wishes/{wishId}",
    response_model=WishDetail,
    operation_id="updateWish",
    responses={
        200: {"headers": ETAG_HEADERS},
        **problem_responses(401, 404, 409, 422),
    },
)
def update_wish(
    authorization: Authorization,
    session: DbSession,
    response: Response,
    body: WishUpdate,
    expected_version: IfMatchVersion,
    wish_id: Annotated[str, Path(alias="wishId")],
) -> WishDetail:
    assert body.title is not None  # der Validator laesst nichts anderes durch
    wish = service.update_wish(
        session,
        authorization,
        wish_id,
        expected_version=expected_version,
        title=body.title,
    )
    response.headers["ETag"] = etag_for(wish.version)
    return _wish_detail(session, authorization, wish)


@router.delete(
    "/spaces/{spaceId}/wishes/{wishId}",
    status_code=http_status.HTTP_204_NO_CONTENT,
    response_class=Response,
    operation_id="deleteWish",
    responses=problem_responses(401, 404, 409, 422),
)
def delete_wish(
    authorization: Authorization,
    session: DbSession,
    expected_version: IfMatchVersion,
    wish_id: Annotated[str, Path(alias="wishId")],
) -> Response:
    service.delete_wish(
        session,
        authorization,
        wish_id,
        expected_version=expected_version,
    )
    return Response(status_code=http_status.HTTP_204_NO_CONTENT)
