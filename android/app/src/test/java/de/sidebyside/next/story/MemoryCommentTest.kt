package de.sidebyside.next.story

import de.sidebyside.next.reference.FakeReferenceContract
import de.sidebyside.next.reference.ReferenceApiException
import de.sidebyside.next.reference.ReferenceConfig
import de.sidebyside.next.reference.ReferenceContract
import de.sidebyside.next.reference.ReferenceViewModel
import de.sidebyside.next.shell.UiStateKind
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
import org.junit.Assert.assertNotNull
import org.junit.Assert.assertTrue
import org.junit.Before
import org.junit.Test
import sidebyside.api.models.AccountMembershipView
import sidebyside.api.models.AccountView
import sidebyside.api.models.AuthorSummary
import sidebyside.api.models.CommentCreate
import sidebyside.api.models.CommentDetail
import sidebyside.api.models.CommentPage
import sidebyside.api.models.CommentUpdate
import sidebyside.api.models.SessionView
import sidebyside.api.models.StoryPage
import sidebyside.api.models.TokenView

private val SPACE: UUID = UUID.fromString("11111111-1111-4111-8111-111111111111")
private val MEMORY: UUID = UUID.fromString("33333333-3333-4333-8333-333333333333")
private val COMMENT: UUID = UUID.fromString("55555555-5555-4555-8555-555555555555")
private val ME: UUID = UUID.fromString("66666666-6666-4666-8666-666666666666")

/**
 * Comments on a memory.
 *
 * A comment carries no `capabilities`, so whose it is decides only what the
 * screen offers. These tests pin that the account is known at all, that a
 * change is written against the version it was read at, and that a refusal
 * arrives as a refusal.
 */
@OptIn(ExperimentalCoroutinesApi::class)
class MemoryCommentTest {
    private val dispatcher = StandardTestDispatcher()

    @Before
    fun setUp() = Dispatchers.setMain(dispatcher)

    @After
    fun tearDown() = Dispatchers.resetMain()

    @Test
    fun knowsWhichAccountIsSignedInSoAuthorshipCanBeTold() = runTest(dispatcher) {
        // Without this there is no signal at all for whose comment it is.
        val model = signedIn(CommentApi())

        assertEquals(ME, model.uiState.value.accountId)
    }

    @Test
    fun readsTheThreadForTheOpenMemory() = runTest(dispatcher) {
        val api = CommentApi(thread = listOf(commentBy(ME, "It was lovely")))
        val model = signedIn(api)

        model.loadComments(PARENT, MEMORY)
        advanceUntilIdle()

        assertEquals(1, model.uiState.value.comments.size)
        assertEquals(listOf(MEMORY), api.listedFor)
        // The contract has one path per kind; asking under the wrong one would
        // read a different resource's thread.
        assertEquals(listOf(ReferenceContract.CommentParent.MEMORY), api.listedParents)
    }

    @Test
    fun writesACommentAndRereadsTheThread() = runTest(dispatcher) {
        val api = CommentApi()
        val model = signedIn(api)

        model.addComment(PARENT, MEMORY, "A thought about this")
        advanceUntilIdle()

        assertEquals("A thought about this", api.created.single().body)
        // Re-read rather than appended locally, so the thread matches the server.
        assertTrue(api.listedFor.isNotEmpty())
    }

    @Test
    fun refusesAnEmptyCommentWithoutSendingAnything() = runTest(dispatcher) {
        val api = CommentApi()
        val model = signedIn(api)

        model.addComment(PARENT, MEMORY, "   ")
        advanceUntilIdle()

        assertTrue(api.created.isEmpty())
    }

    @Test
    fun changesACommentAgainstTheVersionItWasReadAt() = runTest(dispatcher) {
        val api = CommentApi(thread = listOf(commentBy(ME, "First like this", version = 4)))
        val model = signedIn(api)

        model.loadComments(PARENT, MEMORY)
        advanceUntilIdle()
        model.editComment(PARENT, MEMORY, COMMENT, "Then like that")
        advanceUntilIdle()

        assertEquals(listOf(4), api.updateVersions)
        assertEquals("Then like that", api.updates.single().body)
    }

    @Test
    fun aRefusalFromTheServerArrivesAsARefusal() = runTest(dispatcher) {
        // Authorship is a display hint. When the client offers something the
        // server will not allow, the answer must read as a refusal.
        val api = CommentApi(
            thread = listOf(commentBy(UUID.randomUUID(), "Not mine")),
            updateFailure = ReferenceApiException(null, "forbidden", 403),
        )
        val model = signedIn(api)

        model.loadComments(PARENT, MEMORY)
        advanceUntilIdle()
        model.editComment(PARENT, MEMORY, COMMENT, "Mine now")
        advanceUntilIdle()

        assertEquals(UiStateKind.Permission, model.uiState.value.commentsProblem?.kind)
    }

    @Test
    fun reportsAConflictRatherThanOverwriting() = runTest(dispatcher) {
        val api = CommentApi(
            thread = listOf(commentBy(ME, "First like this")),
            updateFailure = ReferenceApiException(null, "conflict", 409),
        )
        val model = signedIn(api)

        model.loadComments(PARENT, MEMORY)
        advanceUntilIdle()
        model.editComment(PARENT, MEMORY, COMMENT, "Then like that")
        advanceUntilIdle()

        assertEquals(UiStateKind.Conflict, model.uiState.value.commentsProblem?.kind)
    }

    @Test
    fun removesACommentAndRereadsTheThread() = runTest(dispatcher) {
        val api = CommentApi(thread = listOf(commentBy(ME, "Away with it", version = 2)))
        val model = signedIn(api)

        model.loadComments(PARENT, MEMORY)
        advanceUntilIdle()
        val readsBefore = api.listedFor.size
        model.removeComment(PARENT, MEMORY, COMMENT)
        advanceUntilIdle()

        assertEquals(listOf(2), api.deleteVersions)
        assertTrue(api.listedFor.size > readsBefore)
    }

    @Test
    fun forgetsTheThreadWhenTheSessionEnds() = runTest(dispatcher) {
        val api = CommentApi(thread = listOf(commentBy(ME, "Does not stay")))
        val model = signedIn(api)

        model.loadComments(PARENT, MEMORY)
        advanceUntilIdle()
        assertNotNull(model.uiState.value.comments.firstOrNull())

        model.logout()

        assertTrue(model.uiState.value.comments.isEmpty())
    }

    private fun TestScope.signedIn(api: ReferenceContract): ReferenceViewModel {
        val model = ReferenceViewModel(config = ReferenceConfig(BASE_URL), api = api)
        model.signIn("someone@example.test", "secret")
        advanceUntilIdle()
        return model
    }
}

private const val BASE_URL = "https://sidebyside.example"
private val PARENT = ReferenceContract.CommentParent.MEMORY

private fun commentBy(authorId: UUID, body: String, version: Int = 1) = CommentDetail(
    author = AuthorSummary(displayName = "Lea", id = authorId),
    authorId = authorId,
    body = body,
    createdAt = OffsetDateTime.now(),
    id = COMMENT,
    spaceId = SPACE,
    updatedAt = OffsetDateTime.now(),
    version = version,
)

private class CommentApi(
    private val thread: List<CommentDetail> = emptyList(),
    private val updateFailure: Throwable? = null,
) : FakeReferenceContract() {
    val listedFor = mutableListOf<UUID>()
    val listedParents = mutableListOf<ReferenceContract.CommentParent>()
    val created = mutableListOf<CommentCreate>()
    val updates = mutableListOf<CommentUpdate>()
    val updateVersions = mutableListOf<Int>()
    val deleteVersions = mutableListOf<Int>()

    override suspend fun signIn(email: String, password: String): SessionView = SessionView(
        account = AccountView(displayName = "Lea", id = ME),
        tokens = TokenView(
            accessExpiresAt = OffsetDateTime.now(),
            accessToken = "access",
            refreshExpiresAt = OffsetDateTime.now(),
            refreshToken = "refresh",
        ),
    )

    override suspend fun listMemberships(accessToken: String): List<AccountMembershipView> =
        listOf(AccountMembershipView(role = "PARTNER", spaceId = SPACE, status = "ACTIVE"))

    override suspend fun getTimeline(spaceId: UUID, accessToken: String): StoryPage =
        StoryPage(hasMore = false, items = emptyList(), nextCursor = null)

    override suspend fun listComments(
        spaceId: UUID,
        accessToken: String,
        parent: ReferenceContract.CommentParent,
        parentId: UUID,
    ): CommentPage {
        listedParents += parent
        listedFor += parentId
        return CommentPage(hasMore = false, items = thread, nextCursor = null)
    }

    override suspend fun createComment(
        spaceId: UUID,
        accessToken: String,
        parent: ReferenceContract.CommentParent,
        parentId: UUID,
        comment: CommentCreate,
    ): CommentDetail {
        created += comment
        return commentBy(ME, comment.body)
    }

    override suspend fun updateComment(
        spaceId: UUID,
        accessToken: String,
        commentId: UUID,
        ifMatch: Int,
        update: CommentUpdate,
    ): CommentDetail {
        updateVersions += ifMatch
        updates += update
        updateFailure?.let { throw it }
        return commentBy(ME, update.body, version = ifMatch + 1)
    }

    override suspend fun deleteComment(
        spaceId: UUID,
        accessToken: String,
        commentId: UUID,
        ifMatch: Int,
    ) {
        deleteVersions += ifMatch
    }
}
