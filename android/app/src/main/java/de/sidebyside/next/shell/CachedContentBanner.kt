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
 * The M2-D18 "this is a stale cache fallback, not a fresh read" indicator.
 * Reuses [UiStatePanel]'s existing `Offline` presentation rather than a new
 * banner style, so a couple sees the same visual language for "the network
 * failed" whether or not a cached answer happened to be available.
 *
 * Renders nothing when [cachedAt] is `null` — the ordinary case, a fresh
 * network read.
 */
@Composable
fun CachedContentBanner(cachedAt: Instant?, modifier: Modifier = Modifier) {
    if (cachedAt == null) return

    val locale = LocalConfiguration.current.locales[0]
    val formatter = DateTimeFormatter.ofLocalizedDateTime(FormatStyle.SHORT).withLocale(locale)
    val formatted = formatter.format(cachedAt.atZone(ZoneId.systemDefault()))

    UiStatePanel(
        kind = UiStateKind.Offline,
        title = stringResource(R.string.cache_banner_title),
        body = stringResource(R.string.cache_banner_body, formatted),
        modifier = modifier,
    )
}
