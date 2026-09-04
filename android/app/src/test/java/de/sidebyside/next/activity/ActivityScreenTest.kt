package de.sidebyside.next.activity

import android.content.Context
import androidx.compose.ui.test.assertIsNotEnabled
import androidx.compose.ui.test.junit4.createComposeRule
import androidx.compose.ui.test.onNodeWithText
import androidx.compose.ui.test.performClick
import androidx.compose.ui.test.performScrollTo
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
 * The load-more affordance (#608): #357 shipped the Activity feed capped at
 * one server page with no way to reach older entries.
 */
@RunWith(RobolectricTestRunner::class)
@Config(sdk = [35], qualifiers = "w320dp-h1200dp")
class ActivityScreenTest {
    @get:Rule
    val composeRule = createComposeRule()

    private val context: Context get() = ApplicationProvider.getApplicationContext()

    @Test
    fun loadMoreIsAbsentWithoutACallback() {
        render(onLoadMore = null)

        composeRule.onNodeWithText(context.getString(R.string.load_more)).assertDoesNotExist()
    }

    @Test
    fun loadMoreInvokesTheCallback() {
        var calls = 0
        render(onLoadMore = { calls++ })

        composeRule.onNodeWithText(context.getString(R.string.load_more))
            .performScrollTo()
            .performClick()

        assertEquals(1, calls)
    }

    @Test
    fun loadMoreIsDisabledWhileLoadingMore() {
        render(onLoadMore = {}, loadingMore = true)

        composeRule.onNodeWithText(context.getString(R.string.load_more_busy))
            .performScrollTo()
            .assertIsNotEnabled()
    }

    @Test
    fun ownActivityRendersDuSentence() {
        val myId = java.util.UUID.randomUUID()
        val item = sidebyside.api.models.ActivityItem(
            id = java.util.UUID.randomUUID(),
            sourceEventId = java.util.UUID.randomUUID(),
            kind = sidebyside.api.models.ActivityKind.PLAN_CREATED,
            actorId = myId,
            actor = sidebyside.api.models.AuthorSummary(
                id = myId,
                displayName = "Philipp",
                profileAttachmentId = null,
            ),
            targetType = sidebyside.api.models.EngagementTarget.PLAN,
            targetId = java.util.UUID.randomUUID(),
            target = sidebyside.api.models.ActivityTargetPresentation(
                targetType = sidebyside.api.models.EngagementTarget.PLAN,
                targetId = java.util.UUID.randomUUID(),
                title = "Urlaub",
            ),
            occurredAt = java.time.OffsetDateTime.now(),
            createdAt = java.time.OffsetDateTime.now(),
        )

        composeRule.setContent {
            SideBySideTheme {
                ActivityScreen(
                    entries = listOf(item),
                    busy = false,
                    problem = null,
                    onBack = {},
                    onOpen = {},
                    currentAccountId = myId,
                )
            }
        }

        val expected = context.getString(R.string.activity_action_own_plan_created, "Urlaub")
        composeRule.onNodeWithText(expected).assertExists()
    }

    @Test
    fun partnerActivityRendersPartnerNameSentence() {
        val myId = java.util.UUID.randomUUID()
        val partnerId = java.util.UUID.randomUUID()
        val item = sidebyside.api.models.ActivityItem(
            id = java.util.UUID.randomUUID(),
            sourceEventId = java.util.UUID.randomUUID(),
            kind = sidebyside.api.models.ActivityKind.PLACE_CREATED,
            actorId = partnerId,
            actor = sidebyside.api.models.AuthorSummary(
                id = partnerId,
                displayName = "Ben",
                profileAttachmentId = null,
            ),
            targetType = sidebyside.api.models.EngagementTarget.PLACE,
            targetId = java.util.UUID.randomUUID(),
            target = sidebyside.api.models.ActivityTargetPresentation(
                targetType = sidebyside.api.models.EngagementTarget.PLACE,
                targetId = java.util.UUID.randomUUID(),
                title = "Lieblingscafé",
            ),
            occurredAt = java.time.OffsetDateTime.now(),
            createdAt = java.time.OffsetDateTime.now(),
        )

        composeRule.setContent {
            SideBySideTheme {
                ActivityScreen(
                    entries = listOf(item),
                    busy = false,
                    problem = null,
                    onBack = {},
                    onOpen = {},
                    currentAccountId = myId,
                )
            }
        }

        val expected = context.getString(R.string.activity_action_place_created, "Ben", "Lieblingscafé")
        composeRule.onNodeWithText(expected).assertExists()
    }

    private fun render(onLoadMore: (() -> Unit)?, loadingMore: Boolean = false) {
        composeRule.setContent {
            SideBySideTheme {
                ActivityScreen(
                    entries = emptyList(),
                    busy = false,
                    problem = null,
                    onBack = {},
                    onOpen = {},
                    onLoadMore = onLoadMore,
                    loadingMore = loadingMore,
                )
            }
        }
    }
}
