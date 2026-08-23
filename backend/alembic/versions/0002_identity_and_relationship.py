"""identity and relationship

Die Sicherheitsgrundlage: Accounts, Anmeldewege, Geraetesitzungen, Spaces
und Mitgliedschaften. Vor jeder Inhaltsdomaene, damit kein Inhalt entstehen
kann, bevor klar ist, wem er gehoert.

Revision ID: 0002
Revises: 0001
Create Date: 2026-08-23
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "0002"
down_revision = "0001"
branch_labels = None
depends_on = None

UUID = postgresql.UUID(as_uuid=True)


def _timestamps() -> list[sa.Column]:
    return [
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
    ]


def upgrade() -> None:
    op.create_table(
        "accounts",
        sa.Column("id", UUID, nullable=False),
        sa.Column("display_name", sa.String(length=120), nullable=False),
        sa.Column("birthday", sa.Date(), nullable=True),
        sa.Column("locale", sa.String(length=16), nullable=False),
        sa.Column("timezone", sa.String(length=64), nullable=False),
        sa.Column("disabled_at", sa.DateTime(timezone=True), nullable=True),
        *_timestamps(),
        sa.PrimaryKeyConstraint("id", name="pk_accounts"),
    )

    op.create_table(
        "account_emails",
        sa.Column("id", UUID, nullable=False),
        sa.Column("account_id", UUID, nullable=False),
        sa.Column("email", sa.String(length=320), nullable=False),
        sa.Column("verified_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("is_primary", sa.Boolean(), nullable=False),
        *_timestamps(),
        sa.PrimaryKeyConstraint("id", name="pk_account_emails"),
        sa.ForeignKeyConstraint(
            ["account_id"],
            ["accounts.id"],
            name="fk_account_emails_account_id_accounts",
            ondelete="CASCADE",
        ),
        sa.UniqueConstraint("email", name="uq_account_emails_email"),
        # Klein geschrieben abgelegt - sonst waeren "A@b.de" und "a@b.de"
        # zwei Adressen und die Eindeutigkeit haette ein Loch.
        sa.CheckConstraint("email = lower(email)", name="ck_account_emails_email_is_lowercase"),
    )

    op.create_table(
        "auth_identities",
        sa.Column("id", UUID, nullable=False),
        sa.Column("account_id", UUID, nullable=False),
        sa.Column("provider", sa.String(length=32), nullable=False),
        sa.Column("subject", sa.String(length=512), nullable=False),
        sa.Column("secret_hash", sa.String(length=255), nullable=True),
        sa.Column("last_used_at", sa.DateTime(timezone=True), nullable=True),
        *_timestamps(),
        sa.PrimaryKeyConstraint("id", name="pk_auth_identities"),
        sa.ForeignKeyConstraint(
            ["account_id"],
            ["accounts.id"],
            name="fk_auth_identities_account_id_accounts",
            ondelete="CASCADE",
        ),
        sa.UniqueConstraint("provider", "subject", name="uq_auth_identities_provider_subject"),
        sa.CheckConstraint(
            "provider IN ('MAGIC_LINK', 'PASSKEY', 'LOCAL_PASSWORD', 'OIDC')",
            name="ck_auth_identities_provider_is_known",
        ),
    )
    op.create_index("ix_auth_identities_account_id", "auth_identities", ["account_id"])

    op.create_table(
        "device_sessions",
        sa.Column("id", UUID, nullable=False),
        sa.Column("account_id", UUID, nullable=False),
        sa.Column("device_name", sa.String(length=120), nullable=False),
        sa.Column("platform", sa.String(length=32), nullable=False),
        # Nur Hashes. Wer die Datenbank liest, kann sich damit nicht anmelden.
        sa.Column("refresh_token_hash", sa.String(length=64), nullable=False),
        sa.Column("previous_refresh_token_hash", sa.String(length=64), nullable=True),
        sa.Column("access_token_hash", sa.String(length=64), nullable=True),
        sa.Column("access_expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column("last_used_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id", name="pk_device_sessions"),
        sa.ForeignKeyConstraint(
            ["account_id"],
            ["accounts.id"],
            name="fk_device_sessions_account_id_accounts",
            ondelete="CASCADE",
        ),
        sa.UniqueConstraint("refresh_token_hash", name="uq_device_sessions_refresh_token_hash"),
    )
    op.create_index(
        "ix_device_sessions_access_token_hash", "device_sessions", ["access_token_hash"]
    )
    op.create_index("ix_device_sessions_account_id", "device_sessions", ["account_id"])

    op.create_table(
        "spaces",
        sa.Column("id", UUID, nullable=False),
        *_timestamps(),
        sa.PrimaryKeyConstraint("id", name="pk_spaces"),
    )

    op.create_table(
        "memberships",
        sa.Column("id", UUID, nullable=False),
        sa.Column("space_id", UUID, nullable=False),
        sa.Column("account_id", UUID, nullable=False),
        sa.Column("role", sa.String(length=16), nullable=False),
        sa.Column("status", sa.String(length=16), nullable=False),
        sa.Column("joined_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("ended_at", sa.DateTime(timezone=True), nullable=True),
        *_timestamps(),
        sa.PrimaryKeyConstraint("id", name="pk_memberships"),
        sa.ForeignKeyConstraint(
            ["space_id"],
            ["spaces.id"],
            name="fk_memberships_space_id_spaces",
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["account_id"],
            ["accounts.id"],
            name="fk_memberships_account_id_accounts",
            ondelete="CASCADE",
        ),
        # Ein Account ist je Space hoechstens einmal Mitglied. Zwei Zeilen
        # waeren zwei Wahrheiten darueber, ob jemand Zugriff hat.
        sa.UniqueConstraint("space_id", "account_id", name="uq_memberships_space_id_account_id"),
        sa.CheckConstraint(
            "status IN ('ACTIVE', 'LEFT', 'REMOVED')",
            name="ck_memberships_status_is_known",
        ),
        sa.CheckConstraint("role IN ('PARTNER')", name="ck_memberships_role_is_known"),
    )
    # Der Guard fragt bei jeder Anfrage nach genau dieser Kombination.
    op.create_index(
        "ix_memberships_account_id_space_id_status",
        "memberships",
        ["account_id", "space_id", "status"],
    )

    op.create_table(
        "space_profiles",
        sa.Column("id", UUID, nullable=False),
        sa.Column("space_id", UUID, nullable=False),
        sa.Column("relationship_started_on", sa.Date(), nullable=True),
        sa.Column("show_relationship_duration", sa.Boolean(), nullable=False),
        sa.Column("duration_display_mode", sa.String(length=16), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        *_timestamps(),
        sa.PrimaryKeyConstraint("id", name="pk_space_profiles"),
        sa.ForeignKeyConstraint(
            ["space_id"],
            ["spaces.id"],
            name="fk_space_profiles_space_id_spaces",
            ondelete="CASCADE",
        ),
        sa.UniqueConstraint("space_id", name="uq_space_profiles_space_id"),
        sa.CheckConstraint(
            "duration_display_mode IN ('YEARS_MONTHS', 'DAYS')",
            name="ck_space_profiles_duration_display_mode_is_known",
        ),
    )


def downgrade() -> None:
    op.drop_table("space_profiles")
    op.drop_index("ix_memberships_account_id_space_id_status", table_name="memberships")
    op.drop_table("memberships")
    op.drop_table("spaces")
    op.drop_index("ix_device_sessions_account_id", table_name="device_sessions")
    op.drop_index("ix_device_sessions_access_token_hash", table_name="device_sessions")
    op.drop_table("device_sessions")
    op.drop_index("ix_auth_identities_account_id", table_name="auth_identities")
    op.drop_table("auth_identities")
    op.drop_table("account_emails")
    op.drop_table("accounts")
