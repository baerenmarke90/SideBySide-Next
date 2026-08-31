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
        assertFalse(model.uiState.value.loggedIn)
        assertNull(model.uiState.value.activeSpaceId)
        assertTrue(model.uiState.value.error != null)
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
    fun signingOutForgetsTheSpace() = runTest(dispatcher) {
        val api = SpaceApi(memberships = listOf(active(FIRST_SPACE)))
        val model = ReferenceViewModel(config = ReferenceConfig(BASE_URL), api = api)

        model.signIn("someone@example.test", "secret")
        advanceUntilIdle()
        model.logout()

        assertNull(model.uiState.value.activeSpaceId)
        assertTrue(model.uiState.value.availableSpaces.isEmpty())
    }
}

private const val BASE_URL = "https://sidebyside.example"

private fun active(spaceId: UUID) = membership("ACTIVE", spaceId)

private fun membership(status: String, spaceId: UUID) =
    AccountMembershipView(role = "PARTNER", spaceId = spaceId, status = status)

private class SpaceApi(
    private val memberships: List<AccountMembershipView>,
    private val holdTimelineAfter: Int = Int.MAX_VALUE,
    private val releaseHeldTimeline: CompletableDeferred<Unit>? = null,
) : ReferenceContract {
    val timelineSpaces = mutableListOf<UUID>()
    private var timelineCalls = 0

    override suspend fun signIn(email: String, password: String): SessionView = SessionView(
        account = AccountView(displayName = "Someone", id = UUID.randomUUID()),
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

    override suspend fun createDemoEntry(baseUrl: String, persona: DemoPersona): String =
        error("Demo entry is not exercised by this test.")

    override suspend fun getTimeline(spaceId: UUID, accessToken: String): StoryPage {
        timelineCalls += 1
        timelineSpaces += spaceId
        if (timelineCalls > holdTimelineAfter) {
            releaseHeldTimeline?.await()
        }
        return StoryPage(hasMore = false, items = emptyList(), nextCursor = null)
    }

    override suspend fun createMemory(
        spaceId: UUID,
        accessToken: String,
        memory: MemoryCreate,
    ): MemoryDetail = error("not used")

    override suspend fun createAttachmentUpload(
        spaceId: UUID,
        accessToken: String,
        request: AttachmentUploadCreate,
    ): UploadDescriptor = error("not used")

    override suspend fun uploadAttachmentBytes(
        accessToken: String,
        descriptor: UploadDescriptor,
        image: SelectedImage,
    ) = error("not used")

    override suspend fun finalizeAttachment(
        spaceId: UUID,
        accessToken: String,
        attachmentId: UUID,
    ): AttachmentDetail = error("not used")

    override suspend fun getAttachment(
        spaceId: UUID,
        accessToken: String,
        attachmentId: UUID,
    ): AttachmentDetail = error("not used")

    override suspend fun replaceMemoryAttachments(
        spaceId: UUID,
        accessToken: String,
        memoryId: UUID,
        ifMatch: Int,
        attachments: MemoryAttachmentSet,
    ): MemoryDetail = error("not used")

    override suspend fun createReadAccess(
        spaceId: UUID,
        accessToken: String,
        attachmentId: UUID,
        request: AttachmentReadRequest,
    ): ReadDescriptor = error("not used")

    override suspend fun readImageBytes(
        accessToken: String,
        descriptor: ReadDescriptor,
    ): ByteArray = error("not used")
}
