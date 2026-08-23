"""Gemeinsame Testvorrichtungen.

Zwei Ebenen, bewusst getrennt:

- Unit-Tests laufen ohne Datenbank und ohne Netz.
- Integrationstests brauchen eine erreichbare PostgreSQL-Instanz. Ist keine
  da, werden sie ÜBERSPRUNGEN und nicht stillschweigend als bestanden
  gewertet - ein grüner Lauf soll nicht mehr versprechen, als er geprüft
  hat.
"""

from __future__ import annotations

import os
from collections.abc import Iterator

import pytest
from sqlalchemy import Engine, create_engine, text
from sqlalchemy.orm import Session, sessionmaker

# Nie versehentlich gegen eine echte Instanz laufen.
os.environ.setdefault("SBS_ENVIRONMENT", "test")

INTEGRATION_DATABASE_URL = os.environ.get("SBS_TEST_DATABASE_URL", "")


def _database_reachable(url: str) -> bool:
    if not url:
        return False
    try:
        engine = create_engine(url, pool_pre_ping=True)
        with engine.connect() as verbindung:
            verbindung.execute(text("SELECT 1"))
        engine.dispose()
    except Exception:
        return False
    return True


DATABASE_AVAILABLE = _database_reachable(INTEGRATION_DATABASE_URL)

requires_database = pytest.mark.skipif(
    not DATABASE_AVAILABLE,
    reason=(
        "Keine PostgreSQL-Instanz erreichbar. "
        "SBS_TEST_DATABASE_URL setzen, um Integrationstests auszufuehren."
    ),
)


@pytest.fixture(scope="session")
def engine() -> Iterator[Engine]:
    if not DATABASE_AVAILABLE:
        pytest.skip("Keine Datenbank erreichbar.")

    from sidebyside.db.base import Base
    from sidebyside.jobs import models as _jobs  # noqa: F401
    from sidebyside.outbox import models as _outbox  # noqa: F401

    eng = create_engine(INTEGRATION_DATABASE_URL, future=True)
    Base.metadata.create_all(eng)
    yield eng
    Base.metadata.drop_all(eng)
    eng.dispose()


@pytest.fixture
def session(engine: Engine) -> Iterator[Session]:
    """Eine Sitzung je Test, die am Ende zurückgerollt wird.

    Kein Test hinterlaesst Zeilen fuer den naechsten. Reihenfolge-
    abhaengige Tests verbergen genau die Fehler, die man sucht.
    """
    verbindung = engine.connect()
    transaktion = verbindung.begin()
    sitzung = sessionmaker(bind=verbindung, expire_on_commit=False)()
    try:
        yield sitzung
    finally:
        sitzung.close()
        transaktion.rollback()
        verbindung.close()
