package de.sidebyside.next.reference

import java.time.OffsetDateTime
import java.util.UUID
import kotlinx.coroutines.CompletableDeferred
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.ExperimentalCoroutinesApi
import kotlinx.coroutines.test.UnconfinedTestDispatcher
import kotlinx.coroutines.test.advanceUntilIdle
import kotlinx.coroutines.test.resetMain
import kotlinx.coroutines.test.runTest
import kotlinx.coroutines.test.setMain
import org.junit.After
import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertNull
import org.junit.Before
import org.junit.Test
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

@OptIn(ExperimentalCoroutinesApi::class)
class ReferenceViewModelTest {
    private val dispatcher = UnconfinedTestDispatcher()
    private val spaceId = UUID.fromString("00000000-0000-0000-0000-000000000010")

    @Before
    fun setUp() {
        Dispatchers.setMain(dispatcher)
    }

    @After
    fun tearDown() {
        Dispatchers.resetMain()
    }

    @Test
    fun logoutIgnoresLateTimelineFailureFromPreviousSession() = runTest(dispatcher) {
        val releaseSecondTimeline = CompletableDeferred<Unit>()
        var timelineCalls = 0
        val api = object : ReferenceContract {
            override suspend fun signIn(email: String, password: String): SessionView = session()

            override suspend fun getTimeline(spaceId: UUID, accessToken: String): StoryPage {
                timelineCalls += 1
                if (timelineCalls == 1) {
                    return StoryPage(hasMore = false, items = emptyList(), nextCursor = null)
                }
                releaseSecondTimeline.await()
                error("late timeline failure")
            }

            override suspend fun createMemory(spaceId: UUID, accessToken: String, memory: MemoryCreate): MemoryDetail =
                error("not used")

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

            override suspend fun readImageBytes(accessToken: String, descriptor: ReadDescriptor): ByteArray =
                error("not used")
        }
        val viewModel = ReferenceViewModel(
            config = ReferenceConfig(apiBaseUrl = "https://sidebyside.invalid", spaceId = spaceId),
            api = api,
        )

        viewModel.signIn("person@example.com", "secret")
        advanceUntilIdle()
        assertEquals(1, timelineCalls)

        viewModel.refreshStory()
        assertEquals(2, timelineCalls)
        viewModel.logout()

        releaseSecondTimeline.complete(Unit)
        advanceUntilIdle()

        val state = viewModel.uiState.value
        assertFalse(state.loggedIn)
        assertEquals("Abgemeldet.", state.status)
        assertNull(state.error)
        assertEquals(emptyList<Any>(), state.storyItems)
    }

    private fun session(): SessionView {
        val now = OffsetDateTime.parse("2026-08-26T08:00:00Z")
        return SessionView(
            account = AccountView(
                displayName = "Test Person",
                id = UUID.fromString("00000000-0000-0000-0000-000000000020"),
            ),
            tokens = TokenView(
                accessExpiresAt = now.plusMinutes(15),
                accessToken = "access-token",
                refreshExpiresAt = now.plusDays(30),
                refreshToken = "refresh-token",
            ),
        )
    }
}
