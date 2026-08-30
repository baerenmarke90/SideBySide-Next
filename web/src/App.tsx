import {
  type FormEvent,
  useCallback,
  useEffect,
  useMemo,
  useRef,
  useState,
} from 'react';
import {
  useMutation,
  useQuery,
  useQueryClient,
  type UseQueryResult,
} from '@tanstack/react-query';
import {
  Link,
  Navigate,
  Route,
  Routes,
  useLocation,
  useNavigate,
} from 'react-router-dom';
import type { AccountView } from './api/generated/models/AccountView';
import type { SpaceView } from './api/generated/models/SpaceView';
import type { StoryPage as StoryPageData } from './api/generated/models/StoryPage';
import type { TokenView } from './api/generated/models/TokenView';
import { loadReferenceClientConfig } from './client/config';
import {
  readSensitiveEntryToken,
  stripSensitiveEntryToken,
} from './client/entryToken';
import { createM4ProductApis } from './client/m4Product';
import { createMemoryWithReadyAttachments } from './client/memoryAttachmentDraft';
import { createPeopleApi } from './client/peopleApi';
import { normalizeClientError } from './client/problemDetails';
import {
  loadAuthorizedMemberships,
  loadAuthorizedSpaces,
  resolveActiveSpaceId,
} from './client/spaceContext';
import {
  createReferenceApis,
  loadAuthorizedImage,
} from './client/referenceFlow';
import {
  appRoutePath,
  DEFAULT_APP_ROUTE,
  MEMORY_DETAIL_ROUTE_PATTERN,
  MEMORY_EDIT_ROUTE_PATTERN,
} from './client/routes';
import { useAttachmentDrafts } from './client/useAttachmentDrafts';
import { AppErrorBoundary } from './components/AppErrorBoundary';
import { AppShell } from './components/AppShell';
import { Brand } from './components/Brand';
import { IdentityEntry } from './components/IdentityEntry';
import {
  ActivityProductPage,
  DashboardProductPage,
  NotificationsProductPage,
  SearchProductPage,
} from './components/M4ProductPages';
import { MemoryProductPage } from './components/MemoryProductPage';
import { PageHeader } from './components/PageHeader';
import { ProblemState } from './components/ProblemState';
import { ProfilePage } from './components/ProfilePage';
import { RelatedPeoplePage } from './components/RelatedPeoplePage';
import { StoryList } from './components/StoryList';
import { ThemeControl } from './components/ThemeControl';
import { UiState } from './components/UiState';
import { useTranslation } from './i18n';

function SpaceContextGate({
  loading,
  error,
  onRetry,
}: {
  loading: boolean;
  error: Error | null;
  onRetry: () => void;
}) {
  const { t } = useTranslation();
  return (
    <main className="setup-shell">
      <div className="entry-aura entry-aura-start" aria-hidden="true" />
      <div className="entry-aura entry-aura-end" aria-hidden="true" />
      <section className="setup-card" aria-labelledby="space-context-heading">
        <Brand
          suffix={<span className="brand-suffix">{t('brand.suffix')}</span>}
        />
        <div className="setup-content">
          <p className="eyebrow">{t('spaceContext.eyebrow')}</p>
          {loading ? (
            <UiState kind="loading" title={t('spaceContext.loading')} />
          ) : error ? (
            <ProblemState error={error} onRetry={onRetry} />
          ) : (
            <>
              <h1 id="space-context-heading">{t('spaceContext.emptyTitle')}</h1>
              <p>{t('spaceContext.emptyBody')}</p>
            </>
          )}
        </div>
      </section>
    </main>
  );
}

function SpacePicker({
  spaces,
  onSelect,
}: {
  spaces: SpaceView[];
  onSelect: (spaceId: string) => void;
}) {
  const { t } = useTranslation();
  return (
    <main className="setup-shell">
      <div className="entry-aura entry-aura-start" aria-hidden="true" />
      <div className="entry-aura entry-aura-end" aria-hidden="true" />
      <section className="setup-card" aria-labelledby="space-picker-heading">
        <Brand
          suffix={<span className="brand-suffix">{t('brand.suffix')}</span>}
        />
        <div className="setup-content">
          <p className="eyebrow">{t('spaceContext.eyebrow')}</p>
          <h1 id="space-picker-heading">{t('spaceContext.pickerTitle')}</h1>
          <p>{t('spaceContext.pickerBody')}</p>
          <fieldset className="form-grid">
            <legend>{t('spaceContext.pickerAria')}</legend>
            {spaces.map((space, index) => {
              const names = space.partners
                .map((partner) => partner.displayName.trim())
                .filter(Boolean)
                .join(' & ');
              return (
                <button
                  key={space.id}
                  type="button"
                  onClick={() => onSelect(space.id)}
                >
                  {names ||
                    t('spaceContext.spaceFallback', { index: index + 1 })}
                </button>
              );
            })}
          </fieldset>
        </div>
      </section>
    </main>
  );
}

function StoryPage({
  storyQuery,
  loadMemoryImage,
}: {
  storyQuery: UseQueryResult<StoryPageData, Error>;
  loadMemoryImage: (memoryId: string, attachmentId: string) => Promise<string>;
}) {
  const { t } = useTranslation();
  const location = useLocation();
  const saved = Boolean((location.state as { saved?: boolean } | null)?.saved);

  return (
    <div className="page story-page">
      {saved && (
        <div className="inline-message inline-message-success" role="status">
          <strong>{t('story.savedTitle')}</strong>
          <span>{t('story.savedBody')}</span>
        </div>
      )}

      <PageHeader
        eyebrow={t('story.eyebrow')}
        title={t('story.title')}
        description={t('story.intro')}
        className="story-heading"
        action={
          <Link
            className="button-link primary-action"
            to={appRoutePath('memoryCreate')}
          >
            {t('story.addMemory')}
          </Link>
        }
      />

      <section className="story-surface" aria-labelledby="timeline-heading">
        <div className="section-head">
          <div>
            <p className="section-kicker">{t('story.timelineKicker')}</p>
            <h2 id="timeline-heading">{t('story.timelineHeading')}</h2>
          </div>
          <button
            type="button"
            className="secondary compact-action"
            onClick={() => storyQuery.refetch()}
            disabled={storyQuery.isFetching}
          >
            {storyQuery.isFetching
              ? t('common.refreshing')
              : t('common.refresh')}
          </button>
        </div>

        {storyQuery.isLoading ? (
          <UiState kind="loading" title={t('story.loadingAria')} />
        ) : null}
        {storyQuery.error ? (
          <ProblemState
            error={storyQuery.error}
            onRetry={() => void storyQuery.refetch()}
          />
        ) : null}
        {storyQuery.data ? (
          <StoryList
            items={storyQuery.data.items}
            loadMemoryImage={loadMemoryImage}
          />
        ) : null}
      </section>
    </div>
  );
}

function MemoryCreatePage({
  accessToken,
  apiBaseUrl,
  spaceId,
  onSaved,
}: {
  accessToken: string;
  apiBaseUrl: string;
  spaceId: string;
  onSaved: () => Promise<void>;
}) {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const apis = useMemo(
    () => createReferenceApis(apiBaseUrl, accessToken),
    [apiBaseUrl, accessToken],
  );
  const attachments = useAttachmentDrafts({
    apis,
    apiBaseUrl,
    accessToken,
    spaceId,
  });

  const mutation = useMutation({
    mutationFn: async ({
      title,
      body,
      happenedOn,
    }: {
      title: string;
      body: string;
      happenedOn?: Date;
    }) => {
      try {
        return await createMemoryWithReadyAttachments(
          apis,
          spaceId,
          { title, body, happenedOn },
          attachments.readyIds,
        );
      } catch (error) {
        throw await normalizeClientError(error);
      }
    },
    onSuccess: async () => {
      attachments.clear();
      await onSaved();
      navigate(appRoutePath('story'), {
        replace: true,
        state: { saved: true },
      });
    },
  });

  function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (attachments.hasPending) return;
    const data = new FormData(event.currentTarget);
    const happenedOnValue = String(data.get('happenedOn') || '');
    mutation.mutate({
      title: String(data.get('title')),
      body: String(data.get('body')),
      happenedOn: happenedOnValue
        ? new Date(`${happenedOnValue}T00:00:00Z`)
        : undefined,
    });
  }

  return (
    <div className="page create-page">
      <PageHeader
        before={
          <Link className="back-link" to={appRoutePath('story')}>
            {t('memory.backToStory')}
          </Link>
        }
        eyebrow={t('memory.eyebrow')}
        title={t('memory.heading')}
        description={t('memory.intro')}
        className="create-heading"
      />

      <section className="form-card" aria-labelledby="memory-form-heading">
        <h2 id="memory-form-heading" className="sr-only">
          {t('memory.formAria')}
        </h2>
        <form onSubmit={submit} className="form-grid memory-form">
          <div className="field-group">
            <label htmlFor="title">{t('memory.titleLabel')}</label>
            <input
              id="title"
              name="title"
              required
              maxLength={200}
              placeholder={t('memory.titlePlaceholder')}
            />
          </div>

          <div className="field-group">
            <label htmlFor="body">{t('memory.bodyLabel')}</label>
            <textarea
              id="body"
              name="body"
              rows={5}
              placeholder={t('memory.bodyPlaceholder')}
            />
          </div>

          <div className="field-group">
            <label htmlFor="happenedOn">{t('memory.dateLabel')}</label>
            <input id="happenedOn" name="happenedOn" type="date" />
            <p className="field-help">{t('memory.dateHelp')}</p>
          </div>

          <div className="field-group">
            <label htmlFor="image">{t('memory.photoLabel')}</label>
            <input
              className="visually-hidden-input"
              id="image"
              name="image"
              type="file"
              accept="image/jpeg,image/png,image/webp,image/heic,image/heif"
              multiple
              onChange={(event) => {
                attachments.addFiles(event.currentTarget.files);
                event.currentTarget.value = '';
              }}
            />
            <label className="file-picker" htmlFor="image">
              <span className="file-picker-icon" aria-hidden="true">
                ＋
              </span>
              <span>
                <strong>
                  {attachments.items.length
                    ? t('memory.photoAddMore')
                    : t('memory.photoSelect')}
                </strong>
                <small>{t('memory.photoFormats')}</small>
              </span>
            </label>

            {attachments.items.length > 0 && (
              <ul
                className="attachment-draft-list"
                aria-label={t('memory.photoDraftsAria')}
              >
                {attachments.items.map((attachment) => {
                  const statusText =
                    attachment.status === 'uploading'
                      ? t('memory.photoUploading')
                      : attachment.status === 'validating'
                        ? t('memory.photoValidating')
                        : attachment.status === 'ready'
                          ? t('memory.photoReady')
                          : t('memory.photoFailed');

                  return (
                    <li className="attachment-draft-item" key={attachment.id}>
                      <div className="attachment-preview-wrap">
                        <img
                          className="attachment-preview"
                          src={attachment.previewUrl}
                          alt={t('memory.photoPreviewAlt', {
                            name: attachment.file.name,
                          })}
                        />
                        <span className="attachment-preview-label">
                          {t('memory.photoLocalPreview')}
                        </span>
                      </div>
                      <div className="attachment-draft-meta">
                        <strong>{attachment.file.name}</strong>
                        <span
                          className={`attachment-status attachment-status-${attachment.status}`}
                          role={
                            attachment.status === 'failed' ? 'alert' : 'status'
                          }
                          aria-live="polite"
                        >
                          {statusText}
                        </span>
                        {attachment.status === 'failed' && (
                          <>
                            <small className="attachment-draft-error">
                              {attachment.error}
                            </small>
                            <small>{t('memory.photoFailedNotSaved')}</small>
                          </>
                        )}
                      </div>
                      <div className="attachment-draft-actions">
                        {attachment.status === 'failed' && (
                          <button
                            type="button"
                            className="secondary"
                            onClick={() => attachments.retry(attachment)}
                          >
                            {t('common.retry')}
                          </button>
                        )}
                        <button
                          type="button"
                          className="tertiary"
                          onClick={() => attachments.remove(attachment.id)}
                        >
                          {t('memory.photoRemove')}
                        </button>
                      </div>
                    </li>
                  );
                })}
              </ul>
            )}
            {attachments.hasPending && (
              <p className="field-help" role="status" aria-live="polite">
                {t('memory.photoPendingSave')}
              </p>
            )}
          </div>

          <div
            className="sharing-note"
            role="note"
            aria-label={t('memory.visibilityAria')}
          >
            <span className="sharing-icon" aria-hidden="true">
              ♥
            </span>
            <div>
              <strong>{t('memory.sharedTitle')}</strong>
              <p>{t('memory.sharedBody')}</p>
            </div>
          </div>

          <div className="form-actions">
            <Link
              className="button-link secondary-link"
              to={appRoutePath('story')}
            >
              {t('common.cancel')}
            </Link>
            <button
              type="submit"
              disabled={mutation.isPending || attachments.hasPending}
            >
              {mutation.isPending ? t('memory.saving') : t('memory.save')}
            </button>
          </div>
        </form>

        {mutation.isPending && (
          <p className="status" role="status" aria-live="polite">
            {t('memory.processing')}
          </p>
        )}
        {mutation.error ? <ProblemState error={mutation.error} /> : null}
      </section>
    </div>
  );
}

function AuthenticatedApp({
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
  const m4Apis = useMemo(
    () => createM4ProductApis(apiBaseUrl, tokens.accessToken),
    [apiBaseUrl, tokens.accessToken],
  );

  useEffect(() => {
    if (previousSpaceId.current === spaceId) return;
    queryClient.clear();
    previousSpaceId.current = spaceId;
  }, [queryClient, spaceId]);

  const storyQuery = useQuery({
    queryKey: ['story', spaceId],
    queryFn: async () => {
      try {
        return await apis.story.getStoryTimeline({ spaceId, limit: 25 });
      } catch (error) {
        throw await normalizeClientError(error);
      }
    },
    retry: false,
  });
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
              <StoryPage
                storyQuery={storyQuery}
                loadMemoryImage={loadMemoryImage}
              />
            }
          />
          <Route
            path={appRoutePath('dashboard')}
            element={<DashboardProductPage apis={m4Apis} spaceId={spaceId} />}
          />
          <Route
            path={appRoutePath('search')}
            element={<SearchProductPage apis={m4Apis} spaceId={spaceId} />}
          />
          <Route
            path={appRoutePath('activity')}
            element={<ActivityProductPage apis={m4Apis} spaceId={spaceId} />}
          />
          <Route
            path={appRoutePath('notifications')}
            element={
              <NotificationsProductPage apis={m4Apis} spaceId={spaceId} />
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
                memoriesApi={apis.memories}
                spaceId={spaceId}
                loadMemoryImage={loadMemoryImage}
              />
            }
          />
          <Route
            path={MEMORY_DETAIL_ROUTE_PATTERN}
            element={
              <MemoryProductPage
                mode="detail"
                memoriesApi={apis.memories}
                spaceId={spaceId}
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

export function App() {
  const config = useMemo(loadReferenceClientConfig, []);
  const queryClient = useQueryClient();
  const [tokens, setTokens] = useState<TokenView | null>(null);
  const [account, setAccount] = useState<AccountView | null>(null);
  const [spaceId, setSpaceId] = useState<string | null>(null);
  const [entryToken, setEntryToken] = useState(() =>
    readSensitiveEntryToken(window.location.pathname, window.location.search),
  );

  useEffect(() => {
    if (!entryToken) return;
    window.history.replaceState(
      window.history.state,
      '',
      stripSensitiveEntryToken(window.location.search),
    );
  }, [entryToken]);

  const membershipsQuery = useQuery({
    queryKey: ['account-memberships'],
    queryFn: async () => {
      if (!tokens) return [];
      return loadAuthorizedMemberships(config.apiBaseUrl, tokens.accessToken);
    },
    enabled: tokens !== null,
    retry: false,
  });

  const spacesQuery = useQuery({
    queryKey: [
      'authorized-spaces',
      (membershipsQuery.data ?? []).map((membership) => membership.spaceId),
    ],
    queryFn: async () => {
      if (!tokens || !membershipsQuery.data) return [];
      return loadAuthorizedSpaces(
        config.apiBaseUrl,
        tokens.accessToken,
        membershipsQuery.data,
      );
    },
    enabled: tokens !== null && (membershipsQuery.data?.length ?? 0) > 1,
    retry: false,
  });

  useEffect(() => {
    if (!tokens || !membershipsQuery.data) {
      setSpaceId(null);
      return;
    }
    setSpaceId((current) =>
      resolveActiveSpaceId(membershipsQuery.data, current),
    );
  }, [membershipsQuery.data, tokens]);

  function logout() {
    setEntryToken(null);
    setSpaceId(null);
    setAccount(null);
    setTokens(null);
    queryClient.clear();
  }

  if (!tokens || !account) {
    return (
      <>
        <ThemeControl />
        <IdentityEntry
          apiBaseUrl={config.apiBaseUrl}
          entryToken={entryToken}
          onEntryTokenCleared={() => setEntryToken(null)}
          onSession={(session) => {
            setEntryToken(null);
            setSpaceId(null);
            setAccount(session.account);
            setTokens(session.tokens);
            queryClient.clear();
          }}
        />
      </>
    );
  }

  const memberships = membershipsQuery.data ?? [];
  if (
    membershipsQuery.isPending ||
    membershipsQuery.error ||
    memberships.length === 0
  ) {
    return (
      <>
        <ThemeControl />
        <SpaceContextGate
          loading={membershipsQuery.isPending}
          error={membershipsQuery.error}
          onRetry={() => void membershipsQuery.refetch()}
        />
      </>
    );
  }

  const activeSpaceId = resolveActiveSpaceId(memberships, spaceId);
  if (!activeSpaceId && memberships.length > 1) {
    if (spacesQuery.isPending || spacesQuery.error || !spacesQuery.data) {
      return (
        <>
          <ThemeControl />
          <SpaceContextGate
            loading={spacesQuery.isPending}
            error={spacesQuery.error}
            onRetry={() => {
              void membershipsQuery.refetch();
              void spacesQuery.refetch();
            }}
          />
        </>
      );
    }

    return (
      <>
        <ThemeControl />
        <SpacePicker spaces={spacesQuery.data} onSelect={setSpaceId} />
      </>
    );
  }

  if (!activeSpaceId) {
    return (
      <>
        <ThemeControl />
        <SpaceContextGate loading error={null} onRetry={() => undefined} />
      </>
    );
  }

  return (
    <AuthenticatedApp
      tokens={tokens}
      account={account}
      logout={logout}
      apiBaseUrl={config.apiBaseUrl}
      spaceId={activeSpaceId}
    />
  );
}
