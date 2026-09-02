import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { renderToStaticMarkup } from 'react-dom/server';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
import type { PrivateAreaApi } from '../api/generated/apis/PrivateAreaApi';
import { privateAreaQueryKeys } from '../client/privateArea';
import {
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
});
