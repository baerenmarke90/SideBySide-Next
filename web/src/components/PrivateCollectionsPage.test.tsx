import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { renderToStaticMarkup } from 'react-dom/server';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
import type { PrivateAreaApi } from '../api/generated/apis/PrivateAreaApi';
import { privateAreaQueryKeys } from '../client/privateArea';
import {
  PrivateCollectionDetailPage,
  PrivateCollectionEditPage,
  PrivateCollectionsListPage,
} from './PrivateCollectionsPage';

const ACCOUNT_ID = 'account-1';
const SPACE_ID = 'space-1';
const COLLECTION_ID = 'collection-1';

function collection(icon: string | null) {
  return {
    capabilities: { canComment: false, canDelete: true, canEdit: true },
    createdAt: new Date('2026-08-01T10:00:00Z'),
    icon,
    id: COLLECTION_ID,
    items: [],
    ownerId: ACCOUNT_ID,
    spaceId: SPACE_ID,
    title: 'Packing list',
    updatedAt: new Date('2026-08-01T10:00:00Z'),
    version: 1,
  };
}

describe('PrivateCollectionsPage', () => {
  it('shows the icon as a title prefix in the list', () => {
    const queryClient = new QueryClient({
      defaultOptions: { queries: { retry: false } },
    });
    queryClient.setQueryData(
      privateAreaQueryKeys.collections(ACCOUNT_ID, SPACE_ID),
      {
        pages: [{ items: [collection('🧳')], nextCursor: null }],
        pageParams: [null],
      },
    );

    const html = renderToStaticMarkup(
      <QueryClientProvider client={queryClient}>
        <MemoryRouter>
          <PrivateCollectionsListPage
            api={{} as PrivateAreaApi}
            accountId={ACCOUNT_ID}
            spaceId={SPACE_ID}
          />
        </MemoryRouter>
      </QueryClientProvider>,
    );

    // #606: the icon field existed on the API but was never exposed here.
    expect(html).toContain('🧳 Packing list');
    // #616: entire card is the primary navigation link without redundant edit button
    expect(html).toContain('private-area-card-clickable');
    expect(html).toContain(`/more/private/collections/${COLLECTION_ID}`);
    expect(html).not.toContain('button-link secondary-link');
  });

  it('offers an icon field when editing', () => {
    const queryClient = new QueryClient({
      defaultOptions: { queries: { retry: false } },
    });
    queryClient.setQueryData(
      privateAreaQueryKeys.collection(ACCOUNT_ID, SPACE_ID, COLLECTION_ID),
      collection('🧳'),
    );

    const html = renderToStaticMarkup(
      <QueryClientProvider client={queryClient}>
        <MemoryRouter
          initialEntries={[`/private/collections/${COLLECTION_ID}/edit`]}
        >
          <Routes>
            <Route
              path="/private/collections/:collectionId/edit"
              element={
                <PrivateCollectionEditPage
                  api={{} as PrivateAreaApi}
                  accountId={ACCOUNT_ID}
                  spaceId={SPACE_ID}
                />
              }
            />
          </Routes>
        </MemoryRouter>
      </QueryClientProvider>,
    );

    expect(html).toContain('private-collection-icon');
  });

  it('renders checklist items with checkboxes, autosave inputs, and grouped sections', () => {
    const queryClient = new QueryClient({
      defaultOptions: { queries: { retry: false } },
    });
    queryClient.setQueryData(
      privateAreaQueryKeys.collection(ACCOUNT_ID, SPACE_ID, COLLECTION_ID),
      {
        ...collection('📝'),
        items: [
          {
            id: 'item-1',
            title: 'Order photo album',
            completed: false,
            position: 0,
            version: 1,
          },
          {
            id: 'item-2',
            title: 'Book train tickets',
            completed: true,
            position: 1,
            version: 1,
          },
        ],
      },
    );

    const html = renderToStaticMarkup(
      <QueryClientProvider client={queryClient}>
        <MemoryRouter
          initialEntries={[`/private/collections/${COLLECTION_ID}`]}
        >
          <Routes>
            <Route
              path="/private/collections/:collectionId"
              element={
                <PrivateCollectionDetailPage
                  api={{} as PrivateAreaApi}
                  accountId={ACCOUNT_ID}
                  spaceId={SPACE_ID}
                />
              }
            />
          </Routes>
        </MemoryRouter>
      </QueryClientProvider>,
    );

    expect(html).toContain('checklist-open');
    expect(html).toContain('checklist-completed');
    expect(html).toContain('private-checklist-checkbox');
    expect(html).toContain('private-checklist-check-label');
    expect(html).toContain('private-checklist-title-input');
    expect(html).toContain('Order photo album');
    expect(html).toContain('Book train tickets');

    // Old CRUD artifacts are removed
    expect(html).not.toContain('private-area-badge');
  });
});
