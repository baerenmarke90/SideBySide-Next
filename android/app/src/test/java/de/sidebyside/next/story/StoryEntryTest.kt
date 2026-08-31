package de.sidebyside.next.story

import java.time.LocalDate
import java.time.OffsetDateTime
import java.util.UUID
import org.junit.Assert.assertEquals
import org.junit.Assert.assertTrue
import org.junit.Test
import sidebyside.api.models.AttachmentReadRequest
import sidebyside.api.models.AttachmentSummary
import sidebyside.api.models.AuthorSummary
import sidebyside.api.models.HeartEmotion
import sidebyside.api.models.MediaType
import sidebyside.api.models.MemoryAttachmentSummary
import sidebyside.api.models.MemorySummary
import sidebyside.api.models.MilestoneSummary
import sidebyside.api.models.ResourceCapabilities
import sidebyside.api.models.SharedHeartMomentSummary
import sidebyside.api.models.StoryHeartMomentItem
import sidebyside.api.models.StoryItem
import sidebyside.api.models.StoryMemoryItem
import sidebyside.api.models.StoryMilestoneItem

/**
 * The Story mixes three contract types into one stream. These tests pin what a
 * couple ends up seeing, including the cases where showing the wrong thing
 * would be worse than showing nothing.
 */
class StoryEntryTest {
    @Test
    fun readsAllThreeKindsIntoOneStream() {
        val entries = listOf(memoryItem(), milestoneItem(), heartMomentItem()).map { it.toEntry() }

        assertEquals(
            listOf(
                StoryEntryKind.MEMORY,
                StoryEntryKind.MILESTONE,
                StoryEntryKind.HEART_MOMENT,
            ),
            entries.map { it.kind },
        )
        assertEquals(
            listOf("A day by the sea", "Moved in together", "Thank you for today"),
            entries.map { it.text },
        )
    }

    @Test
    fun groupsConsecutiveEntriesUnderTheirDay() {
        val first = LocalDate.of(2026, 8, 20)
        val second = LocalDate.of(2026, 8, 18)

        val days = listOf(
            memoryItem(date = first),
            heartMomentItem(date = first),
            memoryItem(date = second),
        ).toStoryDays()

        assertEquals(listOf(first, second), days.map { it.date })
        assertEquals(listOf(2, 1), days.map { it.entries.size })
    }

    @Test
    fun doesNotReorderWhatTheServerOrdered() {
        // The server owns the Story's order and hands out cursors against it.
        // Sorting here would fight the next page, and a date that recurs later
        // in the stream is the server's business, not a defect to repair.
        val early = LocalDate.of(2026, 1, 1)
        val late = LocalDate.of(2026, 9, 9)

        val days = listOf(
            memoryItem(date = late),
            memoryItem(date = early),
            memoryItem(date = late),
        ).toStoryDays()

        assertEquals(listOf(late, early, late), days.map { it.date })
    }

    @Test
    fun showsOnlyAttachmentsThatAreReadyImages() {
        // A pending upload has no bytes to read, and a video is out of scope
        // while the server rejects it. Either would render as a broken tile.
        val item = memoryItem(
            attachments = listOf(
                attachment(position = 0, status = "READY"),
                attachment(position = 1, status = "VALIDATING"),
                attachment(position = 2, status = "READY", mediaType = MediaType.VIDEO),
            ),
        )

        assertEquals(1, item.toEntry().images.size)
    }

    @Test
    fun ordersImagesTheWayTheMemoryDoes() {
        val third = attachment(position = 2, status = "READY")
        val first = attachment(position = 0, status = "READY")
        val second = attachment(position = 1, status = "READY")
        val item = memoryItem(attachments = listOf(third, first, second))

        assertEquals(
            listOf(first.id, second.id, third.id),
            item.toEntry().images.map { it.attachmentId },
        )
    }

    @Test
    fun carriesTheParentEachAuthorizedReadNeeds() {
        // A read is granted against the parent, not the attachment alone, so
        // the wrong parent means a refused read rather than a wrong image.
        val memory = memoryItem(attachments = listOf(attachment(0, "READY"))).toEntry()
        assertEquals(AttachmentReadRequest.ParentType.MEMORY, memory.images.single().parentType)
        assertEquals(memory.id, memory.images.single().parentId)

        val heart = heartMomentItem(withImage = true).toEntry()
        assertEquals(AttachmentReadRequest.ParentType.HEART_MOMENT, heart.images.single().parentType)
        assertEquals(heart.id, heart.images.single().parentId)
    }

    @Test
    fun anEmptyStoryHasNoDays() {
        assertTrue(emptyList<StoryItem>().toStoryDays().isEmpty())
    }
}

private val CAPABILITIES = ResourceCapabilities(canComment = true, canDelete = true, canEdit = true)
private val AUTHOR = AuthorSummary(displayName = "Lea", id = UUID.randomUUID())
private val CREATED: OffsetDateTime = OffsetDateTime.now()
private val DEFAULT_DATE: LocalDate = LocalDate.of(2026, 8, 20)

private fun attachment(
    position: Int,
    status: String,
    mediaType: MediaType = MediaType.IMAGE,
) = MemoryAttachmentSummary(
    hasThumbnail = true,
    height = 1200,
    id = UUID.randomUUID(),
    mediaType = mediaType,
    mimeType = "image/jpeg",
    position = position,
    propertySize = 1024,
    status = status,
    width = 1600,
)

private fun memoryItem(
    date: LocalDate = DEFAULT_DATE,
    attachments: List<MemoryAttachmentSummary> = emptyList(),
) = StoryItem.MemoryWrapper(
    StoryMemoryItem(
        effectiveDate = date,
        kind = StoryMemoryItem.Kind.MEMORY,
        memory = MemorySummary(
            attachments = attachments,
            author = AUTHOR,
            capabilities = CAPABILITIES,
            createdAt = CREATED,
            happenedOn = date,
            id = UUID.randomUUID(),
            title = "A day by the sea",
        ),
    ),
)

private fun milestoneItem(date: LocalDate = DEFAULT_DATE) = StoryItem.MilestoneWrapper(
    StoryMilestoneItem(
        effectiveDate = date,
        kind = StoryMilestoneItem.Kind.MILESTONE,
        milestone = MilestoneSummary(
            author = AUTHOR,
            capabilities = CAPABILITIES,
            createdAt = CREATED,
            happenedOn = date,
            id = UUID.randomUUID(),
            title = "Moved in together",
        ),
    ),
)

private fun heartMomentItem(
    date: LocalDate = DEFAULT_DATE,
    withImage: Boolean = false,
) = StoryItem.HeartMomentWrapper(
    StoryHeartMomentItem(
        effectiveDate = date,
        heartMoment = SharedHeartMomentSummary(
            attachment = if (withImage) {
                AttachmentSummary(
                    hasThumbnail = true,
                    height = 800,
                    id = UUID.randomUUID(),
                    mediaType = MediaType.IMAGE,
                    mimeType = "image/jpeg",
                    propertySize = 512,
                    status = "READY",
                    width = 800,
                )
            } else {
                null
            },
            author = AUTHOR,
            capabilities = CAPABILITIES,
            createdAt = CREATED,
            emotion = HeartEmotion.LOVED,
            happenedOn = date,
            id = UUID.randomUUID(),
            text = "Thank you for today",
        ),
        kind = StoryHeartMomentItem.Kind.HEART_MOMENT,
    ),
)
