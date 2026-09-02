package de.sidebyside.next.shell

import android.view.WindowManager
import androidx.activity.compose.LocalActivity
import androidx.compose.runtime.Composable
import androidx.compose.runtime.DisposableEffect

/**
 * #356's decision for owner-only surfaces: `FLAG_SECURE`, scoped to exactly
 * as long as [secure] is true, rather than applied to the whole app.
 *
 * `FLAG_SECURE` blocks screenshots and screen recording and, as a side
 * effect the platform does not offer independently, blanks the Recents
 * thumbnail for this window — the same one decision satisfies both halves
 * of #356's "screenshot and recents behaviour" acceptance criterion. Scoping
 * it to the route rather than the app means ordinary shared content, where a
 * couple may well want to screenshot or share their screen, is never
 * degraded by it.
 */
@Composable
fun SecureWindowEffect(secure: Boolean) {
    val activity = LocalActivity.current
    DisposableEffect(secure, activity) {
        val window = activity?.window
        if (secure) {
            window?.setFlags(WindowManager.LayoutParams.FLAG_SECURE, WindowManager.LayoutParams.FLAG_SECURE)
        } else {
            window?.clearFlags(WindowManager.LayoutParams.FLAG_SECURE)
        }
        onDispose {
            window?.clearFlags(WindowManager.LayoutParams.FLAG_SECURE)
        }
    }
}
