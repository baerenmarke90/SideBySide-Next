"""M3 places and the plan place link.

Revision ID: 0021
Revises: 0020
Create Date: 2026-08-26
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "0021"
down_revision = "0020"
branch_labels = None
depends_on = None

UUID = postgresql.UUID(as_uuid=True)


def _privacy_class() -> sa.Enum:
    return sa.Enum(
        "SPACE_SHARED",
        "OWNER_ONLY",
        name="privacy_class",
        native_enum=False,
        create_constraint=True,
    )


def upgrade() -> None:
    op.create_table(
        "places",
        sa.Column("id", UUID, nullable=False),
        sa.Column("space_id", UUID, nullable=False),
        sa.Column("owner_id", UUID, nullable=False),
        sa.Column("privacy_class", _privacy_class(), nullable=False),
        # Sensibler Inhalt nach M3-D06, aber typisiert: nur so lassen sich
        # Wertebereich und Genauigkeit in der Datenbank durchsetzen. Die
        # Klassifizierung aendert die Spaltenform nicht - Koordinaten
        # gehoeren trotzdem in kein Log und kein Event.
        #
        # 90.000000 braucht acht Stellen, 180.000000 neun.
        sa.Column("latitude", sa.Numeric(8, 6), nullable=True),
        sa.Column("longitude", sa.Numeric(9, 6), nullable=True),
        sa.Column("crypto_version", sa.SmallInteger(), server_default=sa.text("0"), nullable=False),
        sa.Column("payload", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id", name="pk_places"),
        sa.ForeignKeyConstraint(
            ["space_id"], ["spaces.id"], name="fk_places_space_id_spaces", ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(
            ["owner_id"],
            ["accounts.id"],
            name="fk_places_owner_id_accounts",
            ondelete="CASCADE",
        ),
        sa.CheckConstraint("privacy_class = 'SPACE_SHARED'", name="privacy_is_space_shared"),
        sa.CheckConstraint("crypto_version >= 0", name="crypto_version_is_non_negative"),
        # Beide oder keine - eine halbe Koordinate ist kein Ort.
        sa.CheckConstraint(
            "(latitude IS NULL) = (longitude IS NULL)",
            name="coordinates_are_a_pair",
        ),
        sa.CheckConstraint(
            "latitude IS NULL OR (latitude >= -90 AND latitude <= 90)",
            name="latitude_within_range",
        ),
        sa.CheckConstraint(
            "longitude IS NULL OR (longitude >= -180 AND longitude <= 180)",
            name="longitude_within_range",
        ),
        # Traegt den zusammengesetzten Fremdschluessel von `plans`.
        sa.UniqueConstraint("id", "space_id", name="uq_places_id_space_id"),
    )
    op.create_index("ix_places_space_id", "places", ["space_id"])
    op.create_index("ix_places_owner_id", "places", ["owner_id"])
    op.create_index("ix_places_space_id_created_at_id", "places", ["space_id", "created_at", "id"])

    # Aus M3-S2 verschoben: ohne Place-Domaene haette das Feld auf nichts
    # zeigen koennen (M3-D08/D31).
    op.add_column("plans", sa.Column("place_id", UUID, nullable=True))
    op.create_index("ix_plans_place_id", "plans", ["place_id"])
    # `SET NULL` mit Spaltenliste (PostgreSQL 15+): ohne sie wuerde auch
    # `space_id` geleert, und die ist NOT NULL.
    op.create_foreign_key(
        "fk_plans_place_id_places",
        "plans",
        "places",
        ["place_id", "space_id"],
        ["id", "space_id"],
        ondelete="SET NULL (place_id)",
    )


def downgrade() -> None:
    op.drop_constraint("fk_plans_place_id_places", "plans", type_="foreignkey")
    op.drop_index("ix_plans_place_id", table_name="plans")
    op.drop_column("plans", "place_id")
    op.drop_index("ix_places_space_id_created_at_id", table_name="places")
    op.drop_index("ix_places_owner_id", table_name="places")
    op.drop_index("ix_places_space_id", table_name="places")
    op.drop_table("places")
