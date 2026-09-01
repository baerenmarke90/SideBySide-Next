package de.sidebyside.next.place

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
private val PLACE: UUID = UUID.fromString("22222222-2222-4222-8222-222222222222")
private val CAPABILITIES = ResourceCapabilities(canComment = true, canDelete = true, canEdit = true)
private val AUTHOR = AuthorSummary(displayName = "Lea", id = UUID.randomUUID())
private val CREATED: OffsetDateTime = OffsetDateTime.now()
private val DATE: LocalDate = LocalDate.of(2026, 8, 20)

/**
 * #532: what a place links to on the shared Story.
 *
 * The one thing worth pinning above the CRUD-shaped tests is the privacy
 * property #532 itself named as an acceptance criterion: the typed-relation
 * endpoints return linked ids only, and the client resolves labels
 * exclusively from the timeline it can already read. A private HeartMoment
 * is never in that timeline, so even a linked id pointing at one surfaces
 * as an id with no label rather than as leaked content.
 */
@OptIn(ExperimentalCoroutinesApi::class)
class PlaceRelationsTest {
    private val dispatcher = StandardTestDispatcher()

    @Before
    fun setUp() = Dispatchers.setMain(dispatcher)

    @After
    fun tearDown() = Dispatchers.resetMain()

    @Test
    fun loadingBuildsTargetsFromTheTimelineAndLinkedIdsFromEveryKind() = runTest(dispatcher) {
        val memory = memoryItem()
        val milestone = milestoneItem()
        val api = RelationsApi(
            timeline = listOf(memory, milestone),
            linked = mapOf(ReferenceContract.RelationTargetKind.MEMORY to setOf(memory.value.memory.id)),
        )
        val model = ReferenceViewModel(config = ReferenceConfig(BASE_URL), api = api)

        signIn(model)
        model.loadPlaceRelations(PLACE)
        advanceUntilIdle()

        assertEquals(
            setOf(memory.value.memory.id, milestone.value.milestone.id),
            model.uiState.value.placeRelationTargets.map { it.id }.toSet(),
        )
        assertEquals(setOf(memory.value.memory.id), model.uiState.value.placeLinkedTargetIds)
    }

    @Test
    fun aPrivateHeartMomentLinkedByIdNeverSurfacesAsATargetBecauseItIsNeverInTheTimeline() = runTest(dispatcher) {
        val visibleMemory = memoryItem()
        val privateHeartMomentId = UUID.randomUUID()
        val api = RelationsApi(
            timeline = listOf(visibleMemory),
            linked = mapOf(ReferenceContract.RelationTargetKind.HEART_MOMENT to setOf(privateHeartMomentId)),
        )
        val model = ReferenceViewModel(config = ReferenceConfig(BASE_URL), api = api)

        signIn(model)
        model.loadPlaceRelations(PLACE)
        advanceUntilIdle()

        assertTrue(privateHeartMomentId in model.uiState.value.placeLinkedTargetIds)
        assertFalse(privateHeartMomentId in model.uiState.value.placeRelationTargets.map { it.id })
        assertEquals(listOf(visibleMemory.value.memory.id), model.uiState.value.placeRelationTargets.map { it.id })
    }

    @Test
    fun linkingSendsTheKindAndTargetIdThenReloads() = runTest(dispatcher) {
        val memory = memoryItem()
        val api = RelationsApi(timeline = listOf(memory))
        val model = ReferenceViewModel(config = ReferenceConfig(BASE_URL), api = api)

        signIn(model)
        model.linkPlaceRelation(PLACE, ReferenceContract.RelationTargetKind.MEMORY, memory.value.memory.id)
        advanceUntilIdle()

        assertEquals(
            listOf(Triple(PLACE, ReferenceContract.RelationTargetKind.MEMORY, memory.value.memory.id)),
            api.linkedCalls,
        )
        assertTrue(api.timelineReadCount > 0)
        assertEquals(listOf(memory.value.memory.id), model.uiState.value.placeRelationTargets.map { it.id })
    }

    @Test
    fun unlinkingSendsTheKindAndTargetIdThenReloads() = runTest(dispatcher) {
        val memory = memoryItem()
        val api = RelationsApi(timeline = listOf(memory))
        val model = ReferenceViewModel(config = ReferenceConfig(BASE_URL), api = api)

        signIn(model)
        model.unlinkPlaceRelation(PLACE, ReferenceContract.RelationTargetKind.MEMORY, memory.value.memory.id)
        advanceUntilIdle()

        assertEquals(
            listOf(Triple(PLACE, ReferenceContract.RelationTargetKind.MEMORY, memory.value.memory.id)),
            api.unlinkedCalls,
        )
        assertTrue(api.timelineReadCount > 0)
        assertEquals(listOf(memory.value.memory.id), model.uiState.value.placeRelationTargets.map { it.id })
    }

    @Test
    fun forgetsPlaceRelationsWhenTheSessionEnds() = runTest(dispatcher) {
        val memory = memoryItem()
        val api = RelationsApi(timeline = listOf(memory))
        val model = ReferenceViewModel(config = ReferenceConfig(BASE_URL), api = api)

        signIn(model)
        model.loadPlaceRelations(PLACE)
        advanceUntilIdle()
        assertTrue(model.uiState.value.placeRelationTargets.isNotEmpty())

        model.logout()

        assertTrue(model.uiState.value.placeRelationTargets.isEmpty())
        assertTrue(model.uiState.value.placeLinkedTargetIds.isEmpty())
    }

    private suspend fun TestScope.signIn(model: ReferenceViewModel) {
        model.signIn("someone@example.test", "secret")
        advanceUntilIdle()
    }
}

private const val BASE_URL = "https://sidebyside.example"

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

private class RelationsApi(
    private val timeline: List<StoryItem> = emptyList(),
    private val linked: Map<ReferenceContract.RelationTargetKind, Set<UUID>> = emptyMap(),
) : FakeReferenceContract() {
    var timelineReadCount = 0
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

    override suspend fun getTimeline(spaceId: UUID, accessToken: String, cursor: String?): StoryPage {
        timelineReadCount += 1
        return StoryPage(hasMore = false, items = timeline, nextCursor = null)
    }

    override suspend fun listPlaceRelationTargets(
        spaceId: UUID,
        accessToken: String,
        placeId: UUID,
        kind: ReferenceContract.RelationTargetKind,
    ): List<UUID> = linked[kind]?.toList().orEmpty()

    override suspend fun linkPlaceTarget(
        spaceId: UUID,
        accessToken: String,
        placeId: UUID,
        kind: ReferenceContract.RelationTargetKind,
        targetId: UUID,
    ) {
        linkedCalls += Triple(placeId, kind, targetId)
    }

    override suspend fun unlinkPlaceTarget(
        spaceId: UUID,
        accessToken: String,
        placeId: UUID,
        kind: ReferenceContract.RelationTargetKind,
        targetId: UUID,
    ) {
        unlinkedCalls += Triple(placeId, kind, targetId)
    }
}
