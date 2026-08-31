import { describe, expect, it } from 'vitest';
import {
  canonicalDeepLink,
  validateAppRelativeReturnTarget,
} from './deepLinks';

describe('M5 Web S6 canonical Deep Links', () => {
  it('builds opaque canonical targets for shared and owner-only resources', () => {
    expect(canonicalDeepLink('memory', 'a/b')).toBe('/story/memories/a%2Fb');
    expect(canonicalDeepLink('wish', 'wish id')).toBe('/plan/wishes/wish%20id');
    expect(canonicalDeepLink('privateNote', 'note/1')).toBe(
      '/more/private/notes/note%2F1',
    );
  });

  it('accepts canonical app-relative return targets only', () => {
    expect(validateAppRelativeReturnTarget('/today')).toBe('/today');
    expect(validateAppRelativeReturnTarget('/story/memories/abc')).toBe(
      '/story/memories/abc',
    );
    expect(validateAppRelativeReturnTarget('/more/private/gift-ideas/abc')).toBe(
      '/more/private/gift-ideas/abc',
    );
  });

  it('rejects external, legacy, normalized and content-bearing return targets', () => {
    expect(validateAppRelativeReturnTarget('https://example.test/today')).toBeNull();
    expect(validateAppRelativeReturnTarget('//example.test/today')).toBeNull();
    expect(validateAppRelativeReturnTarget('/dashboard')).toBeNull();
    expect(validateAppRelativeReturnTarget('/story/../today')).toBeNull();
    expect(validateAppRelativeReturnTarget('/search?q=private')).toBeNull();
    expect(validateAppRelativeReturnTarget('/today#token')).toBeNull();
    expect(validateAppRelativeReturnTarget('/auth/magic-link')).toBeNull();
  });
});
