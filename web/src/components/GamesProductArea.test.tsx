// @vitest-environment jsdom
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { EntitlementStatus } from '../api/generated/models/EntitlementStatus';
import { EntitlementTier } from '../api/generated/models/EntitlementTier';
import type { SpaceEntitlementView } from '../api/generated/models/SpaceEntitlementView';
import games from '../i18n/locales/games';
import { GAMES_COUPLE_CAPABILITY, GamesProductArea } from './GamesProductArea';

const SPACE_ID = '22222222-2222-4222-8222-222222222222';

function entitlement(capabilities: string[]): SpaceEntitlementView {
  return {
    capabilities,
    effectiveUntil: null,
    isInGracePeriod: false,
    spaceId: SPACE_ID,
    status: capabilities.length
      ? EntitlementStatus.ACTIVE
      : EntitlementStatus.EXPIRED,
    tier: capabilities.length ? EntitlementTier.PREMIUM : EntitlementTier.FREE,
  };
}

function renderGames(view: SpaceEntitlementView) {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  });

  return render(
    <QueryClientProvider client={queryClient}>
      <GamesProductArea
        apiBaseUrl="http://api.example.test"
        accessToken="test-token"
        spaceId={SPACE_ID}
        loadEntitlement={async () => view}
      />
    </QueryClientProvider>,
  );
}

function expectFiveGameEntries(): void {
  expect(screen.getByText(games.entries.moments.title)).toBeTruthy();
  expect(screen.getByText(games.entries.wishes.title)).toBeTruthy();
  expect(screen.getByText(games.entries.perspective.title)).toBeTruthy();
  expect(screen.getByText(games.entries.happiness.title)).toBeTruthy();
  expect(screen.getByText(games.entries.timeTravel.title)).toBeTruthy();
}

describe('GamesProductArea', () => {
  it('keeps the five-game catalog discoverable for a Free Space with one page-level Premium treatment', async () => {
    renderGames(entitlement([]));

    await screen.findByText(games.premium.title);
    expectFiveGameEntries();
    expect(screen.getAllByText(games.status.premium)).toHaveLength(5);

    const detailsButton = screen.getByRole('button', {
      name: games.premium.action,
    });
    expect(screen.queryByText(games.premium.detailsTitle)).toBeNull();
    fireEvent.click(detailsButton);
    expect(screen.getByText(games.premium.detailsTitle)).toBeTruthy();
    expect(detailsButton.getAttribute('aria-expanded')).toBe('true');
  });

  it('unlocks the hub presentation only when the centralized Games capability is present', async () => {
    renderGames(entitlement([GAMES_COUPLE_CAPABILITY]));

    await waitFor(() => {
      expect(screen.getByText(games.unlocked.title)).toBeTruthy();
    });
    expect(screen.queryByText(games.premium.title)).toBeNull();
    expectFiveGameEntries();
    expect(screen.getAllByText(games.status.comingSoon)).toHaveLength(5);
  });
});
