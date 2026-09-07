type NodeFs = {
  readFileSync(path: URL, encoding: 'utf8'): string;
};

type NodeProcess = {
  getBuiltinModule(name: 'fs'): NodeFs;
};

function readSource(path: string): string {
  const processRef = (
    globalThis as typeof globalThis & { process?: NodeProcess }
  ).process;
  if (!processRef)
    throw new Error('Node process API is unavailable in the test run.');
  return processRef
    .getBuiltinModule('fs')
    .readFileSync(new URL(path, import.meta.url), 'utf8');
}

const shellSource = readSource('./AppShell.tsx');
const shellCss = readSource('./AppShellB2.css');

describe('Direction B2 product shell', () => {
  it('removes the expanded sidebar from runtime markup', () => {
    expect(shellSource).not.toContain('<aside');
    expect(shellSource).not.toContain('shell-sidebar');
    expect(shellSource).toContain('shell-nav-desktop');
  });

  it('keeps desktop quick create global without making it a sidebar CTA', () => {
    expect(shellSource).toContain('shell-header-create');
    expect(shellSource).toContain('<QuickCreateMenu variant="desktop" />');
    expect(shellCss).toMatch(
      /\.shell-header-create \.quick-create-trigger\s*\{[^}]*width:\s*44px/s,
    );
  });

  it('preserves Search, Notifications, Profile and compact navigation', () => {
    expect(shellSource).toContain('to={SEARCH_ROUTE}');
    expect(shellSource).toContain('<HeaderNotificationsMenu');
    expect(shellSource).toContain('<HeaderProfileMenu');
    expect(shellSource).toContain('mobile-bottom-nav');
    expect(shellSource).toContain('mobile-quick-create');
  });
});
