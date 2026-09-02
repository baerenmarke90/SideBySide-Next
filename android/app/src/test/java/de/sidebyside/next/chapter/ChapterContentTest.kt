package de.sidebyside.next.chapter

import de.sidebyside.next.place.RelationTargetItem
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
import sidebyside.api.models.ChapterContent
import sidebyside.api.models.ChapterContentItem
import sidebyside.api.models.MemorySummary
import sidebyside.api.models.MilestoneSummary
import sidebyside.api.models.ResourceCapabilities
import sidebyside.api.models.SessionView
import sidebyside.api.models.StoryItem
import sidebyside.api.models.StoryMemoryItem
import sidebyside.api.models.StoryMilestoneItem
import sidebyside.api.models.StoryPage
import sidebyside.api.models.TokenView

private val SPACE: UUID = UUID.fromString("11111111-1111-4111-8111-111111111111")
private val CHAPTER: UUID = UUID.fromString("33333333-3333-4333-8333-333333333333")

/**
 * #355: a chapter's typed content relations. The property worth pinning
 * beyond ordinary link/unlink is the same one #532 pinned for Place: the
 * timeline is the sole source of both id and label, so a private
 * HeartMoment can never surface here even if a linked id points at one —
 * and the combined content order the server returns is preserved, not
 * re-sorted client-side.
 */
@OptIn(ExperimentalCoroutinesApi::class)
class ChapterContentTest {
    private val dispatcher = StandardTestDispatcher()

    @Before
    fun setUp() = Dispatchers.setMain(dispatcher)

    @After
    fun tearDown() = Dispatchers.resetMain()

    @Test
    fun loadingBuildsCandidatesFromTheTimelineAndLinkedContentInServerOrder() = runTest(dispatcher) {
        val memory = memoryItem()
        val milestone = milestoneItem()
        val api = ChapterContentApi(
            timeline = listOf(memory, milestone),
            content = listOf(
                ChapterContentItem(targetId = milestone.value.milestone.id, targetType = ChapterContentItem.TargetType.MILESTONE),
                ChapterContentItem(targetId = memory.value.memory.id, targetType = ChapterContentItem.TargetType.MEMORY),
            ),
        )
        val model = ReferenceViewModel(config = ReferenceConfig(BASE_URL), api = api)

        signIn(model)
        model.loadChapterContent(CHAPTER)
        advanceUntilIdle()

        assertEquals(
            setOf(memory.value.memory.id, milestone.value.milestone.id),
            model.uiState.value.chapterContentCandidates.map { it.id }.toSet(),
        )
        assertEquals(
            listOf(milestone.value.milestone.id, memory.value.memory.id),
            model.uiState.value.chapterLinkedContent.map { it.id },
        )
    }

    @Test
    fun aPrivateHeartMomentLinkedByIdNeverSurfacesBecauseItIsNeverInTheTimeline() = runTest(dispatcher) {
        val visibleMemory = memoryItem()
        val privateHeartMomentId = UUID.randomUUID()
        val api = ChapterContentApi(
            timeline = listOf(visibleMemory),
            content = listOf(
                ChapterContentItem(targetId = privateHeartMomentId, targetType = ChapterContentItem.TargetType.HEART_MOMENT),
            ),
        )
        val model = ReferenceViewModel(config = ReferenceConfig(BASE_URL), api = api)

        signIn(model)
        model.loadChapterContent(CHAPTER)
        advanceUntilIdle()

        assertTrue(model.uiState.value.chapterLinkedContent.none { it.id == privateHeartMomentId })
        assertEquals(emptyList<UUID>(), model.uiState.value.chapterLinkedContent.map { it.id })
    }

    @Test
    fun linkingSendsTheKindAndTargetIdThenReloads() = runTest(dispatcher) {
        val memory = memoryItem()
        val api = ChapterContentApi(timeline = listOf(memory))
        val model = ReferenceViewModel(config = ReferenceConfig(BASE_URL), api = api)

        signIn(model)
        val target = RelationTargetItem(
            id = memory.value.memory.id,
            kind = ReferenceContract.RelationTargetKind.MEMORY,
            label = "A day by the sea",
            date = LocalDate.of(2026, 8, 20),
        )
        model.linkChapterContent(CHAPTER, target)
        advanceUntilIdle()

        assertEquals(
            listOf(Triple(CHAPTER, ReferenceContract.RelationTargetKind.MEMORY, memory.value.memory.id)),
            api.linkedCalls,
        )
        assertTrue(api.contentCallCount > 0)
    }

    @Test
    fun unlinkingSendsTheKindAndTargetIdThenReloads() = runTest(dispatcher) {
        val memory = memoryItem()
        val api = ChapterContentApi(timeline = listOf(memory))
        val model = ReferenceViewModel(config = ReferenceConfig(BASE_URL), api = api)

        signIn(model)
        val target = RelationTargetItem(
            id = memory.value.memory.id,
            kind = ReferenceContract.RelationTargetKind.MEMORY,
            label = "A day by the sea",
            date = LocalDate.of(2026, 8, 20),
        )
        model.unlinkChapterContent(CHAPTER, target)
        advanceUntilIdle()

        assertEquals(
            listOf(Triple(CHAPTER, ReferenceContract.RelationTargetKind.MEMORY, memory.value.memory.id)),
            api.unlinkedCalls,
        )
        assertTrue(api.contentCallCount > 0)
    }

    @Test
    fun forgetsChapterContentWhenTheSessionEnds() = runTest(dispatcher) {
        val memory = memoryItem()
        val api = ChapterContentApi(
            timeline = listOf(memory),
            content = listOf(ChapterContentItem(targetId = memory.value.memory.id, targetType = ChapterContentItem.TargetType.MEMORY)),
        )
        val model = ReferenceViewModel(config = ReferenceConfig(BASE_URL), api = api)

        signIn(model)
        model.loadChapterContent(CHAPTER)
        advanceUntilIdle()
        assertTrue(model.uiState.value.chapterLinkedContent.isNotEmpty())

        model.logout()

        assertTrue(model.uiState.value.chapterLinkedContent.isEmpty())
        assertTrue(model.uiState.value.chapterContentCandidates.isEmpty())
    }

    private suspend fun TestScope.signIn(model: ReferenceViewModel) {
        model.signIn("someone@example.test", "secret")
        advanceUntilIdle()
    }
}

private const val BASE_URL = "https://sidebyside.example"
private val CAPABILITIES = ResourceCapabilities(canComment = true, canDelete = true, canEdit = true)
private val AUTHOR = AuthorSummary(displayName = "Lea", id = UUID.randomUUID())
private val CREATED: OffsetDateTime = OffsetDateTime.now()
private val DATE: LocalDate = LocalDate.of(2026, 8, 20)

private fun memoryItem(date: LocalDate = DATE) = StoryItem.MemoryWrapper(
    StoryMemoryItem(
        effectiveDate = date,
        kind = StoryMemoryItem.Kind.MEMORY,
        memory = MemorySummary(
            attachments = emptyList(),
            author = AUTHOR,
            capabilities = CAPABILITIES,
            createdAt = CREATED,
            happenedOn = date,
            id = UUID.randomUUID(),
            title = "A day by the sea",
        ),
    ),
)

private fun milestoneItem(date: LocalDate = DATE) = StoryItem.MilestoneWrapper(
    StoryMilestoneItem(
        effectiveDate = date,
        kind = StoryMilestoneItem.Kind.MILESTONE,
        milestone = MilestoneSummary(
            author = AUTHOR,
            capabilities = CAPABILITIES,
            createdAt = CREATED,
            happenedOn = date,
            id = UUID.randomUUID(),
            title = "Moved in together",
        ),
    ),
)

private class ChapterContentApi(
    private val timeline: List<StoryItem> = emptyList(),
    private val content: List<ChapterContentItem> = emptyList(),
) : FakeReferenceContract() {
    var contentCallCount = 0
        private set
    val linkedCalls = mutableListOf<Triple<UUID, ReferenceContract.RelationTargetKind, UUID>>()
    val unlinkedCalls = mutableListOf<Triple<UUID, ReferenceContract.RelationTargetKind, UUID>>()

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

    override suspend fun getTimeline(spaceId: UUID, accessToken: String, cursor: String?): StoryPage =
        StoryPage(hasMore = false, items = timeline, nextCursor = null)

    override suspend fun getChapterContent(spaceId: UUID, accessToken: String, chapterId: UUID): ChapterContent {
        contentCallCount += 1
        return ChapterContent(items = content)
    }

    override suspend fun linkChapterTarget(
        spaceId: UUID,
        accessToken: String,
        chapterId: UUID,
        kind: ReferenceContract.RelationTargetKind,
        targetId: UUID,
    ) {
        linkedCalls += Triple(chapterId, kind, targetId)
    }

    override suspend fun unlinkChapterTarget(
        spaceId: UUID,
        accessToken: String,
        chapterId: UUID,
        kind: ReferenceContract.RelationTargetKind,
        targetId: UUID,
    ) {
        unlinkedCalls += Triple(chapterId, kind, targetId)
    }
}
