"""Aufgaben einstellen und abholen."""

from __future__ import annotations

from collections.abc import Sequence
from datetime import timedelta
from typing import Any

from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from sidebyside.core.clock import now
from sidebyside.jobs.models import Job, JobStatus

DEFAULT_LEASE = timedelta(minutes=5)


def enqueue(
    session: Session,
    kind: str,
    payload: dict[str, Any] | None = None,
    *,
    delay: timedelta | None = None,
    max_attempts: int = 5,
) -> Job:
    """Eine Aufgabe einstellen.

    Ohne Commit - eine Aufgabe, die aus einer fachlichen Änderung folgt,
    gehört in deren Transaktion.
    """
    job = Job(
        kind=kind,
        payload=payload or {},
        max_attempts=max_attempts,
        run_after=now() + delay if delay else now(),
    )
    session.add(job)
    return job


def claim(
    session: Session, worker: str, limit: int = 10, lease: timedelta = DEFAULT_LEASE
) -> Sequence[Job]:
    """Fällige Aufgaben übernehmen.

    `FOR UPDATE SKIP LOCKED` sorgt dafür, dass nebenläufige Worker
    disjunkte Mengen greifen, ohne einander zu blockieren.

    Übernommen wird auch, was als RUNNING gilt, dessen Sperre aber
    abgelaufen ist: das ist eine Aufgabe, deren Worker gestorben ist. Ohne
    diesen Zweig bliebe sie für immer liegen.
    """
    jetzt = now()
    stmt = (
        select(Job)
        .where(
            Job.run_after <= jetzt,
            or_(
                Job.status == JobStatus.PENDING.value,
                (Job.status == JobStatus.RUNNING.value) & (Job.locked_until < jetzt),
            ),
        )
        .order_by(Job.run_after)
        .limit(limit)
        .with_for_update(skip_locked=True)
    )
    jobs = session.execute(stmt).scalars().all()

    for job in jobs:
        job.status = JobStatus.RUNNING.value
        job.locked_by = worker
        job.locked_until = jetzt + lease
        job.attempts += 1

    return jobs


def succeed(job: Job) -> None:
    job.status = JobStatus.SUCCEEDED.value
    job.finished_at = now()
    job.locked_until = None
    job.locked_by = None
    job.last_error = None


def fail(job: Job, error: str, *, backoff: timedelta | None = None) -> None:
    """Fehlschlag verbuchen.

    Solange Versuche übrig sind, geht die Aufgabe zurück in die
    Warteschlange - mit Verzögerung, damit ein dauerhaft kaputter Empfänger
    nicht im Sekundentakt erneut angefragt wird. Sind die Versuche
    aufgebraucht, bleibt sie als FAILED liegen und wird nicht still
    verworfen.
    """
    job.last_error = error[:2000]
    job.locked_until = None
    job.locked_by = None

    if job.attempts >= job.max_attempts:
        job.status = JobStatus.FAILED.value
        job.finished_at = now()
        return

    job.status = JobStatus.PENDING.value
    job.run_after = now() + (backoff or _backoff_for(job.attempts))


def _backoff_for(attempts: int) -> timedelta:
    """Exponentiell, gedeckelt bei einer Stunde."""
    sekunden = min(2 ** min(attempts, 12) * 5, 3600)
    return timedelta(seconds=sekunden)
