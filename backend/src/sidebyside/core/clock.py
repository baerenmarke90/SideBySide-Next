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

from datetime import UTC, date, datetime


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

    Für nutzersichtbare Tagesgrenzen ist das nicht ausreichend - dafür
    braucht es die Zeitzone des Space. Diese Funktion ist für technische
    Zwecke gedacht.
    """
    return now().date()
