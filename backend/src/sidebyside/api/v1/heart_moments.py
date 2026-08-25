"""HTTP-Vertrag fuer M2-HeartMoments."""

from __future__ import annotations

from datetime import date, datetime
from typing import Annotated, Self
from uuid import UUID

from fastapi import APIRouter, Path, Query, Response, status
from pydantic import ConfigDict, field_validator, model_validator

from sidebyside.api.concurrency import IfMatchVersion, etag_for
from sidebyside.api.deps import Authorization, DbSession
from sidebyside.api.errors import problem_responses
from sidebyside.api.schema import ApiModel
from sidebyside.authorization import ContentVisibility, visibility_of
from sidebyside.heart_moments import service
from sidebyside.heart_moments.models import HeartEmotion, HeartMoment
from sidebyside.identity.models import Account

router = APIRouter(tags=["heart-moments"])

ETAG_HEADERS = {
    "ETag": {
        "description": "Version der Ressource fuer den naechsten If-Match-Schreibzugriff.",
        "schema": {"type": "string"},
    }
}


class HeartMomentCreate(ApiModel):
    model_config = ConfigDict(extra="forbid")

    text: str
    emotion: HeartEmotion
    visibility: ContentVisibility
    happened_on: date

    @field_validator("text")
    @classmethod
    def _text_not_blank(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("must not be blank")
        return cleaned


class HeartMomentUpdate(ApiModel):
    """Inhaltliche Aenderung.

    `visibility` fehlt hier bewusst: der Wechsel ist eine eigene Operation
    mit destruktiver Folge und darf nicht als Nebenwirkung eines
    Textupdates passieren.
    """

    model_config = ConfigDict(extra="forbid")

    text: str | None = None
    emotion: HeartEmotion | None = None
    happened_on: date | None = None

    @model_validator(mode="after")
    def _validate_patch(self) -> Self:
        if not self.model_fields_set:
            raise ValueError("at least one field must be supplied")
        if "text" in self.model_fields_set:
            if self.text is None or not self.text.strip():
                raise ValueError("text must not be null or blank")
            self.text = self.text.strip()
        if "emotion" in self.model_fields_set and self.emotion is None:
            raise ValueError("emotion must not be null")
        if "happened_on" in self.model_fields_set and self.happened_on is None:
            raise ValueError("happenedOn must not be null")
        return self


class HeartMomentVisibilityChange(ApiModel):
    model_config = ConfigDict(extra="forbid")

    visibility: ContentVisibility


class AuthorSummary(ApiModel):
    id: UUID
    display_name: str


class ResourceCapabilities(ApiModel):
    can_edit: bool
    can_delete: bool
    can_comment: bool


class HeartMomentDetail(ApiModel):
    id: UUID
    space_id: UUID
    author_id: UUID
    text: str
    emotion: HeartEmotion
    visibility: ContentVisibility
    happened_on: date
    version: int
    created_at: datetime
    updated_at: datetime
    author: AuthorSummary
    capabilities: ResourceCapabilities


class HeartMomentPage(ApiModel):
    items: list[HeartMomentDetail]
    next_cursor: str | None
    has_more: bool


def _heart_moment_detail(
    session: DbSession,
    authorization: Authorization,
    heart_moment: HeartMoment,
) -> HeartMomentDetail:
    author = session.get(Account, heart_moment.owner_id)
    if author is None:
        raise RuntimeError("Heart moment author disappeared despite foreign key protection.")
    is_author = heart_moment.owner_id == authorization.account_id
    visibility = visibility_of(heart_moment.privacy_class)
    return HeartMomentDetail(
        id=heart_moment.id,
        space_id=heart_moment.space_id,
        author_id=heart_moment.owner_id,
        text=heart_moment.payload.text,
        emotion=heart_moment.payload.emotion,
        visibility=visibility,
        happened_on=heart_moment.happened_on,
        version=heart_moment.version,
        created_at=heart_moment.created_at,
        updated_at=heart_moment.updated_at,
        author=AuthorSummary(id=author.id, display_name=author.display_name),
        capabilities=ResourceCapabilities(
            can_edit=is_author,
            can_delete=is_author,
            # Ein privater HeartMoment ist kein gemeinsamer Ort. Kommentare
            # gaebe es dort nur vom Owner an sich selbst - und ein spaeteres
            # Oeffnen wuerde sie sichtbar machen.
            can_comment=visibility is ContentVisibility.SHARED,
        ),
    )


@router.post(
    "/spaces/{spaceId}/heart-moments",
    response_model=HeartMomentDetail,
    status_code=status.HTTP_201_CREATED,
    operation_id="createHeartMoment",
    responses={201: {"headers": ETAG_HEADERS}, **problem_responses(401, 404, 422)},
)
def create_heart_moment(
    authorization: Authorization,
    session: DbSession,
    response: Response,
    body: HeartMomentCreate,
) -> HeartMomentDetail:
    heart_moment = service.create_heart_moment(
        session,
        authorization,
        text=body.text,
        emotion=body.emotion,
        visibility=body.visibility,
        happened_on=body.happened_on,
    )
    response.headers["ETag"] = etag_for(heart_moment.version)
    return _heart_moment_detail(session, authorization, heart_moment)


@router.get(
    "/spaces/{spaceId}/heart-moments",
    response_model=HeartMomentPage,
    operation_id="listHeartMoments",
    responses=problem_responses(400, 401, 404, 422),
)
def list_heart_moments(
    authorization: Authorization,
    session: DbSession,
    cursor: Annotated[str | None, Query()] = None,
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
    visibility: Annotated[ContentVisibility | None, Query()] = None,
) -> HeartMomentPage:
    page = service.list_heart_moments(
        session,
        authorization,
        cursor=cursor,
        limit=limit,
        visibility=visibility,
    )
    return HeartMomentPage(
        items=[
            _heart_moment_detail(session, authorization, heart_moment)
            for heart_moment in page.items
        ],
        next_cursor=page.next_cursor,
        has_more=page.has_more,
    )


@router.get(
    "/spaces/{spaceId}/heart-moments/{heartMomentId}",
    response_model=HeartMomentDetail,
    operation_id="getHeartMoment",
    responses={200: {"headers": ETAG_HEADERS}, **problem_responses(401, 404)},
)
def get_heart_moment(
    authorization: Authorization,
    session: DbSession,
    response: Response,
    heart_moment_id: Annotated[str, Path(alias="heartMomentId")],
) -> HeartMomentDetail:
    heart_moment = service.get_heart_moment(session, authorization, heart_moment_id)
    response.headers["ETag"] = etag_for(heart_moment.version)
    return _heart_moment_detail(session, authorization, heart_moment)


@router.patch(
    "/spaces/{spaceId}/heart-moments/{heartMomentId}",
    response_model=HeartMomentDetail,
    operation_id="updateHeartMoment",
    responses={
        200: {"headers": ETAG_HEADERS},
        **problem_responses(401, 403, 404, 409, 422),
    },
)
def update_heart_moment(
    authorization: Authorization,
    session: DbSession,
    response: Response,
    body: HeartMomentUpdate,
    expected_version: IfMatchVersion,
    heart_moment_id: Annotated[str, Path(alias="heartMomentId")],
) -> HeartMomentDetail:
    heart_moment = service.update_heart_moment(
        session,
        authorization,
        heart_moment_id,
        expected_version=expected_version,
        changed_fields=frozenset(body.model_fields_set),
        text=body.text,
        emotion=body.emotion,
        happened_on=body.happened_on,
    )
    response.headers["ETag"] = etag_for(heart_moment.version)
    return _heart_moment_detail(session, authorization, heart_moment)


@router.patch(
    "/spaces/{spaceId}/heart-moments/{heartMomentId}/visibility",
    response_model=HeartMomentDetail,
    operation_id="changeHeartMomentVisibility",
    responses={
        200: {"headers": ETAG_HEADERS},
        **problem_responses(401, 403, 404, 409, 422),
    },
)
def change_heart_moment_visibility(
    authorization: Authorization,
    session: DbSession,
    response: Response,
    body: HeartMomentVisibilityChange,
    expected_version: IfMatchVersion,
    heart_moment_id: Annotated[str, Path(alias="heartMomentId")],
) -> HeartMomentDetail:
    heart_moment = service.change_visibility(
        session,
        authorization,
        heart_moment_id,
        expected_version=expected_version,
        visibility=body.visibility,
    )
    response.headers["ETag"] = etag_for(heart_moment.version)
    return _heart_moment_detail(session, authorization, heart_moment)


@router.delete(
    "/spaces/{spaceId}/heart-moments/{heartMomentId}",
    status_code=status.HTTP_204_NO_CONTENT,
    response_class=Response,
    operation_id="deleteHeartMoment",
    responses=problem_responses(401, 403, 404, 409, 422),
)
def delete_heart_moment(
    authorization: Authorization,
    session: DbSession,
    expected_version: IfMatchVersion,
    heart_moment_id: Annotated[str, Path(alias="heartMomentId")],
) -> Response:
    service.delete_heart_moment(
        session,
        authorization,
        heart_moment_id,
        expected_version=expected_version,
    )
    return Response(status_code=status.HTTP_204_NO_CONTENT)
