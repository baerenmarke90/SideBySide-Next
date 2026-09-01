package de.sidebyside.next.release

import de.sidebyside.next.reference.BuildConfig
import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertTrue
import org.junit.Test

/**
 * The application ID, which Google Play binds to a listing permanently.
 *
 * It cannot be corrected after a first release, so the value is pinned here
 * rather than left to be noticed in a store console. See #194.
 */
class ReleaseIdentityTest {
    @Test
    fun keepsTheApplicationIdItWasReleasedUnder() {
        // The debug build adds its own suffix so it can sit beside an installed
        // release; everything before that suffix is the frozen identity.
        assertTrue(
            "Unexpected application ID: ${BuildConfig.APPLICATION_ID}",
            BuildConfig.APPLICATION_ID.startsWith("de.sidebyside.app"),
        )
    }

    @Test
    fun carriesNoTraceOfTheM2ReferenceFlow() {
        // `reference` named a technical flow and `next` is this repository's
        // codename. Neither is the product, and neither may reach a store.
        assertFalse(BuildConfig.APPLICATION_ID.contains("reference"))
        assertFalse(BuildConfig.APPLICATION_ID.contains("next"))
    }

    @Test
    fun marksADebugBuildAsSomethingOtherThanARelease() {
        // Without this a developer's build would replace, or be replaced by,
        // the one from the store.
        assertEquals("de.sidebyside.app.debug", BuildConfig.APPLICATION_ID)
    }
}
