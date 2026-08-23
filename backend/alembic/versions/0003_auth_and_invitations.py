"""auth and invitations

Einladungen und die Zaehlung wiederholter Versuche.

Constraint-Namen stehen hier NACKT - die Konvention aus db/base.py setzt
das Praefix davor. Siehe Kopf von 0002.

Revision ID: 0003
Revises: 0002
Create Date: 2026-08-23
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "0003"
down_revision = "0002"
branch_labels = None
depends_on = None

UUID = postgresql.UUID(as_uuid=True)


def upgrade() -> None:
    op.create_table(
        "invitations",
        sa.Column("id", UUID, nullable=False),
        sa.Column("space_id", UUID, nullable=False),
        sa.Column("created_by", UUID, nullable=False),
        # Nur der Hash. Wer die Datenbank liest, kann keinem fremden Space
        # beitreten.
        sa.Column("token_hash", sa.String(length=64), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("accepted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("accepted_by", UUID, nullable=True),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
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
        sa.PrimaryKeyConstraint("id", name="pk_invitations"),
        sa.ForeignKeyConstraint(
            ["space_id"],
            ["spaces.id"],
            name="fk_invitations_space_id_spaces",
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["created_by"],
            ["accounts.id"],
            name="fk_invitations_created_by_accounts",
            ondelete="CASCADE",
        ),
        # SET NULL statt CASCADE: verschwindet der beigetretene Account,
        # soll die Einladung nicht mitgeloescht werden - sie ist der Beleg,
        # dass jemand hereingekommen ist.
        sa.ForeignKeyConstraint(
            ["accepted_by"],
            ["accounts.id"],
            name="fk_invitations_accepted_by_accounts",
            ondelete="SET NULL",
        ),
        sa.UniqueConstraint("token_hash", name="uq_invitations_token_hash"),
    )
    op.create_index("ix_invitations_space_id", "invitations", ["space_id"])

    op.create_table(
        "rate_limit_events",
        sa.Column("id", UUID, nullable=False),
        sa.Column("action", sa.String(length=32), nullable=False),
        # Der Schluessel ist oft eine E-Mail-Adresse. Gehasht, weil "wer
        # wann einen Anmeldeversuch hatte" mehr Wissen waere, als die
        # Begrenzung braucht.
        sa.Column("key_hash", sa.String(length=64), nullable=False),
        sa.Column(
            "occurred_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id", name="pk_rate_limit_events"),
    )
    op.create_index(
        "ix_rate_limit_events_action_key_hash_occurred_at",
        "rate_limit_events",
        ["action", "key_hash", "occurred_at"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_rate_limit_events_action_key_hash_occurred_at",
        table_name="rate_limit_events",
    )
    op.drop_table("rate_limit_events")
    op.drop_index("ix_invitations_space_id", table_name="invitations")
    op.drop_table("invitations")
