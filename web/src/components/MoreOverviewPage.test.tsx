import { renderToStaticMarkup } from 'react-dom/server';
import { MemoryRouter } from 'react-router-dom';
import de from '../i18n/locales/de';
import { MoreOverviewPage } from './MoreOverviewPage';

describe('MoreOverviewPage', () => {
  it('renders only secondary destinations without persistent header affordances (People and Private Area)', () => {
    const html = renderToStaticMarkup(
      <MemoryRouter>
        <MoreOverviewPage />
      </MemoryRouter>,
    );

    expect(html).toContain('more-destinations layout-columns');
    expect(html).toContain('href="/more/people"');
    expect(html).toContain('href="/more/private/notes"');

    // Destinations duplicated by persistent header actions are removed from More cards
    expect(html).not.toContain('href="/more/notifications"');
    expect(html).not.toContain('href="/more/profile"');
    expect(html).not.toContain('href="/more/settings"');

    // Exactly 2 cards have matching structure: icon box + copy with title & description
    const cardMatches = html.match(/class="more-destination"/g);
    expect(cardMatches).toHaveLength(2);

    const iconMatches = html.match(/class="more-destination-icon"/g);
    expect(iconMatches).toHaveLength(2);

    const copyMatches = html.match(/class="more-destination-copy"/g);
    expect(copyMatches).toHaveLength(2);

    // Intro describes remaining scope
    expect(html).toContain(de.more.intro);
  });
});
