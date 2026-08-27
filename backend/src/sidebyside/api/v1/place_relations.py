"""HTTP-Vertrag fuer typisierte M3-Content-Relations.

M3-D08 entscheidet Option A aus `docs/m3/API-DESIGN.md`: verschachtelte
Routen je Zieltyp, kein gemeinsamer Relation-Endpunkt mit Discriminator.
Der Zieltyp steht damit im Pfad und nicht im Body - ein Client kann keinen
Typ benennen, den der Vertrag nicht schon kennt, und die OpenAPI-Typen
bleiben ohne Union.

Die Routen entstehen ueber `_register`, weil sie sich ausser im Zieltyp
nicht unterscheiden. Registriert werden trotzdem feste Pfade und feste
`operation_id`s: das erzeugte Schema ist Zeichen fuer Zeichen dasselbe wie
bei neun ausgeschriebenen Funktionen, nur ohne neun Gelegenheiten, eine
davon anders zu machen als die anderen.

`PUT` ist idempotent und antwortet immer `204`. Ob die Relation eben
entstanden ist oder schon bestand, ist fuer den Aufrufer kein Unterschied,
und ein `201` gegen ein `200` waere hier eine Auskunft darueber, was ein
anderes Geraet kurz zuvor getan hat.
"""

from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Path, Response, status

from sidebyside.api.deps import Authorization, DbSession
from sidebyside.api.errors import problem_responses
from sidebyside.api.schema import ApiModel
from sidebyside.relations import service
from sidebyside.relations.service import RelationKind

router = APIRouter(tags=["place-relations"])


class RelationTargets(ApiModel):
    """Die verknuepften Ziele eines Ortes.

    Ausschliesslich IDs. Inhalte kommen ueber die Route der jeweiligen
    Domaene und damit durch deren eigenen Guard; eine Relationsliste, die
    Inhalte mitliefert, waere ein zweiter Leseweg mit eigener
    Autorisierung.
    """

    items: list[UUID]


def _register(kind: RelationKind, *, singular: str, plural: str) -> None:
    """Die drei Routen einer Relationsart anlegen.

    `singular`/`plural` sind die Namensteile der `operation_id` - sie
    landen in den generierten Clients und werden deshalb ausgeschrieben
    uebergeben statt aus dem Slug abgeleitet.
    """
    collection = f"/spaces/{{spaceId}}/places/{{placeId}}/{kind.slug}"
    item = f"{collection}/{{targetId}}"

    @router.get(
        collection,
        response_model=RelationTargets,
        operation_id=f"listPlace{plural}",
        responses=problem_responses(401, 404),
        name=f"list_place_{kind.slug}",
    )
    def list_targets(
        authorization: Authorization,
        session: DbSession,
        place_id: Annotated[str, Path(alias="placeId")],
    ) -> RelationTargets:
        return RelationTargets(
            items=list(service.list_targets(session, authorization, place_id, kind))
        )

    @router.put(
        item,
        status_code=status.HTTP_204_NO_CONTENT,
        response_class=Response,
        operation_id=f"linkPlace{singular}",
        responses=problem_responses(401, 404),
        name=f"link_place_{kind.slug}",
    )
    def link(
        authorization: Authorization,
        session: DbSession,
        place_id: Annotated[str, Path(alias="placeId")],
        target_id: Annotated[str, Path(alias="targetId")],
    ) -> Response:
        service.link(session, authorization, place_id, target_id, kind)
        return Response(status_code=status.HTTP_204_NO_CONTENT)

    @router.delete(
        item,
        status_code=status.HTTP_204_NO_CONTENT,
        response_class=Response,
        operation_id=f"unlinkPlace{singular}",
        responses=problem_responses(401, 404),
        name=f"unlink_place_{kind.slug}",
    )
    def unlink(
        authorization: Authorization,
        session: DbSession,
        place_id: Annotated[str, Path(alias="placeId")],
        target_id: Annotated[str, Path(alias="targetId")],
    ) -> Response:
        service.unlink(session, authorization, place_id, target_id, kind)
        return Response(status_code=status.HTTP_204_NO_CONTENT)


_register(service.PLACE_MEMORIES, singular="Memory", plural="Memories")
_register(service.PLACE_HEART_MOMENTS, singular="HeartMoment", plural="HeartMoments")
_register(service.PLACE_MILESTONES, singular="Milestone", plural="Milestones")
