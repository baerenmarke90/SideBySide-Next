import { describe, expect, it } from 'vitest';

function readBootstrap(): string {
  return globalThis.process
    ? globalThis.process.getBuiltinModule('fs').readFileSync(
        new URL('../public/theme-bootstrap.js', import.meta.url),
        'utf8',
      )
    : '';
}

describe('theme bootstrap', () => {
  it('applies the persisted theme before the application bundle starts', () => {
    const source = readBootstrap();

    expect(source).toContain("sidebyside.theme");
    expect(source).toContain("root.dataset.theme = theme");
    expect(source).toContain("root.style.colorScheme = theme");
    expect(source).toContain("themeColors[theme]");
  });

  it('does not require inline JavaScript', () => {
    const source = readBootstrap();

    expect(source).not.toContain('<script');
  });
});
