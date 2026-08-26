import { describe, expect, it } from 'vitest';
import baseCss from './styles.css?raw';
import themeCss from './theme.css?raw';

function channel(value: number): number {
  const normalized = value / 255;
  return normalized <= 0.04045
    ? normalized / 12.92
    : ((normalized + 0.055) / 1.055) ** 2.4;
}

function luminance(hex: string): number {
  const value = hex.replace('#', '').slice(0, 6);
  const red = Number.parseInt(value.slice(0, 2), 16);
  const green = Number.parseInt(value.slice(2, 4), 16);
  const blue = Number.parseInt(value.slice(4, 6), 16);
  return 0.2126 * channel(red) + 0.7152 * channel(green) + 0.0722 * channel(blue);
}

function contrast(first: string, second: string): number {
  const firstLuminance = luminance(first);
  const secondLuminance = luminance(second);
  const lighter = Math.max(firstLuminance, secondLuminance);
  const darker = Math.min(firstLuminance, secondLuminance);
  return (lighter + 0.05) / (darker + 0.05);
}

function escapeRegExp(value: string): string {
  return value.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
}

function cssBlock(css: string, selector: string): string {
  const match = css.match(new RegExp(`${escapeRegExp(selector)}\\s*\\{([^}]*)\\}`));
  if (!match) throw new Error(`CSS-Block fehlt: ${selector}`);
  return match[1];
}

function cssVariable(block: string, name: string): string {
  const match = block.match(new RegExp(`--${name}:\\s*(#[0-9a-fA-F]{6,8});`));
  if (!match) throw new Error(`CSS-Variable fehlt oder ist keine Hex-Farbe: --${name}`);
  return match[1];
}

const light = cssBlock(baseCss, ':root');
const dark = cssBlock(themeCss, ":root[data-theme='dark']");
const white = '#ffffff';

describe('theme token contrast', () => {
  it('keeps primary and secondary text at WCAG AA in both schemes', () => {
    expect(contrast(cssVariable(light, 'color-text'), cssVariable(light, 'color-background')))
      .toBeGreaterThanOrEqual(4.5);
    expect(contrast(cssVariable(light, 'color-text-secondary'), cssVariable(light, 'color-surface')))
      .toBeGreaterThanOrEqual(4.5);
    expect(contrast(cssVariable(dark, 'color-text'), cssVariable(dark, 'color-background')))
      .toBeGreaterThanOrEqual(4.5);
    expect(contrast(cssVariable(dark, 'color-text-secondary'), cssVariable(dark, 'color-surface')))
      .toBeGreaterThanOrEqual(4.5);
  });

  it('keeps primary actions readable in both schemes', () => {
    expect(contrast(white, cssVariable(light, 'color-brand-strong'))).toBeGreaterThanOrEqual(4.5);
    expect(contrast(white, cssVariable(dark, 'color-brand-strong'))).toBeGreaterThanOrEqual(4.5);
  });

  it('keeps status text readable on its semantic surface', () => {
    expect(contrast(cssVariable(light, 'color-shared'), cssVariable(light, 'color-shared-surface')))
      .toBeGreaterThanOrEqual(4.5);
    expect(contrast(cssVariable(light, 'color-error'), cssVariable(light, 'color-error-surface')))
      .toBeGreaterThanOrEqual(4.5);
    expect(contrast(cssVariable(dark, 'color-shared'), cssVariable(dark, 'color-shared-surface')))
      .toBeGreaterThanOrEqual(4.5);
    expect(contrast(cssVariable(dark, 'color-error'), cssVariable(dark, 'color-error-surface')))
      .toBeGreaterThanOrEqual(4.5);
  });

  it('keeps the focus indicator above the 3:1 UI contrast threshold', () => {
    expect(contrast(cssVariable(light, 'color-focus'), cssVariable(light, 'color-background')))
      .toBeGreaterThanOrEqual(3);
    expect(contrast(cssVariable(dark, 'color-focus'), cssVariable(dark, 'color-background')))
      .toBeGreaterThanOrEqual(3);
  });
});
