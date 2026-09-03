import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { renderToStaticMarkup } from 'react-dom/server';
import { MemoryRouter } from 'react-router-dom';
import type { M4ProductApis } from '../client/m4Product';
import { TodayPage } from './TodayPage';

function renderTodayPage(dashboardData: unknown): string {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  });
  queryClient.setQueryData(['m5-s5', 'dashboard', 'space-1'], dashboardData);

  return renderToStaticMarkup(
    <QueryClientProvider client={queryClient}>
      <MemoryRouter>
        <TodayPage apis={{} as M4ProductApis} spaceId="space-1" />
      </MemoryRouter>
    </QueryClientProvider>,
  );
}

describe('TodayPage', () => {
  it('renders couple presence hero, days together, thinking-of-you button, and cards', () => {
    const html = renderTodayPage({
      space: {
        id: 'space-1',
        partner: { id: 'partner-1', displayName: 'Marie' },
      },
      relationshipDuration: { daysTogether: 420 },
      upcoming: [
        {
          id: 'plan-1',
          type: 'PLAN',
          titleOrText: 'Weekend trip to Paris',
          scheduledAt: new Date('2026-09-15T10:00:00Z'),
        },
      ],
      recentShared: [
        {
          id: 'mem-1',
          type: 'MEMORY',
          titleOrText: 'Park Picnic',
          occurredOn: new Date('2026-09-01T14:00:00Z'),
        },
      ],
      retrospective: {
        id: 'heart-1',
        type: 'HEART_MOMENT',
        titleOrText: 'Morning Smile',
        createdAt: new Date('2025-09-03T08:00:00Z'),
      },
    });

    expect(html).toContain('Marie');
    expect(html).toContain('420');
    expect(html).toContain('today-hero-action');
    expect(html).toContain('Weekend trip to Paris');
    expect(html).toContain('Park Picnic');
    expect(html).toContain('Morning Smile');
    expect(html).toContain('today-card-badges');
  });

  it('renders welcoming new-space experience when there are no items yet', () => {
    const html = renderTodayPage({
      space: {
        id: 'space-1',
        partner: { id: 'partner-1', displayName: 'Marie' },
      },
      relationshipDuration: null,
      upcoming: [],
      recentShared: [],
      retrospective: null,
    });

    expect(html).toContain('new-space-experience');
    expect(html).toContain('new-space-mark');
    expect(html).toContain('Marie');
    expect(html).toContain('href="/story/memories/new"');
  });
});
