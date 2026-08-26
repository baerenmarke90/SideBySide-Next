"""PostgreSQL-/HTTP-Abnahme fuer die Story-Zeitleiste.

Die Zeitleiste ist die Stelle, an der alle vier M2-Typen zusammenkommen -
und damit die Stelle, an der ein Privacy-Fehler am teuersten waere: ein
privater HeartMoment in einer gemeinsamen Liste ist nicht wiedergutzumachen.
Deshalb pruefen diese Tests die Abwesenheit privater Zeilen aus beiden
Richtungen: der Partner darf sie nicht sehen, und der Owner auch nicht.
"""

from __future__ import annotations

import pytest
from sqlalchemy import text
from sqlalchemy.orm import Session

from sidebyside.relationship import service as relationship_service
from tests.conftest import auth, make_account, make_space, requires_database, sign_in

pytestmark = [pytest.mark.integration, requires_database]


@pytest.fixture
def paar(session: Session):  # type: ignore[no-untyped-def]
    anna = make_account(session, "Anna")
    ben = make_account(session, "Ben")
    fremd = make_account(session, "Fremd")
    space = make_space(session, anna)
    relationship_service.add_member(session, space.id, ben)
    beta = make_space(session, fremd)
    session.flush()
    return {
        "anna": anna,
        "ben": ben,
        "space": space,
        "beta": beta,
        "token_a": sign_in(session, anna),
        "token_b": sign_in(session, ben),
        "token_f": sign_in(session, fremd),
    }


def basis(space_id: object) -> str:
    return f"/api/v1/spaces/{space_id}"


def memory(client, paar, *, titel="M", happened_on="2025-06-13", token=None):  # type: ignore[no-untyped-def]
    rumpf = {"title": titel, "body": "B"}
    if happened_on is not None:
        rumpf["happenedOn"] = happened_on
    antwort = client.post(
        f"{basis(paar['space'].id)}/memories",
        json=rumpf,
        headers=auth(token or paar["token_a"]),
    )
    assert antwort.status_code == 201, antwort.text
    return antwort.json()


def milestone(client, paar, *, titel="MS", happened_on="2025-06-13", token=None):  # type: ignore[no-untyped-def]
    antwort = client.post(
        f"{basis(paar['space'].id)}/milestones",
        json={"title": titel, "happenedOn": happened_on},
        headers=auth(token or paar["token_a"]),
    )
    assert antwort.status_code == 201, antwort.text
    return antwort.json()


def heart_moment(client, paar, *, visibility="SHARED", happened_on="2025-06-13", token=None):  # type: ignore[no-untyped-def]
    antwort = client.post(
        f"{basis(paar['space'].id)}/heart-moments",
        json={
            "text": "Danke",
            "emotion": "LOVED",
            "visibility": visibility,
            "happenedOn": happened_on,
        },
        headers=auth(token or paar["token_a"]),
    )
    assert antwort.status_code == 201, antwort.text
    return antwort.json()


def timeline(client, paar, *, token=None, **parameter):  # type: ignore[no-untyped-def]
    antwort = client.get(
        f"{basis(paar['space'].id)}/timeline",
        params=parameter,
        headers=auth(token or paar["token_a"]),
    )
    return antwort


def ids(antwort) -> list[str]:  # type: ignore[no-untyped-def]
    schluessel = {"MEMORY": "memory", "HEART_MOMENT": "heartMoment", "MILESTONE": "milestone"}
    return [eintrag[schluessel[eintrag["kind"]]]["id"] for eintrag in antwort.json()["items"]]


class TestPrivacy:
    def test_privater_heart_moment_fehlt_dem_partner(self, client, paar) -> None:  # type: ignore[no-untyped-def]
        privat = heart_moment(client, paar, visibility="PRIVATE")
        assert privat["id"] not in ids(timeline(client, paar, token=paar["token_b"]))

    def test_privater_heart_moment_fehlt_auch_dem_owner(self, client, paar) -> None:  # type: ignore[no-untyped-def]
        """M2-D22: die Story ist gemeinsamer Inhalt, kein persoenlicher Verlauf.

        Der Owner sieht seinen privaten Eintrag in seiner eigenen Liste -
        aber nicht hier. Sonst waeren zwei Ergebnismengen unter einer Route.
        """
        privat = heart_moment(client, paar, visibility="PRIVATE")
        assert privat["id"] not in ids(timeline(client, paar, token=paar["token_a"]))

    def test_owner_findet_den_eintrag_in_seiner_eigenen_liste(self, client, paar) -> None:  # type: ignore[no-untyped-def]
        privat = heart_moment(client, paar, visibility="PRIVATE")
        antwort = client.get(
            f"{basis(paar['space'].id)}/heart-moments",
            params={"visibility": "PRIVATE"},
            headers=auth(paar["token_a"]),
        )
        assert [eintrag["id"] for eintrag in antwort.json()["items"]] == [privat["id"]]

    def test_wechsel_auf_privat_entfernt_das_item(self, client, paar) -> None:  # type: ignore[no-untyped-def]
        geteilt = heart_moment(client, paar, visibility="SHARED")
        assert geteilt["id"] in ids(timeline(client, paar))

        client.patch(
            f"{basis(paar['space'].id)}/heart-moments/{geteilt['id']}/visibility",
            json={"visibility": "PRIVATE"},
            headers={**auth(paar["token_a"]), "If-Match": f'"{geteilt["version"]}"'},
        )
        assert geteilt["id"] not in ids(timeline(client, paar))
        assert geteilt["id"] not in ids(timeline(client, paar, token=paar["token_b"]))

    def test_fremder_space_liefert_nichts(self, client, paar) -> None:  # type: ignore[no-untyped-def]
        memory(client, paar)
        antwort = client.get(
            f"{basis(paar['beta'].id)}/timeline",
            headers=auth(paar["token_a"]),
        )
        assert antwort.status_code == 404

    def test_visibility_ist_kein_parameter(self, client, paar) -> None:  # type: ignore[no-untyped-def]
        """M2-D22: ein mitgesendeter Wert darf nicht still gefiltert werden."""
        heart_moment(client, paar, visibility="PRIVATE")
        antwort = timeline(client, paar, visibility="PRIVATE")
        assert ids(antwort) == []


class TestSortierung:
    def test_effective_date_faellt_auf_created_at_zurueck(self, client, paar) -> None:  # type: ignore[no-untyped-def]
        """M2-D08: eine Memory ohne happenedOn verschwindet nicht."""
        ohne_datum = memory(client, paar, happened_on=None)
        eintraege = timeline(client, paar).json()["items"]
        passend = [e for e in eintraege if e["memory"]["id"] == ohne_datum["id"]]
        assert len(passend) == 1
        assert passend[0]["effectiveDate"] == ohne_datum["createdAt"][:10]

    def test_absteigend_ist_der_standard(self, client, paar) -> None:  # type: ignore[no-untyped-def]
        alt = memory(client, paar, titel="alt", happened_on="2024-01-01")
        neu = memory(client, paar, titel="neu", happened_on="2026-01-01")
        assert ids(timeline(client, paar))[:2] == [neu["id"], alt["id"]]

    def test_aufsteigend_dreht_den_vollstaendigen_schluessel(self, client, paar) -> None:  # type: ignore[no-untyped-def]
        alt = memory(client, paar, titel="alt", happened_on="2024-01-01")
        neu = memory(client, paar, titel="neu", happened_on="2026-01-01")
        assert ids(timeline(client, paar, order="ASC"))[:2] == [alt["id"], neu["id"]]

    def test_kind_rank_entscheidet_bei_identischem_zeitstempel(self, client, paar, session) -> None:  # type: ignore[no-untyped-def]
        """MEMORY=1, HEART_MOMENT=2, MILESTONE=3 (M2-D08).

        Der Rang entscheidet erst, wenn `effectiveDate` **und** `createdAt`
        gleich sind. Nacheinander erzeugte Eintraege haben verschiedene
        Zeitstempel - dieser Test erzwingt die Kollision, sonst pruefte er
        den Tie-Breaker gar nicht.
        """
        m = memory(client, paar, happened_on="2025-06-13")
        h = heart_moment(client, paar, happened_on="2025-06-13")
        ms = milestone(client, paar, happened_on="2025-06-13")

        gleich = "2025-06-13 08:00:00+00"
        for tabelle, eintrag in (
            ("memories", m),
            ("heart_moments", h),
            ("milestones", ms),
        ):
            session.execute(
                text(f"UPDATE {tabelle} SET created_at = :wert WHERE id = :id"),
                {"wert": gleich, "id": eintrag["id"]},
            )
        session.flush()

        assert ids(timeline(client, paar, order="ASC")) == [m["id"], h["id"], ms["id"]]
        assert ids(timeline(client, paar)) == [ms["id"], h["id"], m["id"]]

    def test_id_bricht_den_letzten_gleichstand(self, client, paar, session) -> None:  # type: ignore[no-untyped-def]
        """Gleiche Werte in allen drei ersten Schluesseln, gleicher Typ."""
        erste = memory(client, paar, happened_on="2025-06-13")
        zweite = memory(client, paar, happened_on="2025-06-13")
        session.execute(
            text("UPDATE memories SET created_at = :wert WHERE id IN (:a, :b)"),
            {"wert": "2025-06-13 08:00:00+00", "a": erste["id"], "b": zweite["id"]},
        )
        session.flush()

        aufsteigend = ids(timeline(client, paar, order="ASC"))
        assert aufsteigend == sorted([erste["id"], zweite["id"]])
        assert ids(timeline(client, paar)) == list(reversed(aufsteigend))


class TestFilter:
    def test_type_verengt_die_menge(self, client, paar) -> None:  # type: ignore[no-untyped-def]
        m = memory(client, paar)
        milestone(client, paar)
        assert ids(timeline(client, paar, type=["MEMORY"])) == [m["id"]]

    def test_type_ist_wiederholbar(self, client, paar) -> None:  # type: ignore[no-untyped-def]
        m = memory(client, paar)
        ms = milestone(client, paar)
        heart_moment(client, paar)
        assert set(ids(timeline(client, paar, type=["MEMORY", "MILESTONE"]))) == {
            m["id"],
            ms["id"],
        }

    def test_year_filtert_auf_das_effektive_datum(self, client, paar) -> None:  # type: ignore[no-untyped-def]
        alt = memory(client, paar, happened_on="2024-05-05")
        memory(client, paar, happened_on="2026-05-05")
        assert ids(timeline(client, paar, year=2024)) == [alt["id"]]

    def test_year_ausserhalb_des_bereichs_wird_abgewiesen(self, client, paar) -> None:  # type: ignore[no-untyped-def]
        assert timeline(client, paar, year=1800).status_code == 422


class TestPagination:
    def test_seiten_sind_luecken_und_duplikatfrei(self, client, paar) -> None:  # type: ignore[no-untyped-def]
        erwartet = [memory(client, paar, titel=f"M{i}")["id"] for i in range(5)]
        erwartet += [milestone(client, paar, titel=f"MS{i}")["id"] for i in range(4)]

        gesammelt: list[str] = []
        cursor = None
        for _ in range(10):
            antwort = timeline(client, paar, limit=2, **({"cursor": cursor} if cursor else {}))
            gesammelt += ids(antwort)
            cursor = antwort.json()["nextCursor"]
            if cursor is None:
                break
        assert sorted(gesammelt) == sorted(erwartet)
        assert len(gesammelt) == len(set(gesammelt))

    def test_limit_darf_zwischen_seiten_wechseln(self, client, paar) -> None:  # type: ignore[no-untyped-def]
        """Der Cursor ist nicht an die Seitengroesse gebunden."""
        for i in range(6):
            memory(client, paar, titel=f"M{i}")
        erste = timeline(client, paar, limit=2)
        zweite = timeline(client, paar, limit=4, cursor=erste.json()["nextCursor"])
        assert set(ids(erste)) & set(ids(zweite)) == set()
        assert len(ids(zweite)) == 4

    def test_cursor_aus_anderem_filter_wird_abgewiesen(self, client, paar) -> None:  # type: ignore[no-untyped-def]
        for i in range(4):
            memory(client, paar, titel=f"M{i}")
        cursor = timeline(client, paar, limit=2).json()["nextCursor"]
        antwort = timeline(client, paar, limit=2, cursor=cursor, type=["MEMORY"])
        assert antwort.status_code == 400
        assert antwort.json()["code"] == "INVALID_CURSOR"

    def test_cursor_aus_anderer_richtung_wird_abgewiesen(self, client, paar) -> None:  # type: ignore[no-untyped-def]
        for i in range(4):
            memory(client, paar, titel=f"M{i}")
        cursor = timeline(client, paar, limit=2).json()["nextCursor"]
        assert timeline(client, paar, limit=2, cursor=cursor, order="ASC").status_code == 400

    def test_manipulierter_cursor_wird_abgewiesen(self, client, paar) -> None:  # type: ignore[no-untyped-def]
        for i in range(4):
            memory(client, paar, titel=f"M{i}")
        cursor = timeline(client, paar, limit=2).json()["nextCursor"]
        antwort = timeline(client, paar, limit=2, cursor=cursor[:-2] + "xy")
        assert antwort.status_code == 400
        assert "spaceId" not in antwort.text


class TestProjektion:
    def test_memory_traegt_autor_und_galerie(self, client, paar) -> None:  # type: ignore[no-untyped-def]
        memory(client, paar)
        eintrag = timeline(client, paar).json()["items"][0]
        assert eintrag["kind"] == "MEMORY"
        assert eintrag["memory"]["author"]["displayName"] == "Anna"
        assert eintrag["memory"]["attachments"] == []

    def test_capabilities_folgen_der_autorregel(self, client, paar) -> None:  # type: ignore[no-untyped-def]
        memory(client, paar, token=paar["token_a"])
        fuer_autor = timeline(client, paar, token=paar["token_a"]).json()["items"][0]
        fuer_partner = timeline(client, paar, token=paar["token_b"]).json()["items"][0]
        assert fuer_autor["memory"]["capabilities"]["canEdit"] is True
        assert fuer_partner["memory"]["capabilities"]["canEdit"] is False

    def test_kein_memory_body_in_der_liste(self, client, paar) -> None:  # type: ignore[no-untyped-def]
        """Die Karte braucht eine Ueberschrift, nicht den ganzen Text."""
        memory(client, paar)
        assert "body" not in timeline(client, paar).json()["items"][0]["memory"]
