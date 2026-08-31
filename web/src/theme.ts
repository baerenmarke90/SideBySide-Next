export type ThemePreference = 'system' | 'light' | 'dark';
export type ResolvedTheme = 'light' | 'dark';

export const THEME_STORAGE_KEY = 'sidebyside.theme';
export const THEME_PREFERENCE_EVENT = 'sidebyside:theme-preference';
export const DARK_MODE_QUERY = '(prefers-color-scheme: dark)';

const THEME_COLOR: Record<ResolvedTheme, string> = {
  light: '#faf8fc',
  dark: '#1c1525',
};

let activeThemePreference: ThemePreference | null = null;

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
    const preference = parseThemePreference(
      window.localStorage.getItem(THEME_STORAGE_KEY),
    );
    activeThemePreference = preference;
    return preference;
  } catch {
    return activeThemePreference ?? 'system';
  }
}

export function storeThemePreference(preference: ThemePreference): void {
  activeThemePreference = preference;
  try {
    window.localStorage.setItem(THEME_STORAGE_KEY, preference);
  } catch {
    // Storage can be unavailable in hardened/private browser contexts. The
    // active document still changes theme; only persistence is skipped.
  }
  if (
    typeof window.dispatchEvent === 'function' &&
    typeof CustomEvent === 'function'
  ) {
    window.dispatchEvent(
      new CustomEvent<ThemePreference>(THEME_PREFERENCE_EVENT, {
        detail: preference,
      }),
    );
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
