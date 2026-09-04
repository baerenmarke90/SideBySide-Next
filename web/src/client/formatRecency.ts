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
