"""Die Story-Abfrage.

Drei Quelltypen, eine Sortierung, ein Cursor. Der Aufbau folgt M2-D08:
`effectiveDate = happenedOn ?? UTC_DATE(createdAt)` und der vollstaendige
Schluessel `(effectiveDate, createdAt, kindRank, id)`.

Zwei Dinge sind hier bewusst nicht formuliert, weil sie schon existieren:
die Sichtbarkeitsbedingung und die Cursor-Mechanik. Die Legs beginnen bei
`readable()` und tauschen nur die Spalten aus, statt die Bedingung ein
zweites Mal hinzuschreiben - der Ort, an dem sich ein Privacy-Filter sonst
schleichend unterscheidet. Signatur und Bindung des Cursors kommen aus
`core.cursor`, wie bei jeder anderen Collection auch.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, date, datetime
from enum import StrEnum
from typing import Any
from uuid import UUID

from sqlalchemy import Date, Select, cast, func, literal, select, tuple_, union_all
from sqlalchemy.orm import Session

from sidebyside.authorization import AuthorizationContext, PrivacyClass, readable
from sidebyside.core import cursor as cursor_codec
from sidebyside.heart_moments.models import HeartMoment
from sidebyside.memories.models import Memory
from sidebyside.milestones.models import Milestone

DEFAULT_LIMIT = 50
MAX_LIMIT = 100
MIN_YEAR = 1900
MAX_YEAR = 2100


class StoryKind(StrEnum):
    MEMORY = "MEMORY"
    HEART_MOMENT = "HEART_MOMENT"
    MILESTONE = "MILESTONE"


class StoryOrder(StrEnum):
    ASC = "ASC"
    DESC = "DESC"


_KIND_RANK: dict[StoryKind, int] = {
    StoryKind.MEMORY: 1,
    StoryKind.HEART_MOMENT: 2,
    StoryKind.MILESTONE: 3,
}
"""M2-D08. Der Rang gehoert zum Sortierschluessel und ist deshalb Vertrag,
kein Implementierungsdetail: er entscheidet bei gleichem Datum und gleicher
Erstellungszeit die Reihenfolge und damit den Cursor."""

type StoryModel = type[Memory] | type[HeartMoment] | type[Milestone]
"""Die drei Quelltypen namentlich statt als offene Basisklasse.

`PrivateResourceMixin` waere die allgemeinere Angabe, verliert aber
`happened_on`, `created_at` und `id` - und mit ihnen die Pruefung, dass
jeder Zweig der Union tatsaechlich denselben Schluessel liefert."""

_MODELS: dict[StoryKind, StoryModel] = {
    StoryKind.MEMORY: Memory,
    StoryKind.HEART_MOMENT: HeartMoment,
    StoryKind.MILESTONE: Milestone,
}


@dataclass(frozen=True)
class StoryItem:
    """Eine Zeile der Zeitleiste, noch ohne Projektion.

    Die Abfrage liefert absichtlich nur Schluessel und Identitaet. Die
    fachlichen Objekte werden danach gebuendelt geladen - sonst zoege eine
    Seite mit hundert Eintraegen dreihundert Einzelabfragen nach sich.
    """

    kind: StoryKind
    effective_date: date
    created_at: datetime
    id: UUID


@dataclass(frozen=True)
class StoryPageResult:
    items: list[StoryItem]
    next_cursor: str | None
    has_more: bool


def _effective_date(model: StoryModel) -> Any:
    """`happenedOn`, sonst der UTC-Kalendertag von `createdAt` (M2-D08).

    Die Regel steht einmal fuer alle drei Typen. Bei HeartMoment und
    Milestone ist `happened_on` nicht nullbar, dort ist das Coalesce ein
    No-op - aber ein gemeinsamer Ausdruck kann nicht auseinanderlaufen.
    """
    return func.coalesce(
        model.happened_on,
        cast(func.timezone("UTC", model.created_at), Date),
    )


def _leg(
    kind: StoryKind,
    context: AuthorizationContext,
    *,
    year: int | None,
) -> Select[Any]:
    """Ein Zweig der Union - autorisiert, bevor er Spalten waehlt.

    `with_only_columns` behaelt die WHERE-Bedingung aus `readable()` und
    tauscht nur die Projektion. Damit ist ausgeschlossen, dass die Story
    ihre eigene Sichtbarkeitsbedingung bekommt.
    """
    model = _MODELS[kind]
    datum = _effective_date(model)
    statement = readable(model, context).with_only_columns(
        literal(_KIND_RANK[kind]).label("kind_rank"),
        datum.label("effective_date"),
        model.created_at.label("created_at"),
        model.id.label("id"),
    )
    if kind is StoryKind.HEART_MOMENT:
        # M2-D22 und M2-D08: private HeartMoments sind niemals Story-Items,
        # auch nicht fuer ihren Owner. Der Ausschluss steht in der Abfrage
        # und nicht in der Projektion - sonst waeren sie gelesen, gezaehlt
        # und im Cursor beruecksichtigt worden, bevor jemand sie entfernt.
        statement = statement.where(model.privacy_class == PrivacyClass.SPACE_SHARED.value)
    if year is not None:
        statement = statement.where(
            datum >= date(year, 1, 1),
            datum <= date(year, 12, 31),
        )
    return statement


def _cursor_binding(
    context: AuthorizationContext,
    kinds: tuple[StoryKind, ...],
    year: int | None,
    order: StoryOrder,
) -> dict[str, Any]:
    """Woran ein Story-Cursor gebunden ist.

    `limit` fehlt hier bewusst: eine kleinere oder groessere Seite setzt an
    derselben Stelle fort. Alles, was die *Menge* oder ihre *Reihenfolge*
    veraendert, gehoert dagegen hinein - sonst waere der Cursor ein Zeiger
    in eine Liste, die es nicht mehr gibt.
    """
    return {
        "collection": "story",
        "spaceId": str(context.space_id),
        "kinds": [kind.value for kind in kinds],
        "year": year,
        "order": order.value,
    }


def _encode_cursor(
    *,
    context: AuthorizationContext,
    kinds: tuple[StoryKind, ...],
    year: int | None,
    order: StoryOrder,
    item: StoryItem,
) -> str:
    return cursor_codec.encode(
        binding=_cursor_binding(context, kinds, year, order),
        position={
            "effectiveDate": item.effective_date.isoformat(),
            "createdAt": item.created_at.astimezone(UTC).isoformat().replace("+00:00", "Z"),
            "kind": item.kind.value,
            "id": str(item.id),
        },
    )


def _decode_cursor(
    token: str,
    *,
    context: AuthorizationContext,
    kinds: tuple[StoryKind, ...],
    year: int | None,
    order: StoryOrder,
) -> tuple[date, datetime, int, UUID]:
    position = cursor_codec.decode(token, binding=_cursor_binding(context, kinds, year, order))
    datum_roh = position.get("effectiveDate")
    erstellt_roh = position.get("createdAt")
    kind_roh = position.get("kind")
    id_roh = position.get("id")
    if not all(isinstance(wert, str) for wert in (datum_roh, erstellt_roh, kind_roh, id_roh)):
        raise cursor_codec.invalid_cursor()
    try:
        datum = date.fromisoformat(str(datum_roh))
        erstellt = datetime.fromisoformat(str(erstellt_roh).replace("Z", "+00:00"))
        kind = StoryKind(str(kind_roh))
        eintrag_id = UUID(str(id_roh))
    except ValueError as fehler:
        raise cursor_codec.invalid_cursor() from fehler
    if erstellt.tzinfo is None:
        raise cursor_codec.invalid_cursor()
    return datum, erstellt.astimezone(UTC), _KIND_RANK[kind], eintrag_id


def read_timeline(
    session: Session,
    context: AuthorizationContext,
    *,
    kinds: tuple[StoryKind, ...] = (),
    year: int | None = None,
    order: StoryOrder = StoryOrder.DESC,
    cursor: str | None = None,
    limit: int = DEFAULT_LIMIT,
) -> StoryPageResult:
    """Eine Seite der Zeitleiste.

    Ohne `kinds` sind alle drei Typen gemeint. Der Filter verengt die
    bereits autorisierte Menge und erweitert sie nie.
    """
    gewaehlt = kinds or tuple(StoryKind)
    zweige = [_leg(kind, context, year=year) for kind in gewaehlt]
    vereinigt = union_all(*zweige).subquery("story")

    schluessel = (
        vereinigt.c.effective_date,
        vereinigt.c.created_at,
        vereinigt.c.kind_rank,
        vereinigt.c.id,
    )
    statement = select(*schluessel)

    if cursor is not None:
        position = _decode_cursor(cursor, context=context, kinds=gewaehlt, year=year, order=order)
        # Zeilenvergleich statt verschachtelter ODER-Kaskade: PostgreSQL
        # vergleicht das Tupel lexikografisch und trifft damit genau die
        # Semantik aus M2-D08 - strikt hinter dem vollstaendigen Schluessel,
        # nie ein Offset.
        vergleich = tuple_(*schluessel)
        # Die Cursorwerte tragen den Typ ihrer Spalte, damit der Vergleich
        # in der Datenbank derselbe ist wie die Sortierung darueber.
        gegenstueck = tuple_(
            *(literal(wert, spalte.type) for wert, spalte in zip(position, schluessel, strict=True))
        )
        statement = statement.where(
            vergleich < gegenstueck if order is StoryOrder.DESC else vergleich > gegenstueck
        )

    richtung = (
        [spalte.desc() for spalte in schluessel]
        if order is StoryOrder.DESC
        else [spalte.asc() for spalte in schluessel]
    )
    zeilen = session.execute(statement.order_by(*richtung).limit(limit + 1)).all()

    has_more = len(zeilen) > limit
    items = [
        StoryItem(
            kind=_kind_of_rank(zeile.kind_rank),
            effective_date=zeile.effective_date,
            created_at=zeile.created_at,
            id=zeile.id,
        )
        for zeile in zeilen[:limit]
    ]
    next_cursor = None
    if has_more and items:
        next_cursor = _encode_cursor(
            context=context, kinds=gewaehlt, year=year, order=order, item=items[-1]
        )
    return StoryPageResult(items=items, next_cursor=next_cursor, has_more=has_more)


def _kind_of_rank(rank: int) -> StoryKind:
    for kind, wert in _KIND_RANK.items():
        if wert == rank:
            return kind
    raise RuntimeError(f"Unknown story kind rank: {rank}")
