package de.sidebyside.next.reference

import java.util.UUID
import de.sidebyside.next.demo.DemoPersona
import sidebyside.api.models.AccountMembershipView
import sidebyside.api.models.AttachmentDetail
import sidebyside.api.models.AttachmentReadRequest
import sidebyside.api.models.AttachmentUploadCreate
import sidebyside.api.models.MemoryAttachmentSet
import sidebyside.api.models.MemoryCreate
import sidebyside.api.models.MemoryDetail
import sidebyside.api.models.MemoryUpdate
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
    val imageBytes: ByteArray?,
)

interface ReferenceContract {
    suspend fun signIn(email: String, password: String): SessionView

    /**
     * Exchanges a one-time entry proof for a session.
     *
     * The demo entry issues such a proof, so the demo never needs a password
     * that could be embedded in the app.
     */
    suspend fun consumeMagicLink(token: String): SessionView

    /**
     * The Spaces this account may open, as the server sees them.
     *
     * The active Space is derived from this rather than configured, because a
     * demo persona's Space is not known at build time.
     */
    suspend fun listMemberships(accessToken: String): List<AccountMembershipView>

    /**
     * Requests a one-time entry proof for a canonical demo persona.
     *
     * `POST /api/v1/demo/entry` is deliberately absent from the OpenAPI
     * contract: it is a facility of the isolated demo deployment, not a
     * supported authentication method for a normal installation. It is
     * therefore declared here by hand instead of through the generated client,
     * and it is the only call in this client that is.
     */
    suspend fun createDemoEntry(baseUrl: String, persona: DemoPersona): String

    suspend fun createMemory(spaceId: UUID, accessToken: String, memory: MemoryCreate): MemoryDetail

    suspend fun getMemory(spaceId: UUID, accessToken: String, memoryId: UUID): MemoryDetail

    /**
     * Changes a memory.
     *
     * [ifMatch] is the version the change was written against. The server
     * answers 409 when the partner changed the memory in the meantime, which is
     * the point: without it the later write would silently overwrite the
     * earlier one.
     */
    suspend fun updateMemory(
        spaceId: UUID,
        accessToken: String,
        memoryId: UUID,
        ifMatch: Int,
        update: MemoryUpdate,
    ): MemoryDetail

    suspend fun deleteMemory(spaceId: UUID, accessToken: String, memoryId: UUID, ifMatch: Int)

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
