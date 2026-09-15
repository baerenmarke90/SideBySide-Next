package de.eimir.app.today

import de.eimir.app.reference.FakeReferenceContract
import de.eimir.app.reference.ReferenceApiException
import de.eimir.app.reference.ReferenceConfig
import de.eimir.app.reference.ReferenceContract
import de.eimir.app.reference.ReferenceViewModel
import de.eimir.app.shell.UiStateKind
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
import org.junit.Assert.assertNull
import org.junit.Assert.assertTrue
import org.junit.Before
import org.junit.Test
import eimir.api.models.AccountMembershipView
import eimir.api.models.AccountView
import eimir.api.models.DashboardItem
import eimir.api.models.DashboardItemType
import eimir.api.models.DashboardRelationshipDuration
import eimir.api.models.DashboardSpaceSummary
import eimir.api.models.DashboardView
import eimir.api.models.DurationDisplayMode
import eimir.api.models.SessionView
import eimir.api.models.ThinkingOfYouAccepted
import eimir.api.models.ThinkingOfYouCreate
import eimir.api.models.TokenView

private val SPACE: UUID = UUID.fromString("11111111-1111-4111-8111-111111111111")

/**
 * Heute, and the one gesture on it.
 *
 * The gesture carries an idempotency key, so the case worth pinning is the one
 * a person actually creates: tapping again after something looked like it went
 * wrong must be the same gesture, not a second one.
 */
@OptIn(ExperimentalCoroutinesApi::class)
class TodayTest {
    private val dispatcher = StandardTestDispatcher()

    @Before
    fun setUp() = Dispatchers.setMain(dispatcher)

    @After
    fun tearDown() = Dispatchers.resetMain()

    @Test
    fun readsTheDashboardForTheActiveSpace() = runTest(dispatcher) {
        val api = TodayApi(dashboard = dashboard())
        val model = signedIn(api)

        model.loadToday()
        advanceUntilIdle()

        assertEquals(1, model.uiState.value.dashboard?.upcoming?.size)
        assertFalse(model.uiState.value.todayBusy)
    }

    @Test
    fun sendsTheGestureWithAClientRequestId() = runTest(dispatcher) {
        val api = TodayApi(dashboard = dashboard())
        val model = signedIn(api)

        model.sendThinkingOfYou()
        advanceUntilIdle()

        assertEquals(1, api.gestures.size)
        assertTrue(model.uiState.value.thinkingOfYouSent)
    }

    @Test
    fun aRetryAfterAFailureIsTheSameGestureRatherThanASecondOne() = runTest(dispatcher) {
        // The tap someone repeats is the one that looked like it failed. With a
        // fresh id each time, the partner would be sent two.
        val api = TodayApi(dashboard = dashboard(), failTimes = 1)
        val model = signedIn(api)

        model.sendThinkingOfYou()
        advanceUntilIdle()
        model.sendThinkingOfYou()
        advanceUntilIdle()

        assertEquals(2, api.gestures.size)
        assertEquals(api.gestures[0].clientRequestId, api.gestures[1].clientRequestId)
    }

    @Test
    fun aNewGestureAfterASuccessGetsItsOwnId() = runTest(dispatcher) {
        val api = TodayApi(dashboard = dashboard())
        val model = signedIn(api)

        model.sendThinkingOfYou()
        advanceUntilIdle()
        model.acknowledgeThinkingOfYou()
        model.sendThinkingOfYou()
        advanceUntilIdle()

        assertEquals(2, api.gestures.size)
        assertTrue(api.gestures[0].clientRequestId != api.gestures[1].clientRequestId)
    }

    @Test
    fun signedInAccountProvidesDisplayNameToUiState() = runTest(dispatcher) {
        val api = TodayApi(dashboard = dashboard())
        val model = signedIn(api)

        assertEquals("Lea", model.uiState.value.accountDisplayName)
    }

    @Test
    fun beingToldToSlowDownIsItsOwnStateRatherThanAFailure() = runTest(dispatcher) {
        val api = TodayApi(
            dashboard = dashboard(),
            gestureFailure = ReferenceApiException(null, "too many", 429),
        )
        val model = signedIn(api)

        model.sendThinkingOfYou()
        advanceUntilIdle()

        assertEquals(UiStateKind.RateLimit, model.uiState.value.todayProblem?.kind)
        assertFalse(model.uiState.value.thinkingOfYouSent)
    }

    @Test
    fun aDashboardWithoutARelationshipDurationSaysNothingAboutIt() = runTest(dispatcher) {
        // The couple may not have set a start date, or may have turned it off.
        // Zero days together would be a statement they did not make.
        val api = TodayApi(dashboard = dashboard(duration = null))
        val model = signedIn(api)

        model.loadToday()
        advanceUntilIdle()

        assertNull(model.uiState.value.dashboard?.relationshipDuration)
    }

    @Test
    fun forgetsTodayWhenTheSessionEnds() = runTest(dispatcher) {
        val api = TodayApi(dashboard = dashboard())
        val model = signedIn(api)

        model.loadToday()
        advanceUntilIdle()
        model.logout()

        assertNull(model.uiState.value.dashboard)
    }

    private fun TestScope.signedIn(api: ReferenceContract): ReferenceViewModel {
        val model = ReferenceViewModel(config = ReferenceConfig(BASE_URL), api = api)
        model.signIn("someone@example.test", "secret")
        advanceUntilIdle()
        return model
    }
}

private const val BASE_URL = "https://eimir.example"

private fun dashboard(
    duration: DashboardRelationshipDuration? = DashboardRelationshipDuration(
        daysTogether = 400,
        displayMode = DurationDisplayMode.YEARS_MONTHS,
        startedOn = LocalDate.of(2025, 7, 1),
    ),
) = DashboardView(
    keepsake = null,
    recentShared = emptyList(),
    relationshipDuration = duration,
    retrospective = null,
    sharedStorySummary = eimir.api.models.DashboardSharedStorySummary(heartMoments = 0, memories = 0, milestones = 0),
    space = DashboardSpaceSummary(partner = null, spaceId = SPACE),
    thinkingOfYouAvailableAt = null,
    upcoming = listOf(
        DashboardItem(
            createdAt = OffsetDateTime.now(),
            id = UUID.randomUUID(),
            occurredOn = null,
            scheduledAt = OffsetDateTime.now(),
            titleOrText = "A weekend by the sea",
            type = DashboardItemType.PLAN,
        ),
    ),
)

private class TodayApi(
    private val dashboard: DashboardView,
    private val gestureFailure: Throwable? = null,
    private var failTimes: Int = 0,
) : FakeReferenceContract() {
    val gestures = mutableListOf<ThinkingOfYouCreate>()

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

    override suspend fun getDashboard(spaceId: UUID, accessToken: String): DashboardView =
        dashboard

    override suspend fun sendThinkingOfYou(
        spaceId: UUID,
        accessToken: String,
        gesture: ThinkingOfYouCreate,
    ): ThinkingOfYouAccepted {
        gestures += gesture
        gestureFailure?.let { throw it }
        if (failTimes > 0) {
            failTimes -= 1
            throw ReferenceApiException(null, "temporary", 500)
        }
        return ThinkingOfYouAccepted(
            clientRequestId = gesture.clientRequestId,
            thinkingOfYouAvailableAt = OffsetDateTime.now().plusMinutes(30),
        )
    }
}
