package de.sidebyside.next.search

import de.sidebyside.next.reference.FakeReferenceContract
import de.sidebyside.next.reference.ReferenceConfig
import de.sidebyside.next.reference.ReferenceViewModel
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

private class SearchApi(
    private val results: List<SearchResult> = emptyList(),
) : FakeReferenceContract() {
    val queriesSeen = mutableListOf<String>()

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

    override suspend fun search(spaceId: UUID, accessToken: String, query: String, cursor: String?): SearchPage {
        queriesSeen += query
        return SearchPage(items = results, nextCursor = null)
    }
}
