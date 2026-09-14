package de.sidebyside.next.reference

import org.junit.Assert.assertEquals
import org.junit.Assert.assertNull
import org.junit.Test
import sidebyside.api.models.DashboardView

/**
 * Issue #790 added `keepsake` to the Dashboard contract. The generated Kotlin
 * field is required-but-nullable (`val keepsake: DashboardItem?` with no
 * default), so this proves the app's actual [SideBySideJson] configuration
 * (`explicitNulls = false`) still decodes a response from a server that
 * predates the field, rather than throwing `MissingFieldException` during a
 * rolling/staggered deployment where an already-installed app can reach an
 * older or newer backend than the one it was built against.
 */
class DashboardViewWireCompatibilityTest {
    @Test
    fun decodesDashboardResponseMissingTheKeepsakeKeyAsNull() {
        val payload = """
            {
              "recentShared": [],
              "relationshipDuration": null,
              "retrospective": null,
              "sharedStorySummary": {
                "heartMoments": 0,
                "memories": 0,
                "milestones": 0
              },
              "space": {
                "partner": null,
                "spaceId": "00000000-0000-0000-0000-000000000010"
              },
              "upcoming": []
            }
        """.trimIndent()

        val view = SideBySideJson.decodeFromString(DashboardView.serializer(), payload)

        assertNull(view.keepsake)
    }

    @Test
    fun decodesDashboardResponseWithAnExplicitKeepsake() {
        val payload = """
            {
              "keepsake": {
                "id": "00000000-0000-0000-0000-000000000002",
                "type": "MEMORY",
                "titleOrText": "Am See",
                "previewAttachmentId": "00000000-0000-0000-0000-000000000003"
              },
              "recentShared": [],
              "relationshipDuration": null,
              "retrospective": null,
              "sharedStorySummary": {
                "heartMoments": 0,
                "memories": 0,
                "milestones": 0
              },
              "space": {
                "partner": null,
                "spaceId": "00000000-0000-0000-0000-000000000010"
              },
              "upcoming": []
            }
        """.trimIndent()

        val view = SideBySideJson.decodeFromString(DashboardView.serializer(), payload)

        assertEquals("Am See", view.keepsake?.titleOrText)
    }
}
