import {
  type ClientProblemError,
  normalizeClientError,
} from './problemDetails';

export type ProductCacheKind = 'memory' | 'heartMoment' | 'milestone' | 'story';
export type ProductReadSource = 'network' | 'cache';
export type ProductCachePrivacyScope = 'SPACE_SHARED';

interface ProductCacheContext {
  schemaVersion: 1;
  accountId: string;
  spaceId: string;
  generation: string;
}

interface ProductCacheRecord {
  schemaVersion: 3;
  key: string;
  accountId: string;
  spaceId: string;
  generation: string;
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

export interface ProductReadCacheStorage {
  read(key: string): Promise<unknown>;
  write(record: unknown): Promise<void>;
  remove(key: string): Promise<void>;
  clear(): Promise<void>;
}

export const PRODUCT_CACHE_FALLBACK_EVENT = 'sidebyside:read-cache-fallback';
export const PRODUCT_CACHE_NETWORK_EVENT = 'sidebyside:read-cache-network';
export const PRODUCT_READ_CACHE_MAX_AGE_MS = 7 * 24 * 60 * 60 * 1000;

const DATABASE_NAME = 'sidebyside-web-read-cache';
const DATABASE_VERSION = 3;
const STORE_NAME = 'product-details';
const CONTEXT_STORAGE_KEY = 'sidebyside-web-read-cache-context-v3';
const LEGACY_CONTEXT_STORAGE_KEY = 'sidebyside-web-read-cache-context-v2';
const SHARED_SCOPE: ProductCachePrivacyScope = 'SPACE_SHARED';

let activeContext: ProductCacheContext | null = null;
let cacheMutationTail: Promise<void> = Promise.resolve();
const invalidatedGenerations = new Set<string>();

function contextsEqual(
  left: ProductCacheContext | null,
  right: ProductCacheContext | null,
): boolean {
  return (
    left !== null &&
    right !== null &&
    left.accountId === right.accountId &&
    left.spaceId === right.spaceId &&
    left.generation === right.generation
  );
}

function matchesContext(
  context: ProductCacheContext | null,
  accountId: string,
  spaceId: string,
): context is ProductCacheContext {
  return (
    context !== null &&
    context.accountId === accountId &&
    context.spaceId === spaceId
  );
}

function invalidateContext(context: ProductCacheContext | null): void {
  if (context) invalidatedGenerations.add(context.generation);
}

function isContextInvalidated(context: ProductCacheContext | null): boolean {
  return context !== null && invalidatedGenerations.has(context.generation);
}

function createCacheGeneration(): string {
  if (typeof crypto !== 'undefined') {
    if (typeof crypto.randomUUID === 'function') return crypto.randomUUID();
    if (typeof crypto.getRandomValues === 'function') {
      const values = new Uint32Array(4);
      crypto.getRandomValues(values);
      return Array.from(values, (value) =>
        value.toString(16).padStart(8, '0'),
      ).join('');
    }
  }

  throw new Error('Secure cache generation is unavailable');
}

function isCacheContext(value: unknown): value is ProductCacheContext {
  if (!value || typeof value !== 'object') return false;
  const candidate = value as Partial<ProductCacheContext>;
  return (
    candidate.schemaVersion === 1 &&
    typeof candidate.accountId === 'string' &&
    candidate.accountId.length > 0 &&
    typeof candidate.spaceId === 'string' &&
    candidate.spaceId.length > 0 &&
    typeof candidate.generation === 'string' &&
    candidate.generation.length > 0
  );
}

function readCacheContextMarker(): {
  available: boolean;
  hadMarker: boolean;
  context: ProductCacheContext | null;
} {
  if (typeof localStorage === 'undefined') {
    return { available: false, hadMarker: false, context: null };
  }

  try {
    const raw = localStorage.getItem(CONTEXT_STORAGE_KEY);
    const legacy = localStorage.getItem(LEGACY_CONTEXT_STORAGE_KEY);
    if (raw === null) {
      return { available: true, hadMarker: legacy !== null, context: null };
    }

    try {
      const parsed: unknown = JSON.parse(raw);
      return {
        available: true,
        hadMarker: true,
        context: isCacheContext(parsed) ? parsed : null,
      };
    } catch {
      return { available: true, hadMarker: true, context: null };
    }
  } catch {
    return { available: false, hadMarker: false, context: null };
  }
}

function writeCacheContextMarker(context: ProductCacheContext): void {
  if (typeof localStorage === 'undefined') return;
  try {
    localStorage.setItem(CONTEXT_STORAGE_KEY, JSON.stringify(context));
    localStorage.removeItem(LEGACY_CONTEXT_STORAGE_KEY);
  } catch {
    // Marker mismatch makes the new generation fail closed in this runtime.
  }
}

function removeCacheContextMarker(): void {
  if (typeof localStorage === 'undefined') return;
  try {
    localStorage.removeItem(CONTEXT_STORAGE_KEY);
    localStorage.removeItem(LEGACY_CONTEXT_STORAGE_KEY);
  } catch {
    // Invalidated generations keep stale markers unusable in this runtime.
  }
}

function isLeaseCurrent(lease: ProductCacheContext): boolean {
  if (isContextInvalidated(lease) || !contextsEqual(activeContext, lease)) {
    return false;
  }

  const marker = readCacheContextMarker();
  if (!marker.available) return true;
  return contextsEqual(marker.context, lease);
}

function enqueueCacheMutation<T>(operation: () => Promise<T>): Promise<T> {
  const run = cacheMutationTail.then(operation);
  cacheMutationTail = run.then(
    () => undefined,
    () => undefined,
  );
  return run;
}

function cacheKey(
  context: ProductCacheContext,
  privacyScope: ProductCachePrivacyScope,
  kind: ProductCacheKind,
  resourceId: string,
): string {
  return `${context.generation}:${context.accountId}:${context.spaceId}:${privacyScope}:${kind}:${resourceId}`;
}

function openCacheDatabase(): Promise<IDBDatabase | null> {
  if (typeof indexedDB === 'undefined') return Promise.resolve(null);

  return new Promise((resolve, reject) => {
    const request = indexedDB.open(DATABASE_NAME, DATABASE_VERSION);
    request.onerror = () =>
      reject(
        request.error ?? new Error('Failed to open the product read cache'),
      );
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

async function mutateCacheStore(
  mutate: (store: IDBObjectStore) => void,
): Promise<void> {
  const database = await openCacheDatabase();
  if (!database) return;

  await new Promise<void>((resolve, reject) => {
    let settled = false;
    const closeAndResolve = () => {
      if (settled) return;
      settled = true;
      database.close();
      resolve();
    };
    const closeAndReject = (error?: DOMException | null) => {
      if (settled) return;
      settled = true;
      database.close();
      reject(error ?? new Error('Product read cache transaction failed'));
    };

    try {
      const transaction = database.transaction(STORE_NAME, 'readwrite');
      transaction.oncomplete = closeAndResolve;
      transaction.onerror = () => closeAndReject(transaction.error);
      transaction.onabort = () => closeAndReject(transaction.error);
      mutate(transaction.objectStore(STORE_NAME));
    } catch (error) {
      closeAndReject(error instanceof DOMException ? error : null);
    }
  });
}

async function readCacheStoreRecord(key: string): Promise<unknown> {
  const database = await openCacheDatabase();
  if (!database) return null;

  return new Promise<unknown>((resolve, reject) => {
    let settled = false;
    let value: unknown = null;
    const closeAndResolve = () => {
      if (settled) return;
      settled = true;
      database.close();
      resolve(value);
    };
    const closeAndReject = (error?: DOMException | null) => {
      if (settled) return;
      settled = true;
      database.close();
      reject(error ?? new Error('Product read cache transaction failed'));
    };

    try {
      const transaction = database.transaction(STORE_NAME, 'readonly');
      const request = transaction.objectStore(STORE_NAME).get(key);
      request.onerror = () => closeAndReject(request.error);
      request.onsuccess = () => {
        value = request.result ?? null;
      };
      transaction.oncomplete = closeAndResolve;
      transaction.onerror = () => closeAndReject(transaction.error);
      transaction.onabort = () => closeAndReject(transaction.error);
    } catch (error) {
      closeAndReject(error instanceof DOMException ? error : null);
    }
  });
}

const indexedDbStorage: ProductReadCacheStorage = {
  read: readCacheStoreRecord,
  write: (record) => mutateCacheStore((store) => store.put(record)),
  remove: (key) => mutateCacheStore((store) => store.delete(key)),
  clear: () => mutateCacheStore((store) => store.clear()),
};

let cacheStorage: ProductReadCacheStorage = indexedDbStorage;

function scheduleContextStoreClear(): void {
  void enqueueCacheMutation(() => cacheStorage.clear()).catch(() => undefined);
}

function captureCacheLease(
  accountId: string,
  spaceId: string,
): ProductCacheContext {
  const marker = readCacheContextMarker();
  const persistedContext = marker.available ? marker.context : null;

  if (
    marker.available &&
    matchesContext(persistedContext, accountId, spaceId) &&
    !isContextInvalidated(persistedContext)
  ) {
    if (!contextsEqual(activeContext, persistedContext)) {
      invalidateContext(activeContext);
      activeContext = persistedContext;
    }
    return persistedContext;
  }

  if (
    !marker.available &&
    matchesContext(activeContext, accountId, spaceId) &&
    !isContextInvalidated(activeContext)
  ) {
    return activeContext;
  }

  const hadPriorContext =
    persistedContext !== null || activeContext !== null || marker.hadMarker;
  invalidateContext(activeContext);
  invalidateContext(persistedContext);

  const next: ProductCacheContext = {
    schemaVersion: 1,
    accountId,
    spaceId,
    generation: createCacheGeneration(),
  };
  activeContext = next;
  writeCacheContextMarker(next);

  if (hadPriorContext) scheduleContextStoreClear();
  return next;
}

function currentCacheLease(
  accountId: string,
  spaceId: string,
): ProductCacheContext | null {
  const current = activeContext;
  if (!matchesContext(current, accountId, spaceId)) return null;
  return isLeaseCurrent(current) ? current : null;
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
    generation: string;
    kind: ProductCacheKind;
    resourceId: string;
  },
): record is ProductCacheRecord {
  if (!record || typeof record !== 'object') return false;
  const candidate = record as Partial<ProductCacheRecord>;
  return (
    candidate.schemaVersion === 3 &&
    candidate.key === expected.key &&
    candidate.accountId === expected.accountId &&
    candidate.spaceId === expected.spaceId &&
    candidate.generation === expected.generation &&
    candidate.privacyScope === SHARED_SCOPE &&
    candidate.kind === expected.kind &&
    candidate.resourceId === expected.resourceId &&
    typeof candidate.refreshedAt === 'string' &&
    isFreshProductCacheTimestamp(candidate.refreshedAt)
  );
}

async function deleteRecordByKey(
  key: string,
  lease?: ProductCacheContext,
): Promise<void> {
  await enqueueCacheMutation(async () => {
    if (lease && !isLeaseCurrent(lease)) return;
    await cacheStorage.remove(key);
  });
}

async function readRecord(
  expected: {
    key: string;
    accountId: string;
    spaceId: string;
    generation: string;
    kind: ProductCacheKind;
    resourceId: string;
  },
  lease: ProductCacheContext,
): Promise<ProductCacheRecord | null> {
  let record: unknown;
  try {
    record = await cacheStorage.read(expected.key);
  } catch {
    return null;
  }

  if (!isLeaseCurrent(lease)) return null;
  if (!isExpectedRecord(record, expected)) {
    if (record) await deleteRecordByKey(expected.key, lease);
    return null;
  }
  if (!canPersistProductReadPayload(record.kind, record.payload)) {
    await deleteRecordByKey(expected.key, lease);
    return null;
  }
  return record;
}

async function writeRecord(
  record: ProductCacheRecord,
  lease: ProductCacheContext,
): Promise<void> {
  await enqueueCacheMutation(async () => {
    if (!isLeaseCurrent(lease)) return;
    try {
      await cacheStorage.write(record);
    } catch {
      // Ordinary cache writes remain best effort.
    }
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

async function saveProductReadCacheEntryForLease<T>(
  lease: ProductCacheContext,
  {
    kind,
    resourceId,
    value,
    serialize,
    refreshedAt = new Date(),
  }: {
    kind: ProductCacheKind;
    resourceId: string;
    value: T;
    serialize: (value: T) => unknown;
    refreshedAt?: Date;
  },
): Promise<void> {
  if (!isLeaseCurrent(lease)) return;

  const key = cacheKey(lease, SHARED_SCOPE, kind, resourceId);
  const payload = serialize(value);
  if (!canPersistProductReadPayload(kind, payload)) {
    await deleteRecordByKey(key, lease);
    return;
  }

  await writeRecord(
    {
      schemaVersion: 3,
      key,
      accountId: lease.accountId,
      spaceId: lease.spaceId,
      generation: lease.generation,
      privacyScope: SHARED_SCOPE,
      kind,
      resourceId,
      payload,
      refreshedAt: refreshedAt.toISOString(),
    },
    lease,
  );
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
  const lease = currentCacheLease(accountId, spaceId);
  if (!lease) return;
  await saveProductReadCacheEntryForLease(lease, {
    kind,
    resourceId,
    value,
    serialize,
    refreshedAt,
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
  const lease = captureCacheLease(accountId, spaceId);
  const key = cacheKey(lease, SHARED_SCOPE, kind, resourceId);

  let value: T;
  try {
    value = await load();
  } catch (error) {
    const normalized = await normalizeClientError(error);
    if (!mayUseOfflineProductCache(normalized) || !isLeaseCurrent(lease)) {
      throw normalized;
    }

    const cached = await readRecord(
      {
        key,
        accountId,
        spaceId,
        generation: lease.generation,
        kind,
        resourceId,
      },
      lease,
    );
    if (!cached || !isLeaseCurrent(lease)) throw normalized;
    emitCacheEvent(PRODUCT_CACHE_FALLBACK_EVENT, cached.refreshedAt);
    return {
      value: deserialize(cached.payload),
      source: 'cache',
      refreshedAt: new Date(cached.refreshedAt),
    };
  }

  const refreshedAt = new Date();
  await saveProductReadCacheEntryForLease(lease, {
    kind,
    resourceId,
    value,
    serialize,
    refreshedAt,
  });
  if (isLeaseCurrent(lease)) {
    emitCacheEvent(PRODUCT_CACHE_NETWORK_EVENT, refreshedAt.toISOString());
  }
  return { value, source: 'network', refreshedAt };
}

export async function deleteProductReadCacheEntry(
  accountId: string,
  spaceId: string,
  kind: ProductCacheKind,
  resourceId: string,
): Promise<void> {
  const lease = currentCacheLease(accountId, spaceId);
  if (!lease) return;
  await deleteRecordByKey(
    cacheKey(lease, SHARED_SCOPE, kind, resourceId),
    lease,
  );
}

export function clearProductReadCache(): Promise<void> {
  const marker = readCacheContextMarker();
  invalidateContext(activeContext);
  if (marker.available) invalidateContext(marker.context);
  activeContext = null;
  removeCacheContextMarker();
  return enqueueCacheMutation(() => cacheStorage.clear());
}

export function __setProductReadCacheStorageForTests(
  storage: ProductReadCacheStorage,
): void {
  cacheStorage = storage;
}

export function __waitForProductReadCacheMutationsForTests(): Promise<void> {
  return cacheMutationTail;
}

export function __resetProductReadCacheStateForTests(): void {
  activeContext = null;
  cacheMutationTail = Promise.resolve();
  cacheStorage = indexedDbStorage;
  invalidatedGenerations.clear();
}

export const __PRODUCT_READ_CACHE_CONTEXT_STORAGE_KEY_FOR_TESTS =
  CONTEXT_STORAGE_KEY;
