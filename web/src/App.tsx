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
import type { StoryPage as StoryPageData } from './api/generated/models/StoryPage';
import type { TokenView } from './api/generated/models/TokenView';
import { loadReferenceClientConfig } from './client/config';
import { createMemoryWithReadyAttachments } from './client/memoryAttachmentDraft';
import { normalizeClientError } from './client/problemDetails';
import {
  loadAuthorizedMemberships,
  resolveActiveSpaceId,
} from './client/spaceContext';
import {
  createReferenceApis,
  loadAuthorizedImage,
  signIn,
} from './client/referenceFlow';
import { appRoutePath, DEFAULT_APP_ROUTE } from './client/routes';
import { useAttachmentDrafts } from './client/useAttachmentDrafts';
import { AppErrorBoundary } from './components/AppErrorBoundary';
import { AppShell } from './components/AppShell';
import { Brand } from './components/Brand';
import { PageHeader } from './components/PageHeader';
import { ProblemState } from './components/ProblemState';
import { StoryList } from './components/StoryList';
import { ThemeControl } from './components/ThemeControl';
import { UiState } from './components/UiState';
import { useTranslation } from './i18n';

function readableError(error: unknown, fallback: string): string {
  if (!(error instanceof Error)) return fallback;
  if (!error.message || error.message === 'Response returned an error code')
    return fallback;
  return error.message;
}

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

function LoginScreen({
  onLogin,
  pending,
  error,
}: {
  onLogin: (email: string, password: string) => void;
  pending: boolean;
  error: unknown;
}) {
  const { t } = useTranslation();

  function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const data = new FormData(event.currentTarget);
    onLogin(String(data.get('email')), String(data.get('password')));
  }

  return (
    <main className="login-shell">
      <section className="login-intro" aria-labelledby="welcome-heading">
        <Brand
          inverse
          suffix={<span className="brand-suffix">{t('brand.suffix')}</span>}
        />
        <div className="login-intro-content">
          <h1 id="welcome-heading">{t('login.introHeading')}</h1>
          <p>{t('login.introBody')}</p>
        </div>
        <div className="entry-illustration" aria-hidden="true">
          <span className="entry-orbit entry-orbit-large" />
          <span className="entry-orbit entry-orbit-small" />
          <span className="entry-illustration-heart">♡</span>
        </div>
      </section>

      <div className="login-panel">
        <section className="login-card" aria-labelledby="login-heading">
          <div>
            <p className="eyebrow">{t('login.eyebrow')}</p>
            <h2 id="login-heading">{t('login.heading')}</h2>
            <p className="muted">{t('login.body')}</p>
          </div>
          <form onSubmit={submit} className="form-grid login-form">
            <div className="field-group">
              <label htmlFor="email">{t('login.email')}</label>
              <input
                id="email"
                name="email"
                type="email"
                autoComplete="username"
                autoCapitalize="none"
                spellCheck={false}
                required
              />
            </div>
            <div className="field-group">
              <label htmlFor="password">{t('login.password')}</label>
              <input
                id="password"
                name="password"
                type="password"
                autoComplete="current-password"
                required
              />
            </div>
            <button type="submit" disabled={pending} aria-busy={pending}>
              {pending ? t('login.pending') : t('login.submit')}
            </button>
          </form>
          {error ? (
            <p className="status status-error" role="alert">
              {readableError(error, t('login.errorFallback'))}
            </p>
          ) : null}
          <p className="login-assurance">{t('login.assurance')}</p>
        </section>
      </div>
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
  logout,
  apiBaseUrl,
  spaceId,
}: {
  tokens: TokenView;
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
  const [spaceId, setSpaceId] = useState<string | null>(null);

  const membershipsQuery = useQuery({
    queryKey: ['account-memberships', tokens?.accessToken ?? 'signed-out'],
    queryFn: async () => {
      if (!tokens) return [];
      return loadAuthorizedMemberships(
        config.apiBaseUrl,
        tokens.accessToken,
      );
    },
    enabled: tokens !== null,
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

  const loginMutation = useMutation({
    mutationFn: ({ email, password }: { email: string; password: string }) =>
      signIn(config.apiBaseUrl, email, password),
    onSuccess: (session) => {
      setSpaceId(null);
      setTokens(session.tokens);
      queryClient.clear();
    },
  });

  function logout() {
    setSpaceId(null);
    setTokens(null);
    queryClient.clear();
  }

  if (!tokens) {
    return (
      <>
        <ThemeControl />
        <LoginScreen
          onLogin={(email, password) =>
            loginMutation.mutate({ email, password })
          }
          pending={loginMutation.isPending}
          error={loginMutation.error}
        />
      </>
    );
  }

  if (membershipsQuery.isPending || membershipsQuery.error || !spaceId) {
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

  return (
    <AuthenticatedApp
      tokens={tokens}
      logout={logout}
      apiBaseUrl={config.apiBaseUrl}
      spaceId={spaceId}
    />
  );
}
