"""Space-Endpunkte.

Jeder Zugriff laeuft ueber den Tenant Context. Die Route selbst prueft
keine Berechtigung - sie bekommt einen Kontext, der bereits geprueft ist.
"""

from __future__ import annotations

from datetime import date, datetime
from uuid import UUID

from fastapi import APIRouter, Response
from sqlalchemy import select

from sidebyside.api.concurrency import IfMatchVersion, etag_for
from sidebyside.api.deps import DbSession, Tenant, TenantContext
from sidebyside.api.errors import ProblemDetails
from sidebyside.api.schema import ApiModel
from sidebyside.core.clock import today_in
from sidebyside.db.mixins import INITIAL_VERSION
from sidebyside.identity.models import Account
from sidebyside.relationship import duration as duration_calc
from sidebyside.relationship import profile as profile_service
from sidebyside.relationship.models import (
    DurationDisplayMode,
    Membership,
    MembershipStatus,
    SpaceProfile,
)

router = APIRouter(tags=["spaces"])

ETAG_KOPF = {
    "ETag": {
        "description": "Die Version der Ressource. Gehoert unveraendert in das "
        "`If-Match` des naechsten Schreibzugriffs.",
        "schema": {"type": "string"},
    }
}
"""Der ETag steht im Vertrag, weil ein Client ohne ihn nicht schreiben kann."""


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


class SpaceProfileView(ApiModel):
    """Das Beziehungsprofil eines Space.

    `version` ist der Stand, den ein spaeterer Schreibzugriff per `If-Match`
    vorlegen muss. Die Antwort traegt ihn zusaetzlich als ETag.
    """

    space_id: UUID
    version: int
    relationship_started_on: date | None = None
    show_relationship_duration: bool = True
    duration_display_mode: DurationDisplayMode = DurationDisplayMode.YEARS_MONTHS
    relationship_days: int | None = None
    relationship_years: int | None = None
    relationship_months: int | None = None


class SpaceProfileUpdate(ApiModel):
    """Der vollstaendige neue Stand des Profils.

    Alle drei Felder sind Pflicht. Ein weggelassenes Feld waere sonst nicht
    von "auf leer setzen" zu unterscheiden - und der Unterschied entscheidet
    darueber, ob ein Beziehungsbeginn erhalten bleibt oder verschwindet.
    `relationshipStartedOn` wird mit `null` ausdruecklich geloescht.
    """

    relationship_started_on: date | None
    show_relationship_duration: bool
    duration_display_mode: DurationDisplayMode


def _mit_dauer(
    ansicht: SpaceProfileView | SpaceView,
    profil: SpaceProfile,
    today: date,
) -> None:
    """Die gemeinsame Zeit ergaenzen, sofern sie ueberhaupt gezeigt wird.

    Ist die Anzeige abgeschaltet, wird sie auch nicht mitgeschickt. Ein
    Wert, den der Client ausblenden soll, ist trotzdem uebertragen worden.
    """
    if not profil.show_relationship_duration or profil.relationship_started_on is None:
        return

    gemeinsam = duration_calc.since(profil.relationship_started_on, today)
    if gemeinsam is None:
        return

    ansicht.relationship_days = gemeinsam.days
    ansicht.relationship_years = gemeinsam.years
    ansicht.relationship_months = gemeinsam.months


def _profile_view(space_id: UUID, profil: SpaceProfile | None, today: date) -> SpaceProfileView:
    """Die Profilansicht - auch fuer einen Space, der noch keine Zeile hat.

    Ein Space ohne Profilzeile ist ein Altbestand. Er bekommt hier dieselben
    Standardwerte, die der erste Schreibzugriff anlegen wuerde, samt der
    Version, die dieser dann vorfindet. Ein Lesezugriff legt bewusst nichts
    an.
    """
    if profil is None:
        return SpaceProfileView(space_id=space_id, version=INITIAL_VERSION)

    ansicht = SpaceProfileView(
        space_id=space_id,
        version=profil.version,
        relationship_started_on=profil.relationship_started_on,
        show_relationship_duration=profil.show_relationship_duration,
        duration_display_mode=DurationDisplayMode(profil.duration_display_mode),
    )
    _mit_dauer(ansicht, profil, today)
    return ansicht


def _today_for(tenant: TenantContext) -> date:
    """Der heutige Tag aus Sicht der lesenden Person.

    Gemeinsame Tage und Jahrestage wechseln um Mitternacht am Ort dieser
    Person. `today_utc()` waere fuer westlich von UTC lebende Menschen bis
    zu einen Tag zu weit und fuer oestlich lebende einen Tag zu kurz.
    """
    return today_in(tenant.account.timezone)


@router.get("/spaces/{spaceId}", response_model=SpaceView)
def get_space(tenant: Tenant, session: DbSession) -> SpaceView:
    profil = profile_service.load(session, tenant.space_id)

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

    _mit_dauer(ansicht, profil, _today_for(tenant))
    return ansicht


@router.get(
    "/spaces/{spaceId}/profile",
    response_model=SpaceProfileView,
    responses={200: {"headers": ETAG_KOPF}},
)
def get_space_profile(tenant: Tenant, session: DbSession, response: Response) -> SpaceProfileView:
    ansicht = _profile_view(
        tenant.space_id,
        profile_service.load(session, tenant.space_id),
        _today_for(tenant),
    )
    response.headers["ETag"] = etag_for(ansicht.version)
    return ansicht


@router.put(
    "/spaces/{spaceId}/profile",
    response_model=SpaceProfileView,
    responses={
        200: {"headers": ETAG_KOPF},
        409: {
            "model": ProblemDetails,
            "description": (
                "Die vorgelegte Version ist nicht mehr aktuell. Es wurde nichts "
                "geaendert; der aktuelle Stand ist neu zu laden."
            ),
        },
    },
)
def update_space_profile(
    tenant: Tenant,
    session: DbSession,
    response: Response,
    body: SpaceProfileUpdate,
    expected_version: IfMatchVersion,
) -> SpaceProfileView:
    """Das Beziehungsprofil ersetzen.

    Der Aufrufer legt mit `If-Match` die Version vor, die er gelesen hat.
    Hat der Partner inzwischen geschrieben, antwortet der Endpunkt mit 409
    und aendert nichts - ein stilles Ueberschreiben gaebe es sonst genau
    dann, wenn beide gleichzeitig am selben Profil arbeiten.
    """
    heute = _today_for(tenant)
    profil = profile_service.update(
        session,
        tenant.space_id,
        expected_version=expected_version,
        relationship_started_on=body.relationship_started_on,
        show_relationship_duration=body.show_relationship_duration,
        duration_display_mode=body.duration_display_mode,
        today=heute,
    )

    ansicht = _profile_view(tenant.space_id, profil, heute)
    response.headers["ETag"] = etag_for(ansicht.version)
    return ansicht
