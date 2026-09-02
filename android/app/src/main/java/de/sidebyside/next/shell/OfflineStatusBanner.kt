package de.sidebyside.next.shell

import androidx.compose.runtime.Composable
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.LocalConfiguration
import androidx.compose.ui.res.stringResource
import de.sidebyside.next.reference.R
import java.time.Instant
import java.time.ZoneId
import java.time.format.DateTimeFormatter
import java.time.format.FormatStyle

/**
 * The M2-D18 "one coherent application-level connectivity state" — shown
 * once, above whichever destination is open, rather than as a dialog per
 * failed request. Renders nothing while online, which is the ordinary case.
 *
 * Deliberately not [CachedContentBanner]: that one says "this screen's
 * content is a stale cache fallback," which is only true for screens that
 * have cached content to fall back to. This one says "the app itself cannot
 * currently reach the server," which is true regardless of what the current
 * screen happens to show.
 */
@Composable
fun OfflineStatusBanner(offline: Boolean, lastSyncedAt: Instant?, modifier: Modifier = Modifier) {
    if (!offline) return

    val body = lastSyncedAt?.let {
        val locale = LocalConfiguration.current.locales[0]
        val formatter = DateTimeFormatter.ofLocalizedDateTime(FormatStyle.SHORT).withLocale(locale)
        stringResource(R.string.offline_banner_last_synced, formatter.format(it.atZone(ZoneId.systemDefault())))
    } ?: stringResource(R.string.state_offline_body)

    UiStatePanel(
        kind = UiStateKind.Offline,
        title = stringResource(R.string.state_offline_title),
        body = body,
        modifier = modifier,
    )
}
