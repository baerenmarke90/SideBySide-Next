package de.sidebyside.next.place

import de.sidebyside.next.reference.ReferenceContract
import java.time.LocalDate
import java.util.UUID
import sidebyside.api.models.StoryItem

/**
 * A Story item as something that can be linked to a Place — one shape for
 * all three kinds, since the picker and the linked list treat them
 * uniformly. The Story timeline is the sole source of both id and label:
 * the typed-relation endpoints return only linked ids, deliberately not
 * content, so this is also what keeps a private HeartMoment from ever
 * reaching the picker — it never appears in the timeline to begin with.
 */
data class RelationTargetItem(
    val id: UUID,
    val kind: ReferenceContract.RelationTargetKind,
    val label: String,
    val date: LocalDate,
)

fun StoryItem.toRelationTargetItem(): RelationTargetItem = when (this) {
    is StoryItem.MemoryWrapper -> RelationTargetItem(
        id = value.memory.id,
        kind = ReferenceContract.RelationTargetKind.MEMORY,
        label = value.memory.title,
        date = value.effectiveDate,
    )
    is StoryItem.MilestoneWrapper -> RelationTargetItem(
        id = value.milestone.id,
        kind = ReferenceContract.RelationTargetKind.MILESTONE,
        label = value.milestone.title,
        date = value.effectiveDate,
    )
    is StoryItem.HeartMomentWrapper -> RelationTargetItem(
        id = value.heartMoment.id,
        kind = ReferenceContract.RelationTargetKind.HEART_MOMENT,
        label = value.heartMoment.text,
        date = value.effectiveDate,
    )
}
