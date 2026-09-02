package de.sidebyside.next.cache

import de.sidebyside.next.reference.ReferenceApiException
import java.io.IOException
import java.time.Instant
import java.util.UUID

/**
 * The shared Story kinds this cache covers, matching the Web client's own
 * `productReadCache.ts` (`ProductCacheKind`) rather than caching every
 * domain at once. `STORY` is the timeline list itself; the other three are
 * one open detail screen each.
 */
enum class ProductCacheKind(val segment: String) {
    MEMORY("memory"),
    MILESTONE("milestone"),
    HEART_MOMENT("heartMoment"),
    STORY("story"),
    COLLECTION("collection"),
    PLANNING("planning"),
    PLACE("place"),
    CHAPTER("chapter"),
    DASHBOARD("dashboard"),
}

/**
 * Android's Story has no filters (unlike Web's kind/year/order), so there is
 * only ever one timeline per Account+Space — this nil UUID stands in for
 * Web's per-filter synthetic `resourceId`, collapsed to a single constant.
 */
val StoryTimelineResourceId: UUID = UUID(0L, 0L)

/** Shared Collections have no filters either — one list per Account+Space. */
val CollectionListResourceId: UUID = UUID(0L, 0L)

/**
 * Wishes and Plans are fetched and cached together as one snapshot, matching
 * `loadPlanning()`'s existing combined fetch/combined error state — there is
 * one screen, one busy flag, one problem, so there is one cache entry too.
 */
val PlanningResourceId: UUID = UUID(0L, 0L)

/** Places and Chapters have no filters either — one list each per Account+Space. */
val PlaceListResourceId: UUID = UUID(0L, 0L)
val ChapterListResourceId: UUID = UUID(0L, 0L)

/** There is exactly one Today dashboard per Account+Space. */
val TodayDashboardResourceId: UUID = UUID(0L, 0L)

/**
 * The current-user Private Area lists this cache covers. `OWNER_ONLY`
 * content, unlike [ProductCacheKind]'s `SPACE_SHARED` kinds: server-side
 * filtering already scopes each list to its owner, and the cache namespace
 * additionally carries the owner per M2-D18's Android decision.
 */
enum class ProtectedCacheKind(val segment: String) {
    PRIVATE_NOTE("privateNote"),
    GIFT_IDEA("giftIdea"),
    PRIVATE_COLLECTION("privateCollection"),
}

/** Each Private Area surface here is one whole list, not a per-item resource. */
val PrivateAreaListResourceId: UUID = UUID(0L, 0L)

data class ProductReadResult<T>(
    val value: T,
    val fromCache: Boolean,
    val refreshedAt: Instant,
)

private const val MAX_AGE_MILLIS = 7L * 24 * 60 * 60 * 1000
private const val SCOPE = "SPACE_SHARED"
private const val PROTECTED_SCOPE = "OWNER_ONLY"

/**
 * The M2-D18 read cache for shared Story content and the current-user
 * Private Area, backed by Room.
 *
 * A cache attempt is only ever made after [isServerAvailabilityFailure]
 * accepts the failure — the same rule the Web client's
 * `mayUseOfflineProductCache` enforces — so a `401`/`403`/Privacy-safe
 * `404`/`409` is never silently papered over with a stale row.
 *
 * [protectedDao]/[protectedCipher] are both null unless the caller configures
 * `OWNER_ONLY` persistence; [loadProtectedWithFallback] then behaves as
 * memory-only (fresh reads succeed, nothing survives to fall back to), which
 * is also what M2-D18 requires when Keystore-backed encryption cannot be set
 * up safely on a given device.
 */
class ProductReadCache(
    private val productDao: ProductCacheDao,
    private val contextDao: CacheContextDao,
    private val protectedDao: ProtectedCacheDao? = null,
    private val protectedCipher: ProtectedPayloadCipher? = null,
) {
    private fun cacheKey(accountId: UUID, spaceId: UUID, kind: ProductCacheKind, resourceId: UUID): String =
        "$accountId:$spaceId:$SCOPE:${kind.segment}:$resourceId"

    private fun protectedCacheKey(
        accountId: UUID,
        spaceId: UUID,
        ownerId: UUID,
        kind: ProtectedCacheKind,
        resourceId: UUID,
    ): String = "$accountId:$spaceId:$PROTECTED_SCOPE:$ownerId:${kind.segment}:$resourceId"

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

    /**
     * The `OWNER_ONLY` counterpart to [loadWithFallback]: same fallback
     * eligibility and freshness rule, but the cached bytes are encrypted with
     * [protectedCipher] before ever reaching [protectedDao], and a decrypt
     * failure — a corrupted row, or an unreadable key after e.g. a Keystore
     * reset — is treated as no usable cache rather than surfaced as a crash,
     * per M2-D18's "fail closed" requirement.
     */
    suspend fun <T> loadProtectedWithFallback(
        accountId: UUID,
        spaceId: UUID,
        ownerId: UUID,
        kind: ProtectedCacheKind,
        resourceId: UUID,
        load: suspend () -> T,
        serialize: (T) -> String,
        deserialize: (String) -> T,
    ): Result<ProductReadResult<T>> {
        ensureContext(accountId, spaceId)
        val dao = protectedDao
        val cipher = protectedCipher
        val key = protectedCacheKey(accountId, spaceId, ownerId, kind, resourceId)

        val networkResult = runCatching { load() }
        val value = networkResult.getOrNull()
        if (value != null) {
            if (dao != null && cipher != null) {
                // A failure here (e.g. the Keystore key became unusable) means
                // falling back to memory-only owner content, per M2-D18 — not
                // persisting the plaintext as a weaker substitute.
                runCatching {
                    val encrypted = cipher.encrypt(serialize(value))
                    dao.put(
                        ProtectedCacheEntity(
                            cacheKey = key,
                            accountId = accountId.toString(),
                            spaceId = spaceId.toString(),
                            ownerId = ownerId.toString(),
                            kind = kind.segment,
                            resourceId = resourceId.toString(),
                            ciphertext = encrypted.ciphertext,
                            iv = encrypted.iv,
                            refreshedAtEpochMs = System.currentTimeMillis(),
                        ),
                    )
                }
            }
            return Result.success(ProductReadResult(value, fromCache = false, refreshedAt = Instant.now()))
        }

        val throwable = networkResult.exceptionOrNull()
            ?: return Result.failure(IllegalStateException("Neither a value nor a failure was produced."))
        if (!isServerAvailabilityFailure(throwable)) return Result.failure(throwable)
        // No persistence configured at all: there is nothing to fall back to.
        if (dao == null || cipher == null) return Result.failure(throwable)

        val cached = dao.get(key)
        if (cached == null || !isFresh(cached.refreshedAtEpochMs)) {
            if (cached != null) dao.delete(key)
            return Result.failure(throwable)
        }

        val decrypted = runCatching {
            deserialize(cipher.decrypt(EncryptedPayload(cached.ciphertext, cached.iv)))
        }.getOrElse {
            dao.delete(key)
            return Result.failure(throwable)
        }
        return Result.success(
            ProductReadResult(
                decrypted,
                fromCache = true,
                refreshedAt = Instant.ofEpochMilli(cached.refreshedAtEpochMs),
            ),
        )
    }

    /** The full wipe M2-D18 requires on logout, Account switch, and Space switch. */
    suspend fun clearAll() {
        productDao.clearAll()
        protectedDao?.clearAll()
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
