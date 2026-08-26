package de.sidebyside.next.reference

import java.util.UUID
import sidebyside.api.models.AttachmentDetail
import sidebyside.api.models.AttachmentReadRequest
import sidebyside.api.models.AttachmentUploadCreate
import sidebyside.api.models.MemoryAttachmentSet
import sidebyside.api.models.MemoryCreate
import sidebyside.api.models.MemoryDetail
import sidebyside.api.models.ReadDescriptor
import sidebyside.api.models.SessionView
import sidebyside.api.models.StoryPage
import sidebyside.api.models.UploadDescriptor

data class SelectedImage(
    val bytes: ByteArray,
    val displayName: String,
    val mimeType: String,
)

data class ReferenceFlowResult(
    val memory: MemoryDetail,
    val story: StoryPage,
    val imageBytes: ByteArray,
)

interface ReferenceContract {
    suspend fun signIn(email: String, password: String): SessionView

    suspend fun createMemory(spaceId: UUID, accessToken: String, memory: MemoryCreate): MemoryDetail

    suspend fun createAttachmentUpload(
        spaceId: UUID,
        accessToken: String,
        request: AttachmentUploadCreate,
    ): UploadDescriptor

    suspend fun uploadAttachmentBytes(accessToken: String, descriptor: UploadDescriptor, image: SelectedImage)

    suspend fun finalizeAttachment(spaceId: UUID, accessToken: String, attachmentId: UUID): AttachmentDetail

    suspend fun getAttachment(spaceId: UUID, accessToken: String, attachmentId: UUID): AttachmentDetail

    suspend fun replaceMemoryAttachments(
        spaceId: UUID,
        accessToken: String,
        memoryId: UUID,
        ifMatch: Int,
        attachments: MemoryAttachmentSet,
    ): MemoryDetail

    suspend fun getTimeline(spaceId: UUID, accessToken: String): StoryPage

    suspend fun createReadAccess(
        spaceId: UUID,
        accessToken: String,
        attachmentId: UUID,
        request: AttachmentReadRequest,
    ): ReadDescriptor

    suspend fun readImageBytes(accessToken: String, descriptor: ReadDescriptor): ByteArray
}
