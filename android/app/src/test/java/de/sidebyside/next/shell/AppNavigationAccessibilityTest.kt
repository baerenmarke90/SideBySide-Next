package de.sidebyside.next.shell

import android.content.Context
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.size
import androidx.compose.material3.Text
import androidx.compose.runtime.CompositionLocalProvider
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.LocalDensity
import androidx.compose.ui.test.assertIsDisplayed
import androidx.compose.ui.test.assertIsSelected
import androidx.compose.ui.test.hasClickAction
import androidx.compose.ui.test.hasText
import androidx.compose.ui.test.junit4.createComposeRule
import androidx.compose.ui.test.onNode
import androidx.compose.ui.test.onNodeWithText
import androidx.compose.ui.test.performClick
import androidx.compose.ui.unit.Density
import androidx.compose.ui.unit.dp
import androidx.navigation.NavHostController
import androidx.navigation.compose.composable
import androidx.navigation.compose.rememberNavController
import androidx.test.core.app.ApplicationProvider
import de.sidebyside.next.design.SideBySideTheme
import org.junit.Assert.assertTrue
import org.junit.Rule
import org.junit.Test
import org.junit.runner.RunWith
import org.robolectric.RobolectricTestRunner
import org.robolectric.annotation.Config

/**
 * G4 accessibility coverage for the shared Android navigation contract.
 *
 * These tests deliberately exercise the real Navigation Compose host rather
 * than a hand-written fake back stack. Manual TalkBack, external-keyboard and
 * switch-control acceptance remains a release gate in ACCESSIBILITY-QA-MATRIX.
 */
@RunWith(RobolectricTestRunner::class)
@Config(sdk = [35])
class AppNavigationAccessibilityTest {
    @get:Rule
    val composeRule = createComposeRule()

    private val context: Context get() = ApplicationProvider.getApplicationContext()

    private fun label(destination: AppDestination): String =
        context.getString(destination.labelRes)

    @Test
    fun primaryNavigationRemainsReachableAtDoubleFontScale() {
        composeRule.setContent {
            CompositionLocalProvider(LocalDensity provides Density(density = 1f, fontScale = 2f)) {
                SideBySideTheme {
                    Box(Modifier.size(width = 320.dp, height = 640.dp)) {
                        AppNavigation(destinations = declaredDestinations) { destination ->
                            Text("screen:${destination.route}")
                        }
                    }
                }
            }
        }

        for (destination in declaredDestinations) {
            composeRule
                .onNode(hasText(label(destination)) and hasClickAction())
                .assertIsDisplayed()
        }

        composeRule
            .onNode(hasText(label(AppDestination.Today)) and hasClickAction())
            .assertIsSelected()
        composeRule
            .onNode(hasText(label(AppDestination.Story)) and hasClickAction())
            .performClick()

        composeRule.onNodeWithText("screen:story").assertIsDisplayed()
        composeRule
            .onNode(hasText(label(AppDestination.Story)) and hasClickAction())
            .assertIsSelected()
    }

    @Test
    fun detailRouteKeepsItsParentSelectedAndBackReturnsToTheParent() {
        lateinit var navController: NavHostController

        composeRule.setContent {
            SideBySideTheme {
                navController = rememberNavController()
                AppNavigation(
                    destinations = declaredDestinations,
                    navController = navController,
                    detailRoutes = {
                        composable("story/detail") { Text("story-detail") }
                    },
                ) { destination ->
                    Text("screen:${destination.route}")
                }
            }
        }

        composeRule
            .onNode(hasText(label(AppDestination.Story)) and hasClickAction())
            .performClick()
        composeRule.onNodeWithText("screen:story").assertIsDisplayed()

        composeRule.runOnIdle { navController.navigate("story/detail") }
        composeRule.onNodeWithText("story-detail").assertIsDisplayed()
        composeRule
            .onNode(hasText(label(AppDestination.Story)) and hasClickAction())
            .assertIsSelected()

        composeRule.runOnIdle { assertTrue(navController.popBackStack()) }

        composeRule.onNodeWithText("screen:story").assertIsDisplayed()
        composeRule
            .onNode(hasText(label(AppDestination.Story)) and hasClickAction())
            .assertIsSelected()
    }
}
