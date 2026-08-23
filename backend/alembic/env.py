"""Alembic-Umgebung.

Die Verbindung kommt aus der Anwendungskonfiguration, nicht aus alembic.ini
- ein Zugangsdatum gehört nicht in eine eingecheckte Datei.

Alle Modelle werden hier importiert, damit `--autogenerate` sie sieht. Ein
vergessener Import erzeugt eine Migration, die eine Tabelle löschen will.
"""

from __future__ import annotations

from logging.config import fileConfig

from alembic import context
from sqlalchemy import engine_from_config, pool

from sidebyside.config import get_settings
from sidebyside.db.base import Base

# Modelle registrieren. Die Importe sehen ungenutzt aus, sind es aber nicht.
from sidebyside.jobs import models as _jobs  # noqa: F401
from sidebyside.outbox import models as _outbox  # noqa: F401

config = context.config
config.set_main_option("sqlalchemy.url", get_settings().database_url)

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    context.configure(
        url=config.get_main_option("sqlalchemy.url"),
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
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
        )
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
