import { renderToStaticMarkup } from 'react-dom/server';
import { MemoryRouter } from 'react-router-dom';
import { AppShell } from './AppShell';

describe('AppShell', () => {
  it('renders skip navigation, landmarks and only implemented route links', () => {
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
    expect(html).toContain('href="/memory/new"');
    expect(html).toContain('aria-current="page"');
    expect(html).not.toContain('/dashboard');
    expect(html).not.toContain('/reminders');
  });

  it('marks a direct memory deep link as the current route', () => {
    const html = renderToStaticMarkup(
      <MemoryRouter initialEntries={['/memory/new']}>
        <AppShell onLogout={() => undefined}>Memory</AppShell>
      </MemoryRouter>,
    );

    expect(html).toContain('href="/memory/new"');
    expect(html).toContain('aria-current="page"');
    expect(html).toContain('shell-nav-link-active');
  });
});
