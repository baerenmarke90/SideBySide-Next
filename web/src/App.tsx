import { useEffect, useMemo, useState, type FormEvent } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import type { SessionView, StoryItem } from './api/generated';
import { createApiSet } from './api/client';
import { referenceConfig } from './config';
import { ReferenceFlow, storyItemTitle } from './referenceFlow';

function errorText(error: unknown): string {
  if (error instanceof Error) return error.message;
  return 'Unbekannter Fehler.';
}

function MemoryImage({
  flow,
  spaceId,
  memoryId,
  attachmentId,
  alt,
}: {
  flow: ReferenceFlow;
  spaceId: string;
  memoryId: string;
  attachmentId: string;
  alt: string;
}) {
  const image = useQuery({
    queryKey: ['memory-image', memoryId, attachmentId],
    queryFn: () => flow.loadMemoryImage(spaceId, memoryId, attachmentId),
  });

  useEffect(() => {
    return () => {
      if (image.data?.startsWith('blob:')) URL.revokeObjectURL(image.data);
    };
  }, [image.data]);

  if (image.isPending) return <p className="media-status">Bild wird geladen …</p>;
  if (image.isError) return <p className="media-error">Bild konnte nicht geladen werden.</p>;
  return <img className="story-image" src={image.data} alt={alt} />;
}

export function StoryCard({ item, flow, spaceId }: { item: StoryItem; flow: ReferenceFlow; spaceId: string }) {
  if (item.kind === 'MEMORY') {
    return (
      <article className="story-card" aria-labelledby={`story-${item.memory.id}`}>
        <p className="kind">Erinnerung</p>
        <h2 id={`story-${item.memory.id}`}>{item.memory.title}</h2>
        <p className="meta">{item.effectiveDate.toLocaleDateString('de-DE')} · {item.memory.author.displayName}</p>
        {item.memory.attachments.map((attachment, index) => (
          <MemoryImage
            key={attachment.id}
            flow={flow}
            spaceId={spaceId}
            memoryId={item.memory.id}
            attachmentId={attachment.id}
            alt={`Bild ${index + 1} zur Erinnerung „${item.memory.title}“`}
          />
        ))}
      </article>
    );
  }

  if (item.kind === 'MILESTONE') {
    return (
      <article className="story-card" aria-labelledby={`story-${item.milestone.id}`}>
        <p className="kind">Meilenstein</p>
        <h2 id={`story-${item.milestone.id}`}>{item.milestone.title}</h2>
        <p className="meta">{item.effectiveDate.toLocaleDateString('de-DE')} · {item.milestone.author.displayName}</p>
      </article>
    );
  }

  return (
    <article className="story-card" aria-labelledby={`story-${item.heartMoment.id}`}>
      <p className="kind">Herzmoment</p>
      <h2 id={`story-${item.heartMoment.id}`}>{storyItemTitle(item)}</h2>
      <p className="meta">{item.effectiveDate.toLocaleDateString('de-DE')} · {item.heartMoment.author.displayName}</p>
    </article>
  );
}

export default function App() {
  const queryClient = useQueryClient();
  const [session, setSession] = useState<SessionView | null>(null);
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [title, setTitle] = useState('');
  const [body, setBody] = useState('');
  const [happenedOn, setHappenedOn] = useState('');
  const [image, setImage] = useState<File | undefined>();
  const [statusMessage, setStatusMessage] = useState('');

  const anonymousApi = useMemo(() => createApiSet(referenceConfig.apiBaseUrl), []);
  const api = useMemo(
    () => createApiSet(referenceConfig.apiBaseUrl, session?.tokens.accessToken),
    [session?.tokens.accessToken],
  );
  const flow = useMemo(
    () =>
      session
        ? new ReferenceFlow({
            api,
            apiBaseUrl: referenceConfig.apiBaseUrl,
            accessToken: session.tokens.accessToken,
          })
        : null,
    [api, session],
  );

  const story = useQuery({
    queryKey: ['story', referenceConfig.spaceId, session?.account.id],
    queryFn: () => api.story.getStoryTimeline({ spaceId: referenceConfig.spaceId!, limit: 50 }),
    enabled: Boolean(session && referenceConfig.spaceId),
  });

  const signIn = useMutation({
    mutationFn: () =>
      anonymousApi.auth.signInApiV1AuthSignInPost({
        signInRequest: { email, password, deviceName: 'SideBySide Web Referenz', platform: 'WEB' },
      }),
    onSuccess: (nextSession) => {
      setSession(nextSession);
      setPassword('');
      setStatusMessage(`Angemeldet als ${nextSession.account.displayName}.`);
    },
  });

  const createMemory = useMutation({
    mutationFn: async () => {
      if (!flow || !referenceConfig.spaceId) throw new Error('Referenz-Space ist nicht konfiguriert.');
      return flow.createMemoryWithImage(referenceConfig.spaceId, {
        title,
        body,
        happenedOn: happenedOn ? new Date(`${happenedOn}T00:00:00`) : undefined,
        image,
      });
    },
    onSuccess: async (memory) => {
      setTitle('');
      setBody('');
      setHappenedOn('');
      setImage(undefined);
      setStatusMessage(`„${memory.title}“ wurde gespeichert und an die Story übergeben.`);
      await queryClient.invalidateQueries({ queryKey: ['story'] });
    },
  });

  function submitSignIn(event: FormEvent) {
    event.preventDefault();
    setStatusMessage('');
    signIn.mutate();
  }

  function submitMemory(event: FormEvent) {
    event.preventDefault();
    setStatusMessage('');
    createMemory.mutate();
  }

  function logout() {
    setSession(null);
    setImage(undefined);
    queryClient.clear();
    setStatusMessage('Abgemeldet. Flüchtiger Client-State wurde geleert.');
  }

  if (!referenceConfig.spaceId) {
    return (
      <main className="shell">
        <h1>SideBySide Next · M2 Referenzflow</h1>
        <section className="notice" aria-labelledby="missing-config">
          <h2 id="missing-config">Referenz-Space fehlt</h2>
          <p>Der Betreiber muss <code>VITE_SBS_SPACE_ID</code> setzen. Normale Nutzer konfigurieren keine technischen IDs.</p>
        </section>
      </main>
    );
  }

  return (
    <main className="shell">
      <header className="page-header">
        <div>
          <p className="eyebrow">M2-S8 · technischer Referenzflow</p>
          <h1>Memory · Bild · Story</h1>
        </div>
        {session ? <button type="button" className="secondary" onClick={logout}>Abmelden</button> : null}
      </header>

      <p className="sr-only" aria-live="polite">{statusMessage}</p>

      {!session ? (
        <section className="panel" aria-labelledby="login-heading">
          <h2 id="login-heading">Anmelden</h2>
          <form onSubmit={submitSignIn}>
            <label htmlFor="email">E-Mail</label>
            <input id="email" type="email" autoComplete="username" required value={email} onChange={(event) => setEmail(event.target.value)} />
            <label htmlFor="password">Passwort</label>
            <input id="password" type="password" autoComplete="current-password" required value={password} onChange={(event) => setPassword(event.target.value)} />
            <button type="submit" disabled={signIn.isPending}>{signIn.isPending ? 'Anmeldung läuft …' : 'Anmelden'}</button>
          </form>
          {signIn.isError ? <p role="alert" className="error">Anmeldung fehlgeschlagen: {errorText(signIn.error)}</p> : null}
        </section>
      ) : (
        <>
          <section className="panel" aria-labelledby="new-memory-heading">
            <h2 id="new-memory-heading">Erinnerung festhalten</h2>
            <form onSubmit={submitMemory}>
              <label htmlFor="title">Titel</label>
              <input id="title" required maxLength={200} value={title} onChange={(event) => setTitle(event.target.value)} />
              <label htmlFor="body">Text</label>
              <textarea id="body" required rows={4} value={body} onChange={(event) => setBody(event.target.value)} />
              <label htmlFor="date">Datum</label>
              <input id="date" type="date" value={happenedOn} onChange={(event) => setHappenedOn(event.target.value)} />
              <label htmlFor="image">Bild (optional)</label>
              <input
                id="image"
                type="file"
                accept="image/jpeg,image/png,image/webp,image/heic,image/heif"
                onChange={(event) => setImage(event.target.files?.[0])}
              />
              <p className="help">Video ist in M2 bewusst nicht verfügbar.</p>
              <button type="submit" disabled={createMemory.isPending}>{createMemory.isPending ? 'Speichern und verarbeiten …' : 'Erinnerung speichern'}</button>
            </form>
            {createMemory.isError ? <p role="alert" className="error">Speichern fehlgeschlagen: {errorText(createMemory.error)}</p> : null}
          </section>

          <section className="story" aria-labelledby="story-heading" aria-busy={story.isFetching}>
            <div className="section-heading">
              <h2 id="story-heading">Gemeinsame Story</h2>
              <button type="button" className="secondary" onClick={() => story.refetch()} disabled={story.isFetching}>Neu laden</button>
            </div>
            {story.isPending ? <p role="status">Story wird geladen …</p> : null}
            {story.isError ? <p role="alert" className="error">Story konnte nicht geladen werden: {errorText(story.error)}</p> : null}
            {story.data?.items.length === 0 ? <p>Die gemeinsame Story ist noch leer.</p> : null}
            {story.data?.items.map((item) => {
              const id = item.kind === 'MEMORY' ? item.memory.id : item.kind === 'MILESTONE' ? item.milestone.id : item.heartMoment.id;
              return <StoryCard key={`${item.kind}-${id}`} item={item} flow={flow!} spaceId={referenceConfig.spaceId!} />;
            })}
          </section>
        </>
      )}
    </main>
  );
}
