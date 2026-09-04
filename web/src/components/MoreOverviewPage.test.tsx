import { renderToStaticMarkup } from 'react-dom/server';
import { MemoryRouter } from 'react-router-dom';
import { MoreOverviewPage } from './MoreOverviewPage';

describe('MoreOverviewPage', () => {
  it('renders all five secondary destinations with consistent card structure', () => {
    const html = renderToStaticMarkup(
      <MemoryRouter>
        <MoreOverviewPage />
      </MemoryRouter>,
    );

    expect(html).toContain(
      'more-destinations layout-columns layout-columns-dense',
    );
    expect(html).toContain('href="/more/people"');
    expect(html).toContain('href="/more/private/notes"');
    expect(html).toContain('href="/more/notifications"');
    expect(html).toContain('href="/more/profile"');
    expect(html).toContain('href="/more/settings"');

    // All 5 cards have matching structure: icon box + copy with title & description
    const cardMatches = html.match(/class="more-destination"/g);
    expect(cardMatches).toHaveLength(5);

    const iconMatches = html.match(/class="more-destination-icon"/g);
    expect(iconMatches).toHaveLength(5);

    const copyMatches = html.match(/class="more-destination-copy"/g);
    expect(copyMatches).toHaveLength(5);
  });
});
