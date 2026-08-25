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
from http import HTTPStatus

from sidebyside.core.errors import DomainError


class MailTransportError(RuntimeError):
    """Die Nachricht konnte nicht uebergeben werden.

    Ausdruecklich ein eigener Typ: der Aufrufer soll einen Zustellfehler
    von einem Programmierfehler unterscheiden koennen, ohne die
    Fehlermeldung zu lesen.
    """


class MailUnavailableError(DomainError):
    """Diese Instanz versendet ueberhaupt keine E-Mail.

    Bewusst **kein** `MailTransportError`: ein Zustellfehler wird in den
    Auth-Fluessen absichtlich geschluckt, damit die Antwort nicht verraet,
    ob eine Adresse bekannt ist. Ein fehlender Mailweg ist aber kein
    Zustellfehler, sondern eine Eigenschaft der Instanz - und die darf der
    Aufrufer erfahren, weil sie fuer jede Adresse gleich gilt.

    503 statt 404: der Endpunkt existiert, die Faehigkeit dahinter nicht.
    """

    status = HTTPStatus.SERVICE_UNAVAILABLE
    type = "mail_unavailable"
    title = "Mail unavailable"

    def __init__(self) -> None:
        super().__init__(
            "Diese Instanz versendet keine E-Mail. "
            "Anmeldung ist ueber Passwort, Passkey oder OIDC moeglich.",
            "MAIL_TRANSPORT_UNAVAILABLE",
        )


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
