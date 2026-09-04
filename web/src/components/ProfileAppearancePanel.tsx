import { useTranslation } from '../i18n';
import { ThemeControl } from './ThemeControl';

/** Appearance belongs to the centralized personal settings hierarchy. */
export function ProfileAppearancePanel({
  id = 'settings-appearance',
}: {
  id?: string;
} = {}) {
  const { t } = useTranslation();

  return (
    <section
      id={id}
      className="form-card"
      aria-labelledby="profile-appearance-title"
    >
      <h2 id="profile-appearance-title">{t('theme.label')}</h2>
      <p>{t('profileIdentity.appearanceIntro')}</p>
      <ThemeControl variant="inline" />
    </section>
  );
}
