"""Gemeinsame Zeit - reine Kalenderrechnung."""

from __future__ import annotations

from datetime import date

from sidebyside.relationship.duration import since


class TestRechnung:
    def test_ganze_jahre_und_monate(self) -> None:
        gemeinsam = since(date(2022, 5, 17), date(2026, 8, 23))
        assert gemeinsam is not None
        assert (gemeinsam.years, gemeinsam.months) == (4, 3)

    def test_zaehlt_tage(self) -> None:
        gemeinsam = since(date(2026, 8, 1), date(2026, 8, 23))
        assert gemeinsam is not None
        assert gemeinsam.days == 22

    def test_am_ersten_tag_ist_alles_null(self) -> None:
        gemeinsam = since(date(2026, 8, 23), date(2026, 8, 23))
        assert gemeinsam is not None
        assert (gemeinsam.days, gemeinsam.years, gemeinsam.months) == (0, 0, 0)

    def test_monat_noch_nicht_voll(self) -> None:
        """Am 16. ist der am 17. begonnene Monat noch nicht um."""
        gemeinsam = since(date(2022, 5, 17), date(2026, 8, 16))
        assert gemeinsam is not None
        assert (gemeinsam.years, gemeinsam.months) == (4, 2)

    def test_jahreswechsel(self) -> None:
        gemeinsam = since(date(2025, 11, 30), date(2026, 1, 15))
        assert gemeinsam is not None
        assert (gemeinsam.years, gemeinsam.months) == (0, 1)

    def test_schaltjahr(self) -> None:
        gemeinsam = since(date(2024, 2, 29), date(2025, 3, 1))
        assert gemeinsam is not None
        assert gemeinsam.years == 1


class TestZukunft:
    def test_ein_datum_in_der_zukunft_ergibt_nichts(self) -> None:
        """Negative Werte waeren schlimmer als nichts - eine Oberflaeche
        wuerde daraus "-3 Tage zusammen" bauen."""
        assert since(date(2026, 12, 1), date(2026, 8, 23)) is None
