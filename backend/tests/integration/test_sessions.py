"""Geraetesitzungen.

Geprueft wird nicht nur der gute Fall, sondern vor allem: was passiert bei
abgelaufenen, widerrufenen und kopierten Token.
"""

from __future__ import annotations

from datetime import timedelta

import pytest
from sqlalchemy import select
from sqlalchemy.orm import Session

from sidebyside.auth import sessions
from sidebyside.auth.tokens import hash_token
from sidebyside.core.clock import now
from sidebyside.core.errors import UnauthenticatedError
from sidebyside.identity.models import DeviceSession
from tests.conftest import make_account, requires_database

pytestmark = [pytest.mark.integration, requires_database]


class TestAnlegen:
    def test_sitzung_liefert_beide_token(self, session: Session) -> None:
        konto = make_account(session)
        geraet, tokens = sessions.start_session(session, konto, device_name="Pixel")
        session.flush()

        assert tokens.access_token
        assert tokens.refresh_token
        assert tokens.access_token != tokens.refresh_token
        assert geraet.device_name == "Pixel"

    def test_klartext_wird_nicht_gespeichert(self, session: Session) -> None:
        """Wer die Datenbank liest, darf sich damit nicht anmelden koennen."""
        konto = make_account(session)
        geraet, tokens = sessions.start_session(session, konto)
        session.flush()

        assert geraet.refresh_token_hash == hash_token(tokens.refresh_token)
        assert geraet.access_token_hash == hash_token(tokens.access_token)
        assert tokens.access_token not in str(geraet.__dict__)
        assert tokens.refresh_token not in str(geraet.__dict__)

    def test_access_token_ist_kurzlebig(self, session: Session) -> None:
        konto = make_account(session)
        _, tokens = sessions.start_session(session, konto)
        session.flush()
        assert tokens.access_expires_at - now() <= timedelta(minutes=15)


class TestPruefen:
    def test_gueltiger_token_ergibt_den_account(self, session: Session) -> None:
        konto = make_account(session)
        _, tokens = sessions.start_session(session, konto)
        session.flush()

        assert sessions.authenticate(session, tokens.access_token).id == konto.id

    @pytest.mark.parametrize("unfug", ["", "   ", "nicht-echt", "a" * 200])
    def test_unbekannter_token_wird_abgewiesen(self, session: Session, unfug: str) -> None:
        with pytest.raises(UnauthenticatedError):
            sessions.authenticate(session, unfug)

    def test_abgelaufener_token_wird_abgewiesen(self, session: Session) -> None:
        konto = make_account(session)
        geraet, tokens = sessions.start_session(session, konto)
        geraet.access_expires_at = now() - timedelta(seconds=1)
        session.flush()

        with pytest.raises(UnauthenticatedError):
            sessions.authenticate(session, tokens.access_token)

    def test_widerrufene_sitzung_wird_abgewiesen(self, session: Session) -> None:
        konto = make_account(session)
        geraet, tokens = sessions.start_session(session, konto)
        session.flush()

        sessions.revoke(geraet)
        session.flush()

        with pytest.raises(UnauthenticatedError):
            sessions.authenticate(session, tokens.access_token)

    def test_widerruf_entwertet_auch_den_access_token(self, session: Session) -> None:
        """Sonst liefe ein gestohlenes Geraet noch bis zum Ablauf weiter."""
        konto = make_account(session)
        geraet, _ = sessions.start_session(session, konto)
        session.flush()
        sessions.revoke(geraet)
        assert geraet.access_token_hash is None

    def test_abgeschalteter_account_kommt_nicht_hinein(self, session: Session) -> None:
        konto = make_account(session)
        _, tokens = sessions.start_session(session, konto)
        konto.disabled_at = now()
        session.flush()

        with pytest.raises(UnauthenticatedError):
            sessions.authenticate(session, tokens.access_token)

    def test_der_fehler_verraet_den_grund_nicht(self, session: Session) -> None:
        """Ein Aufrufer soll nicht unterscheiden koennen, ob ein Token
        unbekannt, abgelaufen oder widerrufen ist - das waere eine Auskunft
        ueber gueltige Token."""
        konto = make_account(session)
        geraet, tokens = sessions.start_session(session, konto)
        session.flush()
        sessions.revoke(geraet)
        session.flush()

        meldungen = set()
        for token in ["unbekannt", tokens.access_token]:
            with pytest.raises(UnauthenticatedError) as fehler:
                sessions.authenticate(session, token)
            meldungen.add(str(fehler.value))
        assert len(meldungen) == 1


class TestErneuern:
    def test_rotiert_beide_token(self, session: Session) -> None:
        konto = make_account(session)
        _, erste = sessions.start_session(session, konto)
        session.flush()

        zweite = sessions.refresh_session(session, erste.refresh_token)
        session.flush()

        assert zweite.refresh_token != erste.refresh_token
        assert zweite.access_token != erste.access_token
        assert sessions.authenticate(session, zweite.access_token).id == konto.id

    def test_alter_access_token_gilt_nach_dem_erneuern_nicht_mehr(self, session: Session) -> None:
        konto = make_account(session)
        _, erste = sessions.start_session(session, konto)
        session.flush()
        sessions.refresh_session(session, erste.refresh_token)
        session.flush()

        with pytest.raises(UnauthenticatedError):
            sessions.authenticate(session, erste.access_token)

    def test_abgelaufener_refresh_token_wird_abgewiesen(self, session: Session) -> None:
        konto = make_account(session)
        geraet, tokens = sessions.start_session(session, konto)
        geraet.expires_at = now() - timedelta(seconds=1)
        session.flush()

        with pytest.raises(UnauthenticatedError):
            sessions.refresh_session(session, tokens.refresh_token)

    def test_widerrufener_refresh_token_wird_abgewiesen(self, session: Session) -> None:
        konto = make_account(session)
        geraet, tokens = sessions.start_session(session, konto)
        sessions.revoke(geraet)
        session.flush()

        with pytest.raises(UnauthenticatedError):
            sessions.refresh_session(session, tokens.refresh_token)


class TestReplay:
    def test_wiederverwendeter_refresh_token_widerruft_die_sitzung(self, session: Session) -> None:
        """Taucht ein bereits rotierter Token wieder auf, ist er kopiert
        worden - der rechtmaessige Client haette den neuen. Dann darf
        niemand mehr durch, auch nicht der Besitzer."""
        konto = make_account(session)
        geraet, erste = sessions.start_session(session, konto)
        session.flush()

        zweite = sessions.refresh_session(session, erste.refresh_token)
        session.flush()

        with pytest.raises(UnauthenticatedError):
            sessions.refresh_session(session, erste.refresh_token)
        session.flush()

        assert geraet.revoked_at is not None
        with pytest.raises(UnauthenticatedError):
            sessions.authenticate(session, zweite.access_token)


class TestAlleWiderrufen:
    def test_beendet_jede_offene_sitzung(self, session: Session) -> None:
        konto = make_account(session)
        tokens = [sessions.start_session(session, konto)[1] for _ in range(3)]
        session.flush()

        assert sessions.revoke_all(session, konto) == 3
        session.flush()

        for satz in tokens:
            with pytest.raises(UnauthenticatedError):
                sessions.authenticate(session, satz.access_token)

    def test_laesst_fremde_sitzungen_unberuehrt(self, session: Session) -> None:
        eigen = make_account(session, "Eigen")
        fremd = make_account(session, "Fremd")
        _, fremde_tokens = sessions.start_session(session, fremd)
        sessions.start_session(session, eigen)
        session.flush()

        sessions.revoke_all(session, eigen)
        session.flush()

        assert sessions.authenticate(session, fremde_tokens.access_token).id == fremd.id
        offen = (
            session.execute(
                select(DeviceSession).where(
                    DeviceSession.account_id == fremd.id,
                    DeviceSession.revoked_at.is_(None),
                )
            )
            .scalars()
            .all()
        )
        assert len(offen) == 1
