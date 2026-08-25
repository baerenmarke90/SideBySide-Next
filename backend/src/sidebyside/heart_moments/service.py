"""Fachlogik fuer M2-HeartMoments.

Der Unterschied zu Memory ist die Sichtbarkeit. Ein HeartMoment kann
gemeinsam oder owner-only sein, und diese Wahl ist eine Domainoperation mit
eigener Route - kein Feld, das ein normales Update nebenbei mitaendert.

Die Sichtbarkeitsgrenze wird nirgends in dieser Datei formuliert. Lesen und
Schreiben gehen durch dieselbe zentrale Autorisierung wie jede andere
private Ressource; `readable` traegt die Bedingung bereits im Statement,
bevor hier ein Filter oder eine Sortierung angehaengt wird. Ein privater
HeartMoment ist fuer den Partner deshalb nicht "gefiltert", sondern nie
geladen.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, date, datetime
from typing import Any
from uuid import UUID

from sqlalchemy import and_, or_
from sqlalchemy.orm import Session
from sqlalchemy.orm.exc import StaleDataError

from sidebyside.attachments import service as attachment_service
from sidebyside.authorization import (
    AuthorizationContext,
    ContentVisibility,
    PrivacyClass,
    privacy_for,
    readable,
    require_readable,
    require_writable,
    visibility_of,
)
from sidebyside.core import cursor as cursor_codec
from sidebyside.core.errors import ConflictError, ErrorCode, ValidationError
from sidebyside.domain.events import DomainEvent, EventType, PublicEventPayload
from sidebyside.heart_moments.models import HeartEmotion, HeartMoment, HeartMomentPayload
from sidebyside.outbox import service as outbox_service

_HEART_MOMENT_SUBJECT_TYPE = "heart_moment"


@dataclass(frozen=True)
class HeartMomentPageResult:
    items: list[HeartMoment]
    next_cursor: str | None
    has_more: bool


def _normalize_text(value: str) -> str:
    cleaned = value.strip()
    if not cleaned:
        raise ValidationError("Heart moment text must not be blank.", "HEART_MOMENT_TEXT_REQUIRED")
    return cleaned


def _flush(session: Session) -> None:
    try:
        session.flush()
    except StaleDataError as error:
        raise ConflictError(
            "The resource was changed since it was loaded.",
            ErrorCode.RESOURCE_VERSION_CONFLICT,
        ) from error


def _ensure_expected_version(heart_moment: HeartMoment, expected_version: int) -> None:
    if heart_moment.version != expected_version:
        raise ConflictError(
            "The resource was changed since it was loaded.",
            ErrorCode.RESOURCE_VERSION_CONFLICT,
        )


def _record(
    session: Session,
    heart_moment: HeartMoment,
    actor_id: UUID,
    event_type: EventType,
    *,
    visibility: ContentVisibility,
) -> None:
    """Ein Ereignis ohne Text und ohne Emotion.

    `visibility` ist die einzige fachliche Angabe im Envelope. Ein Consumer
    braucht sie, um ein owner-only Ereignis nicht in eine Partnerprojektion
    zu schreiben; Inhalt braucht er dafuer nicht (M2-D06, M2-D16).
    """
    outbox_service.record(
        session,
        DomainEvent(
            type=event_type,
            space_id=heart_moment.space_id,
            actor_id=actor_id,
            subject_type=_HEART_MOMENT_SUBJECT_TYPE,
            subject_id=heart_moment.id,
            resource_version=heart_moment.version,
            payload=PublicEventPayload(visibility=visibility),
        ),
    )


def create_heart_moment(
    session: Session,
    context: AuthorizationContext,
    *,
    text: str,
    emotion: HeartEmotion,
    visibility: ContentVisibility,
    happened_on: date,
    attachment_id: UUID | None = None,
) -> HeartMoment:
    heart_moment = HeartMoment(
        space_id=context.space_id,
        owner_id=context.account_id,
        privacy_class=privacy_for(visibility).value,
        happened_on=happened_on,
        payload=HeartMomentPayload(text=_normalize_text(text), emotion=emotion),
    )
    if attachment_id is not None:
        _bind(session, context, heart_moment, attachment_id)
    session.add(heart_moment)
    _flush(session)
    _record(
        session,
        heart_moment,
        context.account_id,
        EventType.HEART_MOMENT_CREATED,
        visibility=visibility,
    )
    _flush(session)
    return heart_moment


def get_heart_moment(
    session: Session,
    context: AuthorizationContext,
    heart_moment_id: UUID | str,
) -> HeartMoment:
    return require_readable(session, HeartMoment, context, heart_moment_id)


def update_heart_moment(
    session: Session,
    context: AuthorizationContext,
    heart_moment_id: UUID | str,
    *,
    expected_version: int,
    changed_fields: frozenset[str],
    text: str | None,
    emotion: HeartEmotion | None,
    happened_on: date | None,
    attachment_id: UUID | None = None,
) -> HeartMoment:
    """Inhalt aendern - Sichtbarkeit ausdruecklich nicht.

    Der Wechsel `SHARED -> PRIVATE` loescht Kommentare und ist damit
    destruktiv. Er bleibt deshalb eine eigene Operation und kann nicht als
    Nebenwirkung eines Textupdates passieren.
    """
    heart_moment = require_writable(session, HeartMoment, context, heart_moment_id)
    _ensure_expected_version(heart_moment, expected_version)

    next_text = heart_moment.payload.text
    next_emotion = heart_moment.payload.emotion
    if "text" in changed_fields:
        assert text is not None
        next_text = _normalize_text(text)
    if "emotion" in changed_fields:
        assert emotion is not None
        next_emotion = emotion
    if "happened_on" in changed_fields:
        assert happened_on is not None
        heart_moment.happened_on = happened_on

    if "text" in changed_fields or "emotion" in changed_fields:
        heart_moment.payload = HeartMomentPayload(text=next_text, emotion=next_emotion)

    if "attachment_id" in changed_fields:
        _rebind(session, context, heart_moment, attachment_id)

    _flush(session)
    _record(
        session,
        heart_moment,
        context.account_id,
        EventType.HEART_MOMENT_UPDATED,
        visibility=visibility_of(heart_moment.privacy_class),
    )
    _flush(session)
    return heart_moment


def _delete_dependent_comments(session: Session, heart_moment: HeartMoment) -> None:
    """Kommentare eines HeartMoments loeschen, der privat wird.

    M2-D07 verlangt, dass der Wechsel `SHARED -> PRIVATE` vorhandene
    Kommentare in derselben DB-Transaktion loescht - ein blosses Verstecken
    koennte Partnerdaten spaeter erneut sichtbar machen.

    Comments sind noch nicht implementiert; sie kommen im Comments-Slice.
    Diese Funktion ist die Stelle, an der die Loeschung einzuhaengen ist,
    und sie liegt bewusst innerhalb der Transaktion des Wechsels, damit sie
    dort nicht nachtraeglich danebengesetzt wird. Solange es keine
    Comment-Tabelle gibt, gibt es auch nichts zu loeschen - die Invariante
    ist erfuellt, aber nicht bewiesen.
    """
    return None


def change_visibility(
    session: Session,
    context: AuthorizationContext,
    heart_moment_id: UUID | str,
    *,
    expected_version: int,
    visibility: ContentVisibility,
) -> HeartMoment:
    """Die Sichtbarkeit wechseln - atomar, mit allen Folgen.

    Der Wechsel und das Loeschen abhaengiger Kommentare laufen in derselben
    Request-Transaktion. Bricht irgendetwas ab, bleibt der alte Zustand
    vollstaendig erhalten; es gibt keinen Zwischenstand, in dem die Klasse
    schon privat ist und Kommentare noch stehen.

    `PRIVATE -> SHARED` stellt geloeschte Kommentare nicht wieder her.
    """
    heart_moment = require_writable(session, HeartMoment, context, heart_moment_id)
    _ensure_expected_version(heart_moment, expected_version)

    target = privacy_for(visibility)
    if heart_moment.privacy_class == target.value:
        # Kein Zustandswechsel: keine Version, kein Ereignis. Ein Ereignis
        # ohne Aenderung waere fuer jeden Consumer ein falsches Signal.
        return heart_moment

    if target is PrivacyClass.OWNER_ONLY:
        _delete_dependent_comments(session, heart_moment)

    heart_moment.privacy_class = target.value
    _flush(session)
    _record(
        session,
        heart_moment,
        context.account_id,
        EventType.HEART_MOMENT_VISIBILITY_CHANGED,
        visibility=visibility,
    )
    _flush(session)
    return heart_moment


def delete_heart_moment(
    session: Session,
    context: AuthorizationContext,
    heart_moment_id: UUID | str,
    *,
    expected_version: int,
) -> None:
    heart_moment = require_writable(session, HeartMoment, context, heart_moment_id)
    _ensure_expected_version(heart_moment, expected_version)
    actor_id = context.account_id
    visibility = visibility_of(heart_moment.privacy_class)
    session.delete(heart_moment)
    _flush(session)
    _record(
        session,
        heart_moment,
        actor_id,
        EventType.HEART_MOMENT_DELETED,
        visibility=visibility,
    )
    _flush(session)


def _cursor_binding(
    context: AuthorizationContext, visibility: ContentVisibility | None
) -> dict[str, Any]:
    return {
        "collection": "heart_moments",
        "spaceId": str(context.space_id),
        "visibility": visibility.value if visibility is not None else None,
    }


def _encode_cursor(
    *,
    context: AuthorizationContext,
    visibility: ContentVisibility | None,
    created_at: datetime,
    heart_moment_id: UUID,
) -> str:
    return cursor_codec.encode(
        binding=_cursor_binding(context, visibility),
        position={
            "createdAt": created_at.astimezone(UTC).isoformat().replace("+00:00", "Z"),
            "id": str(heart_moment_id),
        },
    )


def _decode_cursor(
    token: str,
    *,
    context: AuthorizationContext,
    visibility: ContentVisibility | None,
) -> tuple[datetime, UUID]:
    position = cursor_codec.decode(token, binding=_cursor_binding(context, visibility))
    created_raw = position.get("createdAt")
    heart_moment_raw = position.get("id")
    if not isinstance(created_raw, str) or not isinstance(heart_moment_raw, str):
        raise cursor_codec.invalid_cursor()
    try:
        created_at = datetime.fromisoformat(created_raw.replace("Z", "+00:00"))
        heart_moment_id = UUID(heart_moment_raw)
    except ValueError as error:
        raise cursor_codec.invalid_cursor() from error
    if created_at.tzinfo is None:
        raise cursor_codec.invalid_cursor()
    return created_at.astimezone(UTC), heart_moment_id


def list_heart_moments(
    session: Session,
    context: AuthorizationContext,
    *,
    cursor: str | None,
    limit: int,
    visibility: ContentVisibility | None,
) -> HeartMomentPageResult:
    """Eine Seite sichtbarer HeartMoments.

    Der `visibility`-Filter verengt die bereits autorisierte Menge; er
    erweitert sie nie. `visibility=PRIVATE` liefert dem Partner deshalb
    eine leere Seite und nicht etwa fremde private Zeilen - die Bedingung
    aus `readable` steht davor.
    """
    statement = readable(HeartMoment, context)
    if visibility is not None:
        statement = statement.where(HeartMoment.privacy_class == privacy_for(visibility).value)
    if cursor is not None:
        created_at, heart_moment_id = _decode_cursor(cursor, context=context, visibility=visibility)
        statement = statement.where(
            or_(
                HeartMoment.created_at < created_at,
                and_(HeartMoment.created_at == created_at, HeartMoment.id < heart_moment_id),
            )
        )

    statement = statement.order_by(HeartMoment.created_at.desc(), HeartMoment.id.desc()).limit(
        limit + 1
    )
    rows = list(session.execute(statement).scalars().all())
    has_more = len(rows) > limit
    items = rows[:limit]
    next_cursor = None
    if has_more and items:
        last = items[-1]
        next_cursor = _encode_cursor(
            context=context,
            visibility=visibility,
            created_at=last.created_at,
            heart_moment_id=last.id,
        )
    return HeartMomentPageResult(items=items, next_cursor=next_cursor, has_more=has_more)


def _bind(
    session: Session,
    context: AuthorizationContext,
    heart_moment: HeartMoment,
    attachment_id: UUID,
) -> None:
    """Ein Attachment an diesen HeartMoment haengen (M2-D03).

    Die Regeln liegen im Bindungsmodul und nicht hier: sonst haette jede
    Domaene ihre eigene Teilmenge davon, und die Unterschiede faenden sich
    erst, wenn eine Sichtbarkeit falsch entschieden wurde.
    """
    from sidebyside.attachments import binding

    gesperrt = binding.lock_for_binding(session, [attachment_id])
    binding.ensure_bindable(
        gesperrt.get(attachment_id),
        space_id=context.space_id,
        account_id=context.account_id,
    )
    binding.ensure_unlinked(session, attachment_id, allow=("HEART_MOMENT", heart_moment.id))
    heart_moment.attachment_id = attachment_id


def _rebind(
    session: Session,
    context: AuthorizationContext,
    heart_moment: HeartMoment,
    attachment_id: UUID | None,
) -> None:
    """Attachment tauschen oder loesen.

    Das abgeloeste Attachment verliert seine letzte Referenz und wird nach
    M2-D11 sofort fachlich unsichtbar; der Providercleanup folgt asynchron.
    """
    from sidebyside.attachments.models import Attachment

    vorher = heart_moment.attachment_id
    if vorher == attachment_id:
        return

    if attachment_id is None:
        heart_moment.attachment_id = None
    else:
        _bind(session, context, heart_moment, attachment_id)

    if vorher is not None:
        abgeloest = session.get(Attachment, vorher)
        if abgeloest is not None:
            attachment_service.mark_for_deletion(session, abgeloest)
