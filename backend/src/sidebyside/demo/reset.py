"""Recurring reset chain for the isolated public demo deployment."""

from __future__ import annotations

import logging
from datetime import date, timedelta
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from sidebyside.config import get_settings
from sidebyside.demo.service import reset_demo_space
from sidebyside.jobs import queue
from sidebyside.jobs.models import Job, JobStatus
from sidebyside.jobs.worker import JobRegistry, registry

log = logging.getLogger(__name__)

DEMO_RESET_JOB = "demo-space-reset"
_LOCK_KEY = 8_150_215


def _enabled() -> bool:
    settings = get_settings()
    return settings.demo_mode and settings.demo_mode_reset_timer


def _open_jobs(session: Session, *statuses: JobStatus) -> int:
    return int(
        session.execute(
            select(func.count())
            .select_from(Job)
            .where(
                Job.kind == DEMO_RESET_JOB,
                Job.status.in_([status.value for status in statuses]),
            )
        ).scalar_one()
    )


def _lock(session: Session) -> None:
    session.execute(select(func.pg_advisory_xact_lock(_LOCK_KEY)))


def ensure_scheduled(session: Session, *, delay: timedelta | None = None) -> Job | None:
    """Ensure one reset chain exists when the deployment opted into the timer."""
    if not _enabled():
        return None
    _lock(session)
    if _open_jobs(session, JobStatus.PENDING, JobStatus.RUNNING):
        return None
    settings = get_settings()
    return queue.enqueue(
        session,
        DEMO_RESET_JOB,
        delay=delay or settings.demo_mode_reset_interval,
    )


def schedule_next(session: Session) -> Job | None:
    """Schedule the next configured interval after a successful reset."""
    if not _enabled():
        return None
    _lock(session)
    if _open_jobs(session, JobStatus.PENDING):
        return None
    return queue.enqueue(
        session,
        DEMO_RESET_JOB,
        delay=get_settings().demo_mode_reset_interval,
    )


def run_demo_reset(session: Session, payload: dict[str, Any]) -> None:
    """Restore canonical demo content and continue the bounded reset chain."""
    del payload
    settings = get_settings()
    if not settings.demo_mode or not settings.demo_mode_reset_timer:
        return

    result = reset_demo_space(
        session,
        environment=settings.environment,
        reference_date=date.today(),
    )
    log.info(
        "canonical demo Space reset",
        extra={
            "space_id": str(result.space_id),
            "reference_date": result.reference_date.isoformat(),
        },
    )
    schedule_next(session)


def register_handlers(target: JobRegistry | None = None) -> None:
    destination = target if target is not None else registry
    if destination.get(DEMO_RESET_JOB) is None:
        destination.register(DEMO_RESET_JOB, run_demo_reset)
