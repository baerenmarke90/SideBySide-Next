import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { renderToStaticMarkup } from 'react-dom/server';
import { MemoryRouter } from 'react-router-dom';
import { DashboardModuleKey } from '../api/generated/models/DashboardModuleKey';
import { dashboardPreferencesQueryKey } from '../client/dashboardPreferences';
import type { M4ProductApis } from '../client/m4Product';
import m5s5 from '../i18n/locales/m5s5';
import { TodayPage } from './TodayPage';

function renderWithPreference(visible: boolean): string {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  });
  queryClient.setQueryData(['m5-s5', 'dashboard', 'space-1'], {
    space: {
      spaceId: 'space-1',
      partner: { id: 'partner-1', displayName: 'Marie' },
    },
    relationshipDuration: null,
    retrospective: null,
    keepsake: null,
    upcoming: [],
    recentShared: [
      {
        id: 'memory-1',
        type: 'MEMORY',
        titleOrText: 'Unser Ausflug',
        occurredOn: new Date('2026-09-01T12:00:00Z'),
      },
    ],
    sharedStorySummary: { memories: 4, heartMoments: 1, milestones: 0 },
    thinkingOfYouAvailableAt: null,
  });
  queryClient.setQueryData(dashboardPreferencesQueryKey('space-1'), {
    items: [{ moduleKey: DashboardModuleKey.SHARED_STORY_SUMMARY, visible }],
  });

  return renderToStaticMarkup(
    <QueryClientProvider client={queryClient}>
      <MemoryRouter>
        <TodayPage apis={{} as M4ProductApis} spaceId="space-1" />
      </MemoryRouter>
    </QueryClientProvider>,
  );
}

describe('Today shared Story integration', () => {
  it('places the eligible summary after the recent shared trace', () => {
    const html = renderWithPreference(true);
    expect(html).toContain(m5s5.dashboard.storySummaryTitle);
    expect(html.indexOf(m5s5.dashboard.recentTitle)).toBeLessThan(
      html.indexOf(m5s5.dashboard.storySummaryTitle),
    );
  });

  it('fails closed when the current user hides the module', () => {
    const html = renderWithPreference(false);
    expect(html).not.toContain(m5s5.dashboard.storySummaryTitle);
  });
});
