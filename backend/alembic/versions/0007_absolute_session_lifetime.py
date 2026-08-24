"""Absolute device session lifetime

Revision ID: 0007
Revises: 0006
Create Date: 2026-08-24
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "0007"
down_revision = "0006"
branch_labels = None
depends_on = None

# Muss zu auth.tokens.SESSION_ABSOLUTE_LIFETIME passen. Bewusst als
# Literal: eine Migration beschreibt einen Zeitpunkt der Vergangenheit und
# darf sich nicht mitaendern, wenn die Konstante spaeter angepasst wird.
ABSOLUTE_LIFETIME = "180 days"


def upgrade() -> None:
    op.add_column(
        "device_sessions",
        sa.Column("absolute_expires_at", sa.DateTime(timezone=True), nullable=True),
    )

    # Bestehende Sitzungen bekommen ihre Grenze ab der tatsaechlichen
    # Anmeldung. GREATEST verhindert dabei, dass das Upgrade eine Sitzung
    # frueher beendet, als dem Client bereits als `refreshExpiresAt`
    # zugesagt wurde: eine lange laufende Sitzung wird nicht rueckwirkend
    # gekappt, erhaelt aber trotzdem eine feste Obergrenze.
    op.execute(
        sa.text(
            f"""
            UPDATE device_sessions
               SET absolute_expires_at =
                   GREATEST(created_at + INTERVAL '{ABSOLUTE_LIFETIME}', expires_at)
             WHERE absolute_expires_at IS NULL
            """
        )
    )

    op.alter_column("device_sessions", "absolute_expires_at", nullable=False)


def downgrade() -> None:
    # Zurueck bleibt allein das gleitende Fenster. Die Sitzungsdauer ist
    # danach wieder nach oben offen.
    op.drop_column("device_sessions", "absolute_expires_at")
