import { useEffect, useState } from 'react';
import { useTranslation } from '../i18n';
import {
  applyResolvedTheme,
  DARK_MODE_QUERY,
  readThemePreference,
  resolveTheme,
  storeThemePreference,
  type ThemePreference,
} from '../theme';

export function ThemeControl() {
  const { t } = useTranslation();
  const [preference, setPreference] = useState<ThemePreference>(readThemePreference);

  useEffect(() => {
    const media = window.matchMedia(DARK_MODE_QUERY);
    const syncTheme = () => applyResolvedTheme(resolveTheme(preference, media.matches), preference);

    syncTheme();
    if (preference === 'system') media.addEventListener('change', syncTheme);
    return () => media.removeEventListener('change', syncTheme);
  }, [preference]);

  function changePreference(next: ThemePreference) {
    storeThemePreference(next);
    setPreference(next);
  }

  return (
    <div className="theme-control">
      <label htmlFor="theme-preference">{t('theme.label')}</label>
      <select
        id="theme-preference"
        aria-label={t('theme.label')}
        value={preference}
        onChange={(event) => changePreference(event.currentTarget.value as ThemePreference)}
      >
        <option value="system">{t('theme.system')}</option>
        <option value="light">{t('theme.light')}</option>
        <option value="dark">{t('theme.dark')}</option>
      </select>
    </div>
  );
}
