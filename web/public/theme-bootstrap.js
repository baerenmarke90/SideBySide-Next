(function bootstrapTheme() {
  var storageKey = 'sidebyside.theme';
  var darkModeQuery = '(prefers-color-scheme: dark)';
  var themeColors = {
    light: '#faf8fc',
    dark: '#1c1525',
  };

  var preference = 'system';
  var storedPreference;
  try {
    storedPreference = window.localStorage.getItem(storageKey);
    if (
      storedPreference === 'system' ||
      storedPreference === 'light' ||
      storedPreference === 'dark'
    ) {
      preference = storedPreference;
    }
  } catch {
    // Storage can be blocked in hardened/private browser contexts. Falling
    // back to the system preference keeps startup deterministic and usable.
  }

  var systemPrefersDark = window.matchMedia(darkModeQuery).matches;
  var theme = preference === 'system' ? (systemPrefersDark ? 'dark' : 'light') : preference;
  var root = document.documentElement;

  root.dataset.theme = theme;
  root.dataset.themePreference = preference;
  root.style.colorScheme = theme;

  var themeColor = document.querySelector('meta[name="theme-color"]');
  if (themeColor) {
    themeColor.content = themeColors[theme];
  }
})();
