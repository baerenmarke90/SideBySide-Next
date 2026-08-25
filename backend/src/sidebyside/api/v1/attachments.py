"""HTTP-Vertrag fuer M2-Attachments."""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Annotated, Literal, Self
from uuid import UUID

from fastapi import APIRouter, Path, Request, Response, status
from fastapi.responses import StreamingResponse
from pydantic import ConfigDict, Field, model_validator

from sidebyside.api.concurrency import IfMatchVersion, etag_for
from sidebyside.api.deps import Authorization, DbSession
from sidebyside.api.errors import problem_responses
from sidebyside.api.schema import ApiModel
from sidebyside.attachments import service
from sidebyside.attachments.models import Attachment, AttachmentStatus, MediaType
from sidebyside.core.clock import now
from sidebyside.media import create_signed_upload, get_media_store

router = APIRouter(tags=["attachments"])

STREAM_CHUNK = 64 * 1024
SIGNED_UPLOAD_TTL = timedelta(minutes=10)
SIGNED_READ_TTL = timedelta(minutes=5)

_PUBLIC_STATUS: dict[str, str] = {
    AttachmentStatus.PENDING.value: "PENDING",
    AttachmentStatus.UPLOADING.value: "PENDING",
    AttachmentStatus.VALIDATING.value: "PROCESSING",
    AttachmentStatus.READY.value: "READY",
    AttachmentStatus.FAILED.value: "FAILED",
}
"""Die oeffentliche Projektion aus API-DESIGN.

`DELETING` und `DELETE_FAILED` fehlen absichtlich: ein geloeschtes
Attachment ist fachlich nicht mehr da und wird gar nicht erst ausgeliefert.
"""


class AttachmentUploadCreate(ApiModel):
    model_config = ConfigDict(extra="forbid")

    media_type: MediaType
    original_name: str = Field(min_length=1, max_length=255)
    expected_mime_type: str = Field(min_length=1, max_length=128)
    expected_size: int = Field(gt=0)


class AttachmentFinalize(ApiModel):
    """Leer nach Vertrag - Finalize traegt keine Clientangaben.

    Was der Server ueber die Datei wissen muss, stellt er selbst fest.
    """

    model_config = ConfigDict(extra="forbid")


class AttachmentReadRequest(ApiModel):
    model_config = ConfigDict(extra="forbid")

    parent_type: Literal["MEMORY", "HEART_MOMENT", "NONE"] = "NONE"
    parent_id: UUID | None = None

    @model_validator(mode="after")
    def _validate_target(self) -> Self:
        if self.parent_type == "NONE":
            if self.parent_id is not None:
                raise ValueError("parentId must be omitted for parentType NONE")
        elif self.parent_id is None:
            raise ValueError("parentId is required for this parentType")
        return self


class AttachmentDetail(ApiModel):
    id: UUID
    status: str
    media_type: MediaType
    mime_type: str | None
    size: int | None
    width: int | None
    height: int | None
    duration_seconds: int | None
    has_thumbnail: bool
    version: int
    created_at: datetime


class AttachmentSummary(ApiModel):
    """Die Projektion eines gebundenen Attachments an seinem Parent.

    Ein Typ und nicht je Domaene einer: zwei gleichnamige DTOs haetten im
    OpenAPI-Vertrag modulqualifizierte Namen erzeugt und damit interne
    Pfade nach aussen getragen.
    """

    id: UUID
    status: str
    media_type: MediaType
    mime_type: str | None
    size: int | None
    width: int | None
    height: int | None
    has_thumbnail: bool


class UploadDescriptor(ApiModel):
    attachment: AttachmentDetail
    method: Literal["STREAM", "SIGNED_UPLOAD"]
    upload_url: str
    expires_at: datetime | None = None
    required_headers: dict[str, str]


class ReadDescriptor(ApiModel):
    method: Literal["STREAM", "SIGNED_URL"]
    url: str
    expires_at: datetime | None = None


def _detail(attachment: Attachment) -> AttachmentDetail:
    return AttachmentDetail(
        id=attachment.id,
        status=_PUBLIC_STATUS.get(attachment.status, "PROCESSING"),
        media_type=MediaType(attachment.media_type),
        mime_type=attachment.mime_type,
        size=attachment.size,
        width=attachment.width,
        height=attachment.height,
        duration_seconds=attachment.duration_seconds,
        has_thumbnail=attachment.has_thumbnail,
        version=attachment.version,
        created_at=attachment.created_at,
    )


def _content_path(space_id: UUID, attachment_id: UUID) -> str:
    return f"/api/v1/spaces/{space_id}/attachments/{attachment_id}/content"


def _no_store(response: Response) -> None:
    # Descriptor-Antworten koennen Bearer-Capabilities enthalten. Weder der
    # Browsercache noch ein vorgeschalteter Cache darf sie dauerhaft halten.
    response.headers["Cache-Control"] = "private, no-store"
    response.headers["Referrer-Policy"] = "no-referrer"


@router.post(
    "/spaces/{spaceId}/attachments",
    response_model=UploadDescriptor,
    status_code=status.HTTP_201_CREATED,
    operation_id="createAttachmentUpload",
    responses=problem_responses(401, 404, 413, 415, 422),
)
def create_attachment_upload(
    authorization: Authorization,
    session: DbSession,
    response: Response,
    body: AttachmentUploadCreate,
) -> UploadDescriptor:
    attachment = service.create_upload(
        session,
        authorization,
        media_type=body.media_type,
        original_name=body.original_name,
        expected_mime_type=body.expected_mime_type,
        expected_size=body.expected_size,
    )
    _no_store(response)

    store = get_media_store()
    signed = create_signed_upload(
        store,
        service.storage_key_for(attachment),
        attachment.declared_mime_type,
        SIGNED_UPLOAD_TTL,
    )
    if signed is not None:
        return UploadDescriptor(
            attachment=_detail(attachment),
            method="SIGNED_UPLOAD",
            upload_url=signed.url,
            expires_at=now() + SIGNED_UPLOAD_TTL,
            required_headers=signed.required_headers,
        )

    return UploadDescriptor(
        attachment=_detail(attachment),
        method="STREAM",
        upload_url=_content_path(attachment.space_id, attachment.id),
        required_headers={"Content-Type": "application/octet-stream"},
    )


@router.put(
    "/spaces/{spaceId}/attachments/{attachmentId}/content",
    status_code=status.HTTP_204_NO_CONTENT,
    response_class=Response,
    operation_id="uploadAttachmentContent",
    responses=problem_responses(401, 403, 404, 409, 413, 415),
)
async def upload_attachment_content(
    authorization: Authorization,
    session: DbSession,
    request: Request,
    attachment_id: Annotated[str, Path(alias="attachmentId")],
) -> Response:
    """Die Bytes im Serverstream entgegennehmen (M2-D13, Local-Adapter).

    Zwei Dinge stehen hier bewusst in dieser Reihenfolge.

    Erst wird autorisiert, dann gelesen. Andernfalls entschiede ein
    beliebiger Absender darueber, wie viel der Server entgegennimmt, bevor
    feststeht, ob er ueberhaupt hochladen darf.

    Und gelesen wird gegen eine Grenze. `await request.body()` wuerde den
    ganzen Koerper puffern, wie gross er auch ist - die Media-Pipeline
    verlangt ausdruecklich kein unbegrenztes Puffern im RAM. Der Strom
    bricht deshalb bei der ersten Ueberschreitung ab, statt erst danach zu
    messen.
    """
    attachment, rule = service.open_upload(session, authorization, attachment_id)

    bloecke: list[bytes] = []
    gelesen = 0
    async for stueck in request.stream():
        gelesen += len(stueck)
        if gelesen > rule.max_size:
            raise service.too_large()
        bloecke.append(stueck)

    service.complete_upload(session, attachment, rule, b"".join(bloecke))
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post(
    "/spaces/{spaceId}/attachments/{attachmentId}/finalize",
    response_model=AttachmentDetail,
    status_code=status.HTTP_202_ACCEPTED,
    operation_id="finalizeAttachmentUpload",
    responses=problem_responses(401, 403, 404, 409, 422),
)
def finalize_attachment_upload(
    authorization: Authorization,
    session: DbSession,
    body: AttachmentFinalize,
    attachment_id: Annotated[str, Path(alias="attachmentId")],
) -> AttachmentDetail:
    del body
    attachment = service.finalize_upload(session, authorization, attachment_id)
    return _detail(attachment)


@router.get(
    "/spaces/{spaceId}/attachments/{attachmentId}",
    response_model=AttachmentDetail,
    operation_id="getAttachment",
    responses={
        200: {"headers": {"ETag": {"schema": {"type": "string"}}}},
        **problem_responses(401, 404),
    },
)
def get_attachment(
    authorization: Authorization,
    session: DbSession,
    response: Response,
    attachment_id: Annotated[str, Path(alias="attachmentId")],
) -> AttachmentDetail:
    attachment = service.get_attachment(session, authorization, attachment_id)
    response.headers["ETag"] = etag_for(attachment.version)
    return _detail(attachment)


@router.post(
    "/spaces/{spaceId}/attachments/{attachmentId}/read-access",
    response_model=ReadDescriptor,
    operation_id="createAttachmentReadAccess",
    responses=problem_responses(401, 403, 404, 409, 422),
)
def create_attachment_read_access(
    authorization: Authorization,
    session: DbSession,
    response: Response,
    body: AttachmentReadRequest,
    attachment_id: Annotated[str, Path(alias="attachmentId")],
) -> ReadDescriptor:
    attachment = service.authorize_read(
        session,
        authorization,
        attachment_id,
        service.ReadTarget.unbound()
        if body.parent_type == "NONE"
        else service.ReadTarget.parent(body.parent_type, body.parent_id),  # type: ignore[arg-type]
    )
    _no_store(response)

    store = get_media_store()
    signed_url = store.create_read_url(service.storage_key_for(attachment), SIGNED_READ_TTL)
    if signed_url is not None:
        return ReadDescriptor(
            method="SIGNED_URL",
            url=signed_url,
            expires_at=now() + SIGNED_READ_TTL,
        )

    return ReadDescriptor(
        method="STREAM",
        url=_content_path(attachment.space_id, attachment.id),
    )


@router.get(
    "/spaces/{spaceId}/attachments/{attachmentId}/content",
    operation_id="getAttachmentContent",
    response_class=StreamingResponse,
    responses=problem_responses(401, 403, 404, 409),
)
def get_attachment_content(
    authorization: Authorization,
    session: DbSession,
    attachment_id: Annotated[str, Path(alias="attachmentId")],
    variant: Literal["original", "thumbnail"] = "original",
) -> StreamingResponse:
    """Die autorisierte Streamingroute (Media-Pipeline, Abschnitt 9).

    Jeder Zugriff wird unmittelbar vor dem Oeffnen geprueft. Der zuvor
    ausgestellte ReadDescriptor ist kein Ausweis: er verkuerzt nichts und
    ersetzt diese Pruefung nicht.
    """
    attachment = service.authorize_read(
        session,
        authorization,
        attachment_id,
        service.ReadTarget.resolved_by_server(),
    )
    if variant == "thumbnail" and not attachment.has_thumbnail:
        raise Attachment.privacy_absence.error()

    quelle = service.open_content(attachment, variant=variant)
    typ = (
        "image/jpeg"
        if variant == "thumbnail"
        else (attachment.mime_type or "application/octet-stream")
    )

    def bloecke() -> object:
        try:
            while stueck := quelle.read(STREAM_CHUNK):
                yield stueck
        finally:
            quelle.close()

    return StreamingResponse(
        bloecke(),  # type: ignore[arg-type]
        media_type=typ,
        headers={
            # Kein Dateisystempfad und kein Benutzername im Header; der
            # Downloadname wird serverseitig kontrolliert.
            "Content-Disposition": f'inline; filename="{attachment.id}"',
            "Cache-Control": "private, no-store",
        },
    )


@router.delete(
    "/spaces/{spaceId}/attachments/{attachmentId}",
    status_code=status.HTTP_204_NO_CONTENT,
    response_class=Response,
    operation_id="deleteAttachment",
    responses=problem_responses(401, 403, 404, 409, 422),
)
def delete_attachment(
    authorization: Authorization,
    session: DbSession,
    expected_version: IfMatchVersion,
    attachment_id: Annotated[str, Path(alias="attachmentId")],
) -> Response:
    service.delete_attachment(
        session,
        authorization,
        attachment_id,
        expected_version=expected_version,
    )
    return Response(status_code=status.HTTP_204_NO_CONTENT)
