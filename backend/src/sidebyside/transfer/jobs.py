"""Background jobs for Transfer Bundle generation, validation and cleanup."""

from __future__ import annotations

import logging
from datetime import timedelta
from typing import Any
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from sidebyside.authorization import AuthorizationContext
from sidebyside.core.clock import now
from sidebyside.core.errors import BadRequestError, ErrorCode
from sidebyside.jobs import queue
from sidebyside.jobs.errors import RetryableJobError
from sidebyside.jobs.models import Job, JobStatus
from sidebyside.jobs.worker import JobRegistry, registry
from sidebyside.media import get_media_store
from sidebyside.relationship.models import Membership, MembershipStatus
from sidebyside.transfer import service
from sidebyside.transfer.models import (
    ExportStatus,
    ImportStatus,
    TransferExport,
    TransferImport,
    TransferScope,
)

log = logging.getLogger(__name__)
CLEANUP_INTERVAL = timedelta(minutes=30)
_LOCK_KEY = 8_150_345


def _lock(session: Session) -> None:
    session.execute(select(func.pg_advisory_xact_lock(_LOCK_KEY)))


def _open_cleanup_jobs(session: Session, *statuses: JobStatus) -> int:
    return int(
        session.execute(
            select(func.count())
            .select_from(Job)
            .where(
                Job.kind == service.CLEANUP_JOB_KIND,
                Job.status.in_([status.value for status in statuses]),
            )
        ).scalar_one()
    )


def ensure_scheduled(session: Session) -> Job | None:
    _lock(session)
    if _open_cleanup_jobs(session, JobStatus.PENDING, JobStatus.RUNNING):
        return None
    return queue.enqueue(session, service.CLEANUP_JOB_KIND)


def schedule_next(session: Session) -> Job | None:
    _lock(session)
    if _open_cleanup_jobs(session, JobStatus.PENDING):
        return None
    return queue.enqueue(session, service.CLEANUP_JOB_KIND, delay=CLEANUP_INTERVAL)


def _active_authorization(
    session: Session, *, space_id: UUID, account_id: UUID
) -> AuthorizationContext | None:
    active = session.execute(
        select(Membership.id).where(
            Membership.space_id == space_id,
            Membership.account_id == account_id,
            Membership.status == MembershipStatus.ACTIVE.value,
        )
    ).scalar_one_or_none()
    if active is None:
        return None
    return AuthorizationContext(account_id=account_id, space_id=space_id)


def _identifier(payload: dict[str, Any], key: str) -> UUID | None:
    raw = payload.get(key)
    if not isinstance(raw, str):
        return None
    try:
        return UUID(raw)
    except ValueError:
        return None


def handle_export(session: Session, payload: dict[str, Any]) -> None:
    identifier = _identifier(payload, "exportId")
    if identifier is None:
        return
    transfer = session.get(TransferExport, identifier)
    if transfer is None or transfer.status in {
        ExportStatus.READY.value,
        ExportStatus.FAILED.value,
        ExportStatus.EXPIRED.value,
    }:
        return
    if transfer.expires_at <= now():
        service.cleanup_expired(session)
        return
    authorization = _active_authorization(
        session, space_id=transfer.space_id, account_id=transfer.created_by
    )
    if authorization is None:
        transfer.status = ExportStatus.FAILED.value
        transfer.error_code = ErrorCode.TRANSFER_EXPORT_FAILED
        return
    transfer.status = ExportStatus.RUNNING.value
    session.flush()

    try:
        # A dedicated repeatable-read transaction gives all domain queries in
        # the archive one deterministic snapshot even though the worker's Job
        # row was claimed in a separate transaction.
        bind = session.get_bind()
        with (
            bind.connect().execution_options(isolation_level="REPEATABLE READ") as connection,
            Session(bind=connection) as snapshot,
            snapshot.begin(),
        ):
            archive = service.build_export_archive(
                snapshot,
                authorization,
                TransferScope(transfer.scope),
            )
        store = get_media_store()
        stored = store.put(service.export_storage_key(transfer), archive, "application/zip")
    except BadRequestError as error:
        transfer.status = ExportStatus.FAILED.value
        transfer.error_code = error.code
        return
    except OSError as error:
        raise RetryableJobError("Transfer export storage is temporarily unavailable.") from error

    transfer.status = ExportStatus.READY.value
    transfer.artifact_size = stored.size
    transfer.ready_at = now()
    transfer.error_code = None
    log.info(
        "transfer export ready",
        extra={"transfer_id": str(transfer.id), "size": stored.size, "scope": transfer.scope},
    )


def handle_validate_import(session: Session, payload: dict[str, Any]) -> None:
    identifier = _identifier(payload, "importId")
    if identifier is None:
        return
    transfer = session.execute(
        select(TransferImport).where(TransferImport.id == identifier).with_for_update()
    ).scalar_one_or_none()
    if transfer is None or transfer.status in {
        ImportStatus.READY_TO_APPLY.value,
        ImportStatus.APPLYING.value,
        ImportStatus.COMPLETED.value,
        ImportStatus.FAILED.value,
        ImportStatus.EXPIRED.value,
    }:
        return
    if transfer.expires_at <= now():
        service.cleanup_expired(session)
        return
    authorization = _active_authorization(
        session, space_id=transfer.space_id, account_id=transfer.created_by
    )
    if authorization is None:
        transfer.status = ImportStatus.FAILED.value
        transfer.error_code = ErrorCode.TRANSFER_IMPORT_FAILED
        return
    transfer.status = ImportStatus.VALIDATING.value
    session.flush()

    try:
        with get_media_store().open(service.import_storage_key(transfer)) as source:
            graph = service.validate_import_bundle(
                session,
                authorization,
                source,
                compressed_size=transfer.artifact_size,
            )
    except BadRequestError as error:
        transfer.status = ImportStatus.FAILED.value
        transfer.error_code = error.code
        return
    except OSError as error:
        raise RetryableJobError("Transfer import storage is temporarily unavailable.") from error

    transfer.scope = graph.scope.value
    transfer.source_space_id = graph.source_space_id
    transfer.source_owner_id = graph.personal_owner_source_id
    transfer.member_mapping = {str(source): str(target) for source, target in graph.mapping.items()}
    transfer.summary = graph.summary
    transfer.validated_at = now()
    transfer.status = ImportStatus.READY_TO_APPLY.value
    transfer.error_code = None
    log.info(
        "transfer import validated",
        extra={
            "transfer_id": str(transfer.id),
            "scope": graph.scope.value,
            "media_count": graph.summary.get("mediaCount", 0),
        },
    )


def handle_apply_import(session: Session, payload: dict[str, Any]) -> None:
    identifier = _identifier(payload, "importId")
    if identifier is None:
        return
    transfer = session.execute(
        select(TransferImport).where(TransferImport.id == identifier).with_for_update()
    ).scalar_one_or_none()
    if transfer is None or transfer.status in {
        ImportStatus.COMPLETED.value,
        ImportStatus.FAILED.value,
        ImportStatus.EXPIRED.value,
    }:
        return
    if transfer.expires_at <= now():
        service.cleanup_expired(session)
        return
    authorization = _active_authorization(
        session, space_id=transfer.space_id, account_id=transfer.created_by
    )
    if authorization is None:
        transfer.status = ImportStatus.FAILED.value
        transfer.error_code = ErrorCode.TRANSFER_IMPORT_FAILED
        return
    transfer.status = ImportStatus.APPLYING.value
    session.flush()

    try:
        with get_media_store().open(service.import_storage_key(transfer)) as source:
            service.apply_import_bundle(session, authorization, transfer, source)
    except BadRequestError as error:
        transfer.status = ImportStatus.FAILED.value
        transfer.error_code = error.code
        return
    except OSError as error:
        raise RetryableJobError("Transfer import storage is temporarily unavailable.") from error

    transfer.status = ImportStatus.COMPLETED.value
    transfer.completed_at = now()
    transfer.error_code = None
    # The source archive is no longer needed after a successful atomic apply.
    # Deleting it immediately minimizes retained private data; delete is
    # idempotent and the completed descriptor remains readable.
    try:
        get_media_store().delete(service.import_storage_key(transfer))
    except OSError:
        log.warning("completed transfer import archive cleanup failed")
    log.info("transfer import applied", extra={"transfer_id": str(transfer.id)})


def handle_cleanup(session: Session, payload: dict[str, Any]) -> None:
    del payload
    affected = service.cleanup_expired(session)
    log.info("transfer cleanup completed", extra={"expired_transfers": affected})
    schedule_next(session)


def register_handlers(target: JobRegistry | None = None) -> None:
    destination = target if target is not None else registry
    handlers = {
        service.EXPORT_JOB_KIND: handle_export,
        service.IMPORT_VALIDATE_JOB_KIND: handle_validate_import,
        service.IMPORT_APPLY_JOB_KIND: handle_apply_import,
        service.CLEANUP_JOB_KIND: handle_cleanup,
    }
    for kind, handler in handlers.items():
        if destination.get(kind) is None:
            destination.register(kind, handler)
