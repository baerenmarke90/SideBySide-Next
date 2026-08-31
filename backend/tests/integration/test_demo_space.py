"""Acceptance coverage for the canonical development/demo Space."""

from __future__ import annotations

from datetime import UTC, date, datetime

import pytest
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from sidebyside.attachments import binding as attachment_binding
from sidebyside.attachments import service as attachment_service
from sidebyside.attachments.models import Attachment, AttachmentStatus
from sidebyside.authorization import AuthorizationContext
from sidebyside.collections.models import Collection
from sidebyside.config import Environment
from sidebyside.core.errors import NotFoundError
from sidebyside.dashboard import service as dashboard_service
from sidebyside.demo.assets import import_demo_asset, load_and_validate_assets
from sidebyside.demo.service import (
    ALEX_NAME,
    LEA_NAME,
    PRIVATE_CANARY_LEA,
    create_demo_space,
    reset_demo_space,
)
from sidebyside.engagement.models import Activity, Notification
from sidebyside.gift_ideas.models import GiftIdea
from sidebyside.heart_moments import service as heart_moment_service
from sidebyside.heart_moments.models import HeartMoment
from sidebyside.identity.models import Account
from sidebyside.media import get_media_store
from sidebyside.memories import service as memory_service
from sidebyside.memories.models import Memory
from sidebyside.milestones.models import Milestone
from sidebyside.people.models import ImportantDate, RelatedPerson
from sidebyside.places.models import Place
from sidebyside.plans.models import Plan, PlanStatus
from sidebyside.private_collections.models import PrivateCollection
from sidebyside.private_notes.models import PrivateNote
from sidebyside.profiles.models import ProfilePreference
from sidebyside.relationship import service as relationship_service
from sidebyside.relationship.models import Membership, MembershipStatus, Space
from sidebyside.search import service as search_service
from sidebyside.wishes.models import Wish, WishStatus
from tests.conftest import make_account, make_space, requires_database

pytestmark = [pytest.mark.integration, requires_database]

REFERENCE_DATE = date(2026, 8, 24)
DEMO_PASSWORD = "canonical-demo-test-password"


def _seed(session: Session):  # type: ignore[no-untyped-def]
    return create_demo_space(
        session,
        environment=Environment.TEST,
        lea_password=DEMO_PASSWORD,
        alex_password=DEMO_PASSWORD,
        reference_date=REFERENCE_DATE,
    )


def _count(session: Session, model: type, space_id) -> int:  # type: ignore[no-untyped-def]
    return int(
        session.execute(
            select(func.count()).select_from(model).where(model.space_id == space_id)
        ).scalar_one()
    )


def test_create_is_idempotent_and_representative(session: Session) -> None:
    first = _seed(session)
    second = _seed(session)

    assert first.created is True
    assert second.created is False
    assert second.space_id == first.space_id
    assert second.lea_id == first.lea_id
    assert second.alex_id == first.alex_id

    assert _count(session, Memory, first.space_id) == 10
    assert _count(session, HeartMoment, first.space_id) == 2
    assert _count(session, Milestone, first.space_id) == 3
    assert _count(session, Wish, first.space_id) == 3
    assert _count(session, Plan, first.space_id) == 6
    assert _count(session, Place, first.space_id) == 2
    assert _count(session, Collection, first.space_id) == 2
    assert _count(session, PrivateNote, first.space_id) == 4
    assert _count(session, GiftIdea, first.space_id) == 4
    assert _count(session, PrivateCollection, first.space_id) == 2
    assert _count(session, RelatedPerson, first.space_id) == 3
    assert _count(session, ImportantDate, first.space_id) == 3
    assert _count(session, ProfilePreference, first.space_id) == 6
    assert _count(session, Activity, first.space_id) > 0
    assert _count(session, Notification, first.space_id) >= 2

    attachments = list(
        session.execute(select(Attachment).where(Attachment.space_id == first.space_id)).scalars()
    )
    assert len(attachments) == 12
    assert {attachment.status for attachment in attachments} == {AttachmentStatus.READY.value}

    assert len({attachment.payload.original_name for attachment in attachments}) == 12
    store = get_media_store()
    for attachment in attachments:
        assert store.exists(attachment_service.storage_key_for(attachment))
        if attachment.has_thumbnail:
            assert store.exists(
                attachment_service.storage_key_for(attachment, attachment_service.THUMBNAIL_VARIANT)
            )

    wishes = list(session.execute(select(Wish).where(Wish.space_id == first.space_id)).scalars())
    assert {wish.status for wish in wishes} == {
        WishStatus.OPEN.value,
        WishStatus.PLANNED.value,
        WishStatus.COMPLETED.value,
    }
    plan_statuses = {
        status
        for status in session.execute(
            select(Plan.status).where(Plan.space_id == first.space_id)
        ).scalars()
    }
    assert plan_statuses == {
        PlanStatus.IDEA.value,
        PlanStatus.PLANNED.value,
        PlanStatus.COMPLETED.value,
    }


def test_private_demo_content_stays_owner_only_across_read_models(session: Session) -> None:
    result = _seed(session)
    lea_context = AuthorizationContext(account_id=result.lea_id, space_id=result.space_id)
    alex_context = AuthorizationContext(account_id=result.alex_id, space_id=result.space_id)

    private_heart = session.execute(
        select(HeartMoment).where(
            HeartMoment.space_id == result.space_id,
            HeartMoment.owner_id == result.lea_id,
            HeartMoment.privacy_class == "OWNER_ONLY",
        )
    ).scalar_one()
    with pytest.raises(NotFoundError):
        heart_moment_service.get_heart_moment(session, alex_context, private_heart.id)

    lea_search = search_service.search(session, lea_context, query="Fotostreifen")
    alex_search = search_service.search(session, alex_context, query="Fotostreifen")
    assert lea_search.items
    assert alex_search.items == []

    activity_target_ids = set(
        session.execute(
            select(Activity.target_id).where(Activity.space_id == result.space_id)
        ).scalars()
    )
    assert private_heart.id not in activity_target_ids

    dashboard = dashboard_service.read_dashboard(
        session,
        alex_context,
        at=datetime.combine(REFERENCE_DATE, datetime.min.time(), tzinfo=UTC),
    )
    dashboard_text = " ".join(
        item.title_or_text or ""
        for item in [
            *dashboard.upcoming,
            *dashboard.recent_shared,
            *([dashboard.retrospective] if dashboard.retrospective is not None else []),
        ]
    )
    assert PRIVATE_CANARY_LEA not in dashboard_text


def _canonical_memory_media(session: Session, space_id) -> dict[str, tuple[str, ...]]:  # type: ignore[no-untyped-def]
    memories = list(session.execute(select(Memory).where(Memory.space_id == space_id)).scalars())
    return {
        memory.payload.title: tuple(
            bound.attachment.payload.original_name
            for bound in attachment_binding.attachments_of_memory(session, memory.id)
        )
        for memory in memories
    }


def test_reset_replaces_only_verified_demo_space(session: Session) -> None:
    result = _seed(session)
    old_space_id = result.space_id
    canonical_media = _canonical_memory_media(session, old_space_id)
    assert len(canonical_media) == 10
    assert sum(len(filenames) for filenames in canonical_media.values()) == 11

    old_attachments = list(
        session.execute(select(Attachment).where(Attachment.space_id == old_space_id)).scalars()
    )
    old_attachment_ids = {attachment.id for attachment in old_attachments}
    old_storage_keys = {
        attachment_service.storage_key_for(attachment) for attachment in old_attachments
    }

    lea_context = AuthorizationContext(account_id=result.lea_id, space_id=result.space_id)
    lea_memory = (
        session.execute(
            select(Memory).where(
                Memory.space_id == result.space_id,
                Memory.owner_id == result.lea_id,
            )
        )
        .scalars()
        .first()
    )
    assert lea_memory is not None
    memory_service.replace_attachments(
        session,
        lea_context,
        lea_memory.id,
        expected_version=lea_memory.version,
        entries=[],
    )

    extra = memory_service.create_memory(
        session,
        lea_context,
        title="Besucheränderung vor Reset",
        body="Dieser Eintrag muss beim Reset vollständig verschwinden.",
        happened_on=REFERENCE_DATE,
    )
    asset = load_and_validate_assets().require("memory-breakfast")
    extra_attachment = import_demo_asset(session, lea_context, asset)
    memory_service.replace_attachments(
        session,
        lea_context,
        extra.id,
        expected_version=extra.version,
        entries=[(extra_attachment.id, 0)],
    )
    extra_storage_key = attachment_service.storage_key_for(extra_attachment)

    outsider = make_account(session, "Unrelated User")
    unrelated_space = make_space(session, outsider)
    unrelated_partner = make_account(session, "Unrelated Partner")
    relationship_service.add_member(session, unrelated_space.id, unrelated_partner)
    unrelated_space_id = unrelated_space.id

    reset = reset_demo_space(
        session,
        environment=Environment.TEST,
        reference_date=REFERENCE_DATE,
    )

    assert reset.space_id != old_space_id
    assert session.get(Space, old_space_id) is None
    assert session.get(Space, unrelated_space_id) is not None
    assert (
        not session.execute(select(Attachment.id).where(Attachment.id.in_(old_attachment_ids)))
        .scalars()
        .all()
    )

    store = get_media_store()
    for storage_key in old_storage_keys | {extra_storage_key}:
        assert not store.exists(storage_key)

    restored_attachments = list(
        session.execute(select(Attachment).where(Attachment.space_id == reset.space_id)).scalars()
    )
    assert len(restored_attachments) == 12
    assert len({attachment.payload.original_name for attachment in restored_attachments}) == 12
    assert _canonical_memory_media(session, reset.space_id) == canonical_media

    active_demo_memberships = list(
        session.execute(
            select(Membership).where(
                Membership.account_id.in_([reset.lea_id, reset.alex_id]),
                Membership.status == MembershipStatus.ACTIVE.value,
            )
        ).scalars()
    )
    assert {membership.space_id for membership in active_demo_memberships} == {reset.space_id}
    assert len(active_demo_memberships) == 2

    names = {
        account.display_name
        for account in session.execute(
            select(Account).where(Account.id.in_([reset.lea_id, reset.alex_id]))
        ).scalars()
    }
    assert names == {LEA_NAME, ALEX_NAME}


def test_asset_preflight_failure_leaves_create_and_reset_unmodified(
    session: Session, monkeypatch: pytest.MonkeyPatch
) -> None:
    before_accounts = session.execute(select(func.count()).select_from(Account)).scalar_one()

    def fail_assets():  # type: ignore[no-untyped-def]
        raise RuntimeError("curated asset preflight failed")

    monkeypatch.setattr("sidebyside.demo.service.load_and_validate_assets", fail_assets)
    with pytest.raises(RuntimeError, match="curated asset preflight failed"):
        create_demo_space(
            session,
            environment=Environment.TEST,
            lea_password=DEMO_PASSWORD,
            alex_password=DEMO_PASSWORD,
            reference_date=REFERENCE_DATE,
        )
    assert (
        session.execute(select(func.count()).select_from(Account)).scalar_one() == before_accounts
    )

    monkeypatch.undo()
    result = _seed(session)
    old_space_id = result.space_id
    old_attachment_ids = set(
        session.execute(select(Attachment.id).where(Attachment.space_id == old_space_id)).scalars()
    )
    monkeypatch.setattr("sidebyside.demo.service.load_and_validate_assets", fail_assets)
    with pytest.raises(RuntimeError, match="curated asset preflight failed"):
        reset_demo_space(
            session,
            environment=Environment.TEST,
            reference_date=REFERENCE_DATE,
        )
    assert session.get(Space, old_space_id) is not None
    assert (
        set(
            session.execute(
                select(Attachment.id).where(Attachment.space_id == old_space_id)
            ).scalars()
        )
        == old_attachment_ids
    )


def test_shared_story_has_no_placeholders_or_external_media_urls(session: Session) -> None:
    result = _seed(session)
    memories = list(
        session.execute(select(Memory).where(Memory.space_id == result.space_id)).scalars()
    )
    shared_text = " ".join(memory.payload.model_dump_json() for memory in memories).lower()

    assert {
        "Frühstück in Saarbrücken",
        "Spaziergang am See",
        "Ravioli-Abend",
        "Wochenendtrip nach Trier",
        "Sonnenuntergang nach Feierabend",
        "Picknick im Grünen",
    } <= {memory.payload.title for memory in memories}
    for forbidden in ("${", "{variable}", "todo", "placeholder", "example", "http://", "https://"):
        assert forbidden not in shared_text


def test_production_creation_is_rejected_before_any_write(session: Session) -> None:
    before = session.execute(select(func.count()).select_from(Account)).scalar_one()

    with pytest.raises(RuntimeError, match="never be created in production"):
        create_demo_space(
            session,
            environment=Environment.PRODUCTION,
            lea_password=DEMO_PASSWORD,
            alex_password=DEMO_PASSWORD,
            reference_date=REFERENCE_DATE,
        )

    after = session.execute(select(func.count()).select_from(Account)).scalar_one()
    assert after == before
