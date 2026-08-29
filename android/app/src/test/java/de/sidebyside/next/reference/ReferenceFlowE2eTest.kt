package de.sidebyside.next.reference

import java.time.LocalDate
import java.util.Base64
import java.util.UUID
import kotlinx.coroutines.runBlocking
import org.junit.Assert.assertEquals
import org.junit.Assert.assertNotNull
import org.junit.Assert.assertTrue
import org.junit.Assume.assumeTrue
import org.junit.Test
import sidebyside.api.models.StoryItem

class ReferenceFlowE2eTest {
    @Test
    fun realClientRunsMemoryImageTimelineAndAuthorizedReadAgainstSideBySideStack() = runBlocking {
        assumeTrue(
            "Only the dedicated G2 E2E workflow provides the real SideBySide stack.",
            System.getenv("G2_E2E_ENABLED") == "1",
        )

        val apiBaseUrl = requiredEnv("G2_E2E_API_BASE")
        val email = requiredEnv("G2_E2E_EMAIL")
        val password = requiredEnv("G2_E2E_PASSWORD")
        val spaceId = UUID.fromString(requiredEnv("G2_E2E_SPACE_ID"))

        val api = OkHttpReferenceApi(apiBaseUrl)
        val session = api.signIn(email, password)
        val accessToken = session.tokens.accessToken
        val image = SelectedImage(
            bytes = Base64.getDecoder().decode(PNG_FIXTURE),
            displayName = "g2-android.png",
            mimeType = "image/png",
        )

        val result = runMemoryMediaStoryFlow(
            api = api,
            spaceId = spaceId,
            accessToken = accessToken,
            title = "G2 Android E2E",
            body = "Real Android transport -> HTTP -> API -> PostgreSQL -> MediaStore -> Story.",
            happenedOn = LocalDate.of(2026, 8, 26),
            image = image,
        )

        assertEquals("G2 Android E2E", result.memory.title)
        assertEquals(1, result.memory.attachments.size)

        val storyMemory = result.story.items
            .filterIsInstance<StoryItem.MemoryWrapper>()
            .firstOrNull { it.value.memory.id == result.memory.id }
        assertNotNull(storyMemory)
        assertEquals("G2 Android E2E", storyMemory!!.value.memory.title)

        val imageBytes = requireNotNull(result.imageBytes)
        assertTrue(imageBytes.size >= 8)
        assertEquals(
            listOf<Byte>(-119, 80, 78, 71, 13, 10, 26, 10),
            imageBytes.take(8),
        )
    }

    private fun requiredEnv(name: String): String =
        System.getenv(name)?.takeIf { it.isNotBlank() }
            ?: error("$name must be set for the G2 E2E run.")

    private companion object {
        const val PNG_FIXTURE =
            "iVBORw0KGgoAAAANSUhEUgAAAAIAAAACCAIAAAD91JpzAAAAFklEQVR4nGOUs4liYGBgYmBgYGBgAAAIXgC4cKsbrQAAAABJRU5ErkJggg=="
    }
}