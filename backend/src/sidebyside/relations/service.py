"""Domain logic for typed M3 content relations.

Three properties define this service.

**The lock order is parent, then target.** Always, without exception
(M3-D26). The Place is locked exclusively, then the target with `FOR SHARE`.
The reverse order would be convenient in exactly one location - a HeartMoment
privacy transition - and would create the deadlock there. The privacy
transition therefore explicitly does *not* acquire parent locks afterwards.

**A target is checked again after locking, not before.** Between lookup and
write it could be deleted or become private. Only the lock makes the check
stable.

**Every invalid target receives the same response.** Unknown, deleted,
foreign space, `OWNER_ONLY`: four different facts, one response
(`RELATION_TARGET_NOT_FOUND`, 404). Distinguishing them would reveal exactly
the information M3-D09 is intended to protect.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Literal, Protocol, cast
from uuid import UUID

from sqlalchemy import delete, select
from sqlalchemy.dialects.postgresql import insert as postgres_insert
from sqlalchemy.orm import Session

from sidebyside.authorization import (
    AuthorizationContext,
    PrivacyClass,
    PrivateResourceMixin,
    require_readable_shared,
    require_writable_locked,
)
from sidebyside.core.errors import DomainError, NotFoundError
from sidebyside.db.base import Base
from sidebyside.domain.events import DomainEvent, EventType, PublicEventPayload
from sidebyside.heart_moments.models import HeartMoment
from sidebyside.memories.models import Memory
from sidebyside.milestones.models import Milestone
from sidebyside.outbox import service as outbox_service
from sidebyside.places.models import Place
from sidebyside.relations.models import PlaceHeartMoment, PlaceMemory, PlaceMilestone

if TYPE_CHECKING:  # pragma: no cover - typing only
    from collections.abc import Sequence


class RelatableTarget(Protocol):
    """The surface this service needs from a target, and nothing more.

    The three target models inherit `IdMixin` and `PrivateResourceMixin`
    separately; there is no common superclass combining both. Rather than
    introducing one only to satisfy type checking, this protocol describes
    the surface actually used here: an ID and a privacy class.
    """

    id: UUID
    privacy_class: str


RELATION_TARGET_NOT_FOUND = "RELATION_TARGET_NOT_FOUND"
RELATION_NOT_FOUND = "RELATION_NOT_FOUND"

_RELATION_SUBJECT_TYPE = "place_relation"


def target_not_found() -> NotFoundError:
    """Return the single response used for every invalid target.

    This is a function rather than a constant so the same exception instance
    is not accidentally raised twice; otherwise a traceback from an earlier
    request could remain attached to a later response.
    """
    return NotFoundError("Relation target not found.", RELATION_TARGET_NOT_FOUND)


@dataclass(frozen=True)
class RelationKind:
    """An allowed relation kind.

    The set of these objects *is* the allowlist. There is no path on which a
    client can name a target type the server does not already know. This is
    what separates typed relations from the `(targetType,targetId)`
    polymorphism excluded by M3-D08.
    """

    slug: str
    """Route segment: `/places/{placeId}/{slug}/{targetId}`."""

    relation: type[Base]
    target: type[PrivateResourceMixin]
    target_column: str
    event_target_type: Literal["MEMORY", "HEART_MOMENT", "MILESTONE"]
    """Target category written to the event.

    This deliberately reuses the same closed set already used by
    `PublicEventPayload` for comments instead of extending it. The allowlist
    is the boundary where long-lived event data is approved, and a second
    representation of the same category would create a second decision point.
    """

    linked_event: EventType
    unlinked_event: EventType
    shared_target_only: bool = False
    """Whether the target must be shared content (M3-D09).

    True only for HeartMoment. Memory and Milestone are always `SPACE_SHARED`;
    checking them would be a tautology that could later be mistaken for a
    meaningful condition.
    """


PLACE_MEMORIES = RelationKind(
    slug="memories",
    event_target_type="MEMORY",
    relation=PlaceMemory,
    target=Memory,
    target_column="memory_id",
    linked_event=EventType.PLACE_MEMORY_LINKED,
    unlinked_event=EventType.PLACE_MEMORY_UNLINKED,
)

PLACE_MILESTONES = RelationKind(
    slug="milestones",
    event_target_type="MILESTONE",
    relation=PlaceMilestone,
    target=Milestone,
    target_column="milestone_id",
    linked_event=EventType.PLACE_MILESTONE_LINKED,
    unlinked_event=EventType.PLACE_MILESTONE_UNLINKED,
)

PLACE_HEART_MOMENTS = RelationKind(
    slug="heart-moments",
    event_target_type="HEART_MOMENT",
    relation=PlaceHeartMoment,
    target=HeartMoment,
    target_column="heart_moment_id",
    linked_event=EventType.PLACE_HEART_MOMENT_LINKED,
    unlinked_event=EventType.PLACE_HEART_MOMENT_UNLINKED,
    shared_target_only=True,
)

PLACE_RELATION_KINDS: tuple[RelationKind, ...] = (
    PLACE_MEMORIES,
    PLACE_HEART_MOMENTS,
    PLACE_MILESTONES,
)

_BY_SLUG = {kind.slug: kind for kind in PLACE_RELATION_KINDS}


def kind_for(slug: str) -> RelationKind:
    """Resolve the relation kind for a route segment, or return 404.

    An unknown slug is not a validation problem. It describes a relation that
    does not exist and therefore receives the same response as a target that
    does not exist.
    """
    found = _BY_SLUG.get(slug)
    if found is None:
        raise target_not_found()
    return found


def _flush(session: Session) -> None:
    session.flush()


def _record(
    session: Session,
    kind: RelationKind,
    place: Place,
    target_id: UUID,
    actor_id: UUID,
    event_type: EventType,
) -> None:
    """Record an event for a relation mutation.

    The payload carries IDs and nothing else. Neither the place name nor any
    target content belongs in an event; an event stream is not a privileged
    read path (M3-D06, redaction section).
    """
    outbox_service.record(
        session,
        DomainEvent(
            type=event_type,
            space_id=place.space_id,
            actor_id=actor_id,
            subject_type=_RELATION_SUBJECT_TYPE,
            subject_id=place.id,
            resource_version=place.version,
            payload=PublicEventPayload(
                target_type=kind.event_target_type,
                target_id=target_id,
            ),
        ),
    )


def _require_relatable_target(
    session: Session,
    context: AuthorizationContext,
    kind: RelationKind,
    target_id: UUID | str,
) -> RelatableTarget:
    """Lock the target and evaluate it afterwards.

    `require_readable_shared` holds the row against deletion with `FOR SHARE`.
    Only then is its privacy class read; before the lock it would merely be a
    snapshot that could become stale before the insert.

    Every guard rejection - malformed ID, unknown target, foreign space, or
    another owner's private row - is normalized to the same response. The
    guard would otherwise expose the target domain's error code and reveal
    which kind of target was referenced.
    """
    try:
        found = require_readable_shared(session, kind.target, context, target_id)
    except DomainError as error:
        raise target_not_found() from error

    if kind.shared_target_only and found.privacy_class != PrivacyClass.SPACE_SHARED.value:
        # An owner's OWNER_ONLY HeartMoment is readable by that owner, so the
        # guard allows it through. It is still not relatable: a shared link to
        # private content would prove its existence to the partner (M3-D09).
        raise target_not_found()

    return cast("RelatableTarget", found)


def link(
    session: Session,
    context: AuthorizationContext,
    place_id: UUID | str,
    target_id: UUID | str,
    kind: RelationKind,
) -> None:
    """Link parent and target idempotently.

    M3-D26 order: lock the Place exclusively, then the target. The insert uses
    `ON CONFLICT DO NOTHING` because a preceding `SELECT` would open exactly
    the race already closed by the primary key. A second `PUT` for the same
    relation is therefore not a conflict but the same final state, and emits
    no second event.
    """
    place = require_writable_locked(session, Place, context, place_id)
    target = _require_relatable_target(session, context, kind, target_id)

    values: dict[str, object] = {
        "place_id": place.id,
        kind.target_column: target.id,
        "space_id": place.space_id,
        "created_by": context.account_id,
    }
    if kind.shared_target_only:
        # Carry the class into the join row where the CHECK pins it. The value
        # comes from the already locked row, not from a second query.
        values["target_privacy_class"] = target.privacy_class

    statement = (
        postgres_insert(kind.relation)
        .values(**values)
        .on_conflict_do_nothing(
            index_elements=["place_id", kind.target_column],
        )
        .returning(kind.relation.__table__.c.place_id)
    )
    created = session.execute(statement).first() is not None
    _flush(session)

    if created:
        _record(session, kind, place, target.id, context.account_id, kind.linked_event)
        _flush(session)


def unlink(
    session: Session,
    context: AuthorizationContext,
    place_id: UUID | str,
    target_id: UUID | str,
    kind: RelationKind,
) -> None:
    """Remove the link and only the link.

    Both original resources remain unchanged. That is the purpose of a join
    table compared with a foreign key embedded in content (M3-D12,
    source-bound).

    A relation that does not exist is a 404 rather than silent success. Unlike
    creation, there is no final state to normalize here: a caller reaching
    this point may write the Place and therefore already knows it exists.
    """
    place = require_writable_locked(session, Place, context, place_id)
    target = _require_relatable_target(session, context, kind, target_id)

    table = kind.relation.__table__
    # Use `RETURNING` rather than `rowcount`: same information, but obtained as
    # a query result rather than a cursor property.
    removed = session.execute(
        delete(kind.relation)
        .where(
            table.c.place_id == place.id,
            table.c[kind.target_column] == target.id,
        )
        .returning(table.c.place_id)
    ).first()
    _flush(session)

    if removed is None:
        raise NotFoundError("Relation not found.", RELATION_NOT_FOUND)

    _record(session, kind, place, target.id, context.account_id, kind.unlinked_event)
    _flush(session)


def list_targets(
    session: Session,
    context: AuthorizationContext,
    place_id: UUID | str,
    kind: RelationKind,
) -> Sequence[UUID]:
    """Return linked target IDs for a place, oldest link first.

    Deliberately return only IDs. Callers wanting content read it through the
    corresponding domain route and therefore through that domain's own guard.
    A relation list returning content would create a second read path with its
    own authorization, and two read paths drift.

    The Place is read but not locked because a list operation holds nothing.
    """
    from sidebyside.authorization import require_readable

    place = require_readable(session, Place, context, place_id)
    table = kind.relation.__table__
    rows = session.execute(
        select(table.c[kind.target_column])
        .where(table.c.place_id == place.id)
        .order_by(table.c.created_at, table.c[kind.target_column])
    ).scalars()
    return list(rows)


def drop_shared_relations_of_heart_moment(session: Session, heart_moment: HeartMoment) -> None:
    """Remove all shared relations of a HeartMoment (M3-D09).

    Called by the HeartMoment service *before* transition to `OWNER_ONLY` and
    in the same transaction. After commit there must be no point at which the
    moment is private while a relation still exists, because that relation
    would continue proving its existence to the partner.

    Deliberately acquire *no* parent lock afterwards. The Place would be the
    second lock in reverse order and therefore create a deadlock with a
    concurrent relation create. The join rows are sufficient: the create path
    holds the Place but must still wait for this moment's `FOR SHARE` lock.

    The foreign key in `place_heart_moments` catches a missed call by carrying
    the new class into the join row and colliding with its CHECK. This function
    is the intended path that avoids that collision.
    """
    table = PlaceHeartMoment.__table__
    session.execute(delete(PlaceHeartMoment).where(table.c.heart_moment_id == heart_moment.id))
    session.flush()
