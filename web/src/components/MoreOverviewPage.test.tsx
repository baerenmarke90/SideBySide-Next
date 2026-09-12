import { renderToStaticMarkup } from 'react-dom/server';
import { MemoryRouter } from 'react-router-dom';
import de from '../i18n/locales/de';
import { MoreOverviewPage } from './MoreOverviewPage';

describe('MoreOverviewPage', () => {
  it('renders Games with the other secondary destinations and omits persistent header affordances', () => {
    const html = renderToStaticMarkup(
      <MemoryRouter>
        <MoreOverviewPage />
      </MemoryRouter>,
    );

    expect(html).toContain('more-destinations layout-columns');
    expect(html).toContain('href="/games"');
    expect(html).toContain('href="/more/people"');
    expect(html).toContain('href="/more/places"');
    expect(html).toContain('href="/more/collections"');
    expect(html).toContain('href="/more/private"');
    expect(html).not.toContain('href="/more/private/notes"');

    // Destinations duplicated by persistent header actions are removed from More cards
    expect(html).not.toContain('href="/more/notifications"');
    expect(html).not.toContain('href="/more/profile"');
    expect(html).not.toContain('href="/more/settings"');

    // Exactly 5 cards have matching structure: icon box + copy with title & description
    const cardMatches = html.match(/class="more-destination"/g);
    expect(cardMatches).toHaveLength(5);

    const iconMatches = html.match(/class="more-destination-icon"/g);
    expect(iconMatches).toHaveLength(5);

    const copyMatches = html.match(/class="more-destination-copy"/g);
    expect(copyMatches).toHaveLength(5);

    // Intro describes remaining scope
    expect(html).toContain(de.more.intro);
  });
});
