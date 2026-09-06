"""Add session-bound recent-authentication state.

Revision ID: 0045
Revises: 0044
Create Date: 2026-09-06
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "0045"
down_revision = "0044"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "webauthn_challenges",
        sa.Column("device_session_id", postgresql.UUID(as_uuid=True), nullable=True),
    )
    op.add_column(
        "webauthn_challenges",
        sa.Column("step_up_purpose", sa.String(length=64), nullable=True),
    )
    op.create_foreign_key(
        "fk_webauthn_challenges_device_session_id_device_sessions",
        "webauthn_challenges",
        "device_sessions",
        ["device_session_id"],
        ["id"],
        ondelete="CASCADE",
    )
    op.drop_constraint("purpose_is_known", "webauthn_challenges", type_="check")
    op.create_check_constraint(
        "purpose_is_known",
        "webauthn_challenges",
        "purpose IN ('REGISTRATION', 'AUTHENTICATION', 'STEP_UP')",
    )
    op.create_check_constraint(
        "step_up_binding_is_complete",
        "webauthn_challenges",
        "(purpose = 'STEP_UP' AND account_id IS NOT NULL AND device_session_id IS NOT NULL "
        "AND step_up_purpose IS NOT NULL) OR (purpose <> 'STEP_UP' AND device_session_id IS NULL "
        "AND step_up_purpose IS NULL)",
    )

    op.add_column(
        "oidc_auth_requests",
        sa.Column("device_session_id", postgresql.UUID(as_uuid=True), nullable=True),
    )
    op.add_column(
        "oidc_auth_requests",
        sa.Column("step_up_purpose", sa.String(length=64), nullable=True),
    )
    op.create_foreign_key(
        "fk_oidc_auth_requests_device_session_id_device_sessions",
        "oidc_auth_requests",
        "device_sessions",
        ["device_session_id"],
        ["id"],
        ondelete="CASCADE",
    )
    op.create_check_constraint(
        "oidc_step_up_binding_is_complete",
        "oidc_auth_requests",
        "(device_session_id IS NULL AND step_up_purpose IS NULL) OR "
        "(device_session_id IS NOT NULL AND account_id IS NOT NULL AND step_up_purpose IS NOT NULL)",
    )

    op.create_table(
        "recent_authentication_grants",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("account_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("device_session_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("purpose", sa.String(length=64), nullable=False),
        sa.Column("method", sa.String(length=32), nullable=False),
        sa.Column("achieved_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["account_id"], ["accounts.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["device_session_id"], ["device_sessions.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "account_id",
            "device_session_id",
            "purpose",
            name="uq_recent_authentication_grants_context",
        ),
        sa.CheckConstraint(
            "method IN ('LOCAL_PASSWORD', 'PASSKEY', 'OIDC')",
            name="recent_authentication_method_is_known",
        ),
        sa.CheckConstraint("expires_at > achieved_at", name="recent_authentication_expiry_after_achievement"),
    )
    op.create_index(
        "ix_recent_authentication_grants_expires_at",
        "recent_authentication_grants",
        ["expires_at"],
        unique=False,
    )
    op.create_index(
        "ix_recent_authentication_grants_device_session_id",
        "recent_authentication_grants",
        ["device_session_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        "ix_recent_authentication_grants_device_session_id",
        table_name="recent_authentication_grants",
    )
    op.drop_index(
        "ix_recent_authentication_grants_expires_at",
        table_name="recent_authentication_grants",
    )
    op.drop_table("recent_authentication_grants")

    op.drop_constraint(
        "oidc_step_up_binding_is_complete",
        "oidc_auth_requests",
        type_="check",
    )
    op.drop_constraint(
        "fk_oidc_auth_requests_device_session_id_device_sessions",
        "oidc_auth_requests",
        type_="foreignkey",
    )
    op.drop_column("oidc_auth_requests", "step_up_purpose")
    op.drop_column("oidc_auth_requests", "device_session_id")

    op.drop_constraint(
        "step_up_binding_is_complete",
        "webauthn_challenges",
        type_="check",
    )
    op.drop_constraint("purpose_is_known", "webauthn_challenges", type_="check")
    op.create_check_constraint(
        "purpose_is_known",
        "webauthn_challenges",
        "purpose IN ('REGISTRATION', 'AUTHENTICATION')",
    )
    op.drop_constraint(
        "fk_webauthn_challenges_device_session_id_device_sessions",
        "webauthn_challenges",
        type_="foreignkey",
    )
    op.drop_column("webauthn_challenges", "step_up_purpose")
    op.drop_column("webauthn_challenges", "device_session_id")
