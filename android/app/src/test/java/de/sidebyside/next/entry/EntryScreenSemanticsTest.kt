package de.sidebyside.next.entry

import android.content.Context
import androidx.compose.runtime.CompositionLocalProvider
import androidx.compose.ui.platform.LocalDensity
import androidx.compose.ui.test.assertHasClickAction
import androidx.compose.ui.test.assertIsDisplayed
import androidx.compose.ui.test.assertIsEnabled
import androidx.compose.ui.test.assertIsNotEnabled
import androidx.compose.ui.test.hasClickAction
import androidx.compose.ui.test.hasText
import androidx.compose.ui.test.junit4.createComposeRule
import androidx.compose.ui.test.onNodeWithContentDescription
import androidx.compose.ui.test.onNodeWithText
import androidx.compose.ui.test.performClick
import androidx.compose.ui.test.performScrollTo
import androidx.compose.ui.test.performTextInput
import androidx.compose.ui.unit.Density
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
class EntryScreenSemanticsTest {
    @get:Rule
    val composeRule = createComposeRule()

    private val context: Context get() = ApplicationProvider.getApplicationContext()

    @Test
    fun entrySurfaceNamesItsFieldsAndPrimaryAction() {
        composeRule.setContent {
            SideBySideTheme { EntryScreen(onSignIn = { _, _ -> }, busy = false) }
        }

        composeRule.onNodeWithText(context.getString(R.string.entry_headline)).assertIsDisplayed()
        composeRule.onNodeWithText(context.getString(R.string.entry_email)).assertIsDisplayed()
        composeRule.onNodeWithText(context.getString(R.string.entry_password)).assertIsDisplayed()
        composeRule
            .onNode(hasText(context.getString(R.string.entry_sign_in)) and hasClickAction())
            .performScrollTo()
            .assertIsDisplayed()
            .assertHasClickAction()
    }

    @Test
    fun brandLockupIsAnnouncedOnceRatherThanPerElement() {
        composeRule.setContent {
            SideBySideTheme { EntryScreen(onSignIn = { _, _ -> }, busy = false) }
        }

        composeRule
            .onNodeWithContentDescription(context.getString(R.string.app_name))
            .assertIsDisplayed()
    }

    @Test
    fun signInStaysDisabledUntilBothCredentialsArePresent() {
        composeRule.setContent {
            SideBySideTheme { EntryScreen(onSignIn = { _, _ -> }, busy = false) }
        }

        val action = composeRule
            .onNode(hasText(context.getString(R.string.entry_sign_in)) and hasClickAction())
        action.performScrollTo().assertIsNotEnabled()

        composeRule.onNodeWithText(context.getString(R.string.entry_email))
            .performTextInput("someone@example.test")
        action.assertIsNotEnabled()

        composeRule.onNodeWithText(context.getString(R.string.entry_password))
            .performTextInput("a-password")
        action.assertIsEnabled()
    }

    @Test
    fun submittingReportsTheEnteredCredentialsOnce() {
        val submitted = mutableListOf<Pair<String, String>>()
        composeRule.setContent {
            SideBySideTheme {
                EntryScreen(onSignIn = { email, password -> submitted += email to password }, busy = false)
            }
        }

        composeRule.onNodeWithText(context.getString(R.string.entry_email))
            .performTextInput("someone@example.test")
        composeRule.onNodeWithText(context.getString(R.string.entry_password))
            .performTextInput("a-password")
        composeRule
            .onNode(hasText(context.getString(R.string.entry_sign_in)) and hasClickAction())
            .performScrollTo()
            .performClick()

        assertEquals(listOf("someone@example.test" to "a-password"), submitted)
    }

    @Test
    fun operatorNoticeIsAnnouncedAndBlocksSignIn() {
        composeRule.setContent {
            SideBySideTheme {
                EntryScreen(
                    onSignIn = { _, _ -> },
                    busy = false,
                    signInEnabled = false,
                    notice = context.getString(R.string.ref_not_configured),
                )
            }
        }

        composeRule.onNodeWithText(context.getString(R.string.ref_not_configured))
            .performScrollTo()
            .assertIsDisplayed()
        composeRule
            .onNode(hasText(context.getString(R.string.entry_sign_in)) and hasClickAction())
            .performScrollTo()
            .assertIsNotEnabled()
    }

    @Test
    fun entrySurfaceStaysOperableAtDoubleFontScale() {
        composeRule.setContent {
            CompositionLocalProvider(LocalDensity provides Density(density = 1f, fontScale = 2f)) {
                SideBySideTheme { EntryScreen(onSignIn = { _, _ -> }, busy = false) }
            }
        }

        composeRule.onNodeWithText(context.getString(R.string.entry_headline))
            .performScrollTo()
            .assertIsDisplayed()
        composeRule
            .onNode(hasText(context.getString(R.string.entry_sign_in)) and hasClickAction())
            .performScrollTo()
            .assertIsDisplayed()
    }
}
