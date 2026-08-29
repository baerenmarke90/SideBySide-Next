import { type FormEvent, useCallback, useMemo, useState } from 'react';
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
import {
  createReferenceApis,
  loadAuthorizedImage,
  signIn,
} from './client/referenceFlow';
import { useAttachmentDrafts } from './client/useAttachmentDrafts';
import { StoryList } from './components/StoryList';
import { useTranslation } from './i18n';

function readableError(error: unknown, fallback: string): string {
  if (!(error instanceof Error)) return fallback;
  if (!error.message || error.message === 'Response returned an error code')
    return fallback;
  return error.message;
}

function Brand() {
  const { t } = useTranslation();
  return (
    <Link className="brand" to="/story" aria-label={t('brand.storyAria')}>
      <span className="brand-mark" aria-hidden="true">
        S
      </span>
      <span>SideBySide</span>
    </Link>
  );
}

function SetupNotice() {
  const { t } = useTranslation();
  return (
    <main className="setup-shell">
      <section className="setup-card" aria-labelledby="setup-heading">
        <div className="brand brand-static">
          <span className="brand-mark" aria-hidden="true">
            S
          </span>
          <span>SideBySide</span>
        </div>
        <p className="eyebrow">{t('setup.eyebrow')}</p>
        <h1 id="setup-heading">{t('setup.heading')}</h1>
        <p>{t('setup.body')}</p>
        <details className="operator-note">
          <summary>{t('setup.operatorSummary')}</summary>
          <p>
            {t('setup.operatorPrefix')} <code>SBS_WEB_SPACE_ID</code>{' '}
            {t('setup.operatorSuffix')}
          </p>
        </details>
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
        <div className="brand brand-static brand-inverse">
          <span className="brand-mark" aria-hidden="true">
            S
          </span>
          <span>SideBySide</span>
        </div>
        <p className="eyebrow eyebrow-inverse">{t('login.introEyebrow')}</p>
        <h1 id="welcome-heading">{t('login.introHeading')}</h1>
        <p>{t('login.introBody')}</p>
      </section>

      <section className="login-card" aria-labelledby="login-heading">
        <div>
          <p className="eyebrow">{t('login.eyebrow')}</p>
          <h2 id="login-heading">{t('login.heading')}</h2>
          <p className="muted">{t('login.body')}</p>
        </div>
        <form onSubmit={submit} className="form-grid">
          <label htmlFor="email">{t('login.email')}</label>
          <input
            id="email"
            name="email"
            type="email"
            autoComplete="username"
            required
          />
          <label htmlFor="password">{t('login.password')}</label>
          <input
            id="password"
            name="password"
            type="password"
            autoComplete="current-password"
            required
          />
          <button type="submit" disabled={pending}>
            {pending ? t('login.pending') : t('login.submit')}
          </button>
        </form>
        <p className="status status-error" role="alert" aria-live="polite">
          {error ? readableError(error, t('login.errorFallback')) : ''}
        </p>
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

      <header className="page-heading story-heading">
        <div>
          <p className="eyebrow">{t('story.eyebrow')}</p>
          <h1>{t('story.title')}</h1>
          <p>{t('story.intro')}</p>
        </div>
        <Link className="button-link primary-action" to="/memory/new">
          {t('story.addMemory')}
        </Link>
      </header>

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

        {storyQuery.isLoading && (
          <div
            className="story-loading"
            role="status"
            aria-label={t('story.loadingAria')}
          >
            <span />
            <span />
            <span />
          </div>
        )}
        {storyQuery.error instanceof Error && (
          <div className="inline-message inline-message-error" role="alert">
            <strong>{t('story.loadErrorTitle')}</strong>
            <span>
              {readableError(storyQuery.error, t('story.loadErrorFallback'))}
            </span>
            <button
              type="button"
              className="secondary"
              onClick={() => storyQuery.refetch()}
            >
              {t('common.retry')}
            </button>
          </div>
        )}
        {storyQuery.data && (
          <StoryList
            items={storyQuery.data.items}
            loadMemoryImage={loadMemoryImage}
          />
        )}
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
    mutationFn: ({
      title,
      body,
      happenedOn,
    }: {
      title: string;
      body: string;
      happenedOn?: Date;
    }) =>
      createMemoryWithReadyAttachments(
        apis,
        spaceId,
        { title, body, happenedOn },
        attachments.readyIds,
      ),
    onSuccess: async () => {
      attachments.clear();
      await onSaved();
      navigate('/story', { replace: true, state: { saved: true } });
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
      <Link className="back-link" to="/story">
        {t('memory.backToStory')}
      </Link>
      <header className="page-heading create-heading">
        <div>
          <p className="eyebrow">{t('memory.eyebrow')}</p>
          <h1>{t('memory.heading')}</h1>
          <p>{t('memory.intro')}</p>
        </div>
      </header>

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
            <Link className="button-link secondary-link" to="/story">
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
        {mutation.error && (
          <div
            className="inline-message inline-message-error form-error"
            role="alert"
          >
            <strong>{t('memory.saveErrorTitle')}</strong>
            <span>
              {readableError(mutation.error, t('memory.saveErrorFallback'))}
            </span>
          </div>
        )}
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
  const queryClient = useQueryClient();
  const apis = useMemo(
    () => createReferenceApis(apiBaseUrl, tokens.accessToken),
    [apiBaseUrl, tokens.accessToken],
  );
  const storyQuery = useQuery({
    queryKey: ['story', spaceId, tokens.accessToken],
    queryFn: () => apis.story.getStoryTimeline({ spaceId, limit: 25 }),
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
    <div className="app-shell">
      <header className="app-header">
        <Brand />
        <div className="header-actions">
          <span className="shared-context">
            <span aria-hidden="true">♥</span> {t('header.sharedArea')}
          </span>
          <button type="button" className="tertiary" onClick={logout}>
            {t('header.logout')}
          </button>
        </div>
      </header>

      <main className="app-main">
        <Routes>
          <Route path="/" element={<Navigate replace to="/story" />} />
          <Route
            path="/story"
            element={
              <StoryPage
                storyQuery={storyQuery}
                loadMemoryImage={loadMemoryImage}
              />
            }
          />
          <Route
            path="/memory/new"
            element={
              <MemoryCreatePage
                accessToken={tokens.accessToken}
                apiBaseUrl={apiBaseUrl}
                spaceId={spaceId}
                onSaved={refreshStory}
              />
            }
          />
          <Route path="*" element={<Navigate replace to="/story" />} />
        </Routes>
      </main>
    </div>
  );
}

export function App() {
  const config = useMemo(loadReferenceClientConfig, []);
  const queryClient = useQueryClient();
  const [tokens, setTokens] = useState<TokenView | null>(null);

  const loginMutation = useMutation({
    mutationFn: ({ email, password }: { email: string; password: string }) =>
      signIn(config.apiBaseUrl, email, password),
    onSuccess: (session) => {
      setTokens(session.tokens);
      queryClient.clear();
    },
  });

  function logout() {
    setTokens(null);
    queryClient.clear();
  }

  if (!config.spaceId) return <SetupNotice />;

  if (!tokens) {
    return (
      <LoginScreen
        onLogin={(email, password) => loginMutation.mutate({ email, password })}
        pending={loginMutation.isPending}
        error={loginMutation.error}
      />
    );
  }

  return (
    <AuthenticatedApp
      tokens={tokens}
      logout={logout}
      apiBaseUrl={config.apiBaseUrl}
      spaceId={config.spaceId}
    />
  );
}