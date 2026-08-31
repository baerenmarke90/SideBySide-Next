import { describe, expect, it } from 'vitest';
import { ClientProblemError } from './problemDetails';
import {
  PRODUCT_READ_CACHE_MAX_AGE_MS,
  canPersistProductReadPayload,
  isFreshProductCacheTimestamp,
  mayUseOfflineProductCache,
} from './productReadCache';

describe('M5 Web S6 persistent read cache policy', () => {
  it('allows cache fallback only for transport and server availability failures', () => {
    expect(mayUseOfflineProductCache(new ClientProblemError('offline'))).toBe(
      true,
    );
    expect(
      mayUseOfflineProductCache(new ClientProblemError('server', 503)),
    ).toBe(true);
    expect(
      mayUseOfflineProductCache(new ClientProblemError('permission', 403)),
    ).toBe(false);
    expect(
      mayUseOfflineProductCache(new ClientProblemError('notFound', 404)),
    ).toBe(false);
    expect(
      mayUseOfflineProductCache(new ClientProblemError('unauthorized', 401)),
    ).toBe(false);
    expect(
      mayUseOfflineProductCache(new ClientProblemError('conflict', 409)),
    ).toBe(false);
  });

  it('enforces the hard seven-day maximum age before a cache hit', () => {
    const now = Date.parse('2026-08-31T12:00:00.000Z');
    expect(
      isFreshProductCacheTimestamp(
        new Date(now - PRODUCT_READ_CACHE_MAX_AGE_MS).toISOString(),
        now,
      ),
    ).toBe(true);
    expect(
      isFreshProductCacheTimestamp(
        new Date(now - PRODUCT_READ_CACHE_MAX_AGE_MS - 1).toISOString(),
        now,
      ),
    ).toBe(false);
    expect(
      isFreshProductCacheTimestamp(new Date(now + 1).toISOString(), now),
    ).toBe(false);
    expect(isFreshProductCacheTimestamp('not-a-date', now)).toBe(false);
  });

  it('never persists private HeartMoment payloads in the Web cache', () => {
    expect(
      canPersistProductReadPayload('heartMoment', { visibility: 'SHARED' }),
    ).toBe(true);
    expect(
      canPersistProductReadPayload('heartMoment', { visibility: 'PRIVATE' }),
    ).toBe(false);
    expect(canPersistProductReadPayload('heartMoment', {})).toBe(false);
    expect(canPersistProductReadPayload('memory', { visibility: 'PRIVATE' })).toBe(
      true,
    );
  });
});
