import { describe, expect, it } from 'vitest';
import tokens from '../../design/tokens.json';

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

const light = tokens.color.semantic;
const dark = tokens.color.scheme.dark;
const white = tokens.color.base.white.$value;

describe('theme token contrast', () => {
  it('keeps primary and secondary text at WCAG AA in both schemes', () => {
    expect(contrast(light.textPrimary.$value, light.background.$value)).toBeGreaterThanOrEqual(4.5);
    expect(contrast(light.textSecondary.$value, light.surface.$value)).toBeGreaterThanOrEqual(4.5);
    expect(contrast(dark.textPrimary.$value, dark.background.$value)).toBeGreaterThanOrEqual(4.5);
    expect(contrast(dark.textSecondary.$value, dark.surface.$value)).toBeGreaterThanOrEqual(4.5);
  });

  it('keeps primary actions readable in both schemes', () => {
    expect(contrast(white, light.brandStrong.$value)).toBeGreaterThanOrEqual(4.5);
    expect(contrast(white, dark.brandStrong.$value)).toBeGreaterThanOrEqual(4.5);
  });

  it('keeps status text readable on its semantic surface', () => {
    expect(contrast(light.shared.$value, light.sharedSurface.$value)).toBeGreaterThanOrEqual(4.5);
    expect(contrast(light.error.$value, light.errorSurface.$value)).toBeGreaterThanOrEqual(4.5);
    expect(contrast(dark.shared.$value, dark.sharedSurface.$value)).toBeGreaterThanOrEqual(4.5);
    expect(contrast(dark.error.$value, dark.errorSurface.$value)).toBeGreaterThanOrEqual(4.5);
  });

  it('keeps the focus indicator above the 3:1 UI contrast threshold', () => {
    expect(contrast(light.focus.$value, light.background.$value)).toBeGreaterThanOrEqual(3);
    expect(contrast(dark.focus.$value, dark.background.$value)).toBeGreaterThanOrEqual(3);
  });
});
