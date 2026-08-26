import i18n from 'i18next';
import { initReactI18next } from 'react-i18next';
import de from './locales/de';

export const DEFAULT_LOCALE = 'de';

export function resolvedLocale(): string {
  return i18n.resolvedLanguage || i18n.language || DEFAULT_LOCALE;
}

function syncDocumentLanguage(): void {
  if (typeof document === 'undefined') return;
  document.documentElement.lang = resolvedLocale().split('-')[0];
}

if (!i18n.isInitialized) {
  void i18n.use(initReactI18next).init({
    resources: {
      de: { translation: de },
    },
    lng: DEFAULT_LOCALE,
    fallbackLng: DEFAULT_LOCALE,
    supportedLngs: [DEFAULT_LOCALE],
    initImmediate: false,
    interpolation: {
      escapeValue: false,
    },
  });
}

syncDocumentLanguage();
i18n.on('languageChanged', syncDocumentLanguage);

export { i18n };
export { useTranslation } from 'react-i18next';
