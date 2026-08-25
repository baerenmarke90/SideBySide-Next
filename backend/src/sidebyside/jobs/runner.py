"""Worker-Prozess.

Bewusst eine Schleife und kein Framework: die Warteschlange liegt in der
Datenbank, und mehr als regelmaessiges Nachsehen braucht es dafuer nicht.

Mehrere Instanzen duerfen parallel laufen - `FOR UPDATE SKIP LOCKED` sorgt
dafuer, dass sie einander nicht in die Quere kommen.
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
from sidebyside.jobs import maintenance
from sidebyside.jobs.worker import run_once

log = logging.getLogger(__name__)

IDLE_SLEEP_SECONDS = 2.0

MAINTENANCE_CHECK_SECONDS = 300.0
"""Wie oft nachgesehen wird, ob die Wartung ueberhaupt noch ansteht.

Die Kette plant sich selbst fort; dieser Blick ist die Rueckfallebene fuer
den Fall, dass eine Aufgabe endgueltig aufgibt. Ohne ihn bliebe der
Cleanup danach still aus - und genau das soll er nicht.
"""

_shutdown = False


def _request_shutdown(signum: int, frame: FrameType | None) -> None:
    """Auf SIGTERM aufhoeren, aber die laufende Runde zu Ende bringen.

    Ein Abbruch mitten in einer Aufgabe hinterliesse sie als RUNNING mit
    laufender Sperre - sie waere erst nach Ablauf der Sperre wieder frei.
    """
    global _shutdown
    _shutdown = True
    log.info("shutdown requested", extra={"signal": signum})


def _ensure_maintenance() -> None:
    """Fehlt die Wartung, wird sie eingeplant. Fehler beenden den Worker nicht."""
    try:
        with unit_of_work() as session:
            maintenance.ensure_scheduled(session)
            media_cleanup.ensure_scheduled(session)
    except Exception:
        log.exception("could not schedule maintenance")


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
    _ensure_maintenance()
    zuletzt_geprueft = time.monotonic()

    while not _shutdown:
        if time.monotonic() - zuletzt_geprueft >= MAINTENANCE_CHECK_SECONDS:
            _ensure_maintenance()
            zuletzt_geprueft = time.monotonic()

        try:
            erledigt = run_once(name)
        except Exception:
            # Ein Fehler beim Abholen darf den Prozess nicht beenden -
            # sonst kippt der Worker bei jeder kurzen Stoerung der
            # Datenbankverbindung um.
            log.exception("worker round failed")
            erledigt = 0

        if erledigt == 0:
            time.sleep(IDLE_SLEEP_SECONDS)

    log.info("worker stopped", extra={"worker": name})


if __name__ == "__main__":
    main()
