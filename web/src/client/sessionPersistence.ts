import type { AccountView } from '../api/generated/models/AccountView';
import type { TokenView } from '../api/generated/models/TokenView';
import { normalizeClientError } from './problemDetails';
import { createReferenceApis } from './referenceFlow';

export const SESSION_STORAGE_KEY = 'sidebyside-session-v1';

let inFlightRefresh: Promise<TokenView> | null = null;

function parseStoredDate(value: unknown): Date {
  if (value instanceof Date) return value;
  if (typeof value === 'string' || typeof value === 'number') {
    const parsed = new Date(value);
    if (!Number.isNaN(parsed.getTime())) return parsed;
  }
  return new Date(0);
}

function parseStoredTokens(raw: unknown): TokenView | null {
  if (!raw || typeof raw !== 'object') return null;
  const obj = raw as Record<string, unknown>;
  if (
    typeof obj.accessToken !== 'string' ||
    typeof obj.refreshToken !== 'string'
  ) {
    return null;
  }

  return {
    accessToken: obj.accessToken,
    refreshToken: obj.refreshToken,
    accessExpiresAt: parseStoredDate(obj.accessExpiresAt),
    refreshExpiresAt: parseStoredDate(obj.refreshExpiresAt),
  };
}

function parseStoredAccount(raw: unknown): AccountView | null {
  if (!raw || typeof raw !== 'object') return null;
  const obj = raw as Record<string, unknown>;
  if (typeof obj.id !== 'string' || typeof obj.displayName !== 'string') {
    return null;
  }
  return { id: obj.id, displayName: obj.displayName };
}

export type StoredSession = {
  account: AccountView;
  tokens: TokenView;
  spaceId?: string | null;
};

export function storeSession(session: StoredSession): void {
  if (typeof window === 'undefined' || !window.sessionStorage) return;
  try {
    const serialized = JSON.stringify({
      account: session.account,
      tokens: {
        accessToken: session.tokens.accessToken,
        refreshToken: session.tokens.refreshToken,
        accessExpiresAt:
          session.tokens.accessExpiresAt instanceof Date
            ? session.tokens.accessExpiresAt.toISOString()
            : new Date(session.tokens.accessExpiresAt).toISOString(),
        refreshExpiresAt:
          session.tokens.refreshExpiresAt instanceof Date
            ? session.tokens.refreshExpiresAt.toISOString()
            : new Date(session.tokens.refreshExpiresAt).toISOString(),
      },
      spaceId: session.spaceId ?? null,
    });
    window.sessionStorage.setItem(SESSION_STORAGE_KEY, serialized);
  } catch {
    // Storage might be disabled or quota exceeded in restrictive environments.
  }
}

export function loadStoredSession(): StoredSession | null {
  if (typeof window === 'undefined' || !window.sessionStorage) return null;
  try {
    const raw = window.sessionStorage.getItem(SESSION_STORAGE_KEY);
    if (!raw) return null;
    const parsed = JSON.parse(raw) as {
      account?: unknown;
      tokens?: unknown;
      spaceId?: unknown;
    };
    const tokens = parseStoredTokens(parsed.tokens);
    const account = parseStoredAccount(parsed.account);
    if (!tokens || !account) {
      clearStoredSession();
      return null;
    }
    const spaceId =
      typeof parsed.spaceId === 'string' && parsed.spaceId.trim()
        ? parsed.spaceId.trim()
        : null;
    return { account, tokens, spaceId };
  } catch {
    clearStoredSession();
    return null;
  }
}

export function clearStoredSession(): void {
  if (typeof window === 'undefined' || !window.sessionStorage) return;
  try {
    window.sessionStorage.removeItem(SESSION_STORAGE_KEY);
  } catch {
    // Storage might be disabled in restrictive environments.
  }
}

export function hasStoredSession(): boolean {
  return loadStoredSession() !== null;
}

export function isAccessTokenValid(
  tokens: TokenView,
  thresholdMs = 30_000,
): boolean {
  const expiresAt = new Date(tokens.accessExpiresAt).getTime();
  return expiresAt > Date.now() + thresholdMs;
}

export function isRefreshTokenValid(
  tokens: TokenView,
  thresholdMs = 0,
): boolean {
  const expiresAt = new Date(tokens.refreshExpiresAt).getTime();
  return expiresAt > Date.now() + thresholdMs;
}

export async function refreshSessionTokens(
  apiBaseUrl: string,
  refreshToken: string,
): Promise<TokenView> {
  if (inFlightRefresh) {
    return inFlightRefresh;
  }

  inFlightRefresh = (async () => {
    try {
      const apis = createReferenceApis(apiBaseUrl);
      const newTokens = await apis.auth.refreshApiV1AuthRefreshPost({
        refreshRequest: { refreshToken },
      });

      // Update session in storage if present
      const currentSession = loadStoredSession();
      if (currentSession) {
        storeSession({
          account: currentSession.account,
          tokens: newTokens,
          spaceId: currentSession.spaceId,
        });
      }

      return newTokens;
    } catch (error) {
      const normalized = await normalizeClientError(error);
      if (normalized.status === 401) {
        clearStoredSession();
      }
      throw normalized;
    } finally {
      inFlightRefresh = null;
    }
  })();

  return inFlightRefresh;
}
