"""PostgreSQL/HTTP evidence for Transfer Bundle authorization and validation."""

from __future__ import annotations

import hashlib
import io
import json
from datetime import UTC, datetime
from uuid import uuid4
from zipfile import ZIP_DEFLATED, ZipFile

import pytest
from sqlalchemy.orm import Session

from sidebyside.authorization import AuthorizationContext
from sidebyside.identity.models import AccountEmail
from sidebyside.private_notes import service as private_note_service
from sidebyside.relationship import service as relationship_service
from sidebyside.transfer import jobs, service
from sidebyside.transfer.models import ImportStatus, TransferScope
from tests.conftest import auth, make_account, make_space, requires_database, sign_in

pytestmark = [pytest.mark.integration, requires_database]


def _verified_email(session: Session, account, address: str) -> None:  # type: ignore[no-untyped-def]
    session.add(
        AccountEmail(
            account_id=account.id,
            email=address,
            verified_at=datetime(2026, 8, 31, 10, 0, tzinfo=UTC),
            is_primary=True,
        )
    )
    session.flush()


def _minimal_bundle(source_id: str, email: str) -> io.BytesIO:
    accounts = (
        json.dumps(
            {
                "members": [
                    {
                        "sourceId": source_id,
                        "displayName": "Portable member",
                        "birthday": None,
                        "locale": "de-DE",
                        "timezone": "Europe/Berlin",
                        "verifiedEmail": email,
                    }
                ]
            },
            sort_keys=True,
            separators=(",", ":"),
        )
        + "\n"
    ).encode()
    manifest = {
        "formatVersion": 1,
        "exportedAt": "2026-08-31T10:00:00+00:00",
        "applicationVersion": "0.1.0",
        "scope": "PERSONAL",
        "sourceSpaceId": str(uuid4()),
        "personalOwnerSourceId": source_id,
        "checksums": {"accounts.json": hashlib.sha256(accounts).hexdigest()},
    }
    output = io.BytesIO()
    with ZipFile(output, "w", compression=ZIP_DEFLATED) as archive:
        archive.writestr("accounts.json", accounts)
        archive.writestr(
            "manifest.json",
            (json.dumps(manifest, sort_keys=True, separators=(",", ":")) + "\n").encode(),
        )
    output.seek(0)
    return output


def test_export_descriptor_is_creator_bound(client, session: Session) -> None:  # type: ignore[no-untyped-def]
    anna = make_account(session, "Anna")
    ben = make_account(session, "Ben")
    space = make_space(session, anna)
    relationship_service.add_member(session, space.id, ben)
    anna_token = sign_in(session, anna)
    ben_token = sign_in(session, ben)

    created = client.post(
        f"/api/v1/spaces/{space.id}/transfer/exports",
        json={"scope": "PERSONAL"},
        headers=auth(anna_token),
    )
    assert created.status_code == 202, created.text
    export_id = created.json()["id"]
    assert created.json()["status"] == "QUEUED"
    assert created.json()["scope"] == "PERSONAL"
    assert created.headers["cache-control"] == "private, no-store"

    own = client.get(
        f"/api/v1/spaces/{space.id}/transfer/exports/{export_id}",
        headers=auth(anna_token),
    )
    assert own.status_code == 200

    partner = client.get(
        f"/api/v1/spaces/{space.id}/transfer/exports/{export_id}",
        headers=auth(ben_token),
    )
    assert partner.status_code == 404


def test_shared_export_excludes_owner_only_and_personal_keeps_only_requester(
    session: Session,
) -> None:
    anna = make_account(session, "Anna")
    ben = make_account(session, "Ben")
    space = make_space(session, anna)
    relationship_service.add_member(session, space.id, ben)
    anna_context = AuthorizationContext(account_id=anna.id, space_id=space.id)
    ben_context = AuthorizationContext(account_id=ben.id, space_id=space.id)

    private_note_service.create_note(
        session,
        anna_context,
        title="Anna secret",
        body="Only Anna may export this.",
        pinned=False,
    )
    private_note_service.create_note(
        session,
        ben_context,
        title="Ben secret",
        body="Anna must never export this.",
        pinned=False,
    )

    with service.build_export_archive(session, anna_context, TransferScope.SHARED) as bundle:
        with ZipFile(bundle, "r") as archive:
            assert "private/notes.json" not in archive.namelist()

    with service.build_export_archive(session, anna_context, TransferScope.PERSONAL) as bundle:
        with ZipFile(bundle, "r") as archive:
            document = json.loads(archive.read("private/notes.json"))

    notes = next(group for group in document["tables"] if group["name"] == "private_notes")[
        "rows"
    ]
    assert len(notes) == 1
    assert notes[0]["ownerId"] == str(anna.id)
    assert notes[0]["payload"]["title"] == "Anna secret"


def test_personal_import_maps_requester_and_apply_is_idempotent(session: Session) -> None:
    target = make_account(session, "Target")
    _verified_email(session, target, "target@example.test")
    space = make_space(session, target)
    authorization = AuthorizationContext(account_id=target.id, space_id=space.id)
    source_id = str(uuid4())
    bundle = _minimal_bundle(source_id, "target@example.test")

    transfer = service.create_import(
        session,
        authorization,
        bundle,
        size=len(bundle.getvalue()),
    )
    session.flush()
    jobs.handle_validate_import(session, {"importId": str(transfer.id)})
    session.flush()

    assert transfer.status == ImportStatus.READY_TO_APPLY.value
    assert transfer.scope == TransferScope.PERSONAL.value
    assert transfer.member_mapping == {source_id: str(target.id)}
    assert transfer.summary == {
        "scope": "PERSONAL",
        "recordCounts": {},
        "mediaCount": 0,
        "sourceMemberCount": 1,
    }

    service.request_apply(session, authorization, str(transfer.id))
    session.flush()
    jobs.handle_apply_import(session, {"importId": str(transfer.id)})
    session.flush()

    assert transfer.status == ImportStatus.COMPLETED.value
    assert transfer.artifact_size == 0
    assert service.request_apply(session, authorization, str(transfer.id)).status == (
        ImportStatus.COMPLETED.value
    )


def test_personal_import_fails_when_owner_maps_to_other_member(session: Session) -> None:
    requester = make_account(session, "Requester")
    partner = make_account(session, "Partner")
    _verified_email(session, requester, "requester@example.test")
    _verified_email(session, partner, "partner@example.test")
    space = make_space(session, requester)
    relationship_service.add_member(session, space.id, partner)
    authorization = AuthorizationContext(account_id=requester.id, space_id=space.id)
    source_id = str(uuid4())
    bundle = _minimal_bundle(source_id, "partner@example.test")

    transfer = service.create_import(
        session,
        authorization,
        bundle,
        size=len(bundle.getvalue()),
    )
    session.flush()
    jobs.handle_validate_import(session, {"importId": str(transfer.id)})
    session.flush()

    assert transfer.status == ImportStatus.FAILED.value
    assert transfer.error_code == "TRANSFER_MEMBER_MAPPING_INVALID"
