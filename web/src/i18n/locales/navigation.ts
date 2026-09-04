/**
 * Navigation copy.
 *
 * Product copy belongs in this directory rather than in `i18n/index.ts`: the
 * engineering-language audit treats `web/src/i18n/locales` as the sanctioned
 * home for localized text and every other module as an engineering surface.
 *
 * The destination names follow `docs/INFORMATION-ARCHITECTURE.md` section 2.
 */
const navigation = {
  today: 'Wir',
  story: 'Momente',
  plan: 'Planen',
  more: 'Mehr',
  search: 'Suche',
  notifications: 'Benachrichtigungen',
  notificationsWithUnread: 'Benachrichtigungen, {{count}} ungelesen',
  profileMenu: 'Profil und Konto',
  profile: 'Profil',
  settings: 'Einstellungen',
  activity: 'Unsere Aktivitäten',
  newContent: 'Neu festhalten',
  closeMenu: 'Menü schließen',
  quickCreateShared: 'Gemeinsam',
  quickCreatePlanning: 'Planen',
  quickCreateMemory: 'Erinnerung',
  quickCreateHeartMoment: 'Herzmoment',
  quickCreateMilestone: 'Meilenstein',
  quickCreatePlan: 'Plan',
  quickCreateWish: 'Wunsch',
  quickCreatePlace: 'Ort',
  quickCreateChapter: 'Kapitel',
  quickCreateCollection: 'Gemeinsame Liste',
  quickCreatePrivate: 'Privat',
  quickCreatePrivateNote: 'Private Notiz',
  // Reserved for the M7 Discover area; declared so the label is not reused.
  discover: 'Entdecken',
};

export default navigation;
