package de.sidebyside.next.today

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.heightIn
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.widthIn
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.Button
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Surface
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.LocalConfiguration
import androidx.compose.ui.res.stringResource
import androidx.compose.ui.semantics.LiveRegionMode
import androidx.compose.ui.semantics.heading
import androidx.compose.ui.semantics.liveRegion
import androidx.compose.ui.semantics.semantics
import androidx.compose.ui.unit.Dp
import androidx.compose.ui.unit.dp
import de.sidebyside.next.design.SideBySideDisplayFamily
import de.sidebyside.next.design.MinimumTouchTarget
import de.sidebyside.next.design.SideBySideTheme
import de.sidebyside.next.reference.R
import de.sidebyside.next.shell.UiProblem
import de.sidebyside.next.shell.UiStateKind
import de.sidebyside.next.shell.UiStatePanel
import java.time.ZoneId
import java.time.format.DateTimeFormatter
import java.time.format.FormatStyle
import java.util.Locale
import sidebyside.api.models.DashboardItem
import sidebyside.api.models.DashboardItemType
import sidebyside.api.models.DashboardRelationshipDuration
import sidebyside.api.models.DashboardView
import sidebyside.api.models.DurationDisplayMode

private val ReadingMeasure: Dp = 560.dp

/**
 * Today.
 *
 * The first destination in the Information Architecture, and the first thing a
 * couple sees. The server assembles nearly all of it in one call, so this
 * screen's job is to present it without inventing anything: what is absent
 * stays absent rather than becoming a zero or an empty row.
 */
@Composable
fun TodayScreen(
    dashboard: DashboardView?,
    busy: Boolean,
    problem: UiProblem?,
    gestureSent: Boolean,
    onSendThinkingOfYou: () -> Unit,
    /**
     * Opens the couple's full Activity feed.
     *
     * Deliberately without a default: an optional navigation entry a caller
     * forgets to pass disappears from the product without breaking the
     * build, which is how one was lost once already in this codebase.
     */
    onOpenActivity: () -> Unit,
    modifier: Modifier = Modifier,
    /** Non-null only while [dashboard] is a stale M2-D18 cache fallback. */
    cachedAt: java.time.Instant? = null,
) {
    if (dashboard == null) {
        problem?.let { UiStatePanel(problem = it, modifier = modifier) }
        return
    }

    val partnerName = dashboard.space.partner?.displayName

    LazyColumn(
        modifier = modifier.fillMaxWidth(),
        contentPadding = androidx.compose.foundation.layout.PaddingValues(
            SideBySideTheme.spacing.pageMargin,
        ),
        verticalArrangement = Arrangement.spacedBy(SideBySideTheme.spacing.step5),
    ) {
        item {
            Text(
                text = stringResource(R.string.today_title),
                style = MaterialTheme.typography.headlineMedium.copy(fontFamily = SideBySideDisplayFamily),
                color = SideBySideTheme.colors.textPrimary,
                modifier = Modifier.semantics { heading() },
            )
        }

        cachedAt?.let { item { de.sidebyside.next.shell.CachedContentBanner(it) } }

        item {
            Button(
                onClick = onOpenActivity,
                modifier = Modifier.heightIn(min = MinimumTouchTarget),
            ) {
                Text(stringResource(R.string.today_open_activity))
            }
        }

        // One hero card, matching the Web layout: the duration line and the
        // gesture live together as one surface, not two. The duration line
        // itself is absent when the couple has not set a start date or has
        // turned it off — nothing is shown rather than "0 Tage" — but the
        // gesture below it is unconditional either way.
        item {
            TodayHero(
                duration = dashboard.relationshipDuration,
                partnerName = partnerName,
                busy = busy,
                sent = gestureSent,
                problem = problem,
                onSend = onSendThinkingOfYou,
            )
        }

        // A problem that is not the gesture's own is reported plainly.
        problem?.takeIf { it.kind != UiStateKind.RateLimit }?.let {
            item { UiStatePanel(problem = it) }
        }

        section(
            headingRes = R.string.today_upcoming,
            emptyRes = R.string.today_upcoming_empty,
            items = dashboard.upcoming,
        )

        section(
            headingRes = R.string.today_recent,
            emptyRes = R.string.today_recent_empty,
            items = dashboard.recentShared,
        )

        dashboard.retrospective?.let { item ->
            section(
                headingRes = R.string.today_retrospective,
                emptyRes = null,
                items = listOf(item),
            )
        }
    }
}

private fun androidx.compose.foundation.lazy.LazyListScope.section(
    headingRes: Int,
    emptyRes: Int?,
    items: List<DashboardItem>,
) {
    item(key = "heading-$headingRes") {
        Text(
            text = stringResource(headingRes),
            style = MaterialTheme.typography.titleMedium,
            color = SideBySideTheme.colors.brandStrong,
            modifier = Modifier
                .padding(top = SideBySideTheme.spacing.step3)
                .semantics { heading() },
        )
    }

    if (items.isEmpty()) {
        emptyRes?.let { res ->
            item(key = "empty-$headingRes") {
                Text(
                    text = stringResource(res),
                    style = MaterialTheme.typography.bodyMedium,
                    color = SideBySideTheme.colors.textSecondary,
                    modifier = Modifier.widthIn(max = ReadingMeasure),
                )
            }
        }
        return
    }

    items(count = items.size, key = { index -> "$headingRes-" + items[index].id }) { index ->
        DashboardCard(items[index])
    }
}

/**
 * The day's hero: how long the couple has been together, in the shape they
 * chose, and the "thinking of you" gesture — one surface, matching the Web
 * layout's single `today-hero` header rather than two stacked cards.
 */
@Composable
private fun TodayHero(
    duration: DashboardRelationshipDuration?,
    partnerName: String?,
    busy: Boolean,
    sent: Boolean,
    problem: UiProblem?,
    onSend: () -> Unit,
) {
    Surface(
        shape = RoundedCornerShape(SideBySideTheme.radii.card),
        color = SideBySideTheme.colors.brandSurface,
        modifier = Modifier.fillMaxWidth(),
    ) {
        Column(
            modifier = Modifier.padding(SideBySideTheme.spacing.cardPadding),
            verticalArrangement = Arrangement.spacedBy(SideBySideTheme.spacing.step3),
        ) {
            // Absent when the couple has not set a start date or has turned
            // the duration off. Nothing is shown rather than "0 Tage".
            duration?.let {
                Text(
                    text = togetherForText(it),
                    style = MaterialTheme.typography.titleMedium,
                    color = SideBySideTheme.colors.brandStrong,
                    modifier = Modifier.widthIn(max = ReadingMeasure),
                )
            }
            Text(
                text = partnerName
                    ?.let { stringResource(R.string.today_thinking_hint, it) }
                    ?: stringResource(R.string.today_thinking_hint_generic),
                style = MaterialTheme.typography.bodyMedium,
                color = SideBySideTheme.colors.textSecondary,
                modifier = Modifier.widthIn(max = ReadingMeasure),
            )
            Button(
                onClick = onSend,
                enabled = !busy,
                modifier = Modifier.heightIn(min = MinimumTouchTarget),
            ) {
                Text(stringResource(R.string.today_thinking_send))
            }
            if (sent) {
                Text(
                    text = stringResource(R.string.today_thinking_sent),
                    style = MaterialTheme.typography.bodyMedium,
                    color = SideBySideTheme.colors.success,
                    modifier = Modifier.semantics { liveRegion = LiveRegionMode.Polite },
                )
            }
            // Being told to slow down here is not an error. The generic
            // rate-limit wording is accurate and cold; this gesture deserves
            // its own sentence.
            if (problem?.kind == UiStateKind.RateLimit) {
                Text(
                    text = stringResource(R.string.today_thinking_too_soon),
                    style = MaterialTheme.typography.bodyMedium,
                    color = SideBySideTheme.colors.textSecondary,
                    modifier = Modifier
                        .widthIn(max = ReadingMeasure)
                        .semantics { liveRegion = LiveRegionMode.Polite },
                )
            }
        }
    }
}

/** The couple chose how they want to see this; the client does not pick for them. */
@Composable
private fun togetherForText(duration: DashboardRelationshipDuration): String = when (duration.displayMode) {
    DurationDisplayMode.DAYS ->
        stringResource(R.string.today_together_days, duration.daysTogether)

    DurationDisplayMode.YEARS_MONTHS -> {
        // Derived from the server's own day count rather than from the
        // device clock, which may disagree and would make the same couple
        // read differently on two phones.
        val period = java.time.Period.between(
            duration.startedOn,
            duration.startedOn.plusDays(duration.daysTogether.toLong()),
        )
        when {
            period.years > 0 && period.months > 0 -> stringResource(
                R.string.today_together_years,
                period.years,
                period.months,
            )

            period.years > 0 ->
                stringResource(R.string.today_together_years_only, period.years)

            else -> stringResource(R.string.today_together_months, period.months)
        }
    }
}

@Composable
private fun DashboardCard(item: DashboardItem) {
    val locale: Locale = LocalConfiguration.current.locales[0]
    val dateFormat = DateTimeFormatter.ofLocalizedDate(FormatStyle.LONG).withLocale(locale)
    val day = item.scheduledAt?.atZoneSameInstant(ZoneId.systemDefault())?.toLocalDate()
        ?: item.occurredOn

    Surface(
        shape = RoundedCornerShape(SideBySideTheme.radii.card),
        color = SideBySideTheme.colors.surface,
        modifier = Modifier.fillMaxWidth(),
    ) {
        Column(
            modifier = Modifier.padding(SideBySideTheme.spacing.cardPadding),
            verticalArrangement = Arrangement.spacedBy(SideBySideTheme.spacing.step2),
        ) {
            Text(
                text = stringResource(item.type.labelRes()),
                style = MaterialTheme.typography.labelSmall,
                color = SideBySideTheme.colors.brandStrong,
            )
            Text(
                // An item can arrive without words; an empty row would look
                // like a rendering fault rather than like what it is.
                text = item.titleOrText?.takeIf { it.isNotBlank() }
                    ?: stringResource(R.string.today_item_untitled),
                style = MaterialTheme.typography.titleMedium,
                color = SideBySideTheme.colors.textPrimary,
                modifier = Modifier.widthIn(max = ReadingMeasure),
            )
            day?.let {
                Text(
                    text = it.format(dateFormat),
                    style = MaterialTheme.typography.bodySmall,
                    color = SideBySideTheme.colors.textSecondary,
                )
            }
        }
    }
}

private fun DashboardItemType.labelRes(): Int = when (this) {
    DashboardItemType.MEMORY -> R.string.today_type_memory
    DashboardItemType.HEART_MOMENT -> R.string.today_type_heart_moment
    DashboardItemType.MILESTONE -> R.string.today_type_milestone
    DashboardItemType.WISH -> R.string.today_type_wish
    DashboardItemType.PLAN -> R.string.today_type_plan
    DashboardItemType.PLACE -> R.string.today_type_place
    DashboardItemType.CHAPTER -> R.string.today_type_chapter
    DashboardItemType.COLLECTION -> R.string.today_type_collection
    DashboardItemType.IMPORTANT_DATE -> R.string.today_type_important_date
    DashboardItemType.BIRTHDAY -> R.string.today_type_birthday
    DashboardItemType.ANNIVERSARY -> R.string.today_type_anniversary
}
