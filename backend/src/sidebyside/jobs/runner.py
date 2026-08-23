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

from sidebyside.jobs.worker import run_once

log = logging.getLogger(__name__)

IDLE_SLEEP_SECONDS = 2.0

_shutdown = False


def _request_shutdown(signum: int, frame: FrameType | None) -> None:
    """Auf SIGTERM aufhoeren, aber die laufende Runde zu Ende bringen.

    Ein Abbruch mitten in einer Aufgabe hinterliesse sie als RUNNING mit
    laufender Sperre - sie waere erst nach Ablauf der Sperre wieder frei.
    """
    global _shutdown
    _shutdown = True
    log.info("shutdown requested", extra={"signal": signum})


def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )

    signal.signal(signal.SIGTERM, _request_shutdown)
    signal.signal(signal.SIGINT, _request_shutdown)

    name = f"{socket.gethostname()}-{os.getpid()}"
    log.info("worker started", extra={"worker": name})

    while not _shutdown:
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
