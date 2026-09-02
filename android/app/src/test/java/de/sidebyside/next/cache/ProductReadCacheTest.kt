package de.sidebyside.next.cache

import androidx.room.Room
import androidx.test.core.app.ApplicationProvider
import de.sidebyside.next.reference.ReferenceApiException
import java.io.IOException
import java.util.UUID
import kotlinx.coroutines.test.runTest
import org.junit.After
import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertTrue
import org.junit.Before
import org.junit.Test
import org.junit.runner.RunWith
import org.robolectric.RobolectricTestRunner
import org.robolectric.annotation.Config

/**
 * The M2-D18 read cache, proven against a real in-memory Room database
 * rather than a mocked DAO — the SQL/entity mapping and the fallback
 * decision are exactly the part worth catching a mistake in.
 */
@RunWith(RobolectricTestRunner::class)
@Config(sdk = [35])
class ProductReadCacheTest {
    private val database = Room.inMemoryDatabaseBuilder(
        ApplicationProvider.getApplicationContext(),
        ReadCacheDatabase::class.java,
    ).allowMainThreadQueries().build()

    private val cache = ProductReadCache(database.productCacheDao(), database.cacheContextDao())

    private val account = UUID.fromString("11111111-1111-4111-8111-111111111111")
    private val space = UUID.fromString("22222222-2222-4222-8222-222222222222")
    private val resource = UUID.fromString("33333333-3333-4333-8333-333333333333")

    @After
    fun tearDown() {
        database.close()
    }

    @Test
    fun onNetworkSuccessReturnsFreshAndCaches() = runTest {
        val result = cache.loadWithFallback(
            accountId = account,
            spaceId = space,
            kind = ProductCacheKind.MEMORY,
            resourceId = resource,
            load = { "A day by the sea" },
            serialize = { it },
            deserialize = { it },
        )

        assertTrue(result.isSuccess)
        assertFalse(result.getOrThrow().fromCache)
        assertEquals("A day by the sea", result.getOrThrow().value)
    }

    @Test
    fun onIOExceptionFallsBackToTheCachedValue() = runTest {
        cache.loadWithFallback(
            accountId = account,
            spaceId = space,
            kind = ProductCacheKind.MEMORY,
            resourceId = resource,
            load = { "A day by the sea" },
            serialize = { it },
            deserialize = { it },
        )

        val result = cache.loadWithFallback(
            accountId = account,
            spaceId = space,
            kind = ProductCacheKind.MEMORY,
            resourceId = resource,
            load = { throw IOException("offline") },
            serialize = { it },
            deserialize = { it },
        )

        assertTrue(result.isSuccess)
        assertTrue(result.getOrThrow().fromCache)
        assertEquals("A day by the sea", result.getOrThrow().value)
    }

    @Test
    fun onA503FallsBackToTheCachedValue() = runTest {
        cache.loadWithFallback(
            accountId = account,
            spaceId = space,
            kind = ProductCacheKind.MEMORY,
            resourceId = resource,
            load = { "A day by the sea" },
            serialize = { it },
            deserialize = { it },
        )

        val result = cache.loadWithFallback(
            accountId = account,
            spaceId = space,
            kind = ProductCacheKind.MEMORY,
            resourceId = resource,
            load = { throw ReferenceApiException(code = null, message = "maintenance", status = 503) },
            serialize = { it },
            deserialize = { it },
        )

        assertTrue(result.getOrThrow().fromCache)
    }

    @Test
    fun aPlain500NeverFallsBackToTheCache() = runTest {
        cache.loadWithFallback(
            accountId = account,
            spaceId = space,
            kind = ProductCacheKind.MEMORY,
            resourceId = resource,
            load = { "A day by the sea" },
            serialize = { it },
            deserialize = { it },
        )

        val result = cache.loadWithFallback(
            accountId = account,
            spaceId = space,
            kind = ProductCacheKind.MEMORY,
            resourceId = resource,
            load = { throw ReferenceApiException(code = null, message = "bug", status = 500) },
            serialize = { it },
            deserialize = { it },
        )

        assertTrue(result.isFailure)
    }

    @Test
    fun a401NeverFallsBackToTheCacheEvenWithAFreshRow() = runTest {
        cache.loadWithFallback(
            accountId = account,
            spaceId = space,
            kind = ProductCacheKind.MEMORY,
            resourceId = resource,
            load = { "A day by the sea" },
            serialize = { it },
            deserialize = { it },
        )

        val result = cache.loadWithFallback(
            accountId = account,
            spaceId = space,
            kind = ProductCacheKind.MEMORY,
            resourceId = resource,
            load = { throw ReferenceApiException(code = "unauthenticated", message = "expired", status = 401) },
            serialize = { it },
            deserialize = { it },
        )

        assertTrue(result.isFailure)
    }

    @Test
    fun anExpiredRowIsNotUsedAndIsRemoved() = runTest {
        val staleTimestamp = System.currentTimeMillis() - 8L * 24 * 60 * 60 * 1000
        database.productCacheDao().put(
            ProductCacheEntity(
                cacheKey = "$account:$space:SPACE_SHARED:memory:$resource",
                accountId = account.toString(),
                spaceId = space.toString(),
                kind = "memory",
                resourceId = resource.toString(),
                payloadJson = "A day by the sea",
                refreshedAtEpochMs = staleTimestamp,
            ),
        )

        val result = cache.loadWithFallback(
            accountId = account,
            spaceId = space,
            kind = ProductCacheKind.MEMORY,
            resourceId = resource,
            load = { throw IOException("offline") },
            serialize = { it },
            deserialize = { it },
        )

        assertTrue(result.isFailure)
        assertEquals(null, database.productCacheDao().get("$account:$space:SPACE_SHARED:memory:$resource"))
    }

    @Test
    fun aRowThatCanNoLongerBePersistedIsRefusedOnReadToo() = runTest {
        // A HeartMoment that has since turned PRIVATE: canPersist must refuse
        // it symmetrically on the cache-read path, not only on write, so a
        // row written while it was still SHARED cannot outlive the transition.
        database.productCacheDao().put(
            ProductCacheEntity(
                cacheKey = "$account:$space:SPACE_SHARED:heartMoment:$resource",
                accountId = account.toString(),
                spaceId = space.toString(),
                kind = "heartMoment",
                resourceId = resource.toString(),
                payloadJson = "PRIVATE",
                refreshedAtEpochMs = System.currentTimeMillis(),
            ),
        )

        val result = cache.loadWithFallback(
            accountId = account,
            spaceId = space,
            kind = ProductCacheKind.HEART_MOMENT,
            resourceId = resource,
            canPersist = { visibility -> visibility == "SHARED" },
            load = { throw IOException("offline") },
            serialize = { it },
            deserialize = { it },
        )

        assertTrue(result.isFailure)
        assertEquals(null, database.productCacheDao().get("$account:$space:SPACE_SHARED:heartMoment:$resource"))
    }

    @Test
    fun clearAllRemovesEveryRowAndTheContextMarker() = runTest {
        cache.loadWithFallback(
            accountId = account,
            spaceId = space,
            kind = ProductCacheKind.MEMORY,
            resourceId = resource,
            load = { "A day by the sea" },
            serialize = { it },
            deserialize = { it },
        )

        cache.clearAll()

        val result = cache.loadWithFallback(
            accountId = account,
            spaceId = space,
            kind = ProductCacheKind.MEMORY,
            resourceId = resource,
            load = { throw IOException("offline") },
            serialize = { it },
            deserialize = { it },
        )
        assertTrue(result.isFailure)
    }

    @Test
    fun aDifferentSpaceWipesThePreviousSpacesCacheOnNextUse() = runTest {
        cache.loadWithFallback(
            accountId = account,
            spaceId = space,
            kind = ProductCacheKind.MEMORY,
            resourceId = resource,
            load = { "A day by the sea" },
            serialize = { it },
            deserialize = { it },
        )

        val otherSpace = UUID.fromString("44444444-4444-4444-8444-444444444444")
        // Any call under the new Space context — even for an unrelated
        // resource — must wipe the previous Space's rows first.
        cache.loadWithFallback(
            accountId = account,
            spaceId = otherSpace,
            kind = ProductCacheKind.MILESTONE,
            resourceId = UUID.randomUUID(),
            load = { throw IOException("offline") },
            serialize = { it },
            deserialize = { it },
        )

        val staleFromOldSpace = database.productCacheDao()
            .get("$account:$space:SPACE_SHARED:memory:$resource")
        assertEquals(null, staleFromOldSpace)
    }
}
