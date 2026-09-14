import {
  DASHBOARD_MODULE_CATALOG,
  DASHBOARD_MODULE_KEYS,
} from './dashboardModules';

describe('dashboardModules', () => {
  it('registers the currently accepted #850 Today modules in deterministic order', () => {
    expect(DASHBOARD_MODULE_KEYS).toEqual([
      'upcoming',
      'keepsake',
      'relationship_signal',
      'monthly_highlights',
      'recent_shared',
    ]);
  });

  it('registers every module key exactly once', () => {
    expect(new Set(DASHBOARD_MODULE_KEYS).size).toBe(
      DASHBOARD_MODULE_KEYS.length,
    );
  });

  it('gives every catalog entry a non-empty i18n label key', () => {
    for (const entry of DASHBOARD_MODULE_CATALOG) {
      expect(entry.labelKey.length).toBeGreaterThan(0);
    }
  });
});
