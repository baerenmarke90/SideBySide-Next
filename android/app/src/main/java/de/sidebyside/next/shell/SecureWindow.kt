package de.sidebyside.next.shell

import android.view.Window
import android.view.WindowManager
import androidx.activity.compose.LocalActivity
import androidx.compose.runtime.Composable
import androidx.compose.runtime.DisposableEffect
import androidx.compose.runtime.rememberUpdatedState
import androidx.navigation.NavController

/**
 * Applies the fail-closed launch/recreation default before Compose content is
 * installed and before Navigation restores a destination.
 */
internal fun secureWindowUntilNavigationIsKnown(window: Window) {
    window.setContentCaptureBlocked(true)
}

private fun Window.setContentCaptureBlocked(blocked: Boolean) {
    if (blocked) {
        setFlags(WindowManager.LayoutParams.FLAG_SECURE, WindowManager.LayoutParams.FLAG_SECURE)
    } else {
        clearFlags(WindowManager.LayoutParams.FLAG_SECURE)
    }
}

/**
 * #356/#683 owner-only policy enforcement, scoped to the current destination.
 *
 * `FLAG_SECURE` blocks screenshots and screen recording and, as a side
 * effect the platform does not offer independently, blanks the Recents
 * thumbnail for this window — the same one decision satisfies both halves
 * of the screenshot and Recents acceptance criterion. Navigation invokes its
 * destination listeners synchronously while committing a destination, before
 * Compose observes and renders that destination's content. The flag is thus
 * already correct when the new destination's content can enter a frame or
 * Recents preview.
 */
@Composable
internal fun SecureWindowNavigationEffect(
    navController: NavController,
    secureWhen: (route: String?) -> Boolean,
) {
    val activity = LocalActivity.current
    val currentSecureWhen = rememberUpdatedState(secureWhen)
    DisposableEffect(navController, activity) {
        val window = activity?.window
        val listener = NavController.OnDestinationChangedListener { _, destination, _ ->
            window?.setContentCaptureBlocked(currentSecureWhen.value(destination.route))
        }
        navController.addOnDestinationChangedListener(listener)
        onDispose {
            navController.removeOnDestinationChangedListener(listener)
            window?.clearFlags(WindowManager.LayoutParams.FLAG_SECURE)
        }
    }
}
