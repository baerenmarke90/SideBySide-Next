"""Begrenzung wiederholter Versuche.

In der Datenbank und nicht im Prozessspeicher: die Cloud-API ist
zustandslos und laeuft mehrfach. Ein Zaehler im Speicher waere pro Instanz
einer, und wer genug Anfragen schickt, verteilt sich einfach darauf.

Der Schluessel wird gehasht abgelegt. Er ist oft eine E-Mail-Adresse, und
eine Tabelle voller Adressen, aus der sich ablesen laesst, wer wann einen
Anmeldeversuch hatte, ist mehr Wissen, als diese Funktion braucht.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from datetime import datetime, timedelta
from functools import partial
from typing import TYPE_CHECKING, Any, cast

from sqlalchemy import delete, func, select
from sqlalchemy.engine import Engine

if TYPE_CHECKING:
    from sqlalchemy import CursorResult
from sqlalchemy.orm import Session

from sidebyside.auth.tokens import hash_token
from sidebyside.core.clock import now
from sidebyside.core.errors import ErrorCode, RateLimitedError
from sidebyside.db.session import schedule_after_rollback
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

# Erneuern: der einzige Fall, in dem nicht Fehlversuche begrenzt werden,
# sondern Erfolge. Jede Rotation schreibt eine Zeile Replay-Historie; ein
# Client mit gueltigem Token koennte davon in einer engen Schleife beliebig
# viele erzeugen.
#
# Ein Access Token lebt 15 Minuten, ein regulaerer Client erneuert also
# etwa einmal pro Fenster. Das Budget liegt bewusst um ein Vielfaches
# darueber: Neustarts, Netzwechsel und Wiederholungen sollen niemanden
# aussperren, eine Schleife aber schon.
REFRESH = Limit(attempts=20, window=timedelta(minutes=15))

_PERSISTED_ATTEMPTS_KEY = "sidebyside.rate_limit.persisted"


def _record_hashed_attempt(session: Session, *, action: str, key_hash: str) -> None:
    session.add(RateLimitEvent(action=action, key_hash=key_hash, occurred_at=now()))
    session.flush()


def _advisory_lock_id(action: str, key_hash: str) -> int:
    """Stabiler PostgreSQL-Lock-Key aus Action und bereits gehashtem Key.

    PostgreSQL-Advisory-Locks akzeptieren ein signed 64-bit Integer. Die
    Ableitung verwendet bewusst nur den ohnehin bereits gehashten
    Rate-Limit-Schluessel; der Klartext landet weder in Tabelle noch Lock.
    """
    digest = hashlib.sha256(f"{action}\0{key_hash}".encode("utf-8")).digest()
    return int.from_bytes(digest[:8], byteorder="big", signed=True)


def _reserve_hashed_attempt(
    session: Session,
    *,
    action: str,
    key_hash: str,
    limit: Limit,
) -> None:
    """Pruefung und Slot-Verbrauch unter einem DB-weiten per-Key Lock."""
    session.execute(select(func.pg_advisory_xact_lock(_advisory_lock_id(action, key_hash))))

    seit = now() - limit.window
    versuche = session.execute(
        select(func.count())
        .select_from(RateLimitEvent)
        .where(
            RateLimitEvent.action == action,
            RateLimitEvent.key_hash == key_hash,
            RateLimitEvent.occurred_at >= seit,
        )
    ).scalar_one()

    if versuche >= limit.attempts:
        raise RateLimitedError("Too many attempts. Please try again later.", ErrorCode.RATE_LIMITED)

    _record_hashed_attempt(session, action=action, key_hash=key_hash)


def _persisted_attempts(session: Session) -> set[tuple[str, str]]:
    return cast(
        "set[tuple[str, str]]",
        session.info.setdefault(_PERSISTED_ATTEMPTS_KEY, set()),
    )


def check(session: Session, action: str, key: str, limit: Limit) -> None:
    """Atomar einen Rate-Limit-Slot pruefen und verbrauchen.

    Produktive Request-Sessions sind an die Engine gebunden. Dort lebt die
    Reservierung in einer kurzen eigenen Security-Transaktion: ihr Commit
    geschieht, bevor die fachliche Anfrage weiterlaeuft. Scheitert die
    Anfrage spaeter und wird zurueckgerollt, bleibt der Versuch dadurch
    gezaehlt. Gleichzeitig serialisiert ein PostgreSQL-Advisory-Lock alle
    API-Instanzen fuer genau `(action, key)`.

    Tests, die eine Session absichtlich an eine bereits offene Connection
    binden, bleiben dagegen in ihrer Testtransaktion; so wird keine
    Testisolation durch einen separaten Commit durchbrochen.

    Historische Aufrufer folgen unmittelbar mit `record_attempt()`. Diese
    Methode markiert die bereits persistierte Reservierung, damit jener
    Aufruf keinen zweiten Eintrag erzeugt.
    """
    key_hash = hash_token(key.lower())
    bind = session.get_bind()

    if isinstance(bind, Engine):
        # Spaeter Import: Tests ersetzen get_sessionmaker fuer den echten
        # produktiven UoW-Lifecycle. Der Ersatz muss auch hier greifen.
        from sidebyside.db import session as db_session

        security_session = db_session.get_sessionmaker()()
        try:
            _reserve_hashed_attempt(
                security_session,
                action=action,
                key_hash=key_hash,
                limit=limit,
            )
            security_session.commit()
        except Exception:
            security_session.rollback()
            raise
        finally:
            security_session.close()
    else:
        _reserve_hashed_attempt(session, action=action, key_hash=key_hash, limit=limit)

    _persisted_attempts(session).add((action, key_hash))


def record_attempt(session: Session, action: str, key: str) -> None:
    """Einen Versuch vermerken, sofern `check` ihn nicht bereits reserviert hat."""
    key_hash = hash_token(key.lower())
    if (action, key_hash) in _persisted_attempts(session):
        return
    _record_hashed_attempt(session, action=action, key_hash=key_hash)


def preserve_attempt_after_rollback(session: Session, action: str, key: str) -> None:
    """Den Versuch auch bei einer abgelehnten Anfrage dauerhaft erhalten.

    `check()` persistiert produktive Reservierungen bereits in einer
    separaten Security-Transaktion. Fuer Alt-/Direktaufrufe ohne vorherige
    Reservierung bleibt der bisherige After-Rollback-Weg erhalten.
    """
    key_hash = hash_token(key.lower())
    if (action, key_hash) in _persisted_attempts(session):
        return

    schedule_after_rollback(
        session,
        partial(
            _record_hashed_attempt,
            action=action,
            key_hash=key_hash,
        ),
    )


def clear(session: Session, action: str, key: str) -> None:
    """Nach erfolgreichem Versuch aufraeumen.

    Sonst zaehlten die Fehlversuche vor einer geglueckten Anmeldung weiter
    und sperrten den rechtmaessigen Nutzer aus.
    """
    key_hash = hash_token(key.lower())
    session.execute(
        delete(RateLimitEvent).where(
            RateLimitEvent.action == action,
            RateLimitEvent.key_hash == key_hash,
        )
    )
    _persisted_attempts(session).discard((action, key_hash))


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
