"""Der SMTP-Adapter.

`smtplib` aus der Standardbibliothek. Ein eigener Client waere eine
Abhaengigkeit fuer ein Protokoll, das Python seit jeher mitbringt.
"""

from __future__ import annotations

import logging
import smtplib
from email.message import EmailMessage

from sidebyside.mail.base import MailMessage, MailSender, MailTransportError

log = logging.getLogger(__name__)

TIMEOUT_SECONDS = 15.0
"""Ein haengender Mailserver darf keine Anfrage festhalten."""


class SmtpMailSender(MailSender):
    def __init__(
        self,
        *,
        host: str,
        port: int,
        username: str = "",
        password: str = "",
        use_starttls: bool = True,
        sender_address: str,
    ) -> None:
        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self.use_starttls = use_starttls
        self.sender_address = sender_address

    def send(self, message: MailMessage) -> None:
        nachricht = EmailMessage()
        nachricht["From"] = self.sender_address
        nachricht["To"] = message.to
        nachricht["Subject"] = message.subject
        nachricht.set_content(message.body)

        try:
            with smtplib.SMTP(self.host, self.port, timeout=TIMEOUT_SECONDS) as verbindung:
                if self.use_starttls:
                    verbindung.starttls()
                if self.username:
                    verbindung.login(self.username, self.password)
                verbindung.send_message(nachricht)
        except (OSError, smtplib.SMTPException) as fehler:
            # Ohne den eigenen Typ und ohne diese Grenze staende der
            # Fehlertext - und mit ihm moeglicherweise der Empfaenger - in
            # einer Antwort an den Aufrufer.
            log.warning("mail transport failed", extra={"host": self.host})
            raise MailTransportError("Die Nachricht konnte nicht zugestellt werden.") from fehler
