package de.sidebyside.next.design

import org.junit.Assert.assertEquals
import org.junit.Assert.assertTrue
import org.junit.Test

class RelationshipComponentStateTest {

    @Test
    fun partnerPresenceStateHasAllDefinedVariants() {
        val states = PartnerPresenceState.entries
        assertTrue(states.contains(PartnerPresenceState.CONNECTED))
        assertTrue(states.contains(PartnerPresenceState.WAITING))
        assertTrue(states.contains(PartnerPresenceState.OFFLINE))
        assertEquals(3, states.size)
    }

    @Test
    fun thinkingOfYouStateHasExpectedTransitions() {
        val states = ThinkingOfYouState.entries
        assertTrue(states.contains(ThinkingOfYouState.IDLE))
        assertTrue(states.contains(ThinkingOfYouState.SENDING))
        assertTrue(states.contains(ThinkingOfYouState.SENT))
        assertEquals(3, states.size)
    }

    @Test
    fun visibilityBadgeTypeMatchesContract() {
        val types = VisibilityBadgeType.entries
        assertTrue(types.contains(VisibilityBadgeType.SHARED))
        assertTrue(types.contains(VisibilityBadgeType.PRIVATE))
        assertTrue(types.contains(VisibilityBadgeType.TEMPORARY))
        assertEquals(3, types.size)
    }
}
