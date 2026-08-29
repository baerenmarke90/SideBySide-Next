package de.sidebyside.next.reference

import java.time.OffsetDateTime
import java.util.UUID
import kotlinx.coroutines.CompletableDeferred
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.ExperimentalCoroutinesApi
import kotlinx.coroutines.test.TestScope
import kotlinx.coroutines.test.UnconfinedTestDispatcher
import kotlinx.coroutines.test.advanceUntilIdle
import kotlinx.coroutines.test.resetMain
import kotlinx.coroutines.test.runTest
import kotlinx.coroutines.test.setMain
import org.junit.After
import org.junit.Assert.assertArrayEquals
import org.junit.Assert.assertEquals
import org.junit.Assert.assertNull
import org.junit.Before
import org.junit.Test
import sidebyside.api.models.AccountView
import sidebyside.api.models.AttachmentDetail
import sidebyside.api.models.AttachmentReadRequest
import sidebyside.api.models.AttachmentUploadCreate
import sidebyside.api.models.MediaType
import sidebyside.api.models.MemoryAttachmentSet
import sidebyside.api.models.MemoryCreate
import sidebyside.api.models.MemoryDetail
import sidebyside.api.models.ReadDescriptor
import sidebyside.api.models.SessionView
import sidebyside.api.models.StoryPage
import sidebyside.api.models.TokenView
import sidebyside.api.models.UploadDescriptor

@OptIn(ExperimentalCoroutinesApi::class)
class ReferenceViewModelAttachmentTest {
    private val dispatcher = UnconfinedTestDispatcher()
    private val spaceId = UUID.fromString("00000000-0000-0000-0000-000000000010")
    private val attachmentId = UUID.fromString("00000000-0000-0000-0000-000000000030")

    @Before
    fun setUp() {
        Dispatchers.setMain(dispatcher)
    }

    @After
    fun tearDown() {
        Dispatchers.resetMain()
    }

    @Test
    fun selectionShowsLocalBytesImmediatelyAndRemovalIgnoresLateUploadCompletion() = runTest(dispatcher) {
        val releaseUpload = CompletableDeferred<Unit>()
        val api = AttachmentContract {
            releaseUpload.await()
        }
        val viewModel = viewModel(api)
        signIn(viewModel)
        val selectionEpoch = checkNotNull(viewModel.beginImageSelection())
        val image = SelectedImage(byteArrayOf(1, 2, 3), "draft.jpg", "image/jpeg")

        viewModel.selectImage(image, selectionEpoch)

        assertEquals("draft.jpg", viewModel.uiState.value.selectedImageName)
        assertArrayEquals(image.bytes, viewModel.uiState.value.selectedImageBytes)
        assertEquals(DraftUploadState.UPLOADING, viewModel.uiState.value.imageUploadState)

        viewModel.removeSelectedImage()
        releaseUpload.complete(Unit)
        advanceUntilIdle()

        assertNull(viewModel.uiState.value.selectedImageName)
        assertNull(viewModel.uiState.value.selectedImageBytes)
        assertNull(viewModel.uiState.value.imageUploadState)
    }

    @Test
    fun failedUploadCanRetryWithoutSelectingTheImageAgain() = runTest(dispatcher) {
        var attempts = 0
        val api = AttachmentContract {
            attempts += 1
            if (attempts == 1) error("first upload failed")
        }
        val viewModel = viewModel(api)
        signIn(viewModel)
        val selectionEpoch = checkNotNull(viewModel.beginImageSelection())
        val image = SelectedImage(byteArrayOf(4, 5, 6), "retry.jpg", "image/jpeg")

        viewModel.selectImage(image, selectionEpoch)
        advanceUntilIdle()
        assertEquals(DraftUploadState.FAILED, viewModel.uiState.value.imageUploadState)
        assertEquals("retry.jpg", viewModel.uiState.value.selectedImageName)

        viewModel.retrySelectedImage()
        advanceUntilIdle()

        assertEquals(2, attempts)
        assertEquals(DraftUploadState.READY, viewModel.uiState.value.imageUploadState)
        assertEquals("retry.jpg", viewModel.uiState.value.selectedImageName)
        assertArrayEquals(image.bytes, viewModel.uiState.value.selectedImageBytes)
    }

    private fun viewModel(api: ReferenceContract) = ReferenceViewModel(
        config = ReferenceConfig(apiBaseUrl = "https://sidebyside.invalid", spaceId = spaceId),
        api = api,
    )

    private fun TestScope.signIn(viewModel: ReferenceViewModel) {
        viewModel.signIn("person@example.com", "secret")
        advanceUntilIdle()
    }

    private inner class AttachmentContract(
        private val upload: suspend () -> Unit,
    ) : ReferenceContract {
        override suspend fun signIn(email: String, password: String): SessionView = session()

        override suspend fun createMemory(
            spaceId: UUID,
            accessToken: String,
            memory: MemoryCreate,
        ): MemoryDetail = error("not used")

        override suspend fun createAttachmentUpload(
            spaceId: UUID,
            accessToken: String,
            request: AttachmentUploadCreate,
        ): UploadDescriptor = UploadDescriptor(
            attachment = attachment("UPLOADING"),
            method = UploadDescriptor.Method.STREAM,
            requiredHeaders = mapOf("Content-Type" to request.expectedMimeType),
            uploadUrl = "/content",
        )

        override suspend fun uploadAttachmentBytes(
            accessToken: String,
            descriptor: UploadDescriptor,
            image: SelectedImage,
        ) = upload()

        override suspend fun finalizeAttachment(
            spaceId: UUID,
            accessToken: String,
            attachmentId: UUID,
        ): AttachmentDetail = attachment("VALIDATING")

        override suspend fun getAttachment(
            spaceId: UUID,
            accessToken: String,
            attachmentId: UUID,
        ): AttachmentDetail = attachment("READY")

        override suspend fun replaceMemoryAttachments(
            spaceId: UUID,
            accessToken: String,
            memoryId: UUID,
            ifMatch: Int,
            attachments: MemoryAttachmentSet,
        ): MemoryDetail = error("not used")

        override suspend fun getTimeline(spaceId: UUID, accessToken: String): StoryPage =
            StoryPage(hasMore = false, items = emptyList(), nextCursor = null)

        override suspend fun createReadAccess(
            spaceId: UUID,
            accessToken: String,
            attachmentId: UUID,
            request: AttachmentReadRequest,
        ): ReadDescriptor = error("not used")

        override suspend fun readImageBytes(accessToken: String, descriptor: ReadDescriptor): ByteArray =
            error("not used")
    }

    private fun attachment(status: String) = AttachmentDetail(
        createdAt = OffsetDateTime.parse("2026-08-29T20:00:00Z"),
        durationSeconds = null,
        hasThumbnail = false,
        height = null,
        id = attachmentId,
        mediaType = MediaType.IMAGE,
        mimeType = "image/jpeg",
        propertySize = 3,
        status = status,
        version = 1,
        width = null,
    )

    private fun session(): SessionView {
        val now = OffsetDateTime.parse("2026-08-29T20:00:00Z")
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
