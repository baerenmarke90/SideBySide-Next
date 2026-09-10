import type { DashboardModulePreferenceList } from '../api/generated/models/DashboardModulePreferenceList';

export const DEFAULT_UPCOMING_ITEM_LIMIT = 2;
export const UPCOMING_MODULE_KEY = 'upcoming';
export const UPCOMING_ITEM_LIMITS = [1, 2, 3] as const;

export type UpcomingItemLimit = (typeof UPCOMING_ITEM_LIMITS)[number];

export function dashboardPreferencesQueryKey(
  accountId: string,
  spaceId: string,
): readonly ['dashboard-preferences', string, string] {
  return ['dashboard-preferences', accountId, spaceId] as const;
}

export function isUpcomingItemLimit(value: number): value is UpcomingItemLimit {
  return UPCOMING_ITEM_LIMITS.some((limit) => limit === value);
}

export function effectiveUpcomingItemLimit(
  preferences: DashboardModulePreferenceList | undefined,
): UpcomingItemLimit {
  const value = preferences?.items.find(
    (item) => item.moduleKey === UPCOMING_MODULE_KEY,
  )?.itemLimit;
  return value !== undefined && isUpcomingItemLimit(value)
    ? value
    : DEFAULT_UPCOMING_ITEM_LIMIT;
}

export function limitUpcomingItems<T>(
  items: readonly T[],
  preferences: DashboardModulePreferenceList | undefined,
): T[] {
  return items.slice(0, effectiveUpcomingItemLimit(preferences));
}
