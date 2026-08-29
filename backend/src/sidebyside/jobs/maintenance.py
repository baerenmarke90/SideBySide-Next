"""Recurring maintenance for security state.

Retention periods that exist only as functions in code are not retention
periods in practice. `sessions.prune_replay_history()` and
`rate_limit.prune()` are tested and documented, but previously nobody ran
them.

This module gives them a scheduler: an ordinary job in the existing queue
that schedules its own successor after successful work. No second scheduler
and no container cron are needed because the queue already lives in
PostgreSQL and survives restarts.
"""

from __future__ import annotations

import logging
from datetime import timedelta
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from sidebyside.auth import oidc, passkeys, rate_limit, sessions
from sidebyside.jobs import queue
from sidebyside.jobs.models import Job, JobStatus
from sidebyside.jobs.worker import JobRegistry, registry

log = logging.getLogger(__name__)

SECURITY_RETENTION = "security_retention"

RETENTION_INTERVAL = timedelta(hours=6)
"""Interval between runs.

This is substantially shorter than the shortest retention period, one day
for rate-limit events. A missed run therefore shifts nothing material, while
running more frequently would add load without adding value.
"""

_LOCK_KEY = 8_150_213
"""Advisory-lock key used while scheduling.

Without it, two workers starting concurrently could both inspect the queue,
both find nothing, and both enqueue a job. The lock lasts until the end of
the transaction and needs no dedicated table.

A duplicate run would still be harmless because both prune functions are
idempotent. The lock merely keeps the queue tidy.
"""


def _open_jobs(session: Session, *statuses: JobStatus) -> int:
    return int(
        session.execute(
            select(func.count())
            .select_from(Job)
            .where(
                Job.kind == SECURITY_RETENTION,
                Job.status.in_([status.value for status in statuses]),
            )
        ).scalar_one()
    )


def _lock(session: Session) -> None:
    session.execute(select(func.pg_advisory_xact_lock(_LOCK_KEY)))


def ensure_scheduled(session: Session, *, delay: timedelta | None = None) -> Job | None:
    """Ensure that at least one run is scheduled.

    Called when a worker starts and periodically afterwards. This is the
    self-healing path: if a job gives up permanently, no chain remains
    attached to it, but this function still creates the next one.

    A currently running job counts as well. It schedules its own successor;
    scheduling another here would double the cadence.
    """
    _lock(session)
    if _open_jobs(session, JobStatus.PENDING, JobStatus.RUNNING):
        return None
    return queue.enqueue(session, SECURITY_RETENTION, delay=delay)


def schedule_next(session: Session, *, delay: timedelta | None = None) -> Job | None:
    """Schedule the next run from within the currently running one.

    Unlike `ensure_scheduled`, this deliberately does not count the current
    RUNNING job; otherwise the chain could never schedule its successor.
    """
    _lock(session)
    if _open_jobs(session, JobStatus.PENDING):
        return None
    return queue.enqueue(session, SECURITY_RETENTION, delay=delay or RETENTION_INTERVAL)


def run_security_retention(session: Session, payload: dict[str, Any]) -> None:
    """Prune expired security state and schedule the next run.

    Retention periods remain defined where the data originates:
    `sessions.REPLAY_HISTORY_RETENTION`, the default in `rate_limit.prune()`,
    and the lifetime of an initiated OIDC authentication request. This job
    makes no retention decisions; it merely makes sure those decisions are
    actually applied.

    Active token families retain their complete history because that history
    *is* replay detection, and `prune_replay_history` does not touch it.
    """
    del payload

    replay_history = sessions.prune_replay_history(session)
    rate_limits = rate_limit.prune(session)
    oidc_requests = oidc.prune_auth_requests(session)
    ceremonies = passkeys.prune_challenges(session)

    log.info(
        "security retention completed",
        extra={
            "replay_history_removed": replay_history,
            "rate_limit_events_removed": rate_limits,
            "oidc_auth_requests_removed": oidc_requests,
            "webauthn_challenges_removed": ceremonies,
        },
    )

    schedule_next(session)


def register_handlers(target: JobRegistry | None = None) -> None:
    """Register maintenance with the worker.

    Deliberately an explicit call rather than an import side effect: whoever
    starts the worker should be able to see what it runs.
    """
    destination = target if target is not None else registry
    if destination.get(SECURITY_RETENTION) is None:
        destination.register(SECURITY_RETENTION, run_security_retention)
