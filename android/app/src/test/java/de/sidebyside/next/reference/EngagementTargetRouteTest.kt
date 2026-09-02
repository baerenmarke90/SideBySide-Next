package de.sidebyside.next.reference

import java.util.UUID
import org.junit.Assert.assertEquals
import org.junit.Assert.assertNull
import org.junit.Test
import sidebyside.api.models.EngagementTarget

/**
 * The M2-D18 cross-client Deep Link contract's "small logical target
 * tuple... maps to the current client's canonical route," pinned on its own
 * since [NotificationsScreen][de.sidebyside.next.notifications.NotificationsScreen]
 * and [ActivityScreen][de.sidebyside.next.activity.ActivityScreen] both
 * decide "does this row open anything?" from this same function — a
 * mistake here would silently make a row look tappable with nowhere to go,
 * or the reverse.
 */
class EngagementTargetRouteTest {
    private val id: UUID = UUID.fromString("00000000-0000-0000-0000-0000000000a1")

    @Test
    fun resolvesEveryKindWithADetailRouteOnAndroid() {
        assertEquals("story/memories/$id", engagementTargetRoute(EngagementTarget.MEMORY, id))
        assertEquals("story/milestones/$id", engagementTargetRoute(EngagementTarget.MILESTONE, id))
        assertEquals("story/heart-moments/$id", engagementTargetRoute(EngagementTarget.HEART_MOMENT, id))
        assertEquals("planning/places/$id/relations", engagementTargetRoute(EngagementTarget.PLACE, id))
        assertEquals("planning/chapters/$id/content", engagementTargetRoute(EngagementTarget.CHAPTER, id))
        assertEquals("planning/collections/$id", engagementTargetRoute(EngagementTarget.COLLECTION, id))
    }

    @Test
    fun wishAndPlanHaveNoPerResourceRouteYet() {
        // Both live in one shared list screen (AppDestination.Plan), not a
        // route of their own to navigate a single entry to.
        assertNull(engagementTargetRoute(EngagementTarget.WISH, id))
        assertNull(engagementTargetRoute(EngagementTarget.PLAN, id))
    }

    @Test
    fun aMissingIdNeverResolvesEvenForAKnownKind() {
        assertNull(engagementTargetRoute(EngagementTarget.MEMORY, null))
    }

    @Test
    fun aMissingKindNeverResolves() {
        assertNull(engagementTargetRoute(null, id))
    }
}
