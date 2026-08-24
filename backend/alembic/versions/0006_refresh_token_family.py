"""Refresh token family replay history

Revision ID: 0006
Revises: 0005
Create Date: 2026-08-24
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql
from uuid6 import uuid7

revision = "0006"
down_revision = "0005"
branch_labels = None
depends_on = None

UUID = postgresql.UUID(as_uuid=True)


def upgrade() -> None:
    op.create_table(
        "consumed_refresh_tokens",
        sa.Column("id", UUID, nullable=False),
        sa.Column("device_session_id", UUID, nullable=False),
        # Nur der Hash. Diese Tabelle darf keine zweite Quelle fuer
        # Anmeldenachweise werden.
        sa.Column("token_hash", sa.String(length=64), nullable=False),
        sa.Column(
            "consumed_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["device_session_id"],
            ["device_sessions.id"],
            name="fk_consumed_refresh_tokens_device_session_id_device_sessions",
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_consumed_refresh_tokens"),
        sa.UniqueConstraint("token_hash", name="uq_consumed_refresh_tokens_token_hash"),
    )
    op.create_index(
        "ix_consumed_refresh_tokens_device_session_id",
        "consumed_refresh_tokens",
        ["device_session_id"],
    )

    # Die bisher einzige gemerkte Vorgaengergeneration wird uebernommen,
    # damit ein Upgrade die schon erreichte Replay-Erkennung nicht kurz
    # verliert. Die Schleife laeuft in Python, weil die ID ein UUIDv7 sein
    # muss; PostgreSQL 17 bringt dafuer keine eigene Funktion mit. Es gibt
    # hoechstens eine Zeile je Geraetesitzung.
    verbindung = op.get_bind()
    bestand = verbindung.execute(
        sa.text(
            """
            SELECT id, previous_refresh_token_hash
              FROM device_sessions
             WHERE previous_refresh_token_hash IS NOT NULL
            """
        )
    ).fetchall()
    for sitzung_id, token_hash in bestand:
        verbindung.execute(
            sa.text(
                """
                INSERT INTO consumed_refresh_tokens
                    (id, device_session_id, token_hash, consumed_at)
                VALUES (:id, :device_session_id, :token_hash, CURRENT_TIMESTAMP)
                """
            ),
            {
                "id": uuid7(),
                "device_session_id": sitzung_id,
                "token_hash": token_hash,
            },
        )

    op.drop_column("device_sessions", "previous_refresh_token_hash")


def downgrade() -> None:
    op.add_column(
        "device_sessions",
        sa.Column("previous_refresh_token_hash", sa.String(length=64), nullable=True),
    )

    # Zurueck bleibt nur das alte Ein-Slot-Fenster: die jeweils juengste
    # verbrauchte Generation. Aeltere Generationen sind danach nicht mehr
    # zuordenbar - genau die Luecke, die dieses Upgrade schliesst.
    op.execute(
        sa.text(
            """
            UPDATE device_sessions AS ziel
               SET previous_refresh_token_hash = juengste.token_hash
              FROM (
                    SELECT DISTINCT ON (device_session_id)
                           device_session_id, token_hash
                      FROM consumed_refresh_tokens
                     ORDER BY device_session_id, consumed_at DESC, id DESC
                   ) AS juengste
             WHERE ziel.id = juengste.device_session_id
            """
        )
    )

    op.drop_index("ix_consumed_refresh_tokens_device_session_id", "consumed_refresh_tokens")
    op.drop_table("consumed_refresh_tokens")
