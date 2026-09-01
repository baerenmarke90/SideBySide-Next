package de.sidebyside.next.story

import de.sidebyside.next.reference.FakeReferenceContract
import de.sidebyside.next.reference.ReferenceApiException
import de.sidebyside.next.reference.ReferenceConfig
import de.sidebyside.next.reference.ReferenceContract
import de.sidebyside.next.reference.ReferenceViewModel
import de.sidebyside.next.shell.UiStateKind
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
import org.junit.Before
import org.junit.Test
import sidebyside.api.models.AccountMembershipView
import sidebyside.api.models.AccountView
import sidebyside.api.models.AuthorSummary
import sidebyside.api.models.CommentCreate
import sidebyside.api.models.CommentDetail
import sidebyside.api.models.CommentPage
import sidebyside.api.models.ContentVisibility
import sidebyside.api.models.HeartEmotion
import sidebyside.api.models.HeartMomentDetail
import sidebyside.api.models.MilestoneDetail
import sidebyside.api.models.MilestoneUpdate
import sidebyside.api.models.ResourceCapabilities
import sidebyside.api.models.SessionView
import sidebyside.api.models.StoryPage
import sidebyside.api.models.TokenView

private val SPACE: UUID = UUID.fromString("11111111-1111-4111-8111-111111111111")
private val MILESTONE: UUID = UUID.fromString("77777777-7777-4777-8777-777777777777")
private val MOMENT: UUID = UUID.fromString("88888888-8888-4888-8888-888888888888")

/**
 * The two Story kinds that had no screen.
 *
 * The comment paths are per kind in the contract, so what is most worth pinning
 * is that each screen reads under its own parent: asking under the wrong one
 * would quietly show another resource's thread.
 */
@OptIn(ExperimentalCoroutinesApi::class)
class StoryItemDetailTest {
    private val dispatcher = StandardTestDispatcher()

    @Before
    fun setUp() = Dispatchers.setMain(dispatcher)

    @After
    fun tearDown() = Dispatchers.resetMain()

    @Test
    fun opensAMilestoneWithTheVersionAChangeIsWrittenAgainst() = runTest(dispatcher) {
        val model = signedIn(DetailApi())

        model.openMilestone(MILESTONE)
        advanceUntilIdle()

        assertEquals(MILESTONE, model.uiState.value.openMilestone?.id)
        assertEquals(5, model.uiState.value.openMilestone?.version)
    }

    @Test
    fun readsAMilestoneThreadUnderTheMilestonePath() = runTest(dispatcher) {
        val api = DetailApi()
        val model = signedIn(api)

        model.loadComments(ReferenceContract.CommentParent.MILESTONE, MILESTONE)
        advanceUntilIdle()

        assertEquals(listOf(ReferenceContract.CommentParent.MILESTONE), api.commentParents)
        assertEquals(listOf(MILESTONE), api.commentParentIds)
    }

    @Test
    fun readsAHeartMomentThreadUnderTheHeartMomentPath() = runTest(dispatcher) {
        val api = DetailApi()
        val model = signedIn(api)

        model.loadComments(ReferenceContract.CommentParent.HEART_MOMENT, MOMENT)
        advanceUntilIdle()

        assertEquals(listOf(ReferenceContract.CommentParent.HEART_MOMENT), api.commentParents)
        assertEquals(listOf(MOMENT), api.commentParentIds)
    }

    @Test
    fun writesAMilestoneChangeAgainstTheVersionItWasMadeFrom() = runTest(dispatcher) {
        val api = DetailApi()
        val model = signedIn(api)

        model.openMilestone(MILESTONE)
        advanceUntilIdle()
        model.saveMilestone("Moved in together", "The day the boxes arrived", "2026-08-20")
        advanceUntilIdle()

        assertEquals(listOf(5), api.milestoneVersions)
        assertEquals(LocalDate.of(2026, 8, 20), api.milestoneUpdates.single().happenedOn)
        assertNull(model.uiState.value.memoryProblem)
    }

    @Test
    fun aMilestoneConflictIsReportedAndTheItemStaysOpen() = runTest(dispatcher) {
        val api = DetailApi(milestoneUpdateFailure = ReferenceApiException(null, "conflict", 409))
        val model = signedIn(api)

        model.openMilestone(MILESTONE)
        advanceUntilIdle()
        model.saveMilestone("Moved in together", "Text", "")
        advanceUntilIdle()

        assertEquals(UiStateKind.Conflict, model.uiState.value.memoryProblem?.kind)
        assertEquals(MILESTONE, model.uiState.value.openMilestone?.id)
    }

    @Test
    fun opensASharedHeartMomentFromTheStory() = runTest(dispatcher) {
        val model = signedIn(DetailApi())

        model.openSharedHeartMoment(MOMENT)
        advanceUntilIdle()

        assertEquals(MOMENT, model.uiState.value.openSharedHeartMoment?.id)
        assertEquals(
            ContentVisibility.SHARED,
            model.uiState.value.openSharedHeartMoment?.visibility,
        )
    }

    @Test
    fun aHeartMomentTheServerWillNotShowFailsAsARefusal() = runTest(dispatcher) {
        // A private moment is never in the Story the id came from, so reaching
        // one means the server refuses — and that must read as a refusal.
        val api = DetailApi(heartMomentFailure = ReferenceApiException(null, "gone", 404))
        val model = signedIn(api)

        model.openSharedHeartMoment(MOMENT)
        advanceUntilIdle()

        assertNull(model.uiState.value.openSharedHeartMoment)
        assertEquals(UiStateKind.Permission, model.uiState.value.memoryProblem?.kind)
    }

    @Test
    fun leavingAStoryItemForgetsIt() = runTest(dispatcher) {
        val model = signedIn(DetailApi())

        model.openMilestone(MILESTONE)
        advanceUntilIdle()
        model.closeStoryItem()

        assertNull(model.uiState.value.openMilestone)
        assertNull(model.uiState.value.openSharedHeartMoment)
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

private fun milestone(version: Int) = MilestoneDetail(
    author = AUTHOR,
    authorId = UUID.randomUUID(),
    body = "The day the boxes arrived",
    capabilities = CAPABILITIES,
    createdAt = OffsetDateTime.now(),
    happenedOn = LocalDate.of(2026, 8, 17),
    id = MILESTONE,
    spaceId = SPACE,
    title = "Moved in together",
    updatedAt = OffsetDateTime.now(),
    version = version,
)

private fun sharedMoment() = HeartMomentDetail(
    attachment = null,
    author = AUTHOR,
    authorId = UUID.randomUUID(),
    capabilities = CAPABILITIES,
    createdAt = OffsetDateTime.now(),
    emotion = HeartEmotion.GRATEFUL,
    happenedOn = LocalDate.of(2026, 8, 18),
    id = MOMENT,
    spaceId = SPACE,
    text = "Thank you for today",
    updatedAt = OffsetDateTime.now(),
    version = 1,
    visibility = ContentVisibility.SHARED,
)

private class DetailApi(
    private val milestoneUpdateFailure: Throwable? = null,
    private val heartMomentFailure: Throwable? = null,
) : FakeReferenceContract() {
    val commentParents = mutableListOf<ReferenceContract.CommentParent>()
    val commentParentIds = mutableListOf<UUID>()
    val milestoneUpdates = mutableListOf<MilestoneUpdate>()
    val milestoneVersions = mutableListOf<Int>()

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
    ): StoryPage =
        StoryPage(hasMore = false, items = emptyList(), nextCursor = null)

    override suspend fun getMilestone(
        spaceId: UUID,
        accessToken: String,
        milestoneId: UUID,
    ): MilestoneDetail = milestone(version = 5)

    override suspend fun updateMilestone(
        spaceId: UUID,
        accessToken: String,
        milestoneId: UUID,
        ifMatch: Int,
        update: MilestoneUpdate,
    ): MilestoneDetail {
        milestoneVersions += ifMatch
        milestoneUpdates += update
        milestoneUpdateFailure?.let { throw it }
        return milestone(version = ifMatch + 1)
    }

    override suspend fun getHeartMoment(
        spaceId: UUID,
        accessToken: String,
        heartMomentId: UUID,
    ): HeartMomentDetail {
        heartMomentFailure?.let { throw it }
        return sharedMoment()
    }

    override suspend fun listComments(
        spaceId: UUID,
        accessToken: String,
        parent: ReferenceContract.CommentParent,
        parentId: UUID,
        cursor: String?,
    ): CommentPage {
        commentParents += parent
        commentParentIds += parentId
        return CommentPage(hasMore = false, items = emptyList<CommentDetail>(), nextCursor = null)
    }

    override suspend fun createComment(
        spaceId: UUID,
        accessToken: String,
        parent: ReferenceContract.CommentParent,
        parentId: UUID,
        comment: CommentCreate,
    ): CommentDetail = error("not used")
}
