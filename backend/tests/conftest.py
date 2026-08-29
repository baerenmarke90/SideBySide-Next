"""Shared test fixtures.

Two layers are deliberately kept separate:

- Unit tests run without a database and without network access.
- Integration tests require a reachable PostgreSQL instance. If none is
  available, they are SKIPPED rather than silently counted as passed; a green
  run must not promise more than it actually verified.
"""

from __future__ import annotations

import os
import shutil
import tempfile
from collections.abc import Iterator

import pytest
from sqlalchemy import Engine, create_engine, text
from sqlalchemy.orm import Session, sessionmaker

# Never accidentally run against a real instance.
os.environ.setdefault("SBS_ENVIRONMENT", "test")

TEST_BOOTSTRAP_TOKEN = "test-bootstrap-token-with-at-least-32-characters"
os.environ.setdefault("SBS_BOOTSTRAP_TOKEN", TEST_BOOTSTRAP_TOKEN)

# Media files go into a temporary directory rather than the working tree. The
# configuration default is "./data/media"; without this override, a test run
# would leave files in the repository that nobody should accidentally commit.
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
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
        engine.dispose()
    except Exception:
        return False
    return True


DATABASE_AVAILABLE = _database_reachable(INTEGRATION_DATABASE_URL)

requires_database = pytest.mark.skipif(
    not DATABASE_AVAILABLE,
    reason=(
        "No PostgreSQL instance is reachable. Set SBS_TEST_DATABASE_URL to run integration tests."
    ),
)


@pytest.fixture(scope="session")
def engine() -> Iterator[Engine]:
    if not DATABASE_AVAILABLE:
        pytest.skip("No database is reachable.")

    # The same list as in alembic/env.py, for the same reason: anything missing
    # here does not exist during create_all. A later import by the app would
    # register the model, but only after the tables have been created, making
    # tests pass or fail accidentally depending on prior imports.
    from sidebyside.attachments import binding as _binding  # noqa: F401
    from sidebyside.attachments import models as _attachments  # noqa: F401
    from sidebyside.chapters import models as _chapters  # noqa: F401
    from sidebyside.comments import models as _comments  # noqa: F401
    from sidebyside.db.base import Base
    from sidebyside.heart_moments import models as _heart_moments  # noqa: F401
    from sidebyside.identity import models as _identity  # noqa: F401
    from sidebyside.jobs import models as _jobs  # noqa: F401
    from sidebyside.memories import models as _memories  # noqa: F401
    from sidebyside.milestones import models as _milestones  # noqa: F401
    from sidebyside.outbox import models as _outbox  # noqa: F401
    from sidebyside.people import models as _people  # noqa: F401
    from sidebyside.places import models as _places  # noqa: F401
    from sidebyside.plans import models as _plans  # noqa: F401
    from sidebyside.profiles import models as _profiles  # noqa: F401
    from sidebyside.relations import models as _relations  # noqa: F401
    from sidebyside.relationship import models as _relationship  # noqa: F401
    from sidebyside.wishes import models as _wishes  # noqa: F401

    # Test probe for owner/privacy authorization. It deliberately exists only
    # here: alembic/env.py does not know it, so it appears in no migration and
    # no production database.
    from tests.support import privacy_probe as _privacy_probe  # noqa: F401

    db_engine = create_engine(INTEGRATION_DATABASE_URL, future=True)
    Base.metadata.create_all(db_engine)
    yield db_engine
    Base.metadata.drop_all(db_engine)
    db_engine.dispose()


@pytest.fixture
def session(engine: Engine) -> Iterator[Session]:
    """Provide one session per test and roll it back afterwards.

    No test leaves rows behind for the next one. Order-dependent tests hide
    exactly the defects these tests are meant to find.
    """
    connection = engine.connect()
    transaction = connection.begin()
    test_session = sessionmaker(bind=connection, expire_on_commit=False)()
    try:
        yield test_session
    finally:
        test_session.close()
        transaction.rollback()
        connection.close()


@pytest.fixture
def client(session: Session):  # type: ignore[no-untyped-def]
    """Provide an HTTP client using the same transaction as the test.

    Without the override, the application would open its own sessions and
    could not see uncommitted test data.
    """
    from fastapi.testclient import TestClient

    from sidebyside.db.session import get_session
    from sidebyside.main import create_app

    app = create_app()
    app.dependency_overrides[get_session] = lambda: session
    return TestClient(app, raise_server_exceptions=False)


def _clear_database(engine: Engine) -> None:
    """Remove committed test data in foreign-key-safe order."""
    from sidebyside.db.base import Base

    with engine.begin() as connection:
        for table in reversed(Base.metadata.sorted_tables):
            connection.execute(table.delete())


@pytest.fixture
def production_client(engine: Engine, monkeypatch):  # type: ignore[no-untyped-def]
    """Provide an HTTP client using the real request unit of work.

    Unlike the normal ``client``, each request gets its own session and
    therefore the exact commit/rollback boundary used in production.
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

    account = Account(display_name=name)
    session.add(account)
    session.flush()
    return account


def make_space(session: Session, founder):  # type: ignore[no-untyped-def]
    from sidebyside.relationship.service import create_space

    return create_space(session, founder)


def sign_in(session: Session, account) -> str:  # type: ignore[no-untyped-def]
    """Issue a real access token.

    Go through the regular service rather than around it; a forged token would
    skip exactly the path that this helper is meant to exercise.
    """
    from sidebyside.auth.sessions import start_session

    _, tokens = start_session(session, account)
    session.flush()
    return tokens.access_token


def auth(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}
