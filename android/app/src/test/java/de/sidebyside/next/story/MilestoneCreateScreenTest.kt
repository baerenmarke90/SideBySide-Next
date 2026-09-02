package de.sidebyside.next.story

import android.content.Context
import androidx.compose.ui.test.assertIsDisplayed
import androidx.compose.ui.test.assertIsEnabled
import androidx.compose.ui.test.assertIsNotEnabled
import androidx.compose.ui.test.junit4.createComposeRule
import androidx.compose.ui.test.onNodeWithText
import androidx.compose.ui.test.performClick
import androidx.compose.ui.test.performScrollTo
import androidx.compose.ui.test.performTextInput
import androidx.test.core.app.ApplicationProvider
import de.sidebyside.next.design.SideBySideTheme
import de.sidebyside.next.reference.R
import de.sidebyside.next.shell.UiProblem
import de.sidebyside.next.shell.UiStateKind
import org.junit.Assert.assertEquals
import org.junit.Rule
import org.junit.Test
import org.junit.runner.RunWith
import org.robolectric.RobolectricTestRunner
import org.robolectric.annotation.Config

/**
 * The Milestone-creation form (#585): title and happenedOn are both required
 * before submit enables, mirroring [MilestoneCreateScreen]'s own guard so a
 * change to one side cannot silently drift from the other.
 */
@RunWith(RobolectricTestRunner::class)
@Config(sdk = [35])
class MilestoneCreateScreenTest {
    @get:Rule
    val composeRule = createComposeRule()

    private val context: Context get() = ApplicationProvider.getApplicationContext()

    @Test
    fun submitIsDisabledUntilBothTitleAndDateAreFilledIn() {
        render()

        composeRule
            .onNodeWithText(context.getString(R.string.milestone_create_submit))
            .assertIsNotEnabled()

        composeRule.onNodeWithText(context.getString(R.string.milestone_title_label))
            .performTextInput("Moved in together")
        composeRule
            .onNodeWithText(context.getString(R.string.milestone_create_submit))
            .assertIsNotEnabled()

        composeRule.onNodeWithText(context.getString(R.string.milestone_happened_on_label))
            .performTextInput("2026-08-20")
        composeRule
            .onNodeWithText(context.getString(R.string.milestone_create_submit))
            .assertIsEnabled()
    }

    @Test
    fun submittingPassesAllThreeFieldsThrough() {
        var created: List<String>? = null
        render(onCreate = { title, body, happenedOn -> created = listOf(title, body, happenedOn) })

        composeRule.onNodeWithText(context.getString(R.string.milestone_title_label))
            .performTextInput("Moved in together")
        composeRule.onNodeWithText(context.getString(R.string.milestone_body_label))
            .performTextInput("The day the boxes arrived")
        composeRule.onNodeWithText(context.getString(R.string.milestone_happened_on_label))
            .performTextInput("2026-08-20")
        composeRule
            .onNodeWithText(context.getString(R.string.milestone_create_submit))
            .performScrollTo()
            .performClick()

        assertEquals(listOf("Moved in together", "The day the boxes arrived", "2026-08-20"), created)
    }

    @Test
    fun busySuppressesSubmitEvenWithBothFieldsFilledIn() {
        render(busy = true)

        composeRule.onNodeWithText(context.getString(R.string.milestone_title_label))
            .performTextInput("Moved in together")
        composeRule.onNodeWithText(context.getString(R.string.milestone_happened_on_label))
            .performTextInput("2026-08-20")

        composeRule
            .onNodeWithText(context.getString(R.string.milestone_create_submit))
            .assertIsNotEnabled()
    }

    @Test
    fun aProblemIsShownWhenOneIsPassedIn() {
        render(
            problem = UiProblem(
                kind = UiStateKind.Error,
                titleRes = R.string.state_validation_title,
                bodyRes = R.string.state_validation_body,
                retryable = false,
            ),
        )

        composeRule
            .onNodeWithText(context.getString(R.string.state_validation_title))
            .assertIsDisplayed()
    }

    @Test
    fun backInvokesTheCallback() {
        var backCalls = 0
        render(onBack = { backCalls++ })

        composeRule.onNodeWithText(context.getString(R.string.memory_back)).performClick()

        assertEquals(1, backCalls)
    }

    private fun render(
        busy: Boolean = false,
        problem: UiProblem? = null,
        onBack: () -> Unit = {},
        onCreate: (title: String, body: String, happenedOn: String) -> Unit = { _, _, _ -> },
    ) {
        composeRule.setContent {
            SideBySideTheme {
                MilestoneCreateScreen(
                    busy = busy,
                    problem = problem,
                    onBack = onBack,
                    onCreate = onCreate,
                )
            }
        }
    }
}
