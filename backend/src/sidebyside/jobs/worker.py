"""Background job worker.

Deliberately simple: it maps job kinds to handlers and ensures every job runs
inside its own transaction. If one fails, the others are unaffected.
"""

from __future__ import annotations

import logging
from collections.abc import Callable
from typing import Any

from sqlalchemy.orm import Session

from sidebyside.db.session import unit_of_work
from sidebyside.jobs import queue
from sidebyside.jobs.errors import RetryableJobError
from sidebyside.jobs.models import Job

log = logging.getLogger(__name__)

Handler = Callable[[Session, dict[str, Any]], None]


class JobRegistry:
    def __init__(self) -> None:
        self._handlers: dict[str, Handler] = {}

    def register(self, kind: str, handler: Handler) -> None:
        if kind in self._handlers:
            raise ValueError(f"Handler for '{kind}' is already registered.")
        self._handlers[kind] = handler

    def get(self, kind: str) -> Handler | None:
        return self._handlers.get(kind)


registry = JobRegistry()


def run_once(worker_name: str, limit: int = 10) -> int:
    """Run one round and return the number of processed jobs.

    Claiming happens in its own short transaction. Holding the claim lock
    until processing completes would allow one long-running job to block the
    queue for everybody.
    """
    with unit_of_work() as session:
        jobs = list(queue.claim(session, worker_name, limit=limit))
        job_ids = [(job.id, job.kind, dict(job.payload)) for job in jobs]

    for job_id, kind, payload in job_ids:
        _run_job(job_id, kind, payload)

    return len(job_ids)


def _run_job(job_id: Any, kind: str, payload: dict[str, Any]) -> None:
    handler = registry.get(kind)

    with unit_of_work() as session:
        job = session.get(Job, job_id)
        if job is None:
            return

        if handler is None:
            # An unknown kind is an application error, not a transient
            # failure. Retrying it cannot help.
            job.attempts = job.max_attempts
            queue.fail(job, f"No handler registered for job kind '{kind}'.")
            log.error("unknown job kind", extra={"kind": kind})
            return

        try:
            handler(session, payload)
        except RetryableJobError as exc:
            # Controlled retry errors contain a stable technical code only.
            # The handler transaction remains valid so safe attempt metadata
            # can commit together with the queue backoff state.
            queue.fail(job, exc.code)
            log.warning("job retry scheduled", extra={"kind": kind, "error_code": exc.code})
        except Exception as exc:
            session.rollback()
            # After rollback the session is usable again, but the failure must
            # still be recorded or the job would remain RUNNING until its
            # lease expires.
            failed = session.get(Job, job_id)
            if failed is not None:
                queue.fail(failed, f"{type(exc).__name__}: {exc}")
            log.exception("job failed", extra={"kind": kind})
        else:
            queue.succeed(job)
