import type { TFunction } from 'i18next';
import { resolvedLocale } from '../i18n';

/**
 * Formats recency for recent activity items:
 * - "Heute" for items from today
 * - "Gestern" for items from yesterday
 * - "vor X Tagen" for 2 to 6 days ago
 * - localized short date (e.g. "16. Feb.") for older entries
 */
export function formatRecency(
  date: Date,
  t: TFunction,
  now: Date = new Date(),
  locale = resolvedLocale(),
): string {
  const nowDate = new Date(now.getFullYear(), now.getMonth(), now.getDate());
  const itemDate = new Date(
    date.getFullYear(),
    date.getMonth(),
    date.getDate(),
  );
  const diffDays = Math.round(
    (nowDate.getTime() - itemDate.getTime()) / (24 * 60 * 60 * 1000),
  );

  if (diffDays <= 0) {
    return t('m5s5.common.today');
  }
  if (diffDays === 1) {
    return t('m5s5.common.yesterday');
  }
  if (diffDays >= 2 && diffDays <= 6) {
    return t('m5s5.common.daysAgo', { count: diffDays });
  }
  return new Intl.DateTimeFormat(locale, {
    day: 'numeric',
    month: 'short',
  }).format(date);
}

/**
 * Formats relative time for notifications:
 * - "Gerade eben" for < 1 minute ago
 * - "vor X Min." for < 60 minutes ago
 * - "vor X Std." for < 24 hours ago (same calendar day)
 * - "Gestern" for yesterday
 * - "vor X Tagen" for 2 to 6 days ago
 * - localized short date (e.g. "16. Feb.") for older entries
 */
export function formatRelativeTime(
  date: Date,
  t: TFunction,
  now: Date = new Date(),
  locale = resolvedLocale(),
): string {
  const diffMs = now.getTime() - date.getTime();
  const diffMinutes = Math.floor(diffMs / 60_000);
  const diffHours = Math.floor(diffMs / 3_600_000);

  if (diffMinutes < 1) {
    return t('m5s5.common.justNow');
  }
  if (diffMinutes < 60) {
    return t('m5s5.common.minutesAgo', { count: diffMinutes });
  }
  if (diffHours < 24 && now.getDate() === date.getDate()) {
    return t('m5s5.common.hoursAgo', { count: diffHours });
  }

  const nowDate = new Date(now.getFullYear(), now.getMonth(), now.getDate());
  const itemDate = new Date(
    date.getFullYear(),
    date.getMonth(),
    date.getDate(),
  );
  const diffDays = Math.round(
    (nowDate.getTime() - itemDate.getTime()) / (24 * 60 * 60 * 1000),
  );

  if (diffDays === 1) {
    return t('m5s5.common.yesterday');
  }
  if (diffDays >= 2 && diffDays <= 6) {
    return t('m5s5.common.daysAgo', { count: diffDays });
  }
  return new Intl.DateTimeFormat(locale, {
    day: 'numeric',
    month: 'short',
  }).format(date);
}

/**
 * Formats relative date for upcoming events/plans:
 * - "Heute · 16. Feb." for today
 * - "Morgen · 17. Feb." for tomorrow
 * - "in X Tagen · 25. Feb." for 2 to 30 days in advance
 * - localized long date for dates beyond 30 days
 */
export function formatUpcomingRelative(
  date: Date,
  t: TFunction,
  now: Date = new Date(),
  locale = resolvedLocale(),
): string {
  const nowDate = new Date(now.getFullYear(), now.getMonth(), now.getDate());
  const targetDate = new Date(
    date.getFullYear(),
    date.getMonth(),
    date.getDate(),
  );
  const diffDays = Math.round(
    (targetDate.getTime() - nowDate.getTime()) / (24 * 60 * 60 * 1000),
  );

  const formattedShort = new Intl.DateTimeFormat(locale, {
    day: 'numeric',
    month: 'short',
  }).format(date);

  if (diffDays <= 0) {
    return `${t('m5s5.common.today')} · ${formattedShort}`;
  }
  if (diffDays === 1) {
    return `${t('m5s5.common.tomorrow')} · ${formattedShort}`;
  }
  if (diffDays >= 2 && diffDays <= 30) {
    return `${t('m5s5.common.inDays', { count: diffDays })} · ${formattedShort}`;
  }
  return new Intl.DateTimeFormat(locale, {
    day: 'numeric',
    month: 'long',
  }).format(date);
}

/** Compact weekday + date for a true instant in the user's local timezone. */
export function formatCompactWeekdayDate(
  date: Date,
  locale = resolvedLocale(),
): string {
  return new Intl.DateTimeFormat(locale, {
    weekday: 'short',
    day: 'numeric',
    month: 'short',
  }).format(date);
}

/**
 * Compact weekday + date for an OpenAPI `date` carrier.
 *
 * Generated TypeScript models represent a date as a Date at UTC midnight.
 * Formatting that value in the browser timezone could shift it to the previous
 * day. `timeZone: UTC` reads only the encoded calendar components and therefore
 * preserves the authoritative day on every device.
 */
export function formatCompactCalendarDate(
  date: Date,
  locale = resolvedLocale(),
): string {
  return new Intl.DateTimeFormat(locale, {
    weekday: 'short',
    day: 'numeric',
    month: 'short',
    timeZone: 'UTC',
  }).format(date);
}
