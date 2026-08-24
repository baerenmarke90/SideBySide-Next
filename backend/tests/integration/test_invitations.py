"""Einladungen.

Die Spezifikation nennt sechs Missbrauchsfaelle namentlich: abgelaufen,
widerrufen, wiederverwendet, Space voll, Wettlauf, ungueltiger Token. Jeder
hat hier seinen Test.
"""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from datetime import timedelta
from threading import Barrier

import pytest
from sqlalchemy import select
from sqlalchemy.orm import Session

from sidebyside.core.clock import now
from sidebyside.core.errors import ConflictError, NotFoundError, ValidationError
from sidebyside.relationship import invitations, service
from sidebyside.relationship.models import Invitation
from tests.conftest import auth, make_account, make_space, requires_database, sign_in

pytestmark = [pytest.mark.integration, requires_database]


@pytest.fixture
def anna_mit_space(session: Session):  # type: ignore[no-untyped-def]
    anna = make_account(session, "Anna")
    space = make_space(session, anna)
    session.flush()
    return {"anna": anna, "space": space, "token": sign_in(session, anna)}


class TestErzeugen:
    def test_token_wird_genau_einmal_ausgegeben(self, session, anna_mit_space) -> None:  # type: ignore[no-untyped-def]
        ergebnis = invitations.create(session, anna_mit_space["space"].id, anna_mit_space["anna"])
        assert ergebnis.token
        # In der Datenbank steht nur der Hash.
        assert ergebnis.token not in str(ergebnis.invitation.__dict__)

    def test_ist_zunaechst_offen(self, session, anna_mit_space) -> None:  # type: ignore[no-untyped-def]
        ergebnis = invitations.create(session, anna_mit_space["space"].id, anna_mit_space["anna"])
        assert ergebnis.invitation.is_open(now())

    def test_liste_zeigt_keinen_token(self, client, anna_mit_space) -> None:  # type: ignore[no-untyped-def]
        client.post(
            f"/api/v1/spaces/{anna_mit_space['space'].id}/invitations",
            headers=auth(anna_mit_space["token"]),
        )
        antwort = client.get(
            f"/api/v1/spaces/{anna_mit_space['space'].id}/invitations",
            headers=auth(anna_mit_space["token"]),
        )
        assert antwort.status_code == 200
        for eintrag in antwort.json():
            assert set(eintrag) == {"id", "expiresAt", "createdAt"}


class TestAnnehmen:
    def test_partner_wird_mitglied(self, session, anna_mit_space) -> None:  # type: ignore[no-untyped-def]
        ben = make_account(session, "Ben")
        ergebnis = invitations.create(session, anna_mit_space["space"].id, anna_mit_space["anna"])

        mitgliedschaft = invitations.accept(session, ergebnis.token, ben)
        assert mitgliedschaft.space_id == anna_mit_space["space"].id
        assert mitgliedschaft.is_active
        assert ergebnis.invitation.accepted_by == ben.id

    def test_ueber_http(self, client, session, anna_mit_space) -> None:  # type: ignore[no-untyped-def]
        ben = make_account(session, "Ben")
        ben_token = sign_in(session, ben)
        session.flush()

        erzeugt = client.post(
            f"/api/v1/spaces/{anna_mit_space['space'].id}/invitations",
            headers=auth(anna_mit_space["token"]),
        )
        assert erzeugt.status_code == 201
        token = erzeugt.json()["token"]

        angenommen = client.post(
            "/api/v1/invitations/accept",
            json={"token": token},
            headers=auth(ben_token),
        )
        assert angenommen.status_code == 201

        # Und jetzt sieht Ben den Space.
        assert (
            client.get(
                f"/api/v1/spaces/{anna_mit_space['space'].id}", headers=auth(ben_token)
            ).status_code
            == 200
        )


class TestMissbrauch:
    def test_ungueltiger_token(self, session, anna_mit_space) -> None:  # type: ignore[no-untyped-def]
        ben = make_account(session, "Ben")
        for unfug in ["", "nicht-echt", "a" * 100]:
            with pytest.raises(ValidationError):
                invitations.accept(session, unfug, ben)

    def test_abgelaufener_token(self, session, anna_mit_space) -> None:  # type: ignore[no-untyped-def]
        ben = make_account(session, "Ben")
        ergebnis = invitations.create(session, anna_mit_space["space"].id, anna_mit_space["anna"])
        ergebnis.invitation.expires_at = now() - timedelta(seconds=1)
        session.flush()

        with pytest.raises(ValidationError):
            invitations.accept(session, ergebnis.token, ben)

    def test_widerrufener_token(self, session, anna_mit_space) -> None:  # type: ignore[no-untyped-def]
        ben = make_account(session, "Ben")
        ergebnis = invitations.create(session, anna_mit_space["space"].id, anna_mit_space["anna"])
        invitations.revoke(session, anna_mit_space["space"].id, ergebnis.invitation.id)
        session.flush()

        with pytest.raises(ValidationError):
            invitations.accept(session, ergebnis.token, ben)

    def test_wiederverwendeter_token(self, session, anna_mit_space) -> None:  # type: ignore[no-untyped-def]
        """Eine Einladung gilt genau einmal."""
        ben = make_account(session, "Ben")
        dritte = make_account(session, "Dritte Person")
        ergebnis = invitations.create(session, anna_mit_space["space"].id, anna_mit_space["anna"])

        invitations.accept(session, ergebnis.token, ben)
        session.flush()

        with pytest.raises(ValidationError):
            invitations.accept(session, ergebnis.token, dritte)

    def test_voller_space_erzeugt_keine_einladung(self, session, anna_mit_space) -> None:  # type: ignore[no-untyped-def]
        """Sonst verschickte jemand einen Link, der beim Oeffnen enttaeuscht."""
        ben = make_account(session, "Ben")
        service.add_member(session, anna_mit_space["space"].id, ben)
        session.flush()

        with pytest.raises(ConflictError) as fehler:
            invitations.create(session, anna_mit_space["space"].id, anna_mit_space["anna"])
        assert fehler.value.code == "SPACE_FULL"

    def test_voller_space_weist_eine_alte_einladung_ab(self, session, anna_mit_space) -> None:  # type: ignore[no-untyped-def]
        """Die Einladung war schon unterwegs, als der Space voll wurde."""
        ergebnis = invitations.create(session, anna_mit_space["space"].id, anna_mit_space["anna"])
        ben = make_account(session, "Ben")
        service.add_member(session, anna_mit_space["space"].id, ben)
        session.flush()

        dritte = make_account(session, "Dritte Person")
        with pytest.raises(ConflictError) as fehler:
            invitations.accept(session, ergebnis.token, dritte)
        assert fehler.value.code == "SPACE_FULL"

        # Die Einladung bleibt offen - der Fehler lag nicht an ihr.
        assert ergebnis.invitation.accepted_at is None

    def test_ersteller_kann_nicht_selbst_annehmen(self, session, anna_mit_space) -> None:  # type: ignore[no-untyped-def]
        ergebnis = invitations.create(session, anna_mit_space["space"].id, anna_mit_space["anna"])
        with pytest.raises(ValidationError) as fehler:
            invitations.accept(session, ergebnis.token, anna_mit_space["anna"])
        assert fehler.value.code == "CANNOT_ACCEPT_OWN_INVITATION"

    def test_jeder_fehlschlag_meldet_dasselbe(self, session, anna_mit_space) -> None:  # type: ignore[no-untyped-def]
        """Ein Unterschied waere eine Auskunft darueber, welche Token es gibt."""
        ben = make_account(session, "Ben")

        abgelaufen = invitations.create(session, anna_mit_space["space"].id, anna_mit_space["anna"])
        abgelaufen.invitation.expires_at = now() - timedelta(seconds=1)
        widerrufen = invitations.create(session, anna_mit_space["space"].id, anna_mit_space["anna"])
        widerrufen.invitation.revoked_at = now()
        session.flush()

        meldungen = set()
        for token in ["gibt-es-nicht", abgelaufen.token, widerrufen.token]:
            with pytest.raises(ValidationError) as fehler:
                invitations.accept(session, token, ben)
            meldungen.add((str(fehler.value), fehler.value.code))
        assert len(meldungen) == 1


class TestWettlauf:
    def test_zwei_einladungen_konkurrieren_um_letzten_platz(self, production_client) -> None:  # type: ignore[no-untyped-def]
        client, macher = production_client
        with macher() as vorbereitung:
            anna = make_account(vorbereitung, "Anna Wettlauf")
            space = make_space(vorbereitung, anna)
            erste_einladung = invitations.create(vorbereitung, space.id, anna)
            zweite_einladung = invitations.create(vorbereitung, space.id, anna)
            ben = make_account(vorbereitung, "Ben Wettlauf")
            clara = make_account(vorbereitung, "Clara Wettlauf")
            ben_token = sign_in(vorbereitung, ben)
            clara_token = sign_in(vorbereitung, clara)
            space_id = space.id
            vorbereitung.commit()

        start = Barrier(2)

        def annehmen(daten):  # type: ignore[no-untyped-def]
            einladungs_token, zugangs_token = daten
            start.wait(timeout=5)
            return client.post(
                "/api/v1/invitations/accept",
                json={"token": einladungs_token},
                headers=auth(zugangs_token),
            )

        versuche = [
            (erste_einladung.token, ben_token),
            (zweite_einladung.token, clara_token),
        ]
        with ThreadPoolExecutor(max_workers=2) as pool:
            antworten = list(pool.map(annehmen, versuche))

        assert sorted(antwort.status_code for antwort in antworten) == [201, 409]
        abgewiesen = next(antwort for antwort in antworten if antwort.status_code == 409)
        assert abgewiesen.json() == {
            "type": "conflict",
            "title": "Conflict",
            "status": 409,
            "detail": "This space already has two partners.",
            "code": "SPACE_FULL",
        }

        with macher() as pruefer:
            aktive = service.active_memberships(pruefer, space_id)
            assert len(aktive) == 2  # Anna und genau einer der beiden
            beide = (
                pruefer.execute(select(Invitation).where(Invitation.space_id == space_id))
                .scalars()
                .all()
            )
            assert sum(einladung.accepted_at is not None for einladung in beide) == 1
            assert sum(einladung.is_open(now()) for einladung in beide) == 1


class TestWiderrufen:
    def test_fremder_space_kann_nicht_widerrufen(self, session, anna_mit_space) -> None:  # type: ignore[no-untyped-def]
        """Eine Einladungs-ID allein darf keinen Zugriff geben."""
        fremd = make_account(session, "Fremde Person")
        fremder_space = make_space(session, fremd)
        ergebnis = invitations.create(session, anna_mit_space["space"].id, anna_mit_space["anna"])
        session.flush()

        with pytest.raises(NotFoundError):
            invitations.revoke(session, fremder_space.id, ergebnis.invitation.id)
