package de.sidebyside.next.reference

import java.time.OffsetDateTime
import java.util.UUID
import kotlinx.coroutines.test.runTest
import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Test
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
import sidebyside.api.models.UploadDescriptor

class AttachmentPreparationTest {
    private val spaceId = UUID.fromString("00000000-0000-0000-0000-000000000010")
    private val memoryId = UUID.fromString("00000000-0000-0000-0000-000000000020")
    private val firstAttachmentId = UUID.fromString("00000000-0000-0000-0000-000000000031")
    private val secondAttachmentId = UUID.fromString("00000000-0000-0000-0000-000000000032")
    private val authorId = UUID.fromString("00000000-0000-0000-0000-000000000040")

    @Test
    fun preparesAttachmentBeforeAnyMemoryIsCreated() = runTest {
        val phases = mutableListOf<AttachmentPreparationPhase>()
        var memoryCreated = false
        val api = RecordingContract(
            onCreateMemory = { memoryCreated = true },
            uploadAttachmentId = firstAttachmentId,
        )

        val prepared = prepareAttachment(
            api = api,
            spaceId = spaceId,
            accessToken = "token",
            image = SelectedImage(byteArrayOf(1, 2, 3), "draft.jpg", "image/jpeg"),
            onPhase = phases::add,
        )

        assertFalse(memoryCreated)
        assertEquals(firstAttachmentId, prepared.attachmentId)
        assertEquals(
            listOf(
                AttachmentPreparationPhase.UPLOADING,
                AttachmentPreparationPhase.VALIDATING,
                AttachmentPreparationPhase.READY,
            ),
            phases,
        )
    }

    @Test
    fun bindsPreparedAttachmentsInStableSelectionOrder() = runTest {
        val api = RecordingContract(uploadAttachmentId = firstAttachmentId)

        createMemoryWithPreparedAttachments(
            api = api,
            spaceId = spaceId,
            accessToken = "token",
            title = "Two photos",
            body = "",
            happenedOn = null,
            attachments = listOf(
                PreparedAttachment(firstAttachmentId),
                PreparedAttachment(secondAttachmentId),
            ),
        )

        assertEquals(
            listOf(firstAttachmentId, secondAttachmentId),
            api.boundAttachments!!.attachments.map { it.attachmentId },
        )
        assertEquals(listOf(0, 1), api.boundAttachments!!.attachments.map { it.position })
    }

    private inner class RecordingContract(
        private val onCreateMemory: () -> Unit = {},
        private val uploadAttachmentId: UUID,
    ) : ReferenceContract {
        var boundAttachments: MemoryAttachmentSet? = null

        override suspend fun signIn(email: String, password: String): SessionView = error("not used")

        override suspend fun createMemory(
            spaceId: UUID,
            accessToken: String,
            memory: MemoryCreate,
        ): MemoryDetail {
            onCreateMemory()
            return this@AttachmentPreparationTest.memory()
        }

        override suspend fun createAttachmentUpload(
            spaceId: UUID,
            accessToken: String,
            request: AttachmentUploadCreate,
        ): UploadDescriptor = UploadDescriptor(
            attachment = attachment(uploadAttachmentId, "UPLOADING"),
            method = UploadDescriptor.Method.STREAM,
            requiredHeaders = mapOf("Content-Type" to request.expectedMimeType),
            uploadUrl = "/content",
        )

        override suspend fun uploadAttachmentBytes(
            accessToken: String,
            descriptor: UploadDescriptor,
            image: SelectedImage,
        ) = Unit

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
        author = AuthorSummary(displayName = "A", id = authorId),
        authorId = authorId,
        body = "",
        capabilities = ResourceCapabilities(canComment = true, canDelete = true, canEdit = true),
        createdAt = OffsetDateTime.parse("2026-08-29T20:00:00Z"),
        happenedOn = null,
        id = memoryId,
        spaceId = spaceId,
        title = "Two photos",
        updatedAt = OffsetDateTime.parse("2026-08-29T20:00:00Z"),
        version = version,
    )
}
