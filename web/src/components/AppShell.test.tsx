import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { renderToStaticMarkup } from 'react-dom/server';
import { MemoryRouter } from 'react-router-dom';
import { AppShell } from './AppShell';

/** Opening anchor tags, so attribute order in the markup does not matter. */
function anchorTags(html: string): string[] {
  return html.match(/<a\b[^>]*>/g) ?? [];
}

/** The navigation link for a destination, not the brand link that shares its href. */
function navigationLinkFor(html: string, href: string): string {
  const tag = anchorTags(html).find(
    (candidate) =>
      candidate.includes(`href="${href}"`) &&
      candidate.includes('shell-nav-link'),
  );
  if (!tag) throw new Error(`No navigation link renders href="${href}".`);
  return tag;
}

function renderShell(route: string): string {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  });
  return renderToStaticMarkup(
    <QueryClientProvider client={queryClient}>
      <MemoryRouter initialEntries={[route]}>
        <AppShell
          onLogout={() => undefined}
          apiBaseUrl="http://api.example.test"
          accessToken="test-token"
          account={{ id: 'account-1', displayName: 'Alex Example' }}
          spaceId="space-1"
        >
          <h1>Content fixture</h1>
        </AppShell>
      </MemoryRouter>
    </QueryClientProvider>,
  );
}

describe('AppShell', () => {
  it('renders skip navigation, landmarks and the primary destinations', () => {
    const html = renderShell('/story');

    expect(html).toContain('href="#main-content"');
    expect(html).toContain('id="main-content"');
    expect(html).toContain('<main');
    expect(html).toContain('<nav');
    expect(html).toContain('href="/today"');
    expect(html).toContain('>Übersicht<');
    expect(html).toContain('href="/story"');
    expect(html).toContain('href="/plan"');
    expect(html).toContain('href="/more"');
    expect(html).toContain('aria-current="page"');
    expect(html).not.toContain('/reminders');
    expect(html).not.toContain('/rules');
  });

  it('keeps Übersicht first in the primary navigation', () => {
    const html = renderShell('/story');
    const sidebar = html.slice(
      html.indexOf('<nav class="shell-nav"'),
      html.indexOf('</nav>', html.indexOf('<nav class="shell-nav"')),
    );

    expect(sidebar.indexOf('href="/today"')).toBeGreaterThanOrEqual(0);
    expect(sidebar.indexOf('href="/today"')).toBeLessThan(
      sidebar.indexOf('href="/story"'),
    );
  });

  it('does not render Discover before its domain exists', () => {
    expect(renderShell('/story')).not.toContain('href="/discover"');
  });

  it('offers Search and Notifications as icon utilities rather than destinations', () => {
    const html = renderShell('/story');
    const header = html.slice(
      html.indexOf('<header'),
      html.indexOf('</header>') + '</header>'.length,
    );

    expect(header).toContain('href="/search"');
    expect(header).toContain('aria-label="Suche"');
    expect(header).toContain('href="/more/notifications"');
    expect(header).toContain('aria-label="Benachrichtigungen"');

    const compact = html.slice(html.indexOf('mobile-bottom-nav'));
    expect(compact).not.toContain('href="/search"');
    expect(compact).not.toContain('href="/more/notifications"');
    const sidebar = html.slice(
      html.indexOf('shell-sidebar'),
      html.indexOf('main-content'),
    );
    expect(sidebar).not.toContain('href="/search"');
    expect(sidebar).not.toContain('href="/more/notifications"');
  });

  it('keeps Profile and Activity in the account tree rather than primary navigation', () => {
    const html = renderShell('/story');
    const header = html.slice(
      html.indexOf('<header'),
      html.indexOf('</header>') + '</header>'.length,
    );
    const sidebar = html.slice(
      html.indexOf('shell-sidebar'),
      html.indexOf('main-content'),
    );

    expect(header).toContain('aria-label="Profil und Konto"');
    expect(header).toContain('href="/more/profile"');
    expect(header).toContain('href="/today/activity"');
    expect(header).toContain('>Abmelden<');
    expect(sidebar).not.toContain('href="/more/profile"');
    expect(sidebar).not.toContain('href="/today/activity"');
  });

  it('offers creation as a shell action and keeps every destination compact', () => {
    const html = renderShell('/story');

    expect(html).toContain('shell-primary-action');
    expect(html).toContain('href="/story/memories/new"');

    const compact = html.slice(html.indexOf('mobile-bottom-nav'));
    for (const path of ['/today', '/story', '/plan', '/more']) {
      expect(compact).toContain(`href="${path}"`);
    }
  });

  it.each([
    ['/today', '/today'],
    ['/today/activity', '/today'],
    ['/story', '/story'],
    ['/plan', '/plan'],
    ['/plan/wishes/wish-1', '/plan'],
    ['/more', '/more'],
    ['/more/people', '/more'],
    ['/more/profile', '/more'],
    ['/more/private/notes', '/more'],
  ])('marks %s as inside the %s destination', (route, destination) => {
    const html = renderShell(route);
    const active = navigationLinkFor(html, destination);

    expect(active).toContain('aria-current="page"');
    expect(active).toContain('shell-nav-link-active');
  });

  it.each([
    ['/story', '/today'],
    ['/story', '/plan'],
    ['/story', '/more'],
    ['/more/people', '/today'],
    ['/today/activity', '/story'],
  ])('does not mark %s as inside the %s destination', (route, sibling) => {
    const inactive = navigationLinkFor(renderShell(route), sibling);

    expect(inactive).not.toContain('aria-current="page"');
    expect(inactive).not.toContain('shell-nav-link-active');
  });
});
