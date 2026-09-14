// @vitest-environment jsdom
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { render, screen } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { EntitlementStatus } from '../api/generated/models/EntitlementStatus';
import { EntitlementTier } from '../api/generated/models/EntitlementTier';
import type { SpaceEntitlementView } from '../api/generated/models/SpaceEntitlementView';
import {
  GAMES_MOMENTS_ROUTE,
  GAMES_WISH_DETECTIVE_ROUTE,
} from '../client/routes';
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
      <MemoryRouter initialEntries={['/games']}>
        <GamesProductArea
          apiBaseUrl="http://api.example.test"
          accessToken="test-token"
          spaceId={SPACE_ID}
          loadEntitlement={async () => view}
        />
      </MemoryRouter>
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
  it('keeps the catalog discoverable for a Free Space without a page-level Premium upsell', async () => {
    renderGames(entitlement([]));

    await screen.findByText(games.entries.moments.title);
    expectFiveGameEntries();
    expect(screen.getAllByText(games.status.premium)).toHaveLength(5);
    expect(document.querySelector('.games-access-panel')).toBeNull();
    expect(screen.queryByText('Premium ansehen')).toBeNull();
    expect(
      screen.queryByRole('link', {
        name: new RegExp(games.entries.moments.title),
      }),
    ).toBeNull();
  });

  it('opens the implemented sofa games without rendering an unlocked Premium panel', async () => {
    renderGames(entitlement([GAMES_COUPLE_CAPABILITY]));

    const momentsLink = await screen.findByRole('link', {
      name: new RegExp(games.entries.moments.title),
    });
    expectFiveGameEntries();
    expect(document.querySelector('.games-access-panel')).toBeNull();
    expect(screen.getAllByText(games.status.comingSoon)).toHaveLength(3);

    expect(momentsLink.textContent).toContain(games.status.playNow);
    expect(momentsLink.getAttribute('href')).toBe(GAMES_MOMENTS_ROUTE);

    const wishesLink = screen.getByRole('link', {
      name: new RegExp(games.entries.wishes.title),
    });
    expect(wishesLink.textContent).toContain(games.status.playNow);
    expect(wishesLink.getAttribute('href')).toBe(GAMES_WISH_DETECTIVE_ROUTE);
  });
});
