import {
  type ClientProblemError,
  normalizeClientError,
} from './problemDetails';

export type ProductCacheKind = 'memory' | 'heartMoment' | 'milestone' | 'story';
export type ProductReadSource = 'network' | 'cache';
export type ProductCachePrivacyScope = 'SPACE_SHARED';

interface ProductCacheRecord {
  schemaVersion: 2;
  key: string;
  accountId: string;
  spaceId: string;
  privacyScope: ProductCachePrivacyScope;
  kind: ProductCacheKind;
  resourceId: string;
  payload: unknown;
  refreshedAt: string;
}

export interface ProductReadResult<T> {
  value: T;
  source: ProductReadSource;
  refreshedAt?: Date;
}

export interface ProductCacheEventDetail {
  refreshedAt: string;
}

export const PRODUCT_CACHE_FALLBACK_EVENT = 'sidebyside:read-cache-fallback';
export const PRODUCT_CACHE_NETWORK_EVENT = 'sidebyside:read-cache-network';
export const PRODUCT_READ_CACHE_MAX_AGE_MS = 7 * 24 * 60 * 60 * 1000;

const DATABASE_NAME = 'sidebyside-web-read-cache';
const DATABASE_VERSION = 2;
const STORE_NAME = 'product-details';
const CONTEXT_STORAGE_KEY = 'sidebyside-web-read-cache-context-v2';
const SHARED_SCOPE: ProductCachePrivacyScope = 'SPACE_SHARED';

function cacheKey(
  accountId: string,
  spaceId: string,
  privacyScope: ProductCachePrivacyScope,
  kind: ProductCacheKind,
  resourceId: string,
): string {
  return `${accountId}:${spaceId}:${privacyScope}:${kind}:${resourceId}`;
}

function openCacheDatabase(): Promise<IDBDatabase | null> {
  if (typeof indexedDB === 'undefined') return Promise.resolve(null);

  return new Promise((resolve) => {
    const request = indexedDB.open(DATABASE_NAME, DATABASE_VERSION);
    request.onerror = () => resolve(null);
    request.onupgradeneeded = (event) => {
      const database = request.result;
      if (
        event.oldVersion < DATABASE_VERSION &&
        database.objectStoreNames.contains(STORE_NAME)
      ) {
        database.deleteObjectStore(STORE_NAME);
      }
      if (!database.objectStoreNames.contains(STORE_NAME)) {
        database.createObjectStore(STORE_NAME, { keyPath: 'key' });
      }
    };
    request.onsuccess = () => resolve(request.result);
  });
}

async function clearCacheStore(): Promise<void> {
  const database = await openCacheDatabase();
  if (!database) return;

  await new Promise<void>((resolve) => {
    const transaction = database.transaction(STORE_NAME, 'readwrite');
    transaction.objectStore(STORE_NAME).clear();
    transaction.oncomplete = () => {
      database.close();
      resolve();
    };
    transaction.onerror = () => {
      database.close();
      resolve();
    };
    transaction.onabort = () => {
      database.close();
      resolve();
    };
  });
}

async function ensureCacheContext(
  accountId: string,
  spaceId: string,
): Promise<void> {
  if (typeof localStorage === 'undefined') return;
  const nextContext = `${accountId}:${spaceId}`;
  const currentContext = localStorage.getItem(CONTEXT_STORAGE_KEY);
  if (currentContext && currentContext !== nextContext) {
    await clearCacheStore();
  }
  localStorage.setItem(CONTEXT_STORAGE_KEY, nextContext);
}

async function deleteRecordByKey(key: string): Promise<void> {
  const database = await openCacheDatabase();
  if (!database) return;

  await new Promise<void>((resolve) => {
    const transaction = database.transaction(STORE_NAME, 'readwrite');
    transaction.objectStore(STORE_NAME).delete(key);
    transaction.oncomplete = () => {
      database.close();
      resolve();
    };
    transaction.onerror = () => {
      database.close();
      resolve();
    };
    transaction.onabort = () => {
      database.close();
      resolve();
    };
  });
}

export function isFreshProductCacheTimestamp(
  refreshedAt: string,
  now = Date.now(),
): boolean {
  const timestamp = Date.parse(refreshedAt);
  return (
    Number.isFinite(timestamp) &&
    timestamp <= now &&
    now - timestamp <= PRODUCT_READ_CACHE_MAX_AGE_MS
  );
}

export function canPersistProductReadPayload(
  kind: ProductCacheKind,
  payload: unknown,
): boolean {
  if (kind !== 'heartMoment') return true;
  if (!payload || typeof payload !== 'object') return false;
  return (payload as { visibility?: unknown }).visibility === 'SHARED';
}

function isExpectedRecord(
  record: unknown,
  expected: {
    key: string;
    accountId: string;
    spaceId: string;
    kind: ProductCacheKind;
    resourceId: string;
  },
): record is ProductCacheRecord {
  if (!record || typeof record !== 'object') return false;
  const candidate = record as Partial<ProductCacheRecord>;
  return (
    candidate.schemaVersion === 2 &&
    candidate.key === expected.key &&
    candidate.accountId === expected.accountId &&
    candidate.spaceId === expected.spaceId &&
    candidate.privacyScope === SHARED_SCOPE &&
    candidate.kind === expected.kind &&
    candidate.resourceId === expected.resourceId &&
    typeof candidate.refreshedAt === 'string' &&
    isFreshProductCacheTimestamp(candidate.refreshedAt)
  );
}

async function readRecord(expected: {
  key: string;
  accountId: string;
  spaceId: string;
  kind: ProductCacheKind;
  resourceId: string;
}): Promise<ProductCacheRecord | null> {
  const database = await openCacheDatabase();
  if (!database) return null;

  const record = await new Promise<unknown>((resolve) => {
    const transaction = database.transaction(STORE_NAME, 'readonly');
    const request = transaction.objectStore(STORE_NAME).get(expected.key);
    request.onerror = () => resolve(null);
    request.onsuccess = () => resolve(request.result ?? null);
    transaction.oncomplete = () => database.close();
    transaction.onerror = () => database.close();
  });

  if (!isExpectedRecord(record, expected)) {
    if (record) await deleteRecordByKey(expected.key);
    return null;
  }
  if (!canPersistProductReadPayload(record.kind, record.payload)) {
    await deleteRecordByKey(expected.key);
    return null;
  }
  return record;
}

async function writeRecord(record: ProductCacheRecord): Promise<void> {
  const database = await openCacheDatabase();
  if (!database) return;

  await new Promise<void>((resolve) => {
    const transaction = database.transaction(STORE_NAME, 'readwrite');
    transaction.objectStore(STORE_NAME).put(record);
    transaction.oncomplete = () => {
      database.close();
      resolve();
    };
    transaction.onerror = () => {
      database.close();
      resolve();
    };
    transaction.onabort = () => {
      database.close();
      resolve();
    };
  });
}

function emitCacheEvent(type: string, refreshedAt: string): void {
  if (typeof window === 'undefined' || typeof CustomEvent === 'undefined')
    return;
  window.dispatchEvent(
    new CustomEvent<ProductCacheEventDetail>(type, {
      detail: { refreshedAt },
    }),
  );
}

export function mayUseOfflineProductCache(error: ClientProblemError): boolean {
  return error.kind === 'offline' || error.kind === 'server';
}

export async function saveProductReadCacheEntry<T>({
  accountId,
  spaceId,
  kind,
  resourceId,
  value,
  serialize,
  refreshedAt = new Date(),
}: {
  accountId: string;
  spaceId: string;
  kind: ProductCacheKind;
  resourceId: string;
  value: T;
  serialize: (value: T) => unknown;
  refreshedAt?: Date;
}): Promise<void> {
  await ensureCacheContext(accountId, spaceId);
  const key = cacheKey(accountId, spaceId, SHARED_SCOPE, kind, resourceId);
  const payload = serialize(value);
  if (!canPersistProductReadPayload(kind, payload)) {
    await deleteRecordByKey(key);
    return;
  }

  await writeRecord({
    schemaVersion: 2,
    key,
    accountId,
    spaceId,
    privacyScope: SHARED_SCOPE,
    kind,
    resourceId,
    payload,
    refreshedAt: refreshedAt.toISOString(),
  });
}

export async function loadProductWithReadCache<T>({
  accountId,
  spaceId,
  kind,
  resourceId,
  load,
  serialize,
  deserialize,
}: {
  accountId: string;
  spaceId: string;
  kind: ProductCacheKind;
  resourceId: string;
  load: () => Promise<T>;
  serialize: (value: T) => unknown;
  deserialize: (payload: unknown) => T;
}): Promise<ProductReadResult<T>> {
  await ensureCacheContext(accountId, spaceId);
  const key = cacheKey(accountId, spaceId, SHARED_SCOPE, kind, resourceId);

  try {
    const value = await load();
    const refreshedAt = new Date();
    await saveProductReadCacheEntry({
      accountId,
      spaceId,
      kind,
      resourceId,
      value,
      serialize,
      refreshedAt,
    });
    emitCacheEvent(PRODUCT_CACHE_NETWORK_EVENT, refreshedAt.toISOString());
    return { value, source: 'network', refreshedAt };
  } catch (error) {
    const normalized = await normalizeClientError(error);
    if (!mayUseOfflineProductCache(normalized)) throw normalized;

    const cached = await readRecord({
      key,
      accountId,
      spaceId,
      kind,
      resourceId,
    });
    if (!cached) throw normalized;
    emitCacheEvent(PRODUCT_CACHE_FALLBACK_EVENT, cached.refreshedAt);
    return {
      value: deserialize(cached.payload),
      source: 'cache',
      refreshedAt: new Date(cached.refreshedAt),
    };
  }
}

export async function deleteProductReadCacheEntry(
  accountId: string,
  spaceId: string,
  kind: ProductCacheKind,
  resourceId: string,
): Promise<void> {
  await deleteRecordByKey(
    cacheKey(accountId, spaceId, SHARED_SCOPE, kind, resourceId),
  );
}

export async function clearProductReadCache(): Promise<void> {
  if (typeof localStorage !== 'undefined') {
    localStorage.removeItem(CONTEXT_STORAGE_KEY);
  }
  await clearCacheStore();
}
