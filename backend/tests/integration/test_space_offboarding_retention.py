"""Bounded final retention for #518 Spaces with no active Memberships."""

from __future__ import annotations

from datetime import timedelta
from io import BytesIO
from pathlib import Path
from uuid import uuid4

import pytest
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from sidebyside.attachments import service as attachment_service
from sidebyside.attachments.models import (
    Attachment,
    AttachmentPayload,
    AttachmentStatus,
    MediaType,
)
from sidebyside.authorization import PrivacyClass
from sidebyside.core.clock import now
from sidebyside.domain.events import PublicEventPayload
from sidebyside.identity.models import Account
from sidebyside.media.local import LocalMediaStore
from sidebyside.memories.models import Memory, MemoryPayload
from sidebyside.outbox.models import OutboxEvent
from sidebyside.relationship import retention
from sidebyside.relationship.models import Membership, MembershipStatus, Space
from sidebyside.relationship.service import add_member
from sidebyside.transfer import service as transfer_service
from sidebyside.transfer.models import (
    ExportStatus,
    ImportStatus,
    TransferExport,
    TransferImport,
    TransferScope,
)
from tests.conftest import make_account, make_space, requires_database

pytestmark = [pytest.mark.integration, requires_database]


def _end_space(session: Session, space_id, *, ended_at) -> None:  # type: ignore[no-untyped-def]
    memberships = session.execute(
        select(Membership).where(Membership.space_id == space_id)
    ).scalars()
    for membership in memberships:
        membership.status = MembershipStatus.LEFT.value
        membership.ended_at = ended_at


def _attachment(session: Session, *, owner_id, space_id) -> Attachment:  # type: ignore[no-untyped-def]
    attachment = Attachment(
        space_id=space_id,
        owner_id=owner_id,
        privacy_class=PrivacyClass.OWNER_ONLY.value,
        status=AttachmentStatus.READY.value,
        media_type=MediaType.IMAGE.value,
        declared_mime_type="image/png",
        declared_size=8,
        mime_type="image/png",
        size=8,
        width=1,
        height=1,
        has_thumbnail=False,
        ready_at=now(),
        payload=AttachmentPayload(original_name="retained-space.png"),
    )
    session.add(attachment)
    session.flush()
    return attachment


def test_final_retention_purges_only_due_orphaned_space(
    session: Session,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    instant = now()
    owner = make_account(session, "Anna")
    partner = make_account(session, "Ben")

    due = make_space(session, owner)
    add_member(session, due.id, partner)
    recent = make_space(session, owner)
    add_member(session, recent.id, partner)
    active = make_space(session, owner)
    add_member(session, active.id, partner)
    empty = Space()
    session.add(empty)
    session.flush()

    _end_space(
        session,
        due.id,
        ended_at=instant - retention.SPACE_OFFBOARDING_RETENTION - timedelta(days=1),
    )
    _end_space(session, recent.id, ended_at=instant - timedelta(days=5))

    shared = Memory(
        space_id=due.id,
        owner_id=owner.id,
        privacy_class=PrivacyClass.SPACE_SHARED.value,
        payload=MemoryPayload(title="History", body="final retention fixture"),
    )
    session.add(shared)
    attachment = _attachment(session, owner_id=owner.id, space_id=due.id)

    export = TransferExport(
        space_id=due.id,
        created_by=owner.id,
        scope=TransferScope.SHARED.value,
        status=ExportStatus.READY.value,
        artifact_size=8,
        ready_at=instant - timedelta(days=31),
        expires_at=instant - timedelta(days=30),
    )
    transfer_import = TransferImport(
        space_id=due.id,
        created_by=partner.id,
        status=ImportStatus.FAILED.value,
        artifact_size=8,
        error_code="fixture",
        expires_at=instant - timedelta(days=30),
    )
    session.add_all([export, transfer_import])
    session.add(
        OutboxEvent(
            event_type="memory.created",
            space_id=due.id,
            actor_id=owner.id,
            subject_type="MEMORY",
            subject_id=shared.id,
            payload=PublicEventPayload(),
        )
    )
    session.flush()

    store = LocalMediaStore(tmp_path / "media")
    monkeypatch.setattr(retention, "get_media_store", lambda: store)
    monkeypatch.setattr(attachment_service, "get_media_store", lambda: store)
    store.put(
        attachment_service.storage_key_for(attachment),
        BytesIO(b"original"),
        "image/png",
    )
    store.put(
        transfer_service.export_storage_key(export),
        BytesIO(b"exported"),
        "application/zip",
    )
    store.put(
        transfer_service.import_storage_key(transfer_import),
        BytesIO(b"imported"),
        "application/zip",
    )

    spaces, media, transfers = retention.purge_due_spaces(session, current_time=instant)
    session.flush()

    assert spaces == 1
    assert media == 1
    assert transfers == 2
    assert session.get(Space, due.id) is None
    assert session.get(Space, recent.id) is not None
    assert session.get(Space, active.id) is not None
    assert session.get(Space, empty.id) is not None
    assert session.get(Account, owner.id) is not None
    assert session.get(Account, partner.id) is not None
    assert (
        session.execute(
            select(func.count(OutboxEvent.id)).where(OutboxEvent.space_id == due.id)
        ).scalar_one()
        == 0
    )
    assert not store.exists(attachment_service.storage_key_for(attachment))
    assert not store.exists(transfer_service.export_storage_key(export))
    assert not store.exists(transfer_service.import_storage_key(transfer_import))


def test_retention_starts_when_last_active_membership_ends(session: Session) -> None:
    instant = now()
    owner = make_account(session, "Anna")
    partner = make_account(session, "Ben")
    space = make_space(session, owner)
    add_member(session, space.id, partner)

    memberships = {
        membership.account_id: membership
        for membership in session.execute(
            select(Membership).where(Membership.space_id == space.id)
        ).scalars()
    }
    memberships[owner.id].status = MembershipStatus.LEFT.value
    memberships[owner.id].ended_at = (
        instant - retention.SPACE_OFFBOARDING_RETENTION - timedelta(days=1)
    )
    memberships[partner.id].status = MembershipStatus.LEFT.value
    memberships[partner.id].ended_at = instant - timedelta(days=5)
    session.flush()

    result = retention.purge_due_spaces(session, current_time=instant)

    assert result == (0, 0, 0)
    assert session.get(Space, space.id) is not None


class _FailDeleteOnceStore(LocalMediaStore):
    def __init__(self, root: Path) -> None:
        super().__init__(root)
        self.failed = False

    def delete(self, storage_key: str) -> None:
        if not self.failed and "/attachments/" in storage_key:
            self.failed = True
            raise OSError("synthetic provider failure")
        super().delete(storage_key)


def test_provider_failure_keeps_due_space_retryable(
    session: Session,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    instant = now()
    owner = make_account(session, "Anna")
    space = make_space(session, owner)
    _end_space(
        session,
        space.id,
        ended_at=instant - retention.SPACE_OFFBOARDING_RETENTION - timedelta(days=1),
    )
    attachment = _attachment(session, owner_id=owner.id, space_id=space.id)
    session.flush()

    store = _FailDeleteOnceStore(tmp_path / "media")
    monkeypatch.setattr(retention, "get_media_store", lambda: store)
    monkeypatch.setattr(attachment_service, "get_media_store", lambda: store)
    store.put(
        attachment_service.storage_key_for(attachment),
        BytesIO(b"original"),
        "image/png",
    )

    first = retention.purge_due_spaces(session, current_time=instant)
    session.flush()

    assert first[0] == 0
    assert session.get(Space, space.id) is not None
    assert attachment.status == AttachmentStatus.DELETE_FAILED.value

    second = retention.purge_due_spaces(session, current_time=instant)
    session.flush()

    assert second[0] == 1
    assert session.get(Space, space.id) is None
    assert not store.exists(attachment_service.storage_key_for(attachment))


def test_retention_scheduler_is_idempotent(session: Session) -> None:
    first = retention.ensure_scheduled(session)
    second = retention.ensure_scheduled(session)

    assert first is not None
    assert second is None
    assert first.kind == retention.JOB_KIND
    assert first.payload == {}
    assert first.id != uuid4()
