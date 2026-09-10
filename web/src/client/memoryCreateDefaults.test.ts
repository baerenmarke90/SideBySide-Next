import { afterEach, describe, expect, it, vi } from 'vitest';
import de from '../i18n/locales/de';
import {
  effectiveMemoryCreateDate,
  formatDateOnly,
  localCalendarDate,
  prepareMemoryCreateSubmission,
} from './memoryCreateDefaults';

const fallbackTitle = (date: string) =>
  de.memory.fallbackTitle.replace('{{date}}', date);

const localizedFallback = (date: string) => fallbackTitle(date);

afterEach(() => {
  vi.unstubAllEnvs();
});

describe('memory create defaults', () => {
  it('uses the browser-local calendar date for a new form', () => {
    const now = new Date(2026, 8, 10, 15, 30);
    expect(localCalendarDate(now)).toBe('2026-09-10');
  });

  it('does not drift to the UTC date at a timezone boundary', () => {
    vi.stubEnv('TZ', 'America/Los_Angeles');
    const now = new Date('2026-09-10T00:30:00.000Z');

    expect(now.toISOString().slice(0, 10)).toBe('2026-09-10');
    expect(localCalendarDate(now)).toBe('2026-09-09');
  });

  it('prefers a user-selected date', () => {
    const now = new Date(2026, 8, 10, 15, 30);
    expect(effectiveMemoryCreateDate('2024-05-12', now)).toBe('2024-05-12');
  });

  it('falls back to local today when the date field was cleared', () => {
    const now = new Date(2026, 8, 10, 15, 30);
    expect(effectiveMemoryCreateDate('', now)).toBe('2026-09-10');
  });

  it('creates a non-empty localized fallback title for a blank title', () => {
    const result = prepareMemoryCreateSubmission({
      title: '',
      selectedDate: '2026-09-10',
      locale: 'de-DE',
      fallbackTitle,
    });

    expect(result.title).toBe(localizedFallback('10.09.2026'));
    expect(result.happenedOn.toISOString()).toBe('2026-09-10T00:00:00.000Z');
  });

  it('treats whitespace-only title as blank', () => {
    const result = prepareMemoryCreateSubmission({
      title: '   \n  ',
      selectedDate: '2026-09-10',
      locale: 'de-DE',
      fallbackTitle,
    });

    expect(result.title).toBe(localizedFallback('10.09.2026'));
  });

  it('uses the selected date in the fallback title', () => {
    const result = prepareMemoryCreateSubmission({
      title: '',
      selectedDate: '2024-05-12',
      locale: 'de-DE',
      fallbackTitle,
    });

    expect(result.title).toBe(localizedFallback('12.05.2024'));
    expect(result.effectiveDate).toBe('2024-05-12');
  });

  it('preserves an authored title apart from trimming surrounding whitespace', () => {
    const result = prepareMemoryCreateSubmission({
      title: '  Our day at the lake  ',
      selectedDate: '2026-09-10',
      locale: 'de-DE',
      fallbackTitle,
    });

    expect(result.title).toBe('Our day at the lake');
  });

  it('uses the same effective local-today date for title and happenedOn', () => {
    const now = new Date(2026, 8, 10, 23, 45);
    const result = prepareMemoryCreateSubmission({
      title: '',
      selectedDate: '',
      locale: 'de-DE',
      fallbackTitle,
      now,
    });

    expect(result.title).toBe(localizedFallback('10.09.2026'));
    expect(result.effectiveDate).toBe('2026-09-10');
    expect(result.happenedOn.toISOString()).toBe('2026-09-10T00:00:00.000Z');
  });

  it('formats date-only values without local timezone reinterpretation', () => {
    vi.stubEnv('TZ', 'America/Los_Angeles');
    expect(formatDateOnly('2026-09-10', 'de-DE')).toBe('10.09.2026');
  });
});
