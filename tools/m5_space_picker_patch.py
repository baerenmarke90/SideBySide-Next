from pathlib import Path

SPACE_CONTEXT = """import { SpacesApi } from '../api/generated/apis/SpacesApi';
import type { AccountMembershipView } from '../api/generated/models/AccountMembershipView';
import type { SpaceView } from '../api/generated/models/SpaceView';
import { Configuration } from '../api/generated/runtime';
import { normalizeClientError } from './problemDetails';
import { createReferenceApis } from './referenceFlow';

export async function loadAuthorizedMemberships(
  apiBaseUrl: string,
  accessToken: string,
): Promise<AccountMembershipView[]> {
  try {
    return await createReferenceApis(
      apiBaseUrl,
      accessToken,
    ).auth.listAccountMembershipsApiV1AuthMembershipsGet();
  } catch (error) {
    throw await normalizeClientError(error);
  }
}

export async function loadAuthorizedSpaces(
  apiBaseUrl: string,
  accessToken: string,
  memberships: AccountMembershipView[],
): Promise<SpaceView[]> {
  const spaces = new SpacesApi(
    new Configuration({
      basePath: apiBaseUrl,
      headers: { Authorization: `Bearer ${accessToken}` },
    }),
  );

  try {
    return await Promise.all(
      memberships.map((membership) =>
        spaces.getSpaceApiV1SpacesSpaceIdGet({
          spaceId: membership.spaceId,
        }),
      ),
    );
  } catch (error) {
    throw await normalizeClientError(error);
  }
}

/**
 * Resolve an active Space exclusively from the server-authorized Membership set.
 * A single Membership can enter directly; multiple Spaces require an explicit choice.
 */
export function resolveActiveSpaceId(
  memberships: AccountMembershipView[],
  currentSpaceId: string | null,
): string | null {
  if (
    currentSpaceId &&
    memberships.some((membership) => membership.spaceId === currentSpaceId)
  ) {
    return currentSpaceId;
  }

  return memberships.length === 1 ? memberships[0].spaceId : null;
}
"""

SPACE_CONTEXT_TEST = """import type { AccountMembershipView } from '../api/generated/models/AccountMembershipView';
import { resolveActiveSpaceId } from './spaceContext';

function membership(spaceId: string): AccountMembershipView {
  return { spaceId, role: 'PARTNER', status: 'ACTIVE' };
}

describe('authorized Space context', () => {
  it('enters directly when exactly one server-authorized Space exists', () => {
    expect(resolveActiveSpaceId([membership('space-a')], null)).toBe('space-a');
  });

  it('requires an explicit choice when multiple authorized Spaces exist', () => {
    expect(
      resolveActiveSpaceId(
        [membership('space-a'), membership('space-b')],
        null,
      ),
    ).toBeNull();
  });

  it('keeps the current Space while it remains authorized', () => {
    expect(
      resolveActiveSpaceId(
        [membership('space-a'), membership('space-b')],
        'space-b',
      ),
    ).toBe('space-b');
  });

  it('drops stale client state and never returns an unauthorized Space', () => {
    expect(resolveActiveSpaceId([membership('space-a')], 'space-removed')).toBe(
      'space-a',
    );
    expect(
      resolveActiveSpaceId(
        [membership('space-a'), membership('space-b')],
        'space-removed',
      ),
    ).toBeNull();
    expect(resolveActiveSpaceId([], 'space-removed')).toBeNull();
  });
});
"""

PICKER = """

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
"""

SPACES_QUERY = """    retry: false,
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

  useEffect(() => {"""

OLD_RENDER = """  if (membershipsQuery.isPending || membershipsQuery.error || !spaceId) {
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
  );"""

NEW_RENDER = """  const memberships = membershipsQuery.data ?? [];
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
      logout={logout}
      apiBaseUrl={config.apiBaseUrl}
      spaceId={activeSpaceId}
    />
  );"""

OLD_LOCALE = """  spaceContext: {
    eyebrow: 'Gemeinsamer Bereich',
    loading: 'Euer gemeinsamer Bereich wird geladen …',
    emptyTitle: 'Noch kein gemeinsamer Bereich',
    emptyBody:
      'Für dieses Konto ist noch kein aktiver gemeinsamer Bereich verbunden. Nimm eine Einladung an oder richte euren gemeinsamen Bereich ein.',
  },"""

NEW_LOCALE = """  spaceContext: {
    eyebrow: 'Gemeinsamer Bereich',
    loading: 'Euer gemeinsamer Bereich wird geladen …',
    emptyTitle: 'Noch kein gemeinsamer Bereich',
    emptyBody:
      'Für dieses Konto ist noch kein aktiver gemeinsamer Bereich verbunden. Nimm eine Einladung an oder richte euren gemeinsamen Bereich ein.',
    pickerTitle: 'Welchen Bereich möchtest du öffnen?',
    pickerBody: 'Wähle den gemeinsamen Bereich, mit dem du fortfahren möchtest.',
    pickerAria: 'Gemeinsamen Bereich auswählen',
    spaceFallback: 'Gemeinsamer Bereich {{index}}',
  },"""

Path('web/src/client/spaceContext.ts').write_text(SPACE_CONTEXT, encoding='utf-8')
Path('web/src/client/spaceContext.test.ts').write_text(SPACE_CONTEXT_TEST, encoding='utf-8')

app_path = Path('web/src/App.tsx')
app = app_path.read_text(encoding='utf-8')

space_view_import = "import type { SpaceView } from './api/generated/models/SpaceView';\n"
story_import = "import type { StoryPage as StoryPageData } from './api/generated/models/StoryPage';\n"
if space_view_import not in app:
    if story_import not in app:
        raise SystemExit('StoryPage import anchor not found')
    app = app.replace(story_import, space_view_import + story_import, 1)

if '  loadAuthorizedSpaces,\n' not in app:
    old_imports = "  loadAuthorizedMemberships,\n  resolveActiveSpaceId,\n"
    new_imports = "  loadAuthorizedMemberships,\n  loadAuthorizedSpaces,\n  resolveActiveSpaceId,\n"
    if old_imports not in app:
        raise SystemExit('Space context import anchor not found')
    app = app.replace(old_imports, new_imports, 1)

if 'function SpacePicker(' not in app:
    anchor = '\n\nfunction LoginScreen'
    if anchor not in app:
        raise SystemExit('LoginScreen anchor not found')
    app = app.replace(anchor, PICKER + anchor, 1)

app = app.replace(
    "queryKey: ['account-memberships', tokens?.accessToken ?? 'signed-out'],",
    "queryKey: ['account-memberships'],",
    1,
)

if 'const spacesQuery = useQuery({' not in app:
    membership_query_end = """    retry: false,
  });

  useEffect(() => {"""
    if membership_query_end not in app:
        raise SystemExit('Membership query end anchor not found')
    app = app.replace(membership_query_end, SPACES_QUERY, 1)

if OLD_RENDER in app:
    app = app.replace(OLD_RENDER, NEW_RENDER, 1)
elif 'const activeSpaceId = resolveActiveSpaceId(memberships, spaceId);' not in app:
    raise SystemExit('Authenticated render anchor not found')

app_path.write_text(app, encoding='utf-8')

locale_path = Path('web/src/i18n/locales/de.ts')
locale = locale_path.read_text(encoding='utf-8')
if 'pickerTitle:' not in locale:
    if OLD_LOCALE not in locale:
        raise SystemExit('Space context locale anchor not found')
    locale = locale.replace(OLD_LOCALE, NEW_LOCALE, 1)
locale_path.write_text(locale, encoding='utf-8')
