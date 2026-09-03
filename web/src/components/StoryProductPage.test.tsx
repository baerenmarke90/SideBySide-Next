import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { renderToStaticMarkup } from 'react-dom/server';
import { MemoryRouter } from 'react-router-dom';
import type { ReferenceApis } from '../client/referenceFlow';
import { StoryProductPage } from './StoryProductPage';

const loadMemoryImage = async () => 'blob:test-image';

function renderStoryPage(route: string, cachedData: unknown): string {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  });
  queryClient.setQueryData(['story', 'space-1', 'timeline:ALL:ALL:DESC'], {
    pages: [
      {
        value: cachedData,
        source: 'network',
      },
    ],
    pageParams: [null],
  });

  return renderToStaticMarkup(
    <QueryClientProvider client={queryClient}>
      <MemoryRouter initialEntries={[route]}>
        <StoryProductPage
          apis={{} as ReferenceApis}
          accountId="account-1"
          spaceId="space-1"
          loadMemoryImage={loadMemoryImage}
        />
      </MemoryRouter>
    </QueryClientProvider>,
  );
}

describe('StoryProductPage', () => {
  it('renders tab switcher and discovery view by default', () => {
    const html = renderStoryPage('/story', {
      items: [
        {
          kind: 'MEMORY',
          effectiveDate: new Date('2026-08-26T00:00:00Z'),
          memory: {
            id: 'mem-1',
            title: 'Summer Lake Vacation',
            notes: 'Wonderful sunset together',
            occurredOn: new Date('2026-08-26T00:00:00Z'),
            createdAt: new Date('2026-08-26T00:00:00Z'),
            attachments: [{ id: 'att-1', mediaType: 'image/jpeg' }],
            author: { id: 'author-1', displayName: 'Alex' },
            creator: { id: 'author-1', displayName: 'Alex' },
            capabilities: { canComment: true, canDelete: true, canEdit: true },
          },
        },
        {
          kind: 'HEART_MOMENT',
          effectiveDate: new Date('2026-08-25T00:00:00Z'),
          heartMoment: {
            id: 'heart-1',
            text: 'I love you more each day',
            createdAt: new Date('2026-08-25T00:00:00Z'),
            author: { id: 'author-2', displayName: 'Taylor' },
            creator: { id: 'author-2', displayName: 'Taylor' },
          },
        },
      ],
      hasMore: false,
      nextCursor: null,
    });

    expect(html).toContain('momente-tabs');
    expect(html).toContain('momente-discover-page');
    expect(html).toContain('momente-hero-highlight');
    expect(html).toContain('Summer Lake Vacation');
    expect(html).toContain('momente-stream-track');
    expect(html).toContain('I love you more each day');
  });

  it('renders timeline view when requested via query parameter', () => {
    const html = renderStoryPage('/story?tab=timeline', {
      items: [
        {
          kind: 'MEMORY',
          effectiveDate: new Date('2026-08-26T00:00:00Z'),
          memory: {
            id: 'mem-1',
            title: 'Summer Lake Vacation',
            occurredOn: new Date('2026-08-26T00:00:00Z'),
            createdAt: new Date('2026-08-26T00:00:00Z'),
            attachments: [],
            author: { id: 'author-1', displayName: 'Alex' },
            creator: { id: 'author-1', displayName: 'Alex' },
            capabilities: { canComment: true, canDelete: true, canEdit: true },
          },
        },
      ],
      hasMore: false,
      nextCursor: null,
    });

    expect(html).toContain('story-timeline');
    expect(html).toContain('story-filter-container');
    expect(html).toContain('Summer Lake Vacation');
  });

  it('renders empty welcoming state when no moments exist', () => {
    const html = renderStoryPage('/story', {
      items: [],
      hasMore: false,
      nextCursor: null,
    });

    expect(html).toContain('new-space-experience');
    expect(html).toContain('/story/memories/new');
  });

  it('renders clickable milestone card with updated non-achievement copy linking to timeline filter', () => {
    const html = renderStoryPage('/story', {
      items: [
        {
          kind: 'MILESTONE',
          effectiveDate: new Date('2026-08-20T00:00:00Z'),
          milestone: {
            id: 'mile-1',
            title: 'Moved in together',
            happenedOn: new Date('2026-08-20T00:00:00Z'),
            createdAt: new Date('2026-08-20T00:00:00Z'),
            author: { id: 'author-1', displayName: 'Alex' },
            creator: { id: 'author-1', displayName: 'Alex' },
          },
        },
      ],
      hasMore: false,
      nextCursor: null,
    });

    expect(html).toContain('Meilensteine &amp; gemeinsame Schritte');
    expect(html).toContain(
      'Große und kleine Stationen eurer gemeinsamen Geschichte.',
    );
    expect(html).not.toContain('Erfolge');
    expect(html).toContain('href="/story?tab=timeline&amp;type=MILESTONE"');
  });
});
