import i18n from 'i18next';
import { initReactI18next } from 'react-i18next';
import de from './locales/de';

export const DEFAULT_LOCALE = 'de';

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

export function resolvedLocale(): string {
  return i18n.resolvedLanguage || i18n.language || DEFAULT_LOCALE;
}

export { i18n };
export { useTranslation } from 'react-i18next';
