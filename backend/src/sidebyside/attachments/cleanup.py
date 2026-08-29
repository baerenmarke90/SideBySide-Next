"""Retention and cleanup for attachments.

Retention periods are defined by M2-D12 and M2-D20. This job does not decide
them; it makes those rules actually happen. A deadline that exists only in a
document is not an enforced deadline.

The job follows the same pattern as security maintenance: an ordinary task in
the existing queue that schedules its next run after completing. No second
scheduler and no container cron are introduced.
"""

from __future__ import annotations

import logging
from datetime import timedelta
from typing import Any
from uuid import UUID

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from sidebyside.attachments import service
from sidebyside.attachments.models import Attachment, AttachmentStatus
from sidebyside.jobs import queue
from sidebyside.jobs.models import Job, JobStatus
from sidebyside.jobs.worker import JobRegistry, registry

log = logging.getLogger(__name__)

MEDIA_CLEANUP = "media_cleanup"

CLEANUP_INTERVAL = timedelta(minutes=30)
"""The media pipeline requires at least hourly cleanup.

A thirty-minute interval still satisfies that guarantee if one run is missed.
"""

UPLOAD_RETENTION = timedelta(hours=24)
"""Retention for PENDING, UPLOADING, and FAILED states under M2-D12."""

_LOCK_KEY = 8_150_214
"""Dedicated advisory-lock key separate from security maintenance.

Sharing the same lock would couple both maintenance chains and let a long media
run delay security maintenance.
"""


def _lock(session: Session) -> None:
    session.execute(select(func.pg_advisory_xact_lock(_LOCK_KEY)))


def _open_jobs(session: Session, *statuses: JobStatus) -> int:
    return int(
        session.execute(
            select(func.count())
            .select_from(Job)
            .where(Job.kind == MEDIA_CLEANUP, Job.status.in_([s.value for s in statuses]))
        ).scalar_one()
    )


def ensure_scheduled(session: Session) -> Job | None:
    _lock(session)
    if _open_jobs(session, JobStatus.PENDING, JobStatus.RUNNING):
        return None
    return queue.enqueue(session, MEDIA_CLEANUP)


def schedule_next(session: Session, *, delay: timedelta | None = None) -> Job | None:
    _lock(session)
    if _open_jobs(session, JobStatus.PENDING):
        return None
    return queue.enqueue(session, MEDIA_CLEANUP, delay=delay or CLEANUP_INTERVAL)


def _expire_stale_uploads(session: Session) -> int:
    """Discard started and failed uploads after 24 hours.

    UPLOADING uses the last server-observed activity. Other states use creation
    time because an upload that never transferred bytes has no later activity.
    """
    candidates = session.execute(
        select(Attachment).where(
            Attachment.status.in_(
                [
                    AttachmentStatus.PENDING.value,
                    AttachmentStatus.UPLOADING.value,
                    AttachmentStatus.FAILED.value,
                ]
            )
        )
    ).scalars()

    affected = 0
    for attachment in candidates:
        reference = attachment.created_at
        if attachment.status == AttachmentStatus.UPLOADING.value and attachment.uploaded_at:
            reference = attachment.uploaded_at
        elif attachment.status == AttachmentStatus.FAILED.value and attachment.failed_at:
            reference = attachment.failed_at
        if service.expired(reference, UPLOAD_RETENTION):
            service.mark_for_deletion(session, attachment)
            affected += 1
    return affected


def _expire_unbound_ready(session: Session) -> int:
    """Discard unbound READY attachments after 60 minutes (M2-D20).

    Only unbound attachments expire this way. Once bound, lifetime follows the
    parent. Rows are locked so a concurrent bind occurs entirely before or after
    cleanup rather than in between; otherwise a fresh relation could point at a
    file already being removed.
    """
    from sidebyside.attachments import binding

    candidates = session.execute(
        select(Attachment)
        .where(Attachment.status == AttachmentStatus.READY.value)
        .with_for_update(skip_locked=True)
    ).scalars()

    affected = 0
    for attachment in candidates:
        if not service.expired(attachment.ready_at, service.BINDING_WINDOW):
            continue
        if binding.parent_of(session, attachment.id) is not None:
            continue
        service.mark_for_deletion(session, attachment)
        affected += 1
    return affected


def _purge_marked(session: Session) -> tuple[int, int]:
    """Remove provider objects without making failures visible again."""
    candidates = session.execute(
        select(Attachment)
        .where(
            or_(
                Attachment.status == AttachmentStatus.DELETING.value,
                Attachment.status == AttachmentStatus.DELETE_FAILED.value,
            )
        )
        .with_for_update(skip_locked=True)
    ).scalars()

    removed = 0
    failed = 0
    for attachment in candidates:
        if service.purge(session, attachment):
            removed += 1
        else:
            failed += 1
    return removed, failed


def run_media_cleanup(session: Session, payload: dict[str, Any]) -> None:
    del payload

    expired_uploads = _expire_stale_uploads(session)
    expired_unbound = _expire_unbound_ready(session)
    session.flush()
    removed, failed = _purge_marked(session)

    log.info(
        "media cleanup completed",
        extra={
            "expired_uploads": expired_uploads,
            "expired_unbound_ready": expired_unbound,
            "purged": removed,
            "purge_failures": failed,
        },
    )

    schedule_next(session)


def run_attachment_validation(session: Session, payload: dict[str, Any]) -> None:
    identifier = payload.get("attachmentId")
    if not isinstance(identifier, str):
        return
    service.validate(session, UUID(identifier))


def register_handlers(target: JobRegistry | None = None) -> None:
    """Register media jobs with a worker registry."""
    destination = target if target is not None else registry
    if destination.get(MEDIA_CLEANUP) is None:
        destination.register(MEDIA_CLEANUP, run_media_cleanup)
    if destination.get(service.ATTACHMENT_VALIDATION) is None:
        destination.register(service.ATTACHMENT_VALIDATION, run_attachment_validation)
