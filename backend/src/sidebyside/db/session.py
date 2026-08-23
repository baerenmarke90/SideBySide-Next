"""Datenbankverbindung und Transaktionsgrenze.

Eine Anfrage ist eine Transaktion. Sie wird am Ende der Anfrage übergeben
oder vollständig zurückgerollt - nicht stückweise während der Verarbeitung.

Das ist die Voraussetzung für die Transactional Outbox: fachliche Änderung
und Ereignis müssen gemeinsam wirksam werden oder gemeinsam ausbleiben.
"""

from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager
from functools import lru_cache

from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import Session, sessionmaker

from sidebyside.config import get_settings


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
        session.rollback()
        raise
    finally:
        session.close()


def get_session() -> Iterator[Session]:
    """Abhängigkeit für FastAPI-Routen."""
    with unit_of_work() as session:
        yield session
