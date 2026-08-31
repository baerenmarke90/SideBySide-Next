"""Worker process.

Deliberately a loop rather than a framework: the queue lives in the database
and needs nothing more than periodic polling.

Multiple instances may run concurrently; `FOR UPDATE SKIP LOCKED` prevents
them from interfering with one another.
"""

from __future__ import annotations

import logging
import os
import signal
import socket
import time
from types import FrameType

from sidebyside.attachments import cleanup as media_cleanup
from sidebyside.db.session import unit_of_work
from sidebyside.demo import reset as demo_reset
from sidebyside.engagement import push as push_delivery
from sidebyside.engagement import service as engagement_service
from sidebyside.jobs import maintenance
from sidebyside.jobs.worker import run_once
from sidebyside.reminders import runtime as reminder_runtime
from sidebyside.transfer import jobs as transfer_jobs

log = logging.getLogger(__name__)

IDLE_SLEEP_SECONDS = 2.0

MAINTENANCE_CHECK_SECONDS = 300.0
"""How often to check that maintenance is still scheduled.

The chain schedules itself; this check is the recovery layer for a job that
gives up permanently. Without it, cleanup would silently stop afterwards.
"""

_shutdown = False


def _request_shutdown(signum: int, frame: FrameType | None) -> None:
    """Stop on SIGTERM after allowing the current round to finish.

    Interrupting a job mid-run would leave it RUNNING with an active lease;
    it would not become available again until its lease expired.
    """
    global _shutdown
    _shutdown = True
    log.info("shutdown requested", extra={"signal": signum})


def _ensure_maintenance() -> None:
    """Schedule missing maintenance without terminating the worker on failure."""
    try:
        with unit_of_work() as session:
            maintenance.ensure_scheduled(session)
            media_cleanup.ensure_scheduled(session)
            reminder_runtime.ensure_scheduled(session)
            demo_reset.ensure_scheduled(session)
            transfer_jobs.ensure_scheduled(session)
    except Exception:
        log.exception("could not schedule maintenance")


def _run_engagement_projection() -> int:
    """Project one committed Outbox batch through the existing DB worker."""
    with unit_of_work() as session:
        return engagement_service.project_pending(session)


def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )

    signal.signal(signal.SIGTERM, _request_shutdown)
    signal.signal(signal.SIGINT, _request_shutdown)

    name = f"{socket.gethostname()}-{os.getpid()}"
    log.info("worker started", extra={"worker": name})

    maintenance.register_handlers()
    media_cleanup.register_handlers()
    push_delivery.register_handlers()
    reminder_runtime.register_handlers()
    demo_reset.register_handlers()
    transfer_jobs.register_handlers()
    _ensure_maintenance()
    last_checked = time.monotonic()

    while not _shutdown:
        if time.monotonic() - last_checked >= MAINTENANCE_CHECK_SECONDS:
            _ensure_maintenance()
            last_checked = time.monotonic()

        try:
            projected = _run_engagement_projection()
            completed = projected + run_once(name)
        except Exception:
            # A failure while polling must not terminate the process; otherwise
            # any brief database connection disruption would take down the
            # worker.
            log.exception("worker round failed")
            completed = 0

        if completed == 0:
            time.sleep(IDLE_SLEEP_SECONDS)

    log.info("worker stopped", extra={"worker": name})


if __name__ == "__main__":
    main()
