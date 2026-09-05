package de.sidebyside.next.reference

import de.sidebyside.next.demo.DemoPersona
import java.util.UUID
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.ExperimentalCoroutinesApi
import kotlinx.coroutines.test.StandardTestDispatcher
import kotlinx.coroutines.test.advanceUntilIdle
import kotlinx.coroutines.test.resetMain
import kotlinx.coroutines.test.runTest
import kotlinx.coroutines.test.setMain
import org.junit.After
import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertNotNull
import org.junit.Assert.assertTrue
import org.junit.Before
import org.junit.Test
import sidebyside.api.models.AccountMembershipView
import sidebyside.api.models.AccountView
import sidebyside.api.models.MembershipStatus
import sidebyside.api.models.SessionView
import sidebyside.api.models.SpaceMembershipExitView
import sidebyside.api.models.StoryPage
import sidebyside.api.models.TokenView

private const val SPACE_OFFBOARDING_BASE_URL = "https://sidebyside.example"
private val SPACE_A: UUID = UUID.fromString("11111111-1111-4111-8111-111111111111")
private val SPACE_B: UUID = UUID.fromString("22222222-2222-4222-8222-222222222222")
private val OFFBOARDING_ACCOUNT: UUID = UUID.fromString("33333333-3333-4333-8333-333333333333")

@OptIn(ExperimentalCoroutinesApi::class)
class SpaceOffboardingTest {
    private val dispatcher = StandardTestDispatcher()

    @Before
    fun setUp() = Dispatchers.setMain(dispatcher)

    @After
    fun tearDown() = Dispatchers.resetMain()

    @Test
    fun acceptedExitUsesCurrentSessionAndMovesToRemainingActiveSpace() =
        runTest(dispatcher) {
            val api = OffboardingApi(remainingSpaces = listOf(SPACE_B))
            val model = model(api)

            model.signIn("someone@example.test", "secret")
            advanceUntilIdle()
            assertEquals(SPACE_A, model.uiState.value.activeSpaceId)
            val generationBeforeExit = model.storyGeneration

            model.leaveActiveSpace()
            advanceUntilIdle()

            assertEquals(listOf(SPACE_A), api.leftSpaces)
            assertEquals(listOf("access"), api.leaveTokens)
            val state = model.uiState.value
            assertTrue(state.loggedIn)
            assertFalse(state.awaitingSpace)
            assertEquals(SPACE_B, state.activeSpaceId)
            assertEquals(listOf(SPACE_B), state.availableSpaces.map { it.spaceId })
            assertTrue(model.storyGeneration > generationBeforeExit)
            assertFalse(state.spaceOffboardingBusy)
            assertEquals(null, state.spaceOffboardingProblem)
        }

    @Test
    fun acceptedExitWithoutAnotherSpaceKeepsAuthenticatedAwaitingSpaceState() =
        runTest(dispatcher) {
            val api = OffboardingApi(remainingSpaces = emptyList())
            val model = model(api)

            model.signIn("someone@example.test", "secret")
            advanceUntilIdle()
            model.leaveActiveSpace()
            advanceUntilIdle()

            val state = model.uiState.value
            assertFalse(state.loggedIn)
            assertTrue(state.awaitingSpace)
            assertEquals(null, state.activeSpaceId)
            assertTrue(state.availableSpaces.isEmpty())
            assertTrue(state.storyItems.isEmpty())
            assertTrue(state.draftImages.isEmpty())
            assertFalse(state.spaceOffboardingBusy)
        }

    @Test
    fun rejectedExitKeepsCurrentSpaceAndSurfacesProblem() = runTest(dispatcher) {
        val api = OffboardingApi(
            remainingSpaces = listOf(SPACE_B),
            leaveFailure = ReferenceApiException(
                code = "SPACE_OFFBOARDING_UNAVAILABLE",
                message = "unavailable",
                status = 503,
            ),
        )
        val model = model(api)

        model.signIn("someone@example.test", "secret")
        advanceUntilIdle()
        model.leaveActiveSpace()
        advanceUntilIdle()

        val state = model.uiState.value
        assertTrue(state.loggedIn)
        assertFalse(state.awaitingSpace)
        assertEquals(SPACE_A, state.activeSpaceId)
        assertFalse(state.spaceOffboardingBusy)
        assertNotNull(state.spaceOffboardingProblem)
        assertEquals(listOf(SPACE_A), api.leaveAttempts)
    }

    @Test
    fun demoSessionNeverCallsSelfExit() = runTest(dispatcher) {
        val api = OffboardingApi(remainingSpaces = listOf(SPACE_B))
        val model = model(api)

        model.enterDemo(DemoPersona.Lea)
        advanceUntilIdle()
        assertTrue(model.uiState.value.demoMode)

        model.leaveActiveSpace()
        advanceUntilIdle()

        assertTrue(api.leaveAttempts.isEmpty())
        assertEquals(SPACE_A, model.uiState.value.activeSpaceId)
    }

    private fun model(api: ReferenceContract) = ReferenceViewModel(
        config = ReferenceConfig(SPACE_OFFBOARDING_BASE_URL),
        api = api,
    )
}

private class OffboardingApi(
    private val remainingSpaces: List<UUID>,
    private val leaveFailure: Throwable? = null,
) : FakeReferenceContract() {
    val leaveAttempts = mutableListOf<UUID>()
    val leftSpaces = mutableListOf<UUID>()
    val leaveTokens = mutableListOf<String>()
    private var exited = false

    override suspend fun signIn(email: String, password: String): SessionView = session()

    override suspend fun createDemoEntry(baseUrl: String, persona: DemoPersona): String = "demo-proof"

    override suspend fun consumeMagicLink(token: String): SessionView = session()

    override suspend fun listMemberships(accessToken: String): List<AccountMembershipView> {
        val spaces = if (exited) remainingSpaces else listOf(SPACE_A, SPACE_B)
        return spaces.map { spaceId ->
            AccountMembershipView(role = "PARTNER", spaceId = spaceId, status = "ACTIVE")
        }
    }

    override suspend fun leaveSpace(
        spaceId: UUID,
        accessToken: String,
    ): SpaceMembershipExitView {
        leaveAttempts += spaceId
        leaveFailure?.let { throw it }
        leftSpaces += spaceId
        leaveTokens += accessToken
        exited = true
        return SpaceMembershipExitView(
            endedAt = java.time.OffsetDateTime.now(),
            spaceId = spaceId,
            status = MembershipStatus.LEFT,
        )
    }

    override suspend fun getTimeline(
        spaceId: UUID,
        accessToken: String,
        cursor: String?,
    ): StoryPage = StoryPage(hasMore = false, items = emptyList(), nextCursor = null)

    private fun session(): SessionView = SessionView(
        account = AccountView(displayName = "Someone", id = OFFBOARDING_ACCOUNT),
        tokens = TokenView(
            accessExpiresAt = java.time.OffsetDateTime.now(),
            accessToken = "access",
            refreshExpiresAt = java.time.OffsetDateTime.now(),
            refreshToken = "refresh",
        ),
    )
}
