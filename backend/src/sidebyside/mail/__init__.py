"""Ausgehende E-Mail.

Ein Magic Link, der nur im Log landet, ist kein Anmeldeweg. Deshalb gibt
es hier eine echte Grenze mit drei Adaptern: einer schreibt ins Log und ist
fuer die Entwicklung gedacht, einer spricht SMTP, und einer versendet
ausdruecklich nichts.

Welcher gilt, entscheidet die Konfiguration - und in Produktion verweigert
die Anwendung den Start, wenn dort der Entwicklungsadapter stehen bleibt.
Der Verzicht dagegen ist erlaubt: eine Instanz ohne Mailserver ist eine
zulaessige Betriebsform, solange sie das offen sagt statt Token zu verlieren.
"""

from __future__ import annotations

from sidebyside.mail.base import (
    MailMessage,
    MailSender,
    MailTransportError,
    MailUnavailableError,
)
from sidebyside.mail.log import LoggingMailSender
from sidebyside.mail.smtp import SmtpMailSender

__all__ = [
    "LoggingMailSender",
    "MailMessage",
    "MailSender",
    "MailTransportError",
    "MailUnavailableError",
    "SmtpMailSender",
    "sender",
]


def sender() -> MailSender:
    """Den konfigurierten Adapter bauen.

    Bewusst kein zwischengespeichertes Modul-Singleton: der Adapter ist
    billig zu bauen, und ein Test soll die Konfiguration wechseln koennen,
    ohne einen Zustand zurueckdrehen zu muessen.
    """
    from sidebyside.config import MailTransport, get_settings

    settings = get_settings()
    if settings.mail_transport is MailTransport.NONE:
        raise MailUnavailableError
    if settings.mail_transport is MailTransport.SMTP:
        return SmtpMailSender(
            host=settings.smtp_host,
            port=settings.smtp_port,
            username=settings.smtp_username,
            password=(
                settings.smtp_password.get_secret_value()
                if settings.smtp_password is not None
                else ""
            ),
            use_starttls=settings.smtp_starttls,
            sender_address=settings.mail_from,
        )
    return LoggingMailSender(sender_address=settings.mail_from)
