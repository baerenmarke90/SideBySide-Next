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
import shutil
import tempfile
from collections.abc import Iterator

import pytest
from sqlalchemy import Engine, create_engine, text
from sqlalchemy.orm import Session, sessionmaker

# Nie versehentlich gegen eine echte Instanz laufen.
os.environ.setdefault("SBS_ENVIRONMENT", "test")

TEST_BOOTSTRAP_TOKEN = "test-bootstrap-token-with-at-least-32-characters"
os.environ.setdefault("SBS_BOOTSTRAP_TOKEN", TEST_BOOTSTRAP_TOKEN)

# Medien landen im temporaeren Verzeichnis, nicht im Arbeitsbaum. Der
# Standardwert der Konfiguration ist "./data/media" - ein Testlauf wuerde
# damit Dateien im Repository hinterlassen, und zwar genau die, die
# niemand versehentlich einchecken will.
MEDIA_ROOT = os.environ.setdefault(
    "SBS_MEDIA_ROOT", tempfile.mkdtemp(prefix="sidebyside-test-media-")
)

INTEGRATION_DATABASE_URL = os.environ.get("SBS_TEST_DATABASE_URL", "")


@pytest.fixture(scope="session", autouse=True)
def _media_root() -> Iterator[None]:
    yield
    if MEDIA_ROOT.startswith(tempfile.gettempdir()):
        shutil.rmtree(MEDIA_ROOT, ignore_errors=True)


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

    # Dieselbe Liste wie in alembic/env.py, und aus demselben Grund: was
    # hier fehlt, existiert beim create_all nicht. Ein spaeterer Import
    # durch die App wuerde das Modell zwar registrieren, aber erst nachdem
    # die Tabellen angelegt sind - die Tests liefen dann nur zufaellig
    # gruen, je nachdem was vorher importiert wurde.
    from sidebyside.attachments import binding as _binding  # noqa: F401
    from sidebyside.attachments import models as _attachments  # noqa: F401
    from sidebyside.comments import models as _comments  # noqa: F401
    from sidebyside.db.base import Base
    from sidebyside.heart_moments import models as _heart_moments  # noqa: F401
    from sidebyside.identity import models as _identity  # noqa: F401
    from sidebyside.jobs import models as _jobs  # noqa: F401
    from sidebyside.memories import models as _memories  # noqa: F401
    from sidebyside.milestones import models as _milestones  # noqa: F401
    from sidebyside.outbox import models as _outbox  # noqa: F401
    from sidebyside.people import models as _people  # noqa: F401
    from sidebyside.profiles import models as _profiles  # noqa: F401
    from sidebyside.relationship import models as _relationship  # noqa: F401
    from sidebyside.wishes import models as _wishes  # noqa: F401

    # Die Testsonde fuer die Owner-/Privacy-Autorisierung. Sie steht
    # bewusst nur hier: alembic/env.py kennt sie nicht, also erscheint
    # sie in keiner Migration und in keiner Produktionsdatenbank.
    from tests.support import privacy_probe as _privacy_probe  # noqa: F401

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


@pytest.fixture
def client(session: Session):  # type: ignore[no-untyped-def]
    """Ein HTTP-Client auf derselben Transaktion wie der Test.

    Ohne die Umleitung wuerde die Anwendung eigene Sitzungen oeffnen und
    die noch nicht uebergebenen Testdaten nicht sehen.
    """
    from fastapi.testclient import TestClient

    from sidebyside.db.session import get_session
    from sidebyside.main import create_app

    app = create_app()
    app.dependency_overrides[get_session] = lambda: session
    return TestClient(app, raise_server_exceptions=False)


def _clear_database(engine: Engine) -> None:
    """Fest geschriebene Testdaten in FK-sicherer Reihenfolge entfernen."""
    from sidebyside.db.base import Base

    with engine.begin() as connection:
        for table in reversed(Base.metadata.sorted_tables):
            connection.execute(table.delete())


@pytest.fixture
def production_client(engine: Engine, monkeypatch):  # type: ignore[no-untyped-def]
    """HTTP-Client mit dem echten Request-Unit-of-Work.

    Im Gegensatz zum normalen ``client`` bekommt jede Anfrage eine eigene
    Session und damit genau die Commit-/Rollback-Grenze aus der Produktion.
    """
    from fastapi.testclient import TestClient

    from sidebyside.db import session as db_session
    from sidebyside.main import create_app

    maker = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False, future=True)
    monkeypatch.setattr(db_session, "get_sessionmaker", lambda: maker)

    _clear_database(engine)
    try:
        with TestClient(create_app(), raise_server_exceptions=False) as test_client:
            yield test_client, maker
    finally:
        _clear_database(engine)


def make_account(session: Session, name: str = "Testperson"):  # type: ignore[no-untyped-def]
    from sidebyside.identity.models import Account

    konto = Account(display_name=name)
    session.add(konto)
    session.flush()
    return konto


def make_space(session: Session, founder):  # type: ignore[no-untyped-def]
    from sidebyside.relationship.service import create_space

    return create_space(session, founder)


def sign_in(session: Session, account) -> str:  # type: ignore[no-untyped-def]
    """Einen echten Access Token ausstellen.

    Ueber den regulaeren Dienst, nicht an ihm vorbei - ein gefaelschter
    Token wuerde genau den Weg ueberspringen, der geprueft werden soll.
    """
    from sidebyside.auth.sessions import start_session

    _, tokens = start_session(session, account)
    session.flush()
    return tokens.access_token


def auth(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}
