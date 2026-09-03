import { describe, expect, it, vi } from 'vitest';
import type { AccountView } from '../api/generated/models/AccountView';
import type { SessionView } from '../api/generated/models/SessionView';
import type { TokenView } from '../api/generated/models/TokenView';
import {
  consumeAuthReturnTarget,
  rememberCurrentAuthReturnTarget,
} from './deepLinks';
import * as referenceFlow from './referenceFlow';
import {
  clearStoredSession,
  hasStoredSession,
  isAccessTokenValid,
  isRefreshTokenValid,
  loadStoredSession,
  refreshSessionTokens,
  storeSession,
} from './sessionPersistence';

const mockAccount: AccountView = {
  id: 'acc-alex',
  displayName: 'Alex',
};

const validTokens: TokenView = {
  accessToken: 'valid-access-1',
  refreshToken: 'valid-refresh-1',
  accessExpiresAt: new Date(Date.now() + 15 * 60 * 1000),
  refreshExpiresAt: new Date(Date.now() + 30 * 24 * 60 * 60 * 1000),
};

const expiredAccessTokens: TokenView = {
  accessToken: 'expired-access-1',
  refreshToken: 'valid-refresh-1',
  accessExpiresAt: new Date(Date.now() - 60 * 1000),
  refreshExpiresAt: new Date(Date.now() + 30 * 24 * 60 * 60 * 1000),
};

const storageMap = new Map<string, string>();
const mockSessionStorage = {
  getItem: (key: string) => storageMap.get(key) ?? null,
  setItem: (key: string, value: string) => storageMap.set(key, String(value)),
  removeItem: (key: string) => {
    storageMap.delete(key);
  },
  clear: () => storageMap.clear(),
  get length() {
    return storageMap.size;
  },
  key: (i: number) => Array.from(storageMap.keys())[i] ?? null,
};

const localStorageMap = new Map<string, string>();
const mockLocalStorage = {
  getItem: (key: string) => localStorageMap.get(key) ?? null,
  setItem: (key: string, value: string) =>
    localStorageMap.set(key, String(value)),
  removeItem: (key: string) => {
    localStorageMap.delete(key);
  },
  clear: () => localStorageMap.clear(),
};

describe('Browser Session Restoration & Lifecycle Flow', () => {
  beforeEach(() => {
    (globalThis as unknown as { window: unknown }).window = {
      sessionStorage: mockSessionStorage,
      localStorage: mockLocalStorage,
      location: { pathname: '/plan/plans/p-123', search: '' },
    };
    storageMap.clear();
    localStorageMap.clear();
    vi.restoreAllMocks();
  });

  afterEach(() => {
    delete (globalThis as unknown as { window?: unknown }).window;
  });

  it('restores valid session from sessionStorage immediately without login flash', () => {
    storeSession({ account: mockAccount, tokens: validTokens });

    expect(hasStoredSession()).toBe(true);
    const session = loadStoredSession();
    expect(session).not.toBeNull();
    expect(session?.account.displayName).toBe('Alex');
    if (!session) throw new Error('Session unexpectedly null');
    expect(isAccessTokenValid(session.tokens)).toBe(true);
  });

  it('detects expired access token and rotates tokens via backend refresh endpoint', async () => {
    storeSession({ account: mockAccount, tokens: expiredAccessTokens });
    const initialSession = loadStoredSession();
    if (!initialSession) throw new Error('Session unexpectedly null');
    expect(isAccessTokenValid(initialSession.tokens)).toBe(false);
    expect(isRefreshTokenValid(initialSession.tokens)).toBe(true);

    const rotatedTokens: TokenView = {
      accessToken: 'rotated-access-new',
      refreshToken: 'rotated-refresh-new',
      accessExpiresAt: new Date(Date.now() + 15 * 60 * 1000),
      refreshExpiresAt: new Date(Date.now() + 30 * 24 * 60 * 60 * 1000),
    };

    const mockRefresh = vi.fn().mockResolvedValue(rotatedTokens);
    vi.spyOn(referenceFlow, 'createReferenceApis').mockReturnValue({
      auth: { refreshApiV1AuthRefreshPost: mockRefresh },
    } as unknown as ReturnType<typeof referenceFlow.createReferenceApis>);

    const refreshed = await refreshSessionTokens(
      'http://localhost:8000',
      initialSession.tokens.refreshToken,
    );
    expect(mockRefresh).toHaveBeenCalledTimes(1);
    expect(refreshed.accessToken).toBe('rotated-access-new');

    const updated = loadStoredSession();
    expect(updated?.tokens.accessToken).toBe('rotated-access-new');
    expect(updated?.tokens.refreshToken).toBe('rotated-refresh-new');
  });

  it('deduplicates parallel refresh requests to prevent token replay storms', async () => {
    storeSession({ account: mockAccount, tokens: expiredAccessTokens });

    let calls = 0;
    const mockRefresh = vi.fn(async () => {
      calls += 1;
      await new Promise((resolve) => setTimeout(resolve, 15));
      return {
        accessToken: 'single-rotated-access',
        refreshToken: 'single-rotated-refresh',
        accessExpiresAt: new Date(Date.now() + 15 * 60 * 1000),
        refreshExpiresAt: new Date(Date.now() + 30 * 24 * 60 * 60 * 1000),
      };
    });

    vi.spyOn(referenceFlow, 'createReferenceApis').mockReturnValue({
      auth: { refreshApiV1AuthRefreshPost: mockRefresh },
    } as unknown as ReturnType<typeof referenceFlow.createReferenceApis>);

    // Launch 3 parallel refresh calls
    const [r1, r2, r3] = await Promise.all([
      refreshSessionTokens('http://localhost:8000', 'valid-refresh-1'),
      refreshSessionTokens('http://localhost:8000', 'valid-refresh-1'),
      refreshSessionTokens('http://localhost:8000', 'valid-refresh-1'),
    ]);

    expect(calls).toBe(1);
    expect(r1.accessToken).toBe('single-rotated-access');
    expect(r2.accessToken).toBe('single-rotated-access');
    expect(r3.accessToken).toBe('single-rotated-access');
  });

  it('purges session on 401 and remembers original deep link route', async () => {
    storeSession({ account: mockAccount, tokens: expiredAccessTokens });

    // Remember deep link before clearing
    const savedTarget = rememberCurrentAuthReturnTarget();
    expect(savedTarget).toBe('/plan/plans/p-123');

    vi.spyOn(referenceFlow, 'createReferenceApis').mockReturnValue({
      auth: {
        refreshApiV1AuthRefreshPost: vi.fn().mockRejectedValue({
          status: 401,
          json: async () => ({
            detail: {
              code: 'AUTHENTICATION_REQUIRED',
              message: 'Session revoked',
            },
          }),
        }),
      },
    } as unknown as ReturnType<typeof referenceFlow.createReferenceApis>);

    await expect(
      refreshSessionTokens('http://localhost:8000', 'valid-refresh-1'),
    ).rejects.toMatchObject({ status: 401 });

    expect(hasStoredSession()).toBe(false);
    expect(loadStoredSession()).toBeNull();

    // After re-login, original target is consumable
    expect(consumeAuthReturnTarget()).toBe('/plan/plans/p-123');
  });

  it('clears session on logout so reload remains logged out', () => {
    storeSession({ account: mockAccount, tokens: validTokens });
    expect(hasStoredSession()).toBe(true);

    clearStoredSession();
    expect(hasStoredSession()).toBe(false);
    expect(loadStoredSession()).toBeNull();
  });

  it('keeps demo session alive across reload after Lea or Alex is chosen', () => {
    const demoSession: SessionView = {
      account: { id: 'demo-lea-id', displayName: 'Lea' },
      tokens: {
        accessToken: 'demo-lea-access',
        refreshToken: 'demo-lea-refresh',
        accessExpiresAt: new Date(Date.now() + 15 * 60 * 1000),
        refreshExpiresAt: new Date(Date.now() + 6 * 60 * 60 * 1000),
      },
    };

    storeSession(demoSession);

    // Simulate browser reload F5
    const restored = loadStoredSession();
    expect(restored).not.toBeNull();
    expect(restored?.account.displayName).toBe('Lea');
    expect(restored?.tokens.accessToken).toBe('demo-lea-access');
  });
});
