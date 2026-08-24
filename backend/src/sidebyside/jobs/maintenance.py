"""Wiederkehrende Wartung fuer Security-State.

Aufbewahrungsfristen, die nur als Funktion im Code stehen, sind keine
Fristen. `sessions.prune_replay_history()` und `rate_limit.prune()` sind
getestet und dokumentiert - ausgefuehrt hat sie bisher niemand.

Hier bekommen sie einen Auftraggeber: eine gewoehnliche Aufgabe in der
vorhandenen Warteschlange, die sich nach getaner Arbeit selbst neu
einstellt. Kein zweiter Scheduler, kein Cron im Container - die
Warteschlange liegt ohnehin in PostgreSQL und ueberlebt einen Neustart.
"""

from __future__ import annotations

import logging
from datetime import timedelta
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from sidebyside.auth import rate_limit, sessions
from sidebyside.jobs import queue
from sidebyside.jobs.models import Job, JobStatus
from sidebyside.jobs.worker import JobRegistry, registry

log = logging.getLogger(__name__)

SECURITY_RETENTION = "security_retention"

RETENTION_INTERVAL = timedelta(hours=6)
"""Abstand zwischen zwei Laeufen.

Deutlich kuerzer als die kuerzeste Aufbewahrungsfrist (ein Tag fuer
Rate-Limit-Ereignisse). Ein verpasster Lauf verschiebt damit nichts
Wesentliches, und haeufiger waere nur mehr Last ohne mehr Wirkung.
"""

_LOCK_KEY = 8_150_213
"""Schluessel der Advisory Lock, unter der eingeplant wird.

Zwei gleichzeitig startende Worker wuerden sonst beide nachsehen, beide
nichts finden und beide einstellen. Die Sperre gilt bis zum Ende der
Transaktion und braucht keine eigene Tabelle.

Ein doppelter Lauf waere ohnehin harmlos - beide Prune-Funktionen sind
idempotent. Die Sperre haelt nur die Warteschlange sauber.
"""


def _open_jobs(session: Session, *stati: JobStatus) -> int:
    return int(
        session.execute(
            select(func.count())
            .select_from(Job)
            .where(
                Job.kind == SECURITY_RETENTION,
                Job.status.in_([status.value for status in stati]),
            )
        ).scalar_one()
    )


def _lock(session: Session) -> None:
    session.execute(select(func.pg_advisory_xact_lock(_LOCK_KEY)))


def ensure_scheduled(session: Session, *, delay: timedelta | None = None) -> Job | None:
    """Dafuer sorgen, dass ueberhaupt ein Lauf ansteht.

    Wird beim Start eines Workers und danach regelmaessig aufgerufen. Das
    ist die Selbstheilung: gibt eine Aufgabe endgueltig auf, haengt keine
    Kette mehr an ihr - hier entsteht die naechste trotzdem.

    Eine bereits laufende Aufgabe zaehlt mit. Sie stellt ihre Nachfolgerin
    selbst ein; zusaetzlich einzuplanen hiesse, den Takt zu verdoppeln.
    """
    _lock(session)
    if _open_jobs(session, JobStatus.PENDING, JobStatus.RUNNING):
        return None
    return queue.enqueue(session, SECURITY_RETENTION, delay=delay)


def schedule_next(session: Session, *, delay: timedelta | None = None) -> Job | None:
    """Den naechsten Lauf einstellen, aus einem laufenden heraus.

    Anders als `ensure_scheduled` zaehlt die eigene, gerade laufende
    Aufgabe hier nicht mit - sonst plante sich die Kette nie fort.
    """
    _lock(session)
    if _open_jobs(session, JobStatus.PENDING):
        return None
    return queue.enqueue(session, SECURITY_RETENTION, delay=delay or RETENTION_INTERVAL)


def run_security_retention(session: Session, payload: dict[str, Any]) -> None:
    """Abgelaufenen Security-State raeumen und den naechsten Lauf einplanen.

    Beide Fristen bleiben dort definiert, wo die Daten entstehen:
    `sessions.REPLAY_HISTORY_RETENTION` und die Voreinstellung in
    `rate_limit.prune()`. Dieser Job entscheidet nichts ueber die
    Aufbewahrung - er sorgt nur dafuer, dass sie tatsaechlich eintritt.

    Laufende Token-Familien behalten ihre vollstaendige Historie: sie
    *ist* die Replay-Erkennung, und `prune_replay_history` fasst sie nicht
    an.
    """
    del payload

    historie = sessions.prune_replay_history(session)
    limits = rate_limit.prune(session)

    log.info(
        "security retention completed",
        extra={"replay_history_removed": historie, "rate_limit_events_removed": limits},
    )

    schedule_next(session)


def register_handlers(target: JobRegistry | None = None) -> None:
    """Die Wartung beim Worker anmelden.

    Absichtlich ein Aufruf und kein Import-Nebeneffekt: wer den Worker
    startet, soll sehen, was er ausfuehrt.
    """
    ziel = target if target is not None else registry
    if ziel.get(SECURITY_RETENTION) is None:
        ziel.register(SECURITY_RETENTION, run_security_retention)
