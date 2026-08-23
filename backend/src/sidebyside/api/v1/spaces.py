"""Space-Endpunkte.

Jeder Zugriff laeuft ueber den Tenant Context. Die Route selbst prueft
keine Berechtigung - sie bekommt einen Kontext, der bereits geprueft ist.
"""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from fastapi import APIRouter
from sqlalchemy import select

from sidebyside.api.deps import DbSession, Tenant
from sidebyside.api.schema import ApiModel
from sidebyside.core.clock import today_utc
from sidebyside.identity.models import Account
from sidebyside.relationship import duration as duration_calc
from sidebyside.relationship.models import Membership, MembershipStatus, SpaceProfile

router = APIRouter(tags=["spaces"])


class PartnerView(ApiModel):
    """Was von einem Account nach aussen geht.

    Ausdruecklich eine Whitelist. Am Account haengen Anmeldedaten und
    Kontaktangaben, die in einer Space-Antwort nichts verloren haben - und
    eine allgemeine Modell-Serialisierung wuerde sie irgendwann mitnehmen.
    """

    id: UUID
    display_name: str


class SpaceView(ApiModel):
    id: UUID
    created_at: datetime
    partners: list[PartnerView]
    relationship_started_on: str | None = None
    show_relationship_duration: bool = True
    duration_display_mode: str = "YEARS_MONTHS"
    relationship_days: int | None = None
    relationship_years: int | None = None
    relationship_months: int | None = None


@router.get("/spaces/{spaceId}", response_model=SpaceView)
def get_space(tenant: Tenant, session: DbSession) -> SpaceView:
    profil = session.execute(
        select(SpaceProfile).where(SpaceProfile.space_id == tenant.space_id)
    ).scalar_one_or_none()

    # Ueber die Mitgliedschaften, nicht ueber eine Account-Abfrage: so kann
    # die Antwort keine Person enthalten, die nicht in diesem Space ist.
    mitglieder = (
        session.execute(
            select(Account)
            .join(Membership, Membership.account_id == Account.id)
            .where(
                Membership.space_id == tenant.space_id,
                Membership.status == MembershipStatus.ACTIVE.value,
            )
            .order_by(Account.created_at)
        )
        .scalars()
        .all()
    )

    ansicht = SpaceView(
        id=tenant.space_id,
        created_at=tenant.membership.space.created_at,
        partners=[PartnerView(id=a.id, display_name=a.display_name or "") for a in mitglieder],
    )

    if profil is None:
        return ansicht

    ansicht.show_relationship_duration = profil.show_relationship_duration
    ansicht.duration_display_mode = profil.duration_display_mode
    if profil.relationship_started_on is not None:
        ansicht.relationship_started_on = profil.relationship_started_on.isoformat()

    # Ist die Anzeige abgeschaltet, wird sie auch nicht mitgeschickt. Ein
    # Wert, den der Client ausblenden soll, ist trotzdem uebertragen worden.
    if profil.show_relationship_duration and profil.relationship_started_on:
        gemeinsam = duration_calc.since(profil.relationship_started_on, today_utc())
        if gemeinsam is not None:
            ansicht.relationship_days = gemeinsam.days
            ansicht.relationship_years = gemeinsam.years
            ansicht.relationship_months = gemeinsam.months

    return ansicht
