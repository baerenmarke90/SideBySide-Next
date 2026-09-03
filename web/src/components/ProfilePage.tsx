import { useMemo, useState } from 'react';
import { Link } from 'react-router-dom';
import { SpacesApi } from '../api/generated/apis/SpacesApi';
import type { AccountView } from '../api/generated/models/AccountView';
import { Configuration } from '../api/generated/runtime';
import { PRIVATE_AREA_ROOT_PATH } from '../client/privateArea';
import { useTranslation } from '../i18n';
import { PageHeader } from './PageHeader';
import { PartnerConnectionPanel } from './PartnerConnectionPanel';
import { PartnerIdentityPanel } from './PartnerIdentityPanel';
import { ProfileAppearancePanel } from './ProfileAppearancePanel';
import { ProfileIdentityPanel } from './ProfileIdentityPanel';
import {
  ProfilePreferencesSection,
  RelationshipProfileSection,
} from './ProfilePageBase';
import { ProfileSettingsIndex } from './ProfileSettingsIndex';
import { TransferPanel } from './TransferPanel';
import './ProfilePage.css';

export interface ProfilePageProps {
  apiBaseUrl: string;
  accessToken: string;
  account: AccountView;
  spaceId: string;
}

export function ProfilePage(props: ProfilePageProps) {
  const { t } = useTranslation();
  const [displayName, setDisplayName] = useState(props.account.displayName);
  const currentAccount = { ...props.account, displayName };
  const currentProps = { ...props, account: currentAccount };

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
    <div className="page profile-page">
      <PageHeader
        eyebrow={t('profiles.eyebrow')}
        title={t('profiles.title')}
        description={t('profiles.intro')}
      />

      {/* 1. PROFIL = DIE PERSON */}
      <ProfileIdentityPanel
        {...currentProps}
        onDisplayNameChanged={(nextDisplayName) => {
          props.account.displayName = nextDisplayName;
          setDisplayName(nextDisplayName);
        }}
      />

      {/* 2. MEINE VORLIEBEN (Categorized Chips, [+ Vorliebe] Modal Dialog) */}
      <ProfilePreferencesSection {...currentProps} />

      {/* 3. EINSTELLUNGEN = KONFIGURATION (Sekundärer Bereich) */}
      <hr className="profile-settings-separator" />

      <section
        className="profile-settings-section"
        aria-labelledby="profile-settings-heading"
      >
        <div className="profile-settings-header-group">
          <p className="eyebrow">{t('profileIdentity.settingsTitle')}</p>
          <h2 id="profile-settings-heading">
            {t('profileIdentity.settingsTitle')}
          </h2>
          <p className="profile-section-intro">
            {t('profileIdentity.settingsIntro')}
          </p>
        </div>

        <ProfileSettingsIndex />

        <div id="profile-appearance-settings">
          <ProfileAppearancePanel />
        </div>

        <div
          id="profile-partner-settings"
          className="profile-partner-settings-block"
        >
          <RelationshipProfileSection
            spacesApi={spacesApi}
            spaceId={props.spaceId}
          />
          <PartnerIdentityPanel {...currentProps} />
          <PartnerConnectionPanel {...currentProps} />
        </div>

        <section
          className="form-card"
          id="profile-private-settings"
          aria-labelledby="private-area-entry-title"
        >
          <p className="eyebrow">{t('privateArea.privacyLabel')}</p>
          <h2 id="private-area-entry-title">{t('privateArea.entry.title')}</h2>
          <p>{t('privateArea.entry.body')}</p>
          <p className="field-help">{t('privateArea.entry.privacy')}</p>
          <div className="form-actions">
            <Link
              className="button-link secondary-link"
              to={PRIVATE_AREA_ROOT_PATH}
            >
              {t('privateArea.entry.action')}
            </Link>
          </div>
        </section>

        <div id="profile-data-settings">
          <TransferPanel
            apiBaseUrl={props.apiBaseUrl}
            accessToken={props.accessToken}
            spaceId={props.spaceId}
          />
        </div>
      </section>
    </div>
  );
}
