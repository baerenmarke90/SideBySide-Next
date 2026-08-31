/**
 * Navigation copy.
 *
 * Product copy belongs in this directory rather than in `i18n/index.ts`: the
 * engineering-language audit treats `web/src/i18n/locales` as the sanctioned
 * home for localized text and every other module as an engineering surface.
 *
 * `navigation.story`, `navigation.newMemory`, `navigation.primary` and
 * `navigation.skipToContent` stay in `de.ts` with the rest of the base bundle;
 * this module carries the destination and group labels.
 */
const navigation = {
  planning: 'Planen',
  people: 'Menschen',
  profile: 'Profil',
  dashboard: 'Übersicht',
  search: 'Suche',
  activity: 'Aktivität',
  notifications: 'Benachrichtigungen',
  groups: {
    together: 'Gemeinsam',
    keepUpToDate: 'Auf dem Laufenden',
    you: 'Ihr zwei',
  },
};

export default navigation;
