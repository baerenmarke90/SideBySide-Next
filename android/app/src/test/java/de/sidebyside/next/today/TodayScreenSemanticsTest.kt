package de.sidebyside.next.today

import android.content.Context
import androidx.compose.ui.test.assertIsDisplayed
import androidx.compose.ui.test.junit4.createComposeRule
import androidx.compose.ui.test.onNodeWithContentDescription
import androidx.compose.ui.test.onNodeWithText
import androidx.compose.ui.test.performClick
import androidx.compose.ui.test.performScrollTo
import androidx.test.core.app.ApplicationProvider
import de.sidebyside.next.design.SideBySideTheme
import de.sidebyside.next.reference.R
import java.time.LocalDate
import java.time.OffsetDateTime
import java.util.UUID
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

        composeRule.onNodeWithText("Wir & Alex").assertIsDisplayed()
        composeRule.onNodeWithText("365 Tage zusammen").assertIsDisplayed()
        composeRule.onNodeWithContentDescription(
            context.getString(R.string.relationship_thinking_of_you_send, "Alex"),
        ).assertIsDisplayed()
    }

    @Test
    fun displaysCouplePresenceWhenWaitingForPartner() {
        val dashboard = sampleDashboard(partnerName = null, daysTogether = null)
        render(dashboard)

        composeRule.onNodeWithText("Wir").assertIsDisplayed()
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
            recentShared = recent,
            relationshipDuration = duration,
            retrospective = retrospective,
            space = DashboardSpaceSummary(partner = partner, spaceId = UUID.randomUUID()),
            upcoming = upcoming,
        )
    }
}
