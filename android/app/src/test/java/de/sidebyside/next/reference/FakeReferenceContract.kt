package de.sidebyside.next.reference

import de.sidebyside.next.demo.DemoPersona
import java.util.UUID
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

/**
 * A [ReferenceContract] whose every call fails until a test says otherwise.
 *
 * Each test double used to restate the whole contract, so most of them carried
 * a dozen `error("not used")` bodies and every new endpoint broke all of them
 * at once. Overriding only what a test exercises also makes the double say what
 * the test is actually about.
 *
 * The failure names the method, so a call a test did not expect is reported as
 * itself rather than as a null or a silent default.
 */
abstract class FakeReferenceContract : ReferenceContract {
    override suspend fun signIn(email: String, password: String): SessionView =
        notExercised("signIn")

    override suspend fun consumeMagicLink(token: String): SessionView =
        notExercised("consumeMagicLink")

    override suspend fun listMemberships(accessToken: String): List<AccountMembershipView> =
        notExercised("listMemberships")

    override suspend fun createDemoEntry(baseUrl: String, persona: DemoPersona): String =
        notExercised("createDemoEntry")

    override suspend fun createMemory(
        spaceId: UUID,
        accessToken: String,
        memory: MemoryCreate,
    ): MemoryDetail = notExercised("createMemory")

    override suspend fun getMemory(
        spaceId: UUID,
        accessToken: String,
        memoryId: UUID,
    ): MemoryDetail = notExercised("getMemory")

    override suspend fun updateMemory(
        spaceId: UUID,
        accessToken: String,
        memoryId: UUID,
        ifMatch: Int,
        update: MemoryUpdate,
    ): MemoryDetail = notExercised("updateMemory")

    override suspend fun deleteMemory(
        spaceId: UUID,
        accessToken: String,
        memoryId: UUID,
        ifMatch: Int,
    ): Unit = notExercised("deleteMemory")

    override suspend fun createAttachmentUpload(
        spaceId: UUID,
        accessToken: String,
        request: AttachmentUploadCreate,
    ): UploadDescriptor = notExercised("createAttachmentUpload")

    override suspend fun uploadAttachmentBytes(
        accessToken: String,
        descriptor: UploadDescriptor,
        image: SelectedImage,
    ): Unit = notExercised("uploadAttachmentBytes")

    override suspend fun finalizeAttachment(
        spaceId: UUID,
        accessToken: String,
        attachmentId: UUID,
    ): AttachmentDetail = notExercised("finalizeAttachment")

    override suspend fun getAttachment(
        spaceId: UUID,
        accessToken: String,
        attachmentId: UUID,
    ): AttachmentDetail = notExercised("getAttachment")

    override suspend fun replaceMemoryAttachments(
        spaceId: UUID,
        accessToken: String,
        memoryId: UUID,
        ifMatch: Int,
        attachments: MemoryAttachmentSet,
    ): MemoryDetail = notExercised("replaceMemoryAttachments")

    override suspend fun getTimeline(spaceId: UUID, accessToken: String): StoryPage =
        notExercised("getTimeline")

    override suspend fun createReadAccess(
        spaceId: UUID,
        accessToken: String,
        attachmentId: UUID,
        request: AttachmentReadRequest,
    ): ReadDescriptor = notExercised("createReadAccess")

    override suspend fun readImageBytes(
        accessToken: String,
        descriptor: ReadDescriptor,
    ): ByteArray = notExercised("readImageBytes")

    private fun notExercised(name: String): Nothing =
        error("$name is not exercised by this test.")
}
