"""M2 comments.

Revision ID: 0018
Revises: 0017
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "0018"
down_revision = "0017"
branch_labels = None
depends_on = None

UUID = postgresql.UUID(as_uuid=True)


def upgrade() -> None:
    op.create_table(
        "comments",
        sa.Column("id", UUID, nullable=False),
        sa.Column("space_id", UUID, nullable=False),
        sa.Column("owner_id", UUID, nullable=False),
        sa.Column("privacy_class", sa.String(32), nullable=False),
        sa.Column("target_type", sa.String(32), nullable=False),
        sa.Column("target_id", UUID, nullable=False),
        sa.Column("crypto_version", sa.SmallInteger(), nullable=False, server_default=sa.text("0")),
        sa.Column("payload", postgresql.JSONB(), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id", name="pk_comments"),
        sa.ForeignKeyConstraint(["space_id"], ["spaces.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["owner_id"], ["accounts.id"], ondelete="CASCADE"),
        sa.CheckConstraint("target_type IN ('MEMORY', 'HEART_MOMENT', 'MILESTONE')", name="comment_target_type_allowed"),
        sa.CheckConstraint("crypto_version >= 0", name="comment_crypto_version_non_negative"),
    )
    op.create_index("ix_comments_space_target_created", "comments", ["space_id", "target_type", "target_id", "created_at", "id"])
    op.create_index("ix_comments_owner_id", "comments", ["owner_id"])


def downgrade() -> None:
    op.drop_index("ix_comments_owner_id", table_name="comments")
    op.drop_index("ix_comments_space_target_created", table_name="comments")
    op.drop_table("comments")
