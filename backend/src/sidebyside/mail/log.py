"""Development mail adapter.

It writes the message to logs so a magic link can be exercised without a mail
server. That is exactly why it must never run in production: the token would be
logged as well. Configuration rejects that mode at startup.
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
        environment = get_settings().environment
        if environment is Environment.PRODUCTION:
            # Defense in depth. Configuration already prevents this adapter in
            # production; if it still reaches this path, do not expose content.
            raise RuntimeError("The logging mail adapter is not allowed in production.")

        log.info(
            "mail (development transport)",
            extra={"to": message.to, "subject": message.subject},
        )
        log.info("mail body:\n%s", message.body)
