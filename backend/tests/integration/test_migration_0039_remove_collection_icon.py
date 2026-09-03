"""Test for Alembic migration 0039 removing legacy icon from collection payloads."""

from __future__ import annotations

import json
from uuid import uuid4

import pytest
import sqlalchemy as sa
from sqlalchemy.orm import Session

from sidebyside.collections.models import Collection
from sidebyside.domain.payload import CRYPTO_VERSION_PLAINTEXT
from sidebyside.private_collections.models import PrivateCollection
from tests.conftest import make_account, make_space, requires_database


@pytest.mark.integration
@requires_database
def test_migration_0039_removes_icon_from_plaintext_payloads(session: Session) -> None:
    # 1. Setup space and account
    account = make_account(session, "Test User")
    space = make_space(session, account)
    session.flush()

    col_id = uuid4()
    pcol_id = uuid4()

    # 2. Insert raw collections with legacy icon field in payload
    session.execute(
        sa.text(
            """
            INSERT INTO collections (
                id, space_id, owner_id, privacy_class,
                crypto_version, payload, version, created_at, updated_at
            )
            VALUES (
                :id, :space_id, :owner_id, 'SPACE_SHARED',
                :crypto_version, CAST(:payload AS jsonb), 1, now(), now()
            )
            """
        ),
        {
            "id": col_id,
            "space_id": space.id,
            "owner_id": account.id,
            "crypto_version": CRYPTO_VERSION_PLAINTEXT,
            "payload": json.dumps({"title": "Shared Vacation", "icon": "plane"}),
        },
    )

    session.execute(
        sa.text(
            """
            INSERT INTO private_collections (
                id, space_id, owner_id, privacy_class,
                crypto_version, payload, version, created_at, updated_at
            )
            VALUES (
                :id, :space_id, :owner_id, 'OWNER_ONLY',
                :crypto_version, CAST(:payload AS jsonb), 1, now(), now()
            )
            """
        ),
        {
            "id": pcol_id,
            "space_id": space.id,
            "owner_id": account.id,
            "crypto_version": CRYPTO_VERSION_PLAINTEXT,
            "payload": json.dumps({"title": "Secret Ideas", "icon": "gift"}),
        },
    )
    session.flush()

    # Verify legacy payload has 'icon'
    raw_col = session.execute(
        sa.text("SELECT payload FROM collections WHERE id = :id"), {"id": col_id}
    ).scalar_one()
    assert "icon" in raw_col
    assert raw_col["icon"] == "plane"

    # 3. Execute upgrade logic
    session.execute(
        sa.text(
            """
            UPDATE collections
            SET payload = payload - 'icon'
            WHERE crypto_version = 0 AND payload ? 'icon';
            """
        )
    )
    session.execute(
        sa.text(
            """
            UPDATE private_collections
            SET payload = payload - 'icon'
            WHERE crypto_version = 0 AND payload ? 'icon';
            """
        )
    )
    session.flush()

    # 4. Verify in DB that 'icon' key is removed
    updated_col_payload = session.execute(
        sa.text("SELECT payload FROM collections WHERE id = :id"), {"id": col_id}
    ).scalar_one()
    assert "icon" not in updated_col_payload
    assert updated_col_payload["title"] == "Shared Vacation"

    updated_pcol_payload = session.execute(
        sa.text("SELECT payload FROM private_collections WHERE id = :id"), {"id": pcol_id}
    ).scalar_one()
    assert "icon" not in updated_pcol_payload
    assert updated_pcol_payload["title"] == "Secret Ideas"

    # 5. Verify ORM deserialization with strict ProtectedPayload(extra="forbid")
    session.expire_all()
    orm_col = session.get(Collection, col_id)
    assert orm_col is not None
    assert orm_col.payload.title == "Shared Vacation"

    orm_pcol = session.get(PrivateCollection, pcol_id)
    assert orm_pcol is not None
    assert orm_pcol.payload.title == "Secret Ideas"

    # 6. Test Downgrade preserves collection data and does not destroy or make unreadable
    session.execute(
        sa.text(
            """
            UPDATE collections
            SET payload = jsonb_set(payload, '{icon}', 'null'::jsonb, true)
            WHERE crypto_version = 0 AND NOT (payload ? 'icon');
            """
        )
    )
    session.execute(
        sa.text(
            """
            UPDATE private_collections
            SET payload = jsonb_set(payload, '{icon}', 'null'::jsonb, true)
            WHERE crypto_version = 0 AND NOT (payload ? 'icon');
            """
        )
    )
    session.flush()

    down_col = session.execute(
        sa.text("SELECT payload FROM collections WHERE id = :id"), {"id": col_id}
    ).scalar_one()
    assert "icon" in down_col
    assert down_col["icon"] is None
    assert down_col["title"] == "Shared Vacation"
