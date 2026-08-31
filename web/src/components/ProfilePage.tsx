import { Link } from 'react-router-dom';
import type { AccountView } from '../api/generated/models/AccountView';
import { PRIVATE_AREA_ROOT_PATH } from '../client/privateArea';
import { useTranslation } from '../i18n';
import { PartnerConnectionPanel } from './PartnerConnectionPanel';
import { ProfilePage as ProfilePageBase } from './ProfilePageBase';

export interface ProfilePageProps {
  apiBaseUrl: string;
  accessToken: string;
  account: AccountView;
  spaceId: string;
}

export function ProfilePage(props: ProfilePageProps) {
  const { t } = useTranslation();
  return (
    <>
      <ProfilePageBase {...props} />
      <PartnerConnectionPanel {...props} />
      <section className="form-card" aria-labelledby="private-area-entry-title">
        <p className="eyebrow">{t('privateArea.privacyLabel')}</p>
        <h2 id="private-area-entry-title">{t('privateArea.entry.title')}</h2>
        <p>{t('privateArea.entry.body')}</p>
        <p className="field-help">{t('privateArea.entry.privacy')}</p>
        <div className="form-actions">
          <Link className="button-link secondary-link" to={PRIVATE_AREA_ROOT_PATH}>
            {t('privateArea.entry.action')}
          </Link>
        </div>
      </section>
    </>
  );
}
