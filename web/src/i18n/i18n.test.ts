import { DEFAULT_LOCALE, i18n, resolvedLocale } from './index';

describe('web i18n', () => {
  it('starts with German as supported default and fallback locale', () => {
    expect(DEFAULT_LOCALE).toBe('de');
    expect(resolvedLocale()).toBe('de');
    expect(i18n.options.fallbackLng).toEqual(['de']);
  });

  it('uses locale plural rules for photo counts', () => {
    expect(i18n.t('story.photos', { count: 1 })).toBe('1 Foto');
    expect(i18n.t('story.photos', { count: 2 })).toBe('2 Fotos');
  });

  it('falls back to German resources for an unsupported language request', async () => {
    await i18n.changeLanguage('en');
    expect(i18n.t('story.kind.memory')).toBe('Erinnerung');
    await i18n.changeLanguage(DEFAULT_LOCALE);
  });
});
