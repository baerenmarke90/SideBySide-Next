"""M2 memories and resource-versioned outbox events.

Revision ID: 0013
Revises: 0012
Create Date: 2026-08-25
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "0013"
down_revision = "0012"
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
    op.add_column("outbox_events", sa.Column("resource_version", sa.Integer(), nullable=True))
    op.create_check_constraint(
        "resource_version_is_positive",
        "outbox_events",
        "resource_version IS NULL OR resource_version >= 1",
    )

    op.create_table(
        "memories",
        sa.Column("id", UUID, nullable=False),
        sa.Column("space_id", UUID, nullable=False),
        sa.Column("owner_id", UUID, nullable=False),
        sa.Column("privacy_class", _privacy_class(), nullable=False),
        sa.Column("happened_on", sa.Date(), nullable=True),
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
        sa.PrimaryKeyConstraint("id", name="pk_memories"),
        sa.ForeignKeyConstraint(
            ["space_id"],
            ["spaces.id"],
            name="fk_memories_space_id_spaces",
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["owner_id"],
            ["accounts.id"],
            name="fk_memories_owner_id_accounts",
            ondelete="CASCADE",
        ),
        sa.CheckConstraint("privacy_class = 'SPACE_SHARED'", name="privacy_is_space_shared"),
        sa.CheckConstraint("crypto_version >= 0", name="crypto_version_is_non_negative"),
    )
    op.create_index("ix_memories_space_id", "memories", ["space_id"])
    op.create_index("ix_memories_owner_id", "memories", ["owner_id"])
    op.create_index(
        "ix_memories_space_id_created_at_id",
        "memories",
        ["space_id", "created_at", "id"],
    )
    op.create_index(
        "ix_memories_space_id_happened_on",
        "memories",
        ["space_id", "happened_on"],
    )


def downgrade() -> None:
    op.drop_index("ix_memories_space_id_happened_on", table_name="memories")
    op.drop_index("ix_memories_space_id_created_at_id", table_name="memories")
    op.drop_index("ix_memories_owner_id", table_name="memories")
    op.drop_index("ix_memories_space_id", table_name="memories")
    op.drop_table("memories")
    op.drop_constraint(
        "ck_outbox_events_resource_version_is_positive",
        "outbox_events",
        type_="check",
    )
    op.drop_column("outbox_events", "resource_version")
