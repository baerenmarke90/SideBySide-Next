"""Fachlogik fuer M3-Plans und den Wish->Plan-Lifecycle.

Dieser Dienst traegt die Operationen, die zwei Aggregate gleichzeitig
beruehren. Drei Dinge sind daran wichtig und stehen deshalb hier oben.

**Sperrreihenfolge.** Im M3-Kern gilt `Place -> Wish -> Plan`. Der Plan
wird immer zuletzt gesperrt; damit kann kein Paar von Operationen sich
gegenseitig blockieren. Ein Plan-Einstieg darf die Plan-ID zunaechst
ungesperrt aufloesen, muss dann den source Wish sperren und den Plan
danach in derselben Transaktion erneut sperren und revalidieren. Zwischen
dem ungesperrten Lesen und dem Sperren kann sich alles geaendert haben -
deshalb wird nach dem Sperren nicht weitergerechnet, sondern nachgesehen.

Ein `placeId` im Request wird aus demselben Grund *vor* dem Plan
aufgeloest und mit `FOR SHARE` gehalten: der Ort darf zwischen der
Pruefung und dem Schreiben des Verweises nicht geloescht werden. Ein
Place-Delete braucht `FOR UPDATE` und wartet deshalb.

**Wem der Status gehoert.** Der Plan-Automat steht hier, der Wish-Automat
in `wishes.service`. Dieser Dienst ruft dort `plan_created`,
`plan_completed` und `plan_returned` auf, statt `wish.status` selbst zu
setzen. Damit gibt es fuer jede Wish-Kante genau eine Stelle, die ihren
Ausgangszustand prueft.

**Was der Client nicht setzt.** `status`, `sourceWishId`, `plannedStart`,
`plannedEnd` und `experiencedOn` entstehen ausschliesslich aus den
Lifecycle-Operationen (M3-D04/D30). Kein Create- und kein Update-Pfad
dieses Moduls nimmt sie als freien Parameter entgegen.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, date, datetime
from typing import Any
from uuid import UUID

from sqlalchemy import and_, or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from sqlalchemy.orm.exc import StaleDataError

from sidebyside.authorization import (
    AuthorizationContext,
    readable,
    require_readable,
    require_readable_shared,
    require_writable,
    require_writable_locked,
)
from sidebyside.core import cursor as cursor_codec
from sidebyside.core.clock import today_in
from sidebyside.core.errors import ConflictError, ErrorCode, ValidationError
from sidebyside.domain.events import DomainEvent, EventType, PublicEventPayload
from sidebyside.identity.models import Account
from sidebyside.outbox import service as outbox_service
from sidebyside.places.models import Place
from sidebyside.plans.models import Plan, PlanPayload, PlanStatus, shared_privacy
from sidebyside.wishes import service as wish_service
from sidebyside.wishes.models import Wish, WishStatus

_PLAN_SUBJECT_TYPE = "plan"

PLAN_TITLE_REQUIRED = "PLAN_TITLE_REQUIRED"
PLAN_STATUS_TRANSITION_INVALID = "PLAN_STATUS_TRANSITION_INVALID"
PLAN_SOURCE_WISH_REQUIRED = "PLAN_SOURCE_WISH_REQUIRED"
PLAN_HAS_SOURCE_WISH = "PLAN_HAS_SOURCE_WISH"
PLAN_SCHEDULE_START_REQUIRED = "PLAN_SCHEDULE_START_REQUIRED"
PLAN_DATE_RANGE_INVALID = "PLAN_DATE_RANGE_INVALID"
PLAN_EXPERIENCED_ON_REQUIRED = "PLAN_EXPERIENCED_ON_REQUIRED"
PLAN_EXPERIENCED_ON_IN_FUTURE = "PLAN_EXPERIENCED_ON_IN_FUTURE"


@dataclass(frozen=True)
class PlanPageResult:
    items: list[Plan]
    next_cursor: str | None
    has_more: bool


@dataclass(frozen=True)
class WishToPlanResult:
    """Das Ergebnis einer Konvertierung - inklusive der Frage, ob sie neu war.

    `created` unterscheidet den ersten Aufruf (201) vom idempotenten Retry
    (200). Die Antwort ist in beiden Faellen dieselbe; nur der Statuscode
    sagt, ob dieser Aufruf den Plan erzeugt hat.
    """

    wish: Wish
    plan: Plan
    created: bool


@dataclass(frozen=True)
class ReturnToWishResult:
    wish: Wish
    removed_plan_id: UUID


def _normalize_title(value: str) -> str:
    cleaned = value.strip()
    if not cleaned:
        raise ValidationError("Plan title must not be blank.", PLAN_TITLE_REQUIRED)
    return cleaned


def _flush(session: Session) -> None:
    try:
        session.flush()
    except StaleDataError as error:
        raise ConflictError(
            "The resource was changed since it was loaded.",
            ErrorCode.RESOURCE_VERSION_CONFLICT,
        ) from error


def _ensure_expected_version(plan: Plan, expected_version: int) -> None:
    if plan.version != expected_version:
        raise ConflictError(
            "The resource was changed since it was loaded.",
            ErrorCode.RESOURCE_VERSION_CONFLICT,
        )


def _record(session: Session, plan: Plan, actor_id: UUID, event_type: EventType) -> None:
    """Ein Ereignis ohne Plantitel und ohne Beschreibung (M3-D13)."""
    outbox_service.record(
        session,
        DomainEvent(
            type=event_type,
            space_id=plan.space_id,
            actor_id=actor_id,
            subject_type=_PLAN_SUBJECT_TYPE,
            subject_id=plan.id,
            resource_version=plan.version,
            payload=PublicEventPayload(),
        ),
    )


def _actor_today(session: Session, context: AuthorizationContext) -> date:
    """Der heutige Kalendertag des handelnden Accounts.

    M3-D04 misst `experiencedOn` am *lokalen* Tag, nicht an UTC. Wer
    westlich von UTC lebt, haette am Abend sonst regelmaessig einen
    gueltigen Tag als Zukunft abgewiesen bekommen.
    """
    account = session.get(Account, context.account_id)
    if account is None:
        raise RuntimeError("Acting account disappeared despite an authenticated request.")
    return today_in(account.timezone)


def _validate_experienced_on(
    session: Session, context: AuthorizationContext, value: date | None
) -> date:
    if value is None:
        raise ValidationError(
            "A completed plan needs the day it was experienced.",
            PLAN_EXPERIENCED_ON_REQUIRED,
        )
    if value > _actor_today(session, context):
        raise ValidationError(
            "A plan cannot be experienced in the future.",
            PLAN_EXPERIENCED_ON_IN_FUTURE,
        )
    return value


def _validate_schedule(planned_start: datetime | None, planned_end: datetime | None) -> None:
    if planned_start is None:
        raise ValidationError(
            "Scheduling a plan needs a start.",
            PLAN_SCHEDULE_START_REQUIRED,
        )
    if planned_end is not None and planned_end < planned_start:
        raise ValidationError(
            "A plan cannot end before it starts.",
            PLAN_DATE_RANGE_INVALID,
        )


def _resolve_place(
    session: Session,
    context: AuthorizationContext,
    place_id: UUID | str | None,
) -> UUID | None:
    """Den Ort space-scoped aufloesen und bis zum Commit halten.

    Ein Ort aus einem fremden Space, eine unbekannte ID und eine
    fehlgeformte ID enden identisch in `PLACE_NOT_FOUND` - der Verweis
    darf keine Existenzauskunft ueber fremde Orte werden.
    """
    if place_id is None:
        return None
    return require_readable_shared(session, Place, context, place_id).id


def create_plan(
    session: Session,
    context: AuthorizationContext,
    *,
    title: str,
    description: str | None,
    place_id: UUID | str | None,
) -> Plan:
    """Direct Plan Create nach M3-D30.

    Immer `IDEA`, immer ohne Termine, immer ohne source Wish. Ein Plan wird
    erst ueber `/schedule` terminiert oder ueber `/complete` spontan
    abgeschlossen.
    """
    plan = Plan(
        space_id=context.space_id,
        owner_id=context.account_id,
        privacy_class=shared_privacy(),
        status=PlanStatus.IDEA.value,
        source_wish_id=None,
        place_id=_resolve_place(session, context, place_id),
        payload=PlanPayload(title=_normalize_title(title), description=description),
    )
    session.add(plan)
    _flush(session)
    _record(session, plan, context.account_id, EventType.PLAN_CREATED)
    _flush(session)
    return plan


def get_plan(
    session: Session,
    context: AuthorizationContext,
    plan_id: UUID | str,
) -> Plan:
    return require_readable(session, Plan, context, plan_id)


def _lock_plan(session: Session, context: AuthorizationContext, plan_id: UUID | str) -> Plan:
    return require_writable_locked(session, Plan, context, plan_id)


def _lock_plan_and_source_wish(
    session: Session,
    context: AuthorizationContext,
    plan_id: UUID | str,
) -> tuple[Plan, Wish | None]:
    """Beide Aggregate in der kanonischen Reihenfolge sperren.

    Die Plan-ID wird zunaechst ungesperrt aufgeloest - nur um zu erfahren,
    *ob* es einen source Wish gibt und welchen. Danach wird der Wish
    gesperrt und der Plan erneut geladen und gesperrt.

    Die Revalidierung danach ist kein Ritual: zwischen dem ersten Lesen und
    der Wish-Sperre kann der Plan geloescht oder zurueckgefuehrt worden
    sein. Wer an dieser Stelle mit dem zuerst gelesenen Objekt
    weiterarbeitet, schreibt auf einen Stand, den es nicht mehr gibt.
    """
    probe = require_writable(session, Plan, context, plan_id)
    source_wish_id = probe.source_wish_id
    if source_wish_id is None:
        return _lock_plan(session, context, plan_id), None

    wish = wish_service.lock(session, context, source_wish_id)
    plan = _lock_plan(session, context, plan_id)
    if plan.source_wish_id != wish.id:
        # Der Plan ist waehrend des Wartens auf den Wish-Lock ein anderer
        # geworden. Ein zweiter Versuch waere ein Rekursionsrisiko; der
        # Aufrufer bekommt den Konflikt und liest neu.
        raise ConflictError(
            "The resource was changed since it was loaded.",
            ErrorCode.RESOURCE_VERSION_CONFLICT,
        )
    return plan, wish


def update_plan(
    session: Session,
    context: AuthorizationContext,
    plan_id: UUID | str,
    *,
    expected_version: int,
    changed_fields: frozenset[str],
    title: str | None,
    description: str | None,
    place_id: UUID | str | None,
    experienced_on: date | None,
) -> Plan:
    """Fachliche Korrektur ohne Statuswirkung (M3-D04).

    Auch ein `COMPLETED` Plan darf korrigiert werden; daraus entsteht keine
    Rueckoeffnung. `experiencedOn` gehoert zum abgeschlossenen Zustand und
    ist deshalb nur dort korrigierbar - auf einem Plan ohne Abschluss waere
    es ein vorweggenommener Completion-Termin.
    """
    # Der Ort steht vor dem Plan - sonst entstuende die umgekehrte
    # Reihenfolge zum Place-Delete, und zwei Requests koennten sich
    # gegenseitig blockieren.
    next_place_id = (
        _resolve_place(session, context, place_id) if "place_id" in changed_fields else None
    )

    plan = _lock_plan(session, context, plan_id)
    _ensure_expected_version(plan, expected_version)

    if "place_id" in changed_fields:
        plan.place_id = next_place_id

    next_title = plan.payload.title
    next_description = plan.payload.description
    if "title" in changed_fields:
        assert title is not None
        next_title = _normalize_title(title)
    if "description" in changed_fields:
        # Anders als der Titel darf die Beschreibung geleert werden.
        next_description = description
    if "experienced_on" in changed_fields:
        if plan.status != PlanStatus.COMPLETED.value:
            raise ConflictError(
                "Only a completed plan carries the day it was experienced.",
                PLAN_STATUS_TRANSITION_INVALID,
            )
        plan.experienced_on = _validate_experienced_on(session, context, experienced_on)

    if "title" in changed_fields or "description" in changed_fields:
        plan.payload = PlanPayload(title=next_title, description=next_description)

    _flush(session)
    _record(session, plan, context.account_id, EventType.PLAN_UPDATED)
    _flush(session)
    return plan


def schedule_plan(
    session: Session,
    context: AuthorizationContext,
    plan_id: UUID | str,
    *,
    expected_version: int,
    planned_start: datetime | None,
    planned_end: datetime | None,
) -> Plan:
    """`IDEA -> PLANNED`, oder eine Terminkorrektur auf `PLANNED`."""
    plan = _lock_plan(session, context, plan_id)
    _ensure_expected_version(plan, expected_version)

    if plan.status == PlanStatus.COMPLETED.value:
        raise ConflictError(
            "A completed plan cannot be scheduled.",
            PLAN_STATUS_TRANSITION_INVALID,
        )

    _validate_schedule(planned_start, planned_end)
    plan.planned_start = planned_start
    plan.planned_end = planned_end
    plan.status = PlanStatus.PLANNED.value

    _flush(session)
    _record(session, plan, context.account_id, EventType.PLAN_UPDATED)
    _flush(session)
    return plan


def unschedule_plan(
    session: Session,
    context: AuthorizationContext,
    plan_id: UUID | str,
    *,
    expected_version: int,
) -> Plan:
    """`PLANNED -> IDEA`. Die Termine werden verworfen, nicht aufgehoben."""
    plan = _lock_plan(session, context, plan_id)
    _ensure_expected_version(plan, expected_version)

    if plan.status != PlanStatus.PLANNED.value:
        raise ConflictError(
            "Only a scheduled plan can be unscheduled.",
            PLAN_STATUS_TRANSITION_INVALID,
        )

    plan.planned_start = None
    plan.planned_end = None
    plan.status = PlanStatus.IDEA.value

    _flush(session)
    _record(session, plan, context.account_id, EventType.PLAN_UPDATED)
    _flush(session)
    return plan


def complete_plan(
    session: Session,
    context: AuthorizationContext,
    plan_id: UUID | str,
    *,
    expected_version: int,
    experienced_on: date | None,
) -> tuple[Plan, Wish | None]:
    """`IDEA | PLANNED -> COMPLETED`, bei einem source Plan mitsamt dem Wish.

    Beide Mutationen liegen in derselben Transaktion. Es gibt keinen
    Zwischenstand, in dem der Plan abgeschlossen ist und der Wish noch
    offen - genau der waere fuer beide Partner sichtbar und fachlich
    falsch.

    Completion aus `IDEA` ist erlaubt: nicht alles Gemeinsame wird vorher
    geplant. Die geplanten Zeiten eines `PLANNED` Plans bleiben als
    Historie stehen.
    """
    plan, wish = _lock_plan_and_source_wish(session, context, plan_id)
    _ensure_expected_version(plan, expected_version)

    if plan.status == PlanStatus.COMPLETED.value:
        raise ConflictError(
            "This plan is already completed.",
            PLAN_STATUS_TRANSITION_INVALID,
        )

    plan.experienced_on = _validate_experienced_on(session, context, experienced_on)
    plan.status = PlanStatus.COMPLETED.value

    _flush(session)
    _record(session, plan, context.account_id, EventType.PLAN_COMPLETED)
    _flush(session)

    if wish is not None:
        wish_service.plan_completed(session, wish, context.account_id)

    return plan, wish


def return_to_wish(
    session: Session,
    context: AuthorizationContext,
    plan_id: UUID | str,
    *,
    expected_version: int,
) -> ReturnToWishResult:
    """Den Plan verwerfen und seinen Wish wieder oeffnen (M3-D03).

    Ausdruecklich destruktiv: Plantitel, Beschreibung und Termine sind
    danach weg und werden nicht in den Wish zurueckkopiert. Die UI muss das
    vor der Bestaetigung verstaendlich machen.
    """
    plan, wish = _lock_plan_and_source_wish(session, context, plan_id)
    _ensure_expected_version(plan, expected_version)

    if wish is None:
        raise ConflictError(
            "This plan did not come from a wish.",
            PLAN_SOURCE_WISH_REQUIRED,
        )
    if plan.status == PlanStatus.COMPLETED.value:
        raise ConflictError(
            "A completed plan cannot be returned to its wish.",
            PLAN_STATUS_TRANSITION_INVALID,
        )

    removed_plan_id = plan.id
    actor_id = context.account_id
    session.delete(plan)
    _flush(session)
    _record(session, plan, actor_id, EventType.PLAN_DELETED)
    _flush(session)

    wish_service.plan_returned(session, wish, actor_id)
    return ReturnToWishResult(wish=wish, removed_plan_id=removed_plan_id)


def delete_plan(
    session: Session,
    context: AuthorizationContext,
    plan_id: UUID | str,
    *,
    expected_version: int,
) -> None:
    """Die Plan-Zeilen der Delete-Matrix aus M3-D05.

    | Plan                         | Ergebnis                |
    |------------------------------|-------------------------|
    | Direct, jeder Status         | erlaubt                 |
    | source, `IDEA` / `PLANNED`   | `PLAN_HAS_SOURCE_WISH`  |
    | source, `COMPLETED`          | erlaubt                 |

    Ein nicht abgeschlossener source Plan wird nicht geloescht, sondern
    zurueckgefuehrt - sonst bliebe ein `PLANNED` Wish ohne Plan zurueck.
    Nach dem Loeschen eines abgeschlossenen source Plans bleibt der Wish
    `COMPLETED` und kann anschliessend separat geloescht werden. Es gibt
    keine Cascade in die Gegenrichtung.
    """
    plan, wish = _lock_plan_and_source_wish(session, context, plan_id)
    _ensure_expected_version(plan, expected_version)

    if wish is not None and plan.status != PlanStatus.COMPLETED.value:
        raise ConflictError(
            "This plan came from a wish. Return it to the wish instead.",
            PLAN_HAS_SOURCE_WISH,
        )

    actor_id = context.account_id
    session.delete(plan)
    _flush(session)
    _record(session, plan, actor_id, EventType.PLAN_DELETED)
    _flush(session)


def convert_wish_to_plan(
    session: Session,
    context: AuthorizationContext,
    wish_id: UUID | str,
    *,
    expected_version: int,
    title: str | None,
    description: str | None,
    place_id: UUID | str | None,
) -> WishToPlanResult:
    """Aus einem Wish genau einen Plan machen - atomar und idempotent (M3-D02).

    Der Ablauf folgt der Reihenfolge aus dem Vertrag: Wish sperren,
    vorhandenen originaeren Plan pruefen, den idempotenten Fall vor der
    Versionspruefung beantworten, erst danach konvertieren.

    Dass der Retry *vor* `If-Match` steht, ist Absicht. Ein Client, dessen
    Antwort unterwegs verlorenging, haelt noch die alte Wish-Version in der
    Hand. Wuerde sie hier geprueft, bekaeme er einen Konflikt fuer eine
    Operation, die laengst erfolgreich war - und der einzige Ausweg waere
    ein zweiter Plan.
    """
    # Erst der Ort, dann der Wish, dann der Plan.
    resolved_place_id = _resolve_place(session, context, place_id)

    wish = wish_service.lock(session, context, wish_id)
    existing = session.execute(
        select(Plan).where(Plan.source_wish_id == wish.id).with_for_update()
    ).scalar_one_or_none()

    if wish.status == WishStatus.PLANNED.value:
        if existing is None:
            raise ConflictError(
                "This wish is planned but has no originating plan.",
                wish_service.WISH_PLAN_STATE_CONFLICT,
            )
        # Der idempotente Retry. Ein abweichender Request ueberschreibt den
        # vorhandenen Plan ausdruecklich nicht - weitere Aenderungen laufen
        # ueber den Plan selbst.
        return WishToPlanResult(wish=wish, plan=existing, created=False)

    if wish.status == WishStatus.COMPLETED.value:
        raise ConflictError(
            "This wish is already completed.",
            wish_service.WISH_ALREADY_COMPLETED,
        )

    if existing is not None:
        raise ConflictError(
            "This wish is open but already has an originating plan.",
            wish_service.WISH_PLAN_STATE_CONFLICT,
        )

    _ensure_wish_version(wish, expected_version)

    plan = Plan(
        space_id=context.space_id,
        owner_id=context.account_id,
        privacy_class=shared_privacy(),
        status=PlanStatus.IDEA.value,
        source_wish_id=wish.id,
        place_id=resolved_place_id,
        payload=PlanPayload(
            # Ohne eigenen Titel uebernimmt der Plan den des Wishes. Danach
            # laufen beide getrennt: eine spaetere Wish-Umbenennung
            # veraendert den Plan nicht (M3-D01).
            title=_normalize_title(title if title is not None else wish.payload.title),
            description=description,
        ),
    )
    session.add(plan)
    try:
        _flush(session)
    except IntegrityError as error:
        # Die letzte Integritaetsgrenze: `UNIQUE(source_wish_id)`. Sie
        # sollte nach der Wish-Sperre nicht mehr greifen koennen - wenn
        # doch, wird daraus ein Konflikt und kein 500.
        raise ConflictError(
            "This wish already has an originating plan.",
            wish_service.WISH_HAS_ACTIVE_PLAN,
        ) from error

    _record(session, plan, context.account_id, EventType.PLAN_CREATED)
    _flush(session)

    wish_service.plan_created(session, wish, context.account_id)
    return WishToPlanResult(wish=wish, plan=plan, created=True)


def _ensure_wish_version(wish: Wish, expected_version: int) -> None:
    if wish.version != expected_version:
        raise ConflictError(
            "The resource was changed since it was loaded.",
            ErrorCode.RESOURCE_VERSION_CONFLICT,
        )


def detach_place(session: Session, place: Place, actor_id: UUID) -> None:
    """Alle Plans von einem Ort loesen, der gleich geloescht wird.

    Aufgerufen vom Place-Dienst, der den Ort bereits gesperrt haelt. Die
    Plans werden hier gesperrt - Reihenfolge `Place -> Plan`, wie ueberall.

    Jeder betroffene Plan bekommt eine neue Version und ein Ereignis. Ein
    stilles `ON DELETE SET NULL` waere bequemer, wuerde aber die
    Zuordnung unter einem Client wegziehen, der weiter mit seiner alten
    Version schreibt und nie einen Konflikt saehe.
    """
    betroffen = list(
        session.execute(
            select(Plan)
            .where(Plan.space_id == place.space_id, Plan.place_id == place.id)
            .order_by(Plan.id)
            .with_for_update()
        )
        .scalars()
        .all()
    )
    for plan in betroffen:
        plan.place_id = None
    if not betroffen:
        return
    _flush(session)
    for plan in betroffen:
        _record(session, plan, actor_id, EventType.PLAN_UPDATED)
    _flush(session)


def _cursor_binding(context: AuthorizationContext, status: PlanStatus | None) -> dict[str, Any]:
    return {
        "collection": "plans",
        "spaceId": str(context.space_id),
        "status": status.value if status is not None else None,
    }


def _encode_cursor(
    *,
    context: AuthorizationContext,
    status: PlanStatus | None,
    created_at: datetime,
    plan_id: UUID,
) -> str:
    return cursor_codec.encode(
        binding=_cursor_binding(context, status),
        position={
            "createdAt": created_at.astimezone(UTC).isoformat().replace("+00:00", "Z"),
            "id": str(plan_id),
        },
    )


def _decode_cursor(
    token: str,
    *,
    context: AuthorizationContext,
    status: PlanStatus | None,
) -> tuple[datetime, UUID]:
    position = cursor_codec.decode(token, binding=_cursor_binding(context, status))
    created_raw = position.get("createdAt")
    plan_raw = position.get("id")
    if not isinstance(created_raw, str) or not isinstance(plan_raw, str):
        raise cursor_codec.invalid_cursor()
    try:
        created_at = datetime.fromisoformat(created_raw.replace("Z", "+00:00"))
        plan_id = UUID(plan_raw)
    except ValueError as error:
        raise cursor_codec.invalid_cursor() from error
    if created_at.tzinfo is None:
        raise cursor_codec.invalid_cursor()
    return created_at.astimezone(UTC), plan_id


def list_plans(
    session: Session,
    context: AuthorizationContext,
    *,
    cursor: str | None,
    limit: int,
    status: PlanStatus | None,
) -> PlanPageResult:
    """Neueste zuerst - wie Wish, und aus demselben Grund ueber Metadaten.

    Eine Sortierung nach `plannedStart` waere fuer eine Terminansicht
    naheliegend, aber sie ist eine eigene Leseflaeche mit eigenem Cursor.
    Sie kann spaeter additiv dazukommen, ohne diesen Vertrag zu brechen.
    """
    statement = readable(Plan, context)
    if status is not None:
        statement = statement.where(Plan.status == status.value)
    if cursor is not None:
        created_at, plan_id = _decode_cursor(cursor, context=context, status=status)
        statement = statement.where(
            or_(
                Plan.created_at < created_at,
                and_(Plan.created_at == created_at, Plan.id < plan_id),
            )
        )

    statement = statement.order_by(Plan.created_at.desc(), Plan.id.desc()).limit(limit + 1)
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
            plan_id=last.id,
        )
    return PlanPageResult(items=items, next_cursor=next_cursor, has_more=has_more)
