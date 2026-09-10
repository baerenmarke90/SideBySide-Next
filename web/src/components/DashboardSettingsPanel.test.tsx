// @vitest-environment jsdom

import {
  act,
  fireEvent,
  render,
  screen,
  waitFor,
} from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { vi } from 'vitest';
import type { DashboardApi } from '../api/generated/apis/DashboardApi';
import { dashboardPreferencesQueryKey } from '../client/dashboardPreferences';
import profileIdentity from '../i18n/locales/profileIdentity';
import { DashboardSettingsPanel } from './DashboardSettingsPanel';

const ACCOUNT_ID = 'account-1';
const SPACE_ID = 'space-1';

function renderPanel(
  updateDashboardModulePreference: DashboardApi['updateDashboardModulePreference'],
) {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false }, mutations: { retry: false } },
  });
  queryClient.setQueryData(dashboardPreferencesQueryKey(ACCOUNT_ID, SPACE_ID), {
    items: [{ moduleKey: 'upcoming', itemLimit: 2 }],
  });
  const dashboardApi = {
    listDashboardModulePreferences: vi.fn().mockResolvedValue({
      items: [{ moduleKey: 'upcoming', itemLimit: 2 }],
    }),
    updateDashboardModulePreference,
  } as unknown as DashboardApi;

  return {
    queryClient,
    ...render(
      <QueryClientProvider client={queryClient}>
        <DashboardSettingsPanel
          dashboardApi={dashboardApi}
          accountId={ACCOUNT_ID}
          spaceId={SPACE_ID}
        />
      </QueryClientProvider>,
    ),
  };
}

describe('DashboardSettingsPanel', () => {
  it('exposes one understandable native 1/2/3 radio group', () => {
    renderPanel(vi.fn());

    screen.getByRole('group', {
      name: profileIdentity.dashboardUpcomingTitle,
    });
    const options = screen.getAllByRole('radio');
    expect(options).toHaveLength(3);
    expect(
      (screen.getByRole('radio', { name: '2' }) as HTMLInputElement).checked,
    ).toBe(true);
    expect(
      (screen.getByRole('radio', { name: '1' }) as HTMLInputElement).checked,
    ).toBe(false);
    expect(
      (screen.getByRole('radio', { name: '3' }) as HTMLInputElement).checked,
    ).toBe(false);
  });

  it('persists immediately and updates the Account+Space query cache', async () => {
    const update = vi.fn().mockResolvedValue({
      moduleKey: 'upcoming',
      itemLimit: 3,
    });
    const { queryClient } = renderPanel(update);

    fireEvent.click(screen.getByRole('radio', { name: '3' }));

    await waitFor(() =>
      expect(update).toHaveBeenCalledWith({
        moduleKey: 'upcoming',
        spaceId: SPACE_ID,
        dashboardModulePreferenceUpdate: { itemLimit: 3 },
      }),
    );
    await waitFor(() => {
      screen.getByText(profileIdentity.dashboardUpcomingSaved);
    });
    expect(
      queryClient.getQueryData(
        dashboardPreferencesQueryKey(ACCOUNT_ID, SPACE_ID),
      ),
    ).toEqual({
      items: [{ moduleKey: 'upcoming', itemLimit: 3 }],
    });
    expect(
      (screen.getByRole('radio', { name: '3' }) as HTMLInputElement).checked,
    ).toBe(true);
  });

  it('keeps the pending choice visible while preventing duplicate changes', async () => {
    let resolveUpdate:
      | ((value: { moduleKey: string; itemLimit: number }) => void)
      | undefined;
    const update = vi.fn().mockReturnValue(
      new Promise((resolve) => {
        resolveUpdate = resolve;
      }),
    );
    renderPanel(update);

    await act(async () => {
      fireEvent.click(screen.getByRole('radio', { name: '3' }));
      await Promise.resolve();
    });

    await waitFor(() => {
      expect(
        (screen.getByRole('radio', { name: '3' }) as HTMLInputElement).checked,
      ).toBe(true);
      expect(
        (screen.getByRole('radio', { name: '1' }) as HTMLInputElement).disabled,
      ).toBe(true);
    });
    screen.getByText(profileIdentity.dashboardUpcomingSaving);

    await act(async () => {
      resolveUpdate?.({ moduleKey: 'upcoming', itemLimit: 3 });
    });
  });

  it('restores the confirmed value when immediate persistence fails', async () => {
    const update = vi.fn().mockRejectedValue(new Error('network unavailable'));
    renderPanel(update);

    fireEvent.click(screen.getByRole('radio', { name: '1' }));

    await waitFor(() =>
      expect(
        (screen.getByRole('radio', { name: '2' }) as HTMLInputElement).checked,
      ).toBe(true),
    );
    screen.getByRole('alert');
  });
});
