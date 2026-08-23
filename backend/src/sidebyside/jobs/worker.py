"""Der Worker.

Bewusst schlicht: er kennt eine Zuordnung von Aufgabenart zu Funktion und
sorgt dafür, dass jede Aufgabe in ihrer eigenen Transaktion läuft. Fällt
eine aus, betrifft das die anderen nicht.
"""

from __future__ import annotations

import logging
from collections.abc import Callable
from typing import Any

from sqlalchemy.orm import Session

from sidebyside.db.session import unit_of_work
from sidebyside.jobs import queue
from sidebyside.jobs.models import Job

log = logging.getLogger(__name__)

Handler = Callable[[Session, dict[str, Any]], None]


class JobRegistry:
    def __init__(self) -> None:
        self._handlers: dict[str, Handler] = {}

    def register(self, kind: str, handler: Handler) -> None:
        if kind in self._handlers:
            raise ValueError(f"Handler für '{kind}' ist bereits registriert.")
        self._handlers[kind] = handler

    def get(self, kind: str) -> Handler | None:
        return self._handlers.get(kind)


registry = JobRegistry()


def run_once(worker_name: str, limit: int = 10) -> int:
    """Eine Runde. Gibt zurück, wie viele Aufgaben bearbeitet wurden.

    Das Übernehmen geschieht in einer eigenen, kurzen Transaktion. Würde die
    Sperre bis zum Ende der Verarbeitung gehalten, blockierte eine lange
    Aufgabe die Warteschlange für alle.
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
            # Eine unbekannte Art ist ein Fehler in der Anwendung, kein
            # vorübergehender Ausfall - es hilft nicht, sie zu wiederholen.
            job.attempts = job.max_attempts
            queue.fail(job, f"Keine Verarbeitung für Aufgabenart '{kind}'.")
            log.error("unknown job kind", extra={"kind": kind})
            return

        try:
            handler(session, payload)
        except Exception as exc:
            session.rollback()
            # Nach dem Rollback ist die Sitzung wieder brauchbar; der
            # Fehlschlag selbst muss aber verbucht werden, sonst bliebe die
            # Aufgabe als RUNNING mit ablaufender Sperre liegen.
            failed = session.get(Job, job_id)
            if failed is not None:
                queue.fail(failed, f"{type(exc).__name__}: {exc}")
            log.exception("job failed", extra={"kind": kind})
        else:
            queue.succeed(job)
