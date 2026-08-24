"""Datenbankverbindung und Transaktionsgrenze.

Eine Anfrage ist eine Transaktion. Sie wird am Ende der Anfrage übergeben
oder vollständig zurückgerollt - nicht stückweise während der Verarbeitung.

Das ist die Voraussetzung für die Transactional Outbox: fachliche Änderung
und Ereignis müssen gemeinsam wirksam werden oder gemeinsam ausbleiben.
"""

from __future__ import annotations

from collections.abc import Callable, Iterator
from contextlib import contextmanager
from functools import lru_cache
from typing import cast

from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import Session, sessionmaker

from sidebyside.config import get_settings


AfterRollbackAction = Callable[[Session], None]
_AFTER_ROLLBACK_KEY = "sidebyside.after_rollback"


@lru_cache
def get_engine() -> Engine:
    settings = get_settings()
    return create_engine(
        settings.database_url,
        echo=settings.database_echo,
        pool_pre_ping=True,
        future=True,
    )


@lru_cache
def get_sessionmaker() -> sessionmaker[Session]:
    return sessionmaker(bind=get_engine(), autoflush=False, expire_on_commit=False, future=True)


def schedule_after_rollback(session: Session, action: AfterRollbackAction) -> None:
    """Eine Sicherheitsaenderung nach einem Request-Rollback dauerhaft ausfuehren.

    Die Aktion bekommt eine frische Session. So kann beispielsweise ein
    fehlgeschlagener Anmeldeversuch gespeichert werden, ohne dass fachliche
    Teilaenderungen aus der abgelehnten Anfrage mit uebernommen werden.
    """
    actions = cast(
        "list[AfterRollbackAction]",
        session.info.setdefault(_AFTER_ROLLBACK_KEY, []),
    )
    actions.append(action)


def _take_after_rollback_actions(session: Session) -> tuple[AfterRollbackAction, ...]:
    actions = cast(
        "list[AfterRollbackAction]",
        session.info.pop(_AFTER_ROLLBACK_KEY, []),
    )
    return tuple(actions)


def _run_after_rollback_actions(actions: tuple[AfterRollbackAction, ...]) -> None:
    if not actions:
        return

    security_session = get_sessionmaker()()
    try:
        for action in actions:
            action(security_session)
        security_session.commit()
    except Exception:
        security_session.rollback()
        raise
    finally:
        security_session.close()


@contextmanager
def unit_of_work() -> Iterator[Session]:
    """Eine Transaktion.

    Wird der Block ohne Ausnahme verlassen, folgt ein Commit. Andernfalls
    ein Rollback - auch bei einer Ausnahme, die nichts mit der Datenbank zu
    tun hat. Ein halb geschriebener Vorgang ist schlimmer als ein
    fehlgeschlagener.
    """
    session = get_sessionmaker()()
    try:
        yield session
        session.commit()
    except Exception:
        actions = _take_after_rollback_actions(session)
        session.rollback()
        _run_after_rollback_actions(actions)
        raise
    finally:
        session.close()


def get_session() -> Iterator[Session]:
    """Abhängigkeit für FastAPI-Routen."""
    with unit_of_work() as session:
        yield session
