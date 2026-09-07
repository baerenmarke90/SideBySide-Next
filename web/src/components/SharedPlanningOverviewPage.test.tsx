import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { renderToStaticMarkup } from 'react-dom/server';
import { MemoryRouter } from 'react-router-dom';
import type { SharedPlanningApis } from '../client/sharedPlanning';
import { CollectionsOverviewPage } from './CollectionsOverviewPage';
import { PlacesOverviewPage } from './PlacesOverviewPage';
import { SharedPlanningOverviewPage } from './SharedPlanningOverviewPage';

function emptyInfinitePage() {
  return {
    pages: [{ items: [], hasMore: false, nextCursor: null }],
    pageParams: [null],
  };
}

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
    expect(html).not.toContain('PrivateNote');
    expect(html).not.toContain('GiftIdea');
    expect(html).not.toContain('PrivateCollection');
  });

  it('shows a Collection title cleanly without legacy emoji icon (#373)', () => {
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
          <CollectionsOverviewPage
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

  it('renders both timeline stops with markers and semantic sections', () => {
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

    const stopMatches = html.match(
      /<section\b[^>]*class="[^"]*future-map-stop/g,
    );
    expect(stopMatches).toHaveLength(2);

    const markerMatches = html.match(/class="future-map-marker"/g);
    expect(markerMatches).toHaveLength(2);
    expect(html).toContain('planning-sanctuary');
  });

  it('uses relationship-native empty states for planning, collections, and places', () => {
    const planningClient = new QueryClient({
      defaultOptions: { queries: { retry: false } },
    });
    planningClient.setQueryData(
      ['m5-s3', 'plans', 'space-1'],
      emptyInfinitePage(),
    );
    planningClient.setQueryData(
      ['m5-s3', 'wishes', 'space-1'],
      emptyInfinitePage(),
    );
    planningClient.setQueryData(['m5-s3', 'places', 'space-1'], []);

    const planningHtml = renderToStaticMarkup(
      <QueryClientProvider client={planningClient}>
        <MemoryRouter>
          <SharedPlanningOverviewPage
            apis={{} as SharedPlanningApis}
            spaceId="space-1"
          />
        </MemoryRouter>
      </QueryClientProvider>,
    );

    expect(planningHtml).toContain('Noch nichts fest geplant.');
    expect(planningHtml).toContain('Noch keine Wünsche festgehalten.');

    const collectionsClient = new QueryClient({
      defaultOptions: { queries: { retry: false } },
    });
    collectionsClient.setQueryData(
      ['m5-s3', 'collections', 'space-1'],
      emptyInfinitePage(),
    );
    const collectionsHtml = renderToStaticMarkup(
      <QueryClientProvider client={collectionsClient}>
        <MemoryRouter>
          <CollectionsOverviewPage
            apis={{} as SharedPlanningApis}
            spaceId="space-1"
          />
        </MemoryRouter>
      </QueryClientProvider>,
    );
    expect(collectionsHtml).toContain('Noch keine gemeinsame Liste.');

    const placesClient = new QueryClient({
      defaultOptions: { queries: { retry: false } },
    });
    placesClient.setQueryData(
      ['m5-s3', 'places', 'space-1'],
      emptyInfinitePage(),
    );
    const placesHtml = renderToStaticMarkup(
      <QueryClientProvider client={placesClient}>
        <MemoryRouter>
          <PlacesOverviewPage
            apis={{} as SharedPlanningApis}
            spaceId="space-1"
          />
        </MemoryRouter>
      </QueryClientProvider>,
    );
    expect(placesHtml).toContain('Noch keine gemeinsamen Orte gespeichert.');
  });
});
