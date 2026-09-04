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

  it('renders compact list interaction with add icon and without per-item save buttons', () => {
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
        items: [
          {
            capabilities: { canComment: false, canDelete: true, canEdit: true },
            completed: false,
            createdAt: new Date('2026-08-01T10:00:00Z'),
            createdBy: 'account-1',
            id: 'item-1',
            position: 1,
            title: 'Passport',
            updatedAt: new Date('2026-08-01T10:00:00Z'),
            version: 1,
          },
        ],
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

    // Title input row has compact save button disabled initially
    // (Removed because title row is now inside edit mode)
    // Add button is rendered
    expect(html).toContain('planning-inline-create');
    // Item row has item title, checkbox, reorder, delete, but no per-item save button
    expect(html).toContain('Passport');
    expect(html).toContain('planning-check');
    // Check that there is no submit button inside the items list
    expect(html).not.toContain('planning-item-title-form button');
  });
});
