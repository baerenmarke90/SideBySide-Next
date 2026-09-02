package de.sidebyside.next.shell

import android.content.Context
import androidx.compose.ui.test.assertIsDisplayed
import androidx.compose.ui.test.junit4.createComposeRule
import androidx.compose.ui.test.onNodeWithContentDescription
import androidx.compose.ui.test.onNodeWithText
import androidx.compose.ui.test.performClick
import androidx.test.core.app.ApplicationProvider
import de.sidebyside.next.design.SideBySideTheme
import de.sidebyside.next.reference.R
import org.junit.Assert.assertEquals
import org.junit.Rule
import org.junit.Test
import org.junit.runner.RunWith
import org.robolectric.RobolectricTestRunner
import org.robolectric.annotation.Config

/**
 * The shell-wide quick-create trigger (#577).
 */
@RunWith(RobolectricTestRunner::class)
@Config(sdk = [35], qualifiers = "w320dp-h800dp")
class QuickCreateFabTest {
    @get:Rule
    val composeRule = createComposeRule()

    private val context: Context get() = ApplicationProvider.getApplicationContext()

    @Test
    fun theTriggerOffersAllThreeCreatableKindsOnceOpened() {
        render()

        composeRule
            .onNodeWithContentDescription(context.getString(R.string.quick_create_trigger))
            .performClick()
        composeRule.waitForIdle()

        composeRule.onNodeWithText(context.getString(R.string.quick_create_memory)).assertIsDisplayed()
        composeRule.onNodeWithText(context.getString(R.string.quick_create_heart_moment)).assertIsDisplayed()
        composeRule.onNodeWithText(context.getString(R.string.quick_create_private_note)).assertIsDisplayed()
    }

    @Test
    fun choosingMemoryInvokesOnlyTheMemoryCallback() {
        var memoryCalls = 0
        var heartMomentCalls = 0
        var privateNoteCalls = 0
        render(
            onCreateMemory = { memoryCalls++ },
            onCreateHeartMoment = { heartMomentCalls++ },
            onCreatePrivateNote = { privateNoteCalls++ },
        )

        composeRule
            .onNodeWithContentDescription(context.getString(R.string.quick_create_trigger))
            .performClick()
        composeRule.waitForIdle()
        composeRule.onNodeWithText(context.getString(R.string.quick_create_memory)).performClick()
        composeRule.waitForIdle()

        assertEquals(1, memoryCalls)
        assertEquals(0, heartMomentCalls)
        assertEquals(0, privateNoteCalls)
    }

    @Test
    fun choosingAnItemClosesTheSheetAfterward() {
        render()

        composeRule
            .onNodeWithContentDescription(context.getString(R.string.quick_create_trigger))
            .performClick()
        composeRule.waitForIdle()
        composeRule.onNodeWithText(context.getString(R.string.quick_create_private_note)).performClick()
        composeRule.waitForIdle()

        composeRule
            .onNodeWithText(context.getString(R.string.quick_create_memory))
            .assertDoesNotExist()
    }

    private fun render(
        onCreateMemory: () -> Unit = {},
        onCreateHeartMoment: () -> Unit = {},
        onCreatePrivateNote: () -> Unit = {},
    ) {
        composeRule.setContent {
            SideBySideTheme {
                QuickCreateFab(
                    onCreateMemory = onCreateMemory,
                    onCreateHeartMoment = onCreateHeartMoment,
                    onCreatePrivateNote = onCreatePrivateNote,
                )
            }
        }
    }
}
