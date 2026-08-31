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
  today: 'Heute',
  plan: 'Planen',
  more: 'Mehr',
  search: 'Suche',
  // Reserved for the M7 Discover area; declared so the label is not reused.
  discover: 'Entdecken',
};

export default navigation;
