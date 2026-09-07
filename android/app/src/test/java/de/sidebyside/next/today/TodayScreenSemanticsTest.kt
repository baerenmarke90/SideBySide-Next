package de.sidebyside.next.today

import android.content.Context
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.setValue
import androidx.compose.ui.test.assertHeightIsAtLeast
import androidx.compose.ui.test.assertIsDisplayed
import androidx.compose.ui.test.assertWidthIsAtLeast
import androidx.compose.ui.test.junit4.createComposeRule
import androidx.compose.ui.test.onNodeWithContentDescription
import androidx.compose.ui.test.onNodeWithText
import androidx.compose.ui.test.performClick
import androidx.compose.ui.test.performScrollTo
import androidx.compose.ui.unit.dp
import androidx.test.core.app.ApplicationProvider
import de.sidebyside.next.design.SideBySideTheme
import de.sidebyside.next.reference.R
import java.time.LocalDate
import java.time.OffsetDateTime
import java.util.UUID
import org.junit.Assert.assertFalse
import org.junit.Assert.assertTrue
import org.junit.Rule
import org.junit.Test
import org.junit.runner.RunWith
import org.robolectric.RobolectricTestRunner
import org.robolectric.annotation.Config
import sidebyside.api.models.DashboardItem
import sidebyside.api.models.DashboardItemType
import sidebyside.api.models.DashboardPartner
import sidebyside.api.models.DashboardRelationshipDuration
import sidebyside.api.models.DashboardSpaceSummary
import sidebyside.api.models.DashboardView
import sidebyside.api.models.DurationDisplayMode

/**
 * Semantics and interaction tests for TodayScreen in Direction B (Living Sanctuary).
 */
@RunWith(RobolectricTestRunner::class)
@Config(sdk = [35])
class TodayScreenSemanticsTest {
    @get:Rule
    val composeRule = createComposeRule()

    private val context: Context get() = ApplicationProvider.getApplicationContext()

    @Test
    fun displaysCouplePresenceMastheadWithPartner() {
        val dashboard = sampleDashboard(partnerName = "Alex", daysTogether = 365)
        render(dashboard)

        composeRule.onNodeWithText("Du & Alex").assertIsDisplayed()
        composeRule.onNodeWithText("365 Tage zusammen").assertIsDisplayed()
        composeRule.onNodeWithContentDescription(
            context.getString(R.string.relationship_thinking_of_you_send, "Alex"),
        ).assertIsDisplayed()
    }

    @Test
    fun displaysCouplePresenceWhenWaitingForPartner() {
        val dashboard = sampleDashboard(partnerName = null, daysTogether = null)
        render(dashboard)

        composeRule.onNodeWithText("Du").assertIsDisplayed()
        composeRule.onNodeWithText(
            context.getString(R.string.relationship_presence_waiting),
        ).assertIsDisplayed()
    }

    @Test
    fun triggersThinkingOfYouOnClick() {
        var clicked = false
        val dashboard = sampleDashboard(partnerName = "Alex")
        composeRule.setContent {
            SideBySideTheme {
                TodayScreen(
                    dashboard = dashboard,
                    busy = false,
                    problem = null,
                    gestureSent = false,
                    onSendThinkingOfYou = { clicked = true },
                    onOpenActivity = {},
                )
            }
        }

        composeRule.onNodeWithContentDescription(
            context.getString(R.string.relationship_thinking_of_you_send, "Alex"),
        ).performClick()

        assertTrue("Expected onSendThinkingOfYou to be invoked", clicked)
    }

    @Test
    fun displaysElevatedRetrospectiveBelowMasthead() {
        val retroItem = DashboardItem(
            createdAt = OffsetDateTime.now(),
            id = UUID.randomUUID(),
            occurredOn = LocalDate.of(2025, 6, 15),
            scheduledAt = null,
            titleOrText = "Unforgettable summer evening by the lake",
            type = DashboardItemType.MEMORY,
        )
        val dashboard = sampleDashboard(partnerName = "Alex", retrospective = retroItem)
        render(dashboard)

        composeRule.onNodeWithText(context.getString(R.string.today_retrospective)).assertIsDisplayed()
        composeRule.onNodeWithText("Unforgettable summer evening by the lake").assertIsDisplayed()
    }

    @Test
    fun displaysUpcomingAndRecentSharedSections() {
        val upcomingItem = DashboardItem(
            createdAt = OffsetDateTime.now(),
            id = UUID.randomUUID(),
            occurredOn = null,
            scheduledAt = OffsetDateTime.now().plusDays(2),
            titleOrText = "Anniversary dinner reservation",
            type = DashboardItemType.ANNIVERSARY,
        )
        val recentItem = DashboardItem(
            createdAt = OffsetDateTime.now().minusDays(1),
            id = UUID.randomUUID(),
            occurredOn = LocalDate.now().minusDays(1),
            scheduledAt = null,
            titleOrText = "Sunday breakfast in bed",
            type = DashboardItemType.HEART_MOMENT,
        )
        val dashboard = sampleDashboard(
            partnerName = "Alex",
            upcoming = listOf(upcomingItem),
            recent = listOf(recentItem),
        )
        render(dashboard)

        composeRule.onNodeWithText("Anniversary dinner reservation").assertIsDisplayed()
        composeRule.onNodeWithText("Sunday breakfast in bed").performScrollTo().assertIsDisplayed()
    }

    @Test
    fun displaysCouplePresenceWithAuthenticatedUserName() {
        val dashboard = sampleDashboard(partnerName = "Alex")
        composeRule.setContent {
            SideBySideTheme {
                TodayScreen(
                    dashboard = dashboard,
                    busy = false,
                    problem = null,
                    gestureSent = false,
                    onSendThinkingOfYou = {},
                    onOpenActivity = {},
                    userName = "Philipp",
                )
            }
        }

        composeRule.onNodeWithContentDescription(
            context.getString(R.string.relationship_partner_pair_connected, "Philipp", "Alex"),
        ).assertIsDisplayed()
    }

    @Test
    fun fallsBackToDefaultUserLabelWhenUserNameIsNull() {
        val dashboard = sampleDashboard(partnerName = "Alex")
        composeRule.setContent {
            SideBySideTheme {
                TodayScreen(
                    dashboard = dashboard,
                    busy = false,
                    problem = null,
                    gestureSent = false,
                    onSendThinkingOfYou = {},
                    onOpenActivity = {},
                    userName = null,
                )
            }
        }

        composeRule.onNodeWithContentDescription(
            context.getString(
                R.string.relationship_partner_pair_connected,
                context.getString(R.string.activity_you),
                "Alex",
            ),
        ).assertIsDisplayed()
    }

    @Test
    fun thinkingOfYouSentStateResetsAfterConfirmationInterval() {
        var acknowledged = false
        val dashboard = sampleDashboard(partnerName = "Alex")
        composeRule.mainClock.autoAdvance = false
        composeRule.setContent {
            SideBySideTheme {
                TodayScreen(
                    dashboard = dashboard,
                    busy = false,
                    problem = null,
                    gestureSent = true,
                    onSendThinkingOfYou = {},
                    onOpenActivity = {},
                    onAcknowledgeThinkingOfYou = { acknowledged = true },
                )
            }
        }

        assertFalse("Should not acknowledge immediately", acknowledged)
        composeRule.mainClock.advanceTimeBy(2600L)
        assertTrue("Should acknowledge after confirmation interval", acknowledged)
    }

    @Test
    fun thinkingOfYouAcknowledgesOnDisposeForNavigation() {
        var acknowledged = false
        val dashboard = sampleDashboard(partnerName = "Alex")
        var isScreenActive by mutableStateOf(true)

        composeRule.setContent {
            SideBySideTheme {
                if (isScreenActive) {
                    TodayScreen(
                        dashboard = dashboard,
                        busy = false,
                        problem = null,
                        gestureSent = true,
                        onSendThinkingOfYou = {},
                        onOpenActivity = {},
                        onAcknowledgeThinkingOfYou = { acknowledged = true },
                    )
                }
            }
        }

        assertFalse("Should not acknowledge prior to dispose", acknowledged)
        isScreenActive = false
        composeRule.waitForIdle()
        assertTrue("Should acknowledge on dispose when leaving screen", acknowledged)
    }

    @Test
    fun compactMastheadAdaptsThinkingOfYouForNarrowWidth() {
        val dashboard = sampleDashboard(partnerName = "Alex")
        composeRule.setContent {
            SideBySideTheme {
                TodayScreen(
                    dashboard = dashboard,
                    busy = false,
                    problem = null,
                    gestureSent = false,
                    onSendThinkingOfYou = {},
                    onOpenActivity = {},
                    isCompact = true,
                )
            }
        }

        // Accessibility content description remains present and touch target meets >=48dp
        composeRule.onNodeWithContentDescription(
            context.getString(R.string.relationship_thinking_of_you_send, "Alex"),
        ).assertIsDisplayed()
            .assertWidthIsAtLeast(48.dp)
            .assertHeightIsAtLeast(48.dp)

        // In compact mode, the textual label is omitted from UI to give space to couple presence
        composeRule.onNodeWithText(
            context.getString(R.string.relationship_thinking_of_you_default),
        ).assertDoesNotExist()
    }

    @Test
    fun expandedMastheadDisplaysFullThinkingOfYouLabel() {
        val dashboard = sampleDashboard(partnerName = "Alex")
        composeRule.setContent {
            SideBySideTheme {
                TodayScreen(
                    dashboard = dashboard,
                    busy = false,
                    problem = null,
                    gestureSent = false,
                    onSendThinkingOfYou = {},
                    onOpenActivity = {},
                    isCompact = false,
                )
            }
        }

        composeRule.onNodeWithText(
            context.getString(R.string.relationship_thinking_of_you_default),
        ).assertIsDisplayed()
    }

    private fun render(dashboard: DashboardView) {
        composeRule.setContent {
            SideBySideTheme {
                TodayScreen(
                    dashboard = dashboard,
                    busy = false,
                    problem = null,
                    gestureSent = false,
                    onSendThinkingOfYou = {},
                    onOpenActivity = {},
                )
            }
        }
    }

    private fun sampleDashboard(
        partnerName: String?,
        daysTogether: Int? = 100,
        retrospective: DashboardItem? = null,
        upcoming: List<DashboardItem> = emptyList(),
        recent: List<DashboardItem> = emptyList(),
    ): DashboardView {
        val partner = partnerName?.let {
            DashboardPartner(displayName = it, id = UUID.randomUUID())
        }
        val duration = daysTogether?.let {
            DashboardRelationshipDuration(
                daysTogether = it,
                displayMode = DurationDisplayMode.DAYS,
                startedOn = LocalDate.now().minusDays(it.toLong()),
            )
        }
        return DashboardView(
            keepsake = null,
            recentShared = recent,
            relationshipDuration = duration,
            retrospective = retrospective,
            space = DashboardSpaceSummary(partner = partner, spaceId = UUID.randomUUID()),
            upcoming = upcoming,
        )
    }
}
