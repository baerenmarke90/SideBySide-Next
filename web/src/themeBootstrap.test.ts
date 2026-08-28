import { describe, expect, it } from 'vitest';

type NodeFs = {
  readFileSync(path: URL, encoding: 'utf8'): string;
};

type NodeProcess = {
  getBuiltinModule(name: 'fs'): NodeFs;
};

type ThemeDocument = {
  documentElement: {
    dataset: Record<string, string>;
    style: Record<string, string>;
  };
  querySelector(selector: string): { content: string } | null;
};

type ThemeWindow = {
  localStorage: { getItem(key: string): string | null };
  matchMedia(query: string): { matches: boolean };
};

function readBootstrap(): string {
  const processRef = (
    globalThis as typeof globalThis & { process?: NodeProcess }
  ).process;
  if (!processRef)
    throw new Error('Node process API is unavailable in the test run.');
  return processRef
    .getBuiltinModule('fs')
    .readFileSync(
      new URL('../public/theme-bootstrap.js', import.meta.url),
      'utf8',
    );
}

function runBootstrap(
  storedPreference: string | null,
  systemPrefersDark: boolean,
  storageThrows = false,
) {
  const dataset: Record<string, string> = {};
  const style: Record<string, string> = {};
  const themeColor = { content: '#faf8fc' };
  const windowMock: ThemeWindow = {
    localStorage: {
      getItem: () => {
        if (storageThrows) throw new Error('storage blocked');
        return storedPreference;
      },
    },
    matchMedia: (query) => {
      expect(query).toBe('(prefers-color-scheme: dark)');
      return { matches: systemPrefersDark };
    },
  };
  const documentMock: ThemeDocument = {
    documentElement: { dataset, style },
    querySelector: (selector) => {
      expect(selector).toBe('meta[name="theme-color"]');
      return themeColor;
    },
  };

  const execute = new Function('window', 'document', readBootstrap());
  execute(windowMock, documentMock);

  return { dataset, style, themeColor };
}

describe('theme bootstrap', () => {
  it('keeps an explicit dark preference before app startup even on a light system', () => {
    const result = runBootstrap('dark', false);
    expect(result.dataset).toEqual({ theme: 'dark', themePreference: 'dark' });
    expect(result.style.colorScheme).toBe('dark');
    expect(result.themeColor.content).toBe('#1c1525');
  });

  it('keeps an explicit light preference before app startup even on a dark system', () => {
    const result = runBootstrap('light', true);
    expect(result.dataset).toEqual({
      theme: 'light',
      themePreference: 'light',
    });
    expect(result.style.colorScheme).toBe('light');
    expect(result.themeColor.content).toBe('#faf8fc');
  });

  it('follows the operating-system preference in system mode', () => {
    const result = runBootstrap('system', true);
    expect(result.dataset).toEqual({
      theme: 'dark',
      themePreference: 'system',
    });
    expect(result.themeColor.content).toBe('#1c1525');
  });

  it('falls back to system for missing or invalid stored values', () => {
    expect(runBootstrap(null, false).dataset).toEqual({
      theme: 'light',
      themePreference: 'system',
    });
    expect(runBootstrap('sepia', true).dataset).toEqual({
      theme: 'dark',
      themePreference: 'system',
    });
  });

  it('falls back to system when localStorage is unavailable', () => {
    const result = runBootstrap(null, true, true);
    expect(result.dataset).toEqual({
      theme: 'dark',
      themePreference: 'system',
    });
    expect(result.style.colorScheme).toBe('dark');
  });
});
