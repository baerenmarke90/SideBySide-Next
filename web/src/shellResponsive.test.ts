type NodeFs = {
  readFileSync(path: URL, encoding: 'utf8'): string;
};

type NodeProcess = {
  getBuiltinModule(name: 'fs'): NodeFs;
};

function readShellCss(): string {
  const processRef = (
    globalThis as typeof globalThis & { process?: NodeProcess }
  ).process;
  if (!processRef)
    throw new Error('Node process API is unavailable in the test run.');
  return processRef
    .getBuiltinModule('fs')
    .readFileSync(new URL('./shell.css', import.meta.url), 'utf8');
}

const css = readShellCss();

describe('responsive app shell source', () => {
  it('keeps mobile bottom navigation as the compact default', () => {
    expect(css).toContain('.mobile-bottom-nav');
    expect(css).toContain('position: fixed');
    expect(css).toContain('env(safe-area-inset-bottom)');
  });

  it('switches to desktop sidebar navigation from the documented 840px layout', () => {
    expect(css).toContain('@media (min-width: 840px)');
    expect(css).toMatch(/\.shell-sidebar\s*\{[^}]*display:\s*block/s);
    expect(css).toMatch(/\.mobile-bottom-nav\s*\{[^}]*display:\s*none/s);
  });

  it('collapses top-bar labels before the medium-width overflow range', () => {
    expect(css).toContain('@media (max-width: 839px)');
    expect(css).toContain('.product-topbar .brand-name');
    expect(css).toContain('.product-topbar .shared-context');
  });
});
