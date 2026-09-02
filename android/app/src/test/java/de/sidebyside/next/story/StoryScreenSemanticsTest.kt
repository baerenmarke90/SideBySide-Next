package de.sidebyside.next.story

import android.content.Context
import androidx.compose.ui.test.assertCountEquals
import androidx.compose.ui.test.assertIsDisplayed
import androidx.compose.ui.test.hasScrollAction
import androidx.compose.ui.test.junit4.createComposeRule
import androidx.compose.ui.test.onAllNodesWithText
import androidx.compose.ui.test.onNodeWithText
import androidx.compose.ui.test.performScrollToIndex
import androidx.test.core.app.ApplicationProvider
import de.sidebyside.next.design.SideBySideTheme
import de.sidebyside.next.reference.R
import java.time.LocalDate
import java.time.OffsetDateTime
import java.util.UUID
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Dispatchers
import org.junit.Assert.assertEquals
import org.junit.Assert.assertTrue
import org.junit.Rule
import org.junit.Test
import org.junit.runner.RunWith
import org.robolectric.RobolectricTestRunner
import org.robolectric.annotation.Config
import sidebyside.api.models.AuthorSummary
import sidebyside.api.models.HeartEmotion
import sidebyside.api.models.MediaType
import sidebyside.api.models.MemoryAttachmentSummary
import sidebyside.api.models.MemorySummary
import sidebyside.api.models.MilestoneSummary
import sidebyside.api.models.ResourceCapabilities
import sidebyside.api.models.SharedHeartMomentSummary
import sidebyside.api.models.StoryHeartMomentItem
import sidebyside.api.models.StoryItem
import sidebyside.api.models.StoryMemoryItem
import sidebyside.api.models.StoryMilestoneItem

/**
 * What a couple actually reads off the Story.
 */
@RunWith(RobolectricTestRunner::class)
@Config(sdk = [35])
class StoryScreenSemanticsTest {
    @get:Rule
    val composeRule = createComposeRule()

    private val context: Context get() = ApplicationProvider.getApplicationContext()

    // Each kind is rendered on its own: a lazy list only composes what is on
    // screen, so asserting three at once would test the window height.
    @Test
    fun namesAMemory() = assertKindIsNamed(memory(), R.string.story_kind_memory)

    @Test
    fun namesAMilestone() = assertKindIsNamed(milestone(), R.string.story_kind_milestone)

    @Test
    fun namesAHeartMoment() = assertKindIsNamed(heartMoment(), R.string.story_kind_heart_moment)

    private fun assertKindIsNamed(item: StoryItem, label: Int) {
        render(listOf(item))
        composeRule.onNodeWithText(context.getString(label)).assertIsDisplayed()
    }

    @Test
    fun writesTheDayOnceAboveTheEntriesThatShareIt() {
        val day = LocalDate.of(2026, 8, 20)
        render(listOf(memory(date = day), heartMoment(date = day)))

        val heading = day.format(
            java.time.format.DateTimeFormatter
                .ofLocalizedDate(java.time.format.FormatStyle.LONG)
                .withLocale(java.util.Locale.getDefault()),
        )
        assertEquals(1, composeRule.onAllNodesWithText(heading).fetchSemanticsNodes().size)
    }

    @Test
    fun saysTheStoryIsEmptyRatherThanShowingNothing() {
        // An empty Story and a Story that failed to load must not look alike.
        render(emptyList())

        composeRule.onNodeWithText(context.getString(R.string.story_empty_title)).assertIsDisplayed()
    }

    @Test
    fun keepsALongTitleWholeInsteadOfCuttingIt() {
        val title = "The long summer evening by the lake where we decided to move in together"
        render(listOf(memory(title = title)))

        composeRule.onNodeWithText(title).assertIsDisplayed()
    }

    @Test
    fun namesWhoWroteEachEntry() {
        render(listOf(memory()))

        composeRule
            .onNodeWithText(context.getString(R.string.story_by_author, "Lea"))
            .assertIsDisplayed()
    }

    @Test
    fun aSingleImageNeverShowsACarouselPositionLabel() {
        // A single photograph has nothing to page between; a one-of-one
        // position label would be a fact no one asked for, not a helpful
        // indicator.
        render(listOf(memory(attachments = listOf(imageAttachment(position = 0)))))

        composeRule
            .onAllNodesWithText(context.getString(R.string.story_carousel_position, 1, 1))
            .assertCountEquals(0)
    }

    @Test
    @Config(qualifiers = "w320dp-h800dp")
    fun multiplePhotographsShowASwipeableCarouselWithAPositionLabel() {
        render(
            listOf(
                memory(
                    attachments = listOf(
                        imageAttachment(position = 0),
                        imageAttachment(position = 1),
                        imageAttachment(position = 2),
                    ),
                ),
            ),
        )

        composeRule
            .onNodeWithText(context.getString(R.string.story_carousel_position, 1, 3))
            .assertIsDisplayed()
    }

    @Test
    @Config(qualifiers = "w320dp-h800dp")
    fun scrollingNearTheEndOfTheStoryLoadsTheNextPageWithoutTappingAnything() {
        // Twelve entries sharing one day, so the LazyColumn's own item count
        // is exactly predictable: one day heading, twelve entries, and the
        // manual "load more" row — 14 items, indices 0..13 — rather than
        // guessing around interleaved per-entry day headings.
        val items = (0 until 12).map { index -> memory(title = "Entry $index") }
        var loadMoreCalls = 0
        render(items = items, onLoadMore = { loadMoreCalls++ }, loadingMore = false)

        composeRule.onNode(hasScrollAction()).performScrollToIndex(13)
        composeRule.waitForIdle()

        assertTrue(loadMoreCalls > 0)
    }

    private fun render(
        items: List<StoryItem>,
        onLoadMore: (() -> Unit)? = null,
        loadingMore: Boolean = false,
    ) {
        val store = StoryImageStore(scope = CoroutineScope(Dispatchers.Unconfined)) {
            error("This test renders no photographs.")
        }
        composeRule.setContent {
            SideBySideTheme {
                StoryScreen(
                    items = items,
                    imageStore = store,
                    generation = 0,
                    onLoadMore = onLoadMore,
                    loadingMore = loadingMore,
                )
            }
        }
    }
}

private fun imageAttachment(position: Int) = MemoryAttachmentSummary(
    hasThumbnail = true,
    height = 100,
    id = UUID.randomUUID(),
    mediaType = MediaType.IMAGE,
    mimeType = "image/jpeg",
    position = position,
    propertySize = 1024,
    status = "READY",
    width = 100,
)

private val CAPABILITIES = ResourceCapabilities(canComment = true, canDelete = true, canEdit = true)
private val AUTHOR = AuthorSummary(displayName = "Lea", id = UUID.randomUUID())
private val CREATED: OffsetDateTime = OffsetDateTime.now()
private val DAY: LocalDate = LocalDate.of(2026, 8, 20)

private fun memory(
    date: LocalDate = DAY,
    title: String = "A day by the sea",
    attachments: List<MemoryAttachmentSummary> = emptyList(),
) =
    StoryItem.MemoryWrapper(
        StoryMemoryItem(
            effectiveDate = date,
            kind = StoryMemoryItem.Kind.MEMORY,
            memory = MemorySummary(
                attachments = attachments,
                author = AUTHOR,
                capabilities = CAPABILITIES,
                createdAt = CREATED,
                happenedOn = date,
                id = UUID.randomUUID(),
                title = title,
            ),
        ),
    )

private fun milestone(date: LocalDate = DAY) = StoryItem.MilestoneWrapper(
    StoryMilestoneItem(
        effectiveDate = date,
        kind = StoryMilestoneItem.Kind.MILESTONE,
        milestone = MilestoneSummary(
            author = AUTHOR,
            capabilities = CAPABILITIES,
            createdAt = CREATED,
            happenedOn = date,
            id = UUID.randomUUID(),
            title = "Moved in together",
        ),
    ),
)

private fun heartMoment(date: LocalDate = DAY) = StoryItem.HeartMomentWrapper(
    StoryHeartMomentItem(
        effectiveDate = date,
        heartMoment = SharedHeartMomentSummary(
            attachment = null,
            author = AUTHOR,
            capabilities = CAPABILITIES,
            createdAt = CREATED,
            emotion = HeartEmotion.LOVED,
            happenedOn = date,
            id = UUID.randomUUID(),
            text = "Thank you for today",
        ),
        kind = StoryHeartMomentItem.Kind.HEART_MOMENT,
    ),
)
