import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { renderToStaticMarkup } from 'react-dom/server';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
import type { SharedPlanningApis } from '../client/sharedPlanning';
import { CollectionProductPage } from './CollectionProductPage';

describe('CollectionProductPage', () => {
  it('shows collection title cleanly without icon prefix or edit field (#373)', () => {
    const queryClient = new QueryClient({
      defaultOptions: { queries: { retry: false } },
    });
    queryClient.setQueryData(
      ['m5-s3', 'collection', 'space-1', 'collection-1'],
      {
        capabilities: { canComment: false, canDelete: true, canEdit: true },
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
    );

    const html = renderToStaticMarkup(
      <QueryClientProvider client={queryClient}>
        <MemoryRouter initialEntries={['/plan/collections/collection-1']}>
          <Routes>
            <Route
              path="/plan/collections/:collectionId"
              element={
                <CollectionProductPage
                  apis={{} as SharedPlanningApis}
                  spaceId="space-1"
                />
              }
            />
          </Routes>
        </MemoryRouter>
      </QueryClientProvider>,
    );

    expect(html).toContain('Packing list');
    expect(html).not.toContain('collection-edit-icon');
  });
});
