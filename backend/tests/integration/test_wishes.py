"""PostgreSQL-/HTTP-Abnahme fuer den M3-S1-Wish-Slice.

Zwei Schwerpunkte, und sie sind die eigentliche Fachlichkeit dieses Slices.

M3-D01: ein Wunsch gehoert dem Paar. Anders als bei Memory und Milestone
darf der Partner ihn aendern und loeschen, ohne ihn geschrieben zu haben -
`createdBy` ist Attribution und keine ACL. Der Nachweis ist deshalb nicht
"Anna darf", sondern "Ben darf, und `createdBy` bleibt trotzdem Anna".

M3-D02/D04: der Wish-Status folgt ausschliesslich dem Wish->Plan-Vertrag.
In M3-S1 gibt es noch keinen Plan, ein Wish ist also immer `OPEN`. Der
Nachweis dafuer ist ein Negativer: es gibt keinen Weg, ueber den ein
Request den Status verschiebt.
"""

from __future__ import annotations

from typing import Any
from uuid import UUID, uuid4

import pytest
from sqlalchemy import select, text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from sidebyside.outbox.models import OutboxEvent
from sidebyside.relationship import service as relationship_service
from sidebyside.wishes.models import Wish, WishStatus
from tests.conftest import auth, make_account, make_space, requires_database, sign_in

pytestmark = [pytest.mark.integration, requires_database]

GEHEIM = "Ein Wunsch, der nicht in Ereignisse gehoert."


def path(space_id: object) -> str:
    return f"/api/v1/spaces/{space_id}/wishes"


def body(*, title: str = "Nordlichter sehen") -> dict[str, Any]:
    return {"title": title}


def if_match(token: str, version: int) -> dict[str, str]:
    return {**auth(token), "If-Match": f'"{version}"'}


@pytest.fixture
def paar(session: Session):  # type: ignore[no-untyped-def]
    anna = make_account(session, "Anna")
    ben = make_account(session, "Ben")
    fremd = make_account(session, "Fremd")
    space = make_space(session, anna)
    relationship_service.add_member(session, space.id, ben)
    fremder_space = make_space(session, fremd)
    # Ben ist bewusst Mitglied beider Spaces. Damit kann die Cursor-Bindung
    # selbst geprueft werden, statt vorher an der Membership zu enden.
    relationship_service.add_member(session, fremder_space.id, ben)
    session.flush()
    return {
        "anna": anna,
        "ben": ben,
        "space": space,
        "fremder_space": fremder_space,
        "token_a": sign_in(session, anna),
        "token_b": sign_in(session, ben),
        "token_fremd": sign_in(session, fremd),
    }


def erstelle(client, paar, *, token_key: str = "token_a", **overrides):  # type: ignore[no-untyped-def]
    return client.post(
        path(paar["space"].id), json=body(**overrides), headers=auth(paar[token_key])
    )


class TestCrud:
    def test_anlegen_lesen_aendern_loeschen(self, client, paar) -> None:  # type: ignore[no-untyped-def]
        angelegt = erstelle(client, paar)
        assert angelegt.status_code == 201
        w = angelegt.json()
        assert UUID(w["id"]).version == 7
        assert w["title"] == "Nordlichter sehen"
        assert w["status"] == "OPEN"
        assert w["createdBy"] == str(paar["anna"].id)
        assert w["creator"]["displayName"] == "Anna"
        assert w["capabilities"] == {"canEdit": True, "canDelete": True, "canComment": False}
        assert "privacyClass" not in w
        assert angelegt.headers["ETag"] == '"1"'

        gelesen = client.get(f"{path(paar['space'].id)}/{w['id']}", headers=auth(paar["token_a"]))
        assert gelesen.status_code == 200
        assert gelesen.headers["ETag"] == '"1"'

        geaendert = client.patch(
            f"{path(paar['space'].id)}/{w['id']}",
            json={"title": "  Nordlichter in Tromsoe sehen  "},
            headers=if_match(paar["token_a"], 1),
        )
        assert geaendert.status_code == 200
        assert geaendert.json()["title"] == "Nordlichter in Tromsoe sehen"
        assert geaendert.json()["version"] == 2
        assert geaendert.headers["ETag"] == '"2"'

        geloescht = client.delete(
            f"{path(paar['space'].id)}/{w['id']}", headers=if_match(paar["token_a"], 2)
        )
        assert geloescht.status_code == 204
        danach = client.get(f"{path(paar['space'].id)}/{w['id']}", headers=auth(paar["token_a"]))
        assert danach.status_code == 404
        assert danach.json()["code"] == "WISH_NOT_FOUND"

    def test_leerer_titel_wird_abgewiesen(self, client, paar) -> None:  # type: ignore[no-untyped-def]
        assert erstelle(client, paar, title="   ").status_code == 422

    def test_liste_zeigt_neueste_zuerst(self, client, paar) -> None:  # type: ignore[no-untyped-def]
        erster = erstelle(client, paar, title="Erster").json()
        zweiter = erstelle(client, paar, title="Zweiter").json()

        seite = client.get(path(paar["space"].id), headers=auth(paar["token_a"])).json()
        assert [eintrag["id"] for eintrag in seite["items"]] == [zweiter["id"], erster["id"]]
        assert seite["hasMore"] is False
        assert seite["nextCursor"] is None

    def test_die_seite_laeuft_ueber_den_cursor_weiter(self, client, paar) -> None:  # type: ignore[no-untyped-def]
        erster = erstelle(client, paar, title="Erster").json()
        zweiter = erstelle(client, paar, title="Zweiter").json()

        erste_seite = client.get(
            f"{path(paar['space'].id)}?limit=1", headers=auth(paar["token_a"])
        ).json()
        assert [eintrag["id"] for eintrag in erste_seite["items"]] == [zweiter["id"]]
        assert erste_seite["hasMore"] is True

        zweite_seite = client.get(
            f"{path(paar['space'].id)}?limit=1&cursor={erste_seite['nextCursor']}",
            headers=auth(paar["token_a"]),
        ).json()
        assert [eintrag["id"] for eintrag in zweite_seite["items"]] == [erster["id"]]
        assert zweite_seite["hasMore"] is False

    def test_der_statusfilter_trifft_nur_vorhandene_zustaende(self, client, paar) -> None:  # type: ignore[no-untyped-def]
        erstelle(client, paar)

        offen = client.get(
            f"{path(paar['space'].id)}?status=OPEN", headers=auth(paar["token_a"])
        ).json()
        assert len(offen["items"]) == 1

        # In M3-S1 gibt es keinen Plan und damit keinen geplanten Wunsch.
        geplant = client.get(
            f"{path(paar['space'].id)}?status=PLANNED", headers=auth(paar["token_a"])
        ).json()
        assert geplant["items"] == []

    def test_ein_unbekannter_status_ist_kein_filter_sondern_ein_fehler(self, client, paar) -> None:  # type: ignore[no-untyped-def]
        """Sonst liefe ein Tippfehler still als ungefilterte Liste durch."""
        antwort = client.get(
            f"{path(paar['space'].id)}?status=ERFUNDEN", headers=auth(paar["token_a"])
        )
        assert antwort.status_code == 422


class TestGemeinsamesSchreiben:
    """M3-D01: beide Partner, nicht nur der Ersteller."""

    def test_der_partner_darf_aendern_und_createdby_bleibt(self, client, paar) -> None:  # type: ignore[no-untyped-def]
        w = erstelle(client, paar).json()

        geaendert = client.patch(
            f"{path(paar['space'].id)}/{w['id']}",
            json={"title": "Nordlichter im Winter sehen"},
            headers=if_match(paar["token_b"], 1),
        )
        assert geaendert.status_code == 200
        # Attribution, keine ACL: Ben hat geschrieben, Anna bleibt Ersteller.
        assert geaendert.json()["createdBy"] == str(paar["anna"].id)
        assert geaendert.json()["creator"]["displayName"] == "Anna"

    def test_der_partner_darf_loeschen(self, client, paar) -> None:  # type: ignore[no-untyped-def]
        w = erstelle(client, paar).json()
        antwort = client.delete(
            f"{path(paar['space'].id)}/{w['id']}", headers=if_match(paar["token_b"], 1)
        )
        assert antwort.status_code == 204

    def test_der_partner_sieht_dieselben_faehigkeiten(self, client, paar) -> None:  # type: ignore[no-untyped-def]
        """Ein `canEdit: false` waere hier eine falsche Auskunft an die UI."""
        w = erstelle(client, paar).json()
        gelesen = client.get(
            f"{path(paar['space'].id)}/{w['id']}", headers=auth(paar["token_b"])
        ).json()
        assert gelesen["capabilities"] == {
            "canEdit": True,
            "canDelete": True,
            "canComment": False,
        }

    def test_memory_bleibt_trotzdem_author_only(self, client, paar) -> None:  # type: ignore[no-untyped-def]
        """Die Gegenprobe zur neuen Schreibregel.

        Collaborative write ist eine Eigenschaft der M3-Planungsdomaenen,
        keine neue Voreinstellung. Waere sie eine, haette dieser Slice
        stillschweigend die Memory-Regel aus Abschnitt 14 der
        Spezifikation aufgeweicht.
        """
        memory = client.post(
            f"/api/v1/spaces/{paar['space'].id}/memories",
            json={"title": "Nur von Anna", "body": "Text", "happenedOn": "2025-06-13"},
            headers=auth(paar["token_a"]),
        ).json()

        antwort = client.patch(
            f"/api/v1/spaces/{paar['space'].id}/memories/{memory['id']}",
            json={"title": "Von Ben geaendert"},
            headers=if_match(paar["token_b"], 1),
        )
        assert antwort.status_code == 403


class TestStatus:
    """M3-D02/D04: kein Weg am Wish->Plan-Vertrag vorbei."""

    def test_ein_neuer_wunsch_ist_offen(self, client, paar, session) -> None:  # type: ignore[no-untyped-def]
        w = erstelle(client, paar).json()
        zeile = session.get(Wish, UUID(w["id"]))
        assert zeile.status == WishStatus.OPEN.value

    def test_create_kann_den_status_nicht_mitschicken(self, client, paar) -> None:  # type: ignore[no-untyped-def]
        antwort = client.post(
            path(paar["space"].id),
            json={"title": "Direkt geplant", "status": "PLANNED"},
            headers=auth(paar["token_a"]),
        )
        assert antwort.status_code == 422

    def test_patch_kann_den_status_nicht_setzen(self, client, paar, session) -> None:  # type: ignore[no-untyped-def]
        w = erstelle(client, paar).json()

        antwort = client.patch(
            f"{path(paar['space'].id)}/{w['id']}",
            json={"status": "COMPLETED"},
            headers=if_match(paar["token_a"], 1),
        )
        assert antwort.status_code == 422

        session.expire_all()
        assert session.get(Wish, UUID(w["id"])).status == WishStatus.OPEN.value

    def test_auch_titel_plus_status_geht_nicht_durch(self, client, paar, session) -> None:  # type: ignore[no-untyped-def]
        """Ein gueltiges Feld darf kein Traeger fuer ein verbotenes sein."""
        w = erstelle(client, paar).json()

        antwort = client.patch(
            f"{path(paar['space'].id)}/{w['id']}",
            json={"title": "Neuer Titel", "status": "COMPLETED"},
            headers=if_match(paar["token_a"], 1),
        )
        assert antwort.status_code == 422

        session.expire_all()
        zeile = session.get(Wish, UUID(w["id"]))
        assert zeile.status == WishStatus.OPEN.value
        assert zeile.payload.title == "Nordlichter sehen"

    def test_eine_titelkorrektur_laesst_den_status_stehen(self, client, paar) -> None:  # type: ignore[no-untyped-def]
        w = erstelle(client, paar).json()
        geaendert = client.patch(
            f"{path(paar['space'].id)}/{w['id']}",
            json={"title": "Andere Formulierung"},
            headers=if_match(paar["token_a"], 1),
        )
        assert geaendert.json()["status"] == "OPEN"

    def test_die_datenbank_laesst_keinen_erfundenen_status_zu(self, client, paar, session) -> None:  # type: ignore[no-untyped-def]
        """Die letzte Grenze liegt im Schema, nicht nur im Dienst.

        Absichtlich als rohes SQL: ueber das ORM faengt schon der
        Spaltentyp den Wert ab. Geprueft werden soll hier aber der CHECK in
        PostgreSQL - er ist es, der auch ein Wartungsskript oder eine
        spaetere Migration aufhaelt.
        """
        w = erstelle(client, paar).json()
        # Der Savepoint faengt den Abbruch: ohne ihn bliebe die
        # Testtransaktion nach dem verletzten CHECK unbrauchbar.
        with pytest.raises(IntegrityError), session.begin_nested():
            session.execute(
                text("UPDATE wishes SET status = 'ERFUNDEN' WHERE id = :id"),
                {"id": w["id"]},
            )


class TestDeleteMatrix:
    """M3-D05, soweit dieser Slice sie beantworten kann.

    `PLANNED` und `COMPLETED` entstehen erst aus dem Wish->Plan-Vertrag und
    sind ueber HTTP noch nicht erreichbar. Der Zustand wird deshalb direkt
    in der Datenbank hergestellt - nicht als Abkuerzung, sondern weil genau
    das der Fall ist, den der spaetere Slice hier vorfinden wird.
    """

    def _setze_status(self, session: Session, wish_id: str, status: WishStatus) -> int:
        zeile = session.get(Wish, UUID(wish_id))
        assert zeile is not None
        zeile.status = status.value
        session.flush()
        return zeile.version

    def test_offen_darf_geloescht_werden(self, client, paar) -> None:  # type: ignore[no-untyped-def]
        w = erstelle(client, paar).json()
        antwort = client.delete(
            f"{path(paar['space'].id)}/{w['id']}", headers=if_match(paar["token_a"], 1)
        )
        assert antwort.status_code == 204

    def test_geplant_wird_blockiert(self, client, paar, session) -> None:  # type: ignore[no-untyped-def]
        w = erstelle(client, paar).json()
        version = self._setze_status(session, w["id"], WishStatus.PLANNED)

        antwort = client.delete(
            f"{path(paar['space'].id)}/{w['id']}", headers=if_match(paar["token_a"], version)
        )
        assert antwort.status_code == 409
        assert antwort.json()["code"] == "WISH_HAS_ACTIVE_PLAN"

        session.expire_all()
        assert session.get(Wish, UUID(w["id"])) is not None

    def test_geplant_meldet_das_auch_in_den_faehigkeiten(self, client, paar, session) -> None:  # type: ignore[no-untyped-def]
        w = erstelle(client, paar).json()
        self._setze_status(session, w["id"], WishStatus.PLANNED)

        gelesen = client.get(
            f"{path(paar['space'].id)}/{w['id']}", headers=auth(paar["token_a"])
        ).json()
        assert gelesen["status"] == "PLANNED"
        assert gelesen["capabilities"]["canDelete"] is False
        # Der Titel bleibt aenderbar: er ist ein Inhaltsupdate, keine
        # Statusmutation (M3-D02).
        assert gelesen["capabilities"]["canEdit"] is True

    def test_abgeschlossen_darf_geloescht_werden(self, client, paar, session) -> None:  # type: ignore[no-untyped-def]
        """Ein abgeschlossener Lifecycle laesst sich vollstaendig entfernen.

        Ohne originaeren Plan - und in M3-S1 gibt es keinen - ist das nach
        der Matrix erlaubt. Es gibt bewusst keine versteckte Cascade.
        """
        w = erstelle(client, paar).json()
        version = self._setze_status(session, w["id"], WishStatus.COMPLETED)

        antwort = client.delete(
            f"{path(paar['space'].id)}/{w['id']}", headers=if_match(paar["token_a"], version)
        )
        assert antwort.status_code == 204

    def test_die_versionspruefung_kommt_vor_der_statuspruefung(self, client, paar, session) -> None:  # type: ignore[no-untyped-def]
        """Ein veralteter Stand darf keine fachliche Auskunft erzeugen."""
        w = erstelle(client, paar).json()
        self._setze_status(session, w["id"], WishStatus.PLANNED)

        antwort = client.delete(
            f"{path(paar['space'].id)}/{w['id']}", headers=if_match(paar["token_a"], 99)
        )
        assert antwort.status_code == 409
        assert antwort.json()["code"] == "RESOURCE_VERSION_CONFLICT"


class TestNebenlaeufigkeit:
    def test_veraltete_version_wird_abgewiesen(self, client, paar) -> None:  # type: ignore[no-untyped-def]
        w = erstelle(client, paar).json()
        client.patch(
            f"{path(paar['space'].id)}/{w['id']}",
            json={"title": "Erste Aenderung"},
            headers=if_match(paar["token_a"], 1),
        )

        zweite = client.patch(
            f"{path(paar['space'].id)}/{w['id']}",
            json={"title": "Zweite Aenderung"},
            headers=if_match(paar["token_a"], 1),
        )
        assert zweite.status_code == 409
        assert zweite.json()["code"] == "RESOURCE_VERSION_CONFLICT"

    def test_beide_partner_teilen_sich_dieselbe_version(self, client, paar) -> None:  # type: ignore[no-untyped-def]
        """Gemeinsames Schreiben heisst nicht: zwei getrennte Versionsspuren."""
        w = erstelle(client, paar).json()
        client.patch(
            f"{path(paar['space'].id)}/{w['id']}",
            json={"title": "Von Anna"},
            headers=if_match(paar["token_a"], 1),
        )

        bens_versuch = client.patch(
            f"{path(paar['space'].id)}/{w['id']}",
            json={"title": "Von Ben"},
            headers=if_match(paar["token_b"], 1),
        )
        assert bens_versuch.status_code == 409

    def test_loeschen_ohne_if_match_wird_nicht_ausgefuehrt(self, client, paar) -> None:  # type: ignore[no-untyped-def]
        w = erstelle(client, paar).json()
        antwort = client.delete(
            f"{path(paar['space'].id)}/{w['id']}", headers=auth(paar["token_a"])
        )
        assert antwort.status_code == 422
        assert (
            client.get(
                f"{path(paar['space'].id)}/{w['id']}", headers=auth(paar["token_a"])
            ).status_code
            == 200
        )


class TestMandant:
    def test_ein_fremder_sieht_den_space_nicht(self, client, paar) -> None:  # type: ignore[no-untyped-def]
        erstelle(client, paar)
        antwort = client.get(path(paar["space"].id), headers=auth(paar["token_fremd"]))
        assert antwort.status_code == 404
        assert antwort.json()["code"] == "SPACE_NOT_FOUND"

    def test_eine_id_aus_dem_anderen_space_bleibt_unsichtbar(self, client, paar) -> None:  # type: ignore[no-untyped-def]
        """Ben ist in beiden Spaces - die ID trennt sie, nicht die Membership."""
        w = erstelle(client, paar).json()

        gelesen = client.get(
            f"{path(paar['fremder_space'].id)}/{w['id']}", headers=auth(paar["token_b"])
        )
        assert gelesen.status_code == 404
        assert gelesen.json()["code"] == "WISH_NOT_FOUND"

    def test_ein_fremdschreibversuch_aendert_nichts(self, client, paar, session) -> None:  # type: ignore[no-untyped-def]
        w = erstelle(client, paar).json()

        antwort = client.patch(
            f"{path(paar['fremder_space'].id)}/{w['id']}",
            json={"title": "Uebernommen"},
            headers=if_match(paar["token_b"], 1),
        )
        assert antwort.status_code == 404

        session.expire_all()
        assert session.get(Wish, UUID(w["id"])).payload.title == "Nordlichter sehen"

    def test_die_liste_des_anderen_space_bleibt_leer(self, client, paar) -> None:  # type: ignore[no-untyped-def]
        erstelle(client, paar)
        seite = client.get(path(paar["fremder_space"].id), headers=auth(paar["token_b"])).json()
        assert seite["items"] == []

    def test_ein_cursor_gilt_nur_in_seinem_space(self, client, paar) -> None:  # type: ignore[no-untyped-def]
        erstelle(client, paar, title="Erster")
        erstelle(client, paar, title="Zweiter")
        seite = client.get(
            f"{path(paar['space'].id)}?limit=1", headers=auth(paar["token_a"])
        ).json()

        antwort = client.get(
            f"{path(paar['fremder_space'].id)}?limit=1&cursor={seite['nextCursor']}",
            headers=auth(paar["token_b"]),
        )
        assert antwort.status_code == 400
        assert antwort.json()["code"] == "INVALID_CURSOR"

    def test_ein_cursor_gilt_nur_fuer_seinen_filter(self, client, paar) -> None:  # type: ignore[no-untyped-def]
        erstelle(client, paar, title="Erster")
        erstelle(client, paar, title="Zweiter")
        seite = client.get(
            f"{path(paar['space'].id)}?limit=1&status=OPEN", headers=auth(paar["token_a"])
        ).json()

        antwort = client.get(
            f"{path(paar['space'].id)}?limit=1&cursor={seite['nextCursor']}",
            headers=auth(paar["token_a"]),
        )
        assert antwort.status_code == 400

    def test_eine_erfundene_id_und_eine_fehlgeformte_klingen_gleich(self, client, paar) -> None:  # type: ignore[no-untyped-def]
        unbekannt = client.get(f"{path(paar['space'].id)}/{uuid4()}", headers=auth(paar["token_a"]))
        unfug = client.get(f"{path(paar['space'].id)}/nicht-echt", headers=auth(paar["token_a"]))
        assert unbekannt.status_code == unfug.status_code == 404
        assert unbekannt.json() == unfug.json()


class TestEreignisse:
    def test_events_enthalten_keinen_wunschtitel(self, client, paar, session) -> None:  # type: ignore[no-untyped-def]
        w = erstelle(client, paar, title=GEHEIM).json()
        client.patch(
            f"{path(paar['space'].id)}/{w['id']}",
            json={"title": "Neu formuliert"},
            headers=if_match(paar["token_a"], 1),
        )
        client.delete(f"{path(paar['space'].id)}/{w['id']}", headers=if_match(paar["token_a"], 2))

        zeilen = list(
            session.execute(select(OutboxEvent).where(OutboxEvent.subject_type == "wish")).scalars()
        )
        assert [z.event_type for z in zeilen] == [
            "WISH_CREATED",
            "WISH_UPDATED",
            "WISH_DELETED",
        ]
        for zeile in zeilen:
            roh = repr(zeile.payload.model_dump())
            assert GEHEIM not in roh
            assert "Neu formuliert" not in roh
            assert zeile.resource_version is not None

    def test_das_ereignis_nennt_den_handelnden_und_nicht_den_ersteller(
        self, client, paar, session
    ) -> None:  # type: ignore[no-untyped-def]
        """Audit nach M3-D01: wer geaendert hat, nicht wem es zugeschrieben ist."""
        w = erstelle(client, paar).json()
        client.patch(
            f"{path(paar['space'].id)}/{w['id']}",
            json={"title": "Von Ben"},
            headers=if_match(paar["token_b"], 1),
        )

        aenderung = session.execute(
            select(OutboxEvent).where(OutboxEvent.event_type == "WISH_UPDATED")
        ).scalar_one()
        assert aenderung.actor_id == paar["ben"].id

    def test_ein_abgewiesener_schreibversuch_erzeugt_kein_ereignis(
        self, client, paar, session
    ) -> None:  # type: ignore[no-untyped-def]
        w = erstelle(client, paar).json()
        client.patch(
            f"{path(paar['space'].id)}/{w['id']}",
            json={"title": "Kollision"},
            headers=if_match(paar["token_a"], 99),
        )

        zeilen = list(
            session.execute(select(OutboxEvent).where(OutboxEvent.subject_type == "wish")).scalars()
        )
        assert [z.event_type for z in zeilen] == ["WISH_CREATED"]
