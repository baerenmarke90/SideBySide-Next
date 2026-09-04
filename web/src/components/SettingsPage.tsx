import { Link } from 'react-router-dom';
import type { AccountView } from '../api/generated/models/AccountView';
import { PRIVATE_AREA_ROOT_PATH } from '../client/privateArea';
import { MORE_NOTIFICATIONS_ROUTE } from '../client/routes';
import { useTranslation } from '../i18n';
import { PageHeader } from './PageHeader';
import { PartnerConnectionPanel } from './PartnerConnectionPanel';
import { PartnerIdentityPanel } from './PartnerIdentityPanel';
import { ProfileAppearancePanel } from './ProfileAppearancePanel';
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

  return (
    <div className="page settings-page">
      <PageHeader
        eyebrow={t('navigation.settings')}
        title={t('navigation.settings')}
        description={t('profileIdentity.settingsPageIntro')}
      />

      <SettingsIndex />

      <div className="settings-sections">
        {/* 1. DARSTELLUNG */}
        <div id="settings-appearance" className="settings-section">
          <ProfileAppearancePanel id="settings-appearance-panel" />
        </div>

        {/* 2. BENACHRICHTIGUNGEN */}
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

        {/* 3. VERBINDUNG / GEMEINSAMER BEREICH */}
        <div
          id="settings-connection"
          className="settings-section settings-connection-block"
        >
          <PartnerIdentityPanel {...props} />
          <PartnerConnectionPanel {...props} />
        </div>

        {/* 4. PRIVATSPHÄRE / MEIN BEREICH */}
        <section
          id="settings-privacy"
          className="form-card settings-section"
          aria-labelledby="settings-privacy-heading"
        >
          <div className="settings-section-head">
            <p className="eyebrow">{t('privateArea.privacyLabel')}</p>
            <h2 id="settings-privacy-heading">
              {t('privateArea.entry.title')}
            </h2>
            <p>{t('privateArea.entry.body')}</p>
            <p className="field-help">{t('privateArea.entry.privacy')}</p>
          </div>
          <div className="form-actions">
            <Link
              className="button-link secondary-link"
              to={PRIVATE_AREA_ROOT_PATH}
            >
              {t('privateArea.entry.action')}
            </Link>
          </div>
        </section>

        {/* 5. DATEN & PORTABILITÄT */}
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
