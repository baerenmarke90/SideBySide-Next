package de.sidebyside.next.privatearea

import de.sidebyside.next.reference.FakeReferenceContract
import de.sidebyside.next.reference.ReferenceConfig
import de.sidebyside.next.reference.ReferenceViewModel
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
import sidebyside.api.models.PrivateNoteCreate
import sidebyside.api.models.PrivateNoteDetail
import sidebyside.api.models.PrivateNotePage
import sidebyside.api.models.PrivateNoteUpdate
import sidebyside.api.models.ResourceCapabilities
import sidebyside.api.models.SessionView
import sidebyside.api.models.TokenView

private val SPACE: UUID = UUID.fromString("11111111-1111-4111-8111-111111111111")

/**
 * #356: owner-only PrivateNote CRUD. The privacy property worth pinning is
 * not "does the list show the right notes" — the server already filters
 * that — but that a Space or Account switch leaves nothing of a previous
 * owner's notes sitting in memory, per #356's own acceptance criterion.
 */
@OptIn(ExperimentalCoroutinesApi::class)
class PrivateNoteTest {
    private val dispatcher = StandardTestDispatcher()

    @Before
    fun setUp() = Dispatchers.setMain(dispatcher)

    @After
    fun tearDown() = Dispatchers.resetMain()

    @Test
    fun loadingPopulatesTheList() = runTest(dispatcher) {
        val note = note("Shopping list")
        val api = PrivateNoteApi(notes = listOf(note))
        val model = ReferenceViewModel(config = ReferenceConfig(BASE_URL), api = api)

        signIn(model)
        model.loadPrivateNotes()
        advanceUntilIdle()

        assertEquals(listOf(note), model.uiState.value.privateNotes)
    }

    @Test
    fun addingWithABlankTitleMakesNoCall() = runTest(dispatcher) {
        val api = PrivateNoteApi()
        val model = ReferenceViewModel(config = ReferenceConfig(BASE_URL), api = api)

        signIn(model)
        model.addPrivateNote("   ", "text", false)
        advanceUntilIdle()

        assertTrue(api.created.isEmpty())
    }

    @Test
    fun addingSendsTheTitleBodyAndPinnedFlag() = runTest(dispatcher) {
        val api = PrivateNoteApi()
        val model = ReferenceViewModel(config = ReferenceConfig(BASE_URL), api = api)

        signIn(model)
        model.addPrivateNote("Gift ideas", "Something cozy", true)
        advanceUntilIdle()

        assertEquals(1, api.created.size)
        assertEquals("Gift ideas", api.created.first().title)
        assertEquals("Something cozy", api.created.first().body)
        assertEquals(true, api.created.first().pinned)
    }

    @Test
    fun updatingSendsTheCurrentVersionAsIfMatch() = runTest(dispatcher) {
        val target = note("Old title", version = 4)
        val api = PrivateNoteApi(notes = listOf(target))
        val model = ReferenceViewModel(config = ReferenceConfig(BASE_URL), api = api)

        signIn(model)
        model.updatePrivateNote(target, "New title", "New body", false)
        advanceUntilIdle()

        assertEquals(1, api.updated.size)
        assertEquals(target.id, api.updated.first().first)
        assertEquals(4, api.updated.first().second)
    }

    @Test
    fun deletingSendsTheEntrysOwnVersion() = runTest(dispatcher) {
        val target = note("To delete", version = 2)
        val api = PrivateNoteApi(notes = listOf(target))
        val model = ReferenceViewModel(config = ReferenceConfig(BASE_URL), api = api)

        signIn(model)
        model.deletePrivateNote(target)
        advanceUntilIdle()

        assertEquals(listOf(target.id to 2), api.deleted)
    }

    @Test
    fun forgetsPrivateNotesWhenTheSessionEnds() = runTest(dispatcher) {
        val api = PrivateNoteApi(notes = listOf(note("Shopping list")))
        val model = ReferenceViewModel(config = ReferenceConfig(BASE_URL), api = api)

        signIn(model)
        model.loadPrivateNotes()
        advanceUntilIdle()
        assertTrue(model.uiState.value.privateNotes.isNotEmpty())

        model.logout()

        assertTrue(model.uiState.value.privateNotes.isEmpty())
    }

    @Test
    fun forgetsPrivateNotesWhenTheSpaceChanges() = runTest(dispatcher) {
        val otherSpace = UUID.fromString("22222222-2222-4222-8222-222222222222")
        val api = PrivateNoteApi(notes = listOf(note("Shopping list")), otherSpaces = listOf(otherSpace))
        val model = ReferenceViewModel(config = ReferenceConfig(BASE_URL), api = api)

        signIn(model)
        model.loadPrivateNotes()
        advanceUntilIdle()
        assertTrue(model.uiState.value.privateNotes.isNotEmpty())

        model.selectSpace(otherSpace)
        advanceUntilIdle()

        assertTrue(model.uiState.value.privateNotes.isEmpty())
    }

    private suspend fun TestScope.signIn(model: ReferenceViewModel) {
        model.signIn("someone@example.test", "secret")
        advanceUntilIdle()
    }
}

private const val BASE_URL = "https://sidebyside.example"

private val FULL_CAPABILITIES = ResourceCapabilities(canComment = false, canDelete = true, canEdit = true)

private fun note(title: String, version: Int = 1) = PrivateNoteDetail(
    body = "",
    capabilities = FULL_CAPABILITIES,
    createdAt = OffsetDateTime.now(),
    id = UUID.randomUUID(),
    ownerId = UUID.randomUUID(),
    pinned = false,
    spaceId = SPACE,
    title = title,
    updatedAt = OffsetDateTime.now(),
    version = version,
)

private class PrivateNoteApi(
    private val notes: List<PrivateNoteDetail> = emptyList(),
    private val otherSpaces: List<UUID> = emptyList(),
) : FakeReferenceContract() {
    val created = mutableListOf<PrivateNoteCreate>()
    val updated = mutableListOf<Pair<UUID, Int>>()
    val deleted = mutableListOf<Pair<UUID, Int>>()

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
        listOf(AccountMembershipView(role = "PARTNER", spaceId = SPACE, status = "ACTIVE")) +
            otherSpaces.map { AccountMembershipView(role = "PARTNER", spaceId = it, status = "ACTIVE") }

    override suspend fun listPrivateNotes(
        spaceId: UUID,
        accessToken: String,
        cursor: String?,
    ): PrivateNotePage = PrivateNotePage(
        hasMore = false,
        items = if (spaceId == SPACE) notes else emptyList(),
        nextCursor = null,
    )

    override suspend fun createPrivateNote(
        spaceId: UUID,
        accessToken: String,
        fields: PrivateNoteCreate,
    ): PrivateNoteDetail {
        created += fields
        return note(fields.title)
    }

    override suspend fun updatePrivateNote(
        spaceId: UUID,
        accessToken: String,
        noteId: UUID,
        ifMatch: Int,
        fields: PrivateNoteUpdate,
    ): PrivateNoteDetail {
        updated += noteId to ifMatch
        return note(fields.title ?: "Updated")
    }

    override suspend fun deletePrivateNote(spaceId: UUID, accessToken: String, noteId: UUID, ifMatch: Int) {
        deleted += noteId to ifMatch
    }
}
