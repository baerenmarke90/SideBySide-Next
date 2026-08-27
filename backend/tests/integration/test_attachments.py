"""PostgreSQL/HTTP acceptance tests for the first media slice.

Schwerpunkte: the Statusautomat, the Strippen after M2-D14, the
Owner boundary and fail-closed behavior for everything that is not on the
Allowlist is stored.
"""

from __future__ import annotations

import io
from datetime import timedelta
from typing import Any
from uuid import uuid4

import pytest
from PIL import Image
from sqlalchemy import select
from sqlalchemy.orm import Session

from sidebyside.attachments import cleanup, service
from sidebyside.attachments.models import Attachment, AttachmentStatus
from sidebyside.core.clock import now
from sidebyside.media import build_storage_key, get_media_store
from sidebyside.relationship import service as relationship_service
from tests.conftest import auth, make_account, make_space, requires_database, sign_in

pytestmark = [pytest.mark.integration, requires_database]

MANUFACTURER = "GeheimKamera GmbH"
COMMENT = "privater Kommentar"


def path(space_id: object) -> str:
    return f"/api/v1/spaces/{space_id}/attachments"


def image_with_metadata(*, size: tuple[int, int] = (64, 48), format: str = "JPEG") -> bytes:
    img = Image.new("RGB", size, (200, 100, 50))
    exif = Image.Exif()
    exif[0x9003] = "2025:06:13 21:15:00"
    exif[0x0112] = 6
    exif[0x010F] = MANUFACTURER
    exif[0x9286] = COMMENT
    exif[0x8825] = {1: "N", 2: (52.0, 31.0, 0.0), 3: "E", 4: (13.0, 24.0, 0.0)}
    buffer = io.BytesIO()
    if format == "JPEG":
        img.save(buffer, format, exif=exif.tobytes())
    else:
        img.save(buffer, format)
    return buffer.getvalue()


def upload_body(**overrides: Any) -> dict[str, Any]:
    return {
        "mediaType": "IMAGE",
        "originalName": "urlaub.jpg",
        "expectedMimeType": "image/jpeg",
        "expectedSize": 4096,
        **overrides,
    }


@pytest.fixture
def couple(session: Session):  # type: ignore[no-untyped-def]
    anna = make_account(session, "Anna")
    ben = make_account(session, "Ben")
    space = make_space(session, anna)
    relationship_service.add_member(session, space.id, ben)
    session.flush()
    return {
        "anna": anna,
        "ben": ben,
        "space": space,
        "token_a": sign_in(session, anna),
        "token_b": sign_in(session, ben),
    }


def upload_hoch(client, couple, *, data: bytes | None = None, **overrides):  # type: ignore[no-untyped-def]
    "Sign in, uebertragen, finalisieren; the volle Clientpfad."
    content = image_with_metadata() if data is None else data
    angelegt = client.post(
        path(couple["space"].id),
        json=upload_body(expectedSize=len(content), **overrides),
        headers=auth(couple["token_a"]),
    )
    if angelegt.status_code != 201:
        return angelegt, None
    attachment_id = angelegt.json()["attachment"]["id"]
    upload_response = client.put(
        f"{path(couple['space'].id)}/{attachment_id}/content",
        content=content,
        headers=auth(couple["token_a"]),
    )
    assert upload_response.status_code == 204, upload_response.text
    finalized = client.post(
        f"{path(couple['space'].id)}/{attachment_id}/finalize",
        json={},
        headers=auth(couple["token_a"]),
    )
    return finalized, attachment_id


def verarbeite(session: Session, attachment_id: str) -> Attachment:
    service.validate(session, __import__("uuid").UUID(attachment_id))
    session.flush()
    return session.execute(
        select(Attachment).where(Attachment.id == __import__("uuid").UUID(attachment_id))
    ).scalar_one()


class TestLifecycle:
    def test_upload_is_validiert_stripped_and_ready(self, client, couple, session) -> None:  # type: ignore[no-untyped-def]
        response, attachment_id = upload_hoch(client, couple)
        assert response.status_code == 202
        assert response.json()["status"] == "PROCESSING"

        attachment = verarbeite(session, attachment_id)
        assert attachment.status == AttachmentStatus.READY.value
        assert attachment.mime_type == "image/jpeg"
        assert attachment.width == 64
        assert attachment.height == 48
        assert attachment.ready_at is not None
        assert attachment.has_thumbnail is True

        stored = get_media_store().open(
            build_storage_key(attachment.space_id, attachment.id, "original")
        )
        with stored as file:
            raw = file.read()
        assert MANUFACTURER.encode() not in raw
        assert COMMENT.encode() not in raw

        detail = client.get(
            f"{path(couple['space'].id)}/{attachment_id}",
            headers=auth(couple["token_a"]),
        )
        assert detail.status_code == 200
        assert detail.json()["status"] == "READY"
        assert detail.json()["hasThumbnail"] is True

    def test_allowlist_aus_exif_remains_protected_payload(self, client, couple, session) -> None:  # type: ignore[no-untyped-def]
        _, attachment_id = upload_hoch(client, couple)
        attachment = verarbeite(session, attachment_id)

        assert attachment.payload.captured_at is not None
        assert attachment.payload.orientation == 6
        # No Plaintext field in the Table; the Capture timestamp is no
        # sortierbares Metadatum geworden.
        assert "captured_at" not in Attachment.__table__.c
        assert "original_name" not in Attachment.__table__.c

    def test_status_is_public_projiziert(self, client, couple) -> None:  # type: ignore[no-untyped-def]
        angelegt = client.post(
            path(couple["space"].id), json=upload_body(), headers=auth(couple["token_a"])
        )
        assert angelegt.status_code == 201
        assert angelegt.json()["attachment"]["status"] == "PENDING"
        assert angelegt.json()["method"] == "STREAM"
        # No Storage-Interna after outside.
        for forbidden in ("storageKey", "bucket", "provider", "filesystemPath", "privacyClass"):
            assert forbidden not in angelegt.text

    def test_finalize_is_idempotent(self, client, couple, session) -> None:  # type: ignore[no-untyped-def]
        _, attachment_id = upload_hoch(client, couple)
        second_time = client.post(
            f"{path(couple['space'].id)}/{attachment_id}/finalize",
            json={},
            headers=auth(couple["token_a"]),
        )
        assert second_time.status_code == 202

        from sidebyside.jobs.models import Job

        jobs = (
            session.execute(select(Job).where(Job.kind == service.ATTACHMENT_VALIDATION))
            .scalars()
            .all()
        )
        assert len(jobs) == 1


class TestFailClosed:
    def test_video_is_until_zum_video_slice_rejected(self, client, couple) -> None:  # type: ignore[no-untyped-def]
        "M2-D23: the Contract erlaubt it, this Lieferstand not."
        response = client.post(
            path(couple["space"].id),
            json=upload_body(mediaType="VIDEO", expectedMimeType="video/mp4"),
            headers=auth(couple["token_a"]),
        )
        assert response.status_code == 415
        assert response.json()["code"] == "ATTACHMENT_TYPE_NOT_ALLOWED"

    def test_unknown_type_is_rejected(self, client, couple) -> None:  # type: ignore[no-untyped-def]
        for mime in ("image/gif", "application/pdf", "image/svg+xml", "video/x-matroska"):
            response = client.post(
                path(couple["space"].id),
                json=upload_body(expectedMimeType=mime),
                headers=auth(couple["token_a"]),
            )
            assert response.status_code == 415, mime

    def test_declared_oversize_is_rejected(self, client, couple) -> None:  # type: ignore[no-untyped-def]
        response = client.post(
            path(couple["space"].id),
            json=upload_body(expectedSize=26 * 1024 * 1024),
            headers=auth(couple["token_a"]),
        )
        assert response.status_code == 413
        assert response.json()["code"] == "ATTACHMENT_TOO_LARGE"

    def test_disguised_content_reaches_no_ready(self, client, couple, session) -> None:  # type: ignore[no-untyped-def]
        "The declared Typ counts not; the magic bytes decide."
        _, attachment_id = upload_hoch(client, couple, data=b"GIF89a" + b"\x00" * 64)
        attachment = verarbeite(session, attachment_id)
        assert attachment.status == AttachmentStatus.FAILED.value
        assert attachment.failure_code is not None
        assert attachment.ready_at is None

    def test_png_als_jpeg_angekuendigt_scheitert(self, client, couple, session) -> None:  # type: ignore[no-untyped-def]
        buffer = io.BytesIO()
        Image.new("RGB", (16, 16)).save(buffer, "PNG")
        _, attachment_id = upload_hoch(client, couple, data=buffer.getvalue())
        attachment = verarbeite(session, attachment_id)
        assert attachment.status == AttachmentStatus.FAILED.value

    def test_truncated_file_scheitert(self, client, couple, session) -> None:  # type: ignore[no-untyped-def]
        full = image_with_metadata()
        _, attachment_id = upload_hoch(client, couple, data=full[: len(full) // 2])
        attachment = verarbeite(session, attachment_id)
        assert attachment.status == AttachmentStatus.FAILED.value

    def test_a_failed_attachment_is_not_readable(self, client, couple, session) -> None:  # type: ignore[no-untyped-def]
        _, attachment_id = upload_hoch(client, couple, data=b"nicht wirklich ein bild")
        verarbeite(session, attachment_id)
        response = client.get(
            f"{path(couple['space'].id)}/{attachment_id}/content",
            headers=auth(couple["token_a"]),
        )
        assert response.status_code == 409
        assert response.json()["code"] == "ATTACHMENT_NOT_READY"


class TestOwnerBoundary:
    def test_partner_sees_foreign_attachment_not(self, client, couple, session) -> None:  # type: ignore[no-untyped-def]
        _, attachment_id = upload_hoch(client, couple)
        verarbeite(session, attachment_id)

        for response in (
            client.get(
                f"{path(couple['space'].id)}/{attachment_id}", headers=auth(couple["token_b"])
            ),
            client.get(
                f"{path(couple['space'].id)}/{attachment_id}/content",
                headers=auth(couple["token_b"]),
            ),
            client.post(
                f"{path(couple['space'].id)}/{attachment_id}/read-access",
                json={"parentType": "NONE"},
                headers=auth(couple["token_b"]),
            ),
        ):
            assert response.status_code == 404

    def test_anonymous_access_is_rejected(self, client, couple, session) -> None:  # type: ignore[no-untyped-def]
        _, attachment_id = upload_hoch(client, couple)
        verarbeite(session, attachment_id)
        assert client.get(f"{path(couple['space'].id)}/{attachment_id}/content").status_code == 401

    def test_guessed_storage_key_helps_not(self, client, couple, session) -> None:  # type: ignore[no-untyped-def]
        "no route accepts a storage key."
        _, attachment_id = upload_hoch(client, couple)
        attachment = verarbeite(session, attachment_id)
        key = build_storage_key(attachment.space_id, attachment.id, "original")
        response = client.get(f"/api/v1/{key}", headers=auth(couple["token_a"]))
        assert response.status_code == 404

    def test_owner_reads_own_ungebundenen_upload(self, client, couple, session) -> None:  # type: ignore[no-untyped-def]
        """M2-D24."""
        _, attachment_id = upload_hoch(client, couple)
        verarbeite(session, attachment_id)

        descriptor = client.post(
            f"{path(couple['space'].id)}/{attachment_id}/read-access",
            json={"parentType": "NONE"},
            headers=auth(couple["token_a"]),
        )
        assert descriptor.status_code == 200
        assert descriptor.json()["method"] == "STREAM"

        content = client.get(descriptor.json()["url"], headers=auth(couple["token_a"]))
        assert content.status_code == 200
        assert content.headers["content-type"].startswith("image/jpeg")
        assert MANUFACTURER.encode() not in content.content

        thumbnail = client.get(
            f"{path(couple['space'].id)}/{attachment_id}/content?variant=thumbnail",
            headers=auth(couple["token_a"]),
        )
        assert thumbnail.status_code == 200

    def test_parent_reference_verleiht_no_access(self, client, couple, session) -> None:  # type: ignore[no-untyped-def]
        "while nothing is bound, there is no parent that grants access."
        _, attachment_id = upload_hoch(client, couple)
        verarbeite(session, attachment_id)
        response = client.post(
            f"{path(couple['space'].id)}/{attachment_id}/read-access",
            json={"parentType": "MEMORY", "parentId": str(uuid4())},
            headers=auth(couple["token_a"]),
        )
        assert response.status_code == 404

    def test_expired_binding_window_sperrt_the_access(self, client, couple, session) -> None:  # type: ignore[no-untyped-def]
        _, attachment_id = upload_hoch(client, couple)
        attachment = verarbeite(session, attachment_id)
        attachment.ready_at = now() - service.BINDING_WINDOW - timedelta(minutes=1)
        session.flush()

        response = client.get(
            f"{path(couple['space'].id)}/{attachment_id}/content",
            headers=auth(couple["token_a"]),
        )
        assert response.status_code == 404


class TestDeletionAndCleanup:
    def test_delete_macht_sofort_unsichtbar(self, client, couple, session) -> None:  # type: ignore[no-untyped-def]
        _, attachment_id = upload_hoch(client, couple)
        attachment = verarbeite(session, attachment_id)

        deleted = client.delete(
            f"{path(couple['space'].id)}/{attachment_id}",
            headers={**auth(couple["token_a"]), "If-Match": f'"{attachment.version}"'},
        )
        assert deleted.status_code == 204

        assert (
            client.get(
                f"{path(couple['space'].id)}/{attachment_id}", headers=auth(couple["token_a"])
            ).status_code
            == 404
        )

    def test_delete_verlangt_aktuelle_version(self, client, couple, session) -> None:  # type: ignore[no-untyped-def]
        _, attachment_id = upload_hoch(client, couple)
        attachment = verarbeite(session, attachment_id)
        response = client.delete(
            f"{path(couple['space'].id)}/{attachment_id}",
            headers={**auth(couple["token_a"]), "If-Match": f'"{attachment.version + 5}"'},
        )
        assert response.status_code == 409

    def test_cleanup_entfernt_original_and_thumbnail(self, client, couple, session) -> None:  # type: ignore[no-untyped-def]
        _, attachment_id = upload_hoch(client, couple)
        attachment = verarbeite(session, attachment_id)
        original = build_storage_key(attachment.space_id, attachment.id, "original")
        thumb = build_storage_key(attachment.space_id, attachment.id, "thumbnail")
        store = get_media_store()
        assert store.exists(original) and store.exists(thumb)

        service.mark_for_deletion(session, attachment)
        session.flush()
        cleanup.run_media_cleanup(session, {})
        session.flush()

        assert not store.exists(original)
        assert not store.exists(thumb)

    def test_ungebundenes_ready_continues_after_dem_window_ab(
        self, client, couple, session
    ) -> None:  # type: ignore[no-untyped-def]
        """M2-D20."""
        _, attachment_id = upload_hoch(client, couple)
        attachment = verarbeite(session, attachment_id)
        attachment.ready_at = now() - service.BINDING_WINDOW - timedelta(minutes=1)
        session.flush()

        cleanup.run_media_cleanup(session, {})
        session.flush()

        assert (
            client.get(
                f"{path(couple['space'].id)}/{attachment_id}", headers=auth(couple["token_a"])
            ).status_code
            == 404
        )

    def test_angefangener_upload_continues_after_24h_ab(self, client, couple, session) -> None:  # type: ignore[no-untyped-def]
        """M2-D12."""
        angelegt = client.post(
            path(couple["space"].id), json=upload_body(), headers=auth(couple["token_a"])
        )
        attachment_id = angelegt.json()["attachment"]["id"]
        row = session.execute(
            select(Attachment).where(Attachment.id == __import__("uuid").UUID(attachment_id))
        ).scalar_one()
        row.created_at = now() - cleanup.UPLOAD_RETENTION - timedelta(minutes=1)
        session.flush()

        cleanup.run_media_cleanup(session, {})
        session.flush()

        assert (
            client.get(
                f"{path(couple['space'].id)}/{attachment_id}", headers=auth(couple["token_a"])
            ).status_code
            == 404
        )

    def test_fresh_upload_is_not_cleaned_up(self, client, couple, session) -> None:  # type: ignore[no-untyped-def]
        angelegt = client.post(
            path(couple["space"].id), json=upload_body(), headers=auth(couple["token_a"])
        )
        attachment_id = angelegt.json()["attachment"]["id"]
        cleanup.run_media_cleanup(session, {})
        session.flush()
        assert (
            client.get(
                f"{path(couple['space'].id)}/{attachment_id}", headers=auth(couple["token_a"])
            ).status_code
            == 200
        )
