"""Fachlogik fuer M3-Wishes.

Die Form ist bewusst dieselbe wie in `milestones.service`: derselbe
signierte Cursor, dieselbe Versionspruefung, dieselbe Outbox. Zwei Dinge
sind fachlich anders und deshalb ausdruecklich benannt.

Erstens das Schreibrecht. Ein Wish gehoert dem Paar, nicht dem, der ihn
zuerst getippt hat (M3-D01). Das steht nicht hier, sondern als
`shared_write` am Modell - `require_writable` laesst deshalb beide Partner
durch, ohne dass dieser Dienst eine eigene Ausnahme formuliert.

Zweitens der Status. `Wish.status` ist kein Feld, das ein Client setzt:
`OPEN -> PLANNED` entsteht ausschliesslich aus der Wish->Plan-Operation,
`PLANNED -> OPEN` aus `return-to-wish`, `PLANNED -> COMPLETED` aus der
Completion des originaeren Plans (M3-D02/D03/D04). In M3-S1 gibt es noch
keinen Plan; ein Wish ist deshalb immer `OPEN`. Dieser Dienst bietet
trotzdem keinen Weg an, den Status zu aendern - sonst entstuende genau die
freie Statusmutation, die der spaetere Vertrag ausschliesst.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any
from uuid import UUID

from sqlalchemy import and_, or_
from sqlalchemy.orm import Session
from sqlalchemy.orm.exc import StaleDataError

from sidebyside.authorization import (
    AuthorizationContext,
    readable,
    require_readable,
    require_writable,
)
from sidebyside.core import cursor as cursor_codec
from sidebyside.core.errors import ConflictError, ErrorCode, ValidationError
from sidebyside.domain.events import DomainEvent, EventType, PublicEventPayload
from sidebyside.outbox import service as outbox_service
from sidebyside.wishes.models import Wish, WishPayload, WishStatus, shared_privacy

_WISH_SUBJECT_TYPE = "wish"

WISH_TITLE_REQUIRED = "WISH_TITLE_REQUIRED"
WISH_HAS_ACTIVE_PLAN = "WISH_HAS_ACTIVE_PLAN"


@dataclass(frozen=True)
class WishPageResult:
    items: list[Wish]
    next_cursor: str | None
    has_more: bool


def _normalize_title(value: str) -> str:
    cleaned = value.strip()
    if not cleaned:
        raise ValidationError("Wish title must not be blank.", WISH_TITLE_REQUIRED)
    return cleaned


def _flush(session: Session) -> None:
    try:
        session.flush()
    except StaleDataError as error:
        raise ConflictError(
            "The resource was changed since it was loaded.",
            ErrorCode.RESOURCE_VERSION_CONFLICT,
        ) from error


def _ensure_expected_version(wish: Wish, expected_version: int) -> None:
    if wish.version != expected_version:
        raise ConflictError(
            "The resource was changed since it was loaded.",
            ErrorCode.RESOURCE_VERSION_CONFLICT,
        )


def _record(session: Session, wish: Wish, actor_id: UUID, event_type: EventType) -> None:
    """Ein Ereignis ohne Wunschtitel.

    M3-D13: Titel gehoeren nicht in Outbox, Logs oder Analytics. Was hier
    hinausgeht, sind IDs, Actor, Version und der Eventtyp.
    """
    outbox_service.record(
        session,
        DomainEvent(
            type=event_type,
            space_id=wish.space_id,
            actor_id=actor_id,
            subject_type=_WISH_SUBJECT_TYPE,
            subject_id=wish.id,
            resource_version=wish.version,
            payload=PublicEventPayload(),
        ),
    )


def create_wish(
    session: Session,
    context: AuthorizationContext,
    *,
    title: str,
) -> Wish:
    """Ein neuer Wish beginnt immer `OPEN`.

    Der Status kommt nicht aus dem Request. Ein Client, der ihn mitschickt,
    wird an der API-Grenze abgewiesen; hier gibt es gar keinen Parameter,
    ueber den er ankommen koennte.
    """
    wish = Wish(
        space_id=context.space_id,
        owner_id=context.account_id,
        privacy_class=shared_privacy(),
        status=WishStatus.OPEN.value,
        payload=WishPayload(title=_normalize_title(title)),
    )
    session.add(wish)
    _flush(session)
    _record(session, wish, context.account_id, EventType.WISH_CREATED)
    _flush(session)
    return wish


def get_wish(
    session: Session,
    context: AuthorizationContext,
    wish_id: UUID | str,
) -> Wish:
    return require_readable(session, Wish, context, wish_id)


def update_wish(
    session: Session,
    context: AuthorizationContext,
    wish_id: UUID | str,
    *,
    expected_version: int,
    title: str,
) -> Wish:
    """Eine Titelkorrektur - und ausdruecklich nichts weiter.

    Sie ist ein versioniertes Inhaltsupdate und veraendert den Status
    nicht (M3-D02). `createdBy`, `spaceId` und `status` sind keine
    Parameter dieser Funktion; es gibt damit keinen Pfad, ueber den ein
    Request sie umsetzen koennte.
    """
    wish = require_writable(session, Wish, context, wish_id)
    _ensure_expected_version(wish, expected_version)

    wish.payload = WishPayload(title=_normalize_title(title))

    _flush(session)
    _record(session, wish, context.account_id, EventType.WISH_UPDATED)
    _flush(session)
    return wish


def _ensure_deletable(wish: Wish) -> None:
    """Die Delete-Matrix aus M3-D05, soweit M3-S1 sie beantworten kann.

    Ein `PLANNED` Wish hat einen aktiven originaeren Plan; geloescht wird
    dann der Plan bzw. `return-to-wish` benutzt, nicht der Wish. `OPEN` und
    `COMPLETED` sind loeschbar, solange kein originaerer Plan mehr
    existiert.

    Der zweite Halbsatz ist in diesem Slice noch nicht pruefbar: es gibt
    keine `plans`-Tabelle, also auch keinen Plan, der einen Wish halten
    koennte. M3-S2 ergaenzt die Plan-Existenzpruefung hier - und damit die
    Zeilen der Matrix, die auf einen vorhandenen Plan zeigen.
    """
    if wish.status == WishStatus.PLANNED.value:
        raise ConflictError(
            "This wish has an active plan. Use the plan instead.",
            WISH_HAS_ACTIVE_PLAN,
        )


def delete_wish(
    session: Session,
    context: AuthorizationContext,
    wish_id: UUID | str,
    *,
    expected_version: int,
) -> None:
    wish = require_writable(session, Wish, context, wish_id)
    _ensure_expected_version(wish, expected_version)
    _ensure_deletable(wish)
    actor_id = context.account_id
    session.delete(wish)
    _flush(session)
    _record(session, wish, actor_id, EventType.WISH_DELETED)
    _flush(session)


def _cursor_binding(context: AuthorizationContext, status: WishStatus | None) -> dict[str, Any]:
    return {
        "collection": "wishes",
        "spaceId": str(context.space_id),
        "status": status.value if status is not None else None,
    }


def _encode_cursor(
    *,
    context: AuthorizationContext,
    status: WishStatus | None,
    created_at: datetime,
    wish_id: UUID,
) -> str:
    return cursor_codec.encode(
        binding=_cursor_binding(context, status),
        position={
            "createdAt": created_at.astimezone(UTC).isoformat().replace("+00:00", "Z"),
            "id": str(wish_id),
        },
    )


def _decode_cursor(
    token: str,
    *,
    context: AuthorizationContext,
    status: WishStatus | None,
) -> tuple[datetime, UUID]:
    position = cursor_codec.decode(token, binding=_cursor_binding(context, status))
    created_raw = position.get("createdAt")
    wish_raw = position.get("id")
    if not isinstance(created_raw, str) or not isinstance(wish_raw, str):
        raise cursor_codec.invalid_cursor()
    try:
        created_at = datetime.fromisoformat(created_raw.replace("Z", "+00:00"))
        wish_id = UUID(wish_raw)
    except ValueError as error:
        raise cursor_codec.invalid_cursor() from error
    if created_at.tzinfo is None:
        raise cursor_codec.invalid_cursor()
    return created_at.astimezone(UTC), wish_id


def list_wishes(
    session: Session,
    context: AuthorizationContext,
    *,
    cursor: str | None,
    limit: int,
    status: WishStatus | None,
) -> WishPageResult:
    """Neueste zuerst, wie bei Memory und Milestone.

    Sortiert wird ueber `createdAt` und ID, nicht ueber den Titel: eine
    Reihenfolge, die den Klartext braucht, waere nach der spaeteren
    Umstellung auf clientseitige Verschluesselung nicht mehr herstellbar.
    """
    statement = readable(Wish, context)
    if status is not None:
        statement = statement.where(Wish.status == status.value)
    if cursor is not None:
        created_at, wish_id = _decode_cursor(cursor, context=context, status=status)
        statement = statement.where(
            or_(
                Wish.created_at < created_at,
                and_(Wish.created_at == created_at, Wish.id < wish_id),
            )
        )

    statement = statement.order_by(Wish.created_at.desc(), Wish.id.desc()).limit(limit + 1)
    rows = list(session.execute(statement).scalars().all())
    has_more = len(rows) > limit
    items = rows[:limit]
    next_cursor = None
    if has_more and items:
        last = items[-1]
        next_cursor = _encode_cursor(
            context=context,
            status=status,
            created_at=last.created_at,
            wish_id=last.id,
        )
    return WishPageResult(items=items, next_cursor=next_cursor, has_more=has_more)
