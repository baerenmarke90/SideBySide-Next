"""OIDC auth requests

Revision ID: 0010
Revises: 0009
Create Date: 2026-08-24
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "0010"
down_revision = "0009"
branch_labels = None
depends_on = None

UUID = postgresql.UUID(as_uuid=True)


def upgrade() -> None:
    op.create_table(
        "oidc_auth_requests",
        sa.Column("id", UUID, nullable=False),
        sa.Column("connection_id", sa.String(length=64), nullable=False),
        sa.Column("state_hash", sa.String(length=64), nullable=False),
        sa.Column("nonce", sa.String(length=128), nullable=False),
        sa.Column("code_verifier", sa.String(length=128), nullable=False),
        sa.Column("redirect_uri", sa.String(length=512), nullable=False),
        sa.Column("account_id", UUID, nullable=True),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("consumed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id", name="pk_oidc_auth_requests"),
        sa.ForeignKeyConstraint(
            ["account_id"],
            ["accounts.id"],
            name="fk_oidc_auth_requests_account_id_accounts",
            ondelete="CASCADE",
        ),
        sa.UniqueConstraint("state_hash", name="uq_oidc_auth_requests_state_hash"),
    )
    op.create_index("ix_oidc_auth_requests_expires_at", "oidc_auth_requests", ["expires_at"])


def downgrade() -> None:
    op.drop_index("ix_oidc_auth_requests_expires_at", table_name="oidc_auth_requests")
    op.drop_table("oidc_auth_requests")
