"""Derived shared-only Dashboard read model for M4-A.

The Dashboard is intentionally computed from authoritative domain rows. It has
no persistence of its own, so privacy transitions and deletions cannot leave a
stale copied Dashboard record behind.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from enum import StrEnum
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from sidebyside.attachments.binding import attachments_of_memories
from sidebyside.attachments.models import AttachmentStatus
from sidebyside.authorization import AuthorizationContext, PrivacyClass, readable
from sidebyside.chapters.models import Chapter
from sidebyside.collections.models import Collection
from sidebyside.core import clock
from sidebyside.heart_moments.models import HeartMoment
from sidebyside.identity.models import Account
from sidebyside.memories.models import Memory
from sidebyside.milestones.models import Milestone
from sidebyside.people.models import DateRepeat, ImportantDate
from sidebyside.places.models import Place
from sidebyside.plans.models import Plan, PlanStatus
from sidebyside.relationship.models import (
    DurationDisplayMode,
    Membership,
    MembershipStatus,
    SpaceProfile,
)
from sidebyside.wishes.models import Wish

SECTION_LIMIT = 8
MAX_RECOGNITION_TEXT = 160


class DashboardItemType(StrEnum):
    MEMORY = "MEMORY"
    HEART_MOMENT = "HEART_MOMENT"
    MILESTONE = "MILESTONE"
    WISH = "WISH"
    PLAN = "PLAN"
    PLACE = "PLACE"
    CHAPTER = "CHAPTER"
    COLLECTION = "COLLECTION"
    IMPORTANT_DATE = "IMPORTANT_DATE"
    BIRTHDAY = "BIRTHDAY"
    ANNIVERSARY = "ANNIVERSARY"


@dataclass(frozen=True)
class PartnerSummary:
    id: UUID
    display_name: str


@dataclass(frozen=True)
class RelationshipDuration:
    started_on: date
    days_together: int
    display_mode: DurationDisplayMode


@dataclass(frozen=True)
class DashboardItem:
    type: DashboardItemType
    id: UUID
    title_or_text: str | None = None
    occurred_on: date | None = None
    scheduled_at: datetime | None = None
    created_at: datetime | None = None
    preview_attachment_id: UUID | None = None


@dataclass(frozen=True)
class DashboardView:
    space_id: UUID
    partner: PartnerSummary | None
    relationship_duration: RelationshipDuration | None
    retrospective: DashboardItem | None
    upcoming: list[DashboardItem]
    recent_shared: list[DashboardItem]


def read_dashboard(
    session: Session,
    authorization: AuthorizationContext,
    *,
    at: datetime | None = None,
) -> DashboardView:
    """Read the shared relationship overview for one already-authorized Space."""
    account = session.get(Account, authorization.account_id)
    if account is None:
        raise RuntimeError("Authorized Dashboard account disappeared.")

    instant = clock.ensure_utc(at if at is not None else clock.now())
    today = clock.today_in(account.timezone, at=instant)
    profile = session.execute(
        select(SpaceProfile).where(SpaceProfile.space_id == authorization.space_id)
    ).scalar_one_or_none()

    return DashboardView(
        space_id=authorization.space_id,
        partner=_partner(session, authorization),
        relationship_duration=_relationship_duration(profile, today),
        retrospective=_retrospective(session, authorization, today),
        upcoming=_upcoming(session, authorization, profile, today, instant),
        recent_shared=_recent_shared(session, authorization),
    )


def _partner(session: Session, authorization: AuthorizationContext) -> PartnerSummary | None:
    partner = session.execute(
        select(Account)
        .join(Membership, Membership.account_id == Account.id)
        .where(
            Membership.space_id == authorization.space_id,
            Membership.status == MembershipStatus.ACTIVE.value,
            Account.id != authorization.account_id,
            Account.disabled_at.is_(None),
        )
        .order_by(Account.id)
        .limit(1)
    ).scalar_one_or_none()
    if partner is None:
        return None
    return PartnerSummary(id=partner.id, display_name=partner.display_name)


def _relationship_duration(
    profile: SpaceProfile | None,
    today: date,
) -> RelationshipDuration | None:
    if (
        profile is None
        or not profile.show_relationship_duration
        or profile.relationship_started_on is None
    ):
        return None
    return RelationshipDuration(
        started_on=profile.relationship_started_on,
        days_together=(today - profile.relationship_started_on).days,
        display_mode=DurationDisplayMode(profile.duration_display_mode),
    )


def _retrospective(
    session: Session,
    authorization: AuthorizationContext,
    today: date,
) -> DashboardItem | None:
    candidates: list[DashboardItem] = []

    memories = session.execute(
        readable(Memory, authorization).where(Memory.happened_on.is_not(None))
    ).scalars()
    for memory in memories:
        if memory.happened_on is not None and _is_prior_same_day(memory.happened_on, today):
            candidates.append(
                DashboardItem(
                    type=DashboardItemType.MEMORY,
                    id=memory.id,
                    title_or_text=_bounded(memory.payload.title),
                    occurred_on=memory.happened_on,
                )
            )

    milestones = session.execute(readable(Milestone, authorization)).scalars()
    for milestone in milestones:
        if _is_prior_same_day(milestone.happened_on, today):
            candidates.append(
                DashboardItem(
                    type=DashboardItemType.MILESTONE,
                    id=milestone.id,
                    title_or_text=_bounded(milestone.payload.title),
                    occurred_on=milestone.happened_on,
                )
            )

    heart_moments = session.execute(
        readable(HeartMoment, authorization).where(
            HeartMoment.privacy_class == PrivacyClass.SPACE_SHARED.value
        )
    ).scalars()
    for heart_moment in heart_moments:
        if _is_prior_same_day(heart_moment.happened_on, today):
            candidates.append(
                DashboardItem(
                    type=DashboardItemType.HEART_MOMENT,
                    id=heart_moment.id,
                    title_or_text=_bounded(heart_moment.payload.text),
                    occurred_on=heart_moment.happened_on,
                )
            )

    if not candidates:
        return None
    chosen = min(
        candidates,
        key=lambda item: (
            -(item.occurred_on.year if item.occurred_on else 0),
            item.type.value,
            str(item.id),
        ),
    )
    if chosen.type == DashboardItemType.MEMORY:
        galleries = attachments_of_memories(session, [chosen.id])
        preview_id = None
        for bound in galleries.get(chosen.id, []):
            if bound.attachment.status == AttachmentStatus.READY:
                preview_id = bound.attachment.id
                break
        if preview_id is not None:
            chosen = DashboardItem(
                type=chosen.type,
                id=chosen.id,
                title_or_text=chosen.title_or_text,
                occurred_on=chosen.occurred_on,
                scheduled_at=chosen.scheduled_at,
                created_at=chosen.created_at,
                preview_attachment_id=preview_id,
            )
    return chosen


def _is_prior_same_day(value: date, today: date) -> bool:
    return value.year < today.year and (value.month, value.day) == (today.month, today.day)


def _upcoming(
    session: Session,
    authorization: AuthorizationContext,
    profile: SpaceProfile | None,
    today: date,
    instant: datetime,
) -> list[DashboardItem]:
    candidates: list[DashboardItem] = []

    plans = session.execute(
        readable(Plan, authorization)
        .where(
            Plan.status == PlanStatus.PLANNED.value,
            Plan.planned_start.is_not(None),
            Plan.planned_start >= instant,
        )
        .order_by(Plan.planned_start, Plan.id)
        .limit(SECTION_LIMIT)
    ).scalars()
    for plan in plans:
        if plan.planned_start is None:
            continue
        candidates.append(
            DashboardItem(
                type=DashboardItemType.PLAN,
                id=plan.id,
                title_or_text=_bounded(plan.payload.title),
                scheduled_at=clock.ensure_utc(plan.planned_start),
            )
        )

    important_dates = session.execute(
        readable(ImportantDate, authorization).where(
            ImportantDate.privacy_class == PrivacyClass.SPACE_SHARED.value,
            ImportantDate.related_person_id.is_(None),
        )
    ).scalars()
    for important_date in important_dates:
        next_on = _next_important_date(important_date, today)
        if next_on is None:
            continue
        candidates.append(
            DashboardItem(
                type=DashboardItemType.IMPORTANT_DATE,
                id=important_date.id,
                title_or_text=_bounded(important_date.payload.label),
                occurred_on=next_on,
            )
        )

    if profile is not None and profile.relationship_started_on is not None:
        candidates.append(
            DashboardItem(
                type=DashboardItemType.ANNIVERSARY,
                id=profile.id,
                occurred_on=_next_annual(profile.relationship_started_on, today),
            )
        )

    candidates.sort(key=_upcoming_sort_key)
    return candidates[:SECTION_LIMIT]


def _next_important_date(value: ImportantDate, today: date) -> date | None:
    if value.repeats == DateRepeat.NONE.value:
        return value.date if value.date >= today else None
    return _next_annual(value.date, today)


def _next_annual(source: date, today: date) -> date:
    """Return the next real calendar occurrence, including Feb-29 semantics."""
    year = today.year
    while True:
        try:
            candidate = date(year, source.month, source.day)
        except ValueError:
            year += 1
            continue
        if candidate >= today:
            return candidate
        year += 1


def _upcoming_sort_key(item: DashboardItem) -> tuple[datetime, str, str]:
    if item.scheduled_at is not None:
        moment = clock.ensure_utc(item.scheduled_at)
    elif item.occurred_on is not None:
        moment = datetime.combine(
            item.occurred_on,
            datetime.min.time(),
            tzinfo=clock.resolve_zone("UTC"),
        )
    else:
        raise RuntimeError("Upcoming Dashboard item has no occurrence.")
    return moment, item.type.value, str(item.id)


def _recent_shared(
    session: Session,
    authorization: AuthorizationContext,
) -> list[DashboardItem]:
    candidates: list[DashboardItem] = []

    memories = list(
        session.execute(
            readable(Memory, authorization)
            .order_by(Memory.created_at.desc(), Memory.id)
            .limit(SECTION_LIMIT)
        ).scalars()
    )
    memory_galleries = attachments_of_memories(session, [m.id for m in memories])

    for memory in memories:
        preview_id = None
        for bound in memory_galleries.get(memory.id, []):
            if bound.attachment.status == AttachmentStatus.READY:
                preview_id = bound.attachment.id
                break
        candidates.append(
            DashboardItem(
                type=DashboardItemType.MEMORY,
                id=memory.id,
                title_or_text=_bounded(memory.payload.title),
                occurred_on=memory.happened_on,
                created_at=memory.created_at,
                preview_attachment_id=preview_id,
            )
        )

    for milestone in session.execute(
        readable(Milestone, authorization)
        .order_by(Milestone.created_at.desc(), Milestone.id)
        .limit(SECTION_LIMIT)
    ).scalars():
        candidates.append(
            DashboardItem(
                type=DashboardItemType.MILESTONE,
                id=milestone.id,
                title_or_text=_bounded(milestone.payload.title),
                occurred_on=milestone.happened_on,
                created_at=milestone.created_at,
            )
        )

    for heart_moment in session.execute(
        readable(HeartMoment, authorization)
        .where(HeartMoment.privacy_class == PrivacyClass.SPACE_SHARED.value)
        .order_by(HeartMoment.created_at.desc(), HeartMoment.id)
        .limit(SECTION_LIMIT)
    ).scalars():
        candidates.append(
            DashboardItem(
                type=DashboardItemType.HEART_MOMENT,
                id=heart_moment.id,
                title_or_text=_bounded(heart_moment.payload.text),
                occurred_on=heart_moment.happened_on,
                created_at=heart_moment.created_at,
            )
        )

    for wish in session.execute(
        readable(Wish, authorization).order_by(Wish.created_at.desc(), Wish.id).limit(SECTION_LIMIT)
    ).scalars():
        candidates.append(
            DashboardItem(
                type=DashboardItemType.WISH,
                id=wish.id,
                title_or_text=_bounded(wish.payload.title),
                created_at=wish.created_at,
            )
        )

    for plan in session.execute(
        readable(Plan, authorization).order_by(Plan.created_at.desc(), Plan.id).limit(SECTION_LIMIT)
    ).scalars():
        candidates.append(
            DashboardItem(
                type=DashboardItemType.PLAN,
                id=plan.id,
                title_or_text=_bounded(plan.payload.title),
                created_at=plan.created_at,
            )
        )

    for place in session.execute(
        readable(Place, authorization)
        .order_by(Place.created_at.desc(), Place.id)
        .limit(SECTION_LIMIT)
    ).scalars():
        candidates.append(
            DashboardItem(
                type=DashboardItemType.PLACE,
                id=place.id,
                title_or_text=_bounded(place.payload.name),
                created_at=place.created_at,
            )
        )

    for chapter in session.execute(
        readable(Chapter, authorization)
        .order_by(Chapter.created_at.desc(), Chapter.id)
        .limit(SECTION_LIMIT)
    ).scalars():
        candidates.append(
            DashboardItem(
                type=DashboardItemType.CHAPTER,
                id=chapter.id,
                title_or_text=_bounded(chapter.payload.title),
                occurred_on=chapter.start_on,
                created_at=chapter.created_at,
            )
        )

    for collection in session.execute(
        readable(Collection, authorization)
        .order_by(Collection.created_at.desc(), Collection.id)
        .limit(SECTION_LIMIT)
    ).scalars():
        candidates.append(
            DashboardItem(
                type=DashboardItemType.COLLECTION,
                id=collection.id,
                title_or_text=_bounded(collection.payload.title),
                created_at=collection.created_at,
            )
        )

    candidates.sort(
        key=lambda item: (
            -(item.created_at.timestamp() if item.created_at is not None else 0),
            item.type.value,
            str(item.id),
        )
    )
    return candidates[:SECTION_LIMIT]


def _bounded(value: str | None) -> str | None:
    if value is None:
        return None
    return value[:MAX_RECOGNITION_TEXT]
