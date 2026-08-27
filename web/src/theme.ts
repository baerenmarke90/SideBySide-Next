export type ThemePreference = 'system' | 'light' | 'dark';
export type ResolvedTheme = 'light' | 'dark';

export const THEME_STORAGE_KEY = 'sidebyside.theme';
export const DARK_MODE_QUERY = '(prefers-color-scheme: dark)';

const THEME_COLOR: Record<ResolvedTheme, string> = {
  light: '#faf8fc',
  dark: '#1c1525',
};

export function parseThemePreference(
  value: string | null | undefined,
): ThemePreference {
  return value === 'light' || value === 'dark' || value === 'system'
    ? value
    : 'system';
}

export function resolveTheme(
  preference: ThemePreference,
  systemPrefersDark: boolean,
): ResolvedTheme {
  if (preference === 'system') return systemPrefersDark ? 'dark' : 'light';
  return preference;
}

export function readThemePreference(): ThemePreference {
  try {
    return parseThemePreference(window.localStorage.getItem(THEME_STORAGE_KEY));
  } catch {
    return 'system';
  }
}

export function storeThemePreference(preference: ThemePreference): void {
  try {
    window.localStorage.setItem(THEME_STORAGE_KEY, preference);
  } catch {
    // Storage can be unavailable in hardened/private browser contexts. The
    // active document still changes theme; only persistence is skipped.
  }
}

export function applyResolvedTheme(
  theme: ResolvedTheme,
  preference?: ThemePreference,
): void {
  const root = document.documentElement;
  root.dataset.theme = theme;
  if (preference) root.dataset.themePreference = preference;
  root.style.colorScheme = theme;

  const themeColor = document.querySelector<HTMLMetaElement>(
    'meta[name="theme-color"]',
  );
  if (themeColor) themeColor.content = THEME_COLOR[theme];
}

export function initializeTheme(): ThemePreference {
  const preference = readThemePreference();
  const systemPrefersDark = window.matchMedia(DARK_MODE_QUERY).matches;
  applyResolvedTheme(resolveTheme(preference, systemPrefersDark), preference);
  return preference;
}
