"""Geraetesitzungen.

Geprueft wird nicht nur der gute Fall, sondern vor allem: was passiert bei
abgelaufenen, widerrufenen und kopierten Token.
"""

from __future__ import annotations

from collections.abc import Callable
from datetime import datetime, timedelta

import pytest
from sqlalchemy import select
from sqlalchemy.orm import Session

from sidebyside.auth import sessions
from sidebyside.auth.tokens import (
    ACCESS_TOKEN_LIFETIME,
    REFRESH_TOKEN_LIFETIME,
    SESSION_ABSOLUTE_LIFETIME,
    hash_token,
)
from sidebyside.core.clock import now
from sidebyside.core.errors import UnauthenticatedError
from sidebyside.identity.models import ConsumedRefreshToken, DeviceSession
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

    def test_aelteste_generation_wird_nach_mehreren_rotationen_erkannt(
        self, session: Session
    ) -> None:
        """T0 -> T1 -> T2, dann Replay von T0.

        Ein Zwei-Slot-Fenster aus aktuellem und vorherigem Token verliert T0
        nach der zweiten Rotation aus dem Blick. Der Token wuerde zwar
        abgewiesen, aber nicht mehr seiner Familie zugeordnet - und die
        kompromittierte Sitzung liefe weiter.
        """
        konto = make_account(session)
        geraet, t0 = sessions.start_session(session, konto)
        session.flush()

        t1 = sessions.refresh_session(session, t0.refresh_token)
        session.flush()
        t2 = sessions.refresh_session(session, t1.refresh_token)
        session.flush()

        with pytest.raises(UnauthenticatedError):
            sessions.refresh_session(session, t0.refresh_token)
        session.flush()

        assert geraet.revoked_at is not None
        with pytest.raises(UnauthenticatedError):
            sessions.authenticate(session, t2.access_token)
        with pytest.raises(UnauthenticatedError):
            sessions.refresh_session(session, t2.refresh_token)

    def test_mittlere_generation_wird_nach_der_naechsten_rotation_erkannt(
        self, session: Session
    ) -> None:
        """Replay von T1, nachdem T2 ausgestellt wurde."""
        konto = make_account(session)
        geraet, t0 = sessions.start_session(session, konto)
        session.flush()

        t1 = sessions.refresh_session(session, t0.refresh_token)
        session.flush()
        t2 = sessions.refresh_session(session, t1.refresh_token)
        session.flush()

        with pytest.raises(UnauthenticatedError):
            sessions.refresh_session(session, t1.refresh_token)
        session.flush()

        assert geraet.revoked_at is not None
        with pytest.raises(UnauthenticatedError):
            sessions.authenticate(session, t2.access_token)

    def test_jede_generation_bleibt_der_familie_zugeordnet(self, session: Session) -> None:
        konto = make_account(session)
        geraet, t0 = sessions.start_session(session, konto)
        session.flush()

        t1 = sessions.refresh_session(session, t0.refresh_token)
        session.flush()
        sessions.refresh_session(session, t1.refresh_token)
        session.flush()

        verbraucht = (
            session.execute(
                select(ConsumedRefreshToken).where(
                    ConsumedRefreshToken.device_session_id == geraet.id
                )
            )
            .scalars()
            .all()
        )
        assert {eintrag.token_hash for eintrag in verbraucht} == {
            hash_token(t0.refresh_token),
            hash_token(t1.refresh_token),
        }

    def test_historie_haelt_nur_hashes(self, session: Session) -> None:
        """Die Replay-Historie darf keine zweite Quelle fuer Anmeldenachweise sein."""
        konto = make_account(session)
        _, t0 = sessions.start_session(session, konto)
        session.flush()
        sessions.refresh_session(session, t0.refresh_token)
        session.flush()

        eintrag = session.execute(select(ConsumedRefreshToken)).scalar_one()
        assert eintrag.token_hash == hash_token(t0.refresh_token)
        assert t0.refresh_token not in str(eintrag.__dict__)

    def test_replay_einer_fremden_familie_laesst_andere_sitzungen_leben(
        self, session: Session
    ) -> None:
        konto = make_account(session)
        betroffen, t0 = sessions.start_session(session, konto)
        unbeteiligt, andere = sessions.start_session(session, konto)
        session.flush()

        sessions.refresh_session(session, t0.refresh_token)
        session.flush()

        with pytest.raises(UnauthenticatedError):
            sessions.refresh_session(session, t0.refresh_token)
        session.flush()

        assert betroffen.revoked_at is not None
        assert unbeteiligt.revoked_at is None
        assert sessions.authenticate(session, andere.access_token).id == konto.id

    def test_unbekannter_token_widerruft_nichts(self, session: Session) -> None:
        """Nur ein echter Token der Familie loest den Widerruf aus.

        Sonst koennte jeder eine fremde Sitzung abschiessen, indem er
        beliebigen Unfug an den Refresh-Endpunkt schickt.
        """
        konto = make_account(session)
        geraet, tokens = sessions.start_session(session, konto)
        session.flush()

        with pytest.raises(UnauthenticatedError):
            sessions.refresh_session(session, "gibt-es-nicht")
        session.flush()

        assert geraet.revoked_at is None
        assert sessions.authenticate(session, tokens.access_token).id == konto.id

    def test_der_fehler_verraet_den_grund_nicht(self, session: Session) -> None:
        """Unbekannt, abgelaufen und als Replay erkannt sehen gleich aus.

        Ein unterscheidbarer Fehler waere die Auskunft, welcher Token
        einmal echt war.
        """
        konto = make_account(session)
        _, t0 = sessions.start_session(session, konto)
        session.flush()
        sessions.refresh_session(session, t0.refresh_token)
        session.flush()

        abgelaufen_konto = make_account(session, "Abgelaufen")
        abgelaufen_geraet, abgelaufen = sessions.start_session(session, abgelaufen_konto)
        abgelaufen_geraet.expires_at = now() - timedelta(seconds=1)
        session.flush()

        meldungen = set()
        codes = set()
        for token in ["gibt-es-nicht", t0.refresh_token, abgelaufen.refresh_token]:
            with pytest.raises(UnauthenticatedError) as fehler:
                sessions.refresh_session(session, token)
            session.flush()
            meldungen.add(str(fehler.value))
            codes.add(fehler.value.code)
        assert len(meldungen) == 1
        assert len(codes) == 1


class TestAbsoluteLebensdauer:
    """Die Familie hat eine harte Obergrenze.

    Ohne sie waere die Sitzungsdauer unbegrenzt: das gleitende Fenster
    laesst sich durch regelmaessiges Erneuern beliebig weit vorschieben,
    und mit ihm waechst eine Replay-Historie, die nie geraeumt wird.
    """

    @staticmethod
    def _uhr(monkeypatch: pytest.MonkeyPatch, start: datetime) -> Callable[[datetime], None]:
        """Eine stellbare Uhr fuer das Sitzungsmodul."""
        stand = {"jetzt": start}
        monkeypatch.setattr(sessions, "now", lambda: stand["jetzt"])

        def stelle(auf: datetime) -> None:
            stand["jetzt"] = auf

        return stelle

    @staticmethod
    def _halte_am_leben(
        session: Session,
        tokens: sessions.IssuedTokens,
        stelle: Callable[[datetime], None],
        *,
        von: datetime,
        bis: datetime,
        schritt: timedelta = timedelta(days=14),
    ) -> tuple[sessions.IssuedTokens, datetime]:
        """Die Sitzung durch regelmaessiges Erneuern bis kurz vor `bis` tragen.

        Ohne das liefe das gleitende Fenster ab, und der Test pruefte die
        falsche Grenze.
        """
        zeitpunkt = von
        while zeitpunkt + schritt < bis:
            zeitpunkt += schritt
            stelle(zeitpunkt)
            tokens = sessions.refresh_session(session, tokens.refresh_token)
            session.flush()
        return tokens, zeitpunkt

    def test_regelmaessiges_erneuern_verschiebt_die_grenze_nicht(
        self, session: Session, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Der Kern der Sache: die Familie altert, auch wenn sie benutzt wird.

        Ein Client, der brav alle zwei Wochen erneuert, haelt das gleitende
        Fenster dauerhaft offen. Die absolute Grenze darf sich davon nicht
        bewegen, sonst gibt es keine obere Schranke - weder fuer die Sitzung
        noch fuer ihre Historie.
        """
        beginn = now()
        stelle = self._uhr(monkeypatch, beginn)

        konto = make_account(session)
        geraet, tokens = sessions.start_session(session, konto)
        session.flush()

        grenze = geraet.absolute_expires_at
        assert grenze == beginn + SESSION_ABSOLUTE_LIFETIME

        schritt = timedelta(days=14)
        zeitpunkt = beginn
        while zeitpunkt + schritt < grenze:
            zeitpunkt += schritt
            stelle(zeitpunkt)
            tokens = sessions.refresh_session(session, tokens.refresh_token)
            session.flush()

            assert geraet.absolute_expires_at == grenze, "die Grenze ist mitgewandert"
            assert geraet.expires_at > zeitpunkt

        # Zwischenstand: die Sitzung lebt kurz vor der Grenze noch.
        assert zeitpunkt > beginn + timedelta(days=150)
        assert sessions.authenticate(session, tokens.access_token).id == konto.id

        stelle(grenze + timedelta(seconds=1))
        with pytest.raises(UnauthenticatedError):
            sessions.refresh_session(session, tokens.refresh_token)
        session.flush()

    def test_gleitendes_fenster_ueberholt_die_grenze_nicht(
        self, session: Session, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Sonst nennte die Antwort ein Ablaufdatum, das nicht gilt."""
        beginn = now()
        stelle = self._uhr(monkeypatch, beginn)

        konto = make_account(session)
        geraet, tokens = sessions.start_session(session, konto)
        session.flush()

        kurz_davor = geraet.absolute_expires_at - timedelta(hours=1)
        tokens, _ = self._halte_am_leben(session, tokens, stelle, von=beginn, bis=kurz_davor)

        stelle(kurz_davor)
        erneuert = sessions.refresh_session(session, tokens.refresh_token)
        session.flush()

        assert erneuert.refresh_expires_at == geraet.absolute_expires_at
        assert erneuert.refresh_expires_at < kurz_davor + REFRESH_TOKEN_LIFETIME
        assert erneuert.access_expires_at <= geraet.absolute_expires_at

    def test_access_token_endet_mit_der_familie(
        self, session: Session, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Ein kurz vor der Grenze ausgestellter Token darf sie nicht ueberleben."""
        beginn = now()
        stelle = self._uhr(monkeypatch, beginn)

        konto = make_account(session)
        geraet, tokens = sessions.start_session(session, konto)
        session.flush()

        kurz_davor = geraet.absolute_expires_at - timedelta(minutes=1)
        tokens, _ = self._halte_am_leben(session, tokens, stelle, von=beginn, bis=kurz_davor)

        stelle(kurz_davor)
        erneuert = sessions.refresh_session(session, tokens.refresh_token)
        session.flush()
        assert sessions.authenticate(session, erneuert.access_token).id == konto.id

        stelle(geraet.absolute_expires_at + timedelta(seconds=1))
        assert erneuert.access_expires_at > beginn
        with pytest.raises(UnauthenticatedError):
            sessions.authenticate(session, erneuert.access_token)

    def test_historie_einer_dauerhaft_genutzten_familie_wird_endlich(
        self, session: Session, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Der eigentliche Zweck der Grenze.

        Erst weil die Familie endet, endet auch ihre Historie. Waere die
        Sitzung unbegrenzt verlaengerbar, waere die Tabelle es auch.
        """
        beginn = now()
        stelle = self._uhr(monkeypatch, beginn)

        konto = make_account(session)
        geraet, tokens = sessions.start_session(session, konto)
        session.flush()

        zeitpunkt = beginn
        schritt = timedelta(days=14)
        while zeitpunkt + schritt < geraet.absolute_expires_at:
            zeitpunkt += schritt
            stelle(zeitpunkt)
            tokens = sessions.refresh_session(session, tokens.refresh_token)
            session.flush()

        gesammelt = session.execute(select(ConsumedRefreshToken)).scalars().all()
        assert len(gesammelt) > 1

        # Solange die Familie lebt, bleibt jede Generation zuordenbar.
        assert sessions.prune_replay_history(session) == 0

        stelle(geraet.absolute_expires_at + sessions.REPLAY_HISTORY_RETENTION + timedelta(days=1))
        assert sessions.prune_replay_history(session) == len(gesammelt)
        session.flush()
        assert session.execute(select(ConsumedRefreshToken)).scalars().all() == []

    def test_replay_bleibt_bis_zur_grenze_ueber_alle_generationen_erkennbar(
        self, session: Session, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Die Grenze darf kein Historienfenster durch die Hintertuer sein."""
        beginn = now()
        stelle = self._uhr(monkeypatch, beginn)

        konto = make_account(session)
        geraet, t0 = sessions.start_session(session, konto)
        session.flush()

        tokens = t0
        zeitpunkt = beginn
        for _ in range(10):
            zeitpunkt += timedelta(days=14)
            stelle(zeitpunkt)
            tokens = sessions.refresh_session(session, tokens.refresh_token)
            session.flush()

        # Die allererste Generation, viele Rotationen und Monate spaeter.
        with pytest.raises(UnauthenticatedError):
            sessions.refresh_session(session, t0.refresh_token)
        session.flush()

        assert geraet.revoked_at is not None

    def test_neue_anmeldung_beginnt_eine_neue_familie(
        self, session: Session, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Nach der Grenze hilft nur Re-Authentifizierung."""
        beginn = now()
        stelle = self._uhr(monkeypatch, beginn)

        konto = make_account(session)
        alt_geraet, alt = sessions.start_session(session, konto)
        session.flush()

        nach_der_grenze = alt_geraet.absolute_expires_at + timedelta(days=1)
        stelle(nach_der_grenze)
        with pytest.raises(UnauthenticatedError):
            sessions.refresh_session(session, alt.refresh_token)
        session.flush()

        neu_geraet, neu = sessions.start_session(session, konto)
        session.flush()

        assert neu_geraet.id != alt_geraet.id
        assert neu_geraet.absolute_expires_at == nach_der_grenze + SESSION_ABSOLUTE_LIFETIME
        assert sessions.authenticate(session, neu.access_token).id == konto.id

    def test_frische_sitzung_haelt_beide_fenster_auseinander(self, session: Session) -> None:
        konto = make_account(session)
        geraet, tokens = sessions.start_session(session, konto)
        session.flush()

        assert geraet.expires_at < geraet.absolute_expires_at
        assert geraet.absolute_expires_at - geraet.expires_at == (
            SESSION_ABSOLUTE_LIFETIME - REFRESH_TOKEN_LIFETIME
        )
        assert tokens.access_expires_at - now() <= ACCESS_TOKEN_LIFETIME


class TestReplayHistorieAufraeumen:
    def test_laufende_sitzung_behaelt_ihre_historie(self, session: Session) -> None:
        """Die Historie einer lebenden Familie IST die Replay-Erkennung."""
        konto = make_account(session)
        _, t0 = sessions.start_session(session, konto)
        session.flush()
        sessions.refresh_session(session, t0.refresh_token)
        session.flush()

        assert sessions.prune_replay_history(session) == 0
        session.flush()
        assert session.execute(select(ConsumedRefreshToken)).scalars().all()

    def test_beendete_sitzung_wird_nach_der_frist_geraeumt(self, session: Session) -> None:
        konto = make_account(session)
        geraet, t0 = sessions.start_session(session, konto)
        session.flush()
        sessions.refresh_session(session, t0.refresh_token)
        session.flush()

        sessions.revoke(geraet)
        geraet.revoked_at = now() - sessions.REPLAY_HISTORY_RETENTION - timedelta(days=1)
        session.flush()

        assert sessions.prune_replay_history(session) == 1
        session.flush()
        assert session.execute(select(ConsumedRefreshToken)).scalars().all() == []

    def test_frisch_widerrufene_sitzung_bleibt_zunaechst_stehen(self, session: Session) -> None:
        konto = make_account(session)
        geraet, t0 = sessions.start_session(session, konto)
        session.flush()
        sessions.refresh_session(session, t0.refresh_token)
        sessions.revoke(geraet)
        session.flush()

        assert sessions.prune_replay_history(session) == 0

    def test_abgelaufene_sitzung_wird_ohne_widerruf_geraeumt(self, session: Session) -> None:
        konto = make_account(session)
        geraet, t0 = sessions.start_session(session, konto)
        session.flush()
        sessions.refresh_session(session, t0.refresh_token)
        geraet.expires_at = now() - sessions.REPLAY_HISTORY_RETENTION - timedelta(days=1)
        session.flush()

        assert sessions.prune_replay_history(session) == 1

    def test_geloeschte_sitzung_nimmt_ihre_historie_mit(self, session: Session) -> None:
        """Der Fremdschluessel raeumt kaskadierend auf."""
        konto = make_account(session)
        geraet, t0 = sessions.start_session(session, konto)
        session.flush()
        sessions.refresh_session(session, t0.refresh_token)
        session.flush()

        session.delete(geraet)
        session.flush()

        assert session.execute(select(ConsumedRefreshToken)).scalars().all() == []


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
