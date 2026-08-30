"""Alembic environment.

The connection comes from the environment rather than alembic.ini because
credentials do not belong in a committed file. Only `DatabaseSettings` is
loaded instead of the complete application configuration: a migration needs
the database, but neither a cursor-signing key nor SMTP nor a public address.
Depending on those would make `alembic upgrade head` fail in production
before the first revision ran.

All models are imported here so `--autogenerate` can see them. A missing
import can produce a migration that tries to drop a table.
"""

from __future__ import annotations

from logging.config import fileConfig

from alembic import context
from pydantic import ValidationError
from sqlalchemy import CheckConstraint, engine_from_config, pool
from sqlalchemy.schema import SchemaItem

from sidebyside.attachments import binding as _binding  # noqa: F401

# Register models. These imports look unused, but they are not.
from sidebyside.attachments import models as _attachments  # noqa: F401
from sidebyside.chapters import models as _chapters  # noqa: F401
from sidebyside.collections import models as _collections  # noqa: F401
from sidebyside.comments import models as _comments  # noqa: F401
from sidebyside.config import DatabaseSettings
from sidebyside.db.base import Base
from sidebyside.gift_ideas import models as _gift_ideas  # noqa: F401
from sidebyside.heart_moments import models as _heart_moments  # noqa: F401
from sidebyside.identity import models as _identity  # noqa: F401
from sidebyside.jobs import models as _jobs  # noqa: F401
from sidebyside.memories import models as _memories  # noqa: F401
from sidebyside.milestones import models as _milestones  # noqa: F401
from sidebyside.outbox import models as _outbox  # noqa: F401
from sidebyside.people import models as _people  # noqa: F401
from sidebyside.places import models as _places  # noqa: F401
from sidebyside.plans import models as _plans  # noqa: F401
from sidebyside.private_collections import models as _private_collections  # noqa: F401
from sidebyside.private_notes import models as _private_notes  # noqa: F401
from sidebyside.profiles import models as _profiles  # noqa: F401
from sidebyside.relations import models as _relations  # noqa: F401
from sidebyside.relationship import models as _relationship  # noqa: F401
from sidebyside.wishes import models as _wishes  # noqa: F401


def _migration_connection() -> str:
    """Return the database URL for this run or fail with a clear diagnostic.

    Validation is caught and reformulated here because a raw
    `ValidationError` looks like an application error. A migration operator
    should instead see which environment variable is missing.
    """
    try:
        return DatabaseSettings().database_url
    except ValidationError as error:
        raise SystemExit(
            "Migration cannot start: SBS_DATABASE_URL is missing or invalid. "
            "Expected a PostgreSQL URL, for example "
            "postgresql+psycopg://user:password@host:5432/database. "
            f"Cause: {error}"
        ) from error


config = context.config
config.set_main_option("sqlalchemy.url", _migration_connection())

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def _type_bound_checks(table_name: str) -> set[str]:
    """Return CHECK names owned by a column type rather than the table.

    `SqlEnum(native_enum=False, create_constraint=True)` creates its allowed
    value check from the type. The constraint lives on the table but belongs
    to the type; Alembic calls this type-bound.
    """
    table = Base.metadata.tables.get(table_name)
    if table is None:
        return set()
    return {
        constraint.name
        for constraint in table.constraints
        if isinstance(constraint, CheckConstraint)
        # No public attribute exists, but this is the same marker Alembic uses
        # internally to identify type-bound constraints.
        and getattr(constraint, "_type_bound", False)
        and constraint.name is not None
    }


def include_object(
    object_: SchemaItem,
    name: str | None,
    type_: str,
    reflected: bool,
    compare_to: SchemaItem | None,
) -> bool:
    """Exclude type-bound CHECK constraints from autogenerate comparison.

    Autogenerate deliberately omits them on the model side but reads them
    from the database, otherwise proposing their removal on every run and
    keeping the drift check permanently red.

    Manually adding the same rule to the table is the obvious but wrong
    workaround: it would receive the same name as the type-owned constraint
    and `create_all` would fail on the duplicate.
    """
    del compare_to
    if type_ != "check_constraint" or not reflected or name is None:
        return True
    table = getattr(object_, "table", None)
    if table is None:
        return True
    return name not in _type_bound_checks(table.name)


def run_migrations_offline() -> None:
    context.configure(
        url=config.get_main_option("sqlalchemy.url"),
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
        include_object=include_object,
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
            include_object=include_object,
        )
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
