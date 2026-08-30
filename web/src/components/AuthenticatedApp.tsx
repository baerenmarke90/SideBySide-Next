import { useCallback, useEffect, useMemo, useRef } from 'react';
import { useQueryClient } from '@tanstack/react-query';
import { Link, Navigate, Route, Routes, useLocation } from 'react-router-dom';
import type { AccountView } from '../api/generated/models/AccountView';
import { AttachmentReadRequestParentTypeEnum } from '../api/generated/models/AttachmentReadRequest';
import type { TokenView } from '../api/generated/models/TokenView';
import { createPeopleApi } from '../client/peopleApi';
import {
  createReferenceApis,
  loadAuthorizedImage,
  loadAuthorizedParentImage,
} from '../client/referenceFlow';
import {
  appRoutePath,
  DEFAULT_APP_ROUTE,
  HEART_MOMENT_CREATE_ROUTE,
  HEART_MOMENT_DETAIL_ROUTE_PATTERN,
  HEART_MOMENT_EDIT_ROUTE_PATTERN,
  MEMORY_DETAIL_ROUTE_PATTERN,
  MEMORY_EDIT_ROUTE_PATTERN,
  MILESTONE_CREATE_ROUTE,
  MILESTONE_DETAIL_ROUTE_PATTERN,
  MILESTONE_EDIT_ROUTE_PATTERN,
} from '../client/routes';
import { useTranslation } from '../i18n';
import { AppErrorBoundary } from './AppErrorBoundary';
import { AppShell } from './AppShell';
import { HeartMomentProductPage } from './HeartMomentProductPage';
import { HeartMomentsPage } from './HeartMomentsPage';
import { MemoryCreatePage } from './MemoryCreatePage';
import { MemoryProductPage } from './MemoryProductPage';
import { MilestoneProductPage } from './MilestoneProductPage';
import { ProfilePage } from './ProfilePage';
import { RelatedPeoplePage } from './RelatedPeoplePage';
import { StoryProductPage } from './StoryProductPage';
import { UiState } from './UiState';

export function AuthenticatedApp({
  tokens,
  account,
  logout,
  apiBaseUrl,
  spaceId,
}: {
  tokens: TokenView;
  account: AccountView;
  logout: () => void;
  apiBaseUrl: string;
  spaceId: string;
}) {
  const { t } = useTranslation();
  const location = useLocation();
  const queryClient = useQueryClient();
  const previousSpaceId = useRef(spaceId);
  const apis = useMemo(
    () => createReferenceApis(apiBaseUrl, tokens.accessToken),
    [apiBaseUrl, tokens.accessToken],
  );
  const peopleApi = useMemo(
    () => createPeopleApi(apiBaseUrl, tokens.accessToken),
    [apiBaseUrl, tokens.accessToken],
  );

  useEffect(() => {
    if (previousSpaceId.current === spaceId) return;
    queryClient.clear();
    previousSpaceId.current = spaceId;
  }, [queryClient, spaceId]);

  const loadMemoryImage = useCallback(
    (memoryId: string, attachmentId: string) =>
      loadAuthorizedImage(
        apis,
        apiBaseUrl,
        tokens.accessToken,
        spaceId,
        memoryId,
        attachmentId,
      ),
    [apiBaseUrl, apis, spaceId, tokens.accessToken],
  );

  const loadHeartMomentImage = useCallback(
    (heartMomentId: string, attachmentId: string) =>
      loadAuthorizedParentImage(
        apis,
        apiBaseUrl,
        tokens.accessToken,
        spaceId,
        AttachmentReadRequestParentTypeEnum.HEART_MOMENT,
        heartMomentId,
        attachmentId,
      ),
    [apiBaseUrl, apis, spaceId, tokens.accessToken],
  );

  async function refreshStory() {
    await queryClient.invalidateQueries({ queryKey: ['story', spaceId] });
  }

  return (
    <AppShell onLogout={logout}>
      <AppErrorBoundary
        resetKey={location.pathname}
        fallback={
          <UiState
            kind="error"
            title={t('states.unexpected.title')}
            body={t('states.unexpected.body')}
            action={
              <Link
                className="button-link secondary-link"
                to={DEFAULT_APP_ROUTE}
              >
                {t('navigation.story')}
              </Link>
            }
          />
        }
      >
        <Routes>
          <Route
            path="/"
            element={<Navigate replace to={DEFAULT_APP_ROUTE} />}
          />
          <Route
            path={appRoutePath('story')}
            element={
              <StoryProductPage
                apis={apis}
                spaceId={spaceId}
                loadMemoryImage={loadMemoryImage}
              />
            }
          />
          <Route
            path={appRoutePath('heartMoments')}
            element={<HeartMomentsPage apis={apis} spaceId={spaceId} />}
          />
          <Route
            path={HEART_MOMENT_CREATE_ROUTE}
            element={
              <HeartMomentProductPage
                mode="create"
                apis={apis}
                apiBaseUrl={apiBaseUrl}
                accessToken={tokens.accessToken}
                spaceId={spaceId}
                currentAccountId={account.id}
                loadHeartMomentImage={loadHeartMomentImage}
              />
            }
          />
          <Route
            path={HEART_MOMENT_EDIT_ROUTE_PATTERN}
            element={
              <HeartMomentProductPage
                mode="edit"
                apis={apis}
                apiBaseUrl={apiBaseUrl}
                accessToken={tokens.accessToken}
                spaceId={spaceId}
                currentAccountId={account.id}
                loadHeartMomentImage={loadHeartMomentImage}
              />
            }
          />
          <Route
            path={HEART_MOMENT_DETAIL_ROUTE_PATTERN}
            element={
              <HeartMomentProductPage
                mode="detail"
                apis={apis}
                apiBaseUrl={apiBaseUrl}
                accessToken={tokens.accessToken}
                spaceId={spaceId}
                currentAccountId={account.id}
                loadHeartMomentImage={loadHeartMomentImage}
              />
            }
          />
          <Route
            path={MILESTONE_CREATE_ROUTE}
            element={
              <MilestoneProductPage
                mode="create"
                apis={apis}
                spaceId={spaceId}
                currentAccountId={account.id}
              />
            }
          />
          <Route
            path={MILESTONE_EDIT_ROUTE_PATTERN}
            element={
              <MilestoneProductPage
                mode="edit"
                apis={apis}
                spaceId={spaceId}
                currentAccountId={account.id}
              />
            }
          />
          <Route
            path={MILESTONE_DETAIL_ROUTE_PATTERN}
            element={
              <MilestoneProductPage
                mode="detail"
                apis={apis}
                spaceId={spaceId}
                currentAccountId={account.id}
              />
            }
          />
          <Route
            path={appRoutePath('people')}
            element={
              <RelatedPeoplePage peopleApi={peopleApi} spaceId={spaceId} />
            }
          />
          <Route
            path={appRoutePath('profile')}
            element={
              <ProfilePage
                apiBaseUrl={apiBaseUrl}
                accessToken={tokens.accessToken}
                account={account}
                spaceId={spaceId}
              />
            }
          />
          <Route
            path={appRoutePath('memoryCreate')}
            element={
              <MemoryCreatePage
                accessToken={tokens.accessToken}
                apiBaseUrl={apiBaseUrl}
                spaceId={spaceId}
                onSaved={refreshStory}
              />
            }
          />
          <Route
            path={MEMORY_EDIT_ROUTE_PATTERN}
            element={
              <MemoryProductPage
                mode="edit"
                apis={apis}
                apiBaseUrl={apiBaseUrl}
                accessToken={tokens.accessToken}
                spaceId={spaceId}
                currentAccountId={account.id}
                loadMemoryImage={loadMemoryImage}
              />
            }
          />
          <Route
            path={MEMORY_DETAIL_ROUTE_PATTERN}
            element={
              <MemoryProductPage
                mode="detail"
                apis={apis}
                apiBaseUrl={apiBaseUrl}
                accessToken={tokens.accessToken}
                spaceId={spaceId}
                currentAccountId={account.id}
                loadMemoryImage={loadMemoryImage}
              />
            }
          />
          <Route
            path="*"
            element={<Navigate replace to={DEFAULT_APP_ROUTE} />}
          />
        </Routes>
      </AppErrorBoundary>
    </AppShell>
  );
}
