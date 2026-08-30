import {
  type ClientProblemError,
  normalizeClientError,
} from './problemDetails';

export type ProductCacheKind = 'memory' | 'heartMoment' | 'milestone';
export type ProductReadSource = 'network' | 'cache';

interface ProductCacheRecord {
  key: string;
  accountId: string;
  spaceId: string;
  kind: ProductCacheKind;
  resourceId: string;
  payload: unknown;
  cachedAt: string;
}

export interface ProductReadResult<T> {
  value: T;
  source: ProductReadSource;
}

const DATABASE_NAME = 'sidebyside-web-read-cache';
const DATABASE_VERSION = 1;
const STORE_NAME = 'product-details';

function cacheKey(
  accountId: string,
  spaceId: string,
  kind: ProductCacheKind,
  resourceId: string,
): string {
  return `${accountId}:${spaceId}:${kind}:${resourceId}`;
}

function openCacheDatabase(): Promise<IDBDatabase | null> {
  if (typeof indexedDB === 'undefined') return Promise.resolve(null);

  return new Promise((resolve) => {
    const request = indexedDB.open(DATABASE_NAME, DATABASE_VERSION);
    request.onerror = () => resolve(null);
    request.onupgradeneeded = () => {
      const database = request.result;
      if (!database.objectStoreNames.contains(STORE_NAME)) {
        database.createObjectStore(STORE_NAME, { keyPath: 'key' });
      }
    };
    request.onsuccess = () => resolve(request.result);
  });
}

async function readRecord(key: string): Promise<ProductCacheRecord | null> {
  const database = await openCacheDatabase();
  if (!database) return null;

  return new Promise((resolve) => {
    const transaction = database.transaction(STORE_NAME, 'readonly');
    const request = transaction.objectStore(STORE_NAME).get(key);
    request.onerror = () => resolve(null);
    request.onsuccess = () =>
      resolve((request.result as ProductCacheRecord | undefined) ?? null);
    transaction.oncomplete = () => database.close();
    transaction.onerror = () => database.close();
  });
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

export function mayUseOfflineProductCache(error: ClientProblemError): boolean {
  return error.kind === 'offline' || error.kind === 'server';
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
  const key = cacheKey(accountId, spaceId, kind, resourceId);

  try {
    const value = await load();
    await writeRecord({
      key,
      accountId,
      spaceId,
      kind,
      resourceId,
      payload: serialize(value),
      cachedAt: new Date().toISOString(),
    });
    return { value, source: 'network' };
  } catch (error) {
    const normalized = await normalizeClientError(error);
    if (!mayUseOfflineProductCache(normalized)) throw normalized;

    const cached = await readRecord(key);
    if (!cached) throw normalized;
    return { value: deserialize(cached.payload), source: 'cache' };
  }
}

export async function deleteProductReadCacheEntry(
  accountId: string,
  spaceId: string,
  kind: ProductCacheKind,
  resourceId: string,
): Promise<void> {
  const database = await openCacheDatabase();
  if (!database) return;

  await new Promise<void>((resolve) => {
    const transaction = database.transaction(STORE_NAME, 'readwrite');
    transaction
      .objectStore(STORE_NAME)
      .delete(cacheKey(accountId, spaceId, kind, resourceId));
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

export async function clearProductReadCache(): Promise<void> {
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
