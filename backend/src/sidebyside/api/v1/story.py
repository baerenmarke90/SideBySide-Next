"""HTTP-Vertrag fuer die Story-Zeitleiste.

Die Route liefert ausschliesslich gemeinsamen Inhalt. Nach M2-D22 gibt es
hier keine `PRIVATE`-Variante, keinen `visibility`-Parameter und keinen
Owner-Modus: der Owner-Bereich fuer private HeartMoments ist eine eigene
Ansicht ueber die HeartMoment-Collection.
"""

from __future__ import annotations

from collections.abc import Iterable
from datetime import date, datetime
from typing import Annotated, Literal
from uuid import UUID

from fastapi import APIRouter, Query
from pydantic import Field, RootModel
from sqlalchemy import select

from sidebyside.api.deps import Authorization, DbSession
from sidebyside.api.errors import problem_responses
from sidebyside.api.schema import ApiModel, AuthorSummary, ResourceCapabilities
from sidebyside.api.v1.attachments import AttachmentSummary
from sidebyside.api.v1.memories import MemoryAttachmentSummary
from sidebyside.attachments import binding
from sidebyside.attachments.models import Attachment, MediaType
from sidebyside.authorization import readable
from sidebyside.heart_moments.models import HeartEmotion, HeartMoment
from sidebyside.identity.models import Account
from sidebyside.memories.models import Memory
from sidebyside.milestones.models import Milestone
from sidebyside.story import service
from sidebyside.story.service import StoryKind, StoryOrder, StoryRow

router = APIRouter(tags=["story"])


class MemorySummary(ApiModel):
    """Eine Memory als Karte der Zeitleiste.

    Ohne `body`: die Karte braucht eine Ueberschrift und ihre Bilder, und
    eine Seite mit hundert vollstaendigen Texten waere die Antwort, die
    niemand angefordert hat. Der Text steht in der Detailansicht.
    """

    id: UUID
    title: str
    happened_on: date | None
    created_at: datetime
    author: AuthorSummary
    capabilities: ResourceCapabilities
    attachments: list[MemoryAttachmentSummary]


class SharedHeartMomentSummary(ApiModel):
    """Ein gemeinsamer HeartMoment. Eine private Variante gibt es nicht."""

    id: UUID
    text: str
    emotion: HeartEmotion
    happened_on: date
    created_at: datetime
    author: AuthorSummary
    capabilities: ResourceCapabilities
    attachment: AttachmentSummary | None


class MilestoneSummary(ApiModel):
    id: UUID
    title: str
    happened_on: date
    created_at: datetime
    author: AuthorSummary
    capabilities: ResourceCapabilities


class StoryMemoryItem(ApiModel):
    kind: Literal[StoryKind.MEMORY]
    effective_date: date
    memory: MemorySummary


class StoryHeartMomentItem(ApiModel):
    kind: Literal[StoryKind.HEART_MOMENT]
    effective_date: date
    heart_moment: SharedHeartMomentSummary


class StoryMilestoneItem(ApiModel):
    kind: Literal[StoryKind.MILESTONE]
    effective_date: date
    milestone: MilestoneSummary


StoryItemVariant = Annotated[
    StoryMemoryItem | StoryHeartMomentItem | StoryMilestoneItem,
    Field(discriminator="kind"),
]
"""`kind` unterscheidet die Varianten im Vertrag selbst.

Ein Client muss nicht raten, welches Feld gesetzt ist, und ein neuer Typ
kann spaeter additiv dazukommen, ohne die bestehenden zu veraendern."""


class StoryItem(RootModel[StoryItemVariant]):
    """Ein Eintrag der Zeitleiste, diskriminiert ueber `kind`.

    Ein eigener Typ und keine anonyme Union im Listenfeld: sonst benennt
    der OpenAPI-Vertrag sie nach ihrem Fundort - `StoryPageItemsInner` -
    und jeder erzeugte Client traegt diesen Namen weiter. `API-DESIGN.md`
    nennt sie `StoryItem`, und das soll auch im Vertrag stehen.
    """

    root: StoryItemVariant


class StoryPage(ApiModel):
    items: list[StoryItem]
    next_cursor: str | None
    has_more: bool


def _autoren(session: DbSession, owner_ids: set[UUID]) -> dict[UUID, Account]:
    if not owner_ids:
        return {}
    zeilen = session.execute(select(Account).where(Account.id.in_(owner_ids))).scalars().all()
    return {konto.id: konto for konto in zeilen}


def _capabilities(
    owner_id: UUID, authorization: Authorization, *, can_comment: bool = True
) -> ResourceCapabilities:
    ist_autor = owner_id == authorization.account_id
    return ResourceCapabilities(can_edit=ist_autor, can_delete=ist_autor, can_comment=can_comment)


def _attachment_summary(attachment: Attachment) -> AttachmentSummary:
    return AttachmentSummary(
        id=attachment.id,
        status="READY",
        media_type=MediaType(attachment.media_type),
        mime_type=attachment.mime_type,
        size=attachment.size,
        width=attachment.width,
        height=attachment.height,
        has_thumbnail=attachment.has_thumbnail,
    )


@router.get(
    "/spaces/{spaceId}/timeline",
    response_model=StoryPage,
    operation_id="getStoryTimeline",
    responses=problem_responses(400, 401, 404, 422),
)
def get_story_timeline(
    authorization: Authorization,
    session: DbSession,
    type: Annotated[list[StoryKind] | None, Query()] = None,
    year: Annotated[int | None, Query(ge=service.MIN_YEAR, le=service.MAX_YEAR)] = None,
    order: Annotated[StoryOrder, Query()] = StoryOrder.DESC,
    cursor: Annotated[str | None, Query()] = None,
    limit: Annotated[int, Query(ge=1, le=service.MAX_LIMIT)] = service.DEFAULT_LIMIT,
) -> StoryPage:
    """Die gemeinsame Zeitleiste aus Memories, Milestones und HeartMoments.

    Private HeartMoments erscheinen hier nie - auch nicht fuer ihren Owner.
    """
    seite = service.read_timeline(
        session,
        authorization,
        kinds=tuple(type or ()),
        year=year,
        order=order,
        cursor=cursor,
        limit=limit,
    )
    return StoryPage(
        items=_projizieren(session, authorization, seite.items),
        next_cursor=seite.next_cursor,
        has_more=seite.has_more,
    )


def _projizieren(
    session: DbSession,
    authorization: Authorization,
    items: list[StoryRow],
) -> list[StoryItem]:
    """Die Seite in DTOs uebersetzen - gebuendelt, nicht Zeile fuer Zeile.

    Die Abfrage hat nur Schluessel geliefert. Hier werden je Typ genau eine
    Abfrage fuer die Objekte, eine fuer die Autoren und eine fuer die
    Galerien abgesetzt. Einzeln waeren es bei hundert Items mehrere hundert.

    Geladen wird wieder ueber `readable()`. Das ist keine doppelte Pruefung
    aus Misstrauen gegen die eigene Abfrage, sondern die Regel, dass keine
    Zeile dieses Systems ohne Sichtbarkeitsbedingung gelesen wird.
    """
    ids_je_kind: dict[StoryKind, list[UUID]] = {kind: [] for kind in StoryKind}
    for item in items:
        ids_je_kind[item.kind].append(item.id)

    memories = _laden(session, authorization, Memory, ids_je_kind[StoryKind.MEMORY])
    heart_moments = _laden(session, authorization, HeartMoment, ids_je_kind[StoryKind.HEART_MOMENT])
    milestones = _laden(session, authorization, Milestone, ids_je_kind[StoryKind.MILESTONE])

    galerien = binding.attachments_of_memories(session, list(memories))
    anhaenge = _anhaenge(session, heart_moments.values())
    autoren = _autoren(
        session,
        {
            eintrag.owner_id
            for quelle in (memories, heart_moments, milestones)
            for eintrag in quelle.values()
        },
    )

    ansicht: list[StoryItemVariant] = []
    for item in items:
        if item.kind is StoryKind.MEMORY:
            memory = memories.get(item.id)
            if memory is None:
                continue
            ansicht.append(
                StoryMemoryItem(
                    kind=StoryKind.MEMORY,
                    effective_date=item.effective_date,
                    memory=MemorySummary(
                        id=memory.id,
                        title=memory.payload.title,
                        happened_on=memory.happened_on,
                        created_at=memory.created_at,
                        author=_autor(autoren, memory.owner_id),
                        capabilities=_capabilities(memory.owner_id, authorization),
                        attachments=[
                            MemoryAttachmentSummary(
                                **_attachment_summary(gebunden.attachment).model_dump(),
                                position=gebunden.position,
                            )
                            for gebunden in galerien.get(memory.id, [])
                        ],
                    ),
                )
            )
        elif item.kind is StoryKind.HEART_MOMENT:
            heart_moment = heart_moments.get(item.id)
            if heart_moment is None:
                continue
            ansicht.append(
                StoryHeartMomentItem(
                    kind=StoryKind.HEART_MOMENT,
                    effective_date=item.effective_date,
                    heart_moment=SharedHeartMomentSummary(
                        id=heart_moment.id,
                        text=heart_moment.payload.text,
                        emotion=heart_moment.payload.emotion,
                        happened_on=heart_moment.happened_on,
                        created_at=heart_moment.created_at,
                        author=_autor(autoren, heart_moment.owner_id),
                        capabilities=_capabilities(heart_moment.owner_id, authorization),
                        attachment=(
                            _attachment_summary(anhaenge[heart_moment.attachment_id])
                            if heart_moment.attachment_id in anhaenge
                            else None
                        ),
                    ),
                )
            )
        else:
            milestone = milestones.get(item.id)
            if milestone is None:
                continue
            ansicht.append(
                StoryMilestoneItem(
                    kind=StoryKind.MILESTONE,
                    effective_date=item.effective_date,
                    milestone=MilestoneSummary(
                        id=milestone.id,
                        title=milestone.payload.title,
                        happened_on=milestone.happened_on,
                        created_at=milestone.created_at,
                        author=_autor(autoren, milestone.owner_id),
                        capabilities=_capabilities(milestone.owner_id, authorization),
                    ),
                )
            )
    # Die Varianten entstehen einzeln und werden erst hier in den
    # benannten Vertragstyp gehuellt.
    return [StoryItem(root=eintrag) for eintrag in ansicht]


def _laden[ResourceT: (Memory, HeartMoment, Milestone)](
    session: DbSession,
    authorization: Authorization,
    model: type[ResourceT],
    ids: list[UUID],
) -> dict[UUID, ResourceT]:
    if not ids:
        return {}
    zeilen = (
        session.execute(readable(model, authorization).where(model.id.in_(ids))).scalars().all()
    )
    return {zeile.id: zeile for zeile in zeilen}


def _anhaenge(session: DbSession, heart_moments: Iterable[HeartMoment]) -> dict[UUID, Attachment]:
    ids = {
        heart_moment.attachment_id
        for heart_moment in heart_moments
        if heart_moment.attachment_id is not None
    }
    if not ids:
        return {}
    zeilen = session.execute(select(Attachment).where(Attachment.id.in_(ids))).scalars().all()
    return {attachment.id: attachment for attachment in zeilen}


def _autor(autoren: dict[UUID, Account], owner_id: UUID) -> AuthorSummary:
    konto = autoren.get(owner_id)
    if konto is None:
        raise RuntimeError("Story author disappeared despite foreign key protection.")
    return AuthorSummary(id=konto.id, display_name=konto.display_name)
