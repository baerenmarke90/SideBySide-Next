package de.sidebyside.next.story

import android.content.Context
import androidx.compose.ui.test.assertIsDisplayed
import androidx.compose.ui.test.assertIsEnabled
import androidx.compose.ui.test.assertIsNotEnabled
import androidx.compose.ui.test.junit4.createComposeRule
import androidx.compose.ui.test.onNodeWithText
import androidx.compose.ui.test.performClick
import androidx.compose.ui.test.performScrollTo
import androidx.compose.ui.test.performTextClearance
import androidx.compose.ui.test.performTextInput
import androidx.test.core.app.ApplicationProvider
import de.sidebyside.next.design.SideBySideTheme
import de.sidebyside.next.reference.R
import java.time.LocalDate
import java.time.OffsetDateTime
import java.util.UUID
import org.junit.Assert.assertEquals
import org.junit.Rule
import org.junit.Test
import org.junit.runner.RunWith
import org.robolectric.RobolectricTestRunner
import org.robolectric.annotation.Config
import sidebyside.api.models.AuthorSummary
import sidebyside.api.models.ContentVisibility
import sidebyside.api.models.HeartEmotion
import sidebyside.api.models.HeartMomentDetail
import sidebyside.api.models.ResourceCapabilities

/**
 * The HeartMoment edit-in-place form (#603): the card's own "Bearbeiten"
 * button swaps it for a form pre-filled from the moment's current values,
 * mirroring [MilestoneCreateScreen]'s submit-gating shape rather than
 * inventing a new one.
 */
@RunWith(RobolectricTestRunner::class)
@Config(sdk = [35], qualifiers = "w320dp-h1200dp")
class HeartMomentsScreenTest {
    @get:Rule
    val composeRule = createComposeRule()

    private val context: Context get() = ApplicationProvider.getApplicationContext()
    private val momentId: UUID = UUID.randomUUID()

    @Test
    fun editingReplacesTheCardWithAPrefilledFormAndSavesTheChanges() {
        var edited: List<String>? = null
        render(onEdit = { id, text, emotion, happenedOn -> edited = listOf(id.toString(), text, emotion.name, happenedOn) })

        composeRule
            .onNodeWithText(context.getString(R.string.heart_moment_edit))
            .performScrollTo()
            .performClick()

        // Found by its current value, not a label — proof the form opened
        // pre-filled from the moment rather than blank.
        composeRule.onNodeWithText("A moment worth keeping").assertIsDisplayed()

        composeRule
            .onNodeWithText(context.getString(R.string.heart_moment_save_changes))
            .performScrollTo()
            .performClick()

        assertEquals(
            listOf(momentId.toString(), "A moment worth keeping", HeartEmotion.GRATEFUL.name, "2026-08-18"),
            edited,
        )
    }

    @Test
    fun cancellingEditDiscardsWithoutCallingOnEdit() {
        var editCalls = 0
        render(onEdit = { _, _, _, _ -> editCalls++ })

        composeRule
            .onNodeWithText(context.getString(R.string.heart_moment_edit))
            .performScrollTo()
            .performClick()
        composeRule
            .onNodeWithText(context.getString(R.string.heart_moment_cancel))
            .performScrollTo()
            .performClick()

        assertEquals(0, editCalls)
        // Back to the display card: the edit-only save-changes button is gone.
        composeRule.onNodeWithText(context.getString(R.string.heart_moment_edit)).assertIsEnabled()
    }

    @Test
    fun clearingTheTextWhileEditingDisablesSavingChanges() {
        render()

        composeRule
            .onNodeWithText(context.getString(R.string.heart_moment_edit))
            .performScrollTo()
            .performClick()
        composeRule
            .onNodeWithText(context.getString(R.string.heart_moment_save_changes))
            .performScrollTo()
            .assertIsEnabled()

        composeRule.onNodeWithText("A moment worth keeping").performTextClearance()
        composeRule
            .onNodeWithText(context.getString(R.string.heart_moment_save_changes))
            .performScrollTo()
            .assertIsNotEnabled()
    }

    @Test
    fun theNewMomentFormRequiresADateBeforeSubmitEnables() {
        render()

        composeRule.onNodeWithText(context.getString(R.string.heart_moment_text))
            .performScrollTo()
            .performTextInput("Something worth keeping")
        composeRule
            .onNodeWithText(context.getString(R.string.heart_moment_save))
            .performScrollTo()
            .assertIsNotEnabled()

        composeRule.onNodeWithText(context.getString(R.string.heart_moment_happened_on))
            .performScrollTo()
            .performTextInput("2026-08-20")
        composeRule
            .onNodeWithText(context.getString(R.string.heart_moment_save))
            .performScrollTo()
            .assertIsEnabled()
    }

    private fun render(
        onCreate: (String, HeartEmotion, String, ContentVisibility) -> Unit = { _, _, _, _ -> },
        onEdit: (UUID, String, HeartEmotion, String) -> Unit = { _, _, _, _ -> },
        onChangeVisibility: (UUID, ContentVisibility) -> Unit = { _, _ -> },
        onDelete: (UUID) -> Unit = {},
    ) {
        val moment = HeartMomentDetail(
            attachment = null,
            author = AuthorSummary(displayName = "Lea", id = UUID.randomUUID()),
            authorId = UUID.randomUUID(),
            capabilities = ResourceCapabilities(canComment = true, canDelete = true, canEdit = true),
            createdAt = OffsetDateTime.now(),
            emotion = HeartEmotion.GRATEFUL,
            happenedOn = LocalDate.of(2026, 8, 18),
            id = momentId,
            spaceId = UUID.randomUUID(),
            text = "A moment worth keeping",
            updatedAt = OffsetDateTime.now(),
            version = 1,
            visibility = ContentVisibility.SHARED,
        )

        composeRule.setContent {
            SideBySideTheme {
                HeartMomentsScreen(
                    moments = listOf(moment),
                    busy = false,
                    problem = null,
                    statusMessage = null,
                    onBack = {},
                    onCreate = onCreate,
                    onEdit = onEdit,
                    onChangeVisibility = onChangeVisibility,
                    onDelete = onDelete,
                )
            }
        }
    }
}
