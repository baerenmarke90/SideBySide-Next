"""Profile avatar attachment binding.

Revision ID: 0034
Revises: 0033
Create Date: 2026-08-31
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "0034"
down_revision = "0033"
branch_labels = None
depends_on = None

UUID = postgresql.UUID(as_uuid=True)


def upgrade() -> None:
    op.create_table(
        "account_profile_attachments",
        sa.Column("id", UUID, nullable=False),
        sa.Column("account_id", UUID, nullable=False),
        sa.Column("attachment_id", UUID, nullable=False),
        sa.PrimaryKeyConstraint("id", name="pk_account_profile_attachments"),
        sa.ForeignKeyConstraint(
            ["account_id"],
            ["accounts.id"],
            name="fk_account_profile_attachments_account_id_accounts",
            ondelete="CASCADE",
        ),
        # Bound profile media must be detached before physical provider cleanup.
        # RESTRICT preserves that ordering instead of silently dropping the
        # current-avatar relation when an attachment row is deleted.
        sa.ForeignKeyConstraint(
            ["attachment_id"],
            ["attachments.id"],
            name="fk_account_profile_attachments_attachment_id_attachments",
            ondelete="RESTRICT",
        ),
        sa.UniqueConstraint(
            "account_id",
            name="uq_account_profile_attachments_account",
        ),
        sa.UniqueConstraint(
            "attachment_id",
            name="uq_account_profile_attachments_attachment",
        ),
    )


def downgrade() -> None:
    op.drop_table("account_profile_attachments")
