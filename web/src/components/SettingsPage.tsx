import { useMemo } from 'react';
import { Link } from 'react-router-dom';
import { DashboardApi } from '../api/generated/apis/DashboardApi';
import { RulesApi } from '../api/generated/apis/RulesApi';
import { SpacesApi } from '../api/generated/apis/SpacesApi';
import type { AccountView } from '../api/generated/models/AccountView';
import { Configuration } from '../api/generated/runtime';
import { isDemoModeConfigured } from '../client/demoMode';
import { MORE_NOTIFICATIONS_ROUTE } from '../client/routes';
import { useTranslation } from '../i18n';
import { AccountSettingsPanel } from './AccountSettingsPanel';
import { AnniversaryReminderSettings } from './AnniversaryReminderSettings';
import { DashboardSettingsPanel } from './DashboardSettingsPanel';
import { PageHeader } from './PageHeader';
import { PartnerConnectionPanel } from './PartnerConnectionPanel';
import { ProfileAppearancePanel } from './ProfileAppearancePanel';
import { RelationshipSettingsSection } from './ProfilePageBase';
import { SettingsIndex } from './SettingsIndex';
import { SpaceOffboardingPanel } from './SpaceOffboardingPanel';
import { TransferPanel } from './TransferPanel';
import './SettingsPage.css';

export interface SettingsPageProps {
  apiBaseUrl: string;
  accessToken: string;
  account: AccountView;
  spaceId: string;
}

export function SettingsPage(props: SettingsPageProps) {
  const { t } = useTranslation();

  const configuration = useMemo(
    () =>
      new Configuration({
        basePath: props.apiBaseUrl,
        headers: { Authorization: `Bearer ${props.accessToken}` },
      }),
    [props.accessToken, props.apiBaseUrl],
  );
  const spacesApi = useMemo(
    () => new SpacesApi(configuration),
    [configuration],
  );
  const rulesApi = useMemo(() => new RulesApi(configuration), [configuration]);
  const dashboardApi = useMemo(
    () => new DashboardApi(configuration),
    [configuration],
  );
  const demoMode = isDemoModeConfigured();

  return (
    <div className="page settings-page">
      <PageHeader
        eyebrow={t('navigation.settings')}
        title={t('navigation.settings')}
        description={t('profileIdentity.settingsPageIntro')}
      />

      <SettingsIndex />

      <div className="settings-sections">
        {/* Relationship context comes before device and account configuration. */}
        <div
          id="settings-connection"
          className="settings-section settings-connection-block"
        >
          <RelationshipSettingsSection
            spacesApi={spacesApi}
            spaceId={props.spaceId}
          />
          <PartnerConnectionPanel {...props} />
        </div>

        <section
          id="settings-notifications"
          className="form-card settings-section settings-functional-panel"
          aria-labelledby="settings-notifications-heading"
        >
          <div className="settings-section-head">
            <h2 id="settings-notifications-heading">
              {t('profileIdentity.settingsNotifications')}
            </h2>
            <p className="settings-section-intro">
              {t('profileIdentity.settingsNotificationsIntro')}
            </p>
          </div>
          <AnniversaryReminderSettings
            rulesApi={rulesApi}
            spaceId={props.spaceId}
          />
          <div className="form-actions settings-notification-inbox-action">
            <Link
              className="button-link secondary-link"
              to={MORE_NOTIFICATIONS_ROUTE}
            >
              {t('profileIdentity.settingsNotificationsAction')}
            </Link>
          </div>
        </section>

        <DashboardSettingsPanel
          dashboardApi={dashboardApi}
          accountId={props.account.id}
          spaceId={props.spaceId}
        />

        <div
          id="settings-appearance"
          className="settings-section settings-appearance-block"
        >
          <ProfileAppearancePanel id="settings-appearance-panel" />
        </div>

        <div
          id="settings-data"
          className="settings-section settings-data-block"
        >
          <TransferPanel
            apiBaseUrl={props.apiBaseUrl}
            accessToken={props.accessToken}
            spaceId={props.spaceId}
          />
        </div>

        {/* Space exit and Account deletion remain distinct flows inside one clearly labelled sensitive zone. */}
        <section
          id="settings-account"
          className="settings-section settings-sensitive-zone"
          aria-labelledby="settings-sensitive-heading"
        >
          <div className="settings-sensitive-head">
            <p className="eyebrow">
              {t('profileIdentity.settingsSensitiveEyebrow')}
            </p>
            <h2 id="settings-sensitive-heading">
              {t('profileIdentity.settingsSensitiveTitle')}
            </h2>
            <p>{t('profileIdentity.settingsSensitiveIntro')}</p>
          </div>
          <div className="settings-sensitive-grid">
            <SpaceOffboardingPanel
              spacesApi={spacesApi}
              spaceId={props.spaceId}
              demoMode={demoMode}
            />
            <AccountSettingsPanel
              apiBaseUrl={props.apiBaseUrl}
              accessToken={props.accessToken}
              demoMode={demoMode}
            />
          </div>
        </section>
      </div>
    </div>
  );
}
