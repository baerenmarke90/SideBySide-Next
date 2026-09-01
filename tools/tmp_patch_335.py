from pathlib import Path


def replace_once(path: str, old: str, new: str) -> None:
    target = Path(path)
    text = target.read_text(encoding="utf-8")
    count = text.count(old)
    if count != 1:
        raise SystemExit(
            f"Expected exactly one match in {path}, found {count}: {old[:80]!r}"
        )
    target.write_text(text.replace(old, new, 1), encoding="utf-8")


page = "web/src/components/ServerAdminPage.tsx"
replace_once(
    page,
    "import { useQuery } from '@tanstack/react-query';\n",
    "import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';\n",
)
replace_once(
    page,
    "import type { ServerAdminOverview } from '../api/generated/models/ServerAdminOverview';\n",
    "import type { ServerAdminActivityItem } from '../api/generated/models/ServerAdminActivityItem';\nimport type { ServerAdminOverview } from '../api/generated/models/ServerAdminOverview';\nimport type { ServerAdminSettings } from '../api/generated/models/ServerAdminSettings';\n",
)
replace_once(
    page,
    "function OverviewContent({ overview }: { overview: ServerAdminOverview }) {\n",
    "export function ServerAdminSettingsPanel({\n  settings,\n  registrationPending,\n  maintenancePending,\n  mutationError,\n  onRegistrationChange,\n  onMaintenanceChange,\n}: {\n  settings: ServerAdminSettings;\n  registrationPending: boolean;\n  maintenancePending: boolean;\n  mutationError: Error | null;\n  onRegistrationChange: (enabled: boolean) => void;\n  onMaintenanceChange: (enabled: boolean) => void;\n}) {\n  const { t } = useTranslation();\n  return (\n    <section\n      className=\"server-admin-panel server-admin-panel-wide\"\n      aria-labelledby=\"server-settings-title\"\n    >\n      <h2 id=\"server-settings-title\">{t('serverAdmin.settings.title')}</h2>\n      <p className=\"server-admin-muted\">{t('serverAdmin.settings.body')}</p>\n      <div className=\"server-admin-setting-list\">\n        <div className=\"server-admin-setting-row\">\n          <div>\n            <strong>{t('serverAdmin.settings.registrationTitle')}</strong>\n            <p id=\"server-registration-help\" className=\"server-admin-muted\">\n              {t('serverAdmin.settings.registrationBody')}\n            </p>\n          </div>\n          <button\n            type=\"button\"\n            className=\"server-admin-toggle\"\n            aria-pressed={settings.registrationEnabled}\n            aria-describedby=\"server-registration-help\"\n            disabled={registrationPending}\n            onClick={() => onRegistrationChange(!settings.registrationEnabled)}\n          >\n            {t(\n              settings.registrationEnabled\n                ? 'serverAdmin.settings.enabled'\n                : 'serverAdmin.settings.disabled',\n            )}\n          </button>\n        </div>\n\n        <div className=\"server-admin-setting-row\">\n          <div>\n            <strong>{t('serverAdmin.settings.maintenanceTitle')}</strong>\n            <p id=\"server-maintenance-help\" className=\"server-admin-muted\">\n              {t('serverAdmin.settings.maintenanceBody')}\n            </p>\n          </div>\n          <button\n            type=\"button\"\n            className=\"server-admin-toggle\"\n            aria-pressed={settings.maintenanceMode}\n            aria-describedby=\"server-maintenance-help\"\n            disabled={maintenancePending}\n            onClick={() => onMaintenanceChange(!settings.maintenanceMode)}\n          >\n            {t(\n              settings.maintenanceMode\n                ? 'serverAdmin.settings.enabled'\n                : 'serverAdmin.settings.disabled',\n            )}\n          </button>\n        </div>\n      </div>\n\n      <div className=\"server-admin-effective-state\" role=\"status\">\n        <span>{t('serverAdmin.settings.effectiveRegistration')}</span>\n        <strong>\n          {t(\n            settings.effectiveRegistrationEnabled\n              ? 'serverAdmin.settings.available'\n              : 'serverAdmin.settings.unavailable',\n          )}\n        </strong>\n      </div>\n      <p className=\"server-admin-muted\">\n        {settings.maintenanceMode\n          ? t('serverAdmin.settings.effectiveMaintenanceHint')\n          : t('serverAdmin.settings.effectivePolicyHint')}\n      </p>\n      {mutationError ? (\n        <p className=\"status status-error\" role=\"alert\">\n          {t('serverAdmin.settings.updateError')}\n        </p>\n      ) : null}\n    </section>\n  );\n}\n\nfunction activitySettingLabel(setting: string, t: (key: string) => string): string {\n  switch (setting) {\n    case 'registration_enabled':\n      return t('serverAdmin.activity.registration');\n    case 'maintenance_mode':\n      return t('serverAdmin.activity.maintenance');\n    default:\n      return t('serverAdmin.activity.unknown');\n  }\n}\n\nfunction booleanStateLabel(value: boolean, t: (key: string) => string): string {\n  return t(\n    value ? 'serverAdmin.activity.enabled' : 'serverAdmin.activity.disabled',\n  );\n}\n\nexport function ServerAdminActivityPanel({\n  activity,\n}: {\n  activity: ServerAdminActivityItem[];\n}) {\n  const { t } = useTranslation();\n  return (\n    <section\n      className=\"server-admin-panel server-admin-panel-wide\"\n      aria-labelledby=\"server-activity-title\"\n    >\n      <h2 id=\"server-activity-title\">{t('serverAdmin.activity.title')}</h2>\n      <p className=\"server-admin-muted\">{t('serverAdmin.activity.body')}</p>\n      {activity.length === 0 ? (\n        <p className=\"server-admin-muted\">{t('serverAdmin.activity.empty')}</p>\n      ) : (\n        <div className=\"server-admin-table-scroll\">\n          <table className=\"server-admin-table\">\n            <thead>\n              <tr>\n                <th scope=\"col\">{t('serverAdmin.activity.setting')}</th>\n                <th scope=\"col\">{t('serverAdmin.activity.change')}</th>\n                <th scope=\"col\">{t('serverAdmin.activity.changedAt')}</th>\n              </tr>\n            </thead>\n            <tbody>\n              {activity.map((item) => (\n                <tr key={item.id}>\n                  <td>{activitySettingLabel(item.setting, t)}</td>\n                  <td>\n                    {booleanStateLabel(item.previousValue, t)} →{' '}\n                    {booleanStateLabel(item.newValue, t)}\n                  </td>\n                  <td>{formatDate(item.createdAt) ?? '–'}</td>\n                </tr>\n              ))}\n            </tbody>\n          </table>\n        </div>\n      )}\n    </section>\n  );\n}\n\nfunction OverviewContent({ overview }: { overview: ServerAdminOverview }) {\n",
)
replace_once(
    page,
    "  const { t } = useTranslation();\n  const apis = useMemo(\n",
    "  const { t } = useTranslation();\n  const queryClient = useQueryClient();\n  const apis = useMemo(\n",
)
replace_once(
    page,
    "  const overviewQuery = useQuery({\n    queryKey: ['server-admin', 'overview'],\n    queryFn: () =>\n      apis.serverAdmin.getServerAdminOverviewApiV1ServerAdminOverviewGet(),\n    retry: false,\n  });\n\n  function logout() {\n",
    "  const overviewQuery = useQuery({\n    queryKey: ['server-admin', 'overview'],\n    queryFn: () =>\n      apis.serverAdmin.getServerAdminOverviewApiV1ServerAdminOverviewGet(),\n    retry: false,\n  });\n  const settingsQuery = useQuery({\n    queryKey: ['server-admin', 'settings'],\n    queryFn: () =>\n      apis.serverAdmin.getServerAdminSettingsApiV1ServerAdminSettingsGet(),\n    retry: false,\n  });\n  const activityQuery = useQuery({\n    queryKey: ['server-admin', 'activity'],\n    queryFn: () =>\n      apis.serverAdmin.getServerAdminActivityApiV1ServerAdminActivityGet(),\n    retry: false,\n  });\n  const registrationMutation = useMutation({\n    mutationFn: (enabled: boolean) =>\n      apis.serverAdmin.updateRegistrationSettingApiV1ServerAdminSettingsRegistrationPut(\n        { serverAdminSettingUpdate: { enabled } },\n      ),\n    onSuccess: (settings) => {\n      queryClient.setQueryData(['server-admin', 'settings'], settings);\n      void queryClient.invalidateQueries({ queryKey: ['server-admin', 'activity'] });\n    },\n  });\n  const maintenanceMutation = useMutation({\n    mutationFn: (enabled: boolean) =>\n      apis.serverAdmin.updateMaintenanceSettingApiV1ServerAdminSettingsMaintenancePut(\n        { serverAdminSettingUpdate: { enabled } },\n      ),\n    onSuccess: (settings) => {\n      queryClient.setQueryData(['server-admin', 'settings'], settings);\n      void queryClient.invalidateQueries({ queryKey: ['server-admin', 'activity'] });\n    },\n  });\n  const refreshing =\n    overviewQuery.isFetching || settingsQuery.isFetching || activityQuery.isFetching;\n  const mutationError = registrationMutation.error ?? maintenanceMutation.error;\n\n  function refreshAll() {\n    void overviewQuery.refetch();\n    void settingsQuery.refetch();\n    void activityQuery.refetch();\n  }\n\n  function updateMaintenance(enabled: boolean) {\n    if (\n      enabled &&\n      !window.confirm(t('serverAdmin.settings.maintenanceConfirmEnable'))\n    ) {\n      return;\n    }\n    maintenanceMutation.mutate(enabled);\n  }\n\n  function logout() {\n",
)
replace_once(
    page,
    "            onClick={() => void overviewQuery.refetch()}\n            disabled={overviewQuery.isFetching}\n",
    "            onClick={refreshAll}\n            disabled={refreshing}\n",
)
replace_once(
    page,
    "        {overviewQuery.isPending ? (\n          <UiState\n            kind=\"loading\"\n            title={t('serverAdmin.states.loadingTitle')}\n            body={t('serverAdmin.states.loadingBody')}\n          />\n        ) : overviewQuery.error ? (\n          <UiState\n            kind=\"error\"\n            title={t('serverAdmin.states.errorTitle')}\n            body={t('serverAdmin.states.errorBody')}\n            action={\n              <button\n                type=\"button\"\n                onClick={() => void overviewQuery.refetch()}\n              >\n                {t('serverAdmin.refresh')}\n              </button>\n            }\n          />\n        ) : overviewQuery.data ? (\n          <div className=\"server-admin-grid\">\n            <OverviewContent overview={overviewQuery.data} />\n          </div>\n        ) : null}\n",
    "        <div className=\"server-admin-grid\">\n          {settingsQuery.isPending ? (\n            <section className=\"server-admin-panel server-admin-panel-wide\">\n              <UiState\n                kind=\"loading\"\n                title={t('serverAdmin.settings.loadingTitle')}\n                body={t('serverAdmin.settings.loadingBody')}\n              />\n            </section>\n          ) : settingsQuery.error ? (\n            <section className=\"server-admin-panel server-admin-panel-wide\">\n              <UiState\n                kind=\"error\"\n                title={t('serverAdmin.settings.errorTitle')}\n                body={t('serverAdmin.settings.errorBody')}\n                action={\n                  <button type=\"button\" onClick={() => void settingsQuery.refetch()}>\n                    {t('serverAdmin.refresh')}\n                  </button>\n                }\n              />\n            </section>\n          ) : settingsQuery.data ? (\n            <ServerAdminSettingsPanel\n              settings={settingsQuery.data}\n              registrationPending={registrationMutation.isPending}\n              maintenancePending={maintenanceMutation.isPending}\n              mutationError={mutationError}\n              onRegistrationChange={(enabled) => registrationMutation.mutate(enabled)}\n              onMaintenanceChange={updateMaintenance}\n            />\n          ) : null}\n\n          {overviewQuery.isPending ? (\n            <section className=\"server-admin-panel server-admin-panel-wide\">\n              <UiState\n                kind=\"loading\"\n                title={t('serverAdmin.states.loadingTitle')}\n                body={t('serverAdmin.states.loadingBody')}\n              />\n            </section>\n          ) : overviewQuery.error ? (\n            <section className=\"server-admin-panel server-admin-panel-wide\">\n              <UiState\n                kind=\"error\"\n                title={t('serverAdmin.states.errorTitle')}\n                body={t('serverAdmin.states.errorBody')}\n                action={\n                  <button type=\"button\" onClick={() => void overviewQuery.refetch()}>\n                    {t('serverAdmin.refresh')}\n                  </button>\n                }\n              />\n            </section>\n          ) : overviewQuery.data ? (\n            <OverviewContent overview={overviewQuery.data} />\n          ) : null}\n\n          {activityQuery.isPending ? (\n            <section className=\"server-admin-panel server-admin-panel-wide\">\n              <UiState\n                kind=\"loading\"\n                title={t('serverAdmin.activity.loadingTitle')}\n                body={t('serverAdmin.activity.loadingBody')}\n              />\n            </section>\n          ) : activityQuery.error ? (\n            <section className=\"server-admin-panel server-admin-panel-wide\">\n              <UiState\n                kind=\"error\"\n                title={t('serverAdmin.activity.errorTitle')}\n                body={t('serverAdmin.activity.errorBody')}\n                action={\n                  <button type=\"button\" onClick={() => void activityQuery.refetch()}>\n                    {t('serverAdmin.refresh')}\n                  </button>\n                }\n              />\n            </section>\n          ) : activityQuery.data ? (\n            <ServerAdminActivityPanel activity={activityQuery.data} />\n          ) : null}\n        </div>\n",
)

replace_once(
    "web/src/i18n/locales/serverAdmin.ts",
    "  configuration: {\n",
    "  settings: {\n    title: 'Anwendungssteuerung',\n    body:\n      'Diese Einstellungen werden in SideBySide gespeichert und gelten sofort für diese Installation.',\n    loadingTitle: 'Anwendungssteuerung wird geladen',\n    loadingBody: 'Registrierungs- und Wartungsstatus werden abgefragt.',\n    errorTitle: 'Anwendungssteuerung nicht verfügbar',\n    errorBody: 'Die aktuellen Einstellungen konnten nicht geladen werden.',\n    registrationTitle: 'Neue Registrierungen',\n    registrationBody:\n      'Steuert, ob über gültige Einladungen neue Konten angelegt werden dürfen. Bestehende Konten bleiben davon unberührt.',\n    maintenanceTitle: 'Wartungsmodus',\n    maintenanceBody:\n      'Sperrt normale Produktzugriffe. Anmeldung, Recovery, Health und Serververwaltung bleiben erreichbar.',\n    maintenanceConfirmEnable:\n      'Wartungsmodus wirklich aktivieren? Normale Produktzugriffe werden bis zum Deaktivieren gesperrt.',\n    effectiveRegistration: 'Effektive Registrierung',\n    effectiveMaintenanceHint:\n      'Registrierung ist während des Wartungsmodus unabhängig vom gespeicherten Registrierungsschalter nicht verfügbar.',\n    effectivePolicyHint:\n      'Ohne Wartungsmodus entspricht die effektive Registrierung dem gespeicherten Registrierungsschalter.',\n    enabled: 'Aktiv',\n    disabled: 'Inaktiv',\n    available: 'Verfügbar',\n    unavailable: 'Nicht verfügbar',\n    updateError: 'Die Einstellung konnte nicht gespeichert werden.',\n  },\n  activity: {\n    title: 'Administrative Änderungen',\n    body:\n      'Letzte Änderungen an Registrierungs- und Wartungseinstellungen. Private Inhalte werden hier nicht protokolliert.',\n    loadingTitle: 'Änderungsverlauf wird geladen',\n    loadingBody: 'Die letzten administrativen Änderungen werden abgefragt.',\n    errorTitle: 'Änderungsverlauf nicht verfügbar',\n    errorBody: 'Die administrativen Änderungen konnten nicht geladen werden.',\n    empty: 'Noch keine administrativen Einstellungsänderungen vorhanden.',\n    setting: 'Einstellung',\n    change: 'Änderung',\n    changedAt: 'Geändert',\n    registration: 'Neue Registrierungen',\n    maintenance: 'Wartungsmodus',\n    unknown: 'Unbekannte Einstellung',\n    enabled: 'Aktiv',\n    disabled: 'Inaktiv',\n  },\n  configuration: {\n",
)

css = "web/src/components/ServerAdminPage.css"
replace_once(
    css,
    ".server-admin-panel {\n",
    ".server-admin-panel-wide {\n  grid-column: 1 / -1;\n}\n\n.server-admin-panel {\n",
)
replace_once(
    css,
    ".server-admin-status-list {\n",
    ".server-admin-setting-list {\n  display: grid;\n  gap: var(--space-3);\n  margin: var(--space-4) 0;\n}\n\n.server-admin-setting-row {\n  display: flex;\n  align-items: center;\n  justify-content: space-between;\n  gap: var(--space-5);\n  padding: var(--space-4);\n  border: 1px solid var(--color-border-subtle);\n  border-radius: var(--radius-medium);\n  background: var(--color-surface-subtle);\n}\n\n.server-admin-setting-row p {\n  margin: var(--space-1) 0 0;\n}\n\n.server-admin-toggle {\n  min-width: 7rem;\n}\n\n.server-admin-toggle[aria-pressed='true'] {\n  border-color: var(--color-shared);\n}\n\n.server-admin-effective-state {\n  display: flex;\n  align-items: center;\n  justify-content: space-between;\n  gap: var(--space-4);\n  padding: var(--space-3) var(--space-4);\n  border-radius: var(--radius-medium);\n  background: var(--color-surface-subtle);\n}\n\n.server-admin-status-list {\n",
)
replace_once(
    css,
    "  .server-admin-status-row {\n    align-items: flex-start;\n    flex-direction: column;\n  }\n",
    "  .server-admin-status-row,\n  .server-admin-setting-row,\n  .server-admin-effective-state {\n    align-items: flex-start;\n    flex-direction: column;\n  }\n\n  .server-admin-toggle {\n    width: 100%;\n  }\n",
)

Path("web/src/components/ServerAdminControls.test.tsx").write_text(
    """import { renderToStaticMarkup } from 'react-dom/server';
import {
  ServerAdminActivityPanel,
  ServerAdminSettingsPanel,
} from './ServerAdminPage';

describe('ServerAdmin controls', () => {
  it('shows stored and effective registration state separately', () => {
    const html = renderToStaticMarkup(
      <ServerAdminSettingsPanel
        settings={{
          effectiveRegistrationEnabled: false,
          maintenanceMode: true,
          registrationEnabled: true,
          version: 3,
        }}
        registrationPending={false}
        maintenancePending={false}
        mutationError={null}
        onRegistrationChange={() => undefined}
        onMaintenanceChange={() => undefined}
      />,
    );

    expect(html).toContain('Neue Registrierungen');
    expect(html).toContain('Wartungsmodus');
    expect(html).toContain('Effektive Registrierung');
    expect(html).toContain('Nicht verfügbar');
    expect(html).toContain('aria-pressed="true"');
  });

  it('renders privacy-safe audit changes without exposing actor ids', () => {
    const actorId = '00000000-0000-0000-0000-000000000099';
    const html = renderToStaticMarkup(
      <ServerAdminActivityPanel
        activity={[
          {
            actorId,
            createdAt: new Date('2026-09-01T12:00:00Z'),
            id: '00000000-0000-0000-0000-000000000100',
            newValue: true,
            previousValue: false,
            setting: 'maintenance_mode',
          },
        ]}
      />,
    );

    expect(html).toContain('Wartungsmodus');
    expect(html).toContain('Inaktiv');
    expect(html).toContain('Aktiv');
    expect(html).not.toContain(actorId);
  });
});
""",
    encoding="utf-8",
)
