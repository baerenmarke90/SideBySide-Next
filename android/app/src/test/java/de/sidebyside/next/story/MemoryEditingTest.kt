package de.sidebyside.next.story

import de.sidebyside.next.demo.DemoPersona
import de.sidebyside.next.reference.FakeReferenceContract
import de.sidebyside.next.reference.ReferenceApiException
import de.sidebyside.next.reference.ReferenceConfig
import de.sidebyside.next.reference.ReferenceContract
import de.sidebyside.next.reference.ReferenceViewModel
import de.sidebyside.next.reference.SelectedImage
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
import sidebyside.api.models.AuthorSummary
import sidebyside.api.models.MemoryAttachmentSet
import sidebyside.api.models.MemoryCreate
import sidebyside.api.models.MemoryDetail
import sidebyside.api.models.MemoryUpdate
import sidebyside.api.models.ReadDescriptor
import sidebyside.api.models.ResourceCapabilities
import sidebyside.api.models.SessionView
import sidebyside.api.models.StoryPage
import sidebyside.api.models.TokenView
import sidebyside.api.models.UploadDescriptor

private val SPACE: UUID = UUID.fromString("11111111-1111-4111-8111-111111111111")
private val MEMORY: UUID = UUID.fromString("33333333-3333-4333-8333-333333333333")

/**
 * Changing and removing a memory.
 *
 * The interesting case is the conflict: the partner changed the same memory
 * meanwhile, and the answer must be recoverable rather than a lost write or
 * lost text.
 */
@OptIn(ExperimentalCoroutinesApi::class)
class MemoryEditingTest {
    private val dispatcher = StandardTestDispatcher()

    @Before
    fun setUp() = Dispatchers.setMain(dispatcher)

    @After
    fun tearDown() = Dispatchers.resetMain()

    @Test
    fun opensAMemoryWithTheVersionAChangeHasToBeWrittenAgainst() = runTest(dispatcher) {
        val api = MemoryApi()
        val model = signedIn(api)

        model.openMemory(MEMORY)
        advanceUntilIdle()

        assertEquals(MEMORY, model.uiState.value.openMemory?.id)
        assertEquals(7, model.uiState.value.openMemory?.version)
        assertFalse(model.uiState.value.memoryBusy)
    }

    @Test
    fun writesAChangeAgainstTheVersionItWasMadeFrom() = runTest(dispatcher) {
        val api = MemoryApi()
        val model = signedIn(api)

        model.openMemory(MEMORY)
        advanceUntilIdle()
        model.saveMemory("A new title", "A new text", "2026-08-20")
        advanceUntilIdle()

        assertEquals(listOf(7), api.updateVersions)
        assertEquals("A new title", api.updates.single().title)
        assertEquals(LocalDate.of(2026, 8, 20), api.updates.single().happenedOn)
        assertNull(model.uiState.value.memoryProblem)
    }

    @Test
    fun reportsAConflictAsRecoverableAndReloadsTheVersionToRetryWith() =
        runTest(dispatcher) {
            // The partner changed the memory in between. The refusal must be
            // visible, and the next attempt must carry the version they left,
            // or it would be refused forever.
            val api = MemoryApi(updateFailure = ReferenceApiException(null, "conflict", 409))
            val model = signedIn(api)

            model.openMemory(MEMORY)
            advanceUntilIdle()
            model.saveMemory("A new title", "A new text", "")
            advanceUntilIdle()

            assertEquals(UiStateKind.Conflict, model.uiState.value.memoryProblem?.kind)
            assertFalse(model.uiState.value.memoryBusy)
            // Reloaded, so the memory on screen is the partner's current one.
            assertTrue(api.getCalls >= 2)
        }

    @Test
    fun aConflictLeavesTheMemoryOpenSoTheTypedTextIsNotThrownAway() =
        runTest(dispatcher) {
            // The form holds the text; the view model must not close the memory
            // out from under it, which would take the text with it.
            val api = MemoryApi(updateFailure = ReferenceApiException(null, "conflict", 409))
            val model = signedIn(api)

            model.openMemory(MEMORY)
            advanceUntilIdle()
            model.saveMemory("A new title", "A new text", "")
            advanceUntilIdle()

            assertEquals(MEMORY, model.uiState.value.openMemory?.id)
            assertFalse(model.uiState.value.openMemoryGone)
        }

    @Test
    fun closesTheFormOnceTheChangeIsWritten() = runTest(dispatcher) {
        // Leaving it open made a successful save look as though nothing had
        // happened: the same fields, the same buttons, no confirmation.
        val api = MemoryApi()
        val model = signedIn(api)

        model.openMemory(MEMORY)
        advanceUntilIdle()
        model.beginEditingMemory()
        model.saveMemory("A new title", "A new text", "")
        advanceUntilIdle()

        assertFalse(model.uiState.value.editingMemory)
        assertTrue(model.uiState.value.memoryStatus != null)
    }

    @Test
    fun confirmsASaveWithoutBorrowingAMessageFromSomewhereElse() = runTest(dispatcher) {
        // The demo banner, sign-in and Space switch all write to `status`.
        // Reusing it here put the demo-entry notice on the memory screen
        // dressed as a save confirmation.
        val api = MemoryApi()
        val model = signedIn(api)

        model.openMemory(MEMORY)
        advanceUntilIdle()
        assertNull(model.uiState.value.memoryStatus)

        model.beginEditingMemory()
        model.saveMemory("A new title", "A new text", "")
        advanceUntilIdle()
        assertTrue(model.uiState.value.memoryStatus != null)

        model.closeMemory()
        assertNull(model.uiState.value.memoryStatus)
    }

    @Test
    fun keepsTheFormOpenOnAConflictSoTheChangeCanBeMadeAgain() = runTest(dispatcher) {
        val api = MemoryApi(updateFailure = ReferenceApiException(null, "conflict", 409))
        val model = signedIn(api)

        model.openMemory(MEMORY)
        advanceUntilIdle()
        model.beginEditingMemory()
        model.saveMemory("A new title", "A new text", "")
        advanceUntilIdle()

        assertTrue(model.uiState.value.editingMemory)
    }

    @Test
    fun removesAMemoryAndTheStoryEntryThatShowedIt() = runTest(dispatcher) {
        val api = MemoryApi()
        val model = signedIn(api)

        model.openMemory(MEMORY)
        advanceUntilIdle()
        model.deleteMemory()
        advanceUntilIdle()

        assertEquals(listOf(7), api.deleteVersions)
        assertTrue(model.uiState.value.openMemoryGone)
        assertNull(model.uiState.value.openMemory)
        // The Story is re-read, so the deleted entry does not linger.
        assertTrue(api.timelineCalls >= 2)
    }

    @Test
    fun aMemoryThePartnerAlreadyDeletedFailsClearlyRatherThanSilently() =
        runTest(dispatcher) {
            val api = MemoryApi(getFailure = ReferenceApiException(null, "gone", 404))
            val model = signedIn(api)

            model.openMemory(MEMORY)
            advanceUntilIdle()

            assertNull(model.uiState.value.openMemory)
            assertEquals(UiStateKind.Permission, model.uiState.value.memoryProblem?.kind)
        }

    @Test
    fun refusesAnUnreadableDateWithoutSendingAnything() = runTest(dispatcher) {
        val api = MemoryApi()
        val model = signedIn(api)

        model.openMemory(MEMORY)
        advanceUntilIdle()
        model.saveMemory("A title", "A text", "20.08.2026")
        advanceUntilIdle()

        assertTrue(api.updates.isEmpty())
        assertTrue(model.uiState.value.error != null)
    }

    @Test
    fun forgetsTheOpenMemoryWhenItsScreenIsLeft() = runTest(dispatcher) {
        val api = MemoryApi()
        val model = signedIn(api)

        model.openMemory(MEMORY)
        advanceUntilIdle()
        model.closeMemory()

        assertNull(model.uiState.value.openMemory)
        assertNull(model.uiState.value.memoryProblem)
    }

    /** Signed in and settled, so a Space is resolved before anything opens. */
    private fun TestScope.signedIn(api: ReferenceContract): ReferenceViewModel {
        val model = ReferenceViewModel(config = ReferenceConfig(BASE_URL), api = api)
        model.signIn("someone@example.test", "secret")
        advanceUntilIdle()
        return model
    }
}

private const val BASE_URL = "https://sidebyside.example"

private fun memoryDetail(version: Int) = MemoryDetail(
    attachments = emptyList(),
    author = AuthorSummary(displayName = "Lea", id = UUID.randomUUID()),
    authorId = UUID.randomUUID(),
    body = "The text as the server has it",
    capabilities = ResourceCapabilities(canComment = true, canDelete = true, canEdit = true),
    createdAt = OffsetDateTime.now(),
    happenedOn = LocalDate.of(2026, 8, 17),
    id = MEMORY,
    spaceId = SPACE,
    title = "The title as the server has it",
    updatedAt = OffsetDateTime.now(),
    version = version,
)

private class MemoryApi(
    private val updateFailure: Throwable? = null,
    private val getFailure: Throwable? = null,
) : FakeReferenceContract() {
    val updates = mutableListOf<MemoryUpdate>()
    val updateVersions = mutableListOf<Int>()
    val deleteVersions = mutableListOf<Int>()
    var getCalls = 0
    var timelineCalls = 0

    override suspend fun signIn(email: String, password: String): SessionView = SessionView(
        account = AccountView(displayName = "Lea", id = UUID.randomUUID()),
        tokens = TokenView(
            accessExpiresAt = OffsetDateTime.now(),
            accessToken = "access",
            refreshExpiresAt = OffsetDateTime.now(),
            refreshToken = "refresh",
        ),
    )

    override suspend fun consumeMagicLink(token: String): SessionView = signIn("demo", "demo")

    override suspend fun listMemberships(accessToken: String): List<AccountMembershipView> =
        listOf(AccountMembershipView(role = "PARTNER", spaceId = SPACE, status = "ACTIVE"))


    override suspend fun getMemory(
        spaceId: UUID,
        accessToken: String,
        memoryId: UUID,
    ): MemoryDetail {
        getCalls += 1
        getFailure?.let { throw it }
        return memoryDetail(version = 7)
    }

    override suspend fun updateMemory(
        spaceId: UUID,
        accessToken: String,
        memoryId: UUID,
        ifMatch: Int,
        update: MemoryUpdate,
    ): MemoryDetail {
        updateVersions += ifMatch
        updates += update
        updateFailure?.let { throw it }
        return memoryDetail(version = ifMatch + 1)
    }

    override suspend fun deleteMemory(
        spaceId: UUID,
        accessToken: String,
        memoryId: UUID,
        ifMatch: Int,
    ) {
        deleteVersions += ifMatch
    }

    override suspend fun getTimeline(
        spaceId: UUID,
        accessToken: String,
        cursor: String?,
    ): StoryPage {
        timelineCalls += 1
        return StoryPage(hasMore = false, items = emptyList(), nextCursor = null)
    }








}
