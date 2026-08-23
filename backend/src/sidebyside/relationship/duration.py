"""Gemeinsame Zeit.

Reine Kalenderrechnung auf einem DATE - kein Zeitpunkt, keine Zeitzone.
Der Beginn einer Beziehung ist ein Tag.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date


@dataclass(frozen=True)
class Duration:
    days: int
    years: int
    months: int


def since(started_on: date, today: date) -> Duration | None:
    """Die verstrichene Zeit, oder None wenn der Beginn in der Zukunft liegt.

    Ein Datum in der Zukunft ergibt keine gemeinsame Zeit. Negative Werte
    zurueckzugeben waere schlimmer als nichts - eine Oberflaeche wuerde
    daraus "-3 Tage zusammen" bauen.
    """
    if started_on > today:
        return None

    tage = (today - started_on).days

    jahre = today.year - started_on.year
    monate = today.month - started_on.month
    if today.day < started_on.day:
        monate -= 1
    if monate < 0:
        jahre -= 1
        monate += 12

    return Duration(days=tage, years=jahre, months=monate)
