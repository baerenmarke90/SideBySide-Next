"""Time.

Two concepts that must not be conflated:

- An *instant* is a moment on the global timeline. It is kept in UTC and
  stored as TIMESTAMPTZ.
- A *domain day* is a calendar date without a time - a birthday, anniversary,
  or the day of an experience. It is stored as DATE.

A birthday has no timezone. Storing it as an instant will eventually shift it
by a day.
"""

from __future__ import annotations

import logging
from datetime import UTC, date, datetime
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

log = logging.getLogger(__name__)


def now() -> datetime:
    """Return the current timezone-aware instant in UTC."""
    return datetime.now(UTC)


def ensure_utc(value: datetime) -> datetime:
    """Normalize an instant to UTC.

    A value without timezone information is interpreted as UTC. That is an
    assumption and is valid only because this project must not create naive
    timestamps; see the conventions in docs/ARCHITECTURE.md.
    """
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)


def today_utc() -> date:
    """Return today's calendar date in UTC.

    For technical use only. This is wrong for every user-visible day boundary
    - shared days, anniversaries, reminders - because those belong to the
    timezone of the person reading them. Use `today_in` for that.
    """
    return now().date()


def resolve_zone(name: str) -> ZoneInfo:
    """Resolve a named timezone, falling back to UTC.

    `Account.timezone` is persisted text. An unknown name must not turn a read
    request into a 500 response: relationship duration is display data rather
    than the purpose of the request. The fallback is logged so invalid data
    remains visible instead of becoming a silent miscalculation.
    """
    try:
        return ZoneInfo(name)
    except (ZoneInfoNotFoundError, ValueError):
        log.warning("unknown timezone, falling back to UTC", extra={"timezone": name})
        return ZoneInfo("UTC")


def today_in(zone: str, *, at: datetime | None = None) -> date:
    """Return today's calendar date in a specific timezone.

    A person's domain day changes at midnight where they are, not at midnight
    UTC. Otherwise somebody west of UTC could count up to one day too many,
    while somebody east of UTC could count one day too few, and an anniversary
    would shift by hours.
    """
    instant = at if at is not None else now()
    return ensure_utc(instant).astimezone(resolve_zone(zone)).date()
