"""M3 typed content relations between places and shared content.

Revision ID: 0022
Revises: 0021
Create Date: 2026-08-27
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "0022"
down_revision = "0021"
branch_labels = None
depends_on = None

UUID = postgresql.UUID(as_uuid=True)

# Die beiden Ziele mit einheitlicher Form. `heart_moments` steht weiter
# unten fuer sich: nur dort haengt die Zulaessigkeit einer Relation an der
# Privacy-Klasse, und das schlaegt sich im Schluessel nieder.
#
# `place_plans` und `place_chapters` entstehen bewusst nicht: `Plan.placeId`
# ist kanonisch und einspaltig, und `Chapter` gibt es erst in S5
# (M3-D08/D31).
_TARGETS = ("memories", "milestones")

_TARGET_COLUMNS = {"memories": "memory_id", "milestones": "milestone_id"}


def _privacy_class() -> sa.Enum:
    return sa.Enum(
        "SPACE_SHARED",
        "OWNER_ONLY",
        name="privacy_class",
        native_enum=False,
        create_constraint=True,
    )


def _relation_columns(target_column: str) -> list[sa.Column]:
    """Die gemeinsame Form aller Join-Tabellen.

    `space_id` steht in der Join-Zeile, obwohl sie aus beiden Seiten
    ableitbar waere. Genau das ist der Zweck: weil *dieselbe* Spalte in
    beiden zusammengesetzten Fremdschluesseln steht, kann eine Relation
    zwei Zeilen aus verschiedenen Spaces gar nicht verbinden. Same-Space
    ist damit eine Schemaeigenschaft und keine Regel, die ein Dienst
    einhalten muss (M3-D08).
    """
    return [
        sa.Column("place_id", UUID, nullable=False),
        sa.Column(target_column, UUID, nullable=False),
        sa.Column("space_id", UUID, nullable=False),
        sa.Column("created_by", UUID, nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    ]


def upgrade() -> None:
    # Ziel der zusammengesetzten Fremdschluessel. Ohne diese Unique-
    # Constraints koennte PostgreSQL das Paar (id, space_id) nicht
    # referenzieren.
    op.create_unique_constraint("uq_memories_id_space_id", "memories", ["id", "space_id"])
    op.create_unique_constraint("uq_milestones_id_space_id", "milestones", ["id", "space_id"])

    # Beim HeartMoment gehoert die Privacy-Klasse mit in den Schluessel.
    # Sie ist der Grund, warum dieser Slice ueberhaupt heikel ist, und sie
    # traegt hier die Last statt einer Dienstregel - siehe unten.
    op.create_unique_constraint(
        "uq_heart_moments_id_space_id_privacy",
        "heart_moments",
        ["id", "space_id", "privacy_class"],
    )

    for target in _TARGETS:
        table = f"place_{target}"
        target_column = _TARGET_COLUMNS[target]

        op.create_table(
            table,
            *_relation_columns(target_column),
            # Der Primaerschluessel ist zugleich die Eindeutigkeit: dieselbe
            # Relation kann nicht zweimal existieren. Ein doppeltes PUT ist
            # deshalb idempotent und braucht kein vorheriges SELECT
            # (M3-D26).
            sa.PrimaryKeyConstraint("place_id", target_column, name=f"pk_{table}"),
            sa.ForeignKeyConstraint(
                ["place_id", "space_id"],
                ["places.id", "places.space_id"],
                name=f"fk_{table}_place_id_places",
                ondelete="CASCADE",
            ),
            sa.ForeignKeyConstraint(
                [target_column, "space_id"],
                [f"{target}.id", f"{target}.space_id"],
                name=f"fk_{table}_{target_column}_{target}",
                ondelete="CASCADE",
            ),
            sa.ForeignKeyConstraint(
                ["created_by"],
                ["accounts.id"],
                name=f"fk_{table}_created_by_accounts",
                ondelete="CASCADE",
            ),
        )
        # Die Gegenrichtung: "welche Orte hat diese Erinnerung?" und das
        # Aufraeumen beim Target-Delete.
        op.create_index(f"ix_{table}_{target_column}", table, [target_column])
        op.create_index(f"ix_{table}_space_id", table, ["space_id"])
        op.create_index(
            f"ix_{table}_place_id_created_at",
            table,
            ["place_id", "created_at", target_column],
        )

    # HeartMoments duerfen nur gemeinsam relationiert werden (M3-D09).
    #
    # Die Join-Zeile traegt die Privacy-Klasse des Ziels mit und ist per
    # CHECK auf `SPACE_SHARED` festgenagelt. Der Fremdschluessel zeigt auf
    # `(id, space_id, privacy_class)` und kaskadiert Aenderungen. Wechselt
    # ein HeartMoment auf `OWNER_ONLY`, ohne dass seine Relationen zuvor
    # entfernt wurden, zieht das Update die Klasse in die Join-Zeile - und
    # der CHECK bricht die Transaktion ab.
    #
    # Der Dienst entfernt die Relationen in derselben Transaktion und laeuft
    # deshalb nie dagegen. Das hier ist der Boden darunter: der Zustand
    # "privat, aber ueber eine gemeinsame Relation beweisbar" laesst sich
    # nicht hinschreiben, auch nicht von einem spaeteren Codepfad, der die
    # Regel nicht kennt.
    op.create_table(
        "place_heart_moments",
        *_relation_columns("heart_moment_id"),
        sa.Column("target_privacy_class", _privacy_class(), nullable=False),
        sa.PrimaryKeyConstraint("place_id", "heart_moment_id", name="pk_place_heart_moments"),
        sa.CheckConstraint(
            "target_privacy_class = 'SPACE_SHARED'",
            name="relation_target_is_shared",
        ),
        sa.ForeignKeyConstraint(
            ["place_id", "space_id"],
            ["places.id", "places.space_id"],
            name="fk_place_heart_moments_place_id_places",
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["heart_moment_id", "space_id", "target_privacy_class"],
            ["heart_moments.id", "heart_moments.space_id", "heart_moments.privacy_class"],
            name="fk_place_heart_moments_heart_moment_id_heart_moments",
            ondelete="CASCADE",
            onupdate="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["created_by"],
            ["accounts.id"],
            name="fk_place_heart_moments_created_by_accounts",
            ondelete="CASCADE",
        ),
    )
    op.create_index(
        "ix_place_heart_moments_heart_moment_id",
        "place_heart_moments",
        ["heart_moment_id"],
    )
    op.create_index("ix_place_heart_moments_space_id", "place_heart_moments", ["space_id"])
    op.create_index(
        "ix_place_heart_moments_place_id_created_at",
        "place_heart_moments",
        ["place_id", "created_at", "heart_moment_id"],
    )


def downgrade() -> None:
    op.drop_index("ix_place_heart_moments_place_id_created_at", table_name="place_heart_moments")
    op.drop_index("ix_place_heart_moments_space_id", table_name="place_heart_moments")
    op.drop_index("ix_place_heart_moments_heart_moment_id", table_name="place_heart_moments")
    op.drop_table("place_heart_moments")

    for target in _TARGETS:
        table = f"place_{target}"
        target_column = _TARGET_COLUMNS[target]
        op.drop_index(f"ix_{table}_place_id_created_at", table_name=table)
        op.drop_index(f"ix_{table}_space_id", table_name=table)
        op.drop_index(f"ix_{table}_{target_column}", table_name=table)
        op.drop_table(table)

    op.drop_constraint("uq_heart_moments_id_space_id_privacy", "heart_moments", type_="unique")
    op.drop_constraint("uq_milestones_id_space_id", "milestones", type_="unique")
    op.drop_constraint("uq_memories_id_space_id", "memories", type_="unique")
