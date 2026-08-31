package de.sidebyside.next.story

import java.util.UUID
import java.util.concurrent.atomic.AtomicInteger
import kotlinx.coroutines.CompletableDeferred
import kotlinx.coroutines.ExperimentalCoroutinesApi
import kotlinx.coroutines.async
import kotlinx.coroutines.test.advanceUntilIdle
import kotlinx.coroutines.test.runTest
import org.junit.Assert.assertEquals
import org.junit.Assert.assertNull
import org.junit.Assert.assertTrue
import org.junit.Test
import sidebyside.api.models.AttachmentReadRequest

/**
 * The Story image cache sits between a couple's private photographs and the
 * screen. These tests pin the properties that make that safe: nothing outlives
 * the Space it belongs to, and nothing grows without bound.
 */
@OptIn(ExperimentalCoroutinesApi::class)
class StoryImageStoreTest {
    @Test
    fun readsAnImageOnceAndThenServesItFromMemory() = runTest {
        val reads = AtomicInteger()
        val ref = imageRef()
        val store = StoryImageStore(scope = this) { reads.incrementAndGet(); bytes(8) }

        val first = store.image(ref)
        val second = store.image(ref)
        advanceUntilIdle()

        assertEquals(1, reads.get())
        assertTrue(first.contentEquals(second))
    }

    @Test
    fun sharesOneReadBetweenSimultaneousRequests() = runTest {
        // The same photograph can appear twice in one Story. Fetching it twice
        // would double the traffic and the memory for no gain.
        val reads = AtomicInteger()
        val release = CompletableDeferred<Unit>()
        val ref = imageRef()
        val store = StoryImageStore(scope = this) {
            reads.incrementAndGet()
            release.await()
            bytes(8)
        }

        val first = async { store.image(ref) }
        val second = async { store.image(ref) }
        advanceUntilIdle()
        release.complete(Unit)

        assertTrue(first.await().contentEquals(second.await()))
        assertEquals(1, reads.get())
    }

    @Test
    fun aFailedReadIsAPlaceholderRatherThanAnException() = runTest {
        // One unreadable photograph must not take down the entry around it.
        val store = StoryImageStore(scope = this) { error("the read failed") }

        assertNull(store.image(imageRef()))
    }

    @Test
    fun forgetsEverythingWhenTheSpaceChanges() = runTest {
        val reads = AtomicInteger()
        val ref = imageRef()
        val store = StoryImageStore(scope = this) { reads.incrementAndGet(); bytes(8) }

        store.image(ref)
        advanceUntilIdle()
        store.reset()
        store.image(ref)
        advanceUntilIdle()

        // Read again rather than served from a cache filled in another Space.
        assertEquals(2, reads.get())
        assertEquals(0, StoryImageStore(scope = this) { bytes(1) }.cachedBytesForTest())
    }

    @Test
    fun aReadStillInFlightWhenTheSpaceChangesIsDiscarded() = runTest {
        // The dangerous case: bytes arriving after the couple has left the
        // Space they were requested from.
        val release = CompletableDeferred<Unit>()
        val store = StoryImageStore(scope = this) { release.await(); bytes(8) }

        val pending = async { store.image(imageRef()) }
        advanceUntilIdle()
        store.reset()
        release.complete(Unit)
        advanceUntilIdle()

        assertNull(pending.await())
        assertEquals(0, store.cachedBytesForTest())
    }

    @Test
    fun dropsTheOldestImagesRatherThanGrowingPastItsBudget() = runTest {
        val store = StoryImageStore(scope = this, budgetBytes = 100) { bytes(40) }

        repeat(4) { store.image(imageRef()); advanceUntilIdle() }

        assertTrue(store.cachedBytesForTest() <= 100)
    }

    @Test
    fun servesAnOversizedImageWithoutKeepingIt() = runTest {
        // Caching it would evict everything else and still not fit.
        val store = StoryImageStore(scope = this, budgetBytes = 10) { bytes(64) }

        val image = store.image(imageRef())

        assertEquals(64, image?.size)
        assertEquals(0, store.cachedBytesForTest())
    }
}

private fun bytes(size: Int) = ByteArray(size) { 1 }

private fun imageRef() = StoryImageRef(
    attachmentId = UUID.randomUUID(),
    parentId = UUID.randomUUID(),
    parentType = AttachmentReadRequest.ParentType.MEMORY,
)
