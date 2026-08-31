package de.sidebyside.next.reference

import org.junit.Assert.assertFalse
import org.junit.Assert.assertTrue
import org.junit.Test

class ReferenceConfigTest {
    @Test
    fun requiresOnlyTheServerAddress() {
        // The Space used to be operator configuration. It is now derived from
        // the account's Memberships after authentication, so a build is not
        // tied to one couple and a couple never enters a technical value.
        assertFalse(ReferenceConfig("").isConfigured)
        assertTrue(ReferenceConfig("https://example.invalid").isConfigured)
    }
}
