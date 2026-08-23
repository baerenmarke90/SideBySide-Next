"""Zeitkonventionen."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta, timezone

from sidebyside.core.clock import ensure_utc, now, today_utc


class TestNow:
    def test_ist_zeitzonen_bewusst(self) -> None:
        """Ein naiver Zeitstempel darf in diesem Projekt nicht entstehen."""
        assert now().tzinfo is not None

    def test_steht_in_utc(self) -> None:
        assert now().utcoffset() == timedelta(0)


class TestEnsureUtc:
    def test_rechnet_eine_andere_zone_um(self) -> None:
        berlin = timezone(timedelta(hours=2))
        wert = datetime(2026, 8, 23, 14, 12, tzinfo=berlin)
        assert ensure_utc(wert) == datetime(2026, 8, 23, 12, 12, tzinfo=UTC)

    def test_liest_einen_naiven_wert_als_utc(self) -> None:
        wert = datetime(2026, 8, 23, 12, 12)
        assert ensure_utc(wert) == datetime(2026, 8, 23, 12, 12, tzinfo=UTC)

    def test_laesst_utc_unveraendert(self) -> None:
        wert = datetime(2026, 8, 23, 12, 12, tzinfo=UTC)
        assert ensure_utc(wert) == wert


class TestTodayUtc:
    def test_ist_ein_datum_ohne_uhrzeit(self) -> None:
        heute = today_utc()
        assert not isinstance(heute, datetime)
        assert heute == now().date()
