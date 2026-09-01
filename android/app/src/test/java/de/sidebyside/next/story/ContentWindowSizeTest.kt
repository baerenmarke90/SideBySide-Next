package de.sidebyside.next.story

import android.content.Context
import androidx.compose.ui.test.assertIsDisplayed
import androidx.compose.ui.test.junit4.createComposeRule
import androidx.compose.ui.test.onNodeWithText
import androidx.test.core.app.ApplicationProvider
import de.sidebyside.next.design.SideBySideTheme
import de.sidebyside.next.reference.R
import java.time.LocalDate
import java.time.OffsetDateTime
import java.util.UUID
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Dispatchers
import org.junit.Rule
import org.junit.Test
import org.junit.runner.RunWith
import org.robolectric.RobolectricTestRunner
import org.robolectric.annotation.Config
import sidebyside.api.models.AuthorSummary
import sidebyside.api.models.CommentDetail
import sidebyside.api.models.MemorySummary
import sidebyside.api.models.ResourceCapabilities
import sidebyside.api.models.StoryItem
import sidebyside.api.models.StoryMemoryItem

/**
 * The content surfaces at the window sizes they actually meet.
 *
 * The shell's own width behaviour was already covered; the surfaces inside it
 * were not, which the earlier slices claimed and did not have. A phone in
 * portrait and an unfolded foldable are the two real cases, and long text at
 * the narrow end is where a layout gives way.
 */
@RunWith(RobolectricTestRunner::class)
@Config(sdk = [35])
class ContentWindowSizeTest {
    @get:Rule
    val composeRule = createComposeRule()

    private val context: Context get() = ApplicationProvider.getApplicationContext()

    @Test
    @Config(qualifiers = "w320dp-h800dp")
    fun theStoryHoldsALongTitleOnANarrowPhone() {
        renderStory()
        composeRule.onNodeWithText(LONG_TITLE).assertIsDisplayed()
    }

    @Test
    @Config(qualifiers = "w840dp-h1200dp")
    fun theStoryHoldsALongTitleOnAnUnfoldedScreen() {
        renderStory()
        composeRule.onNodeWithText(LONG_TITLE).assertIsDisplayed()
    }

    @Test
    @Config(qualifiers = "w320dp-h800dp")
    fun aCommentThreadStaysReadableOnANarrowPhone() {
        renderComments()
        composeRule.onNodeWithText(LONG_COMMENT).assertIsDisplayed()
        composeRule.onNodeWithText(context.getString(R.string.comments_title)).assertIsDisplayed()
    }

    @Test
    @Config(qualifiers = "w840dp-h1200dp")
    fun aCommentThreadStaysReadableOnAnUnfoldedScreen() {
        renderComments()
        composeRule.onNodeWithText(LONG_COMMENT).assertIsDisplayed()
    }

    @Test
    @Config(qualifiers = "w320dp-h800dp")
    fun theStorysEmptyStateSurvivesTheNarrowestCase() {
        composeRule.setContent {
            SideBySideTheme {
                StoryScreen(items = emptyList(), imageStore = store(), generation = 0)
            }
        }
        composeRule.onNodeWithText(context.getString(R.string.story_empty_title)).assertIsDisplayed()
    }

    private fun renderStory() {
        composeRule.setContent {
            SideBySideTheme {
                StoryScreen(items = listOf(memory()), imageStore = store(), generation = 0)
            }
        }
    }

    private fun renderComments() {
        composeRule.setContent {
            SideBySideTheme {
                MemoryComments(
                    comments = listOf(comment()),
                    accountId = null,
                    busy = false,
                    problem = null,
                    onAdd = {},
                    onEdit = { _, _ -> },
                    onDelete = {},
                )
            }
        }
    }

    private fun store() = StoryImageStore(scope = CoroutineScope(Dispatchers.Unconfined)) {
        error("This test renders no photographs.")
    }
}

private const val LONG_TITLE =
    "The long summer evening by the lake where we finally decided to move in together"
private const val LONG_COMMENT =
    "I keep thinking about that evening, the way the light stayed on the water " +
        "long after we had stopped talking about anything in particular."

private val CAPABILITIES = ResourceCapabilities(canComment = true, canDelete = true, canEdit = true)
private val AUTHOR = AuthorSummary(displayName = "Lea", id = UUID.randomUUID())

private fun memory(): StoryItem = StoryItem.MemoryWrapper(
    StoryMemoryItem(
        effectiveDate = LocalDate.of(2026, 8, 20),
        kind = StoryMemoryItem.Kind.MEMORY,
        memory = MemorySummary(
            attachments = emptyList(),
            author = AUTHOR,
            capabilities = CAPABILITIES,
            createdAt = OffsetDateTime.now(),
            happenedOn = LocalDate.of(2026, 8, 20),
            id = UUID.randomUUID(),
            title = LONG_TITLE,
        ),
    ),
)

private fun comment() = CommentDetail(
    author = AUTHOR,
    authorId = UUID.randomUUID(),
    body = LONG_COMMENT,
    createdAt = OffsetDateTime.now(),
    id = UUID.randomUUID(),
    spaceId = UUID.randomUUID(),
    updatedAt = OffsetDateTime.now(),
    version = 1,
)
