"""Die Grenze zum Mailversand."""

from __future__ import annotations

import smtplib
from typing import Any

import pytest

from sidebyside.config import Environment, get_settings
from sidebyside.mail import LoggingMailSender, MailMessage, MailTransportError, SmtpMailSender


class TestNachricht:
    def test_normale_nachricht(self) -> None:
        nachricht = MailMessage(to="anna@example.org", subject="Hallo", body="Text")
        assert nachricht.to == "anna@example.org"

    @pytest.mark.parametrize(
        ("empfaenger", "betreff"),
        [
            ("anna@example.org\nBcc: mit@example.org", "Hallo"),
            ("anna@example.org", "Hallo\r\nBcc: mit@example.org"),
        ],
    )
    def test_zeilenumbruch_waere_eine_header_injection(self, empfaenger: str, betreff: str) -> None:
        with pytest.raises(ValueError):
            MailMessage(to=empfaenger, subject=betreff, body="Text")

    @pytest.mark.parametrize(("empfaenger", "betreff"), [("", "Hallo"), ("a@b.de", "  ")])
    def test_leere_pflichtfelder(self, empfaenger: str, betreff: str) -> None:
        with pytest.raises(ValueError):
            MailMessage(to=empfaenger, subject=betreff, body="Text")


class TestLogAdapter:
    def test_in_produktion_verweigert_er_den_dienst(self, monkeypatch) -> None:  # type: ignore[no-untyped-def]
        """Sonst stuende ein gueltiger Einmal-Token im Log."""
        settings = get_settings().model_copy(update={"environment": Environment.PRODUCTION})
        monkeypatch.setattr("sidebyside.mail.log.get_settings", lambda: settings)

        with pytest.raises(RuntimeError):
            LoggingMailSender().send(MailMessage(to="a@b.de", subject="x", body="y"))

    def test_in_der_entwicklung_schreibt_er_die_nachricht(self, caplog) -> None:  # type: ignore[no-untyped-def]
        with caplog.at_level("INFO"):
            LoggingMailSender().send(MailMessage(to="a@b.de", subject="x", body="link"))
        assert "link" in caplog.text


class TestSmtpAdapter:
    def test_zustellfehler_wird_zum_eigenen_typ(self, monkeypatch) -> None:  # type: ignore[no-untyped-def]
        """Der Aufrufer soll einen Zustellfehler ohne Textvergleich erkennen."""

        def kaputt(*args: Any, **kwargs: Any) -> None:
            raise smtplib.SMTPException("kein Server")

        monkeypatch.setattr(smtplib, "SMTP", kaputt)
        adapter = SmtpMailSender(host="localhost", port=25, sender_address="no-reply@localhost")

        with pytest.raises(MailTransportError):
            adapter.send(MailMessage(to="a@b.de", subject="x", body="y"))

    def test_netzwerkfehler_ebenso(self, monkeypatch) -> None:  # type: ignore[no-untyped-def]
        def kaputt(*args: Any, **kwargs: Any) -> None:
            raise OSError("keine Route")

        monkeypatch.setattr(smtplib, "SMTP", kaputt)
        adapter = SmtpMailSender(host="localhost", port=25, sender_address="no-reply@localhost")

        with pytest.raises(MailTransportError):
            adapter.send(MailMessage(to="a@b.de", subject="x", body="y"))
