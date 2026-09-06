package de.sidebyside.next.cache

import androidx.room.Room
import androidx.test.core.app.ApplicationProvider
import java.io.IOException
import java.util.UUID
import kotlinx.coroutines.CompletableDeferred
import kotlinx.coroutines.async
import kotlinx.coroutines.test.runTest
import org.junit.After
import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertNotNull
import org.junit.Assert.assertNull
import org.junit.Assert.assertTrue
import org.junit.Test
import org.junit.runner.RunWith
import org.robolectric.RobolectricTestRunner
import org.robolectric.annotation.Config

/**
 * The #678 cache-boundary invariant: once an Account+Space context has been
 * invalidated, no read that started under it may persist or serve
 * `SPACE_SHARED` or `OWNER_ONLY` data — and a context change clears both
 * persistent stores or neither.
 *
 * Every ordering here is forced with [CompletableDeferred] barriers rather
 * than with delays: the point is which sequence happened, and a test that
 * only usually produces that sequence proves nothing about a race.
 */
@RunWith(RobolectricTestRunner::class)
@Config(sdk = [35])
class ProductReadCacheInvalidationTest {
    private val database = Room.inMemoryDatabaseBuilder(
        ApplicationProvider.getApplicationContext(),
        ReadCacheDatabase::class.java,
    ).allowMainThreadQueries().build()

    private val cache = ProductReadCache(
        database.productCacheDao(),
        database.cacheContextDao(),
        database.protectedCacheDao(),
        FakeProtectedPayloadCipher(),
    )

    private val account = UUID.fromString("11111111-1111-4111-8111-111111111111")
    private val otherAccount = UUID.fromString("aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa")
    private val space = UUID.fromString("22222222-2222-4222-8222-222222222222")
    private val otherSpace = UUID.fromString("44444444-4444-4444-8444-444444444444")
    private val resource = UUID.fromString("33333333-3333-4333-8333-333333333333")

    private val sharedKey = "$account:$space:SPACE_SHARED:memory:$resource"
    private val protectedKey =
        "$account:$space:OWNER_ONLY:$account:privateNote:$PrivateAreaListResourceId"

    @After
    fun tearDown() {
        database.close()
    }

    @Test
    fun aContextMismatchWipesTheSharedAndTheProtectedStoreTogether() = runTest {
        seedSharedRow()
        seedProtectedRow()
        assertNotNull(database.productCacheDao().get(sharedKey))
        assertNotNull(database.protectedCacheDao().get(protectedKey))

        // Any call under a different Space — even an unrelated shared read —
        // has to take both stores with it, not just the one it touches.
        cache.loadWithFallback(
            accountId = account,
            spaceId = otherSpace,
            kind = ProductCacheKind.MILESTONE,
            resourceId = UUID.randomUUID(),
            load = { throw IOException("offline") },
            serialize = { it },
            deserialize = { it },
        )

        assertNull(database.productCacheDao().get(sharedKey))
        assertNull(database.protectedCacheDao().get(protectedKey))
    }

    /**
     * The process-death half of the same rule. Nothing in the second instance
     * ever observed the first one's writes, so only the persisted marker can
     * tell it that the `OWNER_ONLY` rows in front of it belong to somebody
     * else's context.
     */
    @Test
    fun aFreshInstanceUnderANewContextCannotLeaveTheOldContextsProtectedRowsBehind() = runTest {
        val context = ApplicationProvider.getApplicationContext<android.content.Context>()
        val name = "context-mismatch-test-${UUID.randomUUID()}.db"

        val firstProcess = Room.databaseBuilder(context, ReadCacheDatabase::class.java, name)
            .allowMainThreadQueries()
            .build()
        try {
            ProductReadCache(
                firstProcess.productCacheDao(),
                firstProcess.cacheContextDao(),
                firstProcess.protectedCacheDao(),
                FakeProtectedPayloadCipher(),
            ).loadProtectedWithFallback(
                accountId = account,
                spaceId = space,
                ownerId = account,
                kind = ProtectedCacheKind.PRIVATE_NOTE,
                resourceId = PrivateAreaListResourceId,
                load = { "A secret note" },
                serialize = { it },
                deserialize = { it },
            )
            assertNotNull(firstProcess.protectedCacheDao().get(protectedKey))
        } finally {
            firstProcess.close()
        }

        val secondProcess = Room.databaseBuilder(context, ReadCacheDatabase::class.java, name)
            .allowMainThreadQueries()
            .build()
        try {
            ProductReadCache(
                secondProcess.productCacheDao(),
                secondProcess.cacheContextDao(),
                secondProcess.protectedCacheDao(),
                FakeProtectedPayloadCipher(),
            ).loadWithFallback(
                accountId = otherAccount,
                spaceId = space,
                kind = ProductCacheKind.MEMORY,
                resourceId = resource,
                load = { throw IOException("offline") },
                serialize = { it },
                deserialize = { it },
            )

            assertNull(secondProcess.protectedCacheDao().get(protectedKey))
        } finally {
            secondProcess.close()
            context.deleteDatabase(name)
        }
    }

    @Test
    fun aSharedReadInFlightDuringLogoutDoesNotWriteAfterTheWipe() = runTest {
        val reachedNetwork = CompletableDeferred<Unit>()
        val networkResponse = CompletableDeferred<String>()

        val read = async {
            cache.loadWithFallback(
                accountId = account,
                spaceId = space,
                kind = ProductCacheKind.MEMORY,
                resourceId = resource,
                load = {
                    reachedNetwork.complete(Unit)
                    networkResponse.await()
                },
                serialize = { it },
                deserialize = { it },
            )
        }

        reachedNetwork.await() // the lease is captured; the request is in flight
        cache.clearAll() // logout
        networkResponse.complete("A day by the sea")

        val result = read.await()
        // The caller still gets what the server said — the read is not
        // cancelled, it just loses the right to persist it.
        assertTrue(result.isSuccess)
        assertFalse(result.getOrThrow().fromCache)
        assertNull(database.productCacheDao().get(sharedKey))
    }

    @Test
    fun aProtectedReadInFlightDuringLogoutDoesNotWriteAfterTheWipe() = runTest {
        val reachedNetwork = CompletableDeferred<Unit>()
        val networkResponse = CompletableDeferred<String>()

        val read = async {
            cache.loadProtectedWithFallback(
                accountId = account,
                spaceId = space,
                ownerId = account,
                kind = ProtectedCacheKind.PRIVATE_NOTE,
                resourceId = PrivateAreaListResourceId,
                load = {
                    reachedNetwork.complete(Unit)
                    networkResponse.await()
                },
                serialize = { it },
                deserialize = { it },
            )
        }

        reachedNetwork.await()
        cache.clearAll()
        networkResponse.complete("A secret note")

        val result = read.await()
        assertTrue(result.isSuccess)
        assertNull(database.protectedCacheDao().get(protectedKey))
    }

    /**
     * The other way a context ends: not an explicit wipe, but the next Space
     * claiming the cache. The generation moves even though the marker is
     * never absent, so the in-flight read still finds its lease stale.
     */
    @Test
    fun aSharedReadInFlightDuringASpaceSwitchDoesNotWriteAfterTheSwitch() = runTest {
        val reachedNetwork = CompletableDeferred<Unit>()
        val networkResponse = CompletableDeferred<String>()

        val read = async {
            cache.loadWithFallback(
                accountId = account,
                spaceId = space,
                kind = ProductCacheKind.MEMORY,
                resourceId = resource,
                load = {
                    reachedNetwork.complete(Unit)
                    networkResponse.await()
                },
                serialize = { it },
                deserialize = { it },
            )
        }

        reachedNetwork.await()
        // The new Space establishes itself while the old read is still out.
        cache.loadWithFallback(
            accountId = account,
            spaceId = otherSpace,
            kind = ProductCacheKind.MEMORY,
            resourceId = resource,
            load = { "Somebody else's day" },
            serialize = { it },
            deserialize = { it },
        )
        networkResponse.complete("A day by the sea")

        assertTrue(read.await().isSuccess)
        assertNull(database.productCacheDao().get(sharedKey))
    }

    @Test
    fun anInFlightOfflineReadIsNotServedFromTheCacheItStartedUnder() = runTest {
        seedSharedRow()
        val reachedNetwork = CompletableDeferred<Unit>()
        val networkFailed = CompletableDeferred<Unit>()

        val read = async {
            cache.loadWithFallback(
                accountId = account,
                spaceId = space,
                kind = ProductCacheKind.MEMORY,
                resourceId = resource,
                load = {
                    reachedNetwork.complete(Unit)
                    networkFailed.await()
                    throw IOException("offline")
                },
                serialize = { it },
                deserialize = { it },
            )
        }

        reachedNetwork.await()
        cache.clearAll()
        networkFailed.complete(Unit)

        // Fail closed onto the original transport failure rather than answer
        // with a row the wipe was supposed to make unreachable.
        assertTrue(read.await().isFailure)
    }

    /**
     * The wipe a logout starts cannot be awaited by the screen that starts
     * it, so between the two there is a moment where the marker on disk still
     * names the outgoing context. Ending the context synchronously is what
     * has to carry the invariant through that moment — this test never runs
     * the wipe at all, so nothing else can.
     */
    @Test
    fun anInFlightReadStopsWritingBeforeTheWipeItselfEverRuns() = runTest {
        val reachedNetwork = CompletableDeferred<Unit>()
        val networkResponse = CompletableDeferred<String>()

        val read = async {
            cache.loadWithFallback(
                accountId = account,
                spaceId = space,
                kind = ProductCacheKind.MEMORY,
                resourceId = resource,
                load = {
                    reachedNetwork.complete(Unit)
                    networkResponse.await()
                },
                serialize = { it },
                deserialize = { it },
            )
        }

        reachedNetwork.await()
        cache.invalidateContextNow()
        networkResponse.complete("A day by the sea")

        assertTrue(read.await().isSuccess)
        assertNull(database.productCacheDao().get(sharedKey))
    }

    /**
     * The same moment seen from the next read: it arrives for the very same
     * Account+Space, so only the ended generation stands between it and the
     * predecessor's rows.
     */
    @Test
    fun aReadAfterTheContextEndedDoesNotInheritTheRowsTheWipeHasNotRemovedYet() = runTest {
        seedSharedRow()
        seedProtectedRow()

        cache.invalidateContextNow()

        val shared = cache.loadWithFallback(
            accountId = account,
            spaceId = space,
            kind = ProductCacheKind.MEMORY,
            resourceId = resource,
            load = { throw IOException("offline") },
            serialize = { it },
            deserialize = { it },
        )

        assertTrue(shared.isFailure)
        assertNull(database.productCacheDao().get(sharedKey))
        assertNull(database.protectedCacheDao().get(protectedKey))
    }

    @Test
    fun switchingSpaceAndBackCannotRecoverTheFirstSpacesRows() = runTest {
        seedSharedRow()
        seedProtectedRow()

        cache.loadWithFallback(
            accountId = account,
            spaceId = otherSpace,
            kind = ProductCacheKind.MEMORY,
            resourceId = resource,
            load = { "Somebody else's day" },
            serialize = { it },
            deserialize = { it },
        )

        // Back to the original Space: the keys match again, so only an actual
        // wipe can be what keeps the old rows from answering.
        val shared = cache.loadWithFallback(
            accountId = account,
            spaceId = space,
            kind = ProductCacheKind.MEMORY,
            resourceId = resource,
            load = { throw IOException("offline") },
            serialize = { it },
            deserialize = { it },
        )
        val owned = cache.loadProtectedWithFallback(
            accountId = account,
            spaceId = space,
            ownerId = account,
            kind = ProtectedCacheKind.PRIVATE_NOTE,
            resourceId = PrivateAreaListResourceId,
            load = { throw IOException("offline") },
            serialize = { it },
            deserialize = { it },
        )

        assertTrue(shared.isFailure)
        assertTrue(owned.isFailure)
    }

    @Test
    fun logoutFollowedByAnotherAccountCannotRecoverTheFirstAccountsRows() = runTest {
        seedSharedRow()
        seedProtectedRow()

        cache.clearAll()

        val otherAccountsRead = cache.loadWithFallback(
            accountId = otherAccount,
            spaceId = space,
            kind = ProductCacheKind.MEMORY,
            resourceId = resource,
            load = { throw IOException("offline") },
            serialize = { it },
            deserialize = { it },
        )

        assertTrue(otherAccountsRead.isFailure)
        assertNull(database.productCacheDao().get(sharedKey))
        assertNull(database.protectedCacheDao().get(protectedKey))
    }

    /**
     * Membership loss, Space offboarding and leaving the demo all reach the
     * cache through this one wipe, so what has to hold for them is that the
     * wipe leaves no marker behind for a later read to inherit — otherwise a
     * read that outlived the transition could still match a live context.
     */
    @Test
    fun theWipeEveryIdentityTransitionSharesLeavesNoContextBehind() = runTest {
        seedSharedRow()
        seedProtectedRow()
        assertNotNull(database.cacheContextDao().get())

        cache.clearAll()

        assertNull(database.cacheContextDao().get())
        assertNull(database.productCacheDao().get(sharedKey))
        assertNull(database.protectedCacheDao().get(protectedKey))
    }

    /**
     * A context change owes both stores a wipe. When it cannot pay, the new
     * context is never published and no lease is issued: the cache stops
     * writing and stops answering rather than run on a half-cleared store.
     */
    @Test
    fun aContextChangeThatCannotWipeBothStoresPublishesNothingAndPersistsNothing() = runTest {
        val contextDao = RecordingCacheContextDao()
        val failing = ProductReadCache(
            productDao = database.productCacheDao(),
            contextDao = contextDao,
            protectedDao = FailingProtectedCacheDao(database.protectedCacheDao()),
            protectedCipher = FakeProtectedPayloadCipher(),
        )
        contextDao.set(
            CacheContextEntity(accountId = account.toString(), spaceId = space.toString(), generation = "before"),
        )

        val result = failing.loadWithFallback(
            accountId = otherAccount,
            spaceId = space,
            kind = ProductCacheKind.MEMORY,
            resourceId = resource,
            load = { "Somebody else's day" },
            serialize = { it },
            deserialize = { it },
        )

        // The caller is still served from the network; only persistence stops.
        assertTrue(result.isSuccess)
        assertEquals("before", contextDao.get()?.generation)
        assertNull(
            database.productCacheDao().get("$otherAccount:$space:SPACE_SHARED:memory:$resource"),
        )
    }

    private suspend fun seedSharedRow() {
        cache.loadWithFallback(
            accountId = account,
            spaceId = space,
            kind = ProductCacheKind.MEMORY,
            resourceId = resource,
            load = { "A day by the sea" },
            serialize = { it },
            deserialize = { it },
        )
    }

    private suspend fun seedProtectedRow() {
        cache.loadProtectedWithFallback(
            accountId = account,
            spaceId = space,
            ownerId = account,
            kind = ProtectedCacheKind.PRIVATE_NOTE,
            resourceId = PrivateAreaListResourceId,
            load = { "A secret note" },
            serialize = { it },
            deserialize = { it },
        )
    }
}

/** A [ProtectedCacheDao] whose full wipe never succeeds, e.g. a disk error. */
private class FailingProtectedCacheDao(private val delegate: ProtectedCacheDao) : ProtectedCacheDao by delegate {
    override suspend fun clearAll(): Unit = throw IOException("protected store unavailable")
}

/** The context marker held in memory, so a test can watch what gets published. */
private class RecordingCacheContextDao : CacheContextDao {
    private var entity: CacheContextEntity? = null

    override suspend fun get(): CacheContextEntity? = entity

    override suspend fun set(entity: CacheContextEntity) {
        this.entity = entity
    }

    override suspend fun clear() {
        entity = null
    }
}
