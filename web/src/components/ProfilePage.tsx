import { useMemo, useState } from 'react';
import { SpacesApi } from '../api/generated/apis/SpacesApi';
import type { AccountView } from '../api/generated/models/AccountView';
import { Configuration } from '../api/generated/runtime';
import { useTranslation } from '../i18n';
import { PageHeader } from './PageHeader';
import { ProfileIdentityPanel } from './ProfileIdentityPanel';
import {
  ProfilePreferencesSection,
  RelationshipProfileSection,
} from './ProfilePageBase';
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

      {/* 3. BEZIEHUNG & GEMEINSAME ZEIT */}
      <RelationshipProfileSection
        spacesApi={spacesApi}
        spaceId={props.spaceId}
      />
    </div>
  );
}
