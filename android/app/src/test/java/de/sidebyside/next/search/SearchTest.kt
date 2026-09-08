package de.sidebyside.next.search

import de.sidebyside.next.reference.FakeReferenceContract
import de.sidebyside.next.reference.ReferenceConfig
import de.sidebyside.next.reference.ReferenceViewModel
import java.time.OffsetDateTime
import java.util.UUID
import kotlinx.coroutines.CompletableDeferred
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.ExperimentalCoroutinesApi
import kotlinx.coroutines.test.StandardTestDispatcher
import kotlinx.coroutines.test.TestScope
import kotlinx.coroutines.test.advanceUntilIdle
import kotlinx.coroutines.test.resetMain
import kotlinx.coroutines.test.runCurrent
import kotlinx.coroutines.test.runTest
import kotlinx.coroutines.test.setMain
import org.junit.After
import org.junit.Assert.assertEquals
import org.junit.Assert.assertTrue
import org.junit.Before
import org.junit.Test
import sidebyside.api.models.AccountMembershipView
import sidebyside.api.models.AccountView
import sidebyside.api.models.SearchKind
import sidebyside.api.models.SearchPage
import sidebyside.api.models.SearchResult
import sidebyside.api.models.SearchScope
import sidebyside.api.models.SessionView
import sidebyside.api.models.TokenView

private val SPACE: UUID = UUID.fromString("11111111-1111-4111-8111-111111111111")

/**
 * #357: global Search. The server already restricts a result set to shared
 * Space content plus the caller's own private content — the client sends
 * only the query, never a scope, so it cannot accidentally widen that.
 */
@OptIn(ExperimentalCoroutinesApi::class)
class SearchTest {
    private val dispatcher = StandardTestDispatcher()

    @Before
    fun setUp() = Dispatchers.setMain(dispatcher)

    @After
    fun tearDown() = Dispatchers.resetMain()

    @Test
    fun searchingWithABlankQueryMakesNoCallAndClearsResults() = runTest(dispatcher) {
        val result = searchResult("A day by the sea")
        val api = SearchApi(results = listOf(result))
        val model = ReferenceViewModel(config = ReferenceConfig(BASE_URL), api = api)

        signIn(model)
        model.search("sea")
        advanceUntilIdle()
        assertTrue(model.uiState.value.searchResults.isNotEmpty())

        model.search("   ")
        advanceUntilIdle()

        assertTrue(model.uiState.value.searchResults.isEmpty())
        assertEquals(1, api.queriesSeen.size)
    }

    @Test
    fun searchingSendsTheTrimmedQueryAndPopulatesResults() = runTest(dispatcher) {
        val result = searchResult("A day by the sea")
        val api = SearchApi(results = listOf(result))
        val model = ReferenceViewModel(config = ReferenceConfig(BASE_URL), api = api)

        signIn(model)
        model.search("  sea  ")
        advanceUntilIdle()

        assertEquals(listOf("sea"), api.queriesSeen)
        assertEquals(listOf(result), model.uiState.value.searchResults)
    }

    @Test
    fun forgetsSearchResultsWhenTheSessionEnds() = runTest(dispatcher) {
        val api = SearchApi(results = listOf(searchResult("A day by the sea")))
        val model = ReferenceViewModel(config = ReferenceConfig(BASE_URL), api = api)

        signIn(model)
        model.search("sea")
        advanceUntilIdle()
        assertTrue(model.uiState.value.searchResults.isNotEmpty())

        model.logout()

        assertTrue(model.uiState.value.searchResults.isEmpty())
    }

    @Test
    fun searchingWithAKindSendsItAlongTheQuery() = runTest(dispatcher) {
        val api = SearchApi(results = listOf(searchResult("A day by the sea")))
        val model = ReferenceViewModel(config = ReferenceConfig(BASE_URL), api = api)

        signIn(model)
        model.search("sea", SearchKind.GIFT_IDEA)
        advanceUntilIdle()

        assertEquals(listOf(SearchKind.GIFT_IDEA), api.kindsSeen)
    }

    @Test
    fun loadingMoreRepeatsTheSameQueryAndKindWithTheNewCursor() = runTest(dispatcher) {
        val first = SearchPage(items = listOf(searchResult("A day by the sea")), nextCursor = "page-2")
        val second = SearchPage(items = listOf(searchResult("A second find")), nextCursor = null)
        val api = SearchApi(pages = listOf(first, second))
        val model = ReferenceViewModel(config = ReferenceConfig(BASE_URL), api = api)

        signIn(model)
        model.search("sea", SearchKind.MEMORY)
        advanceUntilIdle()
        assertTrue(model.uiState.value.searchHasMore)

        model.loadMoreSearch()
        advanceUntilIdle()

        assertEquals(listOf("sea", "sea"), api.queriesSeen)
        assertEquals(listOf(SearchKind.MEMORY, SearchKind.MEMORY), api.kindsSeen)
        assertEquals(listOf(null, "page-2"), api.cursorsSeen)
        assertEquals(2, model.uiState.value.searchResults.size)
        assertTrue(!model.uiState.value.searchHasMore)
    }

    @Test
    fun staleFirstPageFromOlderKindCannotReplaceNewerSearch() = runTest(dispatcher) {
        val api = ControllableSearchApi()
        val model = ReferenceViewModel(config = ReferenceConfig(BASE_URL), api = api)
        val currentResult = searchResult("A gift by the sea")

        signIn(model)
        model.search("sea", SearchKind.MEMORY)
        runCurrent()
        val staleFirstPage = api.calls.single()

        model.search("sea", SearchKind.GIFT_IDEA)
        runCurrent()
        val currentFirstPage = api.calls.last()
        currentFirstPage.response.complete(
            SearchPage(items = listOf(currentResult), nextCursor = "gift-page-2"),
        )
        runCurrent()

        assertEquals(listOf(currentResult), model.uiState.value.searchResults)
        assertTrue(model.uiState.value.searchHasMore)

        staleFirstPage.response.complete(
            SearchPage(items = listOf(searchResult("Old memory result")), nextCursor = null),
        )
        advanceUntilIdle()

        assertEquals(listOf(currentResult), model.uiState.value.searchResults)
        assertTrue(model.uiState.value.searchHasMore)

        model.loadMoreSearch()
        runCurrent()
        val currentPagination = api.calls.last()
        assertEquals("sea", currentPagination.query)
        assertEquals(SearchKind.GIFT_IDEA, currentPagination.kind)
        assertEquals("gift-page-2", currentPagination.cursor)
        currentPagination.response.complete(SearchPage(items = emptyList(), nextCursor = null))
        advanceUntilIdle()
    }

    @Test
    fun staleLoadMoreIsIgnoredWhenItFinishesBeforeNewFirstPage() = runTest(dispatcher) {
        val api = ControllableSearchApi()
        val model = ReferenceViewModel(config = ReferenceConfig(BASE_URL), api = api)
        val oldFirst = searchResult("Old first page")
        val newFirst = searchResult("New first page")

        signIn(model)
        model.search("old")
        runCurrent()
        api.calls[0].response.complete(
            SearchPage(items = listOf(oldFirst), nextCursor = "old-page-2"),
        )
        advanceUntilIdle()

        model.loadMoreSearch()
        runCurrent()
        val staleLoadMore = api.calls[1]
        model.search("new")
        runCurrent()
        val currentFirstPage = api.calls[2]

        staleLoadMore.response.complete(
            SearchPage(items = listOf(searchResult("Old second page")), nextCursor = null),
        )
        runCurrent()

        assertEquals(listOf(oldFirst), model.uiState.value.searchResults)
        assertTrue(model.uiState.value.searchBusy)
        assertTrue(!model.uiState.value.searchHasMore)
        assertTrue(!model.uiState.value.searchLoadingMore)

        currentFirstPage.response.complete(
            SearchPage(items = listOf(newFirst), nextCursor = "new-page-2"),
        )
        advanceUntilIdle()

        assertEquals(listOf(newFirst), model.uiState.value.searchResults)
        assertTrue(model.uiState.value.searchHasMore)
    }

    @Test
    fun staleLoadMoreIsIgnoredWhenNewFirstPageFinishesFirst() = runTest(dispatcher) {
        val api = ControllableSearchApi()
        val model = ReferenceViewModel(config = ReferenceConfig(BASE_URL), api = api)
        val oldFirst = searchResult("Old first page")
        val newFirst = searchResult("New first page")

        signIn(model)
        model.search("old")
        runCurrent()
        api.calls[0].response.complete(
            SearchPage(items = listOf(oldFirst), nextCursor = "old-page-2"),
        )
        advanceUntilIdle()

        model.loadMoreSearch()
        runCurrent()
        val staleLoadMore = api.calls[1]
        model.search("new")
        runCurrent()
        val currentFirstPage = api.calls[2]
        currentFirstPage.response.complete(
            SearchPage(items = listOf(newFirst), nextCursor = "new-page-2"),
        )
        runCurrent()

        assertEquals(listOf(newFirst), model.uiState.value.searchResults)
        assertTrue(model.uiState.value.searchHasMore)

        staleLoadMore.response.complete(
            SearchPage(items = listOf(searchResult("Old second page")), nextCursor = null),
        )
        advanceUntilIdle()

        assertEquals(listOf(newFirst), model.uiState.value.searchResults)
        assertTrue(model.uiState.value.searchHasMore)

        model.loadMoreSearch()
        runCurrent()
        val currentPagination = api.calls.last()
        assertEquals("new-page-2", currentPagination.cursor)
        currentPagination.response.complete(SearchPage(items = emptyList(), nextCursor = null))
        advanceUntilIdle()
    }

    @Test
    fun aResultPageWithoutANextCursorReportsNoMore() = runTest(dispatcher) {
        val api = SearchApi(results = listOf(searchResult("A day by the sea")))
        val model = ReferenceViewModel(config = ReferenceConfig(BASE_URL), api = api)

        signIn(model)
        model.search("sea")
        advanceUntilIdle()

        assertTrue(!model.uiState.value.searchHasMore)
    }

    private suspend fun TestScope.signIn(model: ReferenceViewModel) {
        model.signIn("someone@example.test", "secret")
        advanceUntilIdle()
    }
}

private const val BASE_URL = "https://sidebyside.example"

private fun searchResult(title: String) = SearchResult(
    excerpt = null,
    id = UUID.randomUUID(),
    occurredOn = null,
    parentId = null,
    scope = SearchScope.SHARED,
    title = title,
    type = SearchKind.MEMORY,
)

private data class PendingSearchCall(
    val query: String,
    val kind: SearchKind?,
    val cursor: String?,
    val response: CompletableDeferred<SearchPage>,
)

private class ControllableSearchApi : FakeReferenceContract() {
    val calls = mutableListOf<PendingSearchCall>()

    override suspend fun signIn(email: String, password: String): SessionView = SessionView(
        account = AccountView(displayName = "Lea", id = UUID.randomUUID()),
        tokens = TokenView(
            accessExpiresAt = OffsetDateTime.now(),
            accessToken = "access",
            refreshExpiresAt = OffsetDateTime.now(),
            refreshToken = "refresh",
        ),
    )

    override suspend fun listMemberships(accessToken: String): List<AccountMembershipView> =
        listOf(AccountMembershipView(role = "PARTNER", spaceId = SPACE, status = "ACTIVE"))

    override suspend fun search(
        spaceId: UUID,
        accessToken: String,
        query: String,
        kind: SearchKind?,
        cursor: String?,
    ): SearchPage {
        val response = CompletableDeferred<SearchPage>()
        calls += PendingSearchCall(query = query, kind = kind, cursor = cursor, response = response)
        return response.await()
    }
}

private class SearchApi(
    private val results: List<SearchResult> = emptyList(),
    private val pages: List<SearchPage>? = null,
) : FakeReferenceContract() {
    val queriesSeen = mutableListOf<String>()
    val kindsSeen = mutableListOf<SearchKind?>()
    val cursorsSeen = mutableListOf<String?>()
    private var pageIndex = 0

    override suspend fun signIn(email: String, password: String): SessionView = SessionView(
        account = AccountView(displayName = "Lea", id = UUID.randomUUID()),
        tokens = TokenView(
            accessExpiresAt = OffsetDateTime.now(),
            accessToken = "access",
            refreshExpiresAt = OffsetDateTime.now(),
            refreshToken = "refresh",
        ),
    )

    override suspend fun listMemberships(accessToken: String): List<AccountMembershipView> =
        listOf(AccountMembershipView(role = "PARTNER", spaceId = SPACE, status = "ACTIVE"))

    override suspend fun search(
        spaceId: UUID,
        accessToken: String,
        query: String,
        kind: SearchKind?,
        cursor: String?,
    ): SearchPage {
        queriesSeen += query
        kindsSeen += kind
        cursorsSeen += cursor
        pages?.let { return it[pageIndex++] }
        return SearchPage(items = results, nextCursor = null)
    }
}
