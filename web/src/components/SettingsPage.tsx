import { useMemo } from 'react';
import { Link } from 'react-router-dom';
import { SpacesApi } from '../api/generated/apis/SpacesApi';
import type { AccountView } from '../api/generated/models/AccountView';
import { Configuration } from '../api/generated/runtime';
import { MORE_NOTIFICATIONS_ROUTE } from '../client/routes';
import { useTranslation } from '../i18n';
import { PageHeader } from './PageHeader';
import { PartnerConnectionPanel } from './PartnerConnectionPanel';
import { ProfileAppearancePanel } from './ProfileAppearancePanel';
import { RelationshipSettingsSection } from './ProfilePageBase';
import { SettingsIndex } from './SettingsIndex';
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
          <div className="form-actions">
            <Link
              className="button-link secondary-link"
              to={MORE_NOTIFICATIONS_ROUTE}
            >
              {t('profileIdentity.settingsNotificationsAction')}
            </Link>
          </div>
        </section>

        {/* 3. Connection & Relationship Configuration */}
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

        {/* 4. Data & Portability */}
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
