import { describe, expect, it } from 'vitest';
import { PRODUCT_NAME } from './components/Brand';

type NodeFs = {
  readFileSync(path: URL, encoding: 'utf8'): string;
};

type NodeProcess = {
  getBuiltinModule(name: 'fs'): NodeFs;
};

function readSource(relativePath: string): string {
  const processRef = (
    globalThis as typeof globalThis & { process?: NodeProcess }
  ).process;
  if (!processRef)
    throw new Error('Node process API is unavailable in the test run.');
  return processRef
    .getBuiltinModule('fs')
    .readFileSync(new URL(relativePath, import.meta.url), 'utf8');
}

function escapeRegExp(value: string): string {
  return value.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
}

function cssBlock(css: string, selector: string): string {
  const match = css.match(
    new RegExp(`${escapeRegExp(selector)}\\s*\\{([^}]*)\\}`),
  );
  if (!match) throw new Error(`CSS block is missing: ${selector}`);
  return match[1];
}

function darkThemeBlock(css: string): string {
  const match = css.match(
    /:root\[data-theme=(?:"dark"|'dark')\]\s*\{([^}]*)\}/,
  );
  if (!match) throw new Error('CSS block is missing: :root[data-theme=dark]');
  return match[1];
}

function cssVariable(block: string, name: string): string {
  const match = block.match(new RegExp(`--${name}:\\s*([^;]+);`));
  if (!match) throw new Error(`CSS variable is missing: --${name}`);
  return match[1].trim();
}

function normalizeHex(hex: string): string {
  return hex.toLowerCase();
}

const tokensJson = JSON.parse(readSource('../../design/tokens.json'));
const themeCss = readSource('./theme.css');
const stylesCss = readSource('./styles.css');
const themeTs = readSource('./theme.ts');
const themeBootstrapJs = readSource('../public/theme-bootstrap.js');

const lightStyles = cssBlock(stylesCss, ':root');
const lightTheme = cssBlock(themeCss, ':root');
const darkTheme = darkThemeBlock(themeCss);

describe('design token authority and drift enforcement', () => {
  it('enforces canonical metadata in design/tokens.json', () => {
    expect(tokensJson.meta.name).toBe('eimir. Design Tokens');
    expect(tokensJson.meta.version).toBe('2.0.0');
    expect(tokensJson.meta.status).toBe('foundation');
  });

  it('keeps theme.ts THEME_COLOR in sync with tokens.json backgrounds', () => {
    const lightBg = normalizeHex(tokensJson.color.semantic.background.$value);
    const darkBg = normalizeHex(tokensJson.color.scheme.dark.background.$value);

    expect(themeTs).toContain(`light: '${lightBg}'`);
    expect(themeTs).toContain(`dark: '${darkBg}'`);
  });

  it('keeps theme-bootstrap.js themeColors in sync with tokens.json backgrounds', () => {
    const lightBg = normalizeHex(tokensJson.color.semantic.background.$value);
    const darkBg = normalizeHex(tokensJson.color.scheme.dark.background.$value);

    expect(themeBootstrapJs).toContain(`light: '${lightBg}'`);
    expect(themeBootstrapJs).toContain(`dark: '${darkBg}'`);
  });

  it('enforces zero drift between styles.css :root and tokens.json semantic tokens', () => {
    expect(normalizeHex(cssVariable(lightStyles, 'color-background'))).toBe(
      normalizeHex(tokensJson.color.semantic.background.$value),
    );
    expect(normalizeHex(cssVariable(lightStyles, 'color-surface'))).toBe(
      normalizeHex(tokensJson.color.semantic.surface.$value),
    );
    expect(normalizeHex(cssVariable(lightStyles, 'color-surface-subtle'))).toBe(
      normalizeHex(tokensJson.color.semantic.surfaceSubtle.$value),
    );
    expect(normalizeHex(cssVariable(lightStyles, 'color-text'))).toBe(
      normalizeHex(tokensJson.color.semantic.textPrimary.$value),
    );
    expect(normalizeHex(cssVariable(lightStyles, 'color-text-secondary'))).toBe(
      normalizeHex(tokensJson.color.semantic.textSecondary.$value),
    );
    expect(normalizeHex(cssVariable(lightStyles, 'color-text-muted'))).toBe(
      normalizeHex(tokensJson.color.semantic.textMuted.$value),
    );
    expect(normalizeHex(cssVariable(lightStyles, 'color-border'))).toBe(
      normalizeHex(tokensJson.color.semantic.border.$value),
    );
    expect(normalizeHex(cssVariable(lightStyles, 'color-border-subtle'))).toBe(
      normalizeHex(tokensJson.color.semantic.borderSubtle.$value),
    );
    expect(normalizeHex(cssVariable(lightStyles, 'color-brand'))).toBe(
      normalizeHex(tokensJson.color.semantic.brand.$value),
    );
    expect(normalizeHex(cssVariable(lightStyles, 'color-brand-strong'))).toBe(
      normalizeHex(tokensJson.color.semantic.brandStrong.$value),
    );
    expect(normalizeHex(cssVariable(lightStyles, 'color-brand-surface'))).toBe(
      normalizeHex(tokensJson.color.semantic.brandSurface.$value),
    );
    expect(normalizeHex(cssVariable(lightStyles, 'color-shared'))).toBe(
      normalizeHex(tokensJson.color.semantic.shared.$value),
    );
    expect(normalizeHex(cssVariable(lightStyles, 'color-shared-accent'))).toBe(
      normalizeHex(tokensJson.color.semantic.sharedAccent.$value),
    );
    expect(normalizeHex(cssVariable(lightStyles, 'color-shared-surface'))).toBe(
      normalizeHex(tokensJson.color.semantic.sharedSurface.$value),
    );
    expect(normalizeHex(cssVariable(lightStyles, 'color-private'))).toBe(
      normalizeHex(tokensJson.color.semantic.private.$value),
    );
    expect(normalizeHex(cssVariable(lightStyles, 'color-error'))).toBe(
      normalizeHex(tokensJson.color.semantic.error.$value),
    );
    expect(normalizeHex(cssVariable(lightStyles, 'color-error-surface'))).toBe(
      normalizeHex(tokensJson.color.semantic.errorSurface.$value),
    );
    expect(normalizeHex(cssVariable(lightStyles, 'color-focus'))).toBe(
      normalizeHex(tokensJson.color.semantic.focus.$value),
    );
    expect(cssVariable(lightStyles, 'content-max')).toBe(
      tokensJson.layout.contentMax.$value,
    );
    expect(cssVariable(lightStyles, 'reading-max')).toBe(
      tokensJson.layout.readingMax.$value,
    );
  });

  it('enforces zero drift between theme.css light and dark tokens and tokens.json', () => {
    // Light theme additions
    expect(normalizeHex(cssVariable(lightTheme, 'color-brand-ocean'))).toBe(
      normalizeHex(tokensJson.color.base.ink.$value),
    );
    expect(normalizeHex(cssVariable(lightTheme, 'color-surface-raised'))).toBe(
      normalizeHex(tokensJson.color.semantic.surfaceRaised.$value),
    );
    expect(normalizeHex(cssVariable(lightTheme, 'color-surface-overlay'))).toBe(
      normalizeHex(tokensJson.color.semantic.surfaceOverlay.$value),
    );
    expect(normalizeHex(cssVariable(lightTheme, 'color-brand-text'))).toBe(
      normalizeHex(tokensJson.color.semantic.brandStrong.$value),
    );
    expect(normalizeHex(cssVariable(lightTheme, 'color-brand-glow'))).toBe(
      normalizeHex(tokensJson.color.semantic.brandGlow.$value),
    );
    expect(normalizeHex(cssVariable(lightTheme, 'color-on-accent'))).toBe(
      normalizeHex(tokensJson.color.semantic.onAccent.$value),
    );

    // Dark theme values
    expect(normalizeHex(cssVariable(darkTheme, 'color-background'))).toBe(
      normalizeHex(tokensJson.color.scheme.dark.background.$value),
    );
    expect(normalizeHex(cssVariable(darkTheme, 'color-surface'))).toBe(
      normalizeHex(tokensJson.color.scheme.dark.surface.$value),
    );
    expect(normalizeHex(cssVariable(darkTheme, 'color-surface-subtle'))).toBe(
      normalizeHex(tokensJson.color.scheme.dark.surfaceSubtle.$value),
    );
    expect(normalizeHex(cssVariable(darkTheme, 'color-surface-raised'))).toBe(
      normalizeHex(tokensJson.color.scheme.dark.surfaceRaised.$value),
    );
    expect(normalizeHex(cssVariable(darkTheme, 'color-surface-overlay'))).toBe(
      normalizeHex(tokensJson.color.scheme.dark.surfaceOverlay.$value),
    );
    expect(normalizeHex(cssVariable(darkTheme, 'color-text'))).toBe(
      normalizeHex(tokensJson.color.scheme.dark.textPrimary.$value),
    );
    expect(normalizeHex(cssVariable(darkTheme, 'color-text-secondary'))).toBe(
      normalizeHex(tokensJson.color.scheme.dark.textSecondary.$value),
    );
    expect(normalizeHex(cssVariable(darkTheme, 'color-text-muted'))).toBe(
      normalizeHex(tokensJson.color.scheme.dark.textMuted.$value),
    );
    expect(normalizeHex(cssVariable(darkTheme, 'color-border'))).toBe(
      normalizeHex(tokensJson.color.scheme.dark.border.$value),
    );
    expect(normalizeHex(cssVariable(darkTheme, 'color-border-subtle'))).toBe(
      normalizeHex(tokensJson.color.scheme.dark.borderSubtle.$value),
    );
    expect(normalizeHex(cssVariable(darkTheme, 'color-brand'))).toBe(
      normalizeHex(tokensJson.color.scheme.dark.brand.$value),
    );
    expect(normalizeHex(cssVariable(darkTheme, 'color-brand-strong'))).toBe(
      normalizeHex(tokensJson.color.scheme.dark.brandStrong.$value),
    );
    expect(normalizeHex(cssVariable(darkTheme, 'color-brand-surface'))).toBe(
      normalizeHex(tokensJson.color.scheme.dark.brandSurface.$value),
    );
    expect(normalizeHex(cssVariable(darkTheme, 'color-brand-glow'))).toBe(
      normalizeHex(tokensJson.color.scheme.dark.brandGlow.$value),
    );
    expect(normalizeHex(cssVariable(darkTheme, 'color-shared'))).toBe(
      normalizeHex(tokensJson.color.scheme.dark.shared.$value),
    );
    expect(normalizeHex(cssVariable(darkTheme, 'color-shared-accent'))).toBe(
      normalizeHex(tokensJson.color.scheme.dark.sharedAccent.$value),
    );
    expect(normalizeHex(cssVariable(darkTheme, 'color-shared-surface'))).toBe(
      normalizeHex(tokensJson.color.scheme.dark.sharedSurface.$value),
    );
    expect(normalizeHex(cssVariable(darkTheme, 'color-private'))).toBe(
      normalizeHex(tokensJson.color.scheme.dark.private.$value),
    );
    expect(normalizeHex(cssVariable(darkTheme, 'color-error'))).toBe(
      normalizeHex(tokensJson.color.scheme.dark.error.$value),
    );
    expect(normalizeHex(cssVariable(darkTheme, 'color-error-surface'))).toBe(
      normalizeHex(tokensJson.color.scheme.dark.errorSurface.$value),
    );
    expect(normalizeHex(cssVariable(darkTheme, 'color-focus'))).toBe(
      normalizeHex(tokensJson.color.scheme.dark.focus.$value),
    );
    expect(normalizeHex(cssVariable(darkTheme, 'color-on-accent'))).toBe(
      normalizeHex(tokensJson.color.scheme.dark.onAccent.$value),
    );
  });

  it('exports canonical brand name eimir.', () => {
    expect(PRODUCT_NAME).toBe('eimir.');
  });
});
