import { FormEvent, useMemo, useState } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { Link, Navigate, Route, Routes, useLocation, useNavigate } from 'react-router-dom';
import type { TokenView } from './api/generated/models/TokenView';
import { loadReferenceClientConfig } from './client/config';
import { createReferenceApis, runMemoryMediaStoryFlow, signIn } from './client/referenceFlow';
import { StoryList } from './components/StoryList';

function readableError(error: unknown, fallback: string): string {
  if (!(error instanceof Error)) return fallback;
  if (!error.message || error.message === 'Response returned an error code') return fallback;
  return error.message;
}

function Brand() {
  return (
    <Link className="brand" to="/story" aria-label="SideBySide – zur Story">
      <span className="brand-mark" aria-hidden="true">S</span>
      <span>SideBySide</span>
    </Link>
  );
}

function SetupNotice() {
  return (
    <main className="setup-shell">
      <section className="setup-card" aria-labelledby="setup-heading">
        <div className="brand brand-static">
          <span className="brand-mark" aria-hidden="true">S</span>
          <span>SideBySide</span>
        </div>
        <p className="eyebrow">Fast bereit</p>
        <h1 id="setup-heading">Diese Installation ist noch nicht vollständig eingerichtet.</h1>
        <p>Bitte wende dich an die Person, die diese SideBySide-Instanz betreibt.</p>
        <details className="operator-note">
          <summary>Hinweis für Betreiber</summary>
          <p>Für den aktuellen Story-Flow muss beim Web-Build eine vorhandene Space-ID als <code>SBS_WEB_SPACE_ID</code> gesetzt sein.</p>
        </details>
      </section>
    </main>
  );
}

function LoginScreen({ onLogin, pending, error }: {
  onLogin: (email: string, password: string) => void;
  pending: boolean;
  error: unknown;
}) {
  function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const data = new FormData(event.currentTarget);
    onLogin(String(data.get('email')), String(data.get('password')));
  }

  return (
    <main className="login-shell">
      <section className="login-intro" aria-labelledby="welcome-heading">
        <div className="brand brand-static brand-inverse">
          <span className="brand-mark" aria-hidden="true">S</span>
          <span>SideBySide</span>
        </div>
        <p className="eyebrow eyebrow-inverse">Euer gemeinsamer Ort</p>
        <h1 id="welcome-heading">Erinnerungen, die euch gehören.</h1>
        <p>Haltet gemeinsame Momente fest und findet eure Geschichte an einem ruhigen, privaten Ort wieder.</p>
      </section>

      <section className="login-card" aria-labelledby="login-heading">
        <div>
          <p className="eyebrow">Willkommen zurück</p>
          <h2 id="login-heading">Anmelden</h2>
          <p className="muted">Melde dich mit deinem SideBySide-Konto an.</p>
        </div>
        <form onSubmit={submit} className="form-grid">
          <label htmlFor="email">E-Mail</label>
          <input id="email" name="email" type="email" autoComplete="username" required />
          <label htmlFor="password">Passwort</label>
          <input id="password" name="password" type="password" autoComplete="current-password" required />
          <button type="submit" disabled={pending}>
            {pending ? 'Anmeldung läuft …' : 'Anmelden'}
          </button>
        </form>
        <p className="status status-error" role="alert" aria-live="polite">
          {error ? readableError(error, 'Anmeldung fehlgeschlagen. Bitte prüfe deine Zugangsdaten und versuche es erneut.') : ''}
        </p>
      </section>
    </main>
  );
}

function StoryPage({ storyQuery }: {
  storyQuery: ReturnType<typeof useQuery>;
}) {
  const location = useLocation();
  const saved = Boolean((location.state as { saved?: boolean } | null)?.saved);

  return (
    <div className="page story-page">
      {saved && (
        <div className="inline-message inline-message-success" role="status">
          <strong>Erinnerung gespeichert.</strong>
          <span>Sie ist jetzt Teil eurer gemeinsamen Story.</span>
        </div>
      )}

      <header className="page-heading story-heading">
        <div>
          <p className="eyebrow">Gemeinsam erinnern</p>
          <h1>Eure Story</h1>
          <p>Erinnerungen, Herzmomente und Meilensteine – chronologisch an einem Ort.</p>
        </div>
        <Link className="button-link primary-action" to="/memory/new">Erinnerung hinzufügen</Link>
      </header>

      <section className="story-surface" aria-labelledby="timeline-heading">
        <div className="section-head">
          <div>
            <p className="section-kicker">Zeitleiste</p>
            <h2 id="timeline-heading">Gemeinsame Geschichte</h2>
          </div>
          <button
            type="button"
            className="secondary compact-action"
            onClick={() => storyQuery.refetch()}
            disabled={storyQuery.isFetching}
          >
            {storyQuery.isFetching ? 'Aktualisiert …' : 'Aktualisieren'}
          </button>
        </div>

        {storyQuery.isLoading && (
          <div className="story-loading" role="status" aria-label="Story wird geladen">
            <span />
            <span />
            <span />
          </div>
        )}
        {storyQuery.error instanceof Error && (
          <div className="inline-message inline-message-error" role="alert">
            <strong>Die Story konnte nicht geladen werden.</strong>
            <span>{readableError(storyQuery.error, 'Bitte versuche es erneut.')}</span>
            <button type="button" className="secondary" onClick={() => storyQuery.refetch()}>Erneut versuchen</button>
          </div>
        )}
        {storyQuery.data && <StoryList items={storyQuery.data.items} />}
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
  const navigate = useNavigate();
  const [file, setFile] = useState<File | null>(null);
  const apis = useMemo(() => createReferenceApis(apiBaseUrl, accessToken), [apiBaseUrl, accessToken]);

  const mutation = useMutation({
    mutationFn: ({ title, body, happenedOn }: { title: string; body: string; happenedOn?: Date }) => {
      if (!file) throw new Error('Bitte wähle ein Bild aus.');
      return runMemoryMediaStoryFlow(
        apis,
        apiBaseUrl,
        accessToken,
        spaceId,
        { title, body, happenedOn },
        file,
      );
    },
    onSuccess: async (result) => {
      URL.revokeObjectURL(result.imageUrl);
      await onSaved();
      navigate('/story', { replace: true, state: { saved: true } });
    },
  });

  function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const data = new FormData(event.currentTarget);
    const happenedOnValue = String(data.get('happenedOn') || '');
    mutation.mutate({
      title: String(data.get('title')),
      body: String(data.get('body')),
      happenedOn: happenedOnValue ? new Date(`${happenedOnValue}T00:00:00Z`) : undefined,
    });
  }

  return (
    <div className="page create-page">
      <Link className="back-link" to="/story">← Zurück zur Story</Link>
      <header className="page-heading create-heading">
        <div>
          <p className="eyebrow">Moment festhalten</p>
          <h1>Neue Erinnerung</h1>
          <p>Ein Foto, ein paar Worte – und dieser Moment bleibt Teil eurer Geschichte.</p>
        </div>
      </header>

      <section className="form-card" aria-labelledby="memory-form-heading">
        <h2 id="memory-form-heading" className="sr-only">Erinnerung erstellen</h2>
        <form onSubmit={submit} className="form-grid memory-form">
          <div className="field-group">
            <label htmlFor="title">Titel</label>
            <input id="title" name="title" required maxLength={200} placeholder="Zum Beispiel: Unser Tag am See" />
          </div>

          <div className="field-group">
            <label htmlFor="body">Erinnerung</label>
            <textarea id="body" name="body" required rows={5} placeholder="Was möchtet ihr von diesem Moment behalten?" />
          </div>

          <div className="field-group">
            <label htmlFor="happenedOn">Datum</label>
            <input id="happenedOn" name="happenedOn" type="date" />
            <p className="field-help">Optional – wenn der Moment an einem bestimmten Tag war.</p>
          </div>

          <div className="field-group">
            <label htmlFor="image">Foto</label>
            <label className="file-picker" htmlFor="image">
              <span className="file-picker-icon" aria-hidden="true">＋</span>
              <span>
                <strong>{file ? 'Foto ausgewählt' : 'Foto auswählen'}</strong>
                <small>{file ? file.name : 'JPG, PNG, WebP, HEIC oder HEIF'}</small>
              </span>
            </label>
            <input
              className="visually-hidden-input"
              id="image"
              name="image"
              type="file"
              accept="image/jpeg,image/png,image/webp,image/heic,image/heif"
              required
              onChange={(event) => setFile(event.currentTarget.files?.[0] ?? null)}
            />
          </div>

          <div className="sharing-note" aria-label="Sichtbarkeit">
            <span className="sharing-icon" aria-hidden="true">♥</span>
            <div>
              <strong>Mit Partner geteilt</strong>
              <p>Diese Erinnerung ist für beide Personen in eurem gemeinsamen Space sichtbar.</p>
            </div>
          </div>

          <div className="form-actions">
            <Link className="button-link secondary-link" to="/story">Abbrechen</Link>
            <button type="submit" disabled={mutation.isPending || !file}>
              {mutation.isPending ? 'Wird gespeichert …' : 'Erinnerung speichern'}
            </button>
          </div>
        </form>

        {mutation.isPending && (
          <p className="status" role="status" aria-live="polite">Foto wird verarbeitet und die Story aktualisiert …</p>
        )}
        {mutation.error && (
          <div className="inline-message inline-message-error form-error" role="alert">
            <strong>Die Erinnerung konnte nicht gespeichert werden.</strong>
            <span>{readableError(mutation.error, 'Bitte prüfe deine Verbindung und versuche es erneut.')}</span>
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
  const queryClient = useQueryClient();
  const apis = useMemo(() => createReferenceApis(apiBaseUrl, tokens.accessToken), [apiBaseUrl, tokens.accessToken]);
  const storyQuery = useQuery({
    queryKey: ['story', spaceId, tokens.accessToken],
    queryFn: () => apis.story.getStoryTimeline({ spaceId, limit: 25 }),
    retry: false,
  });

  async function refreshStory() {
    await queryClient.invalidateQueries({ queryKey: ['story', spaceId] });
  }

  return (
    <div className="app-shell">
      <header className="app-header">
        <Brand />
        <div className="header-actions">
          <span className="shared-context"><span aria-hidden="true">♥</span> Gemeinsamer Bereich</span>
          <button type="button" className="tertiary" onClick={logout}>Abmelden</button>
        </div>
      </header>

      <main className="app-main">
        <Routes>
          <Route path="/" element={<Navigate replace to="/story" />} />
          <Route path="/story" element={<StoryPage storyQuery={storyQuery} />} />
          <Route
            path="/memory/new"
            element={(
              <MemoryCreatePage
                accessToken={tokens.accessToken}
                apiBaseUrl={apiBaseUrl}
                spaceId={spaceId}
                onSaved={refreshStory}
              />
            )}
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
    mutationFn: ({ email, password }: { email: string; password: string }) => signIn(config.apiBaseUrl, email, password),
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
