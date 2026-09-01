package de.sidebyside.next.shell

import android.app.Activity
import android.view.WindowManager
import androidx.activity.compose.LocalActivity
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.setValue
import androidx.compose.ui.test.junit4.createComposeRule
import org.junit.Assert.assertFalse
import org.junit.Assert.assertTrue
import org.junit.Rule
import org.junit.Test
import org.junit.runner.RunWith
import org.robolectric.RobolectricTestRunner
import org.robolectric.annotation.Config

/**
 * #356's screenshot/Recents decision, verified against the real platform
 * flag rather than only a route predicate: `FLAG_SECURE` blocks screenshots
 * and screen recording, and its well-known side effect is a blanked Recents
 * thumbnail — the one flag decides both halves of the acceptance criterion.
 */
@RunWith(RobolectricTestRunner::class)
@Config(sdk = [35])
class SecureWindowEffectTest {
    @get:Rule
    val composeRule = createComposeRule()

    @Test
    fun setsFlagSecureWhileSecureIsTrueAndClearsItWhenItTurnsFalse() {
        var secure by mutableStateOf(true)
        var activity: Activity? = null

        composeRule.setContent {
            activity = LocalActivity.current
            SecureWindowEffect(secure = secure)
        }
        composeRule.waitForIdle()
        assertTrue(isSecure(activity))

        secure = false
        composeRule.waitForIdle()
        assertFalse(isSecure(activity))
    }

    @Test
    fun clearsFlagSecureOnceTheEffectLeavesComposition() {
        var mounted by mutableStateOf(true)
        var activity: Activity? = null

        composeRule.setContent {
            activity = LocalActivity.current
            if (mounted) {
                SecureWindowEffect(secure = true)
            }
        }
        composeRule.waitForIdle()
        assertTrue(isSecure(activity))

        mounted = false
        composeRule.waitForIdle()
        assertFalse(isSecure(activity))
    }

    private fun isSecure(activity: Activity?): Boolean =
        (activity?.window?.attributes?.flags ?: 0) and WindowManager.LayoutParams.FLAG_SECURE != 0
}
