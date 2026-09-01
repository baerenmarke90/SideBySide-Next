package de.sidebyside.next.plan

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
import org.junit.Assert.assertTrue
import org.junit.Before
import org.junit.Test
import sidebyside.api.models.AccountMembershipView
import sidebyside.api.models.AccountView
import sidebyside.api.models.AuthorSummary
import sidebyside.api.models.PlanComplete
import sidebyside.api.models.PlanDetail
import sidebyside.api.models.PlanPage
import sidebyside.api.models.PlanReturnToWishResponse
import sidebyside.api.models.PlanSchedule
import sidebyside.api.models.PlanStatus
import sidebyside.api.models.ResourceCapabilities
import sidebyside.api.models.SessionView
import sidebyside.api.models.StoryPage
import sidebyside.api.models.TokenView
import sidebyside.api.models.WishCreate
import sidebyside.api.models.WishDetail
import sidebyside.api.models.WishPage
import sidebyside.api.models.WishStatus
import sidebyside.api.models.WishToPlan
import sidebyside.api.models.WishToPlanResponse

private val SPACE: UUID = UUID.fromString("11111111-1111-4111-8111-111111111111")
private val OPEN_WISH: UUID = UUID.fromString("aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa")
private val PLANNED_WISH: UUID = UUID.fromString("bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbbb")
private val PLAN: UUID = UUID.fromString("cccccccc-cccc-4ccc-8ccc-cccccccccccc")

/**
 * Planning is a lifecycle, not two lists.
 *
 * One transition moves two resources — planning a wish creates a plan *and*
 * moves the wish — so what is worth pinning is that the client never guesses at
 * the result, and never shows one intention as two.
 */
@OptIn(ExperimentalCoroutinesApi::class)
class PlanningTest {
    private val dispatcher = StandardTestDispatcher()

    @Before
    fun setUp() = Dispatchers.setMain(dispatcher)

    @After
    fun tearDown() = Dispatchers.resetMain()

    @Test
    fun listsOnlyTheWishesNobodyHasActedOnYet() = runTest(dispatcher) {
        // A planned wish still exists and is still returned. Showing it beside
        // the plan it became would list one intention twice.
        val api = PlanningApi(
            wishes = listOf(
                aWish(OPEN_WISH, WishStatus.OPEN),
                aWish(PLANNED_WISH, WishStatus.PLANNED),
            ),
            plans = listOf(aPlan(PlanStatus.IDEA)),
        )
        val model = signedIn(api)

        model.loadPlanning()
        advanceUntilIdle()

        assertEquals(listOf(OPEN_WISH), model.uiState.value.openWishes.map { it.id })
        assertEquals(1, model.uiState.value.plans.size)
    }

    @Test
    fun notesAWishAndRereadsBothLists() = runTest(dispatcher) {
        val api = PlanningApi()
        val model = signedIn(api)

        model.addWish("A weekend by the sea")
        advanceUntilIdle()

        assertEquals("A weekend by the sea", api.created.single().title)
        // Re-read rather than appended: one write can move two resources.
        assertTrue(api.wishReads >= 1 && api.planReads >= 1)
    }

    @Test
    fun refusesAnEmptyWishWithoutSendingAnything() = runTest(dispatcher) {
        val api = PlanningApi()
        val model = signedIn(api)

        model.addWish("   ")
        advanceUntilIdle()

        assertTrue(api.created.isEmpty())
    }

    @Test
    fun turnsAWishIntoAPlanAgainstTheWishesOwnVersion() = runTest(dispatcher) {
        val api = PlanningApi(wishes = listOf(aWish(OPEN_WISH, WishStatus.OPEN, version = 4)))
        val model = signedIn(api)

        model.loadPlanning()
        advanceUntilIdle()
        model.planWish(OPEN_WISH, "", "")
        advanceUntilIdle()

        assertEquals(listOf(4), api.planWishVersions)
        // A blank title means the wish's own words carry over.
        assertEquals("A weekend by the sea", api.conversions.single().title)
    }

    @Test
    fun schedulingUsesItsOwnCallAndVersion() = runTest(dispatcher) {
        val api = PlanningApi(plans = listOf(aPlan(PlanStatus.IDEA, version = 7)))
        val model = signedIn(api)

        model.loadPlanning()
        advanceUntilIdle()
        model.schedulePlan(PLAN, OffsetDateTime.now())
        advanceUntilIdle()

        assertEquals(listOf(7), api.scheduleVersions)
        assertTrue(api.completions.isEmpty())
    }

    @Test
    fun completingRecordsTheDayItActuallyHappened() = runTest(dispatcher) {
        val api = PlanningApi(plans = listOf(aPlan(PlanStatus.PLANNED, version = 2)))
        val model = signedIn(api)

        model.loadPlanning()
        advanceUntilIdle()
        model.completePlan(PLAN, LocalDate.of(2026, 8, 30))
        advanceUntilIdle()

        assertEquals(LocalDate.of(2026, 8, 30), api.completions.single().experiencedOn)
    }

    @Test
    fun sendingAPlanBackToAWishUsesTheReturnCall() = runTest(dispatcher) {
        val api = PlanningApi(plans = listOf(aPlan(PlanStatus.IDEA, version = 3)))
        val model = signedIn(api)

        model.loadPlanning()
        advanceUntilIdle()
        model.returnPlanToWish(PLAN)
        advanceUntilIdle()

        assertEquals(listOf(3), api.returnVersions)
    }

    @Test
    fun aConflictIsReportedRatherThanOverwritingThePartner() = runTest(dispatcher) {
        val api = PlanningApi(
            plans = listOf(aPlan(PlanStatus.IDEA)),
            scheduleFailure = ReferenceApiException(null, "conflict", 409),
        )
        val model = signedIn(api)

        model.loadPlanning()
        advanceUntilIdle()
        model.schedulePlan(PLAN, OffsetDateTime.now())
        advanceUntilIdle()

        assertEquals(UiStateKind.Conflict, model.uiState.value.planningProblem?.kind)
    }

    @Test
    fun forgetsPlanningWhenTheSessionEnds() = runTest(dispatcher) {
        val api = PlanningApi(wishes = listOf(aWish(OPEN_WISH, WishStatus.OPEN)))
        val model = signedIn(api)

        model.loadPlanning()
        advanceUntilIdle()
        assertTrue(model.uiState.value.openWishes.isNotEmpty())

        model.logout()

        assertTrue(model.uiState.value.openWishes.isEmpty())
        assertTrue(model.uiState.value.plans.isEmpty())
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
private val CREATOR = AuthorSummary(displayName = "Lea", id = UUID.randomUUID())

private fun aWish(id: UUID, status: WishStatus, version: Int = 1) = WishDetail(
    capabilities = CAPABILITIES,
    createdAt = OffsetDateTime.now(),
    createdBy = UUID.randomUUID(),
    creator = CREATOR,
    id = id,
    spaceId = SPACE,
    status = status,
    title = "A weekend by the sea",
    updatedAt = OffsetDateTime.now(),
    version = version,
)

private fun aPlan(status: PlanStatus, version: Int = 1) = PlanDetail(
    capabilities = CAPABILITIES,
    createdAt = OffsetDateTime.now(),
    createdBy = UUID.randomUUID(),
    creator = CREATOR,
    description = null,
    experiencedOn = null,
    id = PLAN,
    placeId = null,
    plannedEnd = null,
    plannedStart = null,
    sourceWishId = null,
    spaceId = SPACE,
    status = status,
    title = "A weekend by the sea",
    updatedAt = OffsetDateTime.now(),
    version = version,
)

private class PlanningApi(
    private val wishes: List<WishDetail> = emptyList(),
    private val plans: List<PlanDetail> = emptyList(),
    private val scheduleFailure: Throwable? = null,
) : FakeReferenceContract() {
    val created = mutableListOf<WishCreate>()
    val conversions = mutableListOf<WishToPlan>()
    val planWishVersions = mutableListOf<Int>()
    val scheduleVersions = mutableListOf<Int>()
    val completions = mutableListOf<PlanComplete>()
    val returnVersions = mutableListOf<Int>()
    var wishReads = 0
    var planReads = 0

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

    override suspend fun listWishes(spaceId: UUID, accessToken: String): WishPage {
        wishReads += 1
        return WishPage(hasMore = false, items = wishes, nextCursor = null)
    }

    override suspend fun listPlans(spaceId: UUID, accessToken: String): PlanPage {
        planReads += 1
        return PlanPage(hasMore = false, items = plans, nextCursor = null)
    }

    override suspend fun createWish(
        spaceId: UUID,
        accessToken: String,
        wish: WishCreate,
    ): WishDetail {
        created += wish
        return aWish(OPEN_WISH, WishStatus.OPEN)
    }

    override suspend fun planWish(
        spaceId: UUID,
        accessToken: String,
        wishId: UUID,
        ifMatch: Int,
        conversion: WishToPlan,
    ): WishToPlanResponse {
        planWishVersions += ifMatch
        conversions += conversion
        return WishToPlanResponse(
            plan = aPlan(PlanStatus.IDEA),
            wish = aWish(wishId, WishStatus.PLANNED),
        )
    }

    override suspend fun schedulePlan(
        spaceId: UUID,
        accessToken: String,
        planId: UUID,
        ifMatch: Int,
        schedule: PlanSchedule,
    ): PlanDetail {
        scheduleVersions += ifMatch
        scheduleFailure?.let { throw it }
        return aPlan(PlanStatus.PLANNED, version = ifMatch + 1)
    }

    override suspend fun completePlan(
        spaceId: UUID,
        accessToken: String,
        planId: UUID,
        ifMatch: Int,
        completion: PlanComplete,
    ): PlanDetail {
        completions += completion
        return aPlan(PlanStatus.COMPLETED, version = ifMatch + 1)
    }

    override suspend fun returnPlanToWish(
        spaceId: UUID,
        accessToken: String,
        planId: UUID,
        ifMatch: Int,
    ): PlanReturnToWishResponse {
        returnVersions += ifMatch
        return PlanReturnToWishResponse(
            removedPlanId = planId,
            wish = aWish(OPEN_WISH, WishStatus.OPEN),
        )
    }
}
