package de.sidebyside.next.cache

import androidx.room.Room
import androidx.test.core.app.ApplicationProvider
import de.sidebyside.next.reference.FakeReferenceContract
import de.sidebyside.next.reference.ReferenceApiException
import de.sidebyside.next.reference.ReferenceConfig
import de.sidebyside.next.reference.ReferenceContract
import de.sidebyside.next.reference.ReferenceViewModel
import java.io.IOException
import java.time.LocalDate
import java.time.OffsetDateTime
import java.util.UUID
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.ExperimentalCoroutinesApi
import kotlinx.coroutines.test.StandardTestDispatcher
import kotlinx.coroutines.test.TestScope
import kotlinx.coroutines.test.advanceUntilIdle
import kotlinx.coroutines.test.resetMain
import kotlinx.coroutines.test.runTest
import kotlinx.coroutines.test.setMain
import org.junit.After
import org.junit.Assert.assertEquals
import org.junit.Assert.assertNull
import org.junit.Assert.assertNotNull
import org.junit.Before
import org.junit.Test
import org.junit.runner.RunWith
import org.robolectric.RobolectricTestRunner
import org.robolectric.annotation.Config
import sidebyside.api.models.AccountMembershipView
import sidebyside.api.models.AccountView
import sidebyside.api.models.AuthorSummary
import sidebyside.api.models.MemoryDetail
import sidebyside.api.models.MemorySummary
import sidebyside.api.models.ResourceCapabilities
import sidebyside.api.models.SessionView
import sidebyside.api.models.StoryItem
import sidebyside.api.models.StoryMemoryItem
import sidebyside.api.models.StoryPage
import sidebyside.api.models.TokenView

private val SPACE: UUID = UUID.fromString("11111111-1111-4111-8111-111111111111")
private val OTHER_SPACE: UUID = UUID.fromString("55555555-5555-4555-8555-555555555555")
private val MEMORY: UUID = UUID.fromString("33333333-3333-4333-8333-333333333333")

/**
 * [ReferenceViewModel] wired to a real, Room-backed [ProductReadCache] —
 * the integration point `ProductReadCacheTest` alone cannot prove, since
 * that file exercises the cache directly rather than through a screen's
 * usual `openMemory`/`reloadMemory` path.
 */
@RunWith(RobolectricTestRunner::class)
@Config(sdk = [35])
@OptIn(ExperimentalCoroutinesApi::class)
class ProductReadCacheViewModelTest {
    private val dispatcher = StandardTestDispatcher()
    // A same-thread executor, not Room's default background thread pool: the
    // ViewModel's own coroutine runs on `Dispatchers.Main`, swapped to this
    // test's `StandardTestDispatcher` below, and `advanceUntilIdle()` only
    // pumps that dispatcher's own queue — a real background thread finishing
    // independently would race it. Room fully synchronous removes that race.
    private val database = Room.inMemoryDatabaseBuilder(
        ApplicationProvider.getApplicationContext(),
        ReadCacheDatabase::class.java,
    )
        .setQueryExecutor { it.run() }
        .setTransactionExecutor { it.run() }
        .allowMainThreadQueries()
        .build()
    private val cache = ProductReadCache(database.productCacheDao(), database.cacheContextDao())

    @Before
    fun setUp() = Dispatchers.setMain(dispatcher)

    @After
    fun tearDown() {
        Dispatchers.resetMain()
        database.close()
    }

    @Test
    fun aFreshNetworkReadCarriesNoCacheTimestamp() = runTest(dispatcher) {
        val model = signedIn(MemoryApi())

        model.openMemory(MEMORY)
        advanceUntilIdle()

        assertEquals(MEMORY, model.uiState.value.openMemory?.id)
        assertNull(model.uiState.value.openMemoryCachedAt)
    }

    @Test
    fun anOfflineReloadFallsBackToWhatWasCachedOnTheFirstSuccessfulRead() = runTest(dispatcher) {
        val api = MemoryApi()
        val model = signedIn(api)

        model.openMemory(MEMORY)
        advanceUntilIdle()

        api.nextFailure = IOException("offline")
        model.openMemory(MEMORY)
        advanceUntilIdle()

        assertEquals(MEMORY, model.uiState.value.openMemory?.id)
        assertNotNull(model.uiState.value.openMemoryCachedAt)
        // The fallback is silent, not an error state on top of the cached read.
        assertNull(model.uiState.value.memoryProblem)
    }

    @Test
    fun a401NeverFallsBackEvenWhenACachedRowExists() = runTest(dispatcher) {
        val api = MemoryApi()
        val model = signedIn(api)

        model.openMemory(MEMORY)
        advanceUntilIdle()

        api.nextFailure = ReferenceApiException(code = "unauthenticated", message = "expired", status = 401)
        model.openMemory(MEMORY)
        advanceUntilIdle()

        // The screen keeps showing the last-good memory while a background
        // reload fails, same as before any cache existed — what must not
        // happen is the 401 being silently swallowed by a cache fallback.
        assertNull(model.uiState.value.openMemoryCachedAt)
        assertNotNull(model.uiState.value.memoryProblem)
    }

    @Test
    fun logoutClearsThePersistentCacheNotJustTheInMemoryState() = runTest(dispatcher) {
        val api = MemoryApi()
        val model = signedIn(api)

        model.openMemory(MEMORY)
        advanceUntilIdle()

        model.logout()
        advanceUntilIdle()

        // A second account/session, same resource id: nothing from the first
        // account's cache may answer for it.
        model.signIn("someone.else@example.test", "secret")
        advanceUntilIdle()
        api.nextFailure = IOException("offline")
        model.openMemory(MEMORY)
        advanceUntilIdle()

        assertNull(model.uiState.value.openMemory)
        assertNull(model.uiState.value.openMemoryCachedAt)
    }

    @Test
    fun switchingSpaceAndBackNoLongerFindsTheOriginalSpacesCachedRow() = runTest(dispatcher) {
        // A different key (Space differs) would miss regardless of any wipe;
        // switching back to the original Space proves the wipe itself ran,
        // not merely that the two Spaces' keys never collided.
        val api = MemoryApi(otherSpace = OTHER_SPACE)
        val model = signedIn(api)

        model.openMemory(MEMORY)
        advanceUntilIdle()

        model.selectSpace(OTHER_SPACE)
        advanceUntilIdle()
        model.selectSpace(SPACE)
        advanceUntilIdle()

        api.nextFailure = IOException("offline")
        model.openMemory(MEMORY)
        advanceUntilIdle()

        // No row survived the two Space switches to fall back to, so the
        // IOException surfaces as an ordinary Offline problem instead.
        assertNull(model.uiState.value.openMemoryCachedAt)
        assertEquals(
            de.sidebyside.next.shell.UiStateKind.Offline,
            model.uiState.value.memoryProblem?.kind,
        )
    }

    @Test
    fun refreshStoryFallsBackToTheCachedTimelineOnceOffline() = runTest(dispatcher) {
        val api = StoryApi()
        // Signing in already runs one refreshStory() itself, which is the
        // first successful network read the fallback below builds on.
        val model = signedIn(api)
        assertEquals(1, model.uiState.value.storyItems.size)
        assertNull(model.uiState.value.storyCachedAt)

        api.nextFailure = IOException("offline")
        model.refreshStory()
        advanceUntilIdle()

        assertEquals(1, model.uiState.value.storyItems.size)
        assertNotNull(model.uiState.value.storyCachedAt)
        // No offline pagination: a cache fallback has no cursor to load more with.
        assertEquals(false, model.uiState.value.storyHasMore)
        assertNull(model.uiState.value.error)
    }

    @Test
    fun refreshStoryNeverFallsBackOnA401EvenWithACachedRow() = runTest(dispatcher) {
        val api = StoryApi()
        val model = signedIn(api)

        api.nextFailure = ReferenceApiException(code = "unauthenticated", message = "expired", status = 401)
        model.refreshStory()
        advanceUntilIdle()

        assertNull(model.uiState.value.storyCachedAt)
        assertNotNull(model.uiState.value.error)
    }

    private suspend fun TestScope.signedIn(api: ReferenceContract): ReferenceViewModel {
        val model = ReferenceViewModel(config = ReferenceConfig(BASE_URL), api = api, productReadCache = cache)
        model.signIn("someone@example.test", "secret")
        advanceUntilIdle()
        return model
    }
}

private const val BASE_URL = "https://sidebyside.example"

private fun memoryDetail() = MemoryDetail(
    attachments = emptyList(),
    author = AuthorSummary(displayName = "Lea", id = UUID.randomUUID()),
    authorId = UUID.randomUUID(),
    body = "The text as the server has it",
    capabilities = ResourceCapabilities(canComment = true, canDelete = true, canEdit = true),
    createdAt = OffsetDateTime.now(),
    happenedOn = LocalDate.of(2026, 8, 17),
    id = MEMORY,
    spaceId = SPACE,
    title = "The title as the server has it",
    updatedAt = OffsetDateTime.now(),
    version = 7,
)

private class MemoryApi(
    private val otherSpace: UUID? = null,
) : FakeReferenceContract() {
    var nextFailure: Throwable? = null

    override suspend fun signIn(email: String, password: String): SessionView = SessionView(
        account = AccountView(displayName = email, id = UUID.randomUUID()),
        tokens = TokenView(
            accessExpiresAt = OffsetDateTime.now(),
            accessToken = "access",
            refreshExpiresAt = OffsetDateTime.now(),
            refreshToken = "refresh",
        ),
    )

    override suspend fun listMemberships(accessToken: String): List<AccountMembershipView> =
        listOfNotNull(
            AccountMembershipView(role = "PARTNER", spaceId = SPACE, status = "ACTIVE"),
            otherSpace?.let { AccountMembershipView(role = "PARTNER", spaceId = it, status = "ACTIVE") },
        )

    override suspend fun getMemory(spaceId: UUID, accessToken: String, memoryId: UUID): MemoryDetail {
        nextFailure?.let {
            nextFailure = null
            throw it
        }
        return memoryDetail()
    }
}

private fun storyMemoryItem(): StoryItem = StoryItem.MemoryWrapper(
    StoryMemoryItem(
        effectiveDate = LocalDate.of(2026, 8, 17),
        kind = StoryMemoryItem.Kind.MEMORY,
        memory = MemorySummary(
            attachments = emptyList(),
            author = AuthorSummary(displayName = "Lea", id = UUID.randomUUID()),
            capabilities = ResourceCapabilities(canComment = true, canDelete = true, canEdit = true),
            createdAt = OffsetDateTime.now(),
            happenedOn = LocalDate.of(2026, 8, 17),
            id = MEMORY,
            title = "A day by the sea",
        ),
    ),
)

private class StoryApi : FakeReferenceContract() {
    var nextFailure: Throwable? = null

    override suspend fun signIn(email: String, password: String): SessionView = SessionView(
        account = AccountView(displayName = email, id = UUID.randomUUID()),
        tokens = TokenView(
            accessExpiresAt = OffsetDateTime.now(),
            accessToken = "access",
            refreshExpiresAt = OffsetDateTime.now(),
            refreshToken = "refresh",
        ),
    )

    override suspend fun listMemberships(accessToken: String): List<AccountMembershipView> =
        listOf(AccountMembershipView(role = "PARTNER", spaceId = SPACE, status = "ACTIVE"))

    override suspend fun getTimeline(spaceId: UUID, accessToken: String, cursor: String?): StoryPage {
        nextFailure?.let {
            nextFailure = null
            throw it
        }
        return StoryPage(hasMore = false, items = listOf(storyMemoryItem()), nextCursor = null)
    }
}
