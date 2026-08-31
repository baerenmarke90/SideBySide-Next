package de.sidebyside.next.shell

import android.content.Context
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.size
import androidx.compose.material3.Text
import androidx.compose.ui.Modifier
import androidx.compose.ui.test.assertIsDisplayed
import androidx.compose.ui.test.assertIsSelected
import androidx.compose.ui.test.hasClickAction
import androidx.compose.ui.test.hasText
import androidx.compose.ui.test.junit4.createComposeRule
import androidx.compose.ui.test.onNodeWithText
import androidx.compose.ui.test.performClick
import androidx.compose.ui.unit.dp
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
class AppShellSemanticsTest {
    @get:Rule
    val composeRule = createComposeRule()

    private val context: Context get() = ApplicationProvider.getApplicationContext()

    private fun label(destination: AppDestination): String =
        context.getString(destination.labelRes)

    @Test
    fun namesEveryDestinationItRenders() {
        composeRule.setContent {
            SideBySideTheme {
                AppShell(
                    widthClass = WindowWidthClass.Compact,
                    destinations = declaredDestinations,
                    currentDestination = AppDestination.Today,
                    onSelectDestination = {},
                ) { Text("content") }
            }
        }

        for (destination in declaredDestinations) {
            composeRule.onNodeWithText(label(destination)).assertIsDisplayed()
        }
        composeRule.onNodeWithText("content").assertIsDisplayed()
    }

    @Test
    fun marksTheCurrentDestinationAsSelected() {
        composeRule.setContent {
            SideBySideTheme {
                AppShell(
                    widthClass = WindowWidthClass.Compact,
                    destinations = declaredDestinations,
                    currentDestination = AppDestination.Plan,
                    onSelectDestination = {},
                ) { Text("content") }
            }
        }

        composeRule
            .onNode(hasText(label(AppDestination.Plan)) and hasClickAction())
            .assertIsSelected()
    }

    @Test
    fun reportsTheChosenDestination() {
        val chosen = mutableListOf<AppDestination>()
        composeRule.setContent {
            SideBySideTheme {
                AppShell(
                    widthClass = WindowWidthClass.Compact,
                    destinations = declaredDestinations,
                    currentDestination = AppDestination.Today,
                    onSelectDestination = { chosen += it },
                ) { Text("content") }
            }
        }

        composeRule
            .onNode(hasText(label(AppDestination.Story)) and hasClickAction())
            .performClick()

        assertEquals(listOf(AppDestination.Story), chosen)
    }

    @Test
    fun drawsNoNavigationSurfaceForASingleDestination() {
        // One destination is not a choice, and an area still being built must
        // not appear as an empty tab.
        composeRule.setContent {
            SideBySideTheme {
                AppShell(
                    widthClass = WindowWidthClass.Compact,
                    destinations = listOf(AppDestination.Story),
                    currentDestination = AppDestination.Story,
                    onSelectDestination = {},
                ) { Text("content") }
            }
        }

        composeRule.onNodeWithText("content").assertIsDisplayed()
        composeRule
            .onAllNodesWithTextSafely(label(AppDestination.Story))
            .let { count -> assertEquals(0, count) }
    }

    @Test
    fun rendersTheSameNavigationInTheExpandedLayout() {
        // ADR 0004: the App keeps bottom navigation at every size, so a wider
        // window changes the content composition but never the surface.
        composeRule.setContent {
            SideBySideTheme {
                AppShell(
                    widthClass = WindowWidthClass.Expanded,
                    destinations = declaredDestinations,
                    currentDestination = AppDestination.More,
                    onSelectDestination = {},
                ) { Text("content") }
            }
        }

        for (destination in declaredDestinations) {
            composeRule.onNodeWithText(label(destination)).assertIsDisplayed()
        }
        composeRule
            .onNode(hasText(label(AppDestination.More)) and hasClickAction())
            .assertIsSelected()
    }

    @Test
    fun rendersTheSameNavigationInTheMediumLayout() {
        composeRule.setContent {
            SideBySideTheme {
                AppShell(
                    widthClass = WindowWidthClass.Medium,
                    destinations = declaredDestinations,
                    currentDestination = AppDestination.Today,
                    onSelectDestination = {},
                ) { Box(Modifier.size(1.dp)) { Text("content") } }
            }
        }

        for (destination in declaredDestinations) {
            composeRule.onNodeWithText(label(destination)).assertIsDisplayed()
        }
    }

    @Test
    fun announcesEveryStatePanelAndOffersRetryOnlyWhenUseful() {
        composeRule.setContent {
            SideBySideTheme {
                UiProblemPanel(
                    problem = problemFor(java.io.IOException()),
                    onRetry = {},
                )
            }
        }

        composeRule
            .onNodeWithText(context.getString(R.string.state_offline_title))
            .assertIsDisplayed()
        composeRule
            .onNode(hasText(context.getString(R.string.state_retry)) and hasClickAction())
            .assertIsDisplayed()
    }

    @Test
    fun hidesRetryWhereRetryingRepeatsTheSameAnswer() {
        composeRule.setContent {
            SideBySideTheme {
                UiProblemPanel(
                    problem = problemFor(
                        de.sidebyside.next.reference.ReferenceApiException(
                            code = null,
                            message = "forbidden",
                            status = 403,
                        ),
                    ),
                    onRetry = {},
                )
            }
        }

        composeRule
            .onNodeWithText(context.getString(R.string.state_permission_title))
            .assertIsDisplayed()
        assertEquals(
            0,
            composeRule.onAllNodesWithTextSafely(context.getString(R.string.state_retry)),
        )
    }
}

/** Counts matches without failing when there are none. */
private fun androidx.compose.ui.test.junit4.ComposeContentTestRule.onAllNodesWithTextSafely(
    text: String,
): Int = onAllNodes(hasText(text)).fetchSemanticsNodes().size
