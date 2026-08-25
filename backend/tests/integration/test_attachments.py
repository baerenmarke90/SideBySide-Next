"""PostgreSQL-/HTTP-Abnahme fuer den ersten Media-Slice.

Schwerpunkte: der Statusautomat, das Strippen nach M2-D14, die
Owner-Grenze und das fail-closed-Verhalten bei allem, was nicht auf der
Allowlist steht.
"""

from __future__ import annotations

import io
from datetime import timedelta
from pathlib import Path
from typing import Any
from uuid import uuid4

import pytest
from PIL import Image
from sqlalchemy import select
from sqlalchemy.orm import Session

from sidebyside.attachments import cleanup, service, videos
from sidebyside.attachments.models import Attachment, AttachmentStatus
from sidebyside.config import Settings
from sidebyside.core.clock import now
from sidebyside.media import build_storage_key, get_media_store
from sidebyside.relationship import service as relationship_service
from tests.conftest import auth, make_account, make_space, requires_database, sign_in

pytestmark = [pytest.mark.integration, requires_database]

HERSTELLER = "GeheimKamera GmbH"
KOMMENTAR = "privater Kommentar"


def path(space_id: object) -> str:
    return f"/api/v1/spaces/{space_id}/attachments"


def bild_mit_metadaten(*, groesse: tuple[int, int] = (64, 48), format: str = "JPEG") -> bytes:
    img = Image.new("RGB", groesse, (200, 100, 50))
    exif = Image.Exif()
    exif[0x9003] = "2025:06:13 21:15:00"
    exif[0x0112] = 6
    exif[0x010F] = HERSTELLER
    exif[0x9286] = KOMMENTAR
    exif[0x8825] = {1: "N", 2: (52.0, 31.0, 0.0), 3: "E", 4: (13.0, 24.0, 0.0)}
    puffer = io.BytesIO()
    if format == "JPEG":
        img.save(puffer, format, exif=exif.tobytes())
    else:
        img.save(puffer, format)
    return puffer.getvalue()


def poster() -> bytes:
    puffer = io.BytesIO()
    Image.new("RGB", (24, 16), (10, 20, 30)).save(puffer, "JPEG")
    return puffer.getvalue()


def upload_body(**overrides: Any) -> dict[str, Any]:
    return {
        "mediaType": "IMAGE",
        "originalName": "urlaub.jpg",
        "expectedMimeType": "image/jpeg",
        "expectedSize": 4096,
        **overrides,
    }


@pytest.fixture
def paar(session: Session):  # type: ignore[no-untyped-def]
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


def lade_hoch(client, paar, *, daten: bytes | None = None, **overrides):  # type: ignore[no-untyped-def]
    """Anmelden, uebertragen, finalisieren - der volle Clientpfad."""
    inhalt = bild_mit_metadaten() if daten is None else daten
    angelegt = client.post(
        path(paar["space"].id),
        json=upload_body(expectedSize=len(inhalt), **overrides),
        headers=auth(paar["token_a"]),
    )
    if angelegt.status_code != 201:
        return angelegt, None
    kennung = angelegt.json()["attachment"]["id"]
    uebertragen = client.put(
        f"{path(paar['space'].id)}/{kennung}/content",
        content=inhalt,
        headers=auth(paar["token_a"]),
    )
    assert uebertragen.status_code == 204, uebertragen.text
    finalisiert = client.post(
        f"{path(paar['space'].id)}/{kennung}/finalize",
        json={},
        headers=auth(paar["token_a"]),
    )
    return finalisiert, kennung


def verarbeite(session: Session, kennung: str) -> Attachment:
    service.validate(session, __import__("uuid").UUID(kennung))
    session.flush()
    return session.execute(
        select(Attachment).where(Attachment.id == __import__("uuid").UUID(kennung))
    ).scalar_one()


class TestLebenszyklus:
    def test_upload_wird_validiert_gestrippt_und_ready(self, client, paar, session) -> None:  # type: ignore[no-untyped-def]
        antwort, kennung = lade_hoch(client, paar)
        assert antwort.status_code == 202
        assert antwort.json()["status"] == "PROCESSING"

        attachment = verarbeite(session, kennung)
        assert attachment.status == AttachmentStatus.READY.value
        assert attachment.mime_type == "image/jpeg"
        assert attachment.width == 64
        assert attachment.height == 48
        assert attachment.ready_at is not None
        assert attachment.has_thumbnail is True

        gespeichert = get_media_store().open(
            build_storage_key(attachment.space_id, attachment.id, "original")
        )
        with gespeichert as datei:
            roh = datei.read()
        assert HERSTELLER.encode() not in roh
        assert KOMMENTAR.encode() not in roh

        detail = client.get(
            f"{path(paar['space'].id)}/{kennung}",
            headers=auth(paar["token_a"]),
        )
        assert detail.status_code == 200
        assert detail.json()["status"] == "READY"
        assert detail.json()["hasThumbnail"] is True

    def test_video_wird_sanitized_ready_mit_poster(self, client, paar, session, monkeypatch) -> None:  # type: ignore[no-untyped-def]
        original = b"untrusted-video-object"
        sanitized = b"server-sanitized-video"
        preview = poster()

        def fake_process(source: Path, target: Path, rule) -> videos.ProcessedVideo:  # type: ignore[no-untyped-def]
            assert source.read_bytes() == original
            assert rule.mime_type == "video/mp4"
            target.write_bytes(sanitized)
            return videos.ProcessedVideo(
                mime_type="video/mp4",
                width=1920,
                height=1080,
                duration_seconds=12,
                captured_at=None,
                orientation=1,
                size=len(sanitized),
                poster=preview,
            )

        monkeypatch.setattr(service, "get_settings", lambda: Settings(ffmpeg_enabled=True))
        monkeypatch.setattr(service.videos, "process", fake_process)

        antwort, kennung = lade_hoch(
            client,
            paar,
            daten=original,
            mediaType="VIDEO",
            originalName="clip.mp4",
            expectedMimeType="video/mp4",
        )
        assert antwort.status_code == 202

        attachment = verarbeite(session, kennung)
        assert attachment.status == AttachmentStatus.READY.value
        assert attachment.mime_type == "video/mp4"
        assert attachment.width == 1920
        assert attachment.height == 1080
        assert attachment.duration_seconds == 12
        assert attachment.has_thumbnail is True

        store = get_media_store()
        with store.open(build_storage_key(attachment.space_id, attachment.id, "original")) as file:
            assert file.read() == sanitized
        with store.open(build_storage_key(attachment.space_id, attachment.id, "thumbnail")) as file:
            assert file.read() == preview

    def test_allowlist_aus_exif_bleibt_protected_payload(self, client, paar, session) -> None:  # type: ignore[no-untyped-def]
        _, kennung = lade_hoch(client, paar)
        attachment = verarbeite(session, kennung)

        assert attachment.payload.captured_at is not None
        assert attachment.payload.orientation == 6
        # Kein Klartextfeld in der Tabelle - der Aufnahmezeitpunkt ist kein
        # sortierbares Metadatum geworden.
        assert "captured_at" not in Attachment.__table__.c
        assert "original_name" not in Attachment.__table__.c

    def test_status_wird_oeffentlich_projiziert(self, client, paar) -> None:  # type: ignore[no-untyped-def]
        angelegt = client.post(
            path(paar["space"].id), json=upload_body(), headers=auth(paar["token_a"])
        )
        assert angelegt.status_code == 201
        assert angelegt.json()["attachment"]["status"] == "PENDING"
        assert angelegt.json()["method"] == "STREAM"
        # Keine Storage-Interna nach aussen.
        for verboten in ("storageKey", "bucket", "provider", "filesystemPath", "privacyClass"):
            assert verboten not in angelegt.text

    def test_finalize_ist_idempotent(self, client, paar, session) -> None:  # type: ignore[no-untyped-def]
        _, kennung = lade_hoch(client, paar)
        zweimal = client.post(
            f"{path(paar['space'].id)}/{kennung}/finalize",
            json={},
            headers=auth(paar["token_a"]),
        )
        assert zweimal.status_code == 202

        from sidebyside.jobs.models import Job

        auftraege = (
            session.execute(select(Job).where(Job.kind == service.ATTACHMENT_VALIDATION))
            .scalars()
            .all()
        )
        assert len(auftraege) == 1


class TestFailClosed:
    def test_video_upload_wird_bei_aktivem_ffmpeg_angenommen(self, client, paar, monkeypatch) -> None:  # type: ignore[no-untyped-def]
        monkeypatch.setattr(service, "get_settings", lambda: Settings(ffmpeg_enabled=True))
        antwort = client.post(
            path(paar["space"].id),
            json=upload_body(mediaType="VIDEO", expectedMimeType="video/mp4"),
            headers=auth(paar["token_a"]),
        )
        assert antwort.status_code == 201
        assert antwort.json()["attachment"]["mediaType"] == "VIDEO"

    def test_video_upload_wird_bei_deaktiviertem_ffmpeg_abgewiesen(self, client, paar, monkeypatch) -> None:  # type: ignore[no-untyped-def]
        monkeypatch.setattr(service, "get_settings", lambda: Settings(ffmpeg_enabled=False))
        antwort = client.post(
            path(paar["space"].id),
            json=upload_body(mediaType="VIDEO", expectedMimeType="video/mp4"),
            headers=auth(paar["token_a"]),
        )
        assert antwort.status_code == 415
        assert antwort.json()["code"] == "ATTACHMENT_TYPE_NOT_ALLOWED"

    def test_worker_startet_ffmpeg_nach_spaeterem_abschalten_nicht(
        self, client, paar, session, monkeypatch  # type: ignore[no-untyped-def]
    ) -> None:
        monkeypatch.setattr(service, "get_settings", lambda: Settings(ffmpeg_enabled=True))
        antwort, kennung = lade_hoch(
            client,
            paar,
            daten=b"queued-video",
            mediaType="VIDEO",
            originalName="clip.mp4",
            expectedMimeType="video/mp4",
        )
        assert antwort.status_code == 202

        monkeypatch.setattr(service, "get_settings", lambda: Settings(ffmpeg_enabled=False))

        def must_not_run(*_: object, **__: object) -> None:
            raise AssertionError("videos.process must not run when ffmpeg is disabled")

        monkeypatch.setattr(service.videos, "process", must_not_run)
        attachment = verarbeite(session, kennung)
        assert attachment.status == AttachmentStatus.FAILED.value
        assert attachment.failure_code == "ATTACHMENT_TYPE_NOT_ALLOWED"

    def test_unbekannter_typ_wird_abgewiesen(self, client, paar) -> None:  # type: ignore[no-untyped-def]
        for mime in ("image/gif", "application/pdf", "image/svg+xml", "video/x-matroska"):
            antwort = client.post(
                path(paar["space"].id),
                json=upload_body(expectedMimeType=mime),
                headers=auth(paar["token_a"]),
            )
            assert antwort.status_code == 415, mime

    def test_angekuendigte_ueberschreitung_wird_abgewiesen(self, client, paar) -> None:  # type: ignore[no-untyped-def]
        antwort = client.post(
            path(paar["space"].id),
            json=upload_body(expectedSize=26 * 1024 * 1024),
            headers=auth(paar["token_a"]),
        )
        assert antwort.status_code == 413
        assert antwort.json()["code"] == "ATTACHMENT_TOO_LARGE"

    def test_getarnter_inhalt_erreicht_kein_ready(self, client, paar, session) -> None:  # type: ignore[no-untyped-def]
        """Der angekuendigte Typ zaehlt nicht - die Magic Bytes entscheiden."""
        _, kennung = lade_hoch(client, paar, daten=b"GIF89a" + b"\x00" * 64)
        attachment = verarbeite(session, kennung)
        assert attachment.status == AttachmentStatus.FAILED.value
        assert attachment.failure_code is not None
        assert attachment.ready_at is None

    def test_png_als_jpeg_angekuendigt_scheitert(self, client, paar, session) -> None:  # type: ignore[no-untyped-def]
        puffer = io.BytesIO()
        Image.new("RGB", (16, 16)).save(puffer, "PNG")
        _, kennung = lade_hoch(client, paar, daten=puffer.getvalue())
        attachment = verarbeite(session, kennung)
        assert attachment.status == AttachmentStatus.FAILED.value

    def test_abgeschnittene_datei_scheitert(self, client, paar, session) -> None:  # type: ignore[no-untyped-def]
        ganz = bild_mit_metadaten()
        _, kennung = lade_hoch(client, paar, daten=ganz[: len(ganz) // 2])
        attachment = verarbeite(session, kennung)
        assert attachment.status == AttachmentStatus.FAILED.value

    def test_ein_gescheitertes_attachment_ist_nicht_lesbar(self, client, paar, session) -> None:  # type: ignore[no-untyped-def]
        _, kennung = lade_hoch(client, paar, daten=b"nicht wirklich ein bild")
        verarbeite(session, kennung)
        antwort = client.get(
            f"{path(paar['space'].id)}/{kennung}/content",
            headers=auth(paar["token_a"]),
        )
        assert antwort.status_code == 409
        assert antwort.json()["code"] == "ATTACHMENT_NOT_READY"


class TestOwnerGrenze:
    def test_partner_sieht_fremdes_attachment_nicht(self, client, paar, session) -> None:  # type: ignore[no-untyped-def]
        _, kennung = lade_hoch(client, paar)
        verarbeite(session, kennung)

        for antwort in (
            client.get(f"{path(paar['space'].id)}/{kennung}", headers=auth(paar["token_b"])),
            client.get(
                f"{path(paar['space'].id)}/{kennung}/content", headers=auth(paar["token_b"])
            ),
            client.post(
                f"{path(paar['space'].id)}/{kennung}/read-access",
                json={"parentType": "NONE"},
                headers=auth(paar["token_b"]),
            ),
        ):
            assert antwort.status_code == 404

    def test_anonymer_zugriff_wird_abgewiesen(self, client, paar, session) -> None:  # type: ignore[no-untyped-def]
        _, kennung = lade_hoch(client, paar)
        verarbeite(session, kennung)
        assert client.get(f"{path(paar['space'].id)}/{kennung}/content").status_code == 401

    def test_geratener_storage_key_hilft_nicht(self, client, paar, session) -> None:  # type: ignore[no-untyped-def]
        """Es gibt keine Route, die einen Storage Key entgegennimmt."""
        _, kennung = lade_hoch(client, paar)
        attachment = verarbeite(session, kennung)
        schluessel = build_storage_key(attachment.space_id, attachment.id, "original")
        antwort = client.get(f"/api/v1/{schluessel}", headers=auth(paar["token_a"]))
        assert antwort.status_code == 404

    def test_owner_liest_eigenen_ungebundenen_upload(self, client, paar, session) -> None:  # type: ignore[no-untyped-def]
        """M2-D24."""
        _, kennung = lade_hoch(client, paar)
        verarbeite(session, kennung)

        beschreibung = client.post(
            f"{path(paar['space'].id)}/{kennung}/read-access",
            json={"parentType": "NONE"},
            headers=auth(paar["token_a"]),
        )
        assert beschreibung.status_code == 200
        assert beschreibung.json()["method"] == "STREAM"

        inhalt = client.get(beschreibung.json()["url"], headers=auth(paar["token_a"]))
        assert inhalt.status_code == 200
        assert inhalt.headers["content-type"].startswith("image/jpeg")
        assert HERSTELLER.encode() not in inhalt.content

        thumbnail = client.get(
            f"{path(paar['space'].id)}/{kennung}/content?variant=thumbnail",
            headers=auth(paar["token_a"]),
        )
        assert thumbnail.status_code == 200

    def test_parentreferenz_verleiht_keinen_zugriff(self, client, paar, session) -> None:  # type: ignore[no-untyped-def]
        """Solange nichts gebunden ist, gibt es keinen Parent, der traegt."""
        _, kennung = lade_hoch(client, paar)
        verarbeite(session, kennung)
        antwort = client.post(
            f"{path(paar['space'].id)}/{kennung}/read-access",
            json={"parentType": "MEMORY", "parentId": str(uuid4())},
            headers=auth(paar["token_a"]),
        )
        assert antwort.status_code == 404

    def test_abgelaufenes_bindungsfenster_sperrt_den_zugriff(self, client, paar, session) -> None:  # type: ignore[no-untyped-def]
        _, kennung = lade_hoch(client, paar)
        attachment = verarbeite(session, kennung)
        attachment.ready_at = now() - service.BINDING_WINDOW - timedelta(minutes=1)
        session.flush()

        antwort = client.get(
            f"{path(paar['space'].id)}/{kennung}/content",
            headers=auth(paar["token_a"]),
        )
        assert antwort.status_code == 404


class TestLoeschenUndAufraeumen:
    def test_delete_macht_sofort_unsichtbar(self, client, paar, session) -> None:  # type: ignore[no-untyped-def]
        _, kennung = lade_hoch(client, paar)
        attachment = verarbeite(session, kennung)

        geloescht = client.delete(
            f"{path(paar['space'].id)}/{kennung}",
            headers={**auth(paar["token_a"]), "If-Match": f'"{attachment.version}"'},
        )
        assert geloescht.status_code == 204

        assert (
            client.get(
                f"{path(paar['space'].id)}/{kennung}", headers=auth(paar["token_a"])
            ).status_code
            == 404
        )

    def test_delete_verlangt_aktuelle_version(self, client, paar, session) -> None:  # type: ignore[no-untyped-def]
        _, kennung = lade_hoch(client, paar)
        attachment = verarbeite(session, kennung)
        antwort = client.delete(
            f"{path(paar['space'].id)}/{kennung}",
            headers={**auth(paar["token_a"]), "If-Match": f'"{attachment.version + 5}"'},
        )
        assert antwort.status_code == 409

    def test_cleanup_entfernt_original_und_thumbnail(self, client, paar, session) -> None:  # type: ignore[no-untyped-def]
        _, kennung = lade_hoch(client, paar)
        attachment = verarbeite(session, kennung)
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

    def test_ungebundenes_ready_laeuft_nach_dem_fenster_ab(self, client, paar, session) -> None:  # type: ignore[no-untyped-def]
        """M2-D20."""
        _, kennung = lade_hoch(client, paar)
        attachment = verarbeite(session, kennung)
        attachment.ready_at = now() - service.BINDING_WINDOW - timedelta(minutes=1)
        session.flush()

        cleanup.run_media_cleanup(session, {})
        session.flush()

        assert (
            client.get(
                f"{path(paar['space'].id)}/{kennung}", headers=auth(paar["token_a"])
            ).status_code
            == 404
        )

    def test_angefangener_upload_laeuft_nach_24h_ab(self, client, paar, session) -> None:  # type: ignore[no-untyped-def]
        """M2-D12."""
        angelegt = client.post(
            path(paar["space"].id), json=upload_body(), headers=auth(paar["token_a"])
        )
        kennung = angelegt.json()["attachment"]["id"]
        zeile = session.execute(
            select(Attachment).where(Attachment.id == __import__("uuid").UUID(kennung))
        ).scalar_one()
        zeile.created_at = now() - cleanup.UPLOAD_RETENTION - timedelta(minutes=1)
        session.flush()

        cleanup.run_media_cleanup(session, {})
        session.flush()

        assert (
            client.get(
                f"{path(paar['space'].id)}/{kennung}", headers=auth(paar["token_a"])
            ).status_code
            == 404
        )

    def test_frischer_upload_wird_nicht_aufgeraeumt(self, client, paar, session) -> None:  # type: ignore[no-untyped-def]
        angelegt = client.post(
            path(paar["space"].id), json=upload_body(), headers=auth(paar["token_a"])
        )
        kennung = angelegt.json()["attachment"]["id"]
        cleanup.run_media_cleanup(session, {})
        session.flush()
        assert (
            client.get(
                f"{path(paar['space'].id)}/{kennung}", headers=auth(paar["token_a"])
            ).status_code
            == 200
        )
