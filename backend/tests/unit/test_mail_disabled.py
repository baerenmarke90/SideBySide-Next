"""Verhalten einer Instanz ohne Mailweg.

`SBS_MAIL_TRANSPORT=none` ist der ausdrueckliche Verzicht. Die
mailabhaengigen Anmeldewege muessen das sagen, statt einen Token zu
erzeugen und `202 Accepted` zu antworten - eine Bestaetigung fuer eine
Nachricht, die niemals entsteht, ist schlimmer als ein Fehler.
"""

from __future__ import annotations

import pytest

from sidebyside.config import MailTransport, Settings, get_settings
from sidebyside.mail import MailTransportError, MailUnavailableError, sender


@pytest.fixture
def ohne_mailweg(monkeypatch: pytest.MonkeyPatch) -> None:
    einstellungen = get_settings().model_copy(update={"mail_transport": MailTransport.NONE})
    monkeypatch.setattr("sidebyside.config.get_settings", lambda: einstellungen)


def test_sender_verweigert_sich_statt_ins_leere_zu_senden(ohne_mailweg: None) -> None:
    with pytest.raises(MailUnavailableError):
        sender()


def test_fehler_ist_kein_zustellfehler() -> None:
    """Sonst schluckt ihn die Absicht-Verschleierung in den Auth-Fluessen.

    `_zustellen` faengt `MailTransportError` bewusst ab, damit die Antwort
    nicht verraet, ob eine Adresse bekannt ist. Waere der fehlende Mailweg
    ein Sonderfall davon, antwortete der Endpunkt weiterhin `202`.
    """
    assert not issubclass(MailUnavailableError, MailTransportError)


def test_antwort_nennt_einen_stabilen_code() -> None:
    fehler = MailUnavailableError()
    assert fehler.code == "MAIL_TRANSPORT_UNAVAILABLE"
    assert fehler.status == 503


def test_log_versand_bleibt_der_entwicklungsweg() -> None:
    """`none` ersetzt `log` nicht - beide existieren nebeneinander."""
    assert Settings(mail_transport="log").mail_transport is MailTransport.LOG  # type: ignore[arg-type]
