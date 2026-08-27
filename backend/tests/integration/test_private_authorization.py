"""Owner and privacy isolation through HTTP against real PostgreSQL.

The matrix from docs/SECURITY.md, extended with the ownership question:

    Owner on own OWNER_ONLY row                 allowed, including mutation
    Partner in the selben Space on OWNER_ONLY        niemals, on keinem Path
    Partner on SPACE_SHARED                      lesend erlaubt
    foreign Space                                 niemals
    anonymous                                        niemals

Tested is through HTTP with real Token. A Direktaufruf the Guards
ueberspringt exactly the Path, on the a Check vergessen are can.

The probe from `tests.support.privacy_probe` is not a product domain, but
the thinnest resource that can exercise the underlying rule itself; see
the rationale there.
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
    """The produktive App with angehaengtem Sondenrouter.

    A eigene App-Instanz: the versionierte OpenAPI-Contract the
    Produktion remains unberuehrt.
    """
    from fastapi.testclient import TestClient

    from tests.support.privacy_probe_api import create_probe_app

    return TestClient(create_probe_app(session), raise_server_exceptions=False)


@pytest.fixture
def szenario(session: Session):  # type: ignore[no-untyped-def]
    "Zwei Partner in a Space, a fremde Person in ihrem eigenen."
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


def _path(szenario, sonde: str, raum: str = "alpha") -> str:  # type: ignore[no-untyped-def]
    return f"/api/v1/spaces/{szenario[raum].id}/privacy-probes/{szenario[sonde].id}"


class TestEigentuemer:
    def test_reads_the_own_private_row(self, probe_client, szenario) -> None:  # type: ignore[no-untyped-def]
        response = probe_client.get(
            _path(szenario, "privat_anna"), headers=auth(szenario["token_anna"])
        )
        assert response.status_code == 200
        assert response.json()["label"] == CANARY_ANNA
        assert response.json()["privacyClass"] == "OWNER_ONLY"

    def test_changes_the_own_private_row(self, probe_client, szenario) -> None:  # type: ignore[no-untyped-def]
        response = probe_client.patch(
            _path(szenario, "privat_anna"),
            headers=auth(szenario["token_anna"]),
            json={"label": "geaendert"},
        )
        assert response.status_code == 200
        assert response.json()["label"] == "geaendert"

    def test_deletes_the_own_private_row(self, probe_client, szenario) -> None:  # type: ignore[no-untyped-def]
        path = _path(szenario, "privat_anna")
        assert probe_client.delete(path, headers=auth(szenario["token_anna"])).status_code == 204
        assert probe_client.get(path, headers=auth(szenario["token_anna"])).status_code == 404

    def test_sees_own_and_shared_in_the_list(self, probe_client, szenario) -> None:  # type: ignore[no-untyped-def]
        response = probe_client.get(
            f"/api/v1/spaces/{szenario['alpha'].id}/privacy-probes",
            headers=auth(szenario["token_anna"]),
        )
        assert response.status_code == 200
        assert {row["label"] for row in response.json()} == {CANARY_ANNA, "Gemeinsam von Anna"}


class TestPartnerImSelbenSpace:
    """The partner is not a privileged reader. With OWNER_ONLY the resource is
    Foreign same."""

    def test_gets_the_private_row_not_via_the_id(self, probe_client, szenario) -> None:  # type: ignore[no-untyped-def]
        response = probe_client.get(
            _path(szenario, "privat_anna"), headers=auth(szenario["token_ben"])
        )
        assert response.status_code == 404
        assert response.json()["code"] == "PRIVACY_PROBE_NOT_FOUND"

    def test_real_and_invented_id_are_not_to_unterscheiden(self, probe_client, szenario) -> None:  # type: ignore[no-untyped-def]
        "From the Unterschied liesse itself otherwise a Existenzauskunft bauen."
        headers = auth(szenario["token_ben"])
        real = probe_client.get(_path(szenario, "privat_anna"), headers=headers)
        erfunden = probe_client.get(
            f"/api/v1/spaces/{szenario['alpha'].id}/privacy-probes/{new_id()}", headers=headers
        )
        assert real.status_code == erfunden.status_code == 404
        assert real.json() == erfunden.json()

    @pytest.mark.parametrize(
        "boese",
        ["nicht-echt", "12345", "' OR 1=1 --", "%2e%2e", "00000000-0000-0000-0000-000000000000"],
    )
    def test_auch_a_malformed_id_klingt_gleich(self, probe_client, szenario, boese: str) -> None:  # type: ignore[no-untyped-def]
        "Malformed, unknown, and foreign-private resources produce the same response."
        headers = auth(szenario["token_ben"])
        real = probe_client.get(_path(szenario, "privat_anna"), headers=headers)
        kaputt = probe_client.get(
            f"/api/v1/spaces/{szenario['alpha'].id}/privacy-probes/{boese}", headers=headers
        )
        assert kaputt.status_code == 404
        assert kaputt.json() == real.json()

    @pytest.mark.parametrize("boese", ["../../etc/passwd", "a/b"])
    def test_a_zerbrochener_path_remains_ebenfalls_404(
        self, probe_client, szenario, boese: str
    ) -> None:  # type: ignore[no-untyped-def]
        """A Slash matches no Route more and gets deshalb the
        allgemeine 404-Response.

        The is no Existenzauskunft: the Unterschied haengt to the Form
        the URL, the the Caller itself gewaehlt has, and not daran, ob
        it a Resource exists. Who IDs durchprobiert, lernt daraus nothing.
        """
        response = probe_client.get(
            f"/api/v1/spaces/{szenario['alpha'].id}/privacy-probes/{boese}",
            headers=auth(szenario["token_ben"]),
        )
        assert response.status_code == 404
        assert CANARY_ANNA not in response.text

    def test_the_list_shows_the_private_row_the_partners_not(self, probe_client, szenario) -> None:  # type: ignore[no-untyped-def]
        response = probe_client.get(
            f"/api/v1/spaces/{szenario['alpha'].id}/privacy-probes",
            headers=auth(szenario["token_ben"]),
        )
        assert {row["label"] for row in response.json()} == {CANARY_BEN, "Gemeinsam von Anna"}
        assert CANARY_ANNA not in response.text

    def test_the_result_count_reveals_it_auch_not(self, probe_client, szenario) -> None:  # type: ignore[no-untyped-def]
        "a count is itself a disclosure."
        response = probe_client.get(
            f"/api/v1/spaces/{szenario['alpha'].id}/privacy-probes/count",
            headers=auth(szenario["token_ben"]),
        )
        assert response.json()["total"] == 2

    def test_can_the_private_row_not_change(self, probe_client, session, szenario) -> None:  # type: ignore[no-untyped-def]
        response = probe_client.patch(
            _path(szenario, "privat_anna"),
            headers=auth(szenario["token_ben"]),
            json={"label": "uebernommen"},
        )
        assert response.status_code == 404
        session.refresh(szenario["privat_anna"])
        assert szenario["privat_anna"].label == CANARY_ANNA

    def test_can_the_private_row_not_delete(self, probe_client, session, szenario) -> None:  # type: ignore[no-untyped-def]
        response = probe_client.delete(
            _path(szenario, "privat_anna"), headers=auth(szenario["token_ben"])
        )
        assert response.status_code == 404
        assert response.json()["code"] == "PRIVACY_PROBE_NOT_FOUND"
        session.refresh(szenario["privat_anna"])
        assert szenario["privat_anna"].label == CANARY_ANNA

    def test_may_shared_lesen(self, probe_client, szenario) -> None:  # type: ignore[no-untyped-def]
        response = probe_client.get(
            _path(szenario, "geteilt_anna"), headers=auth(szenario["token_ben"])
        )
        assert response.status_code == 200
        assert response.json()["label"] == "Gemeinsam von Anna"

    def test_may_shared_the_partners_not_change(self, probe_client, szenario) -> None:  # type: ignore[no-untyped-def]
        """Here 403 and not 404: the Row is stored the Partner already open.

        A 404 would be no Schutz, sondern a Luege through etwas, the it
        itself gerade has anzeigen lassen."""
        response = probe_client.patch(
            _path(szenario, "geteilt_anna"),
            headers=auth(szenario["token_ben"]),
            json={"label": "uebernommen"},
        )
        assert response.status_code == 403
        assert response.json()["code"] == "NOT_RESOURCE_OWNER"


class TestFremderSpace:
    def test_gets_not_to_the_probes_of_a_foreign_space(self, probe_client, szenario) -> None:  # type: ignore[no-untyped-def]
        "The tenant guard responds first; the path already fails here."
        response = probe_client.get(
            _path(szenario, "privat_anna"), headers=auth(szenario["token_carol"])
        )
        assert response.status_code == 404
        assert response.json()["code"] == "SPACE_NOT_FOUND"

    def test_a_foreign_id_im_own_space_remains_unauffindbar(self, probe_client, szenario) -> None:  # type: ignore[no-untyped-def]
        "The ID existiert wirklich; only not in diesem Space."
        headers = auth(szenario["token_anna"])
        foreign = probe_client.get(
            f"/api/v1/spaces/{szenario['alpha'].id}/privacy-probes/{szenario['privat_carol'].id}",
            headers=headers,
        )
        erfunden = probe_client.get(
            f"/api/v1/spaces/{szenario['alpha'].id}/privacy-probes/{new_id()}", headers=headers
        )
        assert foreign.status_code == erfunden.status_code == 404
        assert foreign.json() == erfunden.json()

    def test_no_foreign_content_in_list_oder_count(self, probe_client, szenario) -> None:  # type: ignore[no-untyped-def]
        headers = auth(szenario["token_anna"])
        list = probe_client.get(
            f"/api/v1/spaces/{szenario['alpha'].id}/privacy-probes", headers=headers
        )
        zahl = probe_client.get(
            f"/api/v1/spaces/{szenario['alpha'].id}/privacy-probes/count", headers=headers
        )
        assert CANARY_FREMD not in list.text
        assert CANARY_BEN not in list.text
        assert zahl.json()["total"] == 2


class TestAnonym:
    def test_without_token_no_access(self, probe_client, szenario) -> None:  # type: ignore[no-untyped-def]
        assert probe_client.get(_path(szenario, "privat_anna")).status_code == 401
        assert (
            probe_client.get(f"/api/v1/spaces/{szenario['alpha'].id}/privacy-probes").status_code
            == 401
        )


class TestFilterInDerAbfrage:
    """do not load first and filter afterwards.

    A Treffer, the is created and danach verworfen is, is already a
    leak; it would already have reached storage, logs, and response-size side channels.
    """

    @pytest.fixture
    def queries(self, engine: Engine):  # type: ignore[no-untyped-def]
        aufgezeichnet: list[str] = []

        def _mitschreiben(conn, cursor, statement, parameters, context, executemany) -> None:  # type: ignore[no-untyped-def]
            aufgezeichnet.append(statement)

        event.listen(engine, "before_cursor_execute", _mitschreiben)
        try:
            yield aufgezeichnet
        finally:
            event.remove(engine, "before_cursor_execute", _mitschreiben)

    def test_the_private_row_is_gar_not_initial_loaded(
        self, probe_client, szenario, queries
    ) -> None:  # type: ignore[no-untyped-def]
        queries.clear()
        response = probe_client.get(
            _path(szenario, "privat_anna"), headers=auth(szenario["token_ben"])
        )
        assert response.status_code == 404

        probe_queries = [sql for sql in queries if "privacy_probes" in sql]
        assert probe_queries, "It gab no Abfrage on the Sondentabelle."
        for sql in probe_queries:
            assert "privacy_class" in sql
            assert "owner_id" in sql
            assert "space_id" in sql

    def test_auch_the_list_filtert_in_the_database(self, probe_client, szenario, queries) -> None:  # type: ignore[no-untyped-def]
        queries.clear()
        probe_client.get(
            f"/api/v1/spaces/{szenario['alpha'].id}/privacy-probes",
            headers=auth(szenario["token_ben"]),
        )
        probe_queries = [sql for sql in queries if "privacy_probes" in sql]
        assert probe_queries
        for sql in probe_queries:
            assert "WHERE" in sql.upper()
            assert "privacy_class" in sql
            assert "owner_id" in sql
