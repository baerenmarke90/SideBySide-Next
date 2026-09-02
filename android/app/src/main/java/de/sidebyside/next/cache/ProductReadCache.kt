package de.sidebyside.next.cache

import de.sidebyside.next.reference.ReferenceApiException
import java.io.IOException
import java.time.Instant
import java.util.UUID

/**
 * The three shared Story detail kinds this first cache slice covers,
 * matching the Web client's own first cut in `productReadCache.ts`
 * (`ProductCacheKind`) rather than caching every domain at once.
 */
enum class ProductCacheKind(val segment: String) {
    MEMORY("memory"),
    MILESTONE("milestone"),
    HEART_MOMENT("heartMoment"),
}

data class ProductReadResult<T>(
    val value: T,
    val fromCache: Boolean,
    val refreshedAt: Instant,
)

private const val MAX_AGE_MILLIS = 7L * 24 * 60 * 60 * 1000
private const val SCOPE = "SPACE_SHARED"

/**
 * The M2-D18 read cache for shared Story detail content, backed by Room.
 *
 * A cache attempt is only ever made after [isServerAvailabilityFailure]
 * accepts the failure — the same rule the Web client's
 * `mayUseOfflineProductCache` enforces — so a `401`/`403`/Privacy-safe
 * `404`/`409` is never silently papered over with a stale row.
 */
class ProductReadCache(
    private val productDao: ProductCacheDao,
    private val contextDao: CacheContextDao,
) {
    private fun cacheKey(accountId: UUID, spaceId: UUID, kind: ProductCacheKind, resourceId: UUID): String =
        "$accountId:$spaceId:$SCOPE:${kind.segment}:$resourceId"

    /**
     * Wipes every cached row when the recorded Account+Space marker does not
     * match [accountId]/[spaceId] — the defensive half of M2-D18's clearing
     * rule, catching a context change that happened without this instance
     * ever seeing the matching `clearAll()` call (e.g. process death between
     * sessions). Idempotent and cheap enough to call before every read/write.
     */
    private suspend fun ensureContext(accountId: UUID, spaceId: UUID) {
        val next = CacheContextEntity(accountId = accountId.toString(), spaceId = spaceId.toString())
        val current = contextDao.get()
        if (current != null && (current.accountId != next.accountId || current.spaceId != next.spaceId)) {
            productDao.clearAll()
        }
        contextDao.set(next)
    }

    /**
     * Runs [load]; on success, caches the result (unless [canPersist]
     * refuses it) and returns it fresh. On a server-availability failure,
     * falls back to an unexpired cached row for the same key when one
     * exists. Any other failure — including an expired or otherwise
     * unusable cached row — propagates the original network failure
     * unchanged, so the caller's existing error handling needs no cache-
     * specific branch.
     */
    suspend fun <T> loadWithFallback(
        accountId: UUID,
        spaceId: UUID,
        kind: ProductCacheKind,
        resourceId: UUID,
        canPersist: (T) -> Boolean = { true },
        load: suspend () -> T,
        serialize: (T) -> String,
        deserialize: (String) -> T,
    ): Result<ProductReadResult<T>> {
        ensureContext(accountId, spaceId)
        val key = cacheKey(accountId, spaceId, kind, resourceId)

        val networkResult = runCatching { load() }
        val value = networkResult.getOrNull()
        if (value != null) {
            if (canPersist(value)) {
                productDao.put(
                    ProductCacheEntity(
                        cacheKey = key,
                        accountId = accountId.toString(),
                        spaceId = spaceId.toString(),
                        kind = kind.segment,
                        resourceId = resourceId.toString(),
                        payloadJson = serialize(value),
                        refreshedAtEpochMs = System.currentTimeMillis(),
                    ),
                )
            } else {
                productDao.delete(key)
            }
            return Result.success(ProductReadResult(value, fromCache = false, refreshedAt = Instant.now()))
        }

        val throwable = networkResult.exceptionOrNull()
            ?: return Result.failure(IllegalStateException("Neither a value nor a failure was produced."))
        if (!isServerAvailabilityFailure(throwable)) return Result.failure(throwable)

        val cached = productDao.get(key)
        if (cached == null || !isFresh(cached.refreshedAtEpochMs)) {
            if (cached != null) productDao.delete(key)
            return Result.failure(throwable)
        }

        val cachedValue = deserialize(cached.payloadJson)
        if (!canPersist(cachedValue)) {
            productDao.delete(key)
            return Result.failure(throwable)
        }
        return Result.success(
            ProductReadResult(
                cachedValue,
                fromCache = true,
                refreshedAt = Instant.ofEpochMilli(cached.refreshedAtEpochMs),
            ),
        )
    }

    /** The full wipe M2-D18 requires on logout, Account switch, and Space switch. */
    suspend fun clearAll() {
        productDao.clearAll()
        contextDao.clear()
    }
}

private fun isFresh(refreshedAtEpochMs: Long, now: Long = System.currentTimeMillis()): Boolean =
    refreshedAtEpochMs in 0..now && now - refreshedAtEpochMs <= MAX_AGE_MILLIS

/**
 * M2-D18's "transport/server availability failure" boundary: a network-level
 * [IOException] (timeout, connection refused, DNS failure, offline) or an
 * explicit maintenance/gateway status the issue names (502/503/504). A plain
 * `500` is deliberately excluded — that is more likely a real server bug
 * than a temporary unavailability, and M2-D18 requires the cache to never
 * mask an authoritative failure it is not confident is transient.
 */
fun isServerAvailabilityFailure(throwable: Throwable): Boolean = when (throwable) {
    is IOException -> true
    is ReferenceApiException -> throwable.status in SERVER_UNAVAILABLE_STATUSES
    else -> false
}

private val SERVER_UNAVAILABLE_STATUSES = setOf(502, 503, 504)
