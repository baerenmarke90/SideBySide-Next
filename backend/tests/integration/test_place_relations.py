"""PostgreSQL-/HTTP-Abnahme fuer den M3-S4-Relations-Slice.

Geprueft wird die Pflichtliste aus Abschnitt 12 von
`docs/m3/decisions/PLACE-RELATIONS-CHAPTERS.md`, fuer jede freigegebene
Relationsart.

Der Schwerpunkt liegt auf dem, was M3-D09 zusichert: keine Relation zeigt
je auf einen privaten oder fremden Inhalt, und keine Antwort verraet,
welcher der beiden Faelle vorlag. Der zweite Schwerpunkt ist M3-D12: eine
Relation zu loesen entfernt die Verknuepfung und niemals ein Original.
"""

from __future__ import annotations

from datetime import date
from typing import Any
from uuid import UUID, uuid4

import pytest
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from sidebyside.heart_moments.models import HeartMoment
from sidebyside.memories.models import Memory
from sidebyside.milestones.models import Milestone
from sidebyside.relations.models import PlaceHeartMoment, PlaceMemory, PlaceMilestone
from sidebyside.relationship import service as relationship_service
from tests.conftest import auth, make_account, make_space, requires_database, sign_in

pytestmark = [pytest.mark.integration, requires_database]

HEUTE = date(2026, 8, 27)

# Die drei Relationsarten als Testparameter: Slug, Join-Modell, Original-
# Modell. Jeder Fall der Pflichtliste laeuft damit gegen alle drei, statt
# dreimal ausgeschrieben zu werden - eine vergessene Art faellt so auf.
ARTEN = [
    pytest.param("memories", PlaceMemory, Memory, id="memories"),
    pytest.param("heart-moments", PlaceHeartMoment, HeartMoment, id="heart-moments"),
    pytest.param("milestones", PlaceMilestone, Milestone, id="milestones"),
]


@pytest.fixture
def paar(session: Session):  # type: ignore[no-untyped-def]
    anna = make_account(session, "Anna")
    ben = make_account(session, "Ben")
    fremd = make_account(session, "Fremd")
    space = make_space(session, anna)
    relationship_service.add_member(session, space.id, ben)
    fremder_space = make_space(session, fremd)
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


def _create(client, paar, pfad: str, koerper: dict[str, Any], *, token_key="token_a", space=None):  # type: ignore[no-untyped-def]
    space_id = (space or paar["space"]).id
    antwort = client.post(
        f"/api/v1/spaces/{space_id}/{pfad}",
        json=koerper,
        headers=auth(paar[token_key]),
    )
    assert antwort.status_code == 201, antwort.text
    return antwort.json()


def ort(client, paar, *, token_key="token_a", space=None) -> dict[str, Any]:  # type: ignore[no-untyped-def]
    return _create(client, paar, "places", {"name": "Unser Cafe"}, token_key=token_key, space=space)


def ziel(client, paar, slug: str, *, token_key="token_a", space=None, visibility="SHARED"):  # type: ignore[no-untyped-def]
    """Ein Ziel der jeweiligen Art anlegen."""
    if slug == "memories":
        return _create(
            client,
            paar,
            "memories",
            {"title": "Erster Abend", "body": "Es regnete."},
            token_key=token_key,
            space=space,
        )
    if slug == "milestones":
        return _create(
            client,
            paar,
            "milestones",
            {"title": "Eingezogen", "happenedOn": HEUTE.isoformat()},
            token_key=token_key,
            space=space,
        )
    return _create(
        client,
        paar,
        "heart-moments",
        {
            "text": "Danke fuer heute.",
            "emotion": "LOVED",
            "visibility": visibility,
            "happenedOn": HEUTE.isoformat(),
        },
        token_key=token_key,
        space=space,
    )


def relation_pfad(paar, slug: str, place_id, target_id=None) -> str:  # type: ignore[no-untyped-def]
    basis = f"/api/v1/spaces/{paar['space'].id}/places/{place_id}/{slug}"
    return basis if target_id is None else f"{basis}/{target_id}"


def zaehle(session: Session, modell) -> int:  # type: ignore[no-untyped-def]
    return session.execute(select(func.count()).select_from(modell)).scalar_one()


class TestHappyPath:
    @pytest.mark.parametrize(("slug", "join_modell", "original"), ARTEN)
    def test_verknuepfen_lesen_loesen(  # type: ignore[no-untyped-def]
        self, client, session, paar, slug, join_modell, original
    ) -> None:
        o = ort(client, paar)
        z = ziel(client, paar, slug)

        gesetzt = client.put(
            relation_pfad(paar, slug, o["id"], z["id"]), headers=auth(paar["token_a"])
        )
        assert gesetzt.status_code == 204

        gelesen = client.get(relation_pfad(paar, slug, o["id"]), headers=auth(paar["token_a"]))
        assert gelesen.status_code == 200
        assert gelesen.json()["items"] == [z["id"]]

        # Der Partner sieht dieselbe Verknuepfung: eine Relation ist
        # gemeinsamer Inhalt, kein persoenlicher Merkzettel (M3-D01).
        vom_partner = client.get(relation_pfad(paar, slug, o["id"]), headers=auth(paar["token_b"]))
        assert vom_partner.json()["items"] == [z["id"]]

        geloest = client.delete(
            relation_pfad(paar, slug, o["id"], z["id"]), headers=auth(paar["token_b"])
        )
        assert geloest.status_code == 204
        assert (
            client.get(relation_pfad(paar, slug, o["id"]), headers=auth(paar["token_a"])).json()[
                "items"
            ]
            == []
        )

    @pytest.mark.parametrize(("slug", "join_modell", "original"), ARTEN)
    def test_doppeltes_put_ist_idempotent(  # type: ignore[no-untyped-def]
        self, client, session, paar, slug, join_modell, original
    ) -> None:
        """Zweimal dasselbe `PUT` ist derselbe Endzustand (M3-D26).

        Kein Konflikt, keine zweite Join-Zeile - und ausdruecklich auch
        kein zweites Ereignis: ein Consumer soll nicht zaehlen, wie oft
        jemand auf denselben Knopf getippt hat.
        """
        o = ort(client, paar)
        z = ziel(client, paar, slug)
        pfad = relation_pfad(paar, slug, o["id"], z["id"])

        assert client.put(pfad, headers=auth(paar["token_a"])).status_code == 204
        assert client.put(pfad, headers=auth(paar["token_b"])).status_code == 204

        session.expire_all()
        assert zaehle(session, join_modell) == 1

    @pytest.mark.parametrize(("slug", "join_modell", "original"), ARTEN)
    def test_mehrere_orte_duerfen_dasselbe_ziel_tragen(  # type: ignore[no-untyped-def]
        self, client, session, paar, slug, join_modell, original
    ) -> None:
        erster = ort(client, paar)
        zweiter = ort(client, paar)
        z = ziel(client, paar, slug)

        for o in (erster, zweiter):
            assert (
                client.put(
                    relation_pfad(paar, slug, o["id"], z["id"]), headers=auth(paar["token_a"])
                ).status_code
                == 204
            )

        session.expire_all()
        assert zaehle(session, join_modell) == 2


class TestZielAbweisung:
    """Vier Sachverhalte, eine Antwort (M3-D09)."""

    @pytest.mark.parametrize(("slug", "join_modell", "original"), ARTEN)
    def test_unbekanntes_ziel_ist_404(  # type: ignore[no-untyped-def]
        self, client, paar, slug, join_modell, original
    ) -> None:
        o = ort(client, paar)
        antwort = client.put(
            relation_pfad(paar, slug, o["id"], uuid4()), headers=auth(paar["token_a"])
        )
        assert antwort.status_code == 404
        assert antwort.json()["code"] == "RELATION_TARGET_NOT_FOUND"

    @pytest.mark.parametrize(("slug", "join_modell", "original"), ARTEN)
    def test_ziel_aus_fremdem_space_ist_404(  # type: ignore[no-untyped-def]
        self, client, paar, slug, join_modell, original
    ) -> None:
        """Und zwar mit demselben Code wie ein unbekanntes Ziel.

        Ein eigener Cross-Space-Code ist ausdruecklich ausgeschlossen: er
        wuerde bestaetigen, dass die ID irgendwo existiert.
        """
        o = ort(client, paar)
        fremdes = ziel(client, paar, slug, token_key="token_fremd", space=paar["fremder_space"])

        antwort = client.put(
            relation_pfad(paar, slug, o["id"], fremdes["id"]), headers=auth(paar["token_a"])
        )
        assert antwort.status_code == 404
        assert antwort.json()["code"] == "RELATION_TARGET_NOT_FOUND"

    @pytest.mark.parametrize(("slug", "join_modell", "original"), ARTEN)
    def test_geloeschtes_ziel_ist_404(  # type: ignore[no-untyped-def]
        self, client, paar, slug, join_modell, original
    ) -> None:
        o = ort(client, paar)
        z = ziel(client, paar, slug)
        entfernt = client.delete(
            f"/api/v1/spaces/{paar['space'].id}/{slug}/{z['id']}",
            headers={**auth(paar["token_a"]), "If-Match": '"1"'},
        )
        assert entfernt.status_code == 204

        antwort = client.put(
            relation_pfad(paar, slug, o["id"], z["id"]), headers=auth(paar["token_a"])
        )
        assert antwort.status_code == 404
        assert antwort.json()["code"] == "RELATION_TARGET_NOT_FOUND"

    @pytest.mark.parametrize(("slug", "join_modell", "original"), ARTEN)
    def test_unbekannter_ort_ist_404(  # type: ignore[no-untyped-def]
        self, client, paar, slug, join_modell, original
    ) -> None:
        z = ziel(client, paar, slug)
        antwort = client.put(
            relation_pfad(paar, slug, uuid4(), z["id"]), headers=auth(paar["token_a"])
        )
        assert antwort.status_code == 404
        assert antwort.json()["code"] == "PLACE_NOT_FOUND"

    @pytest.mark.parametrize(("slug", "join_modell", "original"), ARTEN)
    def test_fremder_darf_nicht_verknuepfen(  # type: ignore[no-untyped-def]
        self, client, paar, slug, join_modell, original
    ) -> None:
        o = ort(client, paar)
        z = ziel(client, paar, slug)
        antwort = client.put(
            relation_pfad(paar, slug, o["id"], z["id"]), headers=auth(paar["token_fremd"])
        )
        assert antwort.status_code == 404

    @pytest.mark.parametrize(("slug", "join_modell", "original"), ARTEN)
    def test_nicht_vorhandene_relation_loesen_ist_404(  # type: ignore[no-untyped-def]
        self, client, paar, slug, join_modell, original
    ) -> None:
        o = ort(client, paar)
        z = ziel(client, paar, slug)
        antwort = client.delete(
            relation_pfad(paar, slug, o["id"], z["id"]), headers=auth(paar["token_a"])
        )
        assert antwort.status_code == 404
        assert antwort.json()["code"] == "RELATION_NOT_FOUND"


class TestHeartMomentPrivacy:
    """Die Zusicherungen, die nur den HeartMoment betreffen (M3-D09)."""

    def test_privates_ziel_ist_404_auch_fuer_den_eigentuemer(self, client, paar) -> None:  # type: ignore[no-untyped-def]
        """Lesbar heisst nicht relationierbar.

        Anna darf ihren eigenen privaten Moment lesen. Verknuepfen darf
        sie ihn trotzdem nicht: die Relation waere gemeinsamer Inhalt und
        damit fuer Ben ein Beweis, dass es den Moment gibt.
        """
        o = ort(client, paar)
        privat = ziel(client, paar, "heart-moments", visibility="PRIVATE")

        lesbar = client.get(
            f"/api/v1/spaces/{paar['space'].id}/heart-moments/{privat['id']}",
            headers=auth(paar["token_a"]),
        )
        assert lesbar.status_code == 200

        antwort = client.put(
            relation_pfad(paar, "heart-moments", o["id"], privat["id"]),
            headers=auth(paar["token_a"]),
        )
        assert antwort.status_code == 404
        assert antwort.json()["code"] == "RELATION_TARGET_NOT_FOUND"

    def test_wechsel_auf_privat_entfernt_relationen(self, client, session, paar) -> None:  # type: ignore[no-untyped-def]
        o = ort(client, paar)
        moment = ziel(client, paar, "heart-moments")
        assert (
            client.put(
                relation_pfad(paar, "heart-moments", o["id"], moment["id"]),
                headers=auth(paar["token_a"]),
            ).status_code
            == 204
        )

        gewechselt = client.patch(
            f"/api/v1/spaces/{paar['space'].id}/heart-moments/{moment['id']}/visibility",
            json={"visibility": "PRIVATE"},
            headers={**auth(paar["token_a"]), "If-Match": '"1"'},
        )
        assert gewechselt.status_code == 200

        session.expire_all()
        assert zaehle(session, PlaceHeartMoment) == 0
        # Der Moment selbst bleibt - nur seine gemeinsame Sichtbarkeit ist weg.
        assert session.get(HeartMoment, UUID(moment["id"])) is not None

    def test_wechsel_zurueck_rekonstruiert_nichts(self, client, session, paar) -> None:  # type: ignore[no-untyped-def]
        o = ort(client, paar)
        moment = ziel(client, paar, "heart-moments")
        client.put(
            relation_pfad(paar, "heart-moments", o["id"], moment["id"]),
            headers=auth(paar["token_a"]),
        )
        client.patch(
            f"/api/v1/spaces/{paar['space'].id}/heart-moments/{moment['id']}/visibility",
            json={"visibility": "PRIVATE"},
            headers={**auth(paar["token_a"]), "If-Match": '"1"'},
        )
        zurueck = client.patch(
            f"/api/v1/spaces/{paar['space'].id}/heart-moments/{moment['id']}/visibility",
            json={"visibility": "SHARED"},
            headers={**auth(paar["token_a"]), "If-Match": '"2"'},
        )
        assert zurueck.status_code == 200

        session.expire_all()
        assert zaehle(session, PlaceHeartMoment) == 0

    def test_datenbank_haelt_die_regel_auch_ohne_die_fachlogik(  # type: ignore[no-untyped-def]
        self, client, session, paar
    ) -> None:
        """Der Riegel unter dem Dienst.

        Hier wird die Privacy-Klasse absichtlich an der Fachlogik vorbei
        umgeschrieben - so, wie es ein spaeterer Codepfad tun koennte, der
        M3-D09 nicht kennt. Der Fremdschluessel zieht die neue Klasse in
        die Join-Zeile, und deren CHECK bricht ab. Der Zustand "privat,
        aber ueber eine gemeinsame Relation beweisbar" ist damit nicht
        formulierbar.
        """
        from sqlalchemy import update
        from sqlalchemy.exc import IntegrityError

        o = ort(client, paar)
        moment = ziel(client, paar, "heart-moments")
        client.put(
            relation_pfad(paar, "heart-moments", o["id"], moment["id"]),
            headers=auth(paar["token_a"]),
        )
        session.expire_all()
        assert zaehle(session, PlaceHeartMoment) == 1

        with pytest.raises(IntegrityError):
            session.execute(
                update(HeartMoment)
                .where(HeartMoment.id == UUID(moment["id"]))
                .values(privacy_class="OWNER_ONLY")
            )
            session.flush()
        session.rollback()


class TestKeineOriginalCascade:
    """M3-D12: source-bound. Relationen loesen, Originale behalten."""

    @pytest.mark.parametrize(("slug", "join_modell", "original"), ARTEN)
    def test_place_delete_entfernt_nur_die_verknuepfung(  # type: ignore[no-untyped-def]
        self, client, session, paar, slug, join_modell, original
    ) -> None:
        o = ort(client, paar)
        z = ziel(client, paar, slug)
        client.put(relation_pfad(paar, slug, o["id"], z["id"]), headers=auth(paar["token_a"]))

        geloescht = client.delete(
            f"/api/v1/spaces/{paar['space'].id}/places/{o['id']}",
            headers={**auth(paar["token_a"]), "If-Match": '"1"'},
        )
        assert geloescht.status_code == 204

        session.expire_all()
        assert zaehle(session, join_modell) == 0
        # Das Original ist unveraendert lesbar.
        weiterhin = client.get(
            f"/api/v1/spaces/{paar['space'].id}/{slug}/{z['id']}",
            headers=auth(paar["token_a"]),
        )
        assert weiterhin.status_code == 200
        assert session.get(original, UUID(z["id"])) is not None

    @pytest.mark.parametrize(("slug", "join_modell", "original"), ARTEN)
    def test_ziel_delete_entfernt_nur_die_verknuepfung(  # type: ignore[no-untyped-def]
        self, client, session, paar, slug, join_modell, original
    ) -> None:
        o = ort(client, paar)
        z = ziel(client, paar, slug)
        client.put(relation_pfad(paar, slug, o["id"], z["id"]), headers=auth(paar["token_a"]))

        geloescht = client.delete(
            f"/api/v1/spaces/{paar['space'].id}/{slug}/{z['id']}",
            headers={**auth(paar["token_a"]), "If-Match": '"1"'},
        )
        assert geloescht.status_code == 204

        session.expire_all()
        assert zaehle(session, join_modell) == 0
        # Der Ort bleibt.
        assert (
            client.get(
                f"/api/v1/spaces/{paar['space'].id}/places/{o['id']}",
                headers=auth(paar["token_a"]),
            ).status_code
            == 200
        )
