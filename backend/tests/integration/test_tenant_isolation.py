"""Tenant Isolation - die zentrale Sicherheitsinvariante.

Die Matrix aus docs/SECURITY.md:

    Account A auf Space A (Mitglied)          erlaubt
    Account B auf Space A (Mitglied)          erlaubt
    Account C auf Space B, greift auf Space A niemals
    anonym                                    niemals

Geprueft wird ueber HTTP mit echten Token, nicht gegen die Guard-Funktion.
Ein Direktaufruf ueberspringt genau den Weg, auf dem eine Pruefung
vergessen werden kann.
"""

from __future__ import annotations

import pytest
from sqlalchemy.orm import Session

from sidebyside.core.errors import NotFoundError
from sidebyside.relationship import service
from sidebyside.relationship.models import MembershipStatus
from tests.conftest import auth, make_account, make_space, requires_database, sign_in

pytestmark = [pytest.mark.integration, requires_database]


@pytest.fixture
def paar(session: Session):  # type: ignore[no-untyped-def]
    """Zwei Partner in einem Space und ein Fremder mit eigenem Space."""
    a = make_account(session, "Anna")
    b = make_account(session, "Ben")
    fremd = make_account(session, "Fremde Person")

    space = make_space(session, a)
    service.add_member(session, space.id, b)
    make_space(session, fremd)
    session.flush()

    return {
        "a": a,
        "b": b,
        "fremd": fremd,
        "space": space,
        "token_a": sign_in(session, a),
        "token_b": sign_in(session, b),
        "token_fremd": sign_in(session, fremd),
    }


class TestErlaubterZugriff:
    def test_mitglied_a_sieht_den_space(self, client, paar) -> None:  # type: ignore[no-untyped-def]
        antwort = client.get(f"/api/v1/spaces/{paar['space'].id}", headers=auth(paar["token_a"]))
        assert antwort.status_code == 200
        assert antwort.json()["id"] == str(paar["space"].id)

    def test_mitglied_b_sieht_denselben_space(self, client, paar) -> None:  # type: ignore[no-untyped-def]
        antwort = client.get(f"/api/v1/spaces/{paar['space'].id}", headers=auth(paar["token_b"]))
        assert antwort.status_code == 200

    def test_beide_partner_erscheinen(self, client, paar) -> None:  # type: ignore[no-untyped-def]
        antwort = client.get(f"/api/v1/spaces/{paar['space'].id}", headers=auth(paar["token_a"]))
        namen = {p["displayName"] for p in antwort.json()["partners"]}
        assert namen == {"Anna", "Ben"}


class TestFremderZugriff:
    def test_fremder_bekommt_404_und_nicht_403(self, client, paar) -> None:  # type: ignore[no-untyped-def]
        """Ein 403 wuerde bestaetigen, dass es den Space gibt."""
        antwort = client.get(
            f"/api/v1/spaces/{paar['space'].id}", headers=auth(paar["token_fremd"])
        )
        assert antwort.status_code == 404
        assert antwort.json()["code"] == "SPACE_NOT_FOUND"

    def test_fremder_space_ist_von_einem_erfundenen_nicht_zu_unterscheiden(
        self, client, paar
    ) -> None:  # type: ignore[no-untyped-def]
        """Aus dem Unterschied liesse sich sonst eine Existenzauskunft bauen."""
        from sidebyside.core.ids import new_id

        echt = client.get(f"/api/v1/spaces/{paar['space'].id}", headers=auth(paar["token_fremd"]))
        erfunden = client.get(f"/api/v1/spaces/{new_id()}", headers=auth(paar["token_fremd"]))
        assert echt.status_code == erfunden.status_code == 404
        assert echt.json() == erfunden.json()

    def test_keine_inhalte_in_der_abweisung(self, client, paar) -> None:  # type: ignore[no-untyped-def]
        rohtext = client.get(
            f"/api/v1/spaces/{paar['space'].id}", headers=auth(paar["token_fremd"])
        ).text
        for verboten in ["Anna", "Ben", str(paar["a"].id), str(paar["b"].id)]:
            assert verboten not in rohtext


class TestAnonymerZugriff:
    def test_ohne_kopf_kein_zugriff(self, client, paar) -> None:  # type: ignore[no-untyped-def]
        antwort = client.get(f"/api/v1/spaces/{paar['space'].id}")
        assert antwort.status_code == 401

    @pytest.mark.parametrize(
        "kopf",
        [
            {"Authorization": ""},
            {"Authorization": "Bearer"},
            {"Authorization": "Bearer "},
            {"Authorization": "Basic abc"},
            {"Authorization": "abc"},
            {"Authorization": "Bearer nicht-echt"},
        ],
    )
    def test_unbrauchbarer_kopf_kein_zugriff(self, client, paar, kopf) -> None:  # type: ignore[no-untyped-def]
        antwort = client.get(f"/api/v1/spaces/{paar['space'].id}", headers=kopf)
        assert antwort.status_code == 401


class TestFehlgeformteIds:
    @pytest.mark.parametrize(
        "boese",
        [
            "nicht-echt",
            "12345",
            "' OR 1=1 --",
            "00000000-0000-0000-0000-000000000000",
            "%2e%2e",
        ],
    )
    def test_router_match_bleibt_fachliche_privacy_404(self, client, paar, boese: str) -> None:  # type: ignore[no-untyped-def]
        """Wohlgeformtheit darf bei gematchter Route keine Existenzauskunft liefern."""
        antwort = client.get(f"/api/v1/spaces/{boese}", headers=auth(paar["token_a"]))
        assert antwort.status_code == 404
        assert antwort.json()["code"] == "SPACE_NOT_FOUND"

    def test_zusaetzliches_pfadsegment_wird_framework_404(self, client, paar) -> None:  # type: ignore[no-untyped-def]
        """Ein Route-Miss unter /api/v1 bleibt im ProblemDetails-Vertrag."""
        antwort = client.get(
            "/api/v1/spaces/nicht-echt/unerwartetes-segment",
            headers=auth(paar["token_a"]),
        )
        assert antwort.status_code == 404
        assert antwort.json() == {
            "type": "not_found",
            "title": "Not found",
            "status": 404,
            "detail": "Not Found",
            "code": "HTTP_404",
        }


class TestBeendeteMitgliedschaft:
    def test_wer_gegangen_ist_sieht_nichts_mehr(self, client, session, paar) -> None:  # type: ignore[no-untyped-def]
        mitgliedschaft = service.require_membership(session, paar["b"], paar["space"].id)
        service.end_membership(mitgliedschaft)
        session.flush()

        antwort = client.get(f"/api/v1/spaces/{paar['space'].id}", headers=auth(paar["token_b"]))
        assert antwort.status_code == 404

    def test_der_verbleibende_partner_behaelt_zugriff(self, client, session, paar) -> None:  # type: ignore[no-untyped-def]
        mitgliedschaft = service.require_membership(session, paar["b"], paar["space"].id)
        service.end_membership(mitgliedschaft, removed=True)
        session.flush()

        antwort = client.get(f"/api/v1/spaces/{paar['space'].id}", headers=auth(paar["token_a"]))
        assert antwort.status_code == 200
        assert [p["displayName"] for p in antwort.json()["partners"]] == ["Anna"]


class TestGuardDirekt:
    def test_fremder_space_wirft_notfound(self, session: Session, paar) -> None:  # type: ignore[no-untyped-def]
        with pytest.raises(NotFoundError):
            service.require_membership(session, paar["fremd"], paar["space"].id)

    def test_mitglied_bekommt_die_mitgliedschaft(self, session: Session, paar) -> None:  # type: ignore[no-untyped-def]
        mitgliedschaft = service.require_membership(session, paar["a"], paar["space"].id)
        assert mitgliedschaft.status == MembershipStatus.ACTIVE.value
        assert mitgliedschaft.space_id == paar["space"].id


class TestObergrenze:
    def test_ein_dritter_partner_wird_abgewiesen(self, session: Session, paar) -> None:  # type: ignore[no-untyped-def]
        """Ein Paar-Space hat hoechstens zwei aktive Partner."""
        from sidebyside.core.errors import ConflictError

        dritter = make_account(session, "Dritte Person")
        with pytest.raises(ConflictError) as fehler:
            service.add_member(session, paar["space"].id, dritter)
        assert fehler.value.code == "SPACE_FULL"

    def test_ein_bestehendes_mitglied_kommt_nicht_doppelt_hinein(
        self, session: Session, paar
    ) -> None:  # type: ignore[no-untyped-def]
        from sidebyside.core.errors import ConflictError

        with pytest.raises(ConflictError) as fehler:
            service.add_member(session, paar["space"].id, paar["b"])
        assert fehler.value.code == "ACCOUNT_ALREADY_MEMBER"

    def test_nach_dem_gehen_ist_wieder_platz(self, session: Session, paar) -> None:  # type: ignore[no-untyped-def]
        mitgliedschaft = service.require_membership(session, paar["b"], paar["space"].id)
        service.end_membership(mitgliedschaft)
        session.flush()

        dritter = make_account(session, "Dritte Person")
        neu = service.add_member(session, paar["space"].id, dritter)
        assert neu.is_active


class TestKeineAnmeldedaten:
    def test_die_antwort_traegt_nur_die_whitelist(self, client, paar) -> None:  # type: ignore[no-untyped-def]
        """Am Account haengen Anmeldedaten und Kontaktangaben."""
        antwort = client.get(f"/api/v1/spaces/{paar['space'].id}", headers=auth(paar["token_a"]))
        for partner in antwort.json()["partners"]:
            assert set(partner) == {"id", "displayName"}

        rohtext = antwort.text
        for verboten in ["secret", "token", "hash", "email", "birthday", "locale"]:
            assert verboten not in rohtext.lower()
