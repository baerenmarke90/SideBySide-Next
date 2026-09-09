import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { renderToStaticMarkup } from 'react-dom/server';
import type { DashboardApi } from '../api/generated/apis/DashboardApi';
import { DashboardModuleKey } from '../api/generated/models/DashboardModuleKey';
import { dashboardPreferencesQueryKey } from '../client/dashboardPreferences';
import profileIdentity from '../i18n/locales/profileIdentity';
import { DashboardSettingsPanel } from './DashboardSettingsPanel';

describe('DashboardSettingsPanel', () => {
  it('renders the registered module as an accessible persisted visibility control', () => {
    const queryClient = new QueryClient({
      defaultOptions: { queries: { retry: false } },
    });
    queryClient.setQueryData(dashboardPreferencesQueryKey('space-1'), {
      items: [
        {
          moduleKey: DashboardModuleKey.SHARED_STORY_SUMMARY,
          visible: true,
        },
      ],
    });

    const html = renderToStaticMarkup(
      <QueryClientProvider client={queryClient}>
        <DashboardSettingsPanel
          dashboardApi={{} as DashboardApi}
          spaceId="space-1"
        />
      </QueryClientProvider>,
    );

    expect(html).toContain(profileIdentity.dashboardModuleSharedStorySummary);
    expect(html).toContain('type="checkbox"');
    expect(html).toContain('checked=""');
    expect(html).not.toContain('SHARED_STORY_SUMMARY');
  });
});
