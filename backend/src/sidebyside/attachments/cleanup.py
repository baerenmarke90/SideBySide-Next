"""Aufbewahrung und Aufraeumen fuer Attachments.

Die Fristen stehen in M2-D12 und M2-D20. Dieser Job entscheidet nichts
ueber sie - er sorgt dafuer, dass sie tatsaechlich eintreten. Eine Frist,
die nur im Dokument steht, ist keine Frist.

Er folgt demselben Muster wie die Security-Wartung: eine gewoehnliche
Aufgabe in der vorhandenen Warteschlange, die sich nach getaner Arbeit
selbst neu einstellt. Kein zweiter Scheduler, kein Cron im Container.
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
"""Die Media-Pipeline verlangt mindestens stuendlich. Ein halbstuendiger
Abstand haelt auch bei einem verpassten Lauf die Zusage."""

UPLOAD_RETENTION = timedelta(hours=24)
"""PENDING, UPLOADING und FAILED - M2-D12."""

_LOCK_KEY = 8_150_214
"""Eigener Schluessel neben dem der Security-Wartung.

Dieselbe Sperre zu benutzen haette beide Ketten aneinandergekoppelt: ein
langer Media-Lauf haette die Security-Wartung mitverzoegert."""


def _lock(session: Session) -> None:
    session.execute(select(func.pg_advisory_xact_lock(_LOCK_KEY)))


def _open_jobs(session: Session, *stati: JobStatus) -> int:
    return int(
        session.execute(
            select(func.count())
            .select_from(Job)
            .where(Job.kind == MEDIA_CLEANUP, Job.status.in_([s.value for s in stati]))
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
    """Angefangene und gescheiterte Uploads nach 24 h verwerfen.

    Bei UPLOADING zaehlt die letzte serverbekannte Aktivitaet, sonst der
    Anlagezeitpunkt - ein Upload, der nie Bytes gesehen hat, hat auch
    keine spaetere Aktivitaet.
    """
    kandidaten = session.execute(
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

    betroffen = 0
    for attachment in kandidaten:
        referenz = attachment.created_at
        if attachment.status == AttachmentStatus.UPLOADING.value and attachment.uploaded_at:
            referenz = attachment.uploaded_at
        elif attachment.status == AttachmentStatus.FAILED.value and attachment.failed_at:
            referenz = attachment.failed_at
        if service.expired(referenz, UPLOAD_RETENTION):
            service.mark_for_deletion(session, attachment)
            betroffen += 1
    return betroffen


def _expire_unbound_ready(session: Session) -> int:
    """Ungebundenes READY nach 60 Minuten verwerfen (M2-D20).

    Solange es keine Bindung gibt, ist jedes READY ungebunden. Sobald der
    Media-Integrationsslice sie einfuehrt, gehoert hier die Bedingung
    'ohne Parent' dazu - und die Serialisierung gegen ein gleichzeitiges
    Bind, damit kein gebundener Blob geloescht wird.
    """
    kandidaten = session.execute(
        select(Attachment)
        .where(Attachment.status == AttachmentStatus.READY.value)
        .with_for_update(skip_locked=True)
    ).scalars()

    betroffen = 0
    for attachment in kandidaten:
        if service.expired(attachment.ready_at, service.BINDING_WINDOW):
            service.mark_for_deletion(session, attachment)
            betroffen += 1
    return betroffen


def _purge_marked(session: Session) -> tuple[int, int]:
    """Providerobjekte entfernen. Ein Fehlschlag macht nichts wieder sichtbar."""
    kandidaten = session.execute(
        select(Attachment)
        .where(
            or_(
                Attachment.status == AttachmentStatus.DELETING.value,
                Attachment.status == AttachmentStatus.DELETE_FAILED.value,
            )
        )
        .with_for_update(skip_locked=True)
    ).scalars()

    entfernt = 0
    gescheitert = 0
    for attachment in kandidaten:
        if service.purge(session, attachment):
            entfernt += 1
        else:
            gescheitert += 1
    return entfernt, gescheitert


def run_media_cleanup(session: Session, payload: dict[str, Any]) -> None:
    del payload

    abgelaufen = _expire_stale_uploads(session)
    verwaist = _expire_unbound_ready(session)
    session.flush()
    entfernt, gescheitert = _purge_marked(session)

    log.info(
        "media cleanup completed",
        extra={
            "expired_uploads": abgelaufen,
            "expired_unbound_ready": verwaist,
            "purged": entfernt,
            "purge_failures": gescheitert,
        },
    )

    schedule_next(session)


def run_attachment_validation(session: Session, payload: dict[str, Any]) -> None:
    kennung = payload.get("attachmentId")
    if not isinstance(kennung, str):
        return
    service.validate(session, UUID(kennung))


def register_handlers(target: JobRegistry | None = None) -> None:
    """Media-Aufgaben beim Worker anmelden."""
    ziel = target if target is not None else registry
    if ziel.get(MEDIA_CLEANUP) is None:
        ziel.register(MEDIA_CLEANUP, run_media_cleanup)
    if ziel.get(service.ATTACHMENT_VALIDATION) is None:
        ziel.register(service.ATTACHMENT_VALIDATION, run_attachment_validation)
