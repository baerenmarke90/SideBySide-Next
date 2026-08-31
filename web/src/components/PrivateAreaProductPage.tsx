import { Navigate, Route, Routes } from 'react-router-dom';
import type { PrivateAreaApi } from '../api/generated/apis/PrivateAreaApi';
import {
  GiftIdeaCreatePage,
  GiftIdeaDetailPage,
  GiftIdeaEditPage,
  GiftIdeasListPage,
} from './GiftIdeasPage';
import {
  PrivateCollectionCreatePage,
  PrivateCollectionDetailPage,
  PrivateCollectionEditPage,
  PrivateCollectionsListPage,
} from './PrivateCollectionsPage';
import { PrivateAreaFrame } from './PrivateAreaLayout';
import {
  PrivateNoteCreatePage,
  PrivateNoteDetailPage,
  PrivateNoteEditPage,
  PrivateNotesListPage,
} from './PrivateNotesPage';
import './PrivateAreaProductPage.css';

export function PrivateAreaProductPage({
  api,
  accountId,
  spaceId,
}: {
  api: PrivateAreaApi;
  accountId: string;
  spaceId: string;
}) {
  const props = { api, accountId, spaceId };
  return (
    <PrivateAreaFrame>
      <Routes>
        <Route index element={<Navigate replace to="notes" />} />
        <Route path="notes" element={<PrivateNotesListPage {...props} />} />
        <Route
          path="notes/new"
          element={<PrivateNoteCreatePage {...props} />}
        />
        <Route
          path="notes/:noteId/edit"
          element={<PrivateNoteEditPage {...props} />}
        />
        <Route
          path="notes/:noteId"
          element={<PrivateNoteDetailPage {...props} />}
        />
        <Route path="gift-ideas" element={<GiftIdeasListPage {...props} />} />
        <Route
          path="gift-ideas/new"
          element={<GiftIdeaCreatePage {...props} />}
        />
        <Route
          path="gift-ideas/:giftIdeaId/edit"
          element={<GiftIdeaEditPage {...props} />}
        />
        <Route
          path="gift-ideas/:giftIdeaId"
          element={<GiftIdeaDetailPage {...props} />}
        />
        <Route
          path="collections"
          element={<PrivateCollectionsListPage {...props} />}
        />
        <Route
          path="collections/new"
          element={<PrivateCollectionCreatePage {...props} />}
        />
        <Route
          path="collections/:collectionId/edit"
          element={<PrivateCollectionEditPage {...props} />}
        />
        <Route
          path="collections/:collectionId"
          element={<PrivateCollectionDetailPage {...props} />}
        />
        <Route path="*" element={<Navigate replace to="notes" />} />
      </Routes>
    </PrivateAreaFrame>
  );
}
