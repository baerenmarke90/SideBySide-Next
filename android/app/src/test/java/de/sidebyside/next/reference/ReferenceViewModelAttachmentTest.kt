package de.sidebyside.next.reference

import de.sidebyside.next.demo.DemoPersona
import sidebyside.api.models.AccountMembershipView
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
import org.junit.Assert.assertEquals
import org.junit.Assert.assertNotNull
import org.junit.Before
import org.junit.Test
import sidebyside.api.models.AccountView
import sidebyside.api.models.AttachmentDetail
import sidebyside.api.models.AttachmentReadRequest
import sidebyside.api.models.AttachmentUploadCreate
import sidebyside.api.models.AuthorSummary
import sidebyside.api.models.MediaType
import sidebyside.api.models.MemoryAttachmentSet
import sidebyside.api.models.MemoryCreate
import sidebyside.api.models.MemoryDetail
import sidebyside.api.models.ReadDescriptor
import sidebyside.api.models.ResourceCapabilities
import sidebyside.api.models.SessionView
import sidebyside.api.models.StoryPage
import sidebyside.api.models.TokenView
import sidebyside.api.models.UploadDescriptor

@OptIn(ExperimentalCoroutinesApi::class)
class ReferenceViewModelAttachmentTest {
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
    fun multipleImagesUploadIndependentlyAndKeepSelectionOrder() = runTest(dispatcher) {
        val firstUpload = CompletableDeferred<Unit>()
        val secondUpload = CompletableDeferred<Unit>()
        val api = AttachmentContract { image ->
            when (image.displayName) {
                "first.jpg" -> firstUpload.await()
                "second.jpg" -> secondUpload.await()
            }
        }
        val viewModel = viewModel(api)
        signIn(viewModel)
        val selectionEpoch = checkNotNull(viewModel.beginImageSelection())

        viewModel.selectImages(
            listOf(
                SelectedImage(byteArrayOf(1, 2, 3), "first.jpg", "image/jpeg"),
                SelectedImage(byteArrayOf(4, 5, 6), "second.jpg", "image/jpeg"),
            ),
            selectionEpoch,
        )

        assertEquals(listOf("first.jpg", "second.jpg"), viewModel.uiState.value.draftImages.map { it.displayName })
        assertEquals(
            listOf(DraftUploadState.UPLOADING, DraftUploadState.UPLOADING),
            viewModel.uiState.value.draftImages.map { it.uploadState },
        )

        secondUpload.complete(Unit)
        advanceUntilIdle()
        assertEquals(
            listOf(DraftUploadState.UPLOADING, DraftUploadState.READY),
            viewModel.uiState.value.draftImages.map { it.uploadState },
        )

        firstUpload.complete(Unit)
        advanceUntilIdle()
        assertEquals(
            listOf(DraftUploadState.READY, DraftUploadState.READY),
            viewModel.uiState.value.draftImages.map { it.uploadState },
        )
        assertEquals(listOf("first.jpg", "second.jpg"), viewModel.uiState.value.draftImages.map { it.displayName })
    }

    @Test
    fun removingOneImageIgnoresItsLateCompletionWithoutAffectingSibling() = runTest(dispatcher) {
        val firstUpload = CompletableDeferred<Unit>()
        val api = AttachmentContract { image ->
            if (image.displayName == "first.jpg") firstUpload.await()
        }
        val viewModel = viewModel(api)
        signIn(viewModel)
        val selectionEpoch = checkNotNull(viewModel.beginImageSelection())

        viewModel.selectImages(
            listOf(
                SelectedImage(byteArrayOf(1), "first.jpg", "image/jpeg"),
                SelectedImage(byteArrayOf(2), "second.jpg", "image/jpeg"),
            ),
            selectionEpoch,
        )
        advanceUntilIdle()
        val removedId = viewModel.uiState.value.draftImages.first().id
        assertEquals(DraftUploadState.READY, viewModel.uiState.value.draftImages[1].uploadState)

        viewModel.removeImage(removedId)
        firstUpload.complete(Unit)
        advanceUntilIdle()

        assertEquals(listOf("second.jpg"), viewModel.uiState.value.draftImages.map { it.displayName })
        assertEquals(DraftUploadState.READY, viewModel.uiState.value.draftImages.single().uploadState)
    }

    @Test
    fun failedImageCanRetryWithoutResettingReadySibling() = runTest(dispatcher) {
        var retryAttempts = 0
        val api = AttachmentContract { image ->
            if (image.displayName == "retry.jpg") {
                retryAttempts += 1
                if (retryAttempts == 1) error("first upload failed")
            }
        }
        val viewModel = viewModel(api)
        signIn(viewModel)
        val selectionEpoch = checkNotNull(viewModel.beginImageSelection())

        viewModel.selectImages(
            listOf(
                SelectedImage(byteArrayOf(4, 5, 6), "retry.jpg", "image/jpeg"),
                SelectedImage(byteArrayOf(7, 8, 9), "stable.jpg", "image/jpeg"),
            ),
            selectionEpoch,
        )
        advanceUntilIdle()

        assertEquals(
            listOf(DraftUploadState.FAILED, DraftUploadState.READY),
            viewModel.uiState.value.draftImages.map { it.uploadState },
        )
        val retryId = viewModel.uiState.value.draftImages.first().id

        viewModel.retryImage(retryId)
        advanceUntilIdle()

        assertEquals(2, retryAttempts)
        assertEquals(
            listOf(DraftUploadState.READY, DraftUploadState.READY),
            viewModel.uiState.value.draftImages.map { it.uploadState },
        )
        assertEquals(listOf("retry.jpg", "stable.jpg"), viewModel.uiState.value.draftImages.map { it.displayName })
    }

    @Test
    fun saveBindsReadyImagesInStableDraftOrder() = runTest(dispatcher) {
        val api = AttachmentContract { }
        val viewModel = viewModel(api)
        signIn(viewModel)
        val selectionEpoch = checkNotNull(viewModel.beginImageSelection())

        viewModel.selectImages(
            listOf(
                SelectedImage(byteArrayOf(1), "first.jpg", "image/jpeg"),
                SelectedImage(byteArrayOf(2), "second.jpg", "image/jpeg"),
            ),
            selectionEpoch,
        )
        advanceUntilIdle()
        viewModel.createMemory("Two photos", "", "")
        advanceUntilIdle()

        assertNotNull(api.boundAttachments)
        val bound = checkNotNull(api.boundAttachments)
        assertEquals(listOf(0, 1), bound.attachments.map { it.position })
        assertEquals(api.createdAttachmentIds, bound.attachments.map { it.attachmentId })
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
        private val upload: suspend (SelectedImage) -> Unit,
    ) : ReferenceContract {
        override suspend fun consumeMagicLink(token: String): SessionView =
            error("Magic-link entry is not exercised by this test.")

        override suspend fun listMemberships(accessToken: String): List<AccountMembershipView> =
            error("Memberships are not exercised by this test.")

        override suspend fun createDemoEntry(baseUrl: String, persona: DemoPersona): String =
            error("Demo entry is not exercised by this test.")

        private var nextAttachmentValue = 30L
        val createdAttachmentIds = mutableListOf<UUID>()
        var boundAttachments: MemoryAttachmentSet? = null

        override suspend fun signIn(email: String, password: String): SessionView = session()

        override suspend fun createMemory(
            spaceId: UUID,
            accessToken: String,
            memory: MemoryCreate,
        ): MemoryDetail = memory()

        override suspend fun createAttachmentUpload(
            spaceId: UUID,
            accessToken: String,
            request: AttachmentUploadCreate,
        ): UploadDescriptor {
            val id = UUID(0L, nextAttachmentValue++)
            createdAttachmentIds += id
            return UploadDescriptor(
                attachment = attachment(id, "UPLOADING"),
                method = UploadDescriptor.Method.STREAM,
                requiredHeaders = mapOf("Content-Type" to request.expectedMimeType),
                uploadUrl = "/content",
            )
        }

        override suspend fun uploadAttachmentBytes(
            accessToken: String,
            descriptor: UploadDescriptor,
            image: SelectedImage,
        ) = upload(image)

        override suspend fun finalizeAttachment(
            spaceId: UUID,
            accessToken: String,
            attachmentId: UUID,
        ): AttachmentDetail = attachment(attachmentId, "VALIDATING")

        override suspend fun getAttachment(
            spaceId: UUID,
            accessToken: String,
            attachmentId: UUID,
        ): AttachmentDetail = attachment(attachmentId, "READY")

        override suspend fun replaceMemoryAttachments(
            spaceId: UUID,
            accessToken: String,
            memoryId: UUID,
            ifMatch: Int,
            attachments: MemoryAttachmentSet,
        ): MemoryDetail {
            boundAttachments = attachments
            return memory(version = 2)
        }

        override suspend fun getTimeline(spaceId: UUID, accessToken: String): StoryPage =
            StoryPage(hasMore = false, items = emptyList(), nextCursor = null)

        override suspend fun createReadAccess(
            spaceId: UUID,
            accessToken: String,
            attachmentId: UUID,
            request: AttachmentReadRequest,
        ): ReadDescriptor = ReadDescriptor(ReadDescriptor.Method.SIGNED_URL, "https://storage.invalid/read")

        override suspend fun readImageBytes(accessToken: String, descriptor: ReadDescriptor): ByteArray =
            byteArrayOf(1, 2, 3)
    }

    private fun attachment(id: UUID, status: String) = AttachmentDetail(
        createdAt = OffsetDateTime.parse("2026-08-29T20:00:00Z"),
        durationSeconds = null,
        hasThumbnail = false,
        height = null,
        id = id,
        mediaType = MediaType.IMAGE,
        mimeType = "image/jpeg",
        propertySize = 3,
        status = status,
        version = 1,
        width = null,
    )

    private fun memory(version: Int = 1) = MemoryDetail(
        attachments = emptyList(),
        author = AuthorSummary(
            displayName = "Test Person",
            id = UUID.fromString("00000000-0000-0000-0000-000000000020"),
        ),
        authorId = UUID.fromString("00000000-0000-0000-0000-000000000020"),
        body = "",
        capabilities = ResourceCapabilities(canComment = true, canDelete = true, canEdit = true),
        createdAt = OffsetDateTime.parse("2026-08-29T20:00:00Z"),
        happenedOn = null,
        id = UUID.fromString("00000000-0000-0000-0000-000000000040"),
        spaceId = spaceId,
        title = "Two photos",
        updatedAt = OffsetDateTime.parse("2026-08-29T20:00:00Z"),
        version = version,
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
