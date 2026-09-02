package de.sidebyside.next.story

import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.aspectRatio
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.widthIn
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Surface
import androidx.compose.material3.TextButton
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.LocalConfiguration
import androidx.compose.ui.res.stringResource
import androidx.compose.ui.semantics.heading
import androidx.compose.ui.semantics.semantics
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.unit.Dp
import androidx.compose.ui.unit.dp
import de.sidebyside.next.design.SideBySideTheme
import de.sidebyside.next.reference.R
import java.time.LocalDate
import java.util.UUID
import java.time.format.DateTimeFormatter
import java.time.format.FormatStyle
import java.util.Locale
import sidebyside.api.models.StoryItem

/** Keeps a long title readable rather than letting it run the window's width. */
private val ReadingMeasure: Dp = 560.dp

/**
 * The shared history.
 *
 * Entries are grouped under the day they belong to, in the order the server
 * gave them. Memories, Milestones and HeartMoments sit in one stream because
 * that is how a couple lived them; the kind is named on the entry rather than
 * splitting the history into three lists.
 */
@Composable
fun StoryScreen(
    items: List<StoryItem>,
    imageStore: StoryImageStore,
    generation: Long,
    modifier: Modifier = Modifier,
    /** Opens one entry. Every kind now has a screen of its own. */
    onOpenMemory: ((UUID) -> Unit)? = null,
    onOpenMilestone: ((UUID) -> Unit)? = null,
    onOpenHeartMoment: ((UUID) -> Unit)? = null,
    /** Null where there is no more Story to load. */
    onLoadMore: (() -> Unit)? = null,
    loadingMore: Boolean = false,
    /** Non-null only while [items] is a stale M2-D18 cache fallback. */
    cachedAt: java.time.Instant? = null,
    header: (@Composable () -> Unit)? = null,
) {
    val days = items.toStoryDays()

    LazyColumn(
        modifier = modifier.fillMaxWidth(),
        contentPadding = androidx.compose.foundation.layout.PaddingValues(
            SideBySideTheme.spacing.pageMargin,
        ),
        verticalArrangement = Arrangement.spacedBy(SideBySideTheme.spacing.step6),
    ) {
        header?.let { item(key = "header") { it() } }

        cachedAt?.let { item(key = "cached-banner") { de.sidebyside.next.shell.CachedContentBanner(it) } }

        if (days.isEmpty()) {
            item(key = "empty") { StoryEmpty() }
        }

        for (day in days) {
            item(key = "day-${day.date}") { DayHeading(day.date) }
            items(
                count = day.entries.size,
                key = { index -> day.entries[index].id.toString() },
            ) { index ->
                val entry = day.entries[index]
                StoryEntryCard(
                    entry = entry,
                    imageStore = imageStore,
                    generation = generation,
                    onOpen = when (entry.kind) {
                        StoryEntryKind.MEMORY -> onOpenMemory
                        StoryEntryKind.MILESTONE -> onOpenMilestone
                        StoryEntryKind.HEART_MOMENT -> onOpenHeartMoment
                    }?.let { open -> { open(entry.id) } },
                )
            }
        }

        // A Story that simply stopped after one page would lose history with
        // nothing on screen to say so.
        onLoadMore?.let { more ->
            item(key = "load-more") {
                TextButton(onClick = more, enabled = !loadingMore) {
                    Text(
                        stringResource(
                            if (loadingMore) R.string.load_more_busy else R.string.load_more,
                        ),
                    )
                }
            }
        }
    }
}

@Composable
private fun DayHeading(date: LocalDate) {
    // Read from the composition rather than from the process: the date has to
    // be rewritten when the device language changes, not at next launch.
    val locale: Locale = LocalConfiguration.current.locales[0]
    Text(
        text = date.format(
            DateTimeFormatter.ofLocalizedDate(FormatStyle.LONG).withLocale(locale),
        ),
        style = MaterialTheme.typography.titleSmall,
        color = SideBySideTheme.colors.brandStrong,
        modifier = Modifier.semantics { heading() },
    )
}

@Composable
private fun StoryEntryCard(
    entry: StoryEntry,
    imageStore: StoryImageStore,
    generation: Long,
    onOpen: (() -> Unit)? = null,
) {
    Surface(
        shape = RoundedCornerShape(SideBySideTheme.radii.card),
        color = SideBySideTheme.colors.surface,
        modifier = Modifier
            .fillMaxWidth()
            .then(if (onOpen != null) Modifier.clickable(onClick = onOpen) else Modifier),
    ) {
        Column(
            modifier = Modifier.padding(SideBySideTheme.spacing.cardPadding),
            verticalArrangement = Arrangement.spacedBy(SideBySideTheme.spacing.step3),
        ) {
            Text(
                text = stringResource(entry.kind.labelRes()),
                style = MaterialTheme.typography.labelSmall,
                color = entry.kind.accent(),
            )
            Text(
                text = entry.text,
                style = MaterialTheme.typography.titleMedium,
                color = SideBySideTheme.colors.textPrimary,
                // A long title wraps rather than being cut: the words are the
                // record, and truncation would hide part of it for good.
                modifier = Modifier.widthIn(max = ReadingMeasure),
            )
            Text(
                text = stringResource(R.string.story_by_author, entry.authorName),
                style = MaterialTheme.typography.bodySmall,
                color = SideBySideTheme.colors.textSecondary,
                maxLines = 1,
                overflow = TextOverflow.Ellipsis,
            )

            if (entry.images.isNotEmpty()) {
                Row(
                    horizontalArrangement = Arrangement.spacedBy(
                        SideBySideTheme.spacing.step2,
                    ),
                    modifier = Modifier.fillMaxWidth(),
                ) {
                    for (image in entry.images.take(MAX_IMAGES_PER_ENTRY)) {
                        StoryImage(
                            image = image,
                            store = imageStore,
                            generation = generation,
                            modifier = Modifier
                                .weight(1f)
                                .aspectRatio(1f),
                        )
                    }
                }
            }
        }
    }
}

@Composable
private fun StoryEmpty() {
    Column(
        verticalArrangement = Arrangement.spacedBy(SideBySideTheme.spacing.step2),
        modifier = Modifier.widthIn(max = ReadingMeasure),
    ) {
        Text(
            text = stringResource(R.string.story_empty_title),
            style = MaterialTheme.typography.titleMedium,
            color = SideBySideTheme.colors.textPrimary,
            modifier = Modifier.semantics { heading() },
        )
        Text(
            text = stringResource(R.string.story_empty_body),
            style = MaterialTheme.typography.bodyMedium,
            color = SideBySideTheme.colors.textSecondary,
        )
    }
}

/**
 * A row shows at most this many photographs side by side before each becomes
 * too small to recognise. The rest belong to the Memory's own screen.
 */
private const val MAX_IMAGES_PER_ENTRY = 3

private fun StoryEntryKind.labelRes(): Int = when (this) {
    StoryEntryKind.MEMORY -> R.string.story_kind_memory
    StoryEntryKind.MILESTONE -> R.string.story_kind_milestone
    StoryEntryKind.HEART_MOMENT -> R.string.story_kind_heart_moment
}

@Composable
private fun StoryEntryKind.accent() = when (this) {
    StoryEntryKind.MEMORY -> SideBySideTheme.colors.shared
    StoryEntryKind.MILESTONE -> SideBySideTheme.colors.discovery
    StoryEntryKind.HEART_MOMENT -> SideBySideTheme.colors.brand
}
