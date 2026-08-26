import { FormEvent, useEffect, useMemo, useState } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import type { TokenView } from './api/generated/models/TokenView';
import { loadReferenceClientConfig } from './client/config';
import { createReferenceApis, runMemoryMediaStoryFlow, signIn, type FlowResult } from './client/referenceFlow';
import { StoryList } from './components/StoryList';

export function App() {
  const config = useMemo(loadReferenceClientConfig, []);
  const queryClient = useQueryClient();
  const [tokens, setTokens] = useState<TokenView | null>(null);
  const [lastResult, setLastResult] = useState<FlowResult | null>(null);
  const [file, setFile] = useState<File | null>(null);

  useEffect(() => () => {
    if (lastResult?.imageUrl) URL.revokeObjectURL(lastResult.imageUrl);
  }, [lastResult]);

  const apis = useMemo(
    () => createReferenceApis(config.apiBaseUrl, tokens?.accessToken),
    [config.apiBaseUrl, tokens?.accessToken],
  );

  const storyQuery = useQuery({
    queryKey: ['story', config.spaceId, tokens?.accessToken],
    queryFn: () => apis.story.getStoryTimeline({ spaceId: config.spaceId, limit: 25 }),
    enabled: Boolean(tokens?.accessToken && config.spaceId),
    retry: false,
  });

  const loginMutation = useMutation({
    mutationFn: ({ email, password }: { email: string; password: string }) => signIn(config.apiBaseUrl, email, password),
    onSuccess: (session) => {
      setTokens(session.tokens);
      queryClient.clear();
    },
  });

  const flowMutation = useMutation({
    mutationFn: ({ title, body, happenedOn }: { title: string; body: string; happenedOn?: Date }) => {
      if (!tokens || !file) throw new Error('Bitte zuerst anmelden und ein Bild auswählen.');
      return runMemoryMediaStoryFlow(
        apis,
        config.apiBaseUrl,
        tokens.accessToken,
        config.spaceId,
        { title, body, happenedOn },
        file,
      );
    },
    onSuccess: async (result) => {
      setLastResult(result);
      await queryClient.invalidateQueries({ queryKey: ['story'] });
    },
  });

  function handleLogin(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const data = new FormData(event.currentTarget);
    loginMutation.mutate({ email: String(data.get('email')), password: String(data.get('password')) });
  }

  function handleCreate(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const data = new FormData(event.currentTarget);
    const happenedOnValue = String(data.get('happenedOn') || '');
    flowMutation.mutate({
      title: String(data.get('title')),
      body: String(data.get('body')),
      happenedOn: happenedOnValue ? new Date(`${happenedOnValue}T00:00:00Z`) : undefined,
    });
  }

  function logout() {
    setTokens(null);
    setLastResult(null);
    setFile(null);
    queryClient.clear();
  }

  if (!config.spaceId) {
    return (
      <main className="shell">
        <h1>SideBySide Next</h1>
        <p role="alert">Der M2-Referenzflow ist operatorseitig noch nicht konfiguriert.</p>
      </main>
    );
  }

  return (
    <main className="shell">
      <header className="hero">
        <p className="eyebrow">M2 · technischer Referenzflow</p>
        <h1>Eine Erinnerung mit Bild in eurer Story</h1>
        <p>Dieser dünne Client belegt den echten Memory-/Media-/Story-Vertrag. Er ist noch keine vollständige Web-App.</p>
      </header>

      {!tokens ? (
        <section aria-labelledby="login-heading" className="panel">
          <h2 id="login-heading">Anmelden</h2>
          <form onSubmit={handleLogin} className="form-grid">
            <label htmlFor="email">E-Mail</label>
            <input id="email" name="email" type="email" autoComplete="username" required />
            <label htmlFor="password">Passwort</label>
            <input id="password" name="password" type="password" autoComplete="current-password" required />
            <button type="submit" disabled={loginMutation.isPending}>Anmelden</button>
          </form>
          <p className="status" role="status" aria-live="polite">
            {loginMutation.isPending ? 'Anmeldung läuft …' : loginMutation.error instanceof Error ? loginMutation.error.message : ''}
          </p>
        </section>
      ) : (
        <>
          <div className="session-row">
            <span>Authentifiziert</span>
            <button type="button" className="secondary" onClick={logout}>Abmelden</button>
          </div>

          <section aria-labelledby="create-heading" className="panel">
            <h2 id="create-heading">Erinnerung festhalten</h2>
            <form onSubmit={handleCreate} className="form-grid">
              <label htmlFor="title">Titel</label>
              <input id="title" name="title" required maxLength={200} />
              <label htmlFor="body">Erinnerung</label>
              <textarea id="body" name="body" required rows={4} />
              <label htmlFor="happenedOn">Datum</label>
              <input id="happenedOn" name="happenedOn" type="date" />
              <label htmlFor="image">Bild</label>
              <input
                id="image"
                name="image"
                type="file"
                accept="image/jpeg,image/png,image/webp,image/heic,image/heif"
                required
                onChange={(event) => setFile(event.currentTarget.files?.[0] ?? null)}
              />
              <button type="submit" disabled={flowMutation.isPending || !file}>
                {flowMutation.isPending ? 'Wird gespeichert …' : 'Erinnerung mit Bild speichern'}
              </button>
            </form>
            <p className="status" role="status" aria-live="polite">
              {flowMutation.isPending
                ? 'Memory wird angelegt, Bild verarbeitet und die Story aktualisiert …'
                : flowMutation.error instanceof Error
                  ? flowMutation.error.message
                  : lastResult
                    ? 'Erinnerung und Bild wurden erfolgreich über den M2-Vertrag gespeichert.'
                    : ''}
            </p>
          </section>

          {lastResult && (
            <section aria-labelledby="result-heading" className="panel memory-result">
              <h2 id="result-heading">Zuletzt gespeichert</h2>
              <img src={lastResult.imageUrl} alt="Ausgewähltes Bild zur zuletzt gespeicherten Erinnerung" />
              <h3>{lastResult.memory.title}</h3>
              <p>{lastResult.memory.body}</p>
            </section>
          )}

          <section aria-labelledby="story-heading" className="panel">
            <div className="section-head">
              <h2 id="story-heading">Gemeinsame Story</h2>
              <button type="button" className="secondary" onClick={() => storyQuery.refetch()} disabled={storyQuery.isFetching}>
                Aktualisieren
              </button>
            </div>
            <div aria-live="polite">
              {storyQuery.isLoading && <p role="status">Story wird geladen …</p>}
              {storyQuery.error instanceof Error && <p role="alert">{storyQuery.error.message}</p>}
              {storyQuery.data && <StoryList items={storyQuery.data.items} />}
            </div>
          </section>
        </>
      )}
    </main>
  );
}
