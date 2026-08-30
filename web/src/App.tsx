import { useEffect, useMemo, useState } from 'react';
import { useQuery, useQueryClient } from '@tanstack/react-query';
import type { AccountView } from './api/generated/models/AccountView';
import type { SpaceView } from './api/generated/models/SpaceView';
import type { TokenView } from './api/generated/models/TokenView';
import { loadReferenceClientConfig } from './client/config';
import {
  readSensitiveEntryToken,
  stripSensitiveEntryToken,
} from './client/entryToken';
import {
  loadAuthorizedMemberships,
  loadAuthorizedSpaces,
  resolveActiveSpaceId,
} from './client/spaceContext';
import { AuthenticatedApp } from './components/AuthenticatedApp';
import { Brand } from './components/Brand';
import { IdentityEntry } from './components/IdentityEntry';
import { ProblemState } from './components/ProblemState';
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
