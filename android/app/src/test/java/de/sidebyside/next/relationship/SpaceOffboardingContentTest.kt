package de.sidebyside.next.relationship

import android.content.Context
import androidx.compose.ui.test.assertIsNotEnabled
import androidx.compose.ui.test.hasClickAction
import androidx.compose.ui.test.hasSetTextAction
import androidx.compose.ui.test.hasText
import androidx.compose.ui.test.junit4.createComposeRule
import androidx.compose.ui.test.onNodeWithText
import androidx.compose.ui.test.performClick
import androidx.compose.ui.test.performScrollTo
import androidx.compose.ui.test.performTextInput
import androidx.test.core.app.ApplicationProvider
import de.sidebyside.next.design.SideBySideTheme
import de.sidebyside.next.reference.R
import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertTrue
import org.junit.Rule
import org.junit.Test
import org.junit.runner.RunWith
import org.robolectric.RobolectricTestRunner
import org.robolectric.annotation.Config

@RunWith(RobolectricTestRunner::class)
@Config(sdk = [35])
class SpaceOffboardingContentTest {
    @get:Rule
    val composeRule = createComposeRule()

    private val context: Context get() = ApplicationProvider.getApplicationContext()

    @Test
    fun demoSpaceCannotStartSelfExit() {
        var leaves = 0
        render(demoMode = true, onLeaveSpace = { leaves += 1 })

        composeRule
            .onNodeWithText(
                context.getString(R.string.space_offboarding_demo_unavailable),
                substring = true,
            )
            .assertExists()
        exitAction().assertIsNotEnabled()
        composeRule
            .onNodeWithText(context.getString(R.string.space_offboarding_consequences_title))
            .assertDoesNotExist()
        assertEquals(0, leaves)
    }

    @Test
    fun exportIsOptionalAndDoesNotTriggerExit() {
        var exports = 0
        var leaves = 0
        render(
            onOpenDataExport = { exports += 1 },
            onLeaveSpace = { leaves += 1 },
        )

        exitAction().performClick()
        composeRule
            .onNodeWithText(context.getString(R.string.space_offboarding_export_first))
            .performClick()

        assertEquals(1, exports)
        assertEquals(0, leaves)
        composeRule
            .onNodeWithText(context.getString(R.string.space_offboarding_consequences_title))
            .assertDoesNotExist()
    }

    @Test
    fun confirmationGuardRequiresExactPhraseAndIdleState() {
        val phrase = "BEREICH VERLASSEN"

        assertFalse(
            spaceOffboardingConfirmationEnabled(
                busy = false,
                confirmation = "",
                phrase = phrase,
            )
        )
        assertFalse(
            spaceOffboardingConfirmationEnabled(
                busy = false,
                confirmation = "WRONG",
                phrase = phrase,
            )
        )
        assertFalse(
            spaceOffboardingConfirmationEnabled(
                busy = true,
                confirmation = phrase,
                phrase = phrase,
            )
        )
        assertTrue(
            spaceOffboardingConfirmationEnabled(
                busy = false,
                confirmation = phrase,
                phrase = phrase,
            )
        )
    }

    @Test
    fun exactTypedConfirmationTriggersFinalExit() {
        var leaves = 0
        render(onLeaveSpace = { leaves += 1 })

        exitAction().performClick()
        // The consequences dialog scrolls on small screens, so the continue
        // action has to be brought into the dialog window before it is clicked.
        composeRule
            .onNodeWithText(context.getString(R.string.space_offboarding_continue))
            .performScrollTo()
            .performClick()
        composeRule.onNode(hasSetTextAction()).performTextInput(
            context.getString(R.string.space_offboarding_confirmation_phrase),
        )

        composeRule.onNode(
            hasText(context.getString(R.string.space_offboarding_confirm_action)) and hasClickAction(),
        ).performScrollTo().performClick()

        assertEquals(1, leaves)
    }

    private fun exitAction() = composeRule.onNode(
        hasText(context.getString(R.string.space_offboarding_action)) and hasClickAction(),
    )

    private fun render(
        demoMode: Boolean = false,
        onOpenDataExport: () -> Unit = {},
        onLeaveSpace: () -> Unit = {},
    ) {
        composeRule.setContent {
            SideBySideTheme {
                SpaceOffboardingContent(
                    demoMode = demoMode,
                    busy = false,
                    problem = null,
                    onOpenDataExport = onOpenDataExport,
                    onLeaveSpace = onLeaveSpace,
                )
            }
        }
    }
}
