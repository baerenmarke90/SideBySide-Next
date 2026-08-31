import { Link } from 'react-router-dom';
import { PRIVATE_AREA_ROOT_PATH } from '../client/privateArea';
import { MORE_NOTIFICATIONS_ROUTE } from '../client/routes';
import { useTranslation } from '../i18n';
import './ProfileSettingsIndex.css';

export function ProfileSettingsIndex() {
  const { t } = useTranslation();

  return (
    <nav
      className="form-card profile-settings-index"
      aria-labelledby="profile-settings-title"
    >
      <div>
        <h2 id="profile-settings-title">
          {t('profileIdentity.settingsTitle')}
        </h2>
        <p>{t('profileIdentity.settingsIntro')}</p>
      </div>
      <ul className="profile-settings-links">
        <li>
          <a href="#profile-identity-settings">
            {t('profileIdentity.settingsIdentity')}
          </a>
        </li>
        <li>
          <a href="#profile-partner-settings">
            {t('profileIdentity.settingsRelationship')}
          </a>
        </li>
        <li>
          <Link to={MORE_NOTIFICATIONS_ROUTE}>
            {t('profileIdentity.settingsNotifications')}
          </Link>
        </li>
        <li>
          <Link to={PRIVATE_AREA_ROOT_PATH}>
            {t('profileIdentity.settingsPrivacy')}
          </Link>
        </li>
        <li>
          <a href="#profile-data-settings">
            {t('profileIdentity.settingsData')}
          </a>
        </li>
      </ul>
    </nav>
  );
}
