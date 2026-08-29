"""Boundary to outgoing mail delivery."""

from __future__ import annotations

import smtplib
from typing import Any

import pytest

from sidebyside.config import Environment, get_settings
from sidebyside.mail import LoggingMailSender, MailMessage, MailTransportError, SmtpMailSender


class TestMessage:
    def test_normal_message(self) -> None:
        message = MailMessage(to="anna@example.org", subject="Hallo", body="Text")
        assert message.to == "anna@example.org"

    @pytest.mark.parametrize(
        ("recipient", "subject"),
        [
            ("anna@example.org\nBcc: mit@example.org", "Hallo"),
            ("anna@example.org", "Hallo\r\nBcc: mit@example.org"),
        ],
    )
    def test_line_break_would_be_header_injection(self, recipient: str, subject: str) -> None:
        with pytest.raises(ValueError):
            MailMessage(to=recipient, subject=subject, body="Text")

    @pytest.mark.parametrize(("recipient", "subject"), [("", "Hallo"), ("a@b.de", "  ")])
    def test_empty_required_fields(self, recipient: str, subject: str) -> None:
        with pytest.raises(ValueError):
            MailMessage(to=recipient, subject=subject, body="Text")


class TestLogAdapter:
    def test_refuses_service_in_production(self, monkeypatch) -> None:  # type: ignore[no-untyped-def]
        """Otherwise a valid one-time token would appear in the log."""
        settings = get_settings().model_copy(update={"environment": Environment.PRODUCTION})
        monkeypatch.setattr("sidebyside.mail.log.get_settings", lambda: settings)

        with pytest.raises(RuntimeError):
            LoggingMailSender().send(MailMessage(to="a@b.de", subject="x", body="y"))

    def test_writes_message_in_development(self, caplog) -> None:  # type: ignore[no-untyped-def]
        with caplog.at_level("INFO"):
            LoggingMailSender().send(MailMessage(to="a@b.de", subject="x", body="link"))
        assert "link" in caplog.text


class TestSmtpAdapter:
    def test_delivery_failure_becomes_its_own_type(self, monkeypatch) -> None:  # type: ignore[no-untyped-def]
        """The caller can recognize a delivery failure without text matching."""

        def broken(*args: Any, **kwargs: Any) -> None:
            raise smtplib.SMTPException("no server")

        monkeypatch.setattr(smtplib, "SMTP", broken)
        adapter = SmtpMailSender(host="localhost", port=25, sender_address="no-reply@localhost")

        with pytest.raises(MailTransportError):
            adapter.send(MailMessage(to="a@b.de", subject="x", body="y"))

    def test_network_failure_becomes_the_same_type(self, monkeypatch) -> None:  # type: ignore[no-untyped-def]
        def broken(*args: Any, **kwargs: Any) -> None:
            raise OSError("no route")

        monkeypatch.setattr(smtplib, "SMTP", broken)
        adapter = SmtpMailSender(host="localhost", port=25, sender_address="no-reply@localhost")

        with pytest.raises(MailTransportError):
            adapter.send(MailMessage(to="a@b.de", subject="x", body="y"))
