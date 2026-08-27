package de.sidebyside.next.reference

import java.util.Locale
import org.junit.Assert.assertEquals
import org.junit.Assert.assertNotEquals
import org.junit.Assert.assertTrue
import org.junit.Test
import sidebyside.api.models.StoryItem
import sidebyside.api.models.StoryPage

class StoryItemDeserializationTest {
    @Test
    fun generatedStoryItemSerializerDeserializesMemoryDiscriminator() {
        val payload = """
            {
              "hasMore": false,
              "items": [
                {
                  "kind": "MEMORY",
                  "effectiveDate": "2026-08-26",
                  "memory": {
                    "attachments": [],
                    "author": {
                      "displayName": "A",
                      "id": "00000000-0000-0000-0000-000000000001"
                    },
                    "capabilities": {
                      "canComment": true,
                      "canDelete": true,
                      "canEdit": true
                    },
                    "createdAt": "2026-08-26T08:00:00Z",
                    "happenedOn": "2026-08-26",
                    "id": "00000000-0000-0000-0000-000000000002",
                    "title": "Am See"
                  }
                }
              ],
              "nextCursor": null
            }
        """.trimIndent()

        val story = SideBySideJson.decodeFromString(StoryPage.serializer(), payload)

        assertEquals(1, story.items.size)
        val item = story.items.single()
        assertTrue(item is StoryItem.MemoryWrapper)
        assertEquals("Am See", (item as StoryItem.MemoryWrapper).value.memory.title)
        assertEquals(UiMessage(R.string.ref_story_memory, listOf("Am See")), storyItemLabel(item))
        assertNotEquals(storyItemDate(item, Locale.GERMAN), storyItemDate(item, Locale.ENGLISH))
    }
}
