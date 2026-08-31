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
  return renderToStaticMarkup(
    <MemoryRouter initialEntries={[route]}>
      <AppShell onLogout={() => undefined}>
        <h1>Content fixture</h1>
      </AppShell>
    </MemoryRouter>,
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
    expect(html).toContain('href="/story"');
    expect(html).toContain('href="/plan"');
    expect(html).toContain('href="/more"');
    expect(html).toContain('aria-current="page"');
    expect(html).not.toContain('/reminders');
    expect(html).not.toContain('/rules');
  });

  it('does not render Discover before its domain exists', () => {
    expect(renderShell('/story')).not.toContain('href="/discover"');
  });

  it('offers Search from the app bar rather than as a destination', () => {
    const html = renderShell('/story');

    expect(html).toContain('href="/search"');
    // The link belongs to the header, not to either navigation landmark.
    const compact = html.slice(html.indexOf('mobile-bottom-nav'));
    expect(compact).not.toContain('href="/search"');
    const sidebar = html.slice(
      html.indexOf('shell-sidebar'),
      html.indexOf('main-content'),
    );
    expect(sidebar).not.toContain('href="/search"');
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
