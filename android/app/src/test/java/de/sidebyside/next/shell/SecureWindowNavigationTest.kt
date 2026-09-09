package de.sidebyside.next.shell

import android.app.Activity
import android.view.WindowManager
import androidx.activity.compose.LocalActivity
import androidx.compose.material3.Text
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableIntStateOf
import androidx.compose.runtime.setValue
import androidx.compose.ui.test.junit4.createComposeRule
import androidx.navigation.NavHostController
import androidx.navigation.compose.composable
import androidx.navigation.compose.rememberNavController
import org.junit.Assert.assertFalse
import org.junit.Assert.assertTrue
import org.junit.Rule
import org.junit.Test
import org.junit.runner.RunWith
import org.robolectric.RobolectricTestRunner
import org.robolectric.annotation.Config

/** Platform-level `FLAG_SECURE` timing and navigation coverage for #683. */
@RunWith(RobolectricTestRunner::class)
@Config(sdk = [35])
class SecureWindowNavigationTest {
    @get:Rule
    val composeRule = createComposeRule()

    @Test
    fun launchAndActivityRecreationDefaultIsSecureBeforeNavigationIsKnown() {
        var activity: Activity? = null

        composeRule.setContent {
            activity = LocalActivity.current
            Text("launch")
        }
        composeRule.waitForIdle()

        composeRule.runOnIdle {
            activity?.window?.clearFlags(WindowManager.LayoutParams.FLAG_SECURE)
            secureWindowUntilNavigationIsKnown(requireNotNull(activity).window)
            assertTrue(isSecure(activity))
        }
    }

    @Test
    fun destinationChangesSetSecuritySynchronouslyBeforeDestinationComposition() {
        lateinit var navController: NavHostController
        var activity: Activity? = null
        var secureContentComposedWithFlag = false

        composeRule.setContent {
            activity = LocalActivity.current
            navController = rememberNavController()
            AppNavigation(
                destinations = listOf(AppDestination.Today),
                navController = navController,
                secureWhen = { route -> route == SECURE_ROUTE },
                detailRoutes = {
                    composable(SECURE_ROUTE) {
                        secureContentComposedWithFlag = isSecure(activity)
                        Text("secure-content")
                    }
                    composable(SHARED_ROUTE) {
                        Text("shared-content")
                    }
                },
            ) { Text("shared-start") }
        }
        composeRule.waitForIdle()
        assertFalse(isSecure(activity))

        composeRule.runOnIdle {
            navController.navigate(SECURE_ROUTE)
            assertTrue("The flag must be set inside navigate(), before recomposition", isSecure(activity))
        }
        composeRule.waitForIdle()
        assertTrue(secureContentComposedWithFlag)

        composeRule.runOnIdle {
            navController.navigate(SHARED_ROUTE)
            assertTrue(
                "The outgoing private composition must remain protected until shared content commits",
                isSecure(activity),
            )
        }
        composeRule.waitForIdle()
        assertFalse("Shared content must not retain the prior secure state", isSecure(activity))

        composeRule.runOnIdle {
            assertTrue(navController.popBackStack())
            assertTrue("Back must restore the secure destinations flag synchronously", isSecure(activity))
        }
    }

    @Test
    fun fastNavigationAndUnrelatedRecompositionCannotLeaveAStaleFlag() {
        lateinit var navController: NavHostController
        var activity: Activity? = null
        var recompositionTrigger by mutableIntStateOf(0)

        composeRule.setContent {
            activity = LocalActivity.current
            navController = rememberNavController()
            AppNavigation(
                destinations = listOf(AppDestination.Today),
                navController = navController,
                secureWhen = { route -> route == SECURE_ROUTE },
                detailRoutes = {
                    composable(SECURE_ROUTE) { Text("secure-$recompositionTrigger") }
                    composable(SHARED_ROUTE) { Text("shared-$recompositionTrigger") }
                },
            ) { Text("start-$recompositionTrigger") }
        }
        composeRule.waitForIdle()

        composeRule.runOnIdle {
            navController.navigate(SECURE_ROUTE)
            assertTrue(isSecure(activity))
            navController.navigate(SHARED_ROUTE)
            assertTrue(isSecure(activity))
        }
        composeRule.waitForIdle()
        assertFalse(isSecure(activity))

        composeRule.runOnIdle {
            assertTrue(navController.popBackStack())
            assertTrue(isSecure(activity))
            recompositionTrigger += 1
        }
        composeRule.waitForIdle()
        assertTrue(isSecure(activity))

        composeRule.runOnIdle {
            assertTrue(navController.popBackStack())
            assertTrue(isSecure(activity))
        }
        composeRule.waitForIdle()
        assertFalse(isSecure(activity))
    }

    private fun isSecure(activity: Activity?): Boolean =
        (activity?.window?.attributes?.flags ?: 0) and WindowManager.LayoutParams.FLAG_SECURE != 0

    private companion object {
        const val SECURE_ROUTE = "private/detail"
        const val SHARED_ROUTE = "shared/detail"
    }
}
