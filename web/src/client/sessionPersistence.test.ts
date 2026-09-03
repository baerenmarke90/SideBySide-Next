import type { AccountView } from '../api/generated/models/AccountView';
import type { SessionView } from '../api/generated/models/SessionView';
import type { TokenView } from '../api/generated/models/TokenView';
import * as referenceFlow from './referenceFlow';
import {
  SESSION_STORAGE_KEY,
  clearStoredSession,
  hasStoredSession,
  isAccessTokenValid,
  isRefreshTokenValid,
  loadStoredSession,
  refreshSessionTokens,
  storeSession,
} from './sessionPersistence';

const mockAccount: AccountView = {
  id: 'acc-123',
  displayName: 'Test User',
};

const mockTokens: TokenView = {
  accessToken: 'access-token-1',
  refreshToken: 'refresh-token-1',
  accessExpiresAt: new Date(Date.now() + 15 * 60 * 1000),
  refreshExpiresAt: new Date(Date.now() + 30 * 24 * 60 * 60 * 1000),
};

const mockSession: SessionView = {
  account: mockAccount,
  tokens: mockTokens,
};

const storageMap = new Map<string, string>();
const mockSessionStorage = {
  getItem: (key: string) => storageMap.get(key) ?? null,
  setItem: (key: string, value: string) => {
    storageMap.set(key, String(value));
  },
  removeItem: (key: string) => {
    storageMap.delete(key);
  },
  clear: () => {
    storageMap.clear();
  },
  get length() {
    return storageMap.size;
  },
  key: (index: number) => Array.from(storageMap.keys())[index] ?? null,
};

describe('sessionPersistence', () => {
  beforeEach(() => {
    (globalThis as unknown as { window: unknown }).window = {
      sessionStorage: mockSessionStorage,
    };
    mockSessionStorage.clear();
    vi.restoreAllMocks();
  });

  afterEach(() => {
    delete (globalThis as unknown as { window?: unknown }).window;
  });

  it('stores and restores session with Date objects intact', () => {
    storeSession(mockSession);

    expect(hasStoredSession()).toBe(true);
    const restored = loadStoredSession();
    expect(restored).not.toBeNull();
    expect(restored?.account.id).toBe('acc-123');
    expect(restored?.account.displayName).toBe('Test User');
    expect(restored?.tokens.accessToken).toBe('access-token-1');
    expect(restored?.tokens.refreshToken).toBe('refresh-token-1');
    expect(restored?.tokens.accessExpiresAt).toBeInstanceOf(Date);
    expect(restored?.tokens.refreshExpiresAt).toBeInstanceOf(Date);
    expect(restored?.tokens.accessExpiresAt.getTime()).toBe(
      mockTokens.accessExpiresAt.getTime(),
    );
  });

  it('clears stored session properly', () => {
    storeSession(mockSession);
    expect(hasStoredSession()).toBe(true);

    clearStoredSession();
    expect(hasStoredSession()).toBe(false);
    expect(loadStoredSession()).toBeNull();
    expect(window.sessionStorage.getItem(SESSION_STORAGE_KEY)).toBeNull();
  });

  it('correctly assesses access token validity', () => {
    const freshTokens: TokenView = {
      ...mockTokens,
      accessExpiresAt: new Date(Date.now() + 120_000),
    };
    expect(isAccessTokenValid(freshTokens)).toBe(true);

    // Token in 30-60s window (e.g. 45s remaining) is invalid by default (triggers proactive refresh)
    const tokenInWindow: TokenView = {
      ...mockTokens,
      accessExpiresAt: new Date(Date.now() + 45_000),
    };
    expect(isAccessTokenValid(tokenInWindow)).toBe(false);

    const expiringSoonTokens: TokenView = {
      ...mockTokens,
      accessExpiresAt: new Date(Date.now() + 10_000),
    };
    expect(isAccessTokenValid(expiringSoonTokens)).toBe(false);

    const expiredTokens: TokenView = {
      ...mockTokens,
      accessExpiresAt: new Date(Date.now() - 5_000),
    };
    expect(isAccessTokenValid(expiredTokens)).toBe(false);
  });

  it('correctly assesses refresh token validity', () => {
    const validTokens: TokenView = {
      ...mockTokens,
      refreshExpiresAt: new Date(Date.now() + 100_000),
    };
    expect(isRefreshTokenValid(validTokens)).toBe(true);

    const expiredTokens: TokenView = {
      ...mockTokens,
      refreshExpiresAt: new Date(Date.now() - 5_000),
    };
    expect(isRefreshTokenValid(expiredTokens)).toBe(false);
  });

  it('deduplicates concurrent refresh calls and rotates stored tokens', async () => {
    storeSession(mockSession);

    const rotatedTokens: TokenView = {
      accessToken: 'rotated-access-2',
      refreshToken: 'rotated-refresh-2',
      accessExpiresAt: new Date(Date.now() + 15 * 60 * 1000),
      refreshExpiresAt: new Date(Date.now() + 30 * 24 * 60 * 60 * 1000),
    };

    let callCount = 0;
    const mockRefresh = vi.fn(async () => {
      callCount += 1;
      // Simulate network latency
      await new Promise((resolve) => setTimeout(resolve, 20));
      return rotatedTokens;
    });

    vi.spyOn(referenceFlow, 'createReferenceApis').mockReturnValue({
      auth: {
        refreshApiV1AuthRefreshPost: mockRefresh,
      },
    } as unknown as ReturnType<typeof referenceFlow.createReferenceApis>);

    // Trigger two concurrent refresh calls
    const [result1, result2] = await Promise.all([
      refreshSessionTokens('http://localhost:8000', 'refresh-token-1'),
      refreshSessionTokens('http://localhost:8000', 'refresh-token-1'),
    ]);

    // Deduplication check: only 1 network call occurred
    expect(callCount).toBe(1);
    expect(result1.accessToken).toBe('rotated-access-2');
    expect(result2.accessToken).toBe('rotated-access-2');

    // Storage is updated with the rotated generation
    const updated = loadStoredSession();
    expect(updated?.tokens.accessToken).toBe('rotated-access-2');
    expect(updated?.tokens.refreshToken).toBe('rotated-refresh-2');
  });

  it('clears stored session on 401 unauthenticated refresh response', async () => {
    storeSession(mockSession);

    vi.spyOn(referenceFlow, 'createReferenceApis').mockReturnValue({
      auth: {
        refreshApiV1AuthRefreshPost: vi.fn().mockRejectedValue({
          status: 401,
          json: async () => ({
            detail: {
              code: 'AUTHENTICATION_REQUIRED',
              message: 'Session revoked or expired.',
            },
          }),
        }),
      },
    } as unknown as ReturnType<typeof referenceFlow.createReferenceApis>);

    await expect(
      refreshSessionTokens('http://localhost:8000', 'refresh-token-1'),
    ).rejects.toMatchObject({ status: 401 });

    // Session is purged so next reload stays logged out
    expect(hasStoredSession()).toBe(false);
  });
});
