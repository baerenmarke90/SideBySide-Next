package de.sidebyside.next.reference

import java.time.LocalDate
import java.util.UUID
import kotlinx.coroutines.delay
import sidebyside.api.models.AttachmentReadRequest
import sidebyside.api.models.AttachmentUploadCreate
import sidebyside.api.models.MediaType
import sidebyside.api.models.MemoryAttachmentEntry
import sidebyside.api.models.MemoryAttachmentSet
import sidebyside.api.models.MemoryCreate

suspend fun runMemoryMediaStoryFlow(
    api: ReferenceContract,
    spaceId: UUID,
    accessToken: String,
    title: String,
    body: String,
    happenedOn: LocalDate?,
    image: SelectedImage,
): ReferenceFlowResult {
    require(image.mimeType.startsWith("image/")) { "S8 accepts images only." }
    require(image.bytes.isNotEmpty()) { "The selected image is empty." }

    val memory = api.createMemory(
        spaceId,
        accessToken,
        MemoryCreate(body = body, title = title, happenedOn = happenedOn),
    )

    val upload = api.createAttachmentUpload(
        spaceId,
        accessToken,
        AttachmentUploadCreate(
            expectedMimeType = image.mimeType,
            expectedSize = image.bytes.size,
            mediaType = MediaType.IMAGE,
            originalName = image.displayName,
        ),
    )

    api.uploadAttachmentBytes(accessToken, upload, image)
    api.finalizeAttachment(spaceId, accessToken, upload.attachment.id)
    waitUntilReady(api, spaceId, accessToken, upload.attachment.id)

    val boundMemory = api.replaceMemoryAttachments(
        spaceId = spaceId,
        accessToken = accessToken,
        memoryId = memory.id,
        ifMatch = memory.version,
        attachments = MemoryAttachmentSet(
            attachments = listOf(MemoryAttachmentEntry(upload.attachment.id, position = 0)),
        ),
    )

    val story = api.getTimeline(spaceId, accessToken)
    val readDescriptor = api.createReadAccess(
        spaceId,
        accessToken,
        upload.attachment.id,
        AttachmentReadRequest(
            parentId = boundMemory.id,
            parentType = AttachmentReadRequest.ParentType.MEMORY,
        ),
    )
    val imageBytes = api.readImageBytes(accessToken, readDescriptor)

    return ReferenceFlowResult(
        memory = boundMemory,
        story = story,
        imageBytes = imageBytes,
    )
}

private suspend fun waitUntilReady(
    api: ReferenceContract,
    spaceId: UUID,
    accessToken: String,
    attachmentId: UUID,
) {
    val deadlineNanos = System.nanoTime() + 30_000_000_000L
    while (System.nanoTime() < deadlineNanos) {
        val attachment = api.getAttachment(spaceId, accessToken, attachmentId)
        when (attachment.status) {
            "READY" -> return
            "FAILED", "DELETE_FAILED", "DELETING" -> {
                throw IllegalStateException("Media processing ended with status ${attachment.status}.")
            }
        }
        delay(500)
    }
    throw IllegalStateException("Media processing did not reach READY before the deadline.")
}
