package de.sidebyside.next.account

import android.content.Context
import androidx.compose.ui.test.assertIsEnabled
import androidx.compose.ui.test.assertIsNotEnabled
import androidx.compose.ui.test.hasClickAction
import androidx.compose.ui.test.hasSetTextAction
import androidx.compose.ui.test.hasText
import androidx.compose.ui.test.junit4.createComposeRule
import androidx.compose.ui.test.onNodeWithText
import androidx.compose.ui.test.performClick
import androidx.compose.ui.test.performScrollTo
import androidx.compose.ui.test.performTextClearance
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.test.performTextInput
import androidx.test.core.app.ApplicationProvider
import de.sidebyside.next.design.SideBySideTheme
import de.sidebyside.next.reference.AccountDeletionRecentAuthenticationCapabilities
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
        deletionAction().assertIsNotEnabled()
        composeRule
            .onNodeWithText(context.getString(R.string.account_delete_consequences_title))
            .assertDoesNotExist()
        assertEquals(0, deletes)
    }

    @Test
    fun offersExportBeforeDeletionWithoutMakingItRequired() {
        var exports = 0
        render(onOpenDataExport = { exports += 1 })

        deletionAction().performClick()
        composeRule
            .onNodeWithText(context.getString(R.string.account_delete_export_first))
            .performClick()

        assertEquals(1, exports)
        composeRule
            .onNodeWithText(context.getString(R.string.account_delete_consequences_title))
            .assertDoesNotExist()
    }

    @Test
    fun recentAuthenticationPrecedesExactTypedConfirmationAndDeletion() {
        var deletes = 0
        var passwordAttempts = 0
        render(
            onDeleteAccount = { deletes += 1 },
            onRecentAuthenticationPassword = {
                passwordAttempts += 1
                true
            },
        )

        deletionAction().performClick()
        composeRule
            .onNodeWithText(context.getString(R.string.account_delete_continue))
            .performClick()

        composeRule
            .onNodeWithText(context.getString(R.string.account_delete_reauth_title))
            .assertExists()
        composeRule
            .onNodeWithText(context.getString(R.string.account_delete_confirm_action))
            .assertDoesNotExist()

        composeRule.onNode(hasSetTextAction()).performTextInput("secret")
        composeRule
            .onNodeWithText(context.getString(R.string.account_delete_reauth_password_action))
            .performClick()
        composeRule.waitForIdle()
        assertEquals(1, passwordAttempts)

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
        finalAction.performScrollTo().assertIsEnabled().performClick()

        assertEquals(1, deletes)
    }

    private fun deletionAction() = composeRule.onNode(
        hasText(context.getString(R.string.account_delete_action)) and hasClickAction(),
    )

    private fun render(
        demoMode: Boolean = false,
        onOpenDataExport: () -> Unit = {},
        onDeleteAccount: () -> Unit = {},
        onRecentAuthenticationPassword: (String) -> Boolean = { true },
    ) {
        composeRule.setContent {
            var recentAuthenticationComplete by remember { mutableStateOf(false) }
            SideBySideTheme {
                AccountSettingsContent(
                    demoMode = demoMode,
                    busy = false,
                    problem = null,
                    recentAuthenticationCapabilities =
                        AccountDeletionRecentAuthenticationCapabilities(
                            localPassword = true,
                            passkey = false,
                            oidcConnections = emptyList(),
                        ),
                    recentAuthenticationBusy = false,
                    recentAuthenticationProblem = null,
                    recentAuthenticationComplete = recentAuthenticationComplete,
                    onLoadRecentAuthentication = {},
                    onRecentAuthenticationPassword = { password ->
                        recentAuthenticationComplete = onRecentAuthenticationPassword(password)
                    },
                    onRecentAuthenticationPasskey = {},
                    onRecentAuthenticationOidc = {},
                    onResetRecentAuthentication = { recentAuthenticationComplete = false },
                    onOpenDataExport = onOpenDataExport,
                    onDeleteAccount = onDeleteAccount,
                )
            }
        }
    }
}
