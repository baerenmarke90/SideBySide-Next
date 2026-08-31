import { renderToStaticMarkup } from 'react-dom/server';
import { MemoryRouter } from 'react-router-dom';
import { AppShell } from './AppShell';

describe('AppShell', () => {
  it('renders skip navigation, landmarks and all implemented product links', () => {
    const html = renderToStaticMarkup(
      <MemoryRouter initialEntries={['/story']}>
        <AppShell onLogout={() => undefined}>
          <h1>Content fixture</h1>
        </AppShell>
      </MemoryRouter>,
    );

    expect(html).toContain('href="#main-content"');
    expect(html).toContain('id="main-content"');
    expect(html).toContain('<main');
    expect(html).toContain('<nav');
    expect(html).toContain('href="/story"');
    expect(html).toContain('href="/planning"');
    expect(html).toContain('href="/dashboard"');
    expect(html).toContain('href="/search"');
    expect(html).toContain('href="/activity"');
    expect(html).toContain('href="/notifications"');
    expect(html).toContain('href="/people"');
    expect(html).toContain('href="/profile"');
    expect(html).toContain('href="/memory/new"');
    expect(html).toContain('aria-current="page"');
    expect(html).not.toContain('/reminders');
    expect(html).not.toContain('/rules');
  });

  it.each([
    '/memory/new',
    '/planning',
    '/planning/wishes/wish-1',
    '/people',
    '/profile',
    '/dashboard',
    '/search',
    '/activity',
    '/notifications',
  ])('marks the %s deep link as the current route', (route) => {
    const html = renderToStaticMarkup(
      <MemoryRouter initialEntries={[route]}>
        <AppShell onLogout={() => undefined}>Content</AppShell>
      </MemoryRouter>,
    );

    expect(html).toContain('aria-current="page"');
    expect(html).toContain('shell-nav-link-active');
  });
});