import { useMemo } from 'react';
import { Link } from 'react-router-dom';
import { RulesApi } from '../api/generated/apis/RulesApi';
import { SpacesApi } from '../api/generated/apis/SpacesApi';
import type { AccountView } from '../api/generated/models/AccountView';
import { Configuration } from '../api/generated/runtime';
import { isDemoModeConfigured } from '../client/demoMode';
import { MORE_NOTIFICATIONS_ROUTE } from '../client/routes';
import { useTranslation } from '../i18n';
import { AccountSettingsPanel } from './AccountSettingsPanel';
import { AnniversaryReminderSettings } from './AnniversaryReminderSettings';
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
  onSpaceLeft: () => void | Promise<void>;
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
        {/* 1. Appearance */}
        <div id="settings-appearance" className="settings-section">
          <ProfileAppearancePanel id="settings-appearance-panel" />
        </div>

        {/* 2. Notifications */}
        <section
          id="settings-notifications"
          className="form-card settings-section"
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

        {/* 3. Account-level actions. Partner invitation is reused here when authoritative state permits it. */}
        <div
          id="settings-account"
          className="settings-section settings-account-block"
        >
          <AccountSettingsPanel
            apiBaseUrl={props.apiBaseUrl}
            accessToken={props.accessToken}
            demoMode={demoMode}
          />
          <PartnerConnectionPanel {...props} />
        </div>

        {/* 4. Relationship configuration and relationship offboarding stay separate from Account deletion. */}
        <div
          id="settings-connection"
          className="settings-section settings-connection-block"
        >
          <RelationshipSettingsSection
            spacesApi={spacesApi}
            spaceId={props.spaceId}
          />
          <SpaceOffboardingPanel
            spacesApi={spacesApi}
            spaceId={props.spaceId}
            demoMode={demoMode}
            onSpaceLeft={props.onSpaceLeft}
          />
        </div>

        {/* 5. Data & Portability */}
        <div id="settings-data" className="settings-section">
          <TransferPanel
            apiBaseUrl={props.apiBaseUrl}
            accessToken={props.accessToken}
            spaceId={props.spaceId}
          />
        </div>
      </div>
    </div>
  );
}
