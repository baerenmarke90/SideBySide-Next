package de.sidebyside.next.plan

import androidx.compose.runtime.Composable
import androidx.compose.ui.platform.LocalConfiguration
import androidx.compose.ui.res.stringResource
import de.sidebyside.next.design.SideBySideTheme
import de.sidebyside.next.reference.R
import java.time.LocalDate
import java.time.OffsetDateTime
import java.time.ZoneId
import java.time.format.DateTimeFormatter
import java.time.format.FormatStyle
import java.util.Locale
import sidebyside.api.models.PlanDetail
import sidebyside.api.models.PlanStatus

/**
 * How a plan says what it is and when it is.
 *
 * Shared by the overview and by the focused surfaces so a plan cannot read one
 * way in the stack and another way once it is opened.
 */

internal fun PlanStatus.labelRes(): Int = when (this) {
    PlanStatus.IDEA -> R.string.plan_status_idea
    PlanStatus.PLANNED -> R.string.plan_status_planned
    PlanStatus.COMPLETED -> R.string.plan_status_completed
}

@Composable
internal fun PlanStatus.accent() = when (this) {
    PlanStatus.IDEA -> SideBySideTheme.colors.textSecondary
    PlanStatus.PLANNED -> SideBySideTheme.colors.discovery
    PlanStatus.COMPLETED -> SideBySideTheme.colors.success
}

@Composable
private fun locale(): Locale = LocalConfiguration.current.locales[0]

/** A stored instant, read back in the device's own zone and locale. */
@Composable
internal fun formattedDateTime(value: OffsetDateTime): String = value
    .atZoneSameInstant(ZoneId.systemDefault())
    .format(
        DateTimeFormatter.ofLocalizedDateTime(FormatStyle.LONG, FormatStyle.SHORT)
            .withLocale(locale()),
    )

@Composable
internal fun formattedDate(value: LocalDate): String =
    value.format(DateTimeFormatter.ofLocalizedDate(FormatStyle.LONG).withLocale(locale()))

/**
 * The single timing line a plan card carries, or none.
 *
 * A plan that has been experienced is described by the day it happened; one
 * that has not is described by the day it is meant to. Showing both at once on
 * a card would turn the couple's plan back into a record with fields.
 */
@Composable
internal fun planTimingLine(plan: PlanDetail): String? = when {
    plan.experiencedOn != null ->
        stringResource(R.string.plan_experienced_on, formattedDate(plan.experiencedOn!!))

    plan.plannedStart != null ->
        stringResource(R.string.plan_scheduled_for, formattedDateTime(plan.plannedStart!!))

    else -> null
}
