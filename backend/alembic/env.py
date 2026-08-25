"""Alembic-Umgebung.

Die Verbindung kommt aus der Anwendungskonfiguration, nicht aus alembic.ini
- ein Zugangsdatum gehört nicht in eine eingecheckte Datei.

Alle Modelle werden hier importiert, damit `--autogenerate` sie sieht. Ein
vergessener Import erzeugt eine Migration, die eine Tabelle löschen will.
"""

from __future__ import annotations

from logging.config import fileConfig

from alembic import context
from sqlalchemy import CheckConstraint, engine_from_config, pool
from sqlalchemy.schema import SchemaItem

# Modelle registrieren. Die Importe sehen ungenutzt aus, sind es aber nicht.
from sidebyside.attachments import models as _attachments  # noqa: F401
from sidebyside.config import get_settings
from sidebyside.db.base import Base
from sidebyside.heart_moments import models as _heart_moments  # noqa: F401
from sidebyside.identity import models as _identity  # noqa: F401
from sidebyside.jobs import models as _jobs  # noqa: F401
from sidebyside.memories import models as _memories  # noqa: F401
from sidebyside.outbox import models as _outbox  # noqa: F401
from sidebyside.people import models as _people  # noqa: F401
from sidebyside.profiles import models as _profiles  # noqa: F401
from sidebyside.relationship import models as _relationship  # noqa: F401

config = context.config
config.set_main_option("sqlalchemy.url", get_settings().database_url)

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def _typgebundene_pruefregeln(tabellenname: str) -> set[str]:
    """Namen der CHECK-Regeln, die am Spaltentyp haengen statt an der Tabelle.

    `SqlEnum(native_enum=False, create_constraint=True)` erzeugt seine
    Wertebereichspruefung aus dem Typ heraus. Sie steht in der Tabelle, gehoert
    aber dem Typ - Alembic nennt das typgebunden.
    """
    tabelle = Base.metadata.tables.get(tabellenname)
    if tabelle is None:
        return set()
    return {
        regel.name
        for regel in tabelle.constraints
        if isinstance(regel, CheckConstraint)
        # Kein oeffentliches Attribut, aber genau das Merkmal, an dem auch
        # Alembic selbst typgebundene Regeln erkennt.
        and getattr(regel, "_type_bound", False)
        and regel.name is not None
    }


def include_object(
    objekt: SchemaItem,
    name: str | None,
    typ: str,
    reflektiert: bool,
    verglichen_mit: SchemaItem | None,
) -> bool:
    """Typgebundene CHECK-Regeln aus dem Autogenerate-Vergleich nehmen.

    Autogenerate laesst sie auf der Modellseite bewusst aus, liest sie in der
    Datenbank aber mit - und schlaegt deshalb bei jedem Lauf vor, sie zu
    loeschen. Der Drift-Check waere damit dauerhaft rot.

    Dieselbe Regel zusaetzlich von Hand an die Tabelle zu haengen ist der
    naheliegende Ausweg und der falsche: sie bekaeme denselben Namen wie die
    des Typs, und `create_all` scheitert an der doppelten Constraint.
    """
    if typ != "check_constraint" or not reflektiert or name is None:
        return True
    tabelle = getattr(objekt, "table", None)
    if tabelle is None:
        return True
    return name not in _typgebundene_pruefregeln(tabelle.name)


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
