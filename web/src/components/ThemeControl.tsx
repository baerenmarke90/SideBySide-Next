import { useEffect, useState } from 'react';
import {
  applyResolvedTheme,
  DARK_MODE_QUERY,
  readThemePreference,
  resolveTheme,
  storeThemePreference,
  type ThemePreference,
} from '../theme';

export function ThemeControl() {
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
      <label htmlFor="theme-preference">Darstellung</label>
      <select
        id="theme-preference"
        aria-label="Darstellung"
        value={preference}
        onChange={(event) => changePreference(event.currentTarget.value as ThemePreference)}
      >
        <option value="system">System</option>
        <option value="light">Hell</option>
        <option value="dark">Dunkel</option>
      </select>
    </div>
  );
}
