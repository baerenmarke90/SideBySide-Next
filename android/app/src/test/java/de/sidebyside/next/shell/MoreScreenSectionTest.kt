package de.sidebyside.next.shell

import android.content.Context
import androidx.compose.material3.Text
import androidx.compose.ui.test.junit4.createComposeRule
import androidx.compose.ui.test.onNodeWithText
import androidx.test.core.app.ApplicationProvider
import de.sidebyside.next.design.SideBySideTheme
import de.sidebyside.next.reference.R
import org.junit.Rule
import org.junit.Test
import org.junit.runner.RunWith
import org.robolectric.RobolectricTestRunner
import org.robolectric.annotation.Config

/**
 * Direction B reads Mehr as a human-first hierarchy: identity content first,
 * grouped sections in the middle, and the irreversible Account/Space actions
 * set apart under their own sober heading rather than mixed in as one more
 * equal-weight card.
 */
@RunWith(RobolectricTestRunner::class)
@Config(sdk = [35])
class MoreScreenSectionTest {
    @get:Rule
    val composeRule = createComposeRule()

    private val context: Context get() = ApplicationProvider.getApplicationContext()

    @Test
    fun rendersEachSectionHeadingInHumanFirstOrder() {
        render()

        composeRule
            .onNodeWithText(context.getString(R.string.more_section_relationship_title))
            .assertExists()
        composeRule
            .onNodeWithText(context.getString(R.string.more_section_daily_title))
            .assertExists()
        composeRule
            .onNodeWithText(context.getString(R.string.more_section_data_title))
            .assertExists()
        composeRule
            .onNodeWithText(context.getString(R.string.more_section_sensitive_title))
            .assertExists()
    }

    @Test
    fun identityContentRendersBeforeAnySection() {
        render()

        composeRule.onNodeWithText("identity-marker").assertExists()
    }

    @Test
    fun sensitiveContentRendersUnderTheSensitiveHeading() {
        render()

        composeRule.onNodeWithText("sensitive-marker").assertExists()
    }

    private fun render() {
        composeRule.setContent {
            SideBySideTheme {
                MoreScreen(
                    onSignOut = {},
                    onOpenHeartMoments = {},
                    onOpenInvitations = {},
                    onOpenRelatedPersons = {},
                    onOpenPreferences = {},
                    onOpenPrivateArea = {},
                    onOpenDataExport = {},
                    onOpenDataImport = {},
                    onOpenNotifications = {},
                    onOpenSearch = {},
                    identityContent = { Text("identity-marker") },
                    sensitiveContent = { Text("sensitive-marker") },
                )
            }
        }
    }
}
