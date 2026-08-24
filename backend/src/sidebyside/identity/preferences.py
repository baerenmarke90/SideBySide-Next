"""Zeitzone und Locale eines Accounts - die Schreibgrenze.

Beide Werte steuern sichtbares Verhalten: `timezone` entscheidet, welcher
Kalendertag fuer eine Person gerade gilt, `locale` ueber Sprache und
Formate. Als freier Text waeren sie eine stille Fehlerquelle - ein Tippfehler
faellt erst auf, wenn ein Jahrestag am falschen Tag erscheint.

Hier steht deshalb genau eine Stelle, die diese Felder schreibt. Jeder
kuenftige Schreibpfad - Account-Einstellungen, Import, Migration von
Altdaten - geht durch `set_preferences`. Die Alternative waere, die
Pruefung an jedem neuen Endpunkt zu wiederholen; die Erfahrung dazu steht
in `authorization.guard`.

Lesen bleibt davon unberuehrt: `clock.resolve_zone` faellt fuer bereits
vorhandene unbrauchbare Werte weiterhin protokolliert auf UTC zurueck. Eine
Anzeige darf an einem Altbestand nicht zerbrechen.
"""

from __future__ import annotations

import re
from zoneinfo import available_timezones

from sqlalchemy.orm import Session

from sidebyside.core.errors import ValidationError
from sidebyside.identity.models import Account

MAX_TIMEZONE = 64
MAX_LOCALE = 16


class PreferenceErrorCode:
    TIMEZONE_INVALID = "ACCOUNT_TIMEZONE_INVALID"
    LOCALE_INVALID = "ACCOUNT_LOCALE_INVALID"


_LOCALE = re.compile(
    r"""
    ^
    (?P<language>[A-Za-z]{2,3})
    (?:-(?P<script>[A-Za-z]{4}))?
    (?:-(?P<region>[A-Za-z]{2}|[0-9]{3}))?
    $
    """,
    re.VERBOSE,
)
"""Die Teilmenge von BCP 47, die dieses Produkt fuehrt.

Sprache, optional Schrift, optional Region. Keine Varianten, Erweiterungen
oder privaten Kennzeichnungen: sie kommen in der Oberflaeche nicht vor, und
was nicht vorkommt, wird nicht gespeichert.
"""


def validate_timezone(value: str) -> str:
    """Einen IANA-Zonennamen pruefen.

    Geprueft wird gegen die tatsaechlich vorhandene Zonendatenbank, nicht
    gegen ein Muster: "Europe/Berlinn" sieht aus wie ein Zonenname und ist
    keiner.

    Nur der aussenliegende Leerraum wird entfernt. Die Schreibweise selbst
    bleibt unangetastet - "europe/berlin" wird abgewiesen und nicht still
    zurechtgerueckt. Ein Client, der den Namen aus dem Betriebssystem
    nimmt, liefert ihn ohnehin kanonisch; wer ihn selbst zusammensetzt,
    soll das merken.
    """
    zone = (value or "").strip()
    if not zone or len(zone) > MAX_TIMEZONE or zone not in available_timezones():
        raise ValidationError(
            "Enter a valid IANA time zone, for example Europe/Berlin.",
            PreferenceErrorCode.TIMEZONE_INVALID,
        )
    return zone


def normalize_locale(value: str) -> str:
    """Eine Locale in die kanonische Schreibweise bringen.

    Die Regel steht hier vollstaendig und gilt fuer jeden Schreibpfad:

    - `_` wird zu `-`; Android und die JVM liefern `de_DE`.
    - Sprache klein, Schrift mit grossem Anfangsbuchstaben, Region gross.
      Das ist die uebliche BCP-47-Schreibweise; sie ist ausdruecklich nur
      eine Schreibweise und keine Bedeutungsaenderung.
    - Alles, was danach nicht dem Muster entspricht, wird abgewiesen.

    Gespeicherter und ausgelieferter Wert sind damit derselbe: zweimal
    normalisieren aendert nichts mehr.
    """
    roh = (value or "").strip().replace("_", "-")
    treffer = _LOCALE.match(roh) if roh and len(roh) <= MAX_LOCALE else None
    if treffer is None:
        raise ValidationError(
            "Enter a valid locale, for example de-DE.",
            PreferenceErrorCode.LOCALE_INVALID,
        )

    teile = [treffer.group("language").lower()]
    if treffer.group("script"):
        teile.append(treffer.group("script").capitalize())
    if treffer.group("region"):
        teile.append(treffer.group("region").upper())
    return "-".join(teile)


def set_preferences(
    session: Session,
    account: Account,
    *,
    timezone: str | None = None,
    locale: str | None = None,
) -> Account:
    """Zeitzone und/oder Locale setzen - die einzige Stelle, die das tut.

    Beide Werte werden zuerst vollstaendig geprueft und erst danach
    zugewiesen. Ein ungueltiger zweiter Wert darf keinen halb geaenderten
    Account hinterlassen.
    """
    geprueft_zone = validate_timezone(timezone) if timezone is not None else None
    geprueft_locale = normalize_locale(locale) if locale is not None else None

    if geprueft_zone is not None:
        account.timezone = geprueft_zone
    if geprueft_locale is not None:
        account.locale = geprueft_locale

    session.flush()
    return account
