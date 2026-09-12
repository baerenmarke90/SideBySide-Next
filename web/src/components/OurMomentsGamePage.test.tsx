// @vitest-environment jsdom
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { render, screen } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { i18n } from '../i18n';
import games from '../i18n/locales/games';
import type { OurMomentsGameSetup } from './OurMomentsGamePage';
import { OurMomentsGamePage } from './OurMomentsGamePage';

const SPACE_ID = '22222222-2222-4222-8222-222222222222';

function setup(momentCount: number): OurMomentsGameSetup {
  return {
    participants: [
      { id: 'account-a', displayName: 'Lea' },
      { id: 'account-b', displayName: 'Alex' },
    ],
    moments: Array.from({ length: momentCount }, (_, index) => ({
      memoryId: `memory-${index + 1}`,
      title: `Moment ${index + 1}`,
      effectiveDate: new Date(`2026-0${index + 1}-01T00:00:00.000Z`),
      imageAttachmentId: `attachment-${index + 1}`,
      imageUrl: `https://example.test/moment-${index + 1}.jpg`,
    })),
  };
}

function renderPage(value: OurMomentsGameSetup) {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  });

  return render(
    <QueryClientProvider client={queryClient}>
      <MemoryRouter initialEntries={['/games/our-moments']}>
        <OurMomentsGamePage
          apiBaseUrl="http://api.example.test"
          accessToken="test-token"
          spaceId={SPACE_ID}
          currentAccountId="account-a"
          loadSetup={async () => value}
        />
      </MemoryRouter>
    </QueryClientProvider>,
  );
}

describe('OurMomentsGamePage', () => {
  it('starts immediately with a six-card sofa board from three prepared shared moments', async () => {
    renderPage(setup(3));

    await screen.findByRole('heading', {
      name: games.entries.moments.title,
      level: 1,
    });
    expect(
      screen.getByText(
        i18n.t('games.momentsGame.turnValue', { name: 'Lea' }),
      ),
    ).toBeTruthy();
    expect(
      screen.getByRole('region', { name: games.momentsGame.boardAria }),
    ).toBeTruthy();
    for (let index = 1; index <= 6; index += 1) {
      expect(
        screen.getByRole('button', {
          name: i18n.t('games.momentsGame.cardHidden', {
            index,
            total: 6,
          }),
        }),
      ).toBeTruthy();
    }
  });

  it('shows a relationship-native sparse state below three eligible moments without exposing a hidden count', async () => {
    renderPage(setup(2));

    await screen.findByRole('heading', {
      name: games.momentsGame.sparseTitle,
      level: 2,
    });
    expect(screen.getByText(games.momentsGame.sparseBody)).toBeTruthy();
    const storyLink = screen.getByRole('link', {
      name: games.momentsGame.sparseAction,
    });
    expect(storyLink.getAttribute('href')).toBe('/story');
  });

  it('does not construct a board when the active Space is not a two-partner couple', async () => {
    renderPage({ participants: null, moments: [] });

    await screen.findByText(games.momentsGame.coupleRequiredTitle);
    expect(
      screen.queryByRole('region', { name: games.momentsGame.boardAria }),
    ).toBeNull();
  });
});
