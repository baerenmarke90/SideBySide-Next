import { useTranslation } from '../i18n';
import './SettingsIndex.css';

export function SettingsIndex() {
  const { t } = useTranslation();

  return (
    <nav
      className="form-card settings-index"
      aria-label={t('profileIdentity.settingsTitle')}
    >
      <ul className="settings-links">
        <li>
          <a href="#settings-appearance">{t('theme.label')}</a>
        </li>
        <li>
          <a href="#settings-notifications">
            {t('profileIdentity.settingsNotifications')}
          </a>
        </li>
        <li>
          <a href="#settings-connection">
            {t('profileIdentity.settingsRelationship')}
          </a>
        </li>
        <li>
          <a href="#settings-data">{t('profileIdentity.settingsData')}</a>
        </li>
      </ul>
    </nav>
  );
}
