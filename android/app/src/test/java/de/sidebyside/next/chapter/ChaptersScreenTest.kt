package de.sidebyside.next.chapter

import android.content.Context
import androidx.compose.ui.test.junit4.createComposeRule
import androidx.compose.ui.test.onNodeWithText
import androidx.compose.ui.test.performClick
import androidx.compose.ui.test.performScrollTo
import androidx.compose.ui.test.performTextInput
import androidx.test.core.app.ApplicationProvider
import de.sidebyside.next.design.SideBySideTheme
import de.sidebyside.next.reference.R
import java.time.OffsetDateTime
import java.util.UUID
import org.junit.Assert.assertEquals
import org.junit.Rule
import org.junit.Test
import org.junit.runner.RunWith
import org.robolectric.RobolectricTestRunner
import org.robolectric.annotation.Config
import sidebyside.api.models.AuthorSummary
import sidebyside.api.models.PlaceDetail
import sidebyside.api.models.ResourceCapabilities

/** The Place field #605 added to Chapter create/edit, matching Web's ChapterProductPage. */
@RunWith(RobolectricTestRunner::class)
@Config(sdk = [35], qualifiers = "w320dp-h1200dp")
class ChaptersScreenTest {
    @get:Rule
    val composeRule = createComposeRule()

    private val context: Context get() = ApplicationProvider.getApplicationContext()

    @Test
    fun addingAChapterCanCarryAChosenPlace() {
        val place = PlaceDetail(
            address = null,
            capabilities = ResourceCapabilities(canComment = false, canDelete = true, canEdit = true),
            createdAt = OffsetDateTime.now(),
            createdBy = UUID.randomUUID(),
            creator = AuthorSummary(displayName = "Lea", id = UUID.randomUUID()),
            description = null,
            id = UUID.randomUUID(),
            latitude = null,
            longitude = null,
            name = "The coast",
            spaceId = UUID.randomUUID(),
            updatedAt = OffsetDateTime.now(),
            version = 1,
        )
        var added: UUID? = null

        composeRule.setContent {
            SideBySideTheme {
                ChaptersScreen(
                    chapters = emptyList(),
                    places = listOf(place),
                    busy = false,
                    problem = null,
                    onBack = {},
                    onOpen = {},
                    onAdd = { _, _, _, _, placeId -> added = placeId },
                    onEdit = { _, _, _, _, _, _ -> },
                    onDelete = {},
                )
            }
        }

        composeRule.onNodeWithText(context.getString(R.string.chapter_title_hint))
            .performScrollTo()
            .performTextInput("Our first year")
        composeRule.onNodeWithText(context.getString(R.string.place_picker_none))
            .performScrollTo()
            .performClick()
        composeRule.onNodeWithText("The coast").performClick()
        composeRule.onNodeWithText(context.getString(R.string.chapter_add))
            .performScrollTo()
            .performClick()

        assertEquals(place.id, added)
    }
}
