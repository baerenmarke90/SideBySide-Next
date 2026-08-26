package de.sidebyside.next.reference

import java.util.UUID
import org.junit.Assert.assertFalse
import org.junit.Assert.assertTrue
import org.junit.Test

class ReferenceConfigTest {
    @Test
    fun requiresApiBaseAndSpaceId() {
        assertFalse(ReferenceConfig("", null).isConfigured)
        assertFalse(ReferenceConfig("https://example.invalid", null).isConfigured)
        assertTrue(
            ReferenceConfig(
                "https://example.invalid",
                UUID.fromString("00000000-0000-0000-0000-000000000001"),
            ).isConfigured,
        )
    }
}
