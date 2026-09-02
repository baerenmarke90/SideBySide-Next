package de.sidebyside.next.reference

import java.util.UUID
import kotlinx.coroutines.CompletableDeferred
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.ExperimentalCoroutinesApi
import kotlinx.coroutines.test.StandardTestDispatcher
import kotlinx.coroutines.test.advanceUntilIdle
import kotlinx.coroutines.test.resetMain
import kotlinx.coroutines.test.runTest
import kotlinx.coroutines.test.setMain
import de.sidebyside.next.demo.DemoPersona
import org.junit.After
import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertNull
import org.junit.Assert.assertTrue
import org.junit.Before
import org.junit.Test
import sidebyside.api.models.AccountMembershipView
import sidebyside.api.models.AccountView
import sidebyside.api.models.AuthorSummary
import sidebyside.api.models.AttachmentDetail
import sidebyside.api.models.AttachmentReadRequest
import sidebyside.api.models.AttachmentUploadCreate
import sidebyside.api.models.MemoryAttachmentSet
import sidebyside.api.models.MemoryCreate
import sidebyside.api.models.DashboardSpaceSummary
import sidebyside.api.models.DashboardView
import sidebyside.api.models.MemoryDetail
import sidebyside.api.models.ReadDescriptor
import sidebyside.api.models.SessionView
import sidebyside.api.models.StoryPage
import sidebyside.api.models.TokenView
import sidebyside.api.models.PlanDetail
import sidebyside.api.models.PlanPage
import sidebyside.api.models.PlanStatus
import sidebyside.api.models.UploadDescriptor
import sidebyside.api.models.WishDetail
import sidebyside.api.models.WishPage
import sidebyside.api.models.WishStatus

private val FIRST_SPACE: UUID = UUID.fromString("11111111-1111-4111-8111-111111111111")
private val SECOND_SPACE: UUID = UUID.fromString("22222222-2222-4222-8222-222222222222")

/**
 * The Space is server-authorised state, not build configuration. These tests
 * pin that, and pin what happens at the moment it changes — the point where a
 * stale request or a carried-over draft would write into the wrong couple's
 * Space.
 */
@OptIn(ExperimentalCoroutinesApi::class)
class SpaceContextTest {
    private val dispatcher = StandardTestDispatcher()

    @Before
    fun setUp() = Dispatchers.setMain(dispatcher)

    @After
    fun tearDown() = Dispatchers.resetMain()

    @Test
    fun resolvesTheSpaceFromMembershipsRatherThanFromConfiguration() =
        runTest(dispatcher) {
            val api = SpaceApi(memberships = listOf(active(FIRST_SPACE)))
            val model = ReferenceViewModel(config = ReferenceConfig(BASE_URL), api = api)

            model.signIn("someone@example.test", "secret")
            advanceUntilIdle()

            assertTrue(model.uiState.value.loggedIn)
            assertEquals(FIRST_SPACE, model.uiState.value.activeSpaceId)
            assertEquals(listOf(FIRST_SPACE), api.timelineSpaces)
        }

    @Test
    fun isConfiguredByTheServerAddressAlone() {
        // A Space ID is technical configuration a couple must never enter, and
        // it is no longer part of what makes a build usable.
        assertTrue(ReferenceConfig(BASE_URL).isConfigured)
        assertFalse(ReferenceConfig("").isConfigured)
    }

    @Test
    fun refusesToOpenAnAccountWithoutAnActiveMembership() = runTest(dispatcher) {
        val api = SpaceApi(memberships = listOf(membership("INVITED", FIRST_SPACE)))
        val model = ReferenceViewModel(config = ReferenceConfig(BASE_URL), api = api)

        model.signIn("someone@example.test", "secret")
        advanceUntilIdle()

        // Authenticated, but with nothing to open: a product state, not a
        // sign-in failure, and never a silent fallback into a foreign Space.
        // The session is kept rather than discarded — #391 needs it to accept
        // an invitation — which is why this is `awaitingSpace`, not an error.
        assertFalse(model.uiState.value.loggedIn)
        assertTrue(model.uiState.value.awaitingSpace)
        assertNull(model.uiState.value.activeSpaceId)
    }

    @Test
    fun offersEveryActiveSpaceAndNoneThatIsNotActive() = runTest(dispatcher) {
        val api = SpaceApi(
            memberships = listOf(
                active(FIRST_SPACE),
                membership("REMOVED", UUID.randomUUID()),
                active(SECOND_SPACE),
            ),
        )
        val model = ReferenceViewModel(config = ReferenceConfig(BASE_URL), api = api)

        model.signIn("someone@example.test", "secret")
        advanceUntilIdle()

        assertEquals(
            listOf(FIRST_SPACE, SECOND_SPACE),
            model.uiState.value.availableSpaces.map { it.spaceId },
        )
    }

    @Test
    fun switchingSpaceDropsEverythingBoundToThePreviousOne() = runTest(dispatcher) {
        val api = SpaceApi(memberships = listOf(active(FIRST_SPACE), active(SECOND_SPACE)))
        val model = ReferenceViewModel(config = ReferenceConfig(BASE_URL), api = api)

        model.signIn("someone@example.test", "secret")
        advanceUntilIdle()
        model.selectSpace(SECOND_SPACE)
        advanceUntilIdle()

        val state = model.uiState.value
        assertEquals(SECOND_SPACE, state.activeSpaceId)
        assertTrue(state.draftImages.isEmpty())
        assertNull(state.lastMemoryTitle)
        assertNull(state.lastImageBytes)
        // The new Space is read; the old one is not read again.
        assertEquals(SECOND_SPACE, api.timelineSpaces.last())
        // #572: used to only set the never-rendered `status` field in the
        // signed-in shell; this is what the account actually sees now.
        assertEquals(R.string.space_switched, state.snackbarMessage?.text?.resourceId)
    }

    /**
     * The general Snackbar-event mechanism (#572), pinned once against
     * [ReferenceViewModel.selectSpace] rather than repeated for every call
     * site that posts one: each event gets its own id so the exact same
     * text posted twice in a row is still shown twice, and clearing one by
     * id can never wipe a newer event posted in between.
     */
    @Test
    fun eachSnackbarPostGetsItsOwnIdAndOnlyAMatchingClearRemovesIt() = runTest(dispatcher) {
        val api = SpaceApi(memberships = listOf(active(FIRST_SPACE), active(SECOND_SPACE)))
        val model = ReferenceViewModel(config = ReferenceConfig(BASE_URL), api = api)

        model.signIn("someone@example.test", "secret")
        advanceUntilIdle()
        model.selectSpace(SECOND_SPACE)
        advanceUntilIdle()
        val firstEvent = model.uiState.value.snackbarMessage
        assertTrue(firstEvent != null)

        model.selectSpace(FIRST_SPACE)
        advanceUntilIdle()
        val secondEvent = model.uiState.value.snackbarMessage
        assertTrue(secondEvent != null)
        // Same text (space_switched) both times, but a distinct event.
        assertTrue(firstEvent!!.id != secondEvent!!.id)

        // A stale clear for the already-superseded first event must not
        // touch the second, still-pending one.
        model.snackbarShown(firstEvent.id)
        assertEquals(secondEvent, model.uiState.value.snackbarMessage)

        model.snackbarShown(secondEvent.id)
        assertNull(model.uiState.value.snackbarMessage)
    }

    @Test
    fun aRequestStillInFlightAgainstTheOldSpaceCannotLandInTheNewOne() =
        runTest(dispatcher) {
            val release = CompletableDeferred<Unit>()
            val api = SpaceApi(
                memberships = listOf(active(FIRST_SPACE), active(SECOND_SPACE)),
                holdTimelineAfter = 1,
                releaseHeldTimeline = release,
            )
            val model = ReferenceViewModel(config = ReferenceConfig(BASE_URL), api = api)

            model.signIn("someone@example.test", "secret")
            advanceUntilIdle()

            // The first Space's timeline is still running when the user switches.
            model.selectSpace(SECOND_SPACE)
            advanceUntilIdle()
            release.complete(Unit)
            advanceUntilIdle()

            // The late result belongs to a Space the user has left.
            assertEquals(SECOND_SPACE, model.uiState.value.activeSpaceId)
            assertTrue(model.uiState.value.storyItems.isEmpty())
        }

    @Test
    fun switchingToAnUnauthorizedSpaceIsRefused() = runTest(dispatcher) {
        val api = SpaceApi(memberships = listOf(active(FIRST_SPACE)))
        val model = ReferenceViewModel(config = ReferenceConfig(BASE_URL), api = api)

        model.signIn("someone@example.test", "secret")
        advanceUntilIdle()
        model.selectSpace(UUID.randomUUID())
        advanceUntilIdle()

        // A Space the server did not authorise must not become the context.
        assertEquals(FIRST_SPACE, model.uiState.value.activeSpaceId)
    }

    @Test
    fun switchingSpaceForgetsThePreviousSpacesPlanningAndToday() = runTest(dispatcher) {
        // Only the Story was cleared when Planen and Heute did not exist yet.
        // Both now carry state that must not survive into another Space.
        val api = SpaceApi(memberships = listOf(active(FIRST_SPACE), active(SECOND_SPACE)))
        val model = ReferenceViewModel(config = ReferenceConfig(BASE_URL), api = api)

        model.signIn("someone@example.test", "secret")
        advanceUntilIdle()
        model.loadPlanning()
        model.loadToday()
        advanceUntilIdle()
        assertTrue(model.uiState.value.openWishes.isNotEmpty())
        assertTrue(model.uiState.value.plans.isNotEmpty())
        assertEquals(FIRST_SPACE, model.uiState.value.dashboard?.space?.spaceId)

        model.selectSpace(SECOND_SPACE)

        assertTrue(model.uiState.value.openWishes.isEmpty())
        assertTrue(model.uiState.value.plans.isEmpty())
        assertNull(model.uiState.value.dashboard)
    }

    @Test
    fun signingOutForgetsTheSpace() = runTest(dispatcher) {
        val api = SpaceApi(memberships = listOf(active(FIRST_SPACE)))
        val model = ReferenceViewModel(config = ReferenceConfig(BASE_URL), api = api)

        model.signIn("someone@example.test", "secret")
        advanceUntilIdle()
        model.logout()

        assertNull(model.uiState.value.activeSpaceId)
        assertTrue(model.uiState.value.availableSpaces.isEmpty())
    }

    @Test
    fun rememberedSpaceIsPreferredOverTheFirstActiveMembershipOnSignIn() = runTest(dispatcher) {
        // #391's own deferred piece: relaunching returns to the Space the
        // account was last in, not always whichever membership sorts first.
        val accountId = UUID.randomUUID()
        val store = InMemorySpacePreferenceStore().apply { rememberSpace(accountId, SECOND_SPACE) }
        val api = SpaceApi(
            memberships = listOf(active(FIRST_SPACE), active(SECOND_SPACE)),
            accountId = accountId,
        )
        val model = ReferenceViewModel(config = ReferenceConfig(BASE_URL), api = api, spaceStore = store)

        model.signIn("someone@example.test", "secret")
        advanceUntilIdle()

        assertEquals(SECOND_SPACE, model.uiState.value.activeSpaceId)
    }

    @Test
    fun withNoRememberedSpaceTheFirstActiveMembershipStillWins() = runTest(dispatcher) {
        val api = SpaceApi(memberships = listOf(active(FIRST_SPACE), active(SECOND_SPACE)))
        val model = ReferenceViewModel(
            config = ReferenceConfig(BASE_URL),
            api = api,
            spaceStore = InMemorySpacePreferenceStore(),
        )

        model.signIn("someone@example.test", "secret")
        advanceUntilIdle()

        assertEquals(FIRST_SPACE, model.uiState.value.activeSpaceId)
    }

    @Test
    fun aRememberedSpaceNoLongerActiveFallsBackToTheFirstOne() = runTest(dispatcher) {
        val accountId = UUID.randomUUID()
        val goneSpace = UUID.fromString("99999999-9999-4999-8999-999999999999")
        val store = InMemorySpacePreferenceStore().apply { rememberSpace(accountId, goneSpace) }
        val api = SpaceApi(
            memberships = listOf(active(FIRST_SPACE), active(SECOND_SPACE)),
            accountId = accountId,
        )
        val model = ReferenceViewModel(config = ReferenceConfig(BASE_URL), api = api, spaceStore = store)

        model.signIn("someone@example.test", "secret")
        advanceUntilIdle()

        assertEquals(FIRST_SPACE, model.uiState.value.activeSpaceId)
    }

    @Test
    fun selectingASpaceRemembersItForNextSignIn() = runTest(dispatcher) {
        val accountId = UUID.randomUUID()
        val store = InMemorySpacePreferenceStore()
        val api = SpaceApi(
            memberships = listOf(active(FIRST_SPACE), active(SECOND_SPACE)),
            accountId = accountId,
        )
        val model = ReferenceViewModel(config = ReferenceConfig(BASE_URL), api = api, spaceStore = store)

        model.signIn("someone@example.test", "secret")
        advanceUntilIdle()
        model.selectSpace(SECOND_SPACE)

        assertEquals(SECOND_SPACE, store.rememberedSpace(accountId))
    }

    @Test
    fun theAutomaticFirstPickIsNeverRememberedByItself() = runTest(dispatcher) {
        // Signing in without ever explicitly switching must not make the
        // arbitrary first-active pick sticky.
        val accountId = UUID.randomUUID()
        val store = InMemorySpacePreferenceStore()
        val api = SpaceApi(
            memberships = listOf(active(FIRST_SPACE), active(SECOND_SPACE)),
            accountId = accountId,
        )
        val model = ReferenceViewModel(config = ReferenceConfig(BASE_URL), api = api, spaceStore = store)

        model.signIn("someone@example.test", "secret")
        advanceUntilIdle()

        assertNull(store.rememberedSpace(accountId))
    }
}

private const val BASE_URL = "https://sidebyside.example"

private fun active(spaceId: UUID) = membership("ACTIVE", spaceId)

private fun membership(status: String, spaceId: UUID) =
    AccountMembershipView(role = "PARTNER", spaceId = spaceId, status = status)

private val FULL_CAPABILITIES = sidebyside.api.models.ResourceCapabilities(
    canComment = true,
    canDelete = true,
    canEdit = true,
)

private class SpaceApi(
    private val memberships: List<AccountMembershipView>,
    private val holdTimelineAfter: Int = Int.MAX_VALUE,
    private val releaseHeldTimeline: CompletableDeferred<Unit>? = null,
    private val accountId: UUID = UUID.randomUUID(),
) : FakeReferenceContract() {
    val timelineSpaces = mutableListOf<UUID>()
    private var timelineCalls = 0

    override suspend fun signIn(email: String, password: String): SessionView = SessionView(
        account = AccountView(displayName = "Someone", id = accountId),
        tokens = TokenView(
            accessExpiresAt = java.time.OffsetDateTime.now(),
            accessToken = "access",
            refreshExpiresAt = java.time.OffsetDateTime.now(),
            refreshToken = "refresh",
        ),
    )

    override suspend fun consumeMagicLink(token: String): SessionView =
        signIn("demo", "demo")

    override suspend fun listMemberships(accessToken: String): List<AccountMembershipView> =
        memberships


    override suspend fun getTimeline(
        spaceId: UUID,
        accessToken: String,
        cursor: String?,
    ): StoryPage {
        timelineCalls += 1
        timelineSpaces += spaceId
        if (timelineCalls > holdTimelineAfter) {
            releaseHeldTimeline?.await()
        }
        return StoryPage(hasMore = false, items = emptyList(), nextCursor = null)
    }

    override suspend fun listWishes(spaceId: UUID, accessToken: String): WishPage = WishPage(
        hasMore = false,
        items = listOf(
            WishDetail(
                capabilities = FULL_CAPABILITIES,
                createdAt = java.time.OffsetDateTime.now(),
                createdBy = UUID.randomUUID(),
                creator = AuthorSummary(displayName = "Lea", id = UUID.randomUUID()),
                id = UUID.randomUUID(),
                spaceId = spaceId,
                status = WishStatus.OPEN,
                title = "Something noted in $spaceId",
                updatedAt = java.time.OffsetDateTime.now(),
                version = 1,
            ),
        ),
        nextCursor = null,
    )

    override suspend fun listPlans(spaceId: UUID, accessToken: String): PlanPage = PlanPage(
        hasMore = false,
        items = listOf(
            PlanDetail(
                capabilities = FULL_CAPABILITIES,
                createdAt = java.time.OffsetDateTime.now(),
                createdBy = UUID.randomUUID(),
                creator = AuthorSummary(displayName = "Lea", id = UUID.randomUUID()),
                description = null,
                experiencedOn = null,
                id = UUID.randomUUID(),
                placeId = null,
                plannedEnd = null,
                plannedStart = null,
                sourceWishId = null,
                spaceId = spaceId,
                status = PlanStatus.IDEA,
                title = "A plan in $spaceId",
                updatedAt = java.time.OffsetDateTime.now(),
                version = 1,
            ),
        ),
        nextCursor = null,
    )

    override suspend fun getDashboard(spaceId: UUID, accessToken: String): DashboardView =
        DashboardView(
            recentShared = emptyList(),
            relationshipDuration = null,
            retrospective = null,
            space = DashboardSpaceSummary(partner = null, spaceId = spaceId),
            upcoming = emptyList(),
        )








}
