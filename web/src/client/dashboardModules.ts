/**
 * Central Dashboard module catalog (#817).
 *
 * Every separately rendered Today content section is registered here with a
 * stable key and its Settings label. `DashboardSettingsPanel` and `TodayPage`
 * both read this list instead of each hardcoding which modules exist, so a
 * module cannot silently exist on one surface without a visibility control on
 * the other.
 *
 * The App Shell/navigation and the Today hero (`CouplePresence`) are not
 * Dashboard modules: they render unconditionally as the page's own identity,
 * not as one of the conditional `TodayModuleSection` content blocks this
 * catalog governs. This list must stay in sync with the backend catalog in
 * `backend/src/sidebyside/dashboard/preferences.py`.
 */

export type DashboardModuleKey =
  | 'upcoming'
  | 'keepsake'
  | 'relationship_signal'
  | 'monthly_highlights'
  | 'recent_shared';

export interface DashboardModuleCatalogEntry {
  key: DashboardModuleKey;
  /** i18n key for the module's Settings-facing (and Today-facing) label. */
  labelKey: string;
}

/**
 * Deterministic Settings/Today order, matching the accepted #850 Today
 * composition in `TodayPage.tsx`: Demnaechst, Euer Moment, Gerade bei euch,
 * Diesen Monat, Zuletzt bei euch.
 *
 * `SHARED_STORY_SUMMARY` (#809) is deliberately absent: it is not merged to
 * `main`, and #817 does not implement #809 on its behalf.
 */
export const DASHBOARD_MODULE_CATALOG: readonly DashboardModuleCatalogEntry[] =
  [
    { key: 'upcoming', labelKey: 'm5s5.dashboard.upcomingTitle' },
    { key: 'keepsake', labelKey: 'm5s5.today.keepsake.kicker' },
    { key: 'relationship_signal', labelKey: 'm5s5.today.living.kicker' },
    { key: 'monthly_highlights', labelKey: 'm5s5.today.monthly.title' },
    { key: 'recent_shared', labelKey: 'm5s5.dashboard.recentTitle' },
  ];

export const DASHBOARD_MODULE_KEYS: readonly DashboardModuleKey[] =
  DASHBOARD_MODULE_CATALOG.map((entry) => entry.key);
