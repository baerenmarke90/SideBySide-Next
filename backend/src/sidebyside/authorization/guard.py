"""Die Abfragegrenze fuer private Ressourcen.

Alles, was eine Domaene braucht, um privat zu sein, steht hier - und nur
hier. Eine Domaene beschreibt ihre Daten (`PrivateResourceMixin`) und ruft
diese Funktionen auf; sie formuliert die Sichtbarkeitsbedingung nicht
selbst. Ein zweiter, per Hand geschriebener Guard waere ein zweiter Ort,
an dem er falsch sein kann.

Die Bedingung ist immer Teil der Abfrage. Es gibt in diesem Modul bewusst
keine Funktion, die eine bereits geladene Zeile prueft: eine solche
Funktion wuerde frueher oder spaeter benutzt, und dann waere die Zeile
gelesen worden, bevor jemand nach der Berechtigung gefragt hat.
"""

from __future__ import annotations

from uuid import UUID

from sqlalchemy import Select, select
from sqlalchemy.orm import Session

from sidebyside.authorization.models import PrivateResource
from sidebyside.authorization.privacy import (
    AuthorizationContext,
    AuthorizationErrorCode,
    ResourceAbsence,
)
from sidebyside.authorization.rules import Access, access_clause
from sidebyside.core.errors import ForbiddenError
from sidebyside.core.ids import parse_id


def absence_of(model: type[PrivateResource]) -> ResourceAbsence:
    return model.privacy_absence


def readable[ResourceT: PrivateResource](
    model: type[ResourceT], context: AuthorizationContext
) -> Select[tuple[ResourceT]]:
    """Der Einstieg fuer jede Liste, Suche und Zaehlung.

    Wer von hier ausgeht, kann die Bedingung nicht vergessen: sie steht
    bereits im Statement, bevor die Domaene ihre eigenen Filter,
    Sortierungen und Grenzen anhaengt. Ein `count()` auf diesem Statement
    zaehlt deshalb auch nur Sichtbares - eine Trefferzahl ist sonst selbst
    schon eine Auskunft.
    """
    return select(model).where(access_clause(model, context, Access.READ))


def writable[ResourceT: PrivateResource](
    model: type[ResourceT], context: AuthorizationContext
) -> Select[tuple[ResourceT]]:
    """Dasselbe fuer aendernde Zugriffe."""
    return select(model).where(access_clause(model, context, Access.WRITE))


def _identifier(value: UUID | str) -> UUID | None:
    return value if isinstance(value, UUID) else parse_id(value)


def require_readable[ResourceT: PrivateResource](
    session: Session,
    model: type[ResourceT],
    context: AuthorizationContext,
    resource_id: UUID | str,
) -> ResourceT:
    """Eine Ressource lesen - oder erfahren, dass es sie nicht gibt.

    Fehlgeformte ID, unbekannte ID, fremder Space und fremde private Zeile
    enden in derselben Antwort. Die ID wird nicht vorab nachgeschlagen und
    danach beurteilt; sie ist eine Bedingung derselben Abfrage.
    """
    absence = absence_of(model)
    identifier = _identifier(resource_id)
    if identifier is None:
        raise absence.error()

    found = session.execute(
        readable(model, context).where(model.id == identifier)
    ).scalar_one_or_none()

    if found is None:
        raise absence.error()
    return found


def require_writable[ResourceT: PrivateResource](
    session: Session,
    model: type[ResourceT],
    context: AuthorizationContext,
    resource_id: UUID | str,
) -> ResourceT:
    """Eine Ressource aendern duerfen.

    Zwei verschiedene Ablehnungen, und der Unterschied ist Absicht:

    Was der Account nicht lesen darf, existiert fuer ihn nicht - 404, wie
    beim Lesen, sonst waere die abweichende Antwort die Auskunft, die
    `OWNER_ONLY` gerade verhindern soll.

    Was er lesen darf, aber nicht aendern - eine geteilte Zeile des
    Partners - ergibt 403. Ihre Existenz ist ihm ohnehin bekannt; ein 404
    waere hier kein Schutz, sondern eine Luege ueber etwas, das er gerade
    angezeigt bekommt.

    Beide Bedingungen werden in einer Abfrage beantwortet, damit zwischen
    Lese- und Schreibpruefung nichts liegt, was sich aendern koennte.
    """
    absence = absence_of(model)
    identifier = _identifier(resource_id)
    if identifier is None:
        raise absence.error()

    row = session.execute(
        select(model, access_clause(model, context, Access.WRITE).label("is_writable"))
        .where(access_clause(model, context, Access.READ))
        .where(model.id == identifier)
    ).one_or_none()

    if row is None:
        raise absence.error()

    found: ResourceT = row[0]
    if not row[1]:
        raise ForbiddenError(
            "This resource belongs to someone else.",
            AuthorizationErrorCode.NOT_RESOURCE_OWNER,
        )
    return found
