package de.sidebyside.next.story

import de.sidebyside.next.reference.FakeReferenceContract
import de.sidebyside.next.reference.ReferenceConfig
import de.sidebyside.next.reference.ReferenceContract
import de.sidebyside.next.reference.ReferenceViewModel
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
import org.junit.Assert.assertFalse
import org.junit.Assert.assertTrue
import org.junit.Before
import org.junit.Test
import sidebyside.api.models.AccountMembershipView
import sidebyside.api.models.AccountView
import sidebyside.api.models.AuthorSummary
import sidebyside.api.models.CommentDetail
import sidebyside.api.models.CommentPage
import sidebyside.api.models.MemorySummary
import sidebyside.api.models.ResourceCapabilities
import sidebyside.api.models.SessionView
import sidebyside.api.models.StoryItem
import sidebyside.api.models.StoryMemoryItem
import sidebyside.api.models.StoryPage
import sidebyside.api.models.TokenView

private val SPACE: UUID = UUID.fromString("11111111-1111-4111-8111-111111111111")
private val MEMORY: UUID = UUID.fromString("33333333-3333-4333-8333-333333333333")

/**
 * Reading past the first page.
 *
 * Without this a couple's history simply stops, and nothing on screen says so —
 * which is the quietest kind of loss a client can inflict.
 */
@OptIn(ExperimentalCoroutinesApi::class)
class StoryPagingTest {
    private val dispatcher = StandardTestDispatcher()

    @Before
    fun setUp() = Dispatchers.setMain(dispatcher)

    @After
    fun tearDown() = Dispatchers.resetMain()

    @Test
    fun knowsThereIsMoreStoryThanItHasLoaded() = runTest(dispatcher) {
        val api = PagingApi(pages = listOf(page(2, more = true, cursor = "p2")))
        val model = signedIn(api)

        assertTrue(model.uiState.value.storyHasMore)
    }

    @Test
    fun appendsTheNextPageInsteadOfReplacingWhatIsThere() = runTest(dispatcher) {
        // Replacing would drop what the couple already scrolled past.
        val api = PagingApi(
            pages = listOf(
                page(2, more = true, cursor = "p2"),
                page(3, more = false, cursor = null),
            ),
        )
        // Signing in already reads the first page.
        val model = signedIn(api)

        model.loadMoreStory()
        advanceUntilIdle()

        assertEquals(5, model.uiState.value.storyItems.size)
        assertFalse(model.uiState.value.storyHasMore)
    }

    @Test
    fun continuesFromTheCursorTheServerGave() = runTest(dispatcher) {
        val api = PagingApi(pages = listOf(page(1, more = true, cursor = "opaque-cursor")))
        // Signing in already reads the first page.
        val model = signedIn(api)

        model.loadMoreStory()
        advanceUntilIdle()

        // The first read has no cursor; the second carries the server's own.
        assertEquals(listOf(null, "opaque-cursor"), api.timelineCursors)
    }

    @Test
    fun doesNotStartASecondPageWhileOneIsRunning() = runTest(dispatcher) {
        val api = PagingApi(pages = listOf(page(1, more = true, cursor = "p2")))
        // Signing in already reads the first page.
        val model = signedIn(api)

        model.loadMoreStory()
        model.loadMoreStory()
        advanceUntilIdle()

        assertEquals(2, api.timelineCursors.size)
    }

    @Test
    fun aCommentThreadAlsoContinues() = runTest(dispatcher) {
        val api = PagingApi(
            pages = listOf(page(1, more = false, cursor = null)),
            commentCursor = "c2",
        )
        val model = signedIn(api)

        model.loadComments(ReferenceContract.CommentParent.MEMORY, MEMORY)
        advanceUntilIdle()
        assertTrue(model.uiState.value.commentsHaveMore)

        model.loadMoreComments(ReferenceContract.CommentParent.MEMORY, MEMORY)
        advanceUntilIdle()

        assertEquals(listOf(null, "c2"), api.commentCursors)
        assertEquals(2, model.uiState.value.comments.size)
    }

    private fun TestScope.signedIn(api: ReferenceContract): ReferenceViewModel {
        val model = ReferenceViewModel(config = ReferenceConfig(BASE_URL), api = api)
        model.signIn("someone@example.test", "secret")
        advanceUntilIdle()
        return model
    }
}

private const val BASE_URL = "https://sidebyside.example"
private val CAPABILITIES = ResourceCapabilities(canComment = true, canDelete = true, canEdit = true)
private val AUTHOR = AuthorSummary(displayName = "Lea", id = UUID.randomUUID())

private fun page(count: Int, more: Boolean, cursor: String?) = StoryPage(
    hasMore = more,
    items = List(count) { storyItem() },
    nextCursor = cursor,
)

private fun storyItem(): StoryItem = StoryItem.MemoryWrapper(
    StoryMemoryItem(
        effectiveDate = LocalDate.of(2026, 8, 20),
        kind = StoryMemoryItem.Kind.MEMORY,
        memory = MemorySummary(
            attachments = emptyList(),
            author = AUTHOR,
            capabilities = CAPABILITIES,
            createdAt = OffsetDateTime.now(),
            happenedOn = LocalDate.of(2026, 8, 20),
            id = UUID.randomUUID(),
            title = "A day by the sea",
        ),
    ),
)

private fun aComment() = CommentDetail(
    author = AUTHOR,
    authorId = UUID.randomUUID(),
    body = "Lovely",
    createdAt = OffsetDateTime.now(),
    id = UUID.randomUUID(),
    spaceId = SPACE,
    updatedAt = OffsetDateTime.now(),
    version = 1,
)

private class PagingApi(
    private val pages: List<StoryPage>,
    private val commentCursor: String? = null,
) : FakeReferenceContract() {
    val timelineCursors = mutableListOf<String?>()
    val commentCursors = mutableListOf<String?>()

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

    override suspend fun getTimeline(
        spaceId: UUID,
        accessToken: String,
        cursor: String?,
    ): StoryPage {
        val index = timelineCursors.size.coerceAtMost(pages.lastIndex)
        timelineCursors += cursor
        return pages[index]
    }

    override suspend fun listComments(
        spaceId: UUID,
        accessToken: String,
        parent: ReferenceContract.CommentParent,
        parentId: UUID,
        cursor: String?,
    ): CommentPage {
        val first = commentCursors.isEmpty()
        commentCursors += cursor
        return CommentPage(
            hasMore = first && commentCursor != null,
            items = listOf(aComment()),
            nextCursor = if (first) commentCursor else null,
        )
    }
}
