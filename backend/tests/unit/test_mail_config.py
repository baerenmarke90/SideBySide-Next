"""Configuration boundaries for mail delivery."""

from __future__ import annotations

import pytest

from sidebyside.config import Settings


def production(**overrides: object) -> Settings:
    values: dict[str, object] = {
        "environment": "production",
        "allowed_hosts": ["sidebyside.example"],
        "mail_transport": "smtp",
        "public_base_url": "https://sidebyside.example",
        "cursor_signing_key": "cursor-test-" + ("x" * 40),
    }
    values.update(overrides)
    return Settings(**values)  # type: ignore[arg-type]


class TestProduction:
    def test_complete_configuration_starts(self) -> None:
        assert production().mail_transport.value == "smtp"

    def test_log_delivery_refuses_startup(self) -> None:
        """An instance logging sign-in links could otherwise go unnoticed."""
        with pytest.raises(ValueError, match="SBS_MAIL_TRANSPORT"):
            production(mail_transport="log")

    def test_unencrypted_base_url_refuses_startup(self) -> None:
        with pytest.raises(ValueError, match="SBS_PUBLIC_BASE_URL"):
            production(public_base_url="http://sidebyside.example")

    def test_disabling_mail_is_allowed(self) -> None:
        """An instance without a mail server is a valid operating mode.

        The distinction from `log` is substantive: with `none`, no one-time
        token leaves the system, whereas `log` writes each token to log storage.
        """
        assert production(mail_transport="none").mail_transport.value == "none"
