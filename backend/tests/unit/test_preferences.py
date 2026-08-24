"""Zeitzone und Locale an der Schreibgrenze."""

from __future__ import annotations

import pytest

from sidebyside.core.errors import ValidationError
from sidebyside.identity.preferences import (
    PreferenceErrorCode,
    normalize_locale,
    validate_timezone,
)


class TestZeitzone:
    @pytest.mark.parametrize("zone", ["Europe/Berlin", "UTC", "America/Argentina/Ushuaia"])
    def test_bekannte_zone_wird_unveraendert_uebernommen(self, zone: str) -> None:
        assert validate_timezone(zone) == zone

    def test_umgebender_leerraum_faellt_weg(self) -> None:
        assert validate_timezone("  Europe/Berlin  ") == "Europe/Berlin"

    @pytest.mark.parametrize(
        "zone",
        [
            "",
            "   ",
            "Europe/Berlinn",
            "europe/berlin",
            "MEZ",
            "+01:00",
            "Europe/Berlin; DROP TABLE accounts",
            "A" * 65,
        ],
    )
    def test_unbrauchbare_zone_wird_abgewiesen(self, zone: str) -> None:
        with pytest.raises(ValidationError) as fehler:
            validate_timezone(zone)
        assert fehler.value.code == PreferenceErrorCode.TIMEZONE_INVALID

    def test_die_pruefung_geht_gegen_die_zonendatenbank(self) -> None:
        """Ein Muster wuerde 'Europe/Berlinn' durchlassen - es sieht richtig aus."""
        with pytest.raises(ValidationError):
            validate_timezone("Europe/Berlinn")


class TestLocale:
    @pytest.mark.parametrize(
        ("eingabe", "erwartet"),
        [
            ("de-DE", "de-DE"),
            ("de_DE", "de-DE"),
            ("DE-de", "de-DE"),
            ("de", "de"),
            ("en-US", "en-US"),
            ("zh-hans-cn", "zh-Hans-CN"),
            ("es-419", "es-419"),
            ("  fr-fr  ", "fr-FR"),
        ],
    )
    def test_kanonische_schreibweise(self, eingabe: str, erwartet: str) -> None:
        assert normalize_locale(eingabe) == erwartet

    def test_normalisieren_ist_stabil(self) -> None:
        """Gespeicherter und ausgelieferter Wert muessen derselbe sein."""
        einmal = normalize_locale("zh_hans_cn")
        assert normalize_locale(einmal) == einmal

    @pytest.mark.parametrize(
        "eingabe",
        [
            "",
            "   ",
            "deutsch",
            "d",
            "de-DEUTSCHLAND",
            "de-DE-1996",
            "de-DE@euro",
            "de/DE",
            "12",
            "de-" + "x" * 20,
        ],
    )
    def test_unbrauchbare_locale_wird_abgewiesen(self, eingabe: str) -> None:
        with pytest.raises(ValidationError) as fehler:
            normalize_locale(eingabe)
        assert fehler.value.code == PreferenceErrorCode.LOCALE_INVALID
