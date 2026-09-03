import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { renderToStaticMarkup } from 'react-dom/server';
import { MemoryRouter } from 'react-router-dom';
import type { SharedPlanningApis } from '../client/sharedPlanning';
import { SharedPlanningOverviewPage } from './SharedPlanningOverviewPage';

describe('SharedPlanningOverviewPage', () => {
  it('renders only the shared M3 planning product areas', () => {
    const queryClient = new QueryClient({
      defaultOptions: { queries: { retry: false } },
    });
    const html = renderToStaticMarkup(
      <QueryClientProvider client={queryClient}>
        <MemoryRouter>
          <SharedPlanningOverviewPage
            apis={{} as SharedPlanningApis}
            spaceId="space-1"
          />
        </MemoryRouter>
      </QueryClientProvider>,
    );

    expect(html).toContain('Wünsche');
    expect(html).toContain('Pläne');
    expect(html).toContain('Orte');
    expect(html).toContain('Kapitel');
    expect(html).toContain('Gemeinsame Listen');
    expect(html).not.toContain('PrivateNote');
    expect(html).not.toContain('GiftIdea');
    expect(html).not.toContain('PrivateCollection');
  });

  it('shows a Collection icon as a prefix, and offers an icon field when creating one', () => {
    const queryClient = new QueryClient({
      defaultOptions: { queries: { retry: false } },
    });
    queryClient.setQueryData(['m5-s3', 'collections', 'space-1'], {
      pages: [
        {
          items: [
            {
              capabilities: {
                canComment: false,
                canDelete: true,
                canEdit: true,
              },
              createdAt: new Date('2026-08-01T10:00:00Z'),
              createdBy: 'account-1',
              creator: { id: 'account-1', displayName: 'Lea' },
              id: 'collection-1',
              items: [],
              spaceId: 'space-1',
              title: 'Packing list',
              updatedAt: new Date('2026-08-01T10:00:00Z'),
              version: 1,
            },
          ],
          hasMore: false,
          nextCursor: null,
        },
      ],
      pageParams: [null],
    });

    const html = renderToStaticMarkup(
      <QueryClientProvider client={queryClient}>
        <MemoryRouter>
          <SharedPlanningOverviewPage
            apis={{} as SharedPlanningApis}
            spaceId="space-1"
          />
        </MemoryRouter>
      </QueryClientProvider>,
    );

    // #373: collection icon removed end-to-end
    expect(html).toContain('Packing list');
    expect(html).not.toContain('🧳');
    expect(html).not.toContain('collection-icon');
  });
});
