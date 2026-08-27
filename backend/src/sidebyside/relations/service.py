"""Fachlogik fuer typisierte M3-Content-Relations.

Drei Dinge tragen diesen Dienst.

**Die Sperrreihenfolge ist Parent, dann Target.** Immer, ohne Ausnahme
(M3-D26). Der Place wird exklusiv gesperrt, das Ziel danach mit `FOR
SHARE`. Die umgekehrte Reihenfolge waere an einer einzigen Stelle bequem -
beim Privacy-Wechsel des HeartMoments - und genau dort entstuende der
Deadlock. Der Privacy-Wechsel sperrt deshalb ausdruecklich *keine* Parents
nach.

**Ein Ziel wird nach der Sperre erneut geprueft, nicht davor.** Zwischen
Nachsehen und Schreiben kann es geloescht oder privat geworden sein. Erst
die Sperre macht die Pruefung haltbar.

**Die Antwort auf ein unzulaessiges Ziel ist immer dieselbe.** Unbekannt,
geloescht, fremder Space, `OWNER_ONLY` - vier verschiedene Sachverhalte,
eine Antwort (`RELATION_TARGET_NOT_FOUND`, 404). Ein Unterschied waere die
Auskunft, die M3-D09 gerade verhindert.
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

if TYPE_CHECKING:  # pragma: no cover - nur fuer die Typpruefung
    from collections.abc import Sequence


class RelatableTarget(Protocol):
    """Was dieser Dienst von einem Ziel braucht - und mehr nicht.

    Die drei Zielmodelle erben `IdMixin` und `PrivateResourceMixin`
    getrennt; es gibt keinen gemeinsamen Obertyp, der beides fuehrt. Statt
    einen einzufuehren, nur damit eine Typpruefung durchgeht, steht hier
    die tatsaechlich benutzte Flaeche: eine ID und eine Privacy-Klasse.
    """

    id: UUID
    privacy_class: str


RELATION_TARGET_NOT_FOUND = "RELATION_TARGET_NOT_FOUND"
RELATION_NOT_FOUND = "RELATION_NOT_FOUND"

_RELATION_SUBJECT_TYPE = "place_relation"


def target_not_found() -> NotFoundError:
    """Die eine Antwort auf jedes unzulaessige Ziel.

    Als Funktion und nicht als Konstante, damit nicht versehentlich
    dieselbe Exception-Instanz zweimal geworfen wird - ein Traceback aus
    einem frueheren Request haengt sonst an einer spaeteren Antwort.
    """
    return NotFoundError("Relation target not found.", RELATION_TARGET_NOT_FOUND)


@dataclass(frozen=True)
class RelationKind:
    """Eine freigegebene Relationsart.

    Die Menge dieser Objekte *ist* die Allowlist. Es gibt keinen Pfad, auf
    dem ein Client einen Zieltyp benennt, den der Server nicht schon kennt
    - genau das trennt typisierte Relationen von der
    `(targetType,targetId)`-Polymorphie, die M3-D08 ausschliesst.
    """

    slug: str
    """Das Wegstueck in der Route: `/places/{placeId}/{slug}/{targetId}`."""

    relation: type[Base]
    target: type[PrivateResourceMixin]
    target_column: str
    event_target_type: Literal["MEMORY", "HEART_MOMENT", "MILESTONE"]
    """Die Zielkategorie im Ereignis.

    Dieselbe geschlossene Menge, die `PublicEventPayload` fuer Comments
    schon fuehrt. Sie wird bewusst wiederverwendet statt erweitert: die
    Allowlist ist die Grenze, an der entschieden wird, was dauerhaft
    gespeichert werden darf, und eine zweite Fassung derselben Kategorie
    haette eine zweite Entscheidung bedeutet.
    """

    linked_event: EventType
    unlinked_event: EventType
    shared_target_only: bool = False
    """Ob das Ziel zwingend gemeinsamer Inhalt sein muss (M3-D09).

    Nur beim HeartMoment wahr. Memory und Milestone sind immer
    `SPACE_SHARED`; fuer sie waere die Pruefung eine Tautologie, die
    spaeter jemand fuer eine echte Bedingung haelt.
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
    """Die Relationsart zu einem Routenstueck - oder 404.

    Ein unbekannter Slug ist keine Validierungsfrage. Er beschreibt eine
    Relation, die es nicht gibt, und bekommt deshalb dieselbe Antwort wie
    ein Ziel, das es nicht gibt.
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
    """Das Ereignis zu einer Relationsaenderung.

    Die Nutzlast traegt IDs und sonst nichts. Weder der Name des Ortes noch
    irgendein Inhalt des Ziels gehoert in ein Event - ein Ereignisstrom ist
    kein privilegierter Leseweg (M3-D06, Abschnitt Redaction).
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
    """Das Ziel sperren und danach beurteilen.

    `require_readable_shared` haelt die Zeile mit `FOR SHARE` gegen das
    Loeschen. Erst danach wird die Privacy-Klasse gelesen: davor waere sie
    eine Momentaufnahme, die bis zum Insert veralten kann.

    Jede Ablehnung des Guards - fehlgeformte ID, unbekannt, fremder Space,
    fremde private Zeile - wird auf dieselbe Antwort gezogen. Der Guard
    wuerde sonst den Fehlercode der Zieldomaene durchreichen und damit
    unterscheiden, welche Art von Ziel gemeint war.
    """
    try:
        found = require_readable_shared(session, kind.target, context, target_id)
    except DomainError as error:
        raise target_not_found() from error

    if kind.shared_target_only and found.privacy_class != PrivacyClass.SPACE_SHARED.value:
        # Ein eigener OWNER_ONLY-HeartMoment ist fuer seinen Eigentuemer
        # lesbar - der Guard laesst ihn deshalb durch. Relationierbar ist
        # er trotzdem nicht: eine gemeinsame Relation auf privaten Inhalt
        # waere fuer den Partner ein Beweis seiner Existenz (M3-D09).
        raise target_not_found()

    return cast("RelatableTarget", found)


def link(
    session: Session,
    context: AuthorizationContext,
    place_id: UUID | str,
    target_id: UUID | str,
    kind: RelationKind,
) -> None:
    """Parent und Ziel verknuepfen - idempotent.

    Reihenfolge nach M3-D26: Place exklusiv sperren, danach das Ziel. Der
    Insert laeuft als `ON CONFLICT DO NOTHING`, weil ein vorheriges
    `SELECT` genau die Luecke oeffnete, die der Primaerschluessel bereits
    schliesst. Ein zweites `PUT` derselben Relation ist deshalb kein
    Konflikt, sondern derselbe Endzustand - und erzeugt dann auch kein
    zweites Ereignis.
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
        # Die Klasse wandert in die Join-Zeile und wird dort vom CHECK
        # festgehalten. Sie stammt aus der bereits gesperrten Zeile, nicht
        # aus einer zweiten Abfrage.
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
    """Die Verknuepfung entfernen - und nur sie.

    Beide Originale bleiben unveraendert bestehen; das ist der ganze Sinn
    einer Join-Tabelle gegenueber einem Fremdschluessel im Inhalt
    (M3-D12, source-bound).

    Eine Relation, die es nicht gibt, ist ein 404 und kein stiller Erfolg.
    Anders als beim Anlegen gibt es hier nichts zu vereinheitlichen: wer
    bis hierher kommt, darf den Place schreiben und kennt damit bereits
    seine Existenz.
    """
    place = require_writable_locked(session, Place, context, place_id)
    target = _require_relatable_target(session, context, kind, target_id)

    table = kind.relation.__table__
    # `RETURNING` statt `rowcount`: dieselbe Auskunft, aber als Ergebnis
    # der Abfrage und nicht als Eigenschaft des Cursors.
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
    """Die verknuepften Ziel-IDs eines Ortes, aelteste Verknuepfung zuerst.

    Bewusst nur IDs. Wer Inhalte will, liest sie ueber die Route der
    jeweiligen Domaene und damit durch deren eigenen Guard - eine
    Relationsliste, die Inhalte mitliefert, waere ein zweiter Leseweg mit
    eigener Autorisierung, und zwei Lesewege driften.

    Der Place wird nur gelesen, nicht gesperrt: eine Liste haelt nichts.
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
    """Alle gemeinsamen Relationen eines HeartMoments entfernen (M3-D09).

    Aufgerufen vom HeartMoment-Dienst *vor* dem Wechsel auf `OWNER_ONLY`,
    in derselben Transaktion. Nach dem Commit darf es keinen Zeitpunkt
    geben, an dem der Moment privat und die Relation noch vorhanden ist -
    sonst waere seine Existenz fuer den Partner weiter beweisbar.

    Es wird ausdruecklich *kein* Parent nachgesperrt. Der Place waere hier
    das zweite Schloss in umgekehrter Reihenfolge, und damit der Deadlock
    gegen einen gleichzeitigen Relation-Create. Die Join-Zeilen allein
    genuegen: der Create haelt den Place, wartet aber ohnehin auf den
    `FOR SHARE` dieses Moments.

    Der Fremdschluessel in `place_heart_moments` faenge einen vergessenen
    Aufruf ab - er zoege die neue Klasse in die Join-Zeile und liefe gegen
    deren CHECK. Diese Funktion ist der Weg, der nicht dagegen laeuft.
    """
    table = PlaceHeartMoment.__table__
    session.execute(delete(PlaceHeartMoment).where(table.c.heart_moment_id == heart_moment.id))
    session.flush()
