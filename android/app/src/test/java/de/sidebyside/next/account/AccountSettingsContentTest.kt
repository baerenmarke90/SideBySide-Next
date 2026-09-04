package de.sidebyside.next.account

import android.content.Context
import androidx.compose.ui.test.assertIsEnabled
import androidx.compose.ui.test.assertIsNotEnabled
import androidx.compose.ui.test.hasSetTextAction
import androidx.compose.ui.test.junit4.createComposeRule
import androidx.compose.ui.test.onNodeWithText
import androidx.compose.ui.test.performClick
import androidx.compose.ui.test.performTextClearance
import androidx.compose.ui.test.performTextInput
import androidx.test.core.app.ApplicationProvider
import de.sidebyside.next.design.SideBySideTheme
import de.sidebyside.next.reference.R
import org.junit.Assert.assertEquals
import org.junit.Rule
import org.junit.Test
import org.junit.runner.RunWith
import org.robolectric.RobolectricTestRunner
import org.robolectric.annotation.Config

@RunWith(RobolectricTestRunner::class)
@Config(sdk = [35])
class AccountSettingsContentTest {
    @get:Rule
    val composeRule = createComposeRule()

    private val context: Context get() = ApplicationProvider.getApplicationContext()

    @Test
    fun demoAccountCannotStartDeletion() {
        var deletes = 0
        render(demoMode = true, onDeleteAccount = { deletes += 1 })

        composeRule
            .onNodeWithText(context.getString(R.string.account_delete_demo_unavailable), substring = true)
            .assertExists()
        composeRule
            .onNodeWithText(context.getString(R.string.account_delete_action))
            .assertIsNotEnabled()
            .performClick()
        composeRule
            .onNodeWithText(context.getString(R.string.account_delete_consequences_title))
            .assertDoesNotExist()
        assertEquals(0, deletes)
    }

    @Test
    fun offersExportBeforeDeletionWithoutMakingItRequired() {
        var exports = 0
        render(onOpenDataExport = { exports += 1 })

        composeRule
            .onNodeWithText(context.getString(R.string.account_delete_action))
            .performClick()
        composeRule
            .onNodeWithText(context.getString(R.string.account_delete_export_first))
            .performClick()

        assertEquals(1, exports)
        composeRule
            .onNodeWithText(context.getString(R.string.account_delete_consequences_title))
            .assertDoesNotExist()
    }

    @Test
    fun exactTypedConfirmationUnlocksTheFinalDestructiveAction() {
        var deletes = 0
        render(onDeleteAccount = { deletes += 1 })

        composeRule
            .onNodeWithText(context.getString(R.string.account_delete_action))
            .performClick()
        composeRule
            .onNodeWithText(context.getString(R.string.account_delete_continue))
            .performClick()

        val finalAction = composeRule.onNodeWithText(
            context.getString(R.string.account_delete_confirm_action),
        )
        finalAction.assertIsNotEnabled()

        composeRule.onNode(hasSetTextAction()).performTextInput("WRONG")
        finalAction.assertIsNotEnabled()

        composeRule.onNode(hasSetTextAction()).performTextClearance()
        composeRule.onNode(hasSetTextAction()).performTextInput(
            context.getString(R.string.account_delete_confirmation_phrase),
        )
        finalAction.assertIsEnabled().performClick()

        assertEquals(1, deletes)
    }

    private fun render(
        demoMode: Boolean = false,
        onOpenDataExport: () -> Unit = {},
        onDeleteAccount: () -> Unit = {},
    ) {
        composeRule.setContent {
            SideBySideTheme {
                AccountSettingsContent(
                    demoMode = demoMode,
                    busy = false,
                    problem = null,
                    onOpenDataExport = onOpenDataExport,
                    onDeleteAccount = onDeleteAccount,
                )
            }
        }
    }
}
