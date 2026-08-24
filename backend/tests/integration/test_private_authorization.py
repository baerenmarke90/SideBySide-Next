"""Owner- und Privacy-Isolation ueber HTTP gegen echtes PostgreSQL.

Die Matrix aus docs/SECURITY.md, um die Eigentuemerfrage erweitert:

    Eigentuemer auf eigene OWNER_ONLY-Zeile       erlaubt, auch aendernd
    Partner im selben Space auf OWNER_ONLY        niemals, auf keinem Weg
    Partner auf SPACE_SHARED                      lesend erlaubt
    fremder Space                                 niemals
    anonym                                        niemals

Geprueft wird ueber HTTP mit echten Token. Ein Direktaufruf des Guards
ueberspringt genau den Weg, auf dem eine Pruefung vergessen werden kann.

Die Sonde aus `tests.support.privacy_probe` ist keine Fachdomaene, sondern
die duennste Ressource, an der sich die Grundlage pruefen laesst - siehe
die Begruendung dort.
"""

from __future__ import annotations

import pytest
from sqlalchemy import Engine, event
from sqlalchemy.orm import Session

from sidebyside.authorization import PrivacyClass
from sidebyside.core.ids import new_id
from sidebyside.relationship import service
from tests.conftest import auth, make_account, make_space, requires_database, sign_in
from tests.support.privacy_probe import PrivacyProbe

pytestmark = [pytest.mark.integration, requires_database]

CANARY_ANNA = "CANARY-PRIVATE-ANNA-7421"
CANARY_BEN = "CANARY-PRIVATE-BEN-7422"
CANARY_FREMD = "CANARY-PRIVATE-CAROL-7423"


def _sonde(
    session: Session, *, space_id, owner_id, privacy_class: PrivacyClass, label: str
) -> PrivacyProbe:  # type: ignore[no-untyped-def]
    sonde = PrivacyProbe(
        space_id=space_id,
        owner_id=owner_id,
        privacy_class=privacy_class.value,
        label=label,
    )
    session.add(sonde)
    session.flush()
    return sonde


@pytest.fixture
def probe_client(session: Session):  # type: ignore[no-untyped-def]
    """Die produktive App mit angehaengtem Sondenrouter.

    Eine eigene App-Instanz: der versionierte OpenAPI-Vertrag der
    Produktion bleibt unberuehrt.
    """
    from fastapi.testclient import TestClient

    from tests.support.privacy_probe_api import create_probe_app

    return TestClient(create_probe_app(session), raise_server_exceptions=False)


@pytest.fixture
def szenario(session: Session):  # type: ignore[no-untyped-def]
    """Zwei Partner in einem Space, eine fremde Person in ihrem eigenen."""
    anna = make_account(session, "Anna")
    ben = make_account(session, "Ben")
    carol = make_account(session, "Carol")

    alpha = make_space(session, anna)
    service.add_member(session, alpha.id, ben)
    beta = make_space(session, carol)
    session.flush()

    return {
        "anna": anna,
        "ben": ben,
        "carol": carol,
        "alpha": alpha,
        "beta": beta,
        "token_anna": sign_in(session, anna),
        "token_ben": sign_in(session, ben),
        "token_carol": sign_in(session, carol),
        "privat_anna": _sonde(
            session,
            space_id=alpha.id,
            owner_id=anna.id,
            privacy_class=PrivacyClass.OWNER_ONLY,
            label=CANARY_ANNA,
        ),
        "privat_ben": _sonde(
            session,
            space_id=alpha.id,
            owner_id=ben.id,
            privacy_class=PrivacyClass.OWNER_ONLY,
            label=CANARY_BEN,
        ),
        "geteilt_anna": _sonde(
            session,
            space_id=alpha.id,
            owner_id=anna.id,
            privacy_class=PrivacyClass.SPACE_SHARED,
            label="Gemeinsam von Anna",
        ),
        "privat_carol": _sonde(
            session,
            space_id=beta.id,
            owner_id=carol.id,
            privacy_class=PrivacyClass.OWNER_ONLY,
            label=CANARY_FREMD,
        ),
    }


def _pfad(szenario, sonde: str, raum: str = "alpha") -> str:  # type: ignore[no-untyped-def]
    return f"/api/v1/spaces/{szenario[raum].id}/privacy-probes/{szenario[sonde].id}"


class TestEigentuemer:
    def test_liest_die_eigene_private_zeile(self, probe_client, szenario) -> None:  # type: ignore[no-untyped-def]
        antwort = probe_client.get(
            _pfad(szenario, "privat_anna"), headers=auth(szenario["token_anna"])
        )
        assert antwort.status_code == 200
        assert antwort.json()["label"] == CANARY_ANNA
        assert antwort.json()["privacyClass"] == "OWNER_ONLY"

    def test_aendert_die_eigene_private_zeile(self, probe_client, szenario) -> None:  # type: ignore[no-untyped-def]
        antwort = probe_client.patch(
            _pfad(szenario, "privat_anna"),
            headers=auth(szenario["token_anna"]),
            json={"label": "geaendert"},
        )
        assert antwort.status_code == 200
        assert antwort.json()["label"] == "geaendert"

    def test_loescht_die_eigene_private_zeile(self, probe_client, szenario) -> None:  # type: ignore[no-untyped-def]
        pfad = _pfad(szenario, "privat_anna")
        assert probe_client.delete(pfad, headers=auth(szenario["token_anna"])).status_code == 204
        assert probe_client.get(pfad, headers=auth(szenario["token_anna"])).status_code == 404

    def test_sieht_eigenes_und_geteiltes_in_der_liste(self, probe_client, szenario) -> None:  # type: ignore[no-untyped-def]
        antwort = probe_client.get(
            f"/api/v1/spaces/{szenario['alpha'].id}/privacy-probes",
            headers=auth(szenario["token_anna"]),
        )
        assert antwort.status_code == 200
        assert {zeile["label"] for zeile in antwort.json()} == {CANARY_ANNA, "Gemeinsam von Anna"}


class TestPartnerImSelbenSpace:
    """Der Partner ist kein privilegierter Leser. Bei OWNER_ONLY steht er
    Fremden gleich."""

    def test_bekommt_die_private_zeile_nicht_ueber_die_id(self, probe_client, szenario) -> None:  # type: ignore[no-untyped-def]
        antwort = probe_client.get(
            _pfad(szenario, "privat_anna"), headers=auth(szenario["token_ben"])
        )
        assert antwort.status_code == 404
        assert antwort.json()["code"] == "PRIVACY_PROBE_NOT_FOUND"

    def test_echte_und_erfundene_id_sind_nicht_zu_unterscheiden(
        self, probe_client, szenario
    ) -> None:  # type: ignore[no-untyped-def]
        """Aus dem Unterschied liesse sich sonst eine Existenzauskunft bauen."""
        kopf = auth(szenario["token_ben"])
        echt = probe_client.get(_pfad(szenario, "privat_anna"), headers=kopf)
        erfunden = probe_client.get(
            f"/api/v1/spaces/{szenario['alpha'].id}/privacy-probes/{new_id()}", headers=kopf
        )
        assert echt.status_code == erfunden.status_code == 404
        assert echt.json() == erfunden.json()

    @pytest.mark.parametrize(
        "boese",
        ["nicht-echt", "12345", "' OR 1=1 --", "%2e%2e", "00000000-0000-0000-0000-000000000000"],
    )
    def test_auch_eine_fehlgeformte_id_klingt_gleich(
        self, probe_client, szenario, boese: str
    ) -> None:  # type: ignore[no-untyped-def]
        """Fehlgeformt, unbekannt und fremd-privat ergeben dieselbe Antwort."""
        kopf = auth(szenario["token_ben"])
        echt = probe_client.get(_pfad(szenario, "privat_anna"), headers=kopf)
        kaputt = probe_client.get(
            f"/api/v1/spaces/{szenario['alpha'].id}/privacy-probes/{boese}", headers=kopf
        )
        assert kaputt.status_code == 404
        assert kaputt.json() == echt.json()

    @pytest.mark.parametrize("boese", ["../../etc/passwd", "a/b"])
    def test_ein_zerbrochener_pfad_bleibt_ebenfalls_404(
        self, probe_client, szenario, boese: str
    ) -> None:  # type: ignore[no-untyped-def]
        """Ein Schraegstrich trifft keine Route mehr und bekommt deshalb die
        allgemeine 404-Antwort.

        Das ist keine Existenzauskunft: der Unterschied haengt an der Form
        der URL, die der Aufrufer selbst gewaehlt hat, und nicht daran, ob
        es eine Ressource gibt. Wer IDs durchprobiert, lernt daraus nichts.
        """
        antwort = probe_client.get(
            f"/api/v1/spaces/{szenario['alpha'].id}/privacy-probes/{boese}",
            headers=auth(szenario["token_ben"]),
        )
        assert antwort.status_code == 404
        assert CANARY_ANNA not in antwort.text

    def test_die_liste_zeigt_die_private_zeile_des_partners_nicht(
        self, probe_client, szenario
    ) -> None:  # type: ignore[no-untyped-def]
        antwort = probe_client.get(
            f"/api/v1/spaces/{szenario['alpha'].id}/privacy-probes",
            headers=auth(szenario["token_ben"]),
        )
        assert {zeile["label"] for zeile in antwort.json()} == {CANARY_BEN, "Gemeinsam von Anna"}
        assert CANARY_ANNA not in antwort.text

    def test_die_trefferzahl_verraet_sie_auch_nicht(self, probe_client, szenario) -> None:  # type: ignore[no-untyped-def]
        """Eine Zahl ist selbst schon eine Auskunft."""
        antwort = probe_client.get(
            f"/api/v1/spaces/{szenario['alpha'].id}/privacy-probes/count",
            headers=auth(szenario["token_ben"]),
        )
        assert antwort.json()["total"] == 2

    def test_kann_die_private_zeile_nicht_aendern(self, probe_client, session, szenario) -> None:  # type: ignore[no-untyped-def]
        antwort = probe_client.patch(
            _pfad(szenario, "privat_anna"),
            headers=auth(szenario["token_ben"]),
            json={"label": "uebernommen"},
        )
        assert antwort.status_code == 404
        session.refresh(szenario["privat_anna"])
        assert szenario["privat_anna"].label == CANARY_ANNA

    def test_kann_die_private_zeile_nicht_loeschen(self, probe_client, session, szenario) -> None:  # type: ignore[no-untyped-def]
        antwort = probe_client.delete(
            _pfad(szenario, "privat_anna"), headers=auth(szenario["token_ben"])
        )
        assert antwort.status_code == 404
        assert antwort.json()["code"] == "PRIVACY_PROBE_NOT_FOUND"
        session.refresh(szenario["privat_anna"])
        assert szenario["privat_anna"].label == CANARY_ANNA

    def test_darf_geteiltes_lesen(self, probe_client, szenario) -> None:  # type: ignore[no-untyped-def]
        antwort = probe_client.get(
            _pfad(szenario, "geteilt_anna"), headers=auth(szenario["token_ben"])
        )
        assert antwort.status_code == 200
        assert antwort.json()["label"] == "Gemeinsam von Anna"

    def test_darf_geteiltes_des_partners_nicht_aendern(self, probe_client, szenario) -> None:  # type: ignore[no-untyped-def]
        """Hier 403 und nicht 404: die Zeile steht dem Partner ohnehin offen.

        Ein 404 waere kein Schutz, sondern eine Luege ueber etwas, das er
        sich gerade hat anzeigen lassen."""
        antwort = probe_client.patch(
            _pfad(szenario, "geteilt_anna"),
            headers=auth(szenario["token_ben"]),
            json={"label": "uebernommen"},
        )
        assert antwort.status_code == 403
        assert antwort.json()["code"] == "NOT_RESOURCE_OWNER"


class TestFremderSpace:
    def test_kommt_nicht_an_die_sonden_eines_fremden_space(self, probe_client, szenario) -> None:  # type: ignore[no-untyped-def]
        """Der Tenant Guard antwortet zuerst - hier faellt schon der Pfad."""
        antwort = probe_client.get(
            _pfad(szenario, "privat_anna"), headers=auth(szenario["token_carol"])
        )
        assert antwort.status_code == 404
        assert antwort.json()["code"] == "SPACE_NOT_FOUND"

    def test_eine_fremde_id_im_eigenen_space_bleibt_unauffindbar(
        self, probe_client, szenario
    ) -> None:  # type: ignore[no-untyped-def]
        """Die ID existiert wirklich - nur nicht in diesem Space."""
        kopf = auth(szenario["token_anna"])
        fremd = probe_client.get(
            f"/api/v1/spaces/{szenario['alpha'].id}/privacy-probes/{szenario['privat_carol'].id}",
            headers=kopf,
        )
        erfunden = probe_client.get(
            f"/api/v1/spaces/{szenario['alpha'].id}/privacy-probes/{new_id()}", headers=kopf
        )
        assert fremd.status_code == erfunden.status_code == 404
        assert fremd.json() == erfunden.json()

    def test_kein_fremder_inhalt_in_liste_oder_zaehlung(self, probe_client, szenario) -> None:  # type: ignore[no-untyped-def]
        kopf = auth(szenario["token_anna"])
        liste = probe_client.get(
            f"/api/v1/spaces/{szenario['alpha'].id}/privacy-probes", headers=kopf
        )
        zahl = probe_client.get(
            f"/api/v1/spaces/{szenario['alpha'].id}/privacy-probes/count", headers=kopf
        )
        assert CANARY_FREMD not in liste.text
        assert CANARY_BEN not in liste.text
        assert zahl.json()["total"] == 2


class TestAnonym:
    def test_ohne_token_kein_zugriff(self, probe_client, szenario) -> None:  # type: ignore[no-untyped-def]
        assert probe_client.get(_pfad(szenario, "privat_anna")).status_code == 401
        assert (
            probe_client.get(f"/api/v1/spaces/{szenario['alpha'].id}/privacy-probes").status_code
            == 401
        )


class TestFilterInDerAbfrage:
    """Nicht laden und danach ausfiltern.

    Ein Treffer, der entsteht und danach verworfen wird, ist bereits ein
    Leck - er war im Speicher, im Log und in der Antwortgroesse.
    """

    @pytest.fixture
    def abfragen(self, engine: Engine):  # type: ignore[no-untyped-def]
        aufgezeichnet: list[str] = []

        def _mitschreiben(conn, cursor, statement, parameters, context, executemany) -> None:  # type: ignore[no-untyped-def]
            aufgezeichnet.append(statement)

        event.listen(engine, "before_cursor_execute", _mitschreiben)
        try:
            yield aufgezeichnet
        finally:
            event.remove(engine, "before_cursor_execute", _mitschreiben)

    def test_die_private_zeile_wird_gar_nicht_erst_geholt(
        self, probe_client, szenario, abfragen
    ) -> None:  # type: ignore[no-untyped-def]
        abfragen.clear()
        antwort = probe_client.get(
            _pfad(szenario, "privat_anna"), headers=auth(szenario["token_ben"])
        )
        assert antwort.status_code == 404

        sondenabfragen = [sql for sql in abfragen if "privacy_probes" in sql]
        assert sondenabfragen, "Es gab keine Abfrage auf die Sondentabelle."
        for sql in sondenabfragen:
            assert "privacy_class" in sql
            assert "owner_id" in sql
            assert "space_id" in sql

    def test_auch_die_liste_filtert_in_der_datenbank(
        self, probe_client, szenario, abfragen
    ) -> None:  # type: ignore[no-untyped-def]
        abfragen.clear()
        probe_client.get(
            f"/api/v1/spaces/{szenario['alpha'].id}/privacy-probes",
            headers=auth(szenario["token_ben"]),
        )
        sondenabfragen = [sql for sql in abfragen if "privacy_probes" in sql]
        assert sondenabfragen
        for sql in sondenabfragen:
            assert "WHERE" in sql.upper()
            assert "privacy_class" in sql
            assert "owner_id" in sql
