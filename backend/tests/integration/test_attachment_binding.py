"""Bindung von Attachments an Memory und HeartMoment.

Der Kern ist eine einzige Zusage: nach der Bindung folgt die Lesbarkeit
ausschliesslich dem Parent. Der Attachment-Owner ist dann kein alternativer
Lesepfad mehr.
"""

from __future__ import annotations

import io
from datetime import timedelta
from typing import Any
from uuid import UUID, uuid4

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


def basis(space_id: object) -> str:
    return f"/api/v1/spaces/{space_id}"


def bild() -> bytes:
    puffer = io.BytesIO()
    Image.new("RGB", (32, 24), (10, 20, 30)).save(puffer, "JPEG")
    return puffer.getvalue()


def if_match(token: str, version: int) -> dict[str, str]:
    return {**auth(token), "If-Match": f'"{version}"'}


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


def fertiges_attachment(client, paar, session, *, token_key: str = "token_a") -> str:  # type: ignore[no-untyped-def]
    inhalt = bild()
    angelegt = client.post(
        f"{basis(paar['space'].id)}/attachments",
        json={
            "mediaType": "IMAGE",
            "originalName": "bild.jpg",
            "expectedMimeType": "image/jpeg",
            "expectedSize": len(inhalt),
        },
        headers=auth(paar[token_key]),
    ).json()
    kennung = angelegt["attachment"]["id"]
    client.put(
        f"{basis(paar['space'].id)}/attachments/{kennung}/content",
        content=inhalt,
        headers=auth(paar[token_key]),
    )
    client.post(
        f"{basis(paar['space'].id)}/attachments/{kennung}/finalize",
        json={},
        headers=auth(paar[token_key]),
    )
    service.validate(session, UUID(kennung))
    session.flush()
    return kennung


def memory(client, paar, *, token_key: str = "token_a") -> dict[str, Any]:  # type: ignore[no-untyped-def]
    return client.post(
        f"{basis(paar['space'].id)}/memories",
        json={"title": "Urlaub", "body": "Text", "happenedOn": "2025-06-13"},
        headers=auth(paar[token_key]),
    ).json()


def heart_moment(client, paar, *, visibility: str = "SHARED", attachment_id: str | None = None):  # type: ignore[no-untyped-def]
    koerper: dict[str, Any] = {
        "text": "Danke fuer heute.",
        "emotion": "LOVED",
        "visibility": visibility,
        "happenedOn": "2025-06-13",
    }
    if attachment_id is not None:
        koerper["attachmentId"] = attachment_id
    return client.post(
        f"{basis(paar['space'].id)}/heart-moments", json=koerper, headers=auth(paar["token_a"])
    )


class TestGalerie:
    def test_reihenfolge_bleibt_stabil(self, client, paar, session) -> None:  # type: ignore[no-untyped-def]
        eins = fertiges_attachment(client, paar, session)
        zwei = fertiges_attachment(client, paar, session)
        drei = fertiges_attachment(client, paar, session)
        m = memory(client, paar)

        gesetzt = client.put(
            f"{basis(paar['space'].id)}/memories/{m['id']}/attachments",
            json={
                "attachments": [
                    {"attachmentId": drei, "position": 0},
                    {"attachmentId": eins, "position": 1},
                    {"attachmentId": zwei, "position": 2},
                ]
            },
            headers=if_match(paar["token_a"], m["version"]),
        )
        assert gesetzt.status_code == 200
        assert [a["id"] for a in gesetzt.json()["attachments"]] == [drei, eins, zwei]

        erneut = client.get(
            f"{basis(paar['space'].id)}/memories/{m['id']}", headers=auth(paar["token_a"])
        )
        assert [a["id"] for a in erneut.json()["attachments"]] == [drei, eins, zwei]
        assert [a["position"] for a in erneut.json()["attachments"]] == [0, 1, 2]

    def test_tausch_der_plaetze_funktioniert(self, client, paar, session) -> None:  # type: ignore[no-untyped-def]
        """Eindeutige Positionen duerfen sich beim Tausch nicht selbst blockieren."""
        eins = fertiges_attachment(client, paar, session)
        zwei = fertiges_attachment(client, paar, session)
        m = memory(client, paar)

        erst = client.put(
            f"{basis(paar['space'].id)}/memories/{m['id']}/attachments",
            json={
                "attachments": [
                    {"attachmentId": eins, "position": 0},
                    {"attachmentId": zwei, "position": 1},
                ]
            },
            headers=if_match(paar["token_a"], m["version"]),
        )
        assert erst.status_code == 200

        getauscht = client.put(
            f"{basis(paar['space'].id)}/memories/{m['id']}/attachments",
            json={
                "attachments": [
                    {"attachmentId": zwei, "position": 0},
                    {"attachmentId": eins, "position": 1},
                ]
            },
            headers=if_match(paar["token_a"], erst.json()["version"]),
        )
        assert getauscht.status_code == 200
        assert [a["id"] for a in getauscht.json()["attachments"]] == [zwei, eins]

    def test_luecken_in_den_positionen_werden_abgewiesen(self, client, paar, session) -> None:  # type: ignore[no-untyped-def]
        eins = fertiges_attachment(client, paar, session)
        m = memory(client, paar)
        antwort = client.put(
            f"{basis(paar['space'].id)}/memories/{m['id']}/attachments",
            json={"attachments": [{"attachmentId": eins, "position": 3}]},
            headers=if_match(paar["token_a"], m["version"]),
        )
        assert antwort.status_code == 422

    def test_dasselbe_attachment_zweimal_wird_abgewiesen(self, client, paar, session) -> None:  # type: ignore[no-untyped-def]
        eins = fertiges_attachment(client, paar, session)
        m = memory(client, paar)
        antwort = client.put(
            f"{basis(paar['space'].id)}/memories/{m['id']}/attachments",
            json={
                "attachments": [
                    {"attachmentId": eins, "position": 0},
                    {"attachmentId": eins, "position": 1},
                ]
            },
            headers=if_match(paar["token_a"], m["version"]),
        )
        assert antwort.status_code == 422

    def test_entfernen_gibt_das_attachment_zum_aufraeumen_frei(self, client, paar, session) -> None:  # type: ignore[no-untyped-def]
        eins = fertiges_attachment(client, paar, session)
        m = memory(client, paar)
        gesetzt = client.put(
            f"{basis(paar['space'].id)}/memories/{m['id']}/attachments",
            json={"attachments": [{"attachmentId": eins, "position": 0}]},
            headers=if_match(paar["token_a"], m["version"]),
        )
        geleert = client.put(
            f"{basis(paar['space'].id)}/memories/{m['id']}/attachments",
            json={"attachments": []},
            headers=if_match(paar["token_a"], gesetzt.json()["version"]),
        )
        assert geleert.status_code == 200
        assert geleert.json()["attachments"] == []

        zeile = session.execute(select(Attachment).where(Attachment.id == UUID(eins))).scalar_one()
        assert zeile.status == AttachmentStatus.DELETING.value


class TestExklusiveBindung:
    def test_ein_attachment_gehoert_hoechstens_einem_parent(self, client, paar, session) -> None:  # type: ignore[no-untyped-def]
        eins = fertiges_attachment(client, paar, session)
        erste = memory(client, paar)
        zweite = memory(client, paar)

        client.put(
            f"{basis(paar['space'].id)}/memories/{erste['id']}/attachments",
            json={"attachments": [{"attachmentId": eins, "position": 0}]},
            headers=if_match(paar["token_a"], erste["version"]),
        )
        antwort = client.put(
            f"{basis(paar['space'].id)}/memories/{zweite['id']}/attachments",
            json={"attachments": [{"attachmentId": eins, "position": 0}]},
            headers=if_match(paar["token_a"], zweite["version"]),
        )
        assert antwort.status_code == 409
        assert antwort.json()["code"] == "ATTACHMENT_ALREADY_LINKED"

    def test_nicht_gleichzeitig_an_memory_und_heart_moment(self, client, paar, session) -> None:  # type: ignore[no-untyped-def]
        """Das kann keine einzelne Tabelle wissen - deshalb geprueft."""
        eins = fertiges_attachment(client, paar, session)
        m = memory(client, paar)
        client.put(
            f"{basis(paar['space'].id)}/memories/{m['id']}/attachments",
            json={"attachments": [{"attachmentId": eins, "position": 0}]},
            headers=if_match(paar["token_a"], m["version"]),
        )
        antwort = heart_moment(client, paar, attachment_id=eins)
        assert antwort.status_code == 409
        assert antwort.json()["code"] == "ATTACHMENT_ALREADY_LINKED"

    def test_erneutes_setzen_derselben_menge_ist_kein_konflikt(self, client, paar, session) -> None:  # type: ignore[no-untyped-def]
        eins = fertiges_attachment(client, paar, session)
        m = memory(client, paar)
        erst = client.put(
            f"{basis(paar['space'].id)}/memories/{m['id']}/attachments",
            json={"attachments": [{"attachmentId": eins, "position": 0}]},
            headers=if_match(paar["token_a"], m["version"]),
        )
        nochmal = client.put(
            f"{basis(paar['space'].id)}/memories/{m['id']}/attachments",
            json={"attachments": [{"attachmentId": eins, "position": 0}]},
            headers=if_match(paar["token_a"], erst.json()["version"]),
        )
        assert nochmal.status_code == 200


class TestBindbarkeit:
    def test_nur_ready_ist_bindbar(self, client, paar, session) -> None:  # type: ignore[no-untyped-def]
        inhalt = bild()
        angelegt = client.post(
            f"{basis(paar['space'].id)}/attachments",
            json={
                "mediaType": "IMAGE",
                "originalName": "bild.jpg",
                "expectedMimeType": "image/jpeg",
                "expectedSize": len(inhalt),
            },
            headers=auth(paar["token_a"]),
        ).json()
        m = memory(client, paar)
        antwort = client.put(
            f"{basis(paar['space'].id)}/memories/{m['id']}/attachments",
            json={"attachments": [{"attachmentId": angelegt["attachment"]["id"], "position": 0}]},
            headers=if_match(paar["token_a"], m["version"]),
        )
        assert antwort.status_code == 409
        assert antwort.json()["code"] == "ATTACHMENT_NOT_READY"

    def test_abgelaufenes_fenster_ist_nicht_mehr_bindbar(self, client, paar, session) -> None:  # type: ignore[no-untyped-def]
        eins = fertiges_attachment(client, paar, session)
        zeile = session.execute(select(Attachment).where(Attachment.id == UUID(eins))).scalar_one()
        zeile.ready_at = now() - service.BINDING_WINDOW - timedelta(minutes=1)
        session.flush()

        m = memory(client, paar)
        antwort = client.put(
            f"{basis(paar['space'].id)}/memories/{m['id']}/attachments",
            json={"attachments": [{"attachmentId": eins, "position": 0}]},
            headers=if_match(paar["token_a"], m["version"]),
        )
        assert antwort.status_code == 409

    def test_fremdes_attachment_ist_nicht_bindbar(self, client, paar, session) -> None:  # type: ignore[no-untyped-def]
        von_ben = fertiges_attachment(client, paar, session, token_key="token_b")
        m = memory(client, paar)
        antwort = client.put(
            f"{basis(paar['space'].id)}/memories/{m['id']}/attachments",
            json={"attachments": [{"attachmentId": von_ben, "position": 0}]},
            headers=if_match(paar["token_a"], m["version"]),
        )
        assert antwort.status_code == 404

    def test_unbekanntes_attachment_endet_wie_ein_fremdes(self, client, paar) -> None:  # type: ignore[no-untyped-def]
        m = memory(client, paar)
        antwort = client.put(
            f"{basis(paar['space'].id)}/memories/{m['id']}/attachments",
            json={"attachments": [{"attachmentId": str(uuid4()), "position": 0}]},
            headers=if_match(paar["token_a"], m["version"]),
        )
        assert antwort.status_code == 404


class TestLesbarkeitFolgtDemParent:
    def test_partner_liest_attachment_einer_gemeinsamen_memory(self, client, paar, session) -> None:  # type: ignore[no-untyped-def]
        eins = fertiges_attachment(client, paar, session)
        m = memory(client, paar)
        client.put(
            f"{basis(paar['space'].id)}/memories/{m['id']}/attachments",
            json={"attachments": [{"attachmentId": eins, "position": 0}]},
            headers=if_match(paar["token_a"], m["version"]),
        )

        inhalt = client.get(
            f"{basis(paar['space'].id)}/attachments/{eins}/content",
            headers=auth(paar["token_b"]),
        )
        assert inhalt.status_code == 200

    def test_privater_heart_moment_sperrt_auch_sein_attachment(self, client, paar, session) -> None:  # type: ignore[no-untyped-def]
        eins = fertiges_attachment(client, paar, session)
        hm = heart_moment(client, paar, attachment_id=eins).json()

        # Solange SHARED: der Partner darf.
        assert (
            client.get(
                f"{basis(paar['space'].id)}/attachments/{eins}/content",
                headers=auth(paar["token_b"]),
            ).status_code
            == 200
        )

        client.patch(
            f"{basis(paar['space'].id)}/heart-moments/{hm['id']}/visibility",
            json={"visibility": "PRIVATE"},
            headers=if_match(paar["token_a"], hm["version"]),
        )

        gesperrt = client.get(
            f"{basis(paar['space'].id)}/attachments/{eins}/content",
            headers=auth(paar["token_b"]),
        )
        assert gesperrt.status_code == 404

    def test_owner_ist_nach_der_bindung_kein_eigener_lesepfad(self, client, paar, session) -> None:  # type: ignore[no-untyped-def]
        """Ben laedt hoch, Ben bindet an seinen privaten HeartMoment.

        Danach darf Anna nicht lesen - obwohl sie im selben Space ist.
        """
        von_ben = fertiges_attachment(client, paar, session, token_key="token_b")
        angelegt = client.post(
            f"{basis(paar['space'].id)}/heart-moments",
            json={
                "text": "Nur fuer mich.",
                "emotion": "SEEN",
                "visibility": "PRIVATE",
                "happenedOn": "2025-06-13",
                "attachmentId": von_ben,
            },
            headers=auth(paar["token_b"]),
        )
        assert angelegt.status_code == 201

        assert (
            client.get(
                f"{basis(paar['space'].id)}/attachments/{von_ben}/content",
                headers=auth(paar["token_a"]),
            ).status_code
            == 404
        )

    def test_falsche_parentangabe_wird_abgewiesen(self, client, paar, session) -> None:  # type: ignore[no-untyped-def]
        eins = fertiges_attachment(client, paar, session)
        m = memory(client, paar)
        client.put(
            f"{basis(paar['space'].id)}/memories/{m['id']}/attachments",
            json={"attachments": [{"attachmentId": eins, "position": 0}]},
            headers=if_match(paar["token_a"], m["version"]),
        )
        antwort = client.post(
            f"{basis(paar['space'].id)}/attachments/{eins}/read-access",
            json={"parentType": "MEMORY", "parentId": str(uuid4())},
            headers=auth(paar["token_a"]),
        )
        assert antwort.status_code == 404

    def test_none_ist_nach_der_bindung_unzulaessig(self, client, paar, session) -> None:  # type: ignore[no-untyped-def]
        """M2-D24 gilt nur fuer ungebundene Uploads."""
        eins = fertiges_attachment(client, paar, session)
        m = memory(client, paar)
        client.put(
            f"{basis(paar['space'].id)}/memories/{m['id']}/attachments",
            json={"attachments": [{"attachmentId": eins, "position": 0}]},
            headers=if_match(paar["token_a"], m["version"]),
        )
        antwort = client.post(
            f"{basis(paar['space'].id)}/attachments/{eins}/read-access",
            json={"parentType": "NONE"},
            headers=auth(paar["token_a"]),
        )
        assert antwort.status_code == 404


class TestCleanupRespektiertBindung:
    def test_gebundenes_attachment_laeuft_nicht_ab(self, client, paar, session) -> None:  # type: ignore[no-untyped-def]
        """Seit der Bindung folgt die Lebensdauer dem Parent (M2-D20)."""
        eins = fertiges_attachment(client, paar, session)
        m = memory(client, paar)
        client.put(
            f"{basis(paar['space'].id)}/memories/{m['id']}/attachments",
            json={"attachments": [{"attachmentId": eins, "position": 0}]},
            headers=if_match(paar["token_a"], m["version"]),
        )

        zeile = session.execute(select(Attachment).where(Attachment.id == UUID(eins))).scalar_one()
        zeile.ready_at = now() - service.BINDING_WINDOW - timedelta(hours=5)
        session.flush()

        cleanup.run_media_cleanup(session, {})
        session.flush()

        session.refresh(zeile)
        assert zeile.status == AttachmentStatus.READY.value
        assert get_media_store().exists(build_storage_key(zeile.space_id, zeile.id, "original"))

    def test_ungebundenes_laeuft_weiterhin_ab(self, client, paar, session) -> None:  # type: ignore[no-untyped-def]
        eins = fertiges_attachment(client, paar, session)
        zeile = session.execute(select(Attachment).where(Attachment.id == UUID(eins))).scalar_one()
        zeile.ready_at = now() - service.BINDING_WINDOW - timedelta(minutes=1)
        session.flush()

        cleanup.run_media_cleanup(session, {})
        session.flush()

        assert (
            client.get(
                f"{basis(paar['space'].id)}/attachments/{eins}", headers=auth(paar["token_a"])
            ).status_code
            == 404
        )
