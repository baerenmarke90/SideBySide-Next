// @vitest-environment jsdom
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { act, render, waitFor } from '@testing-library/react';
import { renderToStaticMarkup } from 'react-dom/server';
import { MemoryRouter } from 'react-router-dom';
import navigation from '../i18n/locales/navigation';
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

function renderShell(
  route: string,
  serverAdmin = false,
  unreadCount = 0,
): string {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  });
  queryClient.setQueryData(['profile-identity', 'space-1', 'account-1'], {
    accountId: 'account-1',
    displayName: 'Alex Example',
    profileAttachmentId: null,
    version: 1,
  });
  queryClient.setQueryData(['m5-s5', 'notification-unread-count', 'space-1'], {
    unreadCount,
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
          serverAdmin={serverAdmin}
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
    expect(html).toContain(`>${navigation.today}<`);
    expect(html).toContain('href="/story"');
    expect(html).toContain('href="/plan"');
    expect(html).toContain('href="/more"');
    expect(html).toContain('aria-current="page"');
    expect(html).not.toContain('/reminders');
    expect(html).not.toContain('/rules');
  });

  it('keeps the landing destination first in primary navigation', () => {
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
    expect(header).toContain(`aria-label="${navigation.search}"`);
    expect(header).toContain('href="/more/notifications"');
    expect(header).toContain(`aria-label="${navigation.notifications}"`);
    expect(header).not.toContain('theme-preference');

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

  it('keeps Profile, Settings and Activity in the account tree rather than primary navigation', () => {
    const html = renderShell('/story');
    const header = html.slice(
      html.indexOf('<header'),
      html.indexOf('</header>') + '</header>'.length,
    );
    const sidebar = html.slice(
      html.indexOf('shell-sidebar'),
      html.indexOf('main-content'),
    );

    expect(header).toContain(`aria-label="${navigation.profileMenu}"`);
    expect(header).toContain('href="/more/profile"');
    expect(header).toContain('href="/more/settings"');
    expect(header).toContain('href="/today/activity"');
    expect(header).toContain('header-profile-menu-logout');
    expect(sidebar).not.toContain('href="/more/profile"');
    expect(sidebar).not.toContain('href="/more/settings"');
    expect(sidebar).not.toContain('href="/today/activity"');
  });

  it('shows ServerAdmin only for an authorized account capability', () => {
    expect(renderShell('/story')).not.toContain('href="/server-admin"');

    const authorized = renderShell('/story', true);
    const header = authorized.slice(
      authorized.indexOf('<header'),
      authorized.indexOf('</header>') + '</header>'.length,
    );
    expect(header).toContain('href="/server-admin"');
  });

  it('offers global quick-create triggers for expanded and compact shells', () => {
    const html = renderShell('/story');
    const quickCreateButtons =
      html.match(/<button\b[^>]*quick-create-trigger[^>]*>/g) ?? [];
    const menuIds = quickCreateButtons.map(
      (button) => button.match(/aria-controls="([^"]+)"/)?.[1],
    );

    expect(html).toContain('shell-primary-action');
    expect(html).toContain('mobile-quick-create');
    expect(quickCreateButtons).toHaveLength(2);
    expect(menuIds.every(Boolean)).toBe(true);
    expect(new Set(menuIds).size).toBe(2);
    expect(html).toContain(`>${navigation.newContent}<`);
    expect(html).toContain('aria-haspopup="menu"');
    expect(html).toContain('aria-expanded="false"');

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
    ['/more/settings', '/more'],
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

  it('renders standard bell label and no dot when unread count is zero', () => {
    const html = renderShell('/story', false, 0);

    expect(html).toContain(`aria-label="${navigation.notifications}"`);
    expect(html).not.toContain('notification-dot');
  });

  it('renders unread count accessibility label and visual dot when unread count > 0', () => {
    const html = renderShell('/story', false, 3);

    expect(html).toContain('aria-label="Benachrichtigungen, 3 ungelesen"');
    expect(html).toContain(
      '<span class="notification-dot" aria-hidden="true"></span>',
    );
  });

  it('renders "Unsere Aktivitäten" in header profile menu', () => {
    const html = renderShell('/story');

    expect(html).toContain('Unsere Aktivitäten');
  });

  it('updates unread bell dot and label dynamically on /today without visiting notifications or clicking bell', async () => {
    window.matchMedia =
      window.matchMedia ||
      vi.fn().mockImplementation((query) => ({
        matches: false,
        media: query,
        onchange: null,
        addListener: vi.fn(),
        removeListener: vi.fn(),
        addEventListener: vi.fn(),
        removeEventListener: vi.fn(),
        dispatchEvent: vi.fn(),
      }));

    vi.spyOn(global, 'fetch').mockImplementation(() => Promise.resolve(new Response(JSON.stringify({ unreadCount: 0 }), { status: 200 })));
    const queryClient = new QueryClient({
      defaultOptions: { queries: { retry: false, staleTime: Infinity } },
    });
    queryClient.setQueryData(['profile-identity', 'space-1', 'account-1'], {
      accountId: 'account-1',
      displayName: 'Alex Example',
      profileAttachmentId: null,
      version: 1,
    });
    queryClient.setQueryData(
      ['m5-s5', 'notification-unread-count', 'space-1'],
      { unreadCount: 0 },
    );

    const { container } = render(
      <QueryClientProvider client={queryClient}>
        <MemoryRouter initialEntries={['/today']}>
          <AppShell
            onLogout={() => undefined}
            apiBaseUrl="http://api.example.test"
            accessToken="test-token"
            account={{ id: 'account-1', displayName: 'Alex Example' }}
            spaceId="space-1"
          >
            <h1>Today Content</h1>
          </AppShell>
        </MemoryRouter>
      </QueryClientProvider>,
    );

    // Initial state on /today: unread count is 0, no notification dot
    await waitFor(() => {
      expect(container.querySelector('.notification-dot')).toBeNull();
    });
    let trigger = container.querySelector('.header-notifications-trigger');
    expect(trigger?.getAttribute('aria-label')).toBe(navigation.notifications);

    // Server receives unread notification while user stays on /today
    act(() => {
      queryClient.setQueryData(
        ['m5-s5', 'notification-unread-count', 'space-1'],
        { unreadCount: 1 },
      );
    });

    // Dot appears without visiting notifications or clicking bell
    await waitFor(() => {
      expect(container.querySelector('.notification-dot')).not.toBeNull();
    });
    trigger = container.querySelector('.header-notifications-trigger');
    expect(trigger?.getAttribute('aria-label')).toContain('1 ungelesen');

    // Unread count returns to 0 -> dot disappears
    act(() => {
      queryClient.setQueryData(
        ['m5-s5', 'notification-unread-count', 'space-1'],
        { unreadCount: 0 },
      );
    });

    await waitFor(() => {
      expect(container.querySelector('.notification-dot')).toBeNull();
    });
    trigger = container.querySelector('.header-notifications-trigger');
    expect(trigger?.getAttribute('aria-label')).toBe(navigation.notifications);
  });
});
