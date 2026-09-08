"""One-shot source edits for #809; removed by its generation workflow."""

from __future__ import annotations

from pathlib import Path


def replace_once(path: str, old: str, new: str) -> None:
    file = Path(path)
    text = file.read_text(encoding="utf-8")
    count = text.count(old)
    if count != 1:
        raise SystemExit(f"{path}: expected one match, found {count}: {old[:80]!r}")
    file.write_text(text.replace(old, new, 1), encoding="utf-8", newline="\n")


def write(path: str, content: str) -> None:
    file = Path(path)
    file.parent.mkdir(parents=True, exist_ok=True)
    file.write_text(content, encoding="utf-8", newline="\n")


# Backend endpoint-matrix completeness and the existing Dashboard contract test.
replace_once(
    "backend/tests/integration/test_endpoint_matrix.py",
    '    Endpoint("GET", "/api/v1/spaces/{spaceId}/dashboard"),\n',
    '    Endpoint("GET", "/api/v1/spaces/{spaceId}/dashboard"),\n'
    '    Endpoint("GET", "/api/v1/spaces/{spaceId}/dashboard/preferences"),\n'
    '    Endpoint(\n'
    '        "PUT",\n'
    '        "/api/v1/spaces/{spaceId}/dashboard/preferences/{moduleKey}",\n'
    '        body={"visible": True},\n'
    '    ),\n',
)
replace_once(
    "backend/tests/integration/test_endpoint_matrix.py",
    '            "ruleKey": "important_date_reminder",\n',
    '            "ruleKey": "important_date_reminder",\n'
    '            "moduleKey": "SHARED_STORY_SUMMARY",\n',
)
replace_once(
    "backend/tests/integration/test_dashboard.py",
    '        "recentShared",\n        "thinkingOfYouAvailableAt",\n',
    '        "recentShared",\n        "sharedStorySummary",\n        "thinkingOfYouAvailableAt",\n',
)
replace_once(
    "backend/tests/integration/test_dashboard.py",
    '    assert body["retrospective"]["id"] == str(shared_heart.id)\n\n',
    '    assert body["retrospective"]["id"] == str(shared_heart.id)\n'
    '    assert body["sharedStorySummary"] == {\n'
    '        "memories": 0,\n'
    '        "heartMoments": 1,\n'
    '        "milestones": 0,\n'
    '    }\n\n',
)

# Shared Web query key / registry edge used by Today and Settings.
write(
    "web/src/client/dashboardPreferences.ts",
    """import { DashboardModuleKey } from '../api/generated/models/DashboardModuleKey';

export const dashboardPreferencesQueryKey = (spaceId: string) =>
  ['m5-s5', 'dashboard-preferences', spaceId] as const;

export const SHARED_STORY_SUMMARY_MODULE =
  DashboardModuleKey.SHARED_STORY_SUMMARY;
""",
)

# Quiet editorial Today surface. Eligibility is intentionally presentation-only;
# private HeartMoments are already excluded by the server aggregate.
write(
    "web/src/components/SharedStorySummary.tsx",
    """import type { DashboardSharedStorySummary } from '../api/generated/models/DashboardSharedStorySummary';
import { useTranslation } from '../i18n';
import './SharedStorySummary.css';

interface SharedStorySummaryProps {
  summary: DashboardSharedStorySummary;
}

export function sharedStorySummaryIsEligible(
  summary: DashboardSharedStorySummary,
): boolean {
  const values = [summary.memories, summary.heartMoments, summary.milestones].filter(
    (value) => value > 0,
  );
  return values.length >= 2 && values.reduce((total, value) => total + value, 0) >= 5;
}

export function SharedStorySummary({ summary }: SharedStorySummaryProps) {
  const { t } = useTranslation();
  if (!sharedStorySummaryIsEligible(summary)) return null;

  const metrics = [
    {
      key: 'memories',
      label: t('m5s5.dashboard.storySummaryMemories'),
      value: summary.memories,
    },
    {
      key: 'heartMoments',
      label: t('m5s5.dashboard.storySummaryHeartMoments'),
      value: summary.heartMoments,
    },
    {
      key: 'milestones',
      label: t('m5s5.dashboard.storySummaryMilestones'),
      value: summary.milestones,
    },
  ].filter((metric) => metric.value > 0);

  return (
    <section
      className="shared-story-summary"
      aria-labelledby="shared-story-summary-heading"
    >
      <h2 id="shared-story-summary-heading">
        {t('m5s5.dashboard.storySummaryTitle')}
      </h2>
      <dl className="shared-story-summary-values">
        {metrics.map((metric) => (
          <div className="shared-story-summary-metric" key={metric.key}>
            <dd>{metric.value.toLocaleString('de-DE')}</dd>
            <dt>{metric.label}</dt>
          </div>
        ))}
      </dl>
    </section>
  );
}
""",
)
write(
    "web/src/components/SharedStorySummary.css",
    """.shared-story-summary {
  margin: var(--space-2) 0 var(--space-8);
  border-top: 1px solid var(--color-border-subtle);
  padding: var(--space-6) 0 0;
}

.shared-story-summary h2 {
  margin: 0 0 var(--space-5);
  color: var(--color-text);
  font-family: var(--font-display);
  font-size: clamp(1.45rem, 3vw, 2rem);
  font-weight: 750;
  letter-spacing: -0.02em;
}

.shared-story-summary-values {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  margin: 0;
  gap: var(--space-5) var(--space-4);
}

.shared-story-summary-metric {
  min-width: 0;
}

.shared-story-summary-metric dd,
.shared-story-summary-metric dt {
  margin: 0;
}

.shared-story-summary-metric dd {
  color: var(--color-text);
  font-family: var(--font-display);
  font-size: clamp(2rem, 11vw, 3.25rem);
  font-weight: 760;
  line-height: 1;
  letter-spacing: -0.04em;
  overflow-wrap: anywhere;
}

.shared-story-summary-metric dt {
  margin-top: var(--space-2);
  color: var(--color-text-secondary);
  font-size: 0.9rem;
  font-weight: 650;
  line-height: 1.35;
}

@media (min-width: 640px) {
  .shared-story-summary-values {
    grid-template-columns: repeat(3, minmax(0, 1fr));
  }
}
""",
)
write(
    "web/src/components/SharedStorySummary.test.tsx",
    """import { renderToStaticMarkup } from 'react-dom/server';
import m5s5 from '../i18n/locales/m5s5';
import {
  SharedStorySummary,
  sharedStorySummaryIsEligible,
} from './SharedStorySummary';

describe('SharedStorySummary', () => {
  it('uses the ratified sparse threshold', () => {
    expect(
      sharedStorySummaryIsEligible({ memories: 4, heartMoments: 1, milestones: 0 }),
    ).toBe(true);
    expect(
      sharedStorySummaryIsEligible({ memories: 3, heartMoments: 1, milestones: 0 }),
    ).toBe(false);
    expect(
      sharedStorySummaryIsEligible({ memories: 20, heartMoments: 0, milestones: 0 }),
    ).toBe(false);
  });

  it('renders one editorial surface, omits zero metrics, and preserves metric order', () => {
    const html = renderToStaticMarkup(
      <SharedStorySummary summary={{ memories: 4, heartMoments: 1, milestones: 0 }} />,
    );

    expect(html).toContain(m5s5.dashboard.storySummaryTitle);
    expect(html).toContain(m5s5.dashboard.storySummaryMemories);
    expect(html).toContain(m5s5.dashboard.storySummaryHeartMoments);
    expect(html).not.toContain(m5s5.dashboard.storySummaryMilestones);
    expect(html.indexOf(m5s5.dashboard.storySummaryMemories)).toBeLessThan(
      html.indexOf(m5s5.dashboard.storySummaryHeartMoments),
    );
    expect(html).toContain('<dl');
    expect(html).not.toContain('button');
  });
});
""",
)

# Generic preference panel: #809 registers the first module; #817 expands the
# same central contract to all Dashboard modules rather than adding new flags.
write(
    "web/src/components/DashboardSettingsPanel.tsx",
    """import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import type { DashboardApi } from '../api/generated/apis/DashboardApi';
import type { DashboardModuleKey } from '../api/generated/models/DashboardModuleKey';
import type { DashboardModulePreferenceList } from '../api/generated/models/DashboardModulePreferenceList';
import {
  dashboardPreferencesQueryKey,
  SHARED_STORY_SUMMARY_MODULE,
} from '../client/dashboardPreferences';
import { useTranslation } from '../i18n';
import { ProblemState } from './ProblemState';

export interface DashboardSettingsPanelProps {
  dashboardApi: DashboardApi;
  spaceId: string;
}

export function DashboardSettingsPanel({
  dashboardApi,
  spaceId,
}: DashboardSettingsPanelProps) {
  const { t } = useTranslation();
  const queryClient = useQueryClient();
  const queryKey = dashboardPreferencesQueryKey(spaceId);
  const preferenceQuery = useQuery({
    queryKey,
    queryFn: () => dashboardApi.listDashboardModulePreferences({ spaceId }),
    retry: false,
  });

  const mutation = useMutation({
    mutationFn: ({ moduleKey, visible }: { moduleKey: DashboardModuleKey; visible: boolean }) =>
      dashboardApi.setDashboardModulePreference({
        spaceId,
        moduleKey,
        dashboardModulePreferenceUpdate: { visible },
      }),
    onSuccess: (updated) => {
      queryClient.setQueryData<DashboardModulePreferenceList>(queryKey, (current) =>
        current
          ? {
              ...current,
              items: current.items.map((item) =>
                item.moduleKey === updated.moduleKey ? updated : item,
              ),
            }
          : current,
      );
    },
  });

  if (preferenceQuery.isLoading) {
    return <p className="form-hint">{t('profileIdentity.dashboardSettingsLoading')}</p>;
  }
  if (preferenceQuery.error) {
    return (
      <ProblemState
        error={preferenceQuery.error}
        onRetry={() => void preferenceQuery.refetch()}
      />
    );
  }

  return (
    <div className="dashboard-settings-list">
      {preferenceQuery.data?.items.map((item) => {
        const label =
          item.moduleKey === SHARED_STORY_SUMMARY_MODULE
            ? t('profileIdentity.dashboardModuleSharedStorySummary')
            : item.moduleKey;
        const pending = mutation.isPending && mutation.variables?.moduleKey === item.moduleKey;
        return (
          <label className="form-checkbox-label" key={item.moduleKey}>
            <input
              type="checkbox"
              checked={item.visible}
              disabled={pending}
              onChange={(event) =>
                mutation.mutate({
                  moduleKey: item.moduleKey,
                  visible: event.target.checked,
                })
              }
            />
            <span>
              <strong>{label}</strong>
              <small>
                {pending
                  ? t('profileIdentity.dashboardSettingsSaving')
                  : t('profileIdentity.dashboardModuleVisibleHelp')}
              </small>
            </span>
          </label>
        );
      })}
      {mutation.error ? <ProblemState error={mutation.error} /> : null}
    </div>
  );
}
""",
)
write(
    "web/src/components/DashboardSettingsPanel.test.tsx",
    """import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { renderToStaticMarkup } from 'react-dom/server';
import type { DashboardApi } from '../api/generated/apis/DashboardApi';
import { DashboardModuleKey } from '../api/generated/models/DashboardModuleKey';
import { dashboardPreferencesQueryKey } from '../client/dashboardPreferences';
import profileIdentity from '../i18n/locales/profileIdentity';
import { DashboardSettingsPanel } from './DashboardSettingsPanel';

describe('DashboardSettingsPanel', () => {
  it('renders the registered module as an accessible persisted visibility control', () => {
    const queryClient = new QueryClient({
      defaultOptions: { queries: { retry: false } },
    });
    queryClient.setQueryData(dashboardPreferencesQueryKey('space-1'), {
      items: [
        {
          moduleKey: DashboardModuleKey.SHARED_STORY_SUMMARY,
          visible: true,
        },
      ],
    });

    const html = renderToStaticMarkup(
      <QueryClientProvider client={queryClient}>
        <DashboardSettingsPanel
          dashboardApi={{} as DashboardApi}
          spaceId="space-1"
        />
      </QueryClientProvider>,
    );

    expect(html).toContain(profileIdentity.dashboardModuleSharedStorySummary);
    expect(html).toContain('type="checkbox"');
    expect(html).toContain('checked=""');
    expect(html).not.toContain('SHARED_STORY_SUMMARY');
  });
});
""",
)
write(
    "web/src/components/TodaySharedStoryIntegration.test.tsx",
    """import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { renderToStaticMarkup } from 'react-dom/server';
import { MemoryRouter } from 'react-router-dom';
import { DashboardModuleKey } from '../api/generated/models/DashboardModuleKey';
import { dashboardPreferencesQueryKey } from '../client/dashboardPreferences';
import type { M4ProductApis } from '../client/m4Product';
import m5s5 from '../i18n/locales/m5s5';
import { TodayPage } from './TodayPage';

function renderWithPreference(visible: boolean): string {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  });
  queryClient.setQueryData(['m5-s5', 'dashboard', 'space-1'], {
    space: { spaceId: 'space-1', partner: { id: 'partner-1', displayName: 'Marie' } },
    relationshipDuration: null,
    retrospective: null,
    keepsake: null,
    upcoming: [],
    recentShared: [
      {
        id: 'memory-1',
        type: 'MEMORY',
        titleOrText: 'Unser Ausflug',
        occurredOn: new Date('2026-09-01T12:00:00Z'),
      },
    ],
    sharedStorySummary: { memories: 4, heartMoments: 1, milestones: 0 },
    thinkingOfYouAvailableAt: null,
  });
  queryClient.setQueryData(dashboardPreferencesQueryKey('space-1'), {
    items: [{ moduleKey: DashboardModuleKey.SHARED_STORY_SUMMARY, visible }],
  });

  return renderToStaticMarkup(
    <QueryClientProvider client={queryClient}>
      <MemoryRouter>
        <TodayPage apis={{} as M4ProductApis} spaceId="space-1" />
      </MemoryRouter>
    </QueryClientProvider>,
  );
}

describe('Today shared Story integration', () => {
  it('places the eligible summary after the recent shared trace', () => {
    const html = renderWithPreference(true);
    expect(html).toContain(m5s5.dashboard.storySummaryTitle);
    expect(html.indexOf(m5s5.dashboard.recentTitle)).toBeLessThan(
      html.indexOf(m5s5.dashboard.storySummaryTitle),
    );
  });

  it('fails closed when the current user hides the module', () => {
    const html = renderWithPreference(false);
    expect(html).not.toContain(m5s5.dashboard.storySummaryTitle);
  });
});
""",
)

# Today integration: a preference fetch is presentation-only and fails closed;
# the normal Dashboard content remains available if that secondary request fails.
replace_once(
    "web/src/components/TodayPage.tsx",
    "import type { DashboardItemType } from '../api/generated/models/DashboardItemType';\n",
    "import type { DashboardItemType } from '../api/generated/models/DashboardItemType';\n"
    "import { DashboardModuleKey } from '../api/generated/models/DashboardModuleKey';\n",
)
replace_once(
    "web/src/components/TodayPage.tsx",
    "import { dashboardQueryKey } from '../client/dashboardQuery';\n",
    "import { dashboardPreferencesQueryKey } from '../client/dashboardPreferences';\n"
    "import { dashboardQueryKey } from '../client/dashboardQuery';\n",
)
replace_once(
    "web/src/components/TodayPage.tsx",
    "import { ProblemState } from './ProblemState';\n",
    "import { ProblemState } from './ProblemState';\n"
    "import { SharedStorySummary } from './SharedStorySummary';\n",
)
replace_once(
    "web/src/components/TodayPage.tsx",
    "  const dashboardQuery = useQuery({\n"
    "    queryKey: dashboardQueryKey(spaceId),\n"
    "    queryFn: () => apiCall(() => apis.dashboard.getDashboard({ spaceId })),\n"
    "    retry: false,\n"
    "  });\n\n",
    "  const dashboardQuery = useQuery({\n"
    "    queryKey: dashboardQueryKey(spaceId),\n"
    "    queryFn: () => apiCall(() => apis.dashboard.getDashboard({ spaceId })),\n"
    "    retry: false,\n"
    "  });\n\n"
    "  const dashboardPreferencesQuery = useQuery({\n"
    "    queryKey: dashboardPreferencesQueryKey(spaceId),\n"
    "    queryFn: () =>\n"
    "      apiCall(() =>\n"
    "        apis.dashboard.listDashboardModulePreferences({ spaceId }),\n"
    "      ),\n"
    "    retry: false,\n"
    "  });\n\n",
)
replace_once(
    "web/src/components/TodayPage.tsx",
    "  const isSparse = Boolean(\n"
    "    dashboardQuery.data &&\n"
    "      upcoming.length === 0 &&\n"
    "      recentShared.length === 0 &&\n"
    "      !retrospective &&\n"
    "      !relationshipSignalItem &&\n"
    "      !serverKeepsake,\n"
    "  );\n\n",
    "  const isSparse = Boolean(\n"
    "    dashboardQuery.data &&\n"
    "      upcoming.length === 0 &&\n"
    "      recentShared.length === 0 &&\n"
    "      !retrospective &&\n"
    "      !relationshipSignalItem &&\n"
    "      !serverKeepsake,\n"
    "  );\n"
    "  const sharedStorySummaryVisible =\n"
    "    dashboardPreferencesQuery.data?.items.some(\n"
    "      (item) =>\n"
    "        item.moduleKey === DashboardModuleKey.SHARED_STORY_SUMMARY &&\n"
    "        item.visible,\n"
    "    ) ?? false;\n\n",
)
replace_once(
    "web/src/components/TodayPage.tsx",
    "              ) : null}\n            </>\n          )}\n",
    "              ) : null}\n\n"
    "              {sharedStorySummaryVisible ? (\n"
    "                <SharedStorySummary\n"
    "                  summary={dashboardQuery.data.sharedStorySummary}\n"
    "                />\n"
    "              ) : null}\n"
    "            </>\n          )}\n",
)

# Settings gets the same generated API, not a local-storage or feature-specific flag.
replace_once(
    "web/src/components/SettingsPage.tsx",
    "import { RulesApi } from '../api/generated/apis/RulesApi';\n",
    "import { DashboardApi } from '../api/generated/apis/DashboardApi';\n"
    "import { RulesApi } from '../api/generated/apis/RulesApi';\n",
)
replace_once(
    "web/src/components/SettingsPage.tsx",
    "import { AnniversaryReminderSettings } from './AnniversaryReminderSettings';\n",
    "import { AnniversaryReminderSettings } from './AnniversaryReminderSettings';\n"
    "import { DashboardSettingsPanel } from './DashboardSettingsPanel';\n",
)
replace_once(
    "web/src/components/SettingsPage.tsx",
    "  const rulesApi = useMemo(() => new RulesApi(configuration), [configuration]);\n",
    "  const rulesApi = useMemo(() => new RulesApi(configuration), [configuration]);\n"
    "  const dashboardApi = useMemo(\n"
    "    () => new DashboardApi(configuration),\n"
    "    [configuration],\n"
    "  );\n",
)
replace_once(
    "web/src/components/SettingsPage.tsx",
    "        <section\n          id=\"settings-notifications\"\n",
    "        <section\n"
    "          id=\"settings-dashboard\"\n"
    "          className=\"form-card settings-section settings-functional-panel\"\n"
    "          aria-labelledby=\"settings-dashboard-heading\"\n"
    "        >\n"
    "          <div className=\"settings-section-head\">\n"
    "            <h2 id=\"settings-dashboard-heading\">\n"
    "              {t('profileIdentity.settingsDashboard')}\n"
    "            </h2>\n"
    "            <p className=\"settings-section-intro\">\n"
    "              {t('profileIdentity.settingsDashboardIntro')}\n"
    "            </p>\n"
    "          </div>\n"
    "          <DashboardSettingsPanel\n"
    "            dashboardApi={dashboardApi}\n"
    "            spaceId={props.spaceId}\n"
    "          />\n"
    "        </section>\n\n"
    "        <section\n          id=\"settings-notifications\"\n",
)
replace_once(
    "web/src/components/SettingsIndex.tsx",
    "        <li>\n          <a href=\"#settings-notifications\">\n",
    "        <li>\n"
    "          <a href=\"#settings-dashboard\">\n"
    "            {t('profileIdentity.settingsDashboard')}\n"
    "          </a>\n"
    "        </li>\n"
    "        <li>\n          <a href=\"#settings-notifications\">\n",
)

# Copy: no subtitle on Today; Settings may explain the control.
replace_once(
    "web/src/i18n/locales/profileIdentity.ts",
    "  settingsPageIntro:\n    'Eure Verbindung zuerst, danach Benachrichtigungen, Darstellung, Daten und sensible Aktionen.',\n",
    "  settingsPageIntro:\n"
    "    'Eure Verbindung zuerst, danach Dashboard, Benachrichtigungen, Darstellung, Daten und sensible Aktionen.',\n",
)
replace_once(
    "web/src/i18n/locales/profileIdentity.ts",
    "  settingsRelationship: 'Partner und Verbindung',\n",
    "  settingsRelationship: 'Partner und Verbindung',\n"
    "  settingsDashboard: 'Dashboard',\n"
    "  settingsDashboardIntro:\n"
    "    'Blende die Bereiche ein, die du in deiner Übersicht sehen möchtest.',\n"
    "  dashboardModuleSharedStorySummary: 'Geschichte in Zahlen',\n"
    "  dashboardModuleVisibleHelp: 'In deiner Übersicht anzeigen',\n"
    "  dashboardSettingsLoading: 'Dashboard-Einstellungen werden geladen …',\n"
    "  dashboardSettingsSaving: 'Wird gespeichert …',\n",
)
replace_once(
    "web/src/i18n/locales/m5s5.ts",
    "    recentEmpty: 'Noch keine gemeinsamen Einträge vorhanden.',\n",
    "    recentEmpty: 'Noch keine gemeinsamen Einträge vorhanden.',\n"
    "    storySummaryTitle: 'Eure Geschichte in Zahlen',\n"
    "    storySummaryMemories: 'Momente',\n"
    "    storySummaryHeartMoments: 'Herzmomente',\n"
    "    storySummaryMilestones: 'Meilensteine',\n",
)

# Existing settings index contract grows by exactly one Dashboard entry.
replace_once(
    "web/src/components/SettingsIndex.test.tsx",
    "    expect(html).toContain('href=\"#settings-notifications\"');\n",
    "    expect(html).toContain('href=\"#settings-dashboard\"');\n"
    "    expect(html).toContain(`>${profileIdentity.settingsDashboard}<`);\n\n"
    "    expect(html).toContain('href=\"#settings-notifications\"');\n",
)
replace_once(
    "web/src/components/SettingsIndex.test.tsx",
    "    expect(html.indexOf('href=\"#settings-connection\"')).toBeLessThan(\n"
    "      html.indexOf('href=\"#settings-notifications\"'),\n"
    "    );\n",
    "    expect(html.indexOf('href=\"#settings-connection\"')).toBeLessThan(\n"
    "      html.indexOf('href=\"#settings-dashboard\"'),\n"
    "    );\n"
    "    expect(html.indexOf('href=\"#settings-dashboard\"')).toBeLessThan(\n"
    "      html.indexOf('href=\"#settings-notifications\"'),\n"
    "    );\n",
)
