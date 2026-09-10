import type { DashboardModulePreferenceList } from '../api/generated/models/DashboardModulePreferenceList';
import {
  dashboardPreferencesQueryKey,
  effectiveUpcomingItemLimit,
  limitUpcomingItems,
} from './dashboardPreferences';

function preferences(itemLimit: number): DashboardModulePreferenceList {
  return {
    items: [{ moduleKey: 'upcoming', itemLimit }],
  } as unknown as DashboardModulePreferenceList;
}

describe('dashboardPreferences', () => {
  it('scopes query cache entries by account and Space', () => {
    expect(dashboardPreferencesQueryKey('account-a', 'space-a')).toEqual([
      'dashboard-preferences',
      'account-a',
      'space-a',
    ]);
    expect(dashboardPreferencesQueryKey('account-b', 'space-a')).not.toEqual(
      dashboardPreferencesQueryKey('account-a', 'space-a'),
    );
    expect(dashboardPreferencesQueryKey('account-a', 'space-b')).not.toEqual(
      dashboardPreferencesQueryKey('account-a', 'space-a'),
    );
  });

  it.each([
    [undefined, 1],
    [preferences(1), 1],
    [preferences(2), 2],
    [preferences(3), 3],
    [preferences(4), 1],
    [{ items: [] }, 1],
  ])('resolves only valid effective limits', (value, expected) => {
    expect(effectiveUpcomingItemLimit(value)).toBe(expected);
  });

  it.each([
    [undefined, ['first']],
    [preferences(1), ['first']],
    [preferences(2), ['first', 'second']],
    [preferences(3), ['first', 'second', 'third']],
  ])(
    'limits without reordering the authoritative candidates',
    (value, expected) => {
      expect(
        limitUpcomingItems(['first', 'second', 'third', 'fourth'], value),
      ).toEqual(expected);
    },
  );

  it.each([
    [[], []],
    [['first'], ['first']],
    [
      ['first', 'second'],
      ['first', 'second'],
    ],
  ])('never fabricates unavailable items', (items, expected) => {
    expect(limitUpcomingItems(items, preferences(3))).toEqual(expected);
  });
});
