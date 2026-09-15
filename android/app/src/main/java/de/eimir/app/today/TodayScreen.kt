package de.eimir.app.today

import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
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
import androidx.compose.runtime.DisposableEffect
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.LocalConfiguration
import androidx.compose.ui.res.stringResource
import androidx.compose.ui.semantics.LiveRegionMode
import androidx.compose.ui.semantics.heading
import androidx.compose.ui.semantics.liveRegion
import androidx.compose.ui.semantics.semantics
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.Dp
import androidx.compose.ui.unit.dp
import de.eimir.app.design.CouplePresence
import de.eimir.app.design.MinimumTouchTarget
import de.eimir.app.design.PartnerPresenceState
import de.eimir.app.design.EimirDisplayFamily
import de.eimir.app.design.EimirTheme
import de.eimir.app.design.ThinkingOfYouButton
import de.eimir.app.design.ThinkingOfYouState
import de.eimir.app.design.VisibilityBadge
import de.eimir.app.reference.R
import de.eimir.app.shell.MediumWidthThreshold
import de.eimir.app.shell.UiProblem
import de.eimir.app.shell.UiStateKind
import de.eimir.app.shell.UiStatePanel
import java.time.ZoneId
import java.time.format.DateTimeFormatter
import java.time.format.FormatStyle
import java.util.Locale
import java.util.UUID
import kotlinx.coroutines.delay
import eimir.api.models.DashboardItem
import eimir.api.models.DashboardItemType
import eimir.api.models.DashboardRelationshipDuration
import eimir.api.models.DashboardView
import eimir.api.models.DurationDisplayMode

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
    onOpenDurationDetails: (() -> Unit)? = null,
    onInvitePartner: (() -> Unit)? = null,
    onOpenMemory: ((UUID) -> Unit)? = null,
    userName: String? = null,
    onAcknowledgeThinkingOfYou: (() -> Unit)? = null,
    isCompact: Boolean? = null,
) {
    if (dashboard == null) {
        problem?.let { UiStatePanel(problem = it, modifier = modifier) }
        return
    }

    val resolvedUserName = userName?.takeIf { it.isNotBlank() } ?: stringResource(R.string.activity_you)
    val isCompactWidth = isCompact ?: (LocalConfiguration.current.screenWidthDp.dp < MediumWidthThreshold)

    LaunchedEffect(gestureSent) {
        if (gestureSent) {
            delay(2500L)
            onAcknowledgeThinkingOfYou?.invoke()
        }
    }

    DisposableEffect(onAcknowledgeThinkingOfYou) {
        onDispose {
            onAcknowledgeThinkingOfYou?.invoke()
        }
    }

    val partnerName = dashboard.space.partner?.displayName
    val spaceTitle = partnerName?.let {
        "$resolvedUserName & $it"
    } ?: resolvedUserName

    LazyColumn(
        modifier = modifier.fillMaxWidth(),
        contentPadding = androidx.compose.foundation.layout.PaddingValues(
            EimirTheme.spacing.pageMargin,
        ),
        verticalArrangement = Arrangement.spacedBy(EimirTheme.spacing.step5),
    ) {
        cachedAt?.let { item(key = "cached-banner") { de.eimir.app.shell.CachedContentBanner(it) } }

        // Direction B Living Sanctuary: unboxed couple presence masthead
        item(key = "couple-presence") {
            CouplePresence(
                spaceName = spaceTitle,
                userName = resolvedUserName,
                partnerName = partnerName,
                presenceState = if (partnerName != null) PartnerPresenceState.CONNECTED else PartnerPresenceState.WAITING,
                relationshipDuration = dashboard.relationshipDuration?.let { togetherForText(it) },
                onDurationClick = onOpenDurationDetails,
                onInviteClick = onInvitePartner,
                unboxed = true,
                isCompact = isCompactWidth,
                actionContent = {
                    ThinkingOfYouButton(
                        partnerName = partnerName,
                        isCompact = isCompactWidth,
                        enabled = !busy,
                        externalState = when {
                            gestureSent -> ThinkingOfYouState.SENT
                            busy -> ThinkingOfYouState.SENDING
                            else -> ThinkingOfYouState.IDLE
                        },
                        onClick = onSendThinkingOfYou,
                    )
                },
            )
        }

        if (problem?.kind == UiStateKind.RateLimit) {
            item(key = "rate-limit-hint") {
                Text(
                    text = stringResource(R.string.today_thinking_too_soon),
                    style = MaterialTheme.typography.bodyMedium,
                    color = EimirTheme.colors.textSecondary,
                    modifier = Modifier
                        .widthIn(max = ReadingMeasure)
                        .semantics { liveRegion = LiveRegionMode.Polite },
                )
            }
        }

        // A problem that is not the gesture's own is reported plainly.
        problem?.takeIf { it.kind != UiStateKind.RateLimit }?.let {
            item(key = "problem-panel") { UiStatePanel(problem = it) }
        }

        // Direction B Keepsake Tapestry: Retrospective elevated directly below masthead as primary editorial focal point
        dashboard.retrospective?.let { retroItem ->
            item(key = "retrospective-hero") {
                RetrospectiveEditorialCard(
                    item = retroItem,
                    onOpen = onOpenMemory?.let { open -> { open(retroItem.id) } },
                )
            }
        }

        section(
            headingRes = R.string.today_upcoming,
            emptyRes = R.string.today_upcoming_empty,
            items = dashboard.upcoming,
            onOpenItem = onOpenMemory,
        )

        section(
            headingRes = R.string.today_recent,
            emptyRes = R.string.today_recent_empty,
            items = dashboard.recentShared,
            onOpenItem = onOpenMemory,
        )

        item(key = "open-activity") {
            Button(
                onClick = onOpenActivity,
                modifier = Modifier
                    .fillMaxWidth()
                    .heightIn(min = MinimumTouchTarget),
            ) {
                Text(stringResource(R.string.today_open_activity))
            }
        }
    }
}

private fun androidx.compose.foundation.lazy.LazyListScope.section(
    headingRes: Int,
    emptyRes: Int?,
    items: List<DashboardItem>,
    onOpenItem: ((UUID) -> Unit)? = null,
) {
    item(key = "heading-$headingRes") {
        Text(
            text = stringResource(headingRes),
            style = MaterialTheme.typography.titleMedium,
            color = EimirTheme.colors.brandStrong,
            modifier = Modifier
                .padding(top = EimirTheme.spacing.step3)
                .semantics { heading() },
        )
    }

    if (items.isEmpty()) {
        emptyRes?.let { res ->
            item(key = "empty-$headingRes") {
                Text(
                    text = stringResource(res),
                    style = MaterialTheme.typography.bodyMedium,
                    color = EimirTheme.colors.textSecondary,
                    modifier = Modifier.widthIn(max = ReadingMeasure),
                )
            }
        }
        return
    }

    items(count = items.size, key = { index -> "$headingRes-" + items[index].id }) { index ->
        val item = items[index]
        DashboardCard(
            item = item,
            onOpen = onOpenItem?.let { open -> { open(item.id) } },
        )
    }
}

@Composable
private fun RetrospectiveEditorialCard(
    item: DashboardItem,
    onOpen: (() -> Unit)? = null,
) {
    val locale: Locale = LocalConfiguration.current.locales[0]
    val dateFormat = DateTimeFormatter.ofLocalizedDate(FormatStyle.LONG).withLocale(locale)
    val day = item.scheduledOn
        ?: item.scheduledAt?.atZoneSameInstant(ZoneId.systemDefault())?.toLocalDate()
        ?: item.occurredOn

    Column(
        verticalArrangement = Arrangement.spacedBy(EimirTheme.spacing.step2),
        modifier = Modifier
            .fillMaxWidth()
            .widthIn(max = ReadingMeasure),
    ) {
        Text(
            text = stringResource(R.string.today_retrospective),
            style = MaterialTheme.typography.titleSmall,
            color = EimirTheme.colors.brandStrong,
            modifier = Modifier.semantics { heading() },
        )

        Surface(
            shape = RoundedCornerShape(EimirTheme.radii.card),
            color = EimirTheme.colors.surface,
            border = androidx.compose.foundation.BorderStroke(1.dp, EimirTheme.colors.borderSubtle),
            modifier = Modifier
                .fillMaxWidth()
                .then(if (onOpen != null) Modifier.clickable(onClick = onOpen) else Modifier),
        ) {
            Column(
                modifier = Modifier.padding(EimirTheme.spacing.cardPadding),
                verticalArrangement = Arrangement.spacedBy(EimirTheme.spacing.step3),
            ) {
                Row(
                    modifier = Modifier.fillMaxWidth(),
                    horizontalArrangement = Arrangement.SpaceBetween,
                    verticalAlignment = Alignment.CenterVertically,
                ) {
                    Text(
                        text = stringResource(item.type.labelRes()),
                        style = MaterialTheme.typography.labelSmall,
                        color = EimirTheme.colors.brandStrong,
                    )
                    VisibilityBadge(isShared = true)
                }

                Text(
                    text = item.titleOrText?.takeIf { it.isNotBlank() }
                        ?: stringResource(R.string.today_item_untitled),
                    style = EimirTheme.typography.headlineSmall.copy(
                        fontFamily = EimirDisplayFamily,
                        fontWeight = FontWeight.SemiBold,
                    ),
                    color = EimirTheme.colors.textPrimary,
                    modifier = Modifier.widthIn(max = ReadingMeasure),
                )

                day?.let {
                    Text(
                        text = it.format(dateFormat),
                        style = MaterialTheme.typography.bodySmall,
                        color = EimirTheme.colors.textSecondary,
                    )
                }
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
private fun DashboardCard(
    item: DashboardItem,
    onOpen: (() -> Unit)? = null,
) {
    val locale: Locale = LocalConfiguration.current.locales[0]
    val dateFormat = DateTimeFormatter.ofLocalizedDate(FormatStyle.LONG).withLocale(locale)
    val day = item.scheduledOn
        ?: item.scheduledAt?.atZoneSameInstant(ZoneId.systemDefault())?.toLocalDate()
        ?: item.occurredOn

    Surface(
        shape = RoundedCornerShape(EimirTheme.radii.card),
        color = EimirTheme.colors.surface,
        border = androidx.compose.foundation.BorderStroke(1.dp, EimirTheme.colors.borderSubtle),
        modifier = Modifier
            .fillMaxWidth()
            .then(if (onOpen != null) Modifier.clickable(onClick = onOpen) else Modifier),
    ) {
        Column(
            modifier = Modifier.padding(EimirTheme.spacing.cardPadding),
            verticalArrangement = Arrangement.spacedBy(EimirTheme.spacing.step2),
        ) {
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.SpaceBetween,
                verticalAlignment = Alignment.CenterVertically,
            ) {
                Text(
                    text = stringResource(item.type.labelRes()),
                    style = MaterialTheme.typography.labelSmall,
                    color = EimirTheme.colors.brandStrong,
                )
                VisibilityBadge(isShared = true)
            }
            Text(
                // An item can arrive without words; an empty row would look
                // like a rendering fault rather than like what it is.
                text = item.titleOrText?.takeIf { it.isNotBlank() }
                    ?: stringResource(R.string.today_item_untitled),
                style = MaterialTheme.typography.titleMedium,
                color = EimirTheme.colors.textPrimary,
                modifier = Modifier.widthIn(max = ReadingMeasure),
            )
            day?.let {
                Text(
                    text = it.format(dateFormat),
                    style = MaterialTheme.typography.bodySmall,
                    color = EimirTheme.colors.textSecondary,
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
