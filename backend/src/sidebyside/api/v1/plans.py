"""HTTP-Vertrag fuer M3-Plans und den Wish->Plan-Lifecycle.

Die Konvertierung haengt im Pfad unter `/wishes/{wishId}/plan`, steht aber
hier: sie erzeugt einen Plan, und ihre Antwort traegt beide Ressourcen.
Umgekehrt waere `api.v1.wishes` auf dieses Modul angewiesen - und damit
haetten sich beide gegenseitig importiert. Die Richtung folgt der
Fachlichkeit: Plan kennt Wish, Wish kennt Plan nicht.
"""

from __future__ import annotations

from datetime import date, datetime
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
from sidebyside.api.v1.wishes import ETAG_HEADERS, WishDetail, wish_detail
from sidebyside.identity.models import Account
from sidebyside.plans import service
from sidebyside.plans.models import Plan, PlanStatus

router = APIRouter(tags=["plans"])


class PlanCreate(ApiModel):
    """Direct Plan Create nach M3-D30.

    `status`, `sourceWishId` und alle Termine fehlen bewusst. Ein Plan
    beginnt als Idee; terminiert wird er ueber `/schedule`, abgeschlossen
    ueber `/complete`.
    """

    model_config = ConfigDict(extra="forbid")

    title: str
    description: str | SkipJsonSchema[None] = None

    @field_validator("title")
    @classmethod
    def _title_not_blank(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("must not be blank")
        return cleaned

    @field_validator("description")
    @classmethod
    def _description_not_null(cls, value: str | None) -> str:
        if value is None:
            raise ValueError("description must not be null")
        return value


class PlanUpdate(ApiModel):
    """Fachliche Korrektur ohne Statuswirkung.

    `status`, `plannedStart` und `plannedEnd` sind hier nicht vorgesehen -
    sie gehoeren den Lifecycle-Operationen. `experiencedOn` ist die eine
    Ausnahme: es darf auf einem abgeschlossenen Plan korrigiert werden,
    ohne dass daraus eine Rueckoeffnung wird (M3-D04).
    """

    model_config = ConfigDict(extra="forbid")

    title: str | SkipJsonSchema[None] = None
    description: str | None = None
    experienced_on: date | SkipJsonSchema[None] = None

    @model_validator(mode="after")
    def _validate_patch(self) -> Self:
        if not self.model_fields_set:
            raise ValueError("at least one field must be supplied")
        if "title" in self.model_fields_set:
            if self.title is None or not self.title.strip():
                raise ValueError("title must not be null or blank")
            self.title = self.title.strip()
        if "experienced_on" in self.model_fields_set and self.experienced_on is None:
            raise ValueError("experiencedOn must not be null")
        return self


class PlanSchedule(ApiModel):
    model_config = ConfigDict(extra="forbid")

    planned_start: datetime
    planned_end: datetime | SkipJsonSchema[None] = None

    @field_validator("planned_end")
    @classmethod
    def _end_not_null(cls, value: datetime | None) -> datetime:
        if value is None:
            raise ValueError("plannedEnd must not be null")
        return value


class PlanComplete(ApiModel):
    model_config = ConfigDict(extra="forbid")

    experienced_on: date


class WishToPlan(ApiModel):
    """Der Konvertierungsrequest.

    Alle Felder optional: ohne eigenen Titel uebernimmt der Plan den des
    Wishes. `sourceWishId`, `status` und die Termine kommen nicht vom
    Client - der Wish steht im Pfad, alles andere entsteht serverseitig.
    """

    model_config = ConfigDict(extra="forbid")

    title: str | SkipJsonSchema[None] = None
    description: str | SkipJsonSchema[None] = None

    @field_validator("title")
    @classmethod
    def _title_not_blank(cls, value: str | None) -> str:
        if value is None or not value.strip():
            raise ValueError("title must not be null or blank")
        return value.strip()

    @field_validator("description")
    @classmethod
    def _description_not_null(cls, value: str | None) -> str:
        if value is None:
            raise ValueError("description must not be null")
        return value


class PlanDetail(ApiModel):
    id: UUID
    space_id: UUID
    created_by: UUID
    source_wish_id: UUID | None
    title: str
    description: str | None
    status: PlanStatus
    planned_start: datetime | None
    planned_end: datetime | None
    experienced_on: date | None
    version: int
    created_at: datetime
    updated_at: datetime
    creator: AuthorSummary
    capabilities: ResourceCapabilities


class PlanPage(ApiModel):
    items: list[PlanDetail]
    next_cursor: str | None
    has_more: bool


class WishToPlanResponse(ApiModel):
    """Beide Ressourcen in einer Antwort.

    Die Konvertierung veraendert den Wish und erzeugt den Plan. Ein Client,
    der nur eines von beidem zurueckbekaeme, muesste das andere sofort
    nachladen - und haette bis dahin einen veralteten Stand angezeigt.
    """

    wish: WishDetail
    plan: PlanDetail


class PlanReturnToWishResponse(ApiModel):
    wish: WishDetail
    removed_plan_id: UUID


def _plan_detail(
    session: DbSession,
    authorization: Authorization,
    plan: Plan,
) -> PlanDetail:
    creator = session.get(Account, plan.owner_id)
    if creator is None:
        raise RuntimeError("Plan creator disappeared despite foreign key protection.")
    is_completed = plan.status == PlanStatus.COMPLETED.value
    return PlanDetail(
        id=plan.id,
        space_id=plan.space_id,
        created_by=plan.owner_id,
        source_wish_id=plan.source_wish_id,
        title=plan.payload.title,
        description=plan.payload.description,
        status=PlanStatus(plan.status),
        planned_start=plan.planned_start,
        planned_end=plan.planned_end,
        experienced_on=plan.experienced_on,
        version=plan.version,
        created_at=plan.created_at,
        updated_at=plan.updated_at,
        creator=AuthorSummary(id=creator.id, display_name=creator.display_name),
        capabilities=ResourceCapabilities(
            # M3-D01: beide Partner, unabhaengig von `createdBy`.
            can_edit=True,
            # M3-D05: ein nicht abgeschlossener source Plan wird
            # zurueckgefuehrt, nicht geloescht.
            can_delete=plan.source_wish_id is None or is_completed,
            can_comment=False,
        ),
    )


@router.post(
    "/spaces/{spaceId}/plans",
    response_model=PlanDetail,
    status_code=http_status.HTTP_201_CREATED,
    operation_id="createPlan",
    responses={201: {"headers": ETAG_HEADERS}, **problem_responses(401, 404, 422)},
)
def create_plan(
    authorization: Authorization,
    session: DbSession,
    response: Response,
    body: PlanCreate,
) -> PlanDetail:
    plan = service.create_plan(
        session,
        authorization,
        title=body.title,
        description=body.description,
    )
    response.headers["ETag"] = etag_for(plan.version)
    return _plan_detail(session, authorization, plan)


@router.get(
    "/spaces/{spaceId}/plans",
    response_model=PlanPage,
    operation_id="listPlans",
    responses=problem_responses(400, 401, 404, 422),
)
def list_plans(
    authorization: Authorization,
    session: DbSession,
    cursor: Annotated[str | None, Query()] = None,
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
    status: Annotated[PlanStatus | None, Query()] = None,
) -> PlanPage:
    page = service.list_plans(
        session,
        authorization,
        cursor=cursor,
        limit=limit,
        status=status,
    )
    return PlanPage(
        items=[_plan_detail(session, authorization, plan) for plan in page.items],
        next_cursor=page.next_cursor,
        has_more=page.has_more,
    )


@router.get(
    "/spaces/{spaceId}/plans/{planId}",
    response_model=PlanDetail,
    operation_id="getPlan",
    responses={200: {"headers": ETAG_HEADERS}, **problem_responses(401, 404)},
)
def get_plan(
    authorization: Authorization,
    session: DbSession,
    response: Response,
    plan_id: Annotated[str, Path(alias="planId")],
) -> PlanDetail:
    plan = service.get_plan(session, authorization, plan_id)
    response.headers["ETag"] = etag_for(plan.version)
    return _plan_detail(session, authorization, plan)


@router.patch(
    "/spaces/{spaceId}/plans/{planId}",
    response_model=PlanDetail,
    operation_id="updatePlan",
    responses={200: {"headers": ETAG_HEADERS}, **problem_responses(401, 404, 409, 422)},
)
def update_plan(
    authorization: Authorization,
    session: DbSession,
    response: Response,
    body: PlanUpdate,
    expected_version: IfMatchVersion,
    plan_id: Annotated[str, Path(alias="planId")],
) -> PlanDetail:
    plan = service.update_plan(
        session,
        authorization,
        plan_id,
        expected_version=expected_version,
        changed_fields=frozenset(body.model_fields_set),
        title=body.title,
        description=body.description,
        experienced_on=body.experienced_on,
    )
    response.headers["ETag"] = etag_for(plan.version)
    return _plan_detail(session, authorization, plan)


@router.delete(
    "/spaces/{spaceId}/plans/{planId}",
    status_code=http_status.HTTP_204_NO_CONTENT,
    response_class=Response,
    operation_id="deletePlan",
    responses=problem_responses(401, 404, 409, 422),
)
def delete_plan(
    authorization: Authorization,
    session: DbSession,
    expected_version: IfMatchVersion,
    plan_id: Annotated[str, Path(alias="planId")],
) -> Response:
    service.delete_plan(
        session,
        authorization,
        plan_id,
        expected_version=expected_version,
    )
    return Response(status_code=http_status.HTTP_204_NO_CONTENT)


@router.post(
    "/spaces/{spaceId}/plans/{planId}/schedule",
    response_model=PlanDetail,
    operation_id="schedulePlan",
    responses={200: {"headers": ETAG_HEADERS}, **problem_responses(401, 404, 409, 422)},
)
def schedule_plan(
    authorization: Authorization,
    session: DbSession,
    response: Response,
    body: PlanSchedule,
    expected_version: IfMatchVersion,
    plan_id: Annotated[str, Path(alias="planId")],
) -> PlanDetail:
    plan = service.schedule_plan(
        session,
        authorization,
        plan_id,
        expected_version=expected_version,
        planned_start=body.planned_start,
        planned_end=body.planned_end,
    )
    response.headers["ETag"] = etag_for(plan.version)
    return _plan_detail(session, authorization, plan)


@router.post(
    "/spaces/{spaceId}/plans/{planId}/unschedule",
    response_model=PlanDetail,
    operation_id="unschedulePlan",
    responses={200: {"headers": ETAG_HEADERS}, **problem_responses(401, 404, 409, 422)},
)
def unschedule_plan(
    authorization: Authorization,
    session: DbSession,
    response: Response,
    expected_version: IfMatchVersion,
    plan_id: Annotated[str, Path(alias="planId")],
) -> PlanDetail:
    plan = service.unschedule_plan(
        session,
        authorization,
        plan_id,
        expected_version=expected_version,
    )
    response.headers["ETag"] = etag_for(plan.version)
    return _plan_detail(session, authorization, plan)


@router.post(
    "/spaces/{spaceId}/plans/{planId}/complete",
    response_model=PlanDetail,
    operation_id="completePlan",
    responses={200: {"headers": ETAG_HEADERS}, **problem_responses(401, 404, 409, 422)},
)
def complete_plan(
    authorization: Authorization,
    session: DbSession,
    response: Response,
    body: PlanComplete,
    expected_version: IfMatchVersion,
    plan_id: Annotated[str, Path(alias="planId")],
) -> PlanDetail:
    plan, _wish = service.complete_plan(
        session,
        authorization,
        plan_id,
        expected_version=expected_version,
        experienced_on=body.experienced_on,
    )
    response.headers["ETag"] = etag_for(plan.version)
    return _plan_detail(session, authorization, plan)


@router.post(
    "/spaces/{spaceId}/plans/{planId}/return-to-wish",
    response_model=PlanReturnToWishResponse,
    operation_id="returnPlanToWish",
    responses={200: {"headers": ETAG_HEADERS}, **problem_responses(401, 404, 409, 422)},
)
def return_plan_to_wish(
    authorization: Authorization,
    session: DbSession,
    response: Response,
    expected_version: IfMatchVersion,
    plan_id: Annotated[str, Path(alias="planId")],
) -> PlanReturnToWishResponse:
    result = service.return_to_wish(
        session,
        authorization,
        plan_id,
        expected_version=expected_version,
    )
    # Das ETag gehoert zum Wish: der Plan existiert nicht mehr, und der
    # naechste Schreibzugriff des Clients kann sich nur auf ihn beziehen.
    response.headers["ETag"] = etag_for(result.wish.version)
    return PlanReturnToWishResponse(
        wish=wish_detail(session, authorization, result.wish),
        removed_plan_id=result.removed_plan_id,
    )


@router.post(
    "/spaces/{spaceId}/wishes/{wishId}/plan",
    response_model=WishToPlanResponse,
    status_code=http_status.HTTP_201_CREATED,
    operation_id="convertWishToPlan",
    responses={
        200: {
            "description": (
                "Der Wish war bereits konvertiert. Die Antwort traegt denselben "
                "originaeren Plan; ein zweiter Plan entsteht nicht."
            ),
            "headers": ETAG_HEADERS,
        },
        201: {"headers": ETAG_HEADERS},
        **problem_responses(401, 404, 409, 422),
    },
)
def convert_wish_to_plan(
    authorization: Authorization,
    session: DbSession,
    response: Response,
    body: WishToPlan,
    expected_version: IfMatchVersion,
    wish_id: Annotated[str, Path(alias="wishId")],
) -> WishToPlanResponse:
    result = service.convert_wish_to_plan(
        session,
        authorization,
        wish_id,
        expected_version=expected_version,
        title=body.title,
        description=body.description,
    )
    if not result.created:
        response.status_code = http_status.HTTP_200_OK
    response.headers["ETag"] = etag_for(result.plan.version)
    return WishToPlanResponse(
        wish=wish_detail(session, authorization, result.wish),
        plan=_plan_detail(session, authorization, result.plan),
    )
