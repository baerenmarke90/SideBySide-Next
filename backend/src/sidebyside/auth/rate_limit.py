"""Begrenzung wiederholter Versuche.

In der Datenbank und nicht im Prozessspeicher: die Cloud-API ist
zustandslos und laeuft mehrfach. Ein Zaehler im Speicher waere pro Instanz
einer, und wer genug Anfragen schickt, verteilt sich einfach darauf.

Der Schluessel wird gehasht abgelegt. Er ist oft eine E-Mail-Adresse, und
eine Tabelle voller Adressen, aus der sich ablesen laesst, wer wann einen
Anmeldeversuch hatte, ist mehr Wissen, als diese Funktion braucht.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import TYPE_CHECKING, Any, cast

from sqlalchemy import delete, func, select

if TYPE_CHECKING:
    from sqlalchemy import CursorResult
from sqlalchemy.orm import Session

from sidebyside.auth.tokens import hash_token
from sidebyside.core.clock import now
from sidebyside.core.errors import ErrorCode, RateLimitedError
from sidebyside.identity.models import RateLimitEvent


@dataclass(frozen=True)
class Limit:
    attempts: int
    window: timedelta


# Anmeldung: streng genug, um Durchprobieren unattraktiv zu machen, weit
# genug, um jemanden mit Tippfehlern nicht auszusperren.
SIGN_IN = Limit(attempts=10, window=timedelta(minutes=15))
MAGIC_LINK = Limit(attempts=5, window=timedelta(minutes=15))
INVITATION_ACCEPT = Limit(attempts=10, window=timedelta(minutes=15))


def record_attempt(session: Session, action: str, key: str) -> None:
    """Einen Versuch vermerken. Zaehlt unabhaengig vom Ausgang."""
    session.add(RateLimitEvent(action=action, key_hash=hash_token(key.lower()), occurred_at=now()))
    session.flush()


def check(session: Session, action: str, key: str, limit: Limit) -> None:
    """Wirft, wenn die Grenze erreicht ist.

    Wird VOR dem eigentlichen Versuch aufgerufen, damit ein Angreifer nicht
    erst die teure Passwortpruefung ausloest.
    """
    seit = now() - limit.window
    versuche = session.execute(
        select(func.count())
        .select_from(RateLimitEvent)
        .where(
            RateLimitEvent.action == action,
            RateLimitEvent.key_hash == hash_token(key.lower()),
            RateLimitEvent.occurred_at >= seit,
        )
    ).scalar_one()

    if versuche >= limit.attempts:
        raise RateLimitedError("Too many attempts. Please try again later.", ErrorCode.RATE_LIMITED)


def clear(session: Session, action: str, key: str) -> None:
    """Nach erfolgreichem Versuch aufraeumen.

    Sonst zaehlten die Fehlversuche vor einer geglueckten Anmeldung weiter
    und sperrten den rechtmaessigen Nutzer aus.
    """
    session.execute(
        delete(RateLimitEvent).where(
            RateLimitEvent.action == action,
            RateLimitEvent.key_hash == hash_token(key.lower()),
        )
    )


def prune(session: Session, older_than: datetime | None = None) -> int:
    """Alte Eintraege entfernen. Fuer einen Hintergrundjob gedacht."""
    grenze = older_than or (now() - timedelta(days=1))
    # session.execute ist allgemein typisiert; ein DELETE liefert ein
    # CursorResult mit rowcount.
    ergebnis = cast(
        "CursorResult[Any]",
        session.execute(delete(RateLimitEvent).where(RateLimitEvent.occurred_at < grenze)),
    )
    return int(ergebnis.rowcount or 0)
