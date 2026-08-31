import { useState } from 'react';
import { Link } from 'react-router-dom';
import type { AccountView } from '../api/generated/models/AccountView';
import { PRIVATE_AREA_ROOT_PATH } from '../client/privateArea';
import { useTranslation } from '../i18n';
import { PartnerConnectionPanel } from './PartnerConnectionPanel';
import { ProfileIdentityPanel } from './ProfileIdentityPanel';
import { ProfilePage as ProfilePageBase } from './ProfilePageBase';
import { TransferPanel } from './TransferPanel';

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

  return (
    <>
      <ProfilePageBase {...currentProps} />
      <ProfileIdentityPanel
        {...currentProps}
        onDisplayNameChanged={(nextDisplayName) => {
          // AccountView is the current in-memory session projection. Updating the
          // existing object keeps subsequent routes in this session from showing
          // the pre-edit name; Space/Profile queries are invalidated separately by
          // ProfileIdentityPanel and remain server-authoritative.
          props.account.displayName = nextDisplayName;
          setDisplayName(nextDisplayName);
        }}
      />
      <PartnerConnectionPanel {...currentProps} />
      <TransferPanel
        apiBaseUrl={props.apiBaseUrl}
        accessToken={props.accessToken}
        spaceId={props.spaceId}
      />
      <section className="form-card" aria-labelledby="private-area-entry-title">
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
    </>
  );
}
