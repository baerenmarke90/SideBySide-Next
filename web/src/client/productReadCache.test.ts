import { describe, expect, it } from 'vitest';
import { ClientProblemError } from './problemDetails';
import { mayUseOfflineProductCache } from './productReadCache';

describe('SBS-M5-Web-S2-SCOPE product read cache policy', () => {
  it('allows cache fallback only for transport and server availability failures', () => {
    expect(mayUseOfflineProductCache(new ClientProblemError('offline'))).toBe(true);
    expect(mayUseOfflineProductCache(new ClientProblemError('server', 503))).toBe(true);
    expect(mayUseOfflineProductCache(new ClientProblemError('permission', 403))).toBe(false);
    expect(mayUseOfflineProductCache(new ClientProblemError('notFound', 404))).toBe(false);
    expect(mayUseOfflineProductCache(new ClientProblemError('unauthorized', 401))).toBe(false);
  });
});
