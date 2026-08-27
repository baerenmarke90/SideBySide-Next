"""Device sessions.

The suite tests not only the happy path, but especially what happens for
abgelaufenen, widerrufenen and kopierten Token.
"""

from __future__ import annotations

from collections.abc import Callable
from datetime import datetime, timedelta

import pytest
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from sidebyside.auth import rate_limit, sessions
from sidebyside.auth.tokens import (
    ACCESS_TOKEN_LIFETIME,
    REFRESH_TOKEN_LIFETIME,
    SESSION_ABSOLUTE_LIFETIME,
    hash_token,
)
from sidebyside.core.clock import now
from sidebyside.core.errors import RateLimitedError, UnauthenticatedError
from sidebyside.identity.models import ConsumedRefreshToken, DeviceSession, RateLimitEvent
from tests.conftest import make_account, requires_database

pytestmark = [pytest.mark.integration, requires_database]


class TestAnlegen:
    def test_session_data_returns_beide_token(self, session: Session) -> None:
        account = make_account(session)
        device, tokens = sessions.start_session(session, account, device_name="Pixel")
        session.flush()

        assert tokens.access_token
        assert tokens.refresh_token
        assert tokens.access_token != tokens.refresh_token
        assert device.device_name == "Pixel"

    def test_plaintext_is_not_stored(self, session: Session) -> None:
        "database read access must not provide reusable sign-in credentials."
        account = make_account(session)
        device, tokens = sessions.start_session(session, account)
        session.flush()

        assert device.refresh_token_hash == hash_token(tokens.refresh_token)
        assert device.access_token_hash == hash_token(tokens.access_token)
        assert tokens.access_token not in str(device.__dict__)
        assert tokens.refresh_token not in str(device.__dict__)

    def test_access_token_is_kurzlebig(self, session: Session) -> None:
        account = make_account(session)
        _, tokens = sessions.start_session(session, account)
        session.flush()
        assert tokens.access_expires_at - now() <= timedelta(minutes=15)


class TestPruefen:
    def test_valid_token_returns_the_account(self, session: Session) -> None:
        account = make_account(session)
        _, tokens = sessions.start_session(session, account)
        session.flush()

        assert sessions.authenticate(session, tokens.access_token).id == account.id

    @pytest.mark.parametrize("unfug", ["", "   ", "nicht-echt", "a" * 200])
    def test_unknown_token_is_rejected(self, session: Session, malformed: str) -> None:
        with pytest.raises(UnauthenticatedError):
            sessions.authenticate(session, malformed)

    def test_expired_token_is_rejected(self, session: Session) -> None:
        account = make_account(session)
        device, tokens = sessions.start_session(session, account)
        device.access_expires_at = now() - timedelta(seconds=1)
        session.flush()

        with pytest.raises(UnauthenticatedError):
            sessions.authenticate(session, tokens.access_token)

    def test_revoked_session_data_is_rejected(self, session: Session) -> None:
        account = make_account(session)
        device, tokens = sessions.start_session(session, account)
        session.flush()

        sessions.revoke(device)
        session.flush()

        with pytest.raises(UnauthenticatedError):
            sessions.authenticate(session, tokens.access_token)

    def test_widerruf_invalidates_auch_the_access_token(self, session: Session) -> None:
        "otherwise a stolen device would remain usable until token expiry."
        account = make_account(session)
        device, _ = sessions.start_session(session, account)
        session.flush()
        sessions.revoke(device)
        assert device.access_token_hash is None

    def test_disabled_account_gets_not_in(self, session: Session) -> None:
        account = make_account(session)
        _, tokens = sessions.start_session(session, account)
        account.disabled_at = now()
        session.flush()

        with pytest.raises(UnauthenticatedError):
            sessions.authenticate(session, tokens.access_token)

    def test_the_error_reveals_the_reason_not(self, session: Session) -> None:
        """A Caller soll not distinguish can, ob a Token
        unknown, expired or widerrufen is; the would be a Disclosure
        through valid Token."""
        account = make_account(session)
        device, tokens = sessions.start_session(session, account)
        session.flush()
        sessions.revoke(device)
        session.flush()

        messages = set()
        for token in ["unbekannt", tokens.access_token]:
            with pytest.raises(UnauthenticatedError) as error:
                sessions.authenticate(session, token)
            messages.add(str(error.value))
        assert len(messages) == 1


class TestErneuern:
    def test_rotiert_beide_token(self, session: Session) -> None:
        account = make_account(session)
        _, first = sessions.start_session(session, account)
        session.flush()

        second = sessions.refresh_session(session, first.refresh_token)
        session.flush()

        assert second.refresh_token != first.refresh_token
        assert second.access_token != first.access_token
        assert sessions.authenticate(session, second.access_token).id == account.id

    def test_old_access_token_applies_after_dem_refresh_not_more(self, session: Session) -> None:
        account = make_account(session)
        _, first = sessions.start_session(session, account)
        session.flush()
        sessions.refresh_session(session, first.refresh_token)
        session.flush()

        with pytest.raises(UnauthenticatedError):
            sessions.authenticate(session, first.access_token)

    def test_expired_refresh_token_is_rejected(self, session: Session) -> None:
        account = make_account(session)
        device, tokens = sessions.start_session(session, account)
        device.expires_at = now() - timedelta(seconds=1)
        session.flush()

        with pytest.raises(UnauthenticatedError):
            sessions.refresh_session(session, tokens.refresh_token)

    def test_revoked_refresh_token_is_rejected(self, session: Session) -> None:
        account = make_account(session)
        device, tokens = sessions.start_session(session, account)
        sessions.revoke(device)
        session.flush()

        with pytest.raises(UnauthenticatedError):
            sessions.refresh_session(session, tokens.refresh_token)


class TestReplay:
    def test_reused_refresh_token_revokes_the_session_data(self, session: Session) -> None:
        """Appears a already rotated Token again on, is it kopiert
        worden; the rechtmaessige Client haette the new. Then may
        niemand more through, therefore not the Besitzer."""
        account = make_account(session)
        device, first = sessions.start_session(session, account)
        session.flush()

        second = sessions.refresh_session(session, first.refresh_token)
        session.flush()

        with pytest.raises(UnauthenticatedError):
            sessions.refresh_session(session, first.refresh_token)
        session.flush()

        assert device.revoked_at is not None
        with pytest.raises(UnauthenticatedError):
            sessions.authenticate(session, second.access_token)

    def test_oldest_generation_is_after_mehreren_rotationen_detected(
        self, session: Session
    ) -> None:
        """T0 -> T1 -> T2, then Replay from T0.

        A Zwei-Slot-Fenster from aktuellem and vorherigem Token loses T0
        after the zweiten Rotation from the Blick. The Token would zwar
        rejected, aber not more seiner Family zugeordnet; and the
        kompromittierte Session would run weiter.
        """
        account = make_account(session)
        device, t0 = sessions.start_session(session, account)
        session.flush()

        t1 = sessions.refresh_session(session, t0.refresh_token)
        session.flush()
        t2 = sessions.refresh_session(session, t1.refresh_token)
        session.flush()

        with pytest.raises(UnauthenticatedError):
            sessions.refresh_session(session, t0.refresh_token)
        session.flush()

        assert device.revoked_at is not None
        with pytest.raises(UnauthenticatedError):
            sessions.authenticate(session, t2.access_token)
        with pytest.raises(UnauthenticatedError):
            sessions.refresh_session(session, t2.refresh_token)

    def test_middle_generation_is_after_the_next_rotation_detected(self, session: Session) -> None:
        "Replay from T1, after T2 ausgestellt was."
        account = make_account(session)
        device, t0 = sessions.start_session(session, account)
        session.flush()

        t1 = sessions.refresh_session(session, t0.refresh_token)
        session.flush()
        t2 = sessions.refresh_session(session, t1.refresh_token)
        session.flush()

        with pytest.raises(UnauthenticatedError):
            sessions.refresh_session(session, t1.refresh_token)
        session.flush()

        assert device.revoked_at is not None
        with pytest.raises(UnauthenticatedError):
            sessions.authenticate(session, t2.access_token)

    def test_every_generation_remains_the_family_zugeordnet(self, session: Session) -> None:
        account = make_account(session)
        device, t0 = sessions.start_session(session, account)
        session.flush()

        t1 = sessions.refresh_session(session, t0.refresh_token)
        session.flush()
        sessions.refresh_session(session, t1.refresh_token)
        session.flush()

        consumed = (
            session.execute(
                select(ConsumedRefreshToken).where(
                    ConsumedRefreshToken.device_session_id == device.id
                )
            )
            .scalars()
            .all()
        )
        assert {entry.token_hash for entry in consumed} == {
            hash_token(t0.refresh_token),
            hash_token(t1.refresh_token),
        }

    def test_history_keeps_only_hashes(self, session: Session) -> None:
        "replay history must not become a second source of sign-in credentials."
        account = make_account(session)
        _, t0 = sessions.start_session(session, account)
        session.flush()
        sessions.refresh_session(session, t0.refresh_token)
        session.flush()

        entry = session.execute(select(ConsumedRefreshToken)).scalar_one()
        assert entry.token_hash == hash_token(t0.refresh_token)
        assert t0.refresh_token not in str(entry.__dict__)

    def test_replay_a_foreign_family_allows_other_sessions_leben(self, session: Session) -> None:
        account = make_account(session)
        affected, t0 = sessions.start_session(session, account)
        unaffected, other = sessions.start_session(session, account)
        session.flush()

        sessions.refresh_session(session, t0.refresh_token)
        session.flush()

        with pytest.raises(UnauthenticatedError):
            sessions.refresh_session(session, t0.refresh_token)
        session.flush()

        assert affected.revoked_at is not None
        assert unaffected.revoked_at is None
        assert sessions.authenticate(session, other.access_token).id == account.id

    def test_unknown_token_revokes_nothing(self, session: Session) -> None:
        """only a genuine token from the family may trigger revocation.

        Otherwise could every a fremde Session abschiessen, indem it
        beliebigen Unfug to the Refresh-Endpoint schickt.
        """
        account = make_account(session)
        device, tokens = sessions.start_session(session, account)
        session.flush()

        with pytest.raises(UnauthenticatedError):
            sessions.refresh_session(session, "gibt-es-nicht")
        session.flush()

        assert device.revoked_at is None
        assert sessions.authenticate(session, tokens.access_token).id == account.id

    def test_the_error_reveals_the_reason_not(self, session: Session) -> None:
        """unknown, expired, and replayed tokens must look identical.

        A unterscheidbarer Error would be the Disclosure, welcher Token
        once real war.
        """
        account = make_account(session)
        _, t0 = sessions.start_session(session, account)
        session.flush()
        sessions.refresh_session(session, t0.refresh_token)
        session.flush()

        expired_account = make_account(session, "Abgelaufen")
        expired_device, expired = sessions.start_session(session, expired_account)
        expired_device.expires_at = now() - timedelta(seconds=1)
        session.flush()

        messages = set()
        codes = set()
        for token in ["gibt-es-nicht", t0.refresh_token, expired.refresh_token]:
            with pytest.raises(UnauthenticatedError) as error:
                sessions.refresh_session(session, token)
            session.flush()
            messages.add(str(error.value))
            codes.add(error.value.code)
        assert len(messages) == 1
        assert len(codes) == 1


class TestAbsoluteLebensdauer:
    """the session family has a hard lifetime limit.

    Without it the session lifetime would be unbounded: the sliding window
    allows itself through regular Erneuern beliebig weit vorschieben,
    and with ihm waechst a Replay-History, the nie geraeumt is.
    """

    @staticmethod
    def _uhr(monkeypatch: pytest.MonkeyPatch, start: datetime) -> Callable[[datetime], None]:
        "A controllable clock for the session module."
        stand = {"jetzt": start}
        monkeypatch.setattr(sessions, "now", lambda: stand["jetzt"])

        def set_time(on: datetime) -> None:
            stand["jetzt"] = on

        return set_time

    @staticmethod
    def _halte_at_leben(
        session: Session,
        tokens: sessions.IssuedTokens,
        set_time: Callable[[datetime], None],
        *,
        von: datetime,
        until: datetime,
        schritt: timedelta = timedelta(days=14),
    ) -> tuple[sessions.IssuedTokens, datetime]:
        """The Session through regular Erneuern until kurz before `until` tragen.

        Without the would run the gleitende Fenster ab, and the Test would check the
        falsche Boundary.
        """
        zeitpunkt = von
        while zeitpunkt + schritt < until:
            zeitpunkt += schritt
            set_time(zeitpunkt)
            tokens = sessions.refresh_session(session, tokens.refresh_token)
            session.flush()
        return tokens, zeitpunkt

    def test_regular_refresh_moves_the_boundary_not(
        self, session: Session, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """The Core the Matter: the Family altert, therefore when it used is.

        A Client, the brav alle zwei Wochen erneuert, haelt the gleitende
        Fenster permanently open. The absolute Boundary may itself davon not
        bewegen, otherwise exists it no obere Schranke; weder for the Session
        still for ihre History.
        """
        beginn = now()
        set_time = self._uhr(monkeypatch, beginn)

        account = make_account(session)
        device, tokens = sessions.start_session(session, account)
        session.flush()

        boundary = device.absolute_expires_at
        assert boundary == beginn + SESSION_ABSOLUTE_LIFETIME

        schritt = timedelta(days=14)
        zeitpunkt = beginn
        while zeitpunkt + schritt < boundary:
            zeitpunkt += schritt
            set_time(zeitpunkt)
            tokens = sessions.refresh_session(session, tokens.refresh_token)
            session.flush()

            assert device.absolute_expires_at == boundary, "the Boundary is mitgewandert"
            assert device.expires_at > zeitpunkt

        # Zwischenstand: the Session is alive kurz before the Boundary still.
        assert zeitpunkt > beginn + timedelta(days=150)
        assert sessions.authenticate(session, tokens.access_token).id == account.id

        set_time(boundary + timedelta(seconds=1))
        with pytest.raises(UnauthenticatedError):
            sessions.refresh_session(session, tokens.refresh_token)
        session.flush()

    def test_sliding_window_ueberholt_the_boundary_not(
        self, session: Session, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        "Otherwise the response would name to expiry date that does not apply."
        beginn = now()
        set_time = self._uhr(monkeypatch, beginn)

        account = make_account(session)
        device, tokens = sessions.start_session(session, account)
        session.flush()

        short_davor = device.absolute_expires_at - timedelta(hours=1)
        tokens, _ = self._halte_at_leben(session, tokens, set_time, von=beginn, until=short_davor)

        set_time(short_davor)
        refreshed = sessions.refresh_session(session, tokens.refresh_token)
        session.flush()

        assert refreshed.refresh_expires_at == device.absolute_expires_at
        assert refreshed.refresh_expires_at < short_davor + REFRESH_TOKEN_LIFETIME
        assert refreshed.access_expires_at <= device.absolute_expires_at

    def test_access_token_endet_with_the_family(
        self, session: Session, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        "A kurz before the Boundary ausgestellter Token may it not outlive."
        beginn = now()
        set_time = self._uhr(monkeypatch, beginn)

        account = make_account(session)
        device, tokens = sessions.start_session(session, account)
        session.flush()

        short_davor = device.absolute_expires_at - timedelta(minutes=1)
        tokens, _ = self._halte_at_leben(session, tokens, set_time, von=beginn, until=short_davor)

        set_time(short_davor)
        refreshed = sessions.refresh_session(session, tokens.refresh_token)
        session.flush()
        assert sessions.authenticate(session, refreshed.access_token).id == account.id

        set_time(device.absolute_expires_at + timedelta(seconds=1))
        assert refreshed.access_expires_at > beginn
        with pytest.raises(UnauthenticatedError):
            sessions.authenticate(session, refreshed.access_token)

    def test_history_a_permanently_genutzten_family_is_endlich(
        self, session: Session, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """The eigentliche Zweck the Boundary.

        Erst weil the Family endet, endet therefore ihre History. Would be the
        Session unbegrenzt verlaengerbar, would be the Table it therefore.
        """
        beginn = now()
        set_time = self._uhr(monkeypatch, beginn)

        account = make_account(session)
        device, tokens = sessions.start_session(session, account)
        session.flush()

        zeitpunkt = beginn
        schritt = timedelta(days=14)
        while zeitpunkt + schritt < device.absolute_expires_at:
            zeitpunkt += schritt
            set_time(zeitpunkt)
            tokens = sessions.refresh_session(session, tokens.refresh_token)
            session.flush()

        gesammelt = session.execute(select(ConsumedRefreshToken)).scalars().all()
        assert len(gesammelt) > 1

        # While the Family is alive, remains every Generation zuordenbar.
        assert sessions.prune_replay_history(session) == 0

        set_time(device.absolute_expires_at + sessions.REPLAY_HISTORY_RETENTION + timedelta(days=1))
        assert sessions.prune_replay_history(session) == len(gesammelt)
        session.flush()
        assert session.execute(select(ConsumedRefreshToken)).scalars().all() == []

    def test_replay_remains_until_zur_boundary_via_all_generations_erkennbar(
        self, session: Session, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        "The Boundary may no Historienfenster through the Hintertuer be."
        beginn = now()
        set_time = self._uhr(monkeypatch, beginn)

        account = make_account(session)
        device, t0 = sessions.start_session(session, account)
        session.flush()

        tokens = t0
        zeitpunkt = beginn
        for _ in range(10):
            zeitpunkt += timedelta(days=14)
            set_time(zeitpunkt)
            tokens = sessions.refresh_session(session, tokens.refresh_token)
            session.flush()

        # The allererste Generation, viele Rotationen and Months later.
        with pytest.raises(UnauthenticatedError):
            sessions.refresh_session(session, t0.refresh_token)
        session.flush()

        assert device.revoked_at is not None

    def test_new_sign_in_starts_a_new_family(
        self, session: Session, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        "After the Boundary hilft only Re-Authentifizierung."
        beginn = now()
        set_time = self._uhr(monkeypatch, beginn)

        account = make_account(session)
        alt_device, alt = sessions.start_session(session, account)
        session.flush()

        after_the_boundary = alt_device.absolute_expires_at + timedelta(days=1)
        set_time(after_the_boundary)
        with pytest.raises(UnauthenticatedError):
            sessions.refresh_session(session, alt.refresh_token)
        session.flush()

        new_device, new = sessions.start_session(session, account)
        session.flush()

        assert new_device.id != alt_device.id
        assert new_device.absolute_expires_at == after_the_boundary + SESSION_ABSOLUTE_LIFETIME
        assert sessions.authenticate(session, new.access_token).id == account.id

    def test_fresh_session_data_keeps_beide_window_auseinander(self, session: Session) -> None:
        account = make_account(session)
        device, tokens = sessions.start_session(session, account)
        session.flush()

        assert device.expires_at < device.absolute_expires_at
        assert device.absolute_expires_at - device.expires_at == (
            SESSION_ABSOLUTE_LIFETIME - REFRESH_TOKEN_LIFETIME
        )
        assert tokens.access_expires_at - now() <= ACCESS_TOKEN_LIFETIME


class TestReplayHistorieAufraeumen:
    def test_active_session_data_behaelt_ihre_history(self, session: Session) -> None:
        "The History a lebenden Family IS the Replay-Erkennung."
        account = make_account(session)
        _, t0 = sessions.start_session(session, account)
        session.flush()
        sessions.refresh_session(session, t0.refresh_token)
        session.flush()

        assert sessions.prune_replay_history(session) == 0
        session.flush()
        assert session.execute(select(ConsumedRefreshToken)).scalars().all()

    def test_ended_session_data_is_after_the_retention_period_geraeumt(
        self, session: Session
    ) -> None:
        account = make_account(session)
        device, t0 = sessions.start_session(session, account)
        session.flush()
        sessions.refresh_session(session, t0.refresh_token)
        session.flush()

        sessions.revoke(device)
        device.revoked_at = now() - sessions.REPLAY_HISTORY_RETENTION - timedelta(days=1)
        session.flush()

        assert sessions.prune_replay_history(session) == 1
        session.flush()
        assert session.execute(select(ConsumedRefreshToken)).scalars().all() == []

    def test_fresh_revoked_session_data_remains_zunaechst_stehen(self, session: Session) -> None:
        account = make_account(session)
        device, t0 = sessions.start_session(session, account)
        session.flush()
        sessions.refresh_session(session, t0.refresh_token)
        sessions.revoke(device)
        session.flush()

        assert sessions.prune_replay_history(session) == 0

    def test_expired_session_data_is_without_widerruf_geraeumt(self, session: Session) -> None:
        account = make_account(session)
        device, t0 = sessions.start_session(session, account)
        session.flush()
        sessions.refresh_session(session, t0.refresh_token)
        device.expires_at = now() - sessions.REPLAY_HISTORY_RETENTION - timedelta(days=1)
        session.flush()

        assert sessions.prune_replay_history(session) == 1

    def test_deleted_session_data_nimmt_ihre_history_with(self, session: Session) -> None:
        "The Foreign key raeumt kaskadierend on."
        account = make_account(session)
        device, t0 = sessions.start_session(session, account)
        session.flush()
        sessions.refresh_session(session, t0.refresh_token)
        session.flush()

        session.delete(device)
        session.flush()

        assert session.execute(select(ConsumedRefreshToken)).scalars().all() == []


class TestAlleWiderrufen:
    def test_ended_every_offene_session_data(self, session: Session) -> None:
        account = make_account(session)
        tokens = [sessions.start_session(session, account)[1] for _ in range(3)]
        session.flush()

        assert sessions.revoke_all(session, account) == 3
        session.flush()

        for satz in tokens:
            with pytest.raises(UnauthenticatedError):
                sessions.authenticate(session, satz.access_token)

    def test_allows_foreign_sessions_unberuehrt(self, session: Session) -> None:
        eigen = make_account(session, "Eigen")
        foreign = make_account(session, "Fremd")
        _, foreign_tokens = sessions.start_session(session, foreign)
        sessions.start_session(session, eigen)
        session.flush()

        sessions.revoke_all(session, eigen)
        session.flush()

        assert sessions.authenticate(session, foreign_tokens.access_token).id == foreign.id
        offen = (
            session.execute(
                select(DeviceSession).where(
                    DeviceSession.account_id == foreign.id,
                    DeviceSession.revoked_at.is_(None),
                )
            )
            .scalars()
            .all()
        )
        assert len(offen) == 1


class TestRotationsflut:
    """Successful rotations are themselves limited.

    Without this boundary a client with a valid token could, in a tight
    loop, create arbitrarily many generations and therefore arbitrarily many rows
    Replay-History erzeugen. The absolute Lebensdauer makes the Wachstum
    endlich, aber not langsam.
    """

    def test_budget_limits_the_rotationen(self, session: Session) -> None:
        account = make_account(session)
        _, tokens = sessions.start_session(session, account)
        session.flush()

        token = tokens.refresh_token
        for _ in range(rate_limit.REFRESH.attempts):
            token = sessions.refresh_session(session, token).refresh_token
            session.flush()

        with pytest.raises(RateLimitedError):
            sessions.refresh_session(session, token)

    def test_the_boundary_belongs_to_the_session_data_and_not_at_token(
        self, session: Session
    ) -> None:
        "the token value changes on each rotation; the counter does not."
        account = make_account(session)
        device, tokens = sessions.start_session(session, account)
        session.flush()

        token = tokens.refresh_token
        for _ in range(3):
            token = sessions.refresh_session(session, token).refresh_token
            session.flush()

        key = (
            session.execute(
                select(RateLimitEvent.key_hash).where(RateLimitEvent.action == "refresh")
            )
            .scalars()
            .all()
        )
        assert len(key) == 3
        assert set(key) == {hash_token(str(device.id))}

    def test_other_session_data_same_accounts_remains_frei(self, session: Session) -> None:
        account = make_account(session)
        _, first = sessions.start_session(session, account, device_name="Pixel")
        _, second = sessions.start_session(session, account, device_name="Laptop")
        session.flush()

        token = first.refresh_token
        for _ in range(rate_limit.REFRESH.attempts):
            token = sessions.refresh_session(session, token).refresh_token
            session.flush()
        with pytest.raises(RateLimitedError):
            sessions.refresh_session(session, token)

        assert sessions.refresh_session(session, second.refresh_token).refresh_token

    def test_unknown_token_remains_401_and_is_not_gezaehlt(self, session: Session) -> None:
        "a 429 must not disclose that a session exists."
        account = make_account(session)
        _, tokens = sessions.start_session(session, account)
        session.flush()
        sessions.refresh_session(session, tokens.refresh_token)
        session.flush()

        with pytest.raises(UnauthenticatedError):
            sessions.refresh_session(session, "voellig-unbekannt")

        attempts = session.execute(
            select(func.count())
            .select_from(RateLimitEvent)
            .where(RateLimitEvent.action == "refresh")
        ).scalar_one()
        assert attempts == 1

    def test_replay_remains_401_and_revokes_weiterhin(self, session: Session) -> None:
        account = make_account(session)
        device, tokens = sessions.start_session(session, account)
        session.flush()
        sessions.refresh_session(session, tokens.refresh_token)
        session.flush()

        with pytest.raises(UnauthenticatedError):
            sessions.refresh_session(session, tokens.refresh_token)
        assert device.revoked_at is not None
