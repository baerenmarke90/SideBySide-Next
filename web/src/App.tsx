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
import {
  createMemoryWithPreparedAttachments,
  createReferenceApis,
  loadAuthorizedImage,
  prepareAttachment,
  signIn,
  type AttachmentPreparationPhase,
  type PreparedAttachment,
} from './client/referenceFlow';
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

type DraftAttachmentStatus =
  | 'preparing'
  | AttachmentPreparationPhase
  | 'failed';

interface DraftAttachment {
  id: number;
  file: File;
  previewUrl: string;
  status: DraftAttachmentStatus;
  prepared?: PreparedAttachment;
  error?: string;
}

function revokeDraftPreview({ previewUrl }: DraftAttachment) {
  URL.revokeObjectURL(previewUrl);
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
  const [attachments, setAttachments] = useState<DraftAttachment[]>([]);
  const attachmentsRef = useRef<DraftAttachment[]>([]);
  const activeAttachmentIds = useRef(new Set<number>());
  const attachmentSequence = useRef(0);
  const apis = useMemo(
    () => createReferenceApis(apiBaseUrl, accessToken),
    [apiBaseUrl, accessToken],
  );

  useEffect(() => {
    attachmentsRef.current = attachments;
  }, [attachments]);

  useEffect(
    () => () => {
      activeAttachmentIds.current.clear();
      attachmentsRef.current.forEach(revokeDraftPreview);
    },
    [],
  );

  function updateAttachment(
    id: number,
    update: (attachment: DraftAttachment) => DraftAttachment,
  ) {
    setAttachments((current) =>
      current.map((attachment) =>
        attachment.id === id ? update(attachment) : attachment,
      ),
    );
  }

  async function uploadDraft(attachment: DraftAttachment) {
    activeAttachmentIds.current.add(attachment.id);
    updateAttachment(attachment.id, (current) => ({
      ...current,
      status: 'uploading',
      prepared: undefined,
      error: undefined,
    }));

    try {
      const prepared = await prepareAttachment(
        apis,
        apiBaseUrl,
        accessToken,
        spaceId,
        attachment.file,
        (phase) => {
          if (!activeAttachmentIds.current.has(attachment.id)) return;
          updateAttachment(attachment.id, (current) => ({
            ...current,
            status: phase,
          }));
        },
      );
      if (!activeAttachmentIds.current.has(attachment.id)) return;
      updateAttachment(attachment.id, (current) => ({
        ...current,
        status: 'ready',
        prepared,
        error: undefined,
      }));
    } catch (error) {
      if (!activeAttachmentIds.current.has(attachment.id)) return;
      updateAttachment(attachment.id, (current) => ({
        ...current,
        status: 'failed',
        prepared: undefined,
        error: readableError(error, t('memory.uploadFailed')),
      }));
    }
  }

  function selectFiles(files: FileList | null) {
    if (!files) return;
    for (const file of Array.from(files)) {
      const attachment: DraftAttachment = {
        id: ++attachmentSequence.current,
        file,
        previewUrl: URL.createObjectURL(file),
        status: 'preparing',
      };
      activeAttachmentIds.current.add(attachment.id);
      setAttachments((current) => [...current, attachment]);
      void uploadDraft(attachment);
    }
  }

  function removeAttachment(id: number) {
    activeAttachmentIds.current.delete(id);
    const attachment = attachmentsRef.current.find((item) => item.id === id);
    if (attachment) URL.revokeObjectURL(attachment.previewUrl);
    setAttachments((current) => current.filter((item) => item.id !== id));
  }

  function retryAttachment(attachment: DraftAttachment) {
    activeAttachmentIds.current.add(attachment.id);
    updateAttachment(attachment.id, (current) => ({
      ...current,
      status: 'preparing',
      prepared: undefined,
      error: undefined,
    }));
    void uploadDraft(attachment);
  }

  function clearDraftAttachments() {
    activeAttachmentIds.current.clear();
    attachmentsRef.current.forEach(revokeDraftPreview);
    attachmentsRef.current = [];
    setAttachments([]);
  }

  const uploadsPending = attachments.some(
    (attachment) => attachment.status !== 'ready',
  );

  const mutation = useMutation({
    mutationFn: ({
      title,
      body,
      happenedOn,
      preparedAttachments,
    }: {
      title: string;
      body: string;
      happenedOn?: Date;
      preparedAttachments: PreparedAttachment[];
    }) =>
      createMemoryWithPreparedAttachments(
        apis,
        apiBaseUrl,
        accessToken,
        spaceId,
        { title, body, happenedOn },
        preparedAttachments,
      ),
    onSuccess: async (result) => {
      clearDraftAttachments();
      if (result.imageUrl?.startsWith('blob:')) {
        URL.revokeObjectURL(result.imageUrl);
      }
      await onSaved();
      navigate('/story', { replace: true, state: { saved: true } });
    },
  });

  function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (uploadsPending) return;
    const data = new FormData(event.currentTarget);
    const happenedOnValue = String(data.get('happenedOn') || '');
    mutation.mutate({
      title: String(data.get('title')),
      body: String(data.get('body')),
      happenedOn: happenedOnValue
        ? new Date(`${happenedOnValue}T00:00:00Z`)
        : undefined,
      preparedAttachments: attachments.flatMap((attachment) =>
        attachment.prepared ? [attachment.prepared] : [],
      ),
    });
  }

  function statusText(status: DraftAttachmentStatus): string {
    switch (status) {
      case 'preparing':
        return t('memory.uploadPreparing');
      case 'uploading':
        return t('memory.uploadUploading');
      case 'validating':
        return t('memory.uploadValidating');
      case 'ready':
        return t('memory.uploadReady');
      case 'failed':
        return t('memory.uploadFailed');
    }
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
              multiple
              disabled={mutation.isPending}
              accept="image/jpeg,image/png,image/webp,image/heic,image/heif"
              onChange={(event) => {
                selectFiles(event.currentTarget.files);
                event.currentTarget.value = '';
              }}
            />
            <label className="file-picker" htmlFor="image">
              <span className="file-picker-icon" aria-hidden="true">
                ＋
              </span>
              <span>
                <strong>
                  {attachments.length > 0
                    ? t('memory.photoSelected')
                    : t('memory.photoSelect')}
                </strong>
                <small>
                  {attachments.length > 0
                    ? attachments.map(({ file }) => file.name).join(', ')
                    : t('memory.photoFormats')}
                </small>
              </span>
            </label>
          </div>

          {attachments.length > 0 && (
            <div className="attachment-draft-list" aria-live="polite">
              {attachments.map((attachment) => (
                <article className="attachment-draft" key={attachment.id}>
                  <img
                    className="attachment-draft-preview"
                    src={attachment.previewUrl}
                    alt={t('memory.previewAlt', { name: attachment.file.name })}
                  />
                  <div className="attachment-draft-details">
                    <strong>{attachment.file.name}</strong>
                    <span
                      className={`attachment-status attachment-status-${attachment.status}`}
                      role="status"
                    >
                      {statusText(attachment.status)}
                    </span>
                    {attachment.error && (
                      <span className="attachment-error" role="alert">
                        {attachment.error}
                      </span>
                    )}
                    <div className="attachment-actions">
                      {attachment.status === 'failed' && (
                        <button
                          type="button"
                          className="secondary compact-action"
                          onClick={() => retryAttachment(attachment)}
                          disabled={mutation.isPending}
                        >
                          {t('common.retry')}
                        </button>
                      )}
                      <button
                        type="button"
                        className="tertiary compact-action"
                        onClick={() => removeAttachment(attachment.id)}
                        disabled={mutation.isPending}
                      >
                        {t('common.remove')}
                      </button>
                    </div>
                  </div>
                </article>
              ))}
              <p className="field-help">{t('memory.previewNotice')}</p>
            </div>
          )}

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
              disabled={mutation.isPending || uploadsPending}
            >
              {mutation.isPending ? t('memory.saving') : t('memory.save')}
            </button>
          </div>
        </form>

        {uploadsPending && attachments.length > 0 && (
          <p className="status" role="status" aria-live="polite">
            {t('memory.uploadsPending')}
          </p>
        )}
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
