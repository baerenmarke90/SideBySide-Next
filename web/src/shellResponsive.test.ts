type NodeFs = {
  readFileSync(path: URL, encoding: 'utf8'): string;
};

type NodeProcess = {
  getBuiltinModule(name: 'fs'): NodeFs;
};

function readCss(path: string): string {
  const processRef = (
    globalThis as typeof globalThis & { process?: NodeProcess }
  ).process;
  if (!processRef)
    throw new Error('Node process API is unavailable in the test run.');
  return processRef
    .getBuiltinModule('fs')
    .readFileSync(new URL(path, import.meta.url), 'utf8');
}

const shellCss = readCss('./shell.css');
const b2Css = readCss('./components/AppShellB2.css');

describe('responsive app shell source', () => {
  it('keeps mobile bottom navigation as the compact baseline', () => {
    expect(shellCss).toContain('.mobile-bottom-nav');
    expect(shellCss).toContain('position: fixed');
    expect(shellCss).toContain('env(safe-area-inset-bottom)');
  });

  it('keeps compact navigation through the intermediate range', () => {
    expect(b2Css).toContain('@media (min-width: 840px) and (max-width: 959px)');
    expect(b2Css).toMatch(
      /\.product-shell-b2 \.mobile-bottom-nav\s*\{[^}]*display:\s*grid/s,
    );
    expect(b2Css).toMatch(
      /\.product-shell-b2 \.mobile-quick-create\s*\{[^}]*display:\s*flex/s,
    );
  });

  it('uses horizontal product navigation and no compact nav from 960px', () => {
    expect(b2Css).toContain('@media (min-width: 960px)');
    expect(b2Css).toMatch(/\.shell-nav-desktop\s*\{[^}]*display:\s*flex/s);
    expect(b2Css).toMatch(
      /\.product-shell-b2 \.mobile-bottom-nav,[\s\S]*?display:\s*none/s,
    );
  });

  it('keeps the medium-width header from forcing icon-heavy navigation', () => {
    expect(b2Css).toContain('@media (min-width: 960px) and (max-width: 1120px)');
    expect(b2Css).toMatch(
      /\.shell-nav-desktop \.shell-nav-icon\s*\{[^}]*display:\s*none/s,
    );
  });
});
