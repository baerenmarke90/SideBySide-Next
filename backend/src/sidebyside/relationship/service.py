"""Mitgliedschaft und Zugriff auf einen Space.

Hier steht die zentrale Sicherheitsinvariante des Produkts. Jeder Zugriff
auf Space-Daten laeuft ueber `require_membership`, und zwar BEVOR
irgendeine Ressource geladen wird.

Es gibt keinen Datenzugriff allein anhand einer Ressourcen-ID.
"""

from __future__ import annotations

from collections.abc import Sequence
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from sidebyside.core.clock import now
from sidebyside.core.errors import ConflictError, NotFoundError
from sidebyside.identity.models import Account
from sidebyside.relationship.models import (
    MAX_ACTIVE_PARTNERS,
    Membership,
    MembershipRole,
    MembershipStatus,
    Space,
    SpaceProfile,
)


class SpaceErrorCode:
    NOT_FOUND = "SPACE_NOT_FOUND"
    FULL = "SPACE_FULL"
    ALREADY_MEMBER = "ACCOUNT_ALREADY_MEMBER"


def require_membership(session: Session, account: Account, space_id: UUID) -> Membership:
    """Die aktive Mitgliedschaft - oder 404.

    Bewusst NotFoundError und nicht ForbiddenError: ein 403 bestaetigt, dass
    es den Space gibt. Wer fremde IDs durchprobiert, soll nicht erfahren,
    welche davon existieren. Fuer den Aufrufer ist ein fremder Space
    ununterscheidbar von einem, den es nicht gibt.

    Auch eine beendete Mitgliedschaft fuehrt hierher: wer den Space
    verlassen hat, sieht seine Inhalte nicht mehr.
    """
    mitgliedschaft = session.execute(
        select(Membership).where(
            Membership.account_id == account.id,
            Membership.space_id == space_id,
            Membership.status == MembershipStatus.ACTIVE.value,
        )
    ).scalar_one_or_none()

    if mitgliedschaft is None:
        raise NotFoundError("Space not found.", SpaceErrorCode.NOT_FOUND)

    return mitgliedschaft


def _ensure_partner_profile(session: Session, space_id: UUID, account_id: UUID) -> None:
    """Profil-Lifecycle an den Membership-Lifecycle koppeln.

    Der Import bleibt lokal, damit Relationship- und Profiles-Domain keine
    zyklische Modulinitialisierung erzeugen.
    """
    from sidebyside.profiles.service import ensure_profile

    ensure_profile(session, space_id, account_id)


def create_space(session: Session, founder: Account) -> Space:
    """Einen Space anlegen und den Gruender als Partner aufnehmen."""
    space = Space()
    session.add(space)
    session.flush()

    session.add(SpaceProfile(space_id=space.id))
    session.add(
        Membership(
            space_id=space.id,
            account_id=founder.id,
            role=MembershipRole.PARTNER.value,
            status=MembershipStatus.ACTIVE.value,
            joined_at=now(),
        )
    )
    session.flush()
    _ensure_partner_profile(session, space.id, founder.id)
    return space


def active_memberships(session: Session, space_id: UUID) -> Sequence[Membership]:
    return (
        session.execute(
            select(Membership).where(
                Membership.space_id == space_id,
                Membership.status == MembershipStatus.ACTIVE.value,
            )
        )
        .scalars()
        .all()
    )


def add_member(session: Session, space_id: UUID, account: Account) -> Membership:
    """Einen Account in einen Space aufnehmen.

    Die Obergrenze wird hier geprueft, nicht erst beim Annehmen einer
    Einladung: ein Paar-Space hat hoechstens zwei aktive Partner, und diese
    Regel darf nicht davon abhaengen, ueber welchen Weg jemand hereinkommt.

    Die Space-Zeile serialisiert Pruefung und Aenderung bis zum Commit. So
    koennen auch zwei verschiedene Einladungen den letzten freien Platz
    nicht gleichzeitig belegen.
    """
    space = session.execute(
        select(Space).where(Space.id == space_id).with_for_update()
    ).scalar_one_or_none()
    if space is None:
        raise NotFoundError("Space not found.", SpaceErrorCode.NOT_FOUND)

    vorhanden = session.execute(
        select(Membership).where(
            Membership.space_id == space_id,
            Membership.account_id == account.id,
        )
    ).scalar_one_or_none()

    if vorhanden is not None and vorhanden.is_active:
        raise ConflictError("Account is already a member.", SpaceErrorCode.ALREADY_MEMBER)

    if len(active_memberships(session, space_id)) >= MAX_ACTIVE_PARTNERS:
        raise ConflictError("This space already has two partners.", SpaceErrorCode.FULL)

    if vorhanden is not None:
        # Eine frueher beendete Mitgliedschaft wird wiederbelebt statt
        # doppelt angelegt - die Eindeutigkeit je Space und Account bleibt.
        vorhanden.status = MembershipStatus.ACTIVE.value
        vorhanden.joined_at = now()
        vorhanden.ended_at = None
        session.flush()
        _ensure_partner_profile(session, space_id, account.id)
        return vorhanden

    mitgliedschaft = Membership(
        space_id=space_id,
        account_id=account.id,
        role=MembershipRole.PARTNER.value,
        status=MembershipStatus.ACTIVE.value,
        joined_at=now(),
    )
    session.add(mitgliedschaft)
    session.flush()
    _ensure_partner_profile(session, space_id, account.id)
    return mitgliedschaft


def end_membership(membership: Membership, *, removed: bool = False) -> None:
    """Eine Mitgliedschaft beenden, ohne sie zu loeschen.

    Geloescht waere spaeter nicht mehr nachvollziehbar, wer einen Inhalt
    angelegt hat.
    """
    membership.status = MembershipStatus.REMOVED.value if removed else MembershipStatus.LEFT.value
    membership.ended_at = now()


def partner_of(session: Session, space_id: UUID, account: Account) -> Account | None:
    """Der jeweils andere aktive Partner, falls es ihn gibt."""
    mitglieder = active_memberships(session, space_id)
    for mitgliedschaft in mitglieder:
        if mitgliedschaft.account_id != account.id:
            return session.get(Account, mitgliedschaft.account_id)
    return None
