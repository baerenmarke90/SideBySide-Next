// @vitest-environment jsdom
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { fireEvent, render, screen } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import games from '../i18n/locales/games';
import type { WishDetectiveGameSetup } from './WishDetectiveGamePage';
import { WishDetectiveGamePage } from './WishDetectiveGamePage';

const SPACE_ID = '22222222-2222-4222-8222-222222222222';

function playableSetup(): WishDetectiveGameSetup {
  return {
    participants: [
      { id: 'lea', displayName: 'Lea' },
      { id: 'alex', displayName: 'Alex' },
    ],
    rounds: [
      { wishId: 'l1', createdBy: 'lea', title: 'Sterne gucken im Garten' },
      { wishId: 'a1', createdBy: 'alex', title: 'Wochenende am Meer' },
      { wishId: 'l2', createdBy: 'lea', title: 'Picknick am See' },
      { wishId: 'a2', createdBy: 'alex', title: 'Konzert in Berlin' },
    ],
  };
}

function renderPage(setup: WishDetectiveGameSetup) {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  });

  return render(
    <QueryClientProvider client={queryClient}>
      <MemoryRouter initialEntries={['/games/wish-detective']}>
        <WishDetectiveGamePage
          apiBaseUrl="http://api.example.test"
          accessToken="test-token"
          spaceId={SPACE_ID}
          currentAccountId="lea"
          loadSetup={async () => setup}
        />
      </MemoryRouter>
    </QueryClientProvider>,
  );
}

describe('WishDetectiveGamePage', () => {
  it('keeps the wish visible during clue entry and hides it for handoff and guessing', async () => {
    renderPage(playableSetup());

    await screen.findByRole('heading', {
      name: games.entries.wishes.title,
      level: 1,
    });
    expect(screen.getByText('Sterne gucken im Garten')).toBeTruthy();

    fireEvent.change(screen.getByLabelText('Hinweis 1'), {
      target: { value: 'Nacht' },
    });
    fireEvent.change(screen.getByLabelText('Hinweis 2'), {
      target: { value: 'Decke' },
    });
    fireEvent.change(screen.getByLabelText('Hinweis 3'), {
      target: { value: 'Warm' },
    });

    expect(screen.getByText('Sterne gucken im Garten')).toBeTruthy();
    fireEvent.click(screen.getByRole('button', { name: 'Gerät weitergeben' }));

    expect(screen.queryByText('Sterne gucken im Garten')).toBeNull();
    expect(
      screen.getByRole('heading', { name: 'Gerät an Alex reichen' }),
    ).toBeTruthy();

    fireEvent.click(screen.getByRole('button', { name: 'Alex: Ich habe es' }));
    expect(screen.queryByText('Sterne gucken im Garten')).toBeNull();
    expect(screen.getByText('Nacht')).toBeTruthy();
    expect(screen.getByText('Decke')).toBeTruthy();
    expect(screen.getByText('Warm')).toBeTruthy();
    expect(screen.getByLabelText('Welchen Wunsch meint Lea?')).toBeTruthy();
  });

  it('shows validation feedback instead of silently accepting invalid clues', async () => {
    renderPage(playableSetup());
    await screen.findByText('Sterne gucken im Garten');

    fireEvent.change(screen.getByLabelText('Hinweis 1'), {
      target: { value: 'romantischer Abend' },
    });
    fireEvent.change(screen.getByLabelText('Hinweis 2'), {
      target: { value: 'Garten' },
    });
    fireEvent.change(screen.getByLabelText('Hinweis 3'), {
      target: { value: 'Garten' },
    });
    fireEvent.click(screen.getByRole('button', { name: 'Gerät weitergeben' }));

    expect(screen.getByText('Bitte genau ein Wort verwenden.')).toBeTruthy();
    expect(
      screen.getAllByText('Nimm für jeden Hinweis ein anderes Wort.'),
    ).toHaveLength(2);
    expect(screen.getByText('Sterne gucken im Garten')).toBeTruthy();
  });

  it('shows the sparse state without exposing hidden candidate totals', async () => {
    const setup = playableSetup();
    renderPage({ participants: setup.participants, rounds: [] });

    await screen.findByRole('heading', {
      name: games.wishDetective.sparseTitle,
      level: 2,
    });
    const wishesLink = screen.getByRole('link', {
      name: games.wishDetective.sparseAction,
    });
    expect(wishesLink.getAttribute('href')).toBe('/plan#wish-title');
  });

  it('does not start when the active Space is not a two-partner couple', async () => {
    renderPage({ participants: null, rounds: [] });

    await screen.findByText(games.wishDetective.coupleRequiredTitle);
    expect(screen.queryByText('Sterne gucken im Garten')).toBeNull();
  });
});
