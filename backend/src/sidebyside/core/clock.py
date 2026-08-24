"""Zeit.

Zwei Begriffe, die nicht vermischt werden dürfen:

- Ein *Zeitpunkt* ist ein Moment auf der Weltzeitachse. Er wird in UTC
  gehalten und als TIMESTAMPTZ gespeichert.
- Ein *fachlicher Tag* ist ein Kalendertag ohne Uhrzeit - ein Geburtstag,
  ein Jahrestag, der Tag eines Erlebnisses. Er wird als DATE gespeichert.

Ein Geburtstag hat keine Zeitzone. Ihn als Zeitpunkt zu speichern
verschiebt ihn früher oder später um einen Tag.
"""

from __future__ import annotations

import logging
from datetime import UTC, date, datetime
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

log = logging.getLogger(__name__)


def now() -> datetime:
    """Der aktuelle Zeitpunkt, zeitzonen-bewusst in UTC."""
    return datetime.now(UTC)


def ensure_utc(value: datetime) -> datetime:
    """Einen Zeitpunkt nach UTC bringen.

    Ein Wert ohne Zeitzone wird als UTC gelesen. Das ist eine Annahme, und
    sie gilt nur, weil in diesem Projekt kein naiver Zeitstempel entstehen
    darf - siehe die Konventionen in docs/ARCHITECTURE.md.
    """
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)


def today_utc() -> date:
    """Der heutige Kalendertag in UTC.

    Ausschließlich für technische Zwecke. Für jede nutzersichtbare
    Tagesgrenze - gemeinsame Tage, Jahrestage, Erinnerungen - ist das
    falsch: sie gehört in die Zeitzone der lesenden Person. Dafür gibt es
    `today_in`.
    """
    return now().date()


def resolve_zone(name: str) -> ZoneInfo:
    """Eine benannte Zeitzone aufloesen, mit UTC als Rueckfallebene.

    `Account.timezone` ist ein freies Textfeld. Ein unbekannter Name darf
    eine Leseanfrage nicht mit 500 beenden - die Beziehungsdauer ist eine
    Anzeige, nicht der Zweck der Antwort. Der Fall wird protokolliert, damit
    er sichtbar bleibt und nicht als stille Fehlberechnung untergeht.
    """
    try:
        return ZoneInfo(name)
    except (ZoneInfoNotFoundError, ValueError):
        log.warning("unknown timezone, falling back to UTC", extra={"timezone": name})
        return ZoneInfo("UTC")


def today_in(zone: str, *, at: datetime | None = None) -> date:
    """Der heutige Kalendertag in einer bestimmten Zeitzone.

    Der fachliche Tag eines Menschen wechselt um Mitternacht an seinem Ort,
    nicht um Mitternacht UTC. Wer westlich von UTC lebt, haette sonst bis
    zu einen Tag zu viel gezaehlt, wer oestlich lebt, einen zu wenig - und
    ein Jahrestag waere um Stunden verschoben.
    """
    zeitpunkt = at if at is not None else now()
    return ensure_utc(zeitpunkt).astimezone(resolve_zone(zone)).date()
