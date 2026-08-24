"""Die Grenze zum Mailversand.

Der Application Core kennt weder SMTP noch einen Anbieter. Er kennt eine
Nachricht und einen Versender.

Eine Regel gilt fuer jede Implementierung: **der Inhalt gehoert nicht ins
Log.** Eine Anmelde-Mail traegt einen gueltigen Einmal-Token; ein Log, das
ihn mitschreibt, ist eine zweite Kopie des Anmeldenachweises an einer
Stelle mit ganz anderer Aufbewahrung und ganz anderem Zugriff.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass


class MailTransportError(RuntimeError):
    """Die Nachricht konnte nicht uebergeben werden.

    Ausdruecklich ein eigener Typ: der Aufrufer soll einen Zustellfehler
    von einem Programmierfehler unterscheiden koennen, ohne die
    Fehlermeldung zu lesen.
    """


@dataclass(frozen=True)
class MailMessage:
    """Eine Nachricht an genau einen Empfaenger."""

    to: str
    subject: str
    body: str

    def __post_init__(self) -> None:
        # Ein Zeilenumbruch im Betreff oder in der Adresse waere eine
        # Header Injection: alles danach wuerde zu einer eigenen Kopfzeile.
        for feld, wert in (("to", self.to), ("subject", self.subject)):
            if "\r" in wert or "\n" in wert:
                raise ValueError(f"{feld} darf keinen Zeilenumbruch enthalten")
        if not self.to.strip() or not self.subject.strip():
            raise ValueError("Empfaenger und Betreff sind erforderlich")


class MailSender(ABC):
    @abstractmethod
    def send(self, message: MailMessage) -> None:
        """Die Nachricht uebergeben oder `MailTransportError` werfen."""
