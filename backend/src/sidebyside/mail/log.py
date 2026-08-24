"""Der Entwicklungsadapter.

Er schreibt die Nachricht ins Log, damit ein Magic Link ohne Mailserver
ausprobierbar ist. Genau deshalb darf er in Produktion nicht laufen - der
Token stuende dann im Log. Die Konfiguration verhindert das beim Start.
"""

from __future__ import annotations

import logging

from sidebyside.config import Environment, get_settings
from sidebyside.mail.base import MailMessage, MailSender

log = logging.getLogger(__name__)


class LoggingMailSender(MailSender):
    def __init__(self, sender_address: str = "") -> None:
        self.sender_address = sender_address

    def send(self, message: MailMessage) -> None:
        umgebung = get_settings().environment
        if umgebung is Environment.PRODUCTION:
            # Doppelter Boden. Die Konfiguration laesst diesen Adapter in
            # Produktion gar nicht erst zu; faende er trotzdem einen Weg
            # dorthin, schweigt er ueber den Inhalt.
            raise RuntimeError("Der Log-Mailadapter ist in Produktion nicht zulaessig.")

        log.info(
            "mail (development transport)",
            extra={"to": message.to, "subject": message.subject},
        )
        log.info("mail body:\n%s", message.body)
