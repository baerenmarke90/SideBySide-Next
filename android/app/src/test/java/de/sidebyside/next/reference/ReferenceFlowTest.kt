package de.sidebyside.next.reference

import de.sidebyside.next.demo.DemoPersona
import sidebyside.api.models.AccountMembershipView
import java.time.OffsetDateTime
import java.util.UUID
import kotlinx.coroutines.test.runTest
import org.junit.Assert.assertEquals
import org.junit.Assert.assertNull
import org.junit.Assert.assertSame
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

class ReferenceFlowTest {
    private val spaceId = UUID.fromString("00000000-0000-0000-0000-000000000010")
    private val memoryId = UUID.fromString("00000000-0000-0000-0000-000000000020")
    private val attachmentId = UUID.fromString("00000000-0000-0000-0000-000000000030")
    private val authorId = UUID.fromString("00000000-0000-0000-0000-000000000040")

    @Test
    fun createsTitleOnlyMemoryWithoutAttachmentCalls() = runTest {
        var createdRequest: MemoryCreate? = null
        val createdMemory = memory(version = 1, body = "")
        val story = StoryPage(hasMore = false, items = emptyList(), nextCursor = null)

        val api = object : FakeReferenceContract() {




            override suspend fun createMemory(spaceId: UUID, accessToken: String, memory: MemoryCreate): MemoryDetail {
                createdRequest = memory
                return createdMemory
            }






            override suspend fun getTimeline(spaceId: UUID, accessToken: String): StoryPage = story


        }

        val result = runMemoryMediaStoryFlow(
            api = api,
            spaceId = spaceId,
            accessToken = "token",
            title = "Title only",
            body = "",
            happenedOn = null,
            image = null,
        )

        assertEquals("Title only", createdRequest!!.title)
        assertEquals("", createdRequest!!.body)
        assertSame(createdMemory, result.memory)
        assertSame(story, result.story)
        assertNull(result.imageBytes)
    }

    @Test
    fun orchestratesMemoryImageTimelineAndAuthorizedReadInOrder() = runTest {
        val calls = mutableListOf<String>()
        val attachment = attachment(status = "UPLOADING")
        val memory = memory(version = 1)
        val boundMemory = memory(version = 2)
        val story = StoryPage(hasMore = false, items = emptyList(), nextCursor = null)

        val api = object : FakeReferenceContract() {



            var boundSet: MemoryAttachmentSet? = null
            var boundIfMatch: Int? = null
            var readRequest: AttachmentReadRequest? = null


            override suspend fun createMemory(spaceId: UUID, accessToken: String, memory: MemoryCreate): MemoryDetail {
                calls += "create-memory"
                return this@ReferenceFlowTest.memory(version = 1)
            }

            override suspend fun createAttachmentUpload(
                spaceId: UUID,
                accessToken: String,
                request: AttachmentUploadCreate,
            ): UploadDescriptor {
                calls += "create-upload"
                assertEquals(MediaType.IMAGE, request.mediaType)
                return UploadDescriptor(
                    attachment = attachment,
                    method = UploadDescriptor.Method.STREAM,
                    requiredHeaders = mapOf("Content-Type" to "image/jpeg"),
                    uploadUrl = "/api/v1/spaces/$spaceId/attachments/$attachmentId/content",
                )
            }

            override suspend fun uploadAttachmentBytes(
                accessToken: String,
                descriptor: UploadDescriptor,
                image: SelectedImage,
            ) {
                calls += "upload-bytes"
            }

            override suspend fun finalizeAttachment(
                spaceId: UUID,
                accessToken: String,
                attachmentId: UUID,
            ): AttachmentDetail {
                calls += "finalize-upload"
                return attachment(status = "VALIDATING")
            }

            override suspend fun getAttachment(
                spaceId: UUID,
                accessToken: String,
                attachmentId: UUID,
            ): AttachmentDetail {
                calls += "wait-ready"
                return attachment(status = "READY")
            }

            override suspend fun replaceMemoryAttachments(
                spaceId: UUID,
                accessToken: String,
                memoryId: UUID,
                ifMatch: Int,
                attachments: MemoryAttachmentSet,
            ): MemoryDetail {
                calls += "bind-memory"
                boundIfMatch = ifMatch
                boundSet = attachments
                return boundMemory
            }

            override suspend fun getTimeline(spaceId: UUID, accessToken: String): StoryPage {
                calls += "timeline"
                return story
            }

            override suspend fun createReadAccess(
                spaceId: UUID,
                accessToken: String,
                attachmentId: UUID,
                request: AttachmentReadRequest,
            ): ReadDescriptor {
                calls += "authorize-read"
                readRequest = request
                return ReadDescriptor(ReadDescriptor.Method.SIGNED_URL, "https://storage.invalid/read")
            }

            override suspend fun readImageBytes(accessToken: String, descriptor: ReadDescriptor): ByteArray {
                calls += "read-bytes"
                return byteArrayOf(1, 2, 3)
            }
        }

        val result = runMemoryMediaStoryFlow(
            api = api,
            spaceId = spaceId,
            accessToken = "token",
            title = "Lakeside",
            body = "A day together.",
            happenedOn = null,
            image = SelectedImage(byteArrayOf(9, 8, 7), "lakeside.jpg", "image/jpeg"),
        )

        assertEquals(
            listOf(
                "create-memory",
                "create-upload",
                "upload-bytes",
                "finalize-upload",
                "wait-ready",
                "bind-memory",
                "timeline",
                "authorize-read",
                "read-bytes",
            ),
            calls,
        )
        assertEquals(1, api.boundIfMatch)
        assertEquals(attachmentId, api.boundSet!!.attachments.single().attachmentId)
        assertEquals(0, api.boundSet!!.attachments.single().position)
        assertEquals(AttachmentReadRequest.ParentType.MEMORY, api.readRequest!!.parentType)
        assertEquals(memoryId, api.readRequest!!.parentId)
        assertSame(boundMemory, result.memory)
        assertSame(story, result.story)
        assertEquals(listOf<Byte>(1, 2, 3), result.imageBytes!!.toList())
    }

    private fun attachment(status: String) = AttachmentDetail(
        createdAt = OffsetDateTime.parse("2026-08-26T08:00:00Z"),
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

    private fun memory(version: Int, body: String = "A day together.") = MemoryDetail(
        attachments = emptyList(),
        author = AuthorSummary(displayName = "A", id = authorId),
        authorId = authorId,
        body = body,
        capabilities = ResourceCapabilities(canComment = true, canDelete = true, canEdit = true),
        createdAt = OffsetDateTime.parse("2026-08-26T08:00:00Z"),
        happenedOn = null,
        id = memoryId,
        spaceId = spaceId,
        title = if (body.isEmpty()) "Title only" else "Lakeside",
        updatedAt = OffsetDateTime.parse("2026-08-26T08:00:00Z"),
        version = version,
    )
}
