package de.sidebyside.next.design

import android.content.Context
import androidx.compose.ui.test.assertHeightIsAtLeast
import androidx.compose.ui.test.assertIsDisplayed
import androidx.compose.ui.test.assertWidthIsAtLeast
import androidx.compose.ui.test.junit4.createComposeRule
import androidx.compose.ui.test.onNodeWithContentDescription
import androidx.compose.ui.test.onNodeWithText
import androidx.compose.ui.unit.dp
import androidx.test.core.app.ApplicationProvider
import de.sidebyside.next.reference.R
import org.junit.Rule
import org.junit.Test
import org.junit.runner.RunWith
import org.robolectric.RobolectricTestRunner
import org.robolectric.annotation.Config

/**
 * Semantics and hit-target tests for relationship components in Direction B.
 */
@RunWith(RobolectricTestRunner::class)
@Config(sdk = [35])
class RelationshipComponentsSemanticsTest {
    @get:Rule
    val composeRule = createComposeRule()

    private val context: Context get() = ApplicationProvider.getApplicationContext()

    @Test
    fun thinkingOfYouButtonReflectsDynamicSemantics() {
        composeRule.setContent {
            SideBySideTheme {
                ThinkingOfYouButton(
                    partnerName = "Lea",
                    externalState = ThinkingOfYouState.SENDING,
                )
            }
        }

        composeRule.onNodeWithContentDescription(
            context.getString(R.string.relationship_thinking_of_you_sending),
        ).assertIsDisplayed()
            .assertWidthIsAtLeast(48.dp)
            .assertHeightIsAtLeast(48.dp)
    }

    @Test
    fun thinkingOfYouButtonSentState() {
        composeRule.setContent {
            SideBySideTheme {
                ThinkingOfYouButton(
                    partnerName = "Lea",
                    externalState = ThinkingOfYouState.SENT,
                )
            }
        }

        composeRule.onNodeWithContentDescription(
            context.getString(R.string.relationship_thinking_of_you_sent),
        ).assertIsDisplayed()
            .assertWidthIsAtLeast(48.dp)
            .assertHeightIsAtLeast(48.dp)
    }

    @Test
    fun couplePresenceDurationHasMinimumTouchTarget() {
        composeRule.setContent {
            SideBySideTheme {
                CouplePresence(
                    spaceName = "Wir & Lea",
                    userName = "Alex",
                    partnerName = "Lea",
                    relationshipDuration = "2 Jahre zusammen",
                    onDurationClick = {},
                    unboxed = true,
                )
            }
        }

        composeRule.onNodeWithText("2 Jahre zusammen")
            .assertIsDisplayed()
            .assertHeightIsAtLeast(48.dp)
    }

    @Test
    fun partnerAvatarPairInviteHasMinimumTouchTarget() {
        composeRule.setContent {
            SideBySideTheme {
                PartnerAvatarPair(
                    userName = "Alex",
                    partnerName = null,
                    onInviteClick = {},
                )
            }
        }

        composeRule.onNodeWithContentDescription(
            context.getString(R.string.relationship_partner_pair_invite),
        ).assertIsDisplayed()
            .assertWidthIsAtLeast(48.dp)
            .assertHeightIsAtLeast(48.dp)
    }
}
