"""Space endpoints.

Every access passes through the tenant context. Routes do not repeat the
authorization check; they receive a context that has already been verified.
"""

from __future__ import annotations

from datetime import date, datetime
from uuid import UUID

from fastapi import APIRouter, Response
from sqlalchemy import select

from sidebyside.api.concurrency import IfMatchVersion, etag_for
from sidebyside.api.deps import DbSession, Tenant, TenantContext
from sidebyside.api.errors import problem_responses
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

ETAG_HEADERS = {
    "ETag": {
        "description": (
            "Resource version. Send it unchanged in the next write request's `If-Match` header."
        ),
        "schema": {"type": "string"},
    }
}
"""ETag is part of the contract because clients cannot write without it."""


class PartnerView(ApiModel):
    """Account projection exposed through a space response.

    This is deliberately an allowlist. Accounts also contain authentication
    and contact data that do not belong in a space response; serializing the
    general model would eventually expose such fields by accident.
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
    """Relationship profile of a space.

    ``version`` is the state a later write must supply through ``If-Match``.
    The response also carries that version as an ETag.
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
    """Complete replacement state for a relationship profile.

    All three fields are required. Otherwise an omitted field could not be
    distinguished from clearing it, and that distinction determines whether a
    relationship start date is preserved or removed. ``relationshipStartedOn``
    is explicitly removed by sending ``null``.
    """

    relationship_started_on: date | None
    show_relationship_duration: bool
    duration_display_mode: DurationDisplayMode


def _add_duration(
    view: SpaceProfileView | SpaceView,
    profile: SpaceProfile,
    today: date,
) -> None:
    """Add relationship duration when the profile permits it to be shown.

    When display is disabled, the value is not transmitted at all. A value the
    client is merely told to hide has still been disclosed.
    """
    if not profile.show_relationship_duration or profile.relationship_started_on is None:
        return

    duration = duration_calc.since(profile.relationship_started_on, today)
    if duration is None:
        return

    view.relationship_days = duration.days
    view.relationship_years = duration.years
    view.relationship_months = duration.months


def _profile_view(space_id: UUID, profile: SpaceProfile | None, today: date) -> SpaceProfileView:
    """Build the profile view, including for a space without a profile row.

    A space without a profile row is legacy state. Reads project the same
    defaults that the first write would create, including the version that
    write will observe. Reads intentionally do not create database state.
    """
    if profile is None:
        return SpaceProfileView(space_id=space_id, version=INITIAL_VERSION)

    view = SpaceProfileView(
        space_id=space_id,
        version=profile.version,
        relationship_started_on=profile.relationship_started_on,
        show_relationship_duration=profile.show_relationship_duration,
        duration_display_mode=DurationDisplayMode(profile.duration_display_mode),
    )
    _add_duration(view, profile, today)
    return view


def _today_for(tenant: TenantContext) -> date:
    """Return today's date from the reading account's timezone.

    Shared-day counters and anniversaries roll over at midnight where that
    person is located. ``today_utc()`` would be up to one day ahead for users
    west of UTC and one day behind for users east of UTC.
    """
    return today_in(tenant.account.timezone)


@router.get(
    "/spaces/{spaceId}",
    response_model=SpaceView,
    responses=problem_responses(401, 404),
)
def get_space(tenant: Tenant, session: DbSession) -> SpaceView:
    profile = profile_service.load(session, tenant.space_id)

    # Query through memberships rather than Accounts directly so the response
    # cannot include a person who is not a member of this space.
    members = (
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

    view = SpaceView(
        id=tenant.space_id,
        created_at=tenant.membership.space.created_at,
        partners=[PartnerView(id=a.id, display_name=a.display_name or "") for a in members],
    )

    if profile is None:
        return view

    view.show_relationship_duration = profile.show_relationship_duration
    view.duration_display_mode = profile.duration_display_mode
    if profile.relationship_started_on is not None:
        view.relationship_started_on = profile.relationship_started_on.isoformat()

    _add_duration(view, profile, _today_for(tenant))
    return view


@router.get(
    "/spaces/{spaceId}/profile",
    response_model=SpaceProfileView,
    responses={
        200: {"headers": ETAG_HEADERS},
        **problem_responses(401, 404),
    },
)
def get_space_profile(tenant: Tenant, session: DbSession, response: Response) -> SpaceProfileView:
    view = _profile_view(
        tenant.space_id,
        profile_service.load(session, tenant.space_id),
        _today_for(tenant),
    )
    response.headers["ETag"] = etag_for(view.version)
    return view


@router.put(
    "/spaces/{spaceId}/profile",
    response_model=SpaceProfileView,
    responses={
        200: {"headers": ETAG_HEADERS},
        **problem_responses(
            401,
            404,
            409,
            422,
            descriptions={
                409: (
                    "The supplied version is no longer current. Nothing was changed; "
                    "reload the latest state before retrying."
                )
            },
        ),
    },
)
def update_space_profile(
    tenant: Tenant,
    session: DbSession,
    response: Response,
    body: SpaceProfileUpdate,
    expected_version: IfMatchVersion,
) -> SpaceProfileView:
    """Replace the relationship profile.

    The caller supplies the version it read through ``If-Match``. If the
    partner has written in the meantime, the endpoint returns 409 and changes
    nothing; otherwise simultaneous edits could silently overwrite each other.
    """
    today = _today_for(tenant)
    profile = profile_service.update(
        session,
        tenant.space_id,
        expected_version=expected_version,
        relationship_started_on=body.relationship_started_on,
        show_relationship_duration=body.show_relationship_duration,
        duration_display_mode=body.duration_display_mode,
        today=today,
    )

    view = _profile_view(tenant.space_id, profile, today)
    response.headers["ETag"] = etag_for(view.version)
    return view
