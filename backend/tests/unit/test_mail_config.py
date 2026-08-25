"""Konfigurationsgrenzen fuer den Mailversand."""

from __future__ import annotations

import pytest

from sidebyside.config import Settings


def produktion(**ueberschreibungen: object) -> Settings:
    werte: dict[str, object] = {
        "environment": "production",
        "allowed_hosts": ["sidebyside.example"],
        "mail_transport": "smtp",
        "public_base_url": "https://sidebyside.example",
        "cursor_signing_key": "cursor-test-" + ("x" * 40),
    }
    werte.update(ueberschreibungen)
    return Settings(**werte)  # type: ignore[arg-type]


class TestProduktion:
    def test_vollstaendige_konfiguration_startet(self) -> None:
        assert produktion().mail_transport.value == "smtp"

    def test_log_versand_verweigert_den_start(self) -> None:
        """Eine Instanz, die Anmeldelinks ins Log schreibt, faellt sonst niemandem auf."""
        with pytest.raises(ValueError, match="SBS_MAIL_TRANSPORT"):
            produktion(mail_transport="log")

    def test_unverschluesselte_basisadresse_verweigert_den_start(self) -> None:
        with pytest.raises(ValueError, match="SBS_PUBLIC_BASE_URL"):
            produktion(public_base_url="http://sidebyside.example")
