import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { renderToStaticMarkup } from 'react-dom/server';
import { MemoryRouter } from 'react-router-dom';
import type { ActivityApi } from '../api/generated/apis/ActivityApi';
import type { M4ProductApis } from '../client/m4Product';
import { ActivityProductPage } from './M4ProductPages';

const SPACE_ID = 'space-1';

function renderActivityPage(items: unknown[]): string {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  });
  queryClient.setQueryData(['m5-s5', 'activity', SPACE_ID], {
    pages: [
      {
        items,
        nextCursor: null,
      },
    ],
    pageParams: [null],
  });

  return renderToStaticMarkup(
    <QueryClientProvider client={queryClient}>
      <MemoryRouter>
        <ActivityProductPage
          apis={{ activity: {} as ActivityApi } as M4ProductApis}
          spaceId={SPACE_ID}
        />
      </MemoryRouter>
    </QueryClientProvider>,
  );
}

describe('issue #501: Activity relationship chronology presentation', () => {
  it('renders relationship chronology card with actor name, action verb, and target title', () => {
    const html = renderActivityPage([
      {
        id: 'act-1',
        sourceEventId: 'evt-1',
        kind: 'MEMORY_CREATED',
        actorId: 'user-1',
        actor: {
          id: 'user-1',
          displayName: 'Anna',
          profileAttachmentId: null,
        },
        targetType: 'MEMORY',
        targetId: 'mem-1',
        target: {
          targetType: 'MEMORY',
          targetId: 'mem-1',
          title: 'Sommerurlaub am See',
        },
        occurredAt: new Date('2026-08-20T14:30:00Z'),
        createdAt: new Date('2026-08-20T14:30:00Z'),
      },
    ]);

    // Actor Presentation
    expect(html).toContain('Anna');
    expect(html).toContain('hat eine Erinnerung festgehalten');
    // Target Presentation
    expect(html).toContain('Sommerurlaub am See');
    // Deep Link Navigation
    expect(html).toContain('href="/story/memories/mem-1"');
  });

  it('renders target title for heart moments and milestones', () => {
    const html = renderActivityPage([
      {
        id: 'act-2',
        sourceEventId: 'evt-2',
        kind: 'HEART_MOMENT_CREATED',
        actorId: 'user-2',
        actor: {
          id: 'user-2',
          displayName: 'Ben',
          profileAttachmentId: null,
        },
        targetType: 'HEART_MOMENT',
        targetId: 'heart-1',
        target: {
          targetType: 'HEART_MOMENT',
          targetId: 'heart-1',
          title: 'Du bringst mich jeden Tag zum Lächeln',
        },
        occurredAt: new Date('2026-08-21T10:00:00Z'),
        createdAt: new Date('2026-08-21T10:00:00Z'),
      },
    ]);

    expect(html).toContain('Ben');
    expect(html).toContain('hat einen Herzensmoment geteilt');
    expect(html).toContain('Du bringst mich jeden Tag zum Lächeln');
    expect(html).toContain('href="/story"');
  });

  it('renders empty state when no activities exist', () => {
    const html = renderActivityPage([]);
    expect(html).toContain('Noch keine Aktivität');
  });
});
