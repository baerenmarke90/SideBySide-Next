"""Fachlogik fuer M3-Places.

Zwei Dinge unterscheiden diesen Dienst von Wish und Plan.

**Koordinaten.** Sie sind sensibler Inhalt, liegen aber nach M3-D06 als
typisierte Spalten vor. Was hier passiert, ist deshalb Validierung und
Quantisierung - nicht Anreicherung. Es gibt kein Geocoding, keinen
Provideraufruf und keine Ableitung von Adresse zu Koordinaten oder
umgekehrt. Ein Ort weiss genau das, was jemand eingetragen hat.

**Keine Deduplizierung.** Jeder Create-Request erzeugt einen neuen Place,
auch bei gleichem Namen und gleichen Koordinaten (M3-D07). Zwei Orte
zusammenzufuehren waere eine Datenaenderung, die niemand angefordert hat -
und eine, die sich nicht zurueckdrehen laesst.

Die kanonische Sperrreihenfolge im M3-Kern ist `Place -> Wish -> Plan`.
Ein Place wird also immer *vor* einem Plan gesperrt, nie danach.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal, InvalidOperation
from typing import Any
from uuid import UUID

from sqlalchemy import and_, or_
from sqlalchemy.orm import Session
from sqlalchemy.orm.exc import StaleDataError

from sidebyside.authorization import (
    AuthorizationContext,
    readable,
    require_readable,
    require_writable_locked,
)
from sidebyside.core import cursor as cursor_codec
from sidebyside.core.errors import ConflictError, ErrorCode, ValidationError
from sidebyside.domain.events import DomainEvent, EventType, PublicEventPayload
from sidebyside.outbox import service as outbox_service
from sidebyside.places.models import (
    COORDINATE_PLACES,
    LATITUDE_LIMIT,
    LONGITUDE_LIMIT,
    Place,
    PlacePayload,
    shared_privacy,
)

_PLACE_SUBJECT_TYPE = "place"

PLACE_NAME_REQUIRED = "PLACE_NAME_REQUIRED"
PLACE_COORDINATE_PAIR_REQUIRED = "PLACE_COORDINATE_PAIR_REQUIRED"
PLACE_LATITUDE_INVALID = "PLACE_LATITUDE_INVALID"
PLACE_LONGITUDE_INVALID = "PLACE_LONGITUDE_INVALID"

_QUANTUM = Decimal(1).scaleb(-COORDINATE_PLACES)


@dataclass(frozen=True)
class PlacePageResult:
    items: list[Place]
    next_cursor: str | None
    has_more: bool


@dataclass(frozen=True)
class Coordinates:
    latitude: Decimal | None
    longitude: Decimal | None


def _normalize_name(value: str) -> str:
    cleaned = value.strip()
    if not cleaned:
        raise ValidationError("Place name must not be blank.", PLACE_NAME_REQUIRED)
    return cleaned


def _quantize(value: float | Decimal, *, limit: Decimal, code: str) -> Decimal:
    """Eine Koordinate auf die Persistenzgenauigkeit bringen.

    Ueber `str` und nicht direkt aus dem Float: `Decimal(52.520008)` traegt
    den binaeren Rundungsfehler mit, `Decimal("52.520008")` nicht.

    Quantisiert wird bewusst, statt zu viele Nachkommastellen abzulehnen.
    Ein Client, der aus einem Sensor sechzehn Stellen bekommt, hat nichts
    falsch gemacht; gespeichert werden davon sechs (M3-D06).
    """
    try:
        exact = Decimal(str(value))
    except InvalidOperation as error:
        raise ValidationError("Coordinate is not a number.", code) from error
    if not exact.is_finite() or abs(exact) > limit:
        raise ValidationError("Coordinate is out of range.", code)
    quantized = exact.quantize(_QUANTUM)
    if abs(quantized) > limit:
        # Die Rundung selbst darf die Grenze nicht ueberschreiten.
        raise ValidationError("Coordinate is out of range.", code)
    return quantized


def normalize_coordinates(
    latitude: float | Decimal | None,
    longitude: float | Decimal | None,
) -> Coordinates:
    """Beide oder keine - und beide innerhalb ihrer Grenzen (M3-D06)."""
    if (latitude is None) != (longitude is None):
        raise ValidationError(
            "Latitude and longitude must be given together.",
            PLACE_COORDINATE_PAIR_REQUIRED,
        )
    if latitude is None or longitude is None:
        return Coordinates(latitude=None, longitude=None)
    return Coordinates(
        latitude=_quantize(latitude, limit=LATITUDE_LIMIT, code=PLACE_LATITUDE_INVALID),
        longitude=_quantize(longitude, limit=LONGITUDE_LIMIT, code=PLACE_LONGITUDE_INVALID),
    )


def _flush(session: Session) -> None:
    try:
        session.flush()
    except StaleDataError as error:
        raise ConflictError(
            "The resource was changed since it was loaded.",
            ErrorCode.RESOURCE_VERSION_CONFLICT,
        ) from error


def _ensure_expected_version(place: Place, expected_version: int) -> None:
    if place.version != expected_version:
        raise ConflictError(
            "The resource was changed since it was loaded.",
            ErrorCode.RESOURCE_VERSION_CONFLICT,
        )


def _record(session: Session, place: Place, actor_id: UUID, event_type: EventType) -> None:
    """Ein Ereignis ohne Name, Adresse und ohne Koordinaten (M3-D28).

    Der Eventvertrag laesst ohnehin nur die Allowlist aus
    `PublicEventPayload` zu. Der Hinweis steht hier trotzdem: ein Ort ist
    die Art von Angabe, die in einem Log ueber Jahre stehen bleibt.
    """
    outbox_service.record(
        session,
        DomainEvent(
            type=event_type,
            space_id=place.space_id,
            actor_id=actor_id,
            subject_type=_PLACE_SUBJECT_TYPE,
            subject_id=place.id,
            resource_version=place.version,
            payload=PublicEventPayload(),
        ),
    )


def create_place(
    session: Session,
    context: AuthorizationContext,
    *,
    name: str,
    description: str | None,
    address: str | None,
    latitude: float | Decimal | None,
    longitude: float | Decimal | None,
) -> Place:
    coordinates = normalize_coordinates(latitude, longitude)
    place = Place(
        space_id=context.space_id,
        owner_id=context.account_id,
        privacy_class=shared_privacy(),
        latitude=coordinates.latitude,
        longitude=coordinates.longitude,
        payload=PlacePayload(
            name=_normalize_name(name),
            description=description,
            address=address,
        ),
    )
    session.add(place)
    _flush(session)
    _record(session, place, context.account_id, EventType.PLACE_CREATED)
    _flush(session)
    return place


def get_place(
    session: Session,
    context: AuthorizationContext,
    place_id: UUID | str,
) -> Place:
    return require_readable(session, Place, context, place_id)


def update_place(
    session: Session,
    context: AuthorizationContext,
    place_id: UUID | str,
    *,
    expected_version: int,
    changed_fields: frozenset[str],
    name: str | None,
    description: str | None,
    address: str | None,
    latitude: float | Decimal | None,
    longitude: float | Decimal | None,
) -> Place:
    """Eine Korrektur am Ort.

    Koordinaten werden als Paar behandelt, auch beim PATCH: wer eine von
    beiden anfasst, aendert beide. Nur `latitude` zu senden waere sonst
    der Weg zu einer halben Koordinate, den die Invariante gerade
    ausschliesst.
    """
    place = require_writable_locked(session, Place, context, place_id)
    _ensure_expected_version(place, expected_version)

    beruehrt_koordinaten = bool({"latitude", "longitude"} & changed_fields)
    if beruehrt_koordinaten:
        coordinates = normalize_coordinates(
            latitude if "latitude" in changed_fields else place.latitude,
            longitude if "longitude" in changed_fields else place.longitude,
        )
        place.latitude = coordinates.latitude
        place.longitude = coordinates.longitude

    next_name = place.payload.name
    next_description = place.payload.description
    next_address = place.payload.address
    if "name" in changed_fields:
        assert name is not None
        next_name = _normalize_name(name)
    if "description" in changed_fields:
        next_description = description
    if "address" in changed_fields:
        next_address = address

    if {"name", "description", "address"} & changed_fields:
        place.payload = PlacePayload(
            name=next_name,
            description=next_description,
            address=next_address,
        )

    _flush(session)
    _record(session, place, context.account_id, EventType.PLACE_UPDATED)
    _flush(session)
    return place


def delete_place(
    session: Session,
    context: AuthorizationContext,
    place_id: UUID | str,
    *,
    expected_version: int,
) -> None:
    """Den Ort entfernen - und nichts sonst (M3-D06, Abschnitt 9).

    Plans, die auf ihn zeigen, verlieren ihre Zuordnung und bleiben
    bestehen. Das geschieht ausdruecklich im Dienst und nicht nur ueber
    `ON DELETE SET NULL`: ein Plan, dessen Ort verschwindet, hat sich
    geaendert, und seine Version muss das sagen. Sonst schriebe ein
    Partner mit einem Stand weiter, der einen Ort zeigt, den es nicht mehr
    gibt - ohne je einen Konflikt zu sehen.

    Der Fremdschluessel bleibt trotzdem auf `SET NULL`. Er ist die Grenze
    fuer den Fall, dass dieser Weg einmal nicht gelaufen ist.
    """
    from sidebyside.plans import service as plan_service

    place = require_writable_locked(session, Place, context, place_id)
    _ensure_expected_version(place, expected_version)

    actor_id = context.account_id
    plan_service.detach_place(session, place, actor_id)

    session.delete(place)
    _flush(session)
    _record(session, place, actor_id, EventType.PLACE_DELETED)
    _flush(session)


def _cursor_binding(context: AuthorizationContext) -> dict[str, Any]:
    return {"collection": "places", "spaceId": str(context.space_id)}


def _encode_cursor(
    *,
    context: AuthorizationContext,
    created_at: datetime,
    place_id: UUID,
) -> str:
    return cursor_codec.encode(
        binding=_cursor_binding(context),
        position={
            "createdAt": created_at.astimezone(UTC).isoformat().replace("+00:00", "Z"),
            "id": str(place_id),
        },
    )


def _decode_cursor(token: str, *, context: AuthorizationContext) -> tuple[datetime, UUID]:
    position = cursor_codec.decode(token, binding=_cursor_binding(context))
    created_raw = position.get("createdAt")
    place_raw = position.get("id")
    if not isinstance(created_raw, str) or not isinstance(place_raw, str):
        raise cursor_codec.invalid_cursor()
    try:
        created_at = datetime.fromisoformat(created_raw.replace("Z", "+00:00"))
        place_id = UUID(place_raw)
    except ValueError as error:
        raise cursor_codec.invalid_cursor() from error
    if created_at.tzinfo is None:
        raise cursor_codec.invalid_cursor()
    return created_at.astimezone(UTC), place_id


def list_places(
    session: Session,
    context: AuthorizationContext,
    *,
    cursor: str | None,
    limit: int,
) -> PlacePageResult:
    """Neueste zuerst.

    Kein Filter nach Naehe, kein Umkreis, keine Sortierung nach Distanz -
    das waere eine Geo-Abfrage und braucht einen bewussten spaeteren
    Scope samt Indexform. Und kein Filter nach Name: der liegt hinter der
    ProtectedPayload-Grenze.
    """
    statement = readable(Place, context)
    if cursor is not None:
        created_at, place_id = _decode_cursor(cursor, context=context)
        statement = statement.where(
            or_(
                Place.created_at < created_at,
                and_(Place.created_at == created_at, Place.id < place_id),
            )
        )

    statement = statement.order_by(Place.created_at.desc(), Place.id.desc()).limit(limit + 1)
    rows = list(session.execute(statement).scalars().all())
    has_more = len(rows) > limit
    items = rows[:limit]
    next_cursor = None
    if has_more and items:
        last = items[-1]
        next_cursor = _encode_cursor(
            context=context,
            created_at=last.created_at,
            place_id=last.id,
        )
    return PlacePageResult(items=items, next_cursor=next_cursor, has_more=has_more)


__all__ = [
    "Coordinates",
    "PlacePageResult",
    "create_place",
    "delete_place",
    "get_place",
    "list_places",
    "normalize_coordinates",
    "update_place",
]
