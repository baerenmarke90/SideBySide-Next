package de.sidebyside.next.reference

import de.sidebyside.next.demo.DemoPersona
import java.util.UUID
import sidebyside.api.models.AccountMembershipView
import sidebyside.api.models.AttachmentDetail
import sidebyside.api.models.AttachmentReadRequest
import sidebyside.api.models.AttachmentUploadCreate
import sidebyside.api.models.ContentVisibility
import sidebyside.api.models.HeartMomentCreate
import sidebyside.api.models.HeartMomentDetail
import sidebyside.api.models.HeartMomentPage
import sidebyside.api.models.HeartMomentUpdate
import sidebyside.api.models.HeartMomentVisibilityChange
import sidebyside.api.models.MemoryAttachmentSet
import sidebyside.api.models.MemoryCreate
import sidebyside.api.models.MemoryDetail
import sidebyside.api.models.MemoryUpdate
import sidebyside.api.models.PartnerProfileView
import sidebyside.api.models.ProfileIdentityUpdate
import sidebyside.api.models.ReadDescriptor
import sidebyside.api.models.SessionView
import sidebyside.api.models.SpaceView
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

    /**
     * The HeartMoments this account may read.
     *
     * The server narrows this to what the caller is authorised for, and the
     * [visibility] filter narrows it further — it never widens it. Asking for
     * `PRIVATE` therefore returns the caller's own private moments, and an
     * empty page for anyone else's, rather than a refusal that would confirm
     * that someone else's exist.
     */
    suspend fun listHeartMoments(
        spaceId: UUID,
        accessToken: String,
        visibility: ContentVisibility? = null,
    ): HeartMomentPage

    suspend fun createHeartMoment(
        spaceId: UUID,
        accessToken: String,
        heartMoment: HeartMomentCreate,
    ): HeartMomentDetail

    suspend fun updateHeartMoment(
        spaceId: UUID,
        accessToken: String,
        heartMomentId: UUID,
        ifMatch: Int,
        update: HeartMomentUpdate,
    ): HeartMomentDetail

    /**
     * Changes who may see a HeartMoment.
     *
     * Its own call, not a field on [updateHeartMoment], because the server
     * makes it one: `SHARED -> PRIVATE` deletes the moment's comments in the
     * same transaction, and going back does not restore them. That must never
     * happen as a side effect of editing text.
     */
    suspend fun changeHeartMomentVisibility(
        spaceId: UUID,
        accessToken: String,
        heartMomentId: UUID,
        ifMatch: Int,
        change: HeartMomentVisibilityChange,
    ): HeartMomentDetail

    suspend fun deleteHeartMoment(
        spaceId: UUID,
        accessToken: String,
        heartMomentId: UUID,
        ifMatch: Int,
    )

    suspend fun createAttachmentUpload(
        spaceId: UUID,
        accessToken: String,
        request: AttachmentUploadCreate,
    ): UploadDescriptor

    suspend fun uploadAttachmentBytes(accessToken: String, descriptor: UploadDescriptor, image: SelectedImage)

    suspend fun finalizeAttachment(spaceId: UUID, accessToken: String, attachmentId: UUID): AttachmentDetail

    suspend fun getAttachment(spaceId: UUID, accessToken: String, attachmentId: UUID): AttachmentDetail

    suspend fun deleteAttachment(
        spaceId: UUID,
        accessToken: String,
        attachmentId: UUID,
        ifMatch: Int,
    ) {
        unsupportedProfileOperation()
    }

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

    /** Profile APIs are optional for older test fakes and loaded lazily by the UI. */
    suspend fun getSpace(spaceId: UUID, accessToken: String): SpaceView = unsupportedProfileOperation()

    suspend fun getProfile(
        spaceId: UUID,
        accessToken: String,
        accountId: UUID,
    ): PartnerProfileView = unsupportedProfileOperation()

    suspend fun updateProfileIdentity(
        spaceId: UUID,
        accessToken: String,
        accountId: UUID,
        ifMatch: Int,
        update: ProfileIdentityUpdate,
    ): PartnerProfileView = unsupportedProfileOperation()

    /**
     * Explicit avatar removal is separate because the generated nullable DTO is
     * encoded with `explicitNulls = false`; the wire contract still requires a
     * literal JSON null to distinguish removal from omission.
     */
    suspend fun removeProfileAvatar(
        spaceId: UUID,
        accessToken: String,
        accountId: UUID,
        ifMatch: Int,
    ): PartnerProfileView = unsupportedProfileOperation()

    suspend fun readProfileAvatar(
        spaceId: UUID,
        accessToken: String,
        accountId: UUID,
    ): ByteArray = unsupportedProfileOperation()
}

private fun unsupportedProfileOperation(): Nothing =
    throw UnsupportedOperationException("This ReferenceContract fake does not implement profile identity.")
