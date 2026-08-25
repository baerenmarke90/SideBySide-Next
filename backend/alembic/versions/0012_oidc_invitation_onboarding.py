"""OIDC invitation onboarding.

Revision ID: 0012
Revises: 0011
Create Date: 2026-08-25
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "0012"
down_revision = "0011"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "oidc_auth_requests",
        sa.Column("invitation_token_hash", sa.String(length=64), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("oidc_auth_requests", "invitation_token_hash")
