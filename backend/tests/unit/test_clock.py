"""Zeitkonventionen."""

from __future__ import annotations

from datetime import UTC, date, datetime, timedelta, timezone

import pytest

from sidebyside.core.clock import ensure_utc, now, resolve_zone, today_in, today_utc


def today_utc_at(zeitpunkt: datetime) -> date:
    """Der UTC-Tag zu einem festen Zeitpunkt - der Vergleichsmassstab."""
    return zeitpunkt.date()


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


class TestResolveZone:
    def test_loest_eine_benannte_zone_auf(self) -> None:
        assert resolve_zone("Europe/Berlin").key == "Europe/Berlin"

    @pytest.mark.parametrize(
        "name",
        ["", "Nicht/Echt", "../../etc/localtime", "UTC+2", "Europe/Bärlin"],
    )
    def test_unbekannte_zone_faellt_auf_utc_zurueck(self, name: str) -> None:
        """`Account.timezone` ist ein freies Textfeld.

        Ein unbrauchbarer Wert darf eine Leseanfrage nicht mit 500 beenden.
        """
        assert resolve_zone(name).key == "UTC"


class TestTodayIn:
    def test_oestlich_von_utc_ist_der_tag_schon_weiter(self) -> None:
        """In Auckland ist es bereits der naechste Tag, in UTC noch nicht."""
        zeitpunkt = datetime(2026, 8, 24, 12, 30, tzinfo=UTC)
        assert today_in("Pacific/Auckland", at=zeitpunkt) == date(2026, 8, 25)
        assert today_utc_at(zeitpunkt) == date(2026, 8, 24)

    def test_westlich_von_utc_ist_der_tag_noch_zurueck(self) -> None:
        """In Los Angeles ist noch der Vortag, in UTC schon der naechste."""
        zeitpunkt = datetime(2026, 8, 25, 5, 0, tzinfo=UTC)
        assert today_in("America/Los_Angeles", at=zeitpunkt) == date(2026, 8, 24)
        assert today_utc_at(zeitpunkt) == date(2026, 8, 25)

    def test_derselbe_zeitpunkt_ergibt_zwei_verschiedene_tage(self) -> None:
        zeitpunkt = datetime(2026, 8, 24, 12, 30, tzinfo=UTC)
        assert today_in("Pacific/Auckland", at=zeitpunkt) != today_in(
            "America/Los_Angeles", at=zeitpunkt
        )

    def test_sommerzeit_wird_beruecksichtigt(self) -> None:
        """Berlin steht im August auf UTC+2; um 22:30 UTC ist dort schon
        der naechste Tag."""
        assert today_in("Europe/Berlin", at=datetime(2026, 8, 24, 22, 30, tzinfo=UTC)) == date(
            2026, 8, 25
        )

    def test_winterzeit_verschiebt_die_grenze(self) -> None:
        """Im Dezember steht Berlin auf UTC+1; um 22:30 UTC ist dort noch
        derselbe Tag."""
        assert today_in("Europe/Berlin", at=datetime(2026, 12, 24, 22, 30, tzinfo=UTC)) == date(
            2026, 12, 24
        )

    def test_ein_naiver_zeitpunkt_wird_als_utc_gelesen(self) -> None:
        assert today_in("Pacific/Auckland", at=datetime(2026, 8, 24, 12, 30)) == date(2026, 8, 25)

    def test_ohne_zeitpunkt_zaehlt_die_aktuelle_zeit(self) -> None:
        assert today_in("UTC") == now().date()

    def test_unbekannte_zone_ergibt_den_utc_tag(self) -> None:
        zeitpunkt = datetime(2026, 8, 24, 12, 30, tzinfo=UTC)
        assert today_in("Nicht/Echt", at=zeitpunkt) == date(2026, 8, 24)
