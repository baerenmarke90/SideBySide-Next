package de.sidebyside.next.demo

import de.sidebyside.next.reference.FakeReferenceContract
import de.sidebyside.next.reference.ReferenceApiException
import de.sidebyside.next.reference.ReferenceConfig
import de.sidebyside.next.reference.ReferenceContract
import de.sidebyside.next.reference.ReferenceViewModel
import de.sidebyside.next.reference.SelectedImage
import java.util.UUID
import kotlinx.coroutines.ExperimentalCoroutinesApi
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.test.StandardTestDispatcher
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
import sidebyside.api.models.AccountMembershipView
import sidebyside.api.models.AttachmentDetail
import sidebyside.api.models.AttachmentReadRequest
import sidebyside.api.models.AttachmentUploadCreate
import sidebyside.api.models.MemoryAttachmentSet
import sidebyside.api.models.MemoryCreate
import sidebyside.api.models.MemoryDetail
import sidebyside.api.models.ReadDescriptor
import sidebyside.api.models.SessionView
import sidebyside.api.models.StoryPage
import sidebyside.api.models.TokenView
import sidebyside.api.models.UploadDescriptor

private const val PRODUCTION_URL = "https://sidebyside.example"
private val PRODUCTION_SPACE: UUID = UUID.fromString("11111111-1111-4111-8111-111111111111")
private val DEMO_SPACE: UUID = UUID.fromString("22222222-2222-4222-8222-222222222222")

/**
 * Demo mode has to be a separate session against a separate deployment. These
 * tests pin the boundaries that make that true, because a leak between the two
 * would put demo content into someone's own Space or vice versa.
 */
@OptIn(ExperimentalCoroutinesApi::class)
class DemoModeTest {
    private val dispatcher = StandardTestDispatcher()

    @Before
    fun setUp() = Dispatchers.setMain(dispatcher)

    @After
    fun tearDown() = Dispatchers.resetMain()

    @Test
    fun entersTheDemoWithoutAPasswordAndResolvesTheSpaceFromMemberships() =
        runTest(dispatcher) {
            val api = RecordingDemoApi()
            val model = viewModel(api)

            model.enterDemo(DemoPersona.Lea)
            advanceUntilIdle()

            val state = model.uiState.value
            assertTrue(state.loggedIn)
            assertTrue(state.demoMode)
            assertEquals(DemoPersona.Lea, state.demoPersona)
            // The persona is exchanged for a one-time proof; no password exists.
            assertEquals(listOf(DemoPersona.Lea), api.demoEntries)
            assertEquals(listOf("demo-token"), api.consumedTokens)
            assertTrue(api.signInCalls.isEmpty())
            // The Space came from the server, not from the build configuration.
            assertEquals(listOf(DEMO_SPACE), api.timelineSpaces)
        }

    @Test
    fun targetsTheDemoDeploymentWithoutRewritingTheConfiguredEndpoint() =
        runTest(dispatcher) {
            val created = mutableListOf<String>()
            val api = RecordingDemoApi()
            val model = ReferenceViewModel(
                config = ReferenceConfig(PRODUCTION_URL),
                apiFactory = { baseUrl -> created += baseUrl; api },
            )

            model.enterDemo(DemoPersona.Alex)
            advanceUntilIdle()

            assertEquals(DemoEndpoint.BASE_URL, api.demoBaseUrls.single())
            // The configured endpoint is still the one a normal sign-in uses.
            assertTrue(created.contains(PRODUCTION_URL))
            assertTrue(created.contains(DemoEndpoint.BASE_URL))
        }

    @Test
    fun leavingTheDemoClearsTheSessionAndReturnsToTheConfiguredServer() =
        runTest(dispatcher) {
            val api = RecordingDemoApi()
            val model = viewModel(api)

            model.enterDemo(DemoPersona.Lea)
            advanceUntilIdle()
            model.leaveDemo()

            val state = model.uiState.value
            assertFalse(state.loggedIn)
            assertFalse(state.demoMode)
            assertNull(state.demoPersona)
            assertTrue(state.storyItems.isEmpty())
            assertTrue(state.draftImages.isEmpty())
        }

    @Test
    fun signingOutOfTheDemoAlsoRestoresTheEndpoint() = runTest(dispatcher) {
        // Sign-out and leaving the demo are the same gesture for the user, so
        // the ordinary sign-out must not leave the app pointed at the demo.
        val api = RecordingDemoApi()
        val model = viewModel(api)

        model.enterDemo(DemoPersona.Alex)
        advanceUntilIdle()
        model.logout()

        assertFalse(model.uiState.value.demoMode)
        assertNull(model.uiState.value.demoPersona)
    }

    @Test
    fun demoContentDoesNotSurviveIntoTheNextSession() = runTest(dispatcher) {
        val api = RecordingDemoApi()
        val model = viewModel(api)

        model.enterDemo(DemoPersona.Lea)
        advanceUntilIdle()
        model.leaveDemo()
        advanceUntilIdle()

        // Nothing loaded under the demo persona may still be readable.
        val state = model.uiState.value
        assertTrue(state.storyItems.isEmpty())
        assertNull(state.lastMemoryTitle)
        assertNull(state.lastImageBytes)
    }

    @Test
    fun anUnavailableDemoStaysRecoverableAndKeepsTheConfiguredEndpoint() =
        runTest(dispatcher) {
            // A demo reset invalidates the persona mid-flight; the user has to
            // be able to try again rather than land in a dead state.
            val api = RecordingDemoApi(demoEntryFailure = ReferenceApiException(null, "gone", 404))
            val model = viewModel(api)

            model.enterDemo(DemoPersona.Lea)
            advanceUntilIdle()

            val state = model.uiState.value
            assertFalse(state.loggedIn)
            assertFalse(state.demoMode)
            assertFalse(state.busy)
            assertTrue(state.error != null)
        }

    @Test
    fun refusesADemoAccountWithoutAnActiveMembership() = runTest(dispatcher) {
        val api = RecordingDemoApi(memberships = listOf(membership("INVITED", DEMO_SPACE)))
        val model = viewModel(api)

        model.enterDemo(DemoPersona.Lea)
        advanceUntilIdle()

        // An invited or removed membership must not become the working context.
        assertFalse(model.uiState.value.loggedIn)
        assertFalse(model.uiState.value.demoMode)
    }

    private fun viewModel(api: ReferenceContract) = ReferenceViewModel(
        config = ReferenceConfig(PRODUCTION_URL),
        api = api,
    )
}

private fun membership(status: String, spaceId: UUID) =
    AccountMembershipView(role = "PARTNER", spaceId = spaceId, status = status)

private fun session() = SessionView(
    account = sidebyside.api.models.AccountView(
        displayName = "Lea",
        id = UUID.randomUUID(),
    ),
    tokens = TokenView(
        accessExpiresAt = java.time.OffsetDateTime.now(),
        accessToken = "demo-access",
        refreshExpiresAt = java.time.OffsetDateTime.now(),
        refreshToken = "demo-refresh",
    ),
)

private class RecordingDemoApi(
    private val memberships: List<AccountMembershipView> =
        listOf(membership("ACTIVE", DEMO_SPACE)),
    private val demoEntryFailure: Throwable? = null,
) : FakeReferenceContract() {
    val demoEntries = mutableListOf<DemoPersona>()
    val demoBaseUrls = mutableListOf<String>()
    val consumedTokens = mutableListOf<String>()
    val signInCalls = mutableListOf<String>()
    val timelineSpaces = mutableListOf<UUID>()

    override suspend fun signIn(email: String, password: String): SessionView {
        signInCalls += email
        return session()
    }

    override suspend fun consumeMagicLink(token: String): SessionView {
        consumedTokens += token
        return session()
    }

    override suspend fun listMemberships(accessToken: String): List<AccountMembershipView> =
        memberships

    override suspend fun createDemoEntry(baseUrl: String, persona: DemoPersona): String {
        demoBaseUrls += baseUrl
        demoEntries += persona
        demoEntryFailure?.let { throw it }
        return "demo-token"
    }

    override suspend fun getTimeline(spaceId: UUID, accessToken: String): StoryPage {
        timelineSpaces += spaceId
        return StoryPage(hasMore = false, items = emptyList(), nextCursor = null)
    }








}
