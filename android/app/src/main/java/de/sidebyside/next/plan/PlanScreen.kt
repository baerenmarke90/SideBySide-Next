package de.sidebyside.next.plan

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.heightIn
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.widthIn
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.AlertDialog
import androidx.compose.material3.Button
import androidx.compose.material3.FilledTonalButton
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.Surface
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.saveable.rememberSaveable
import androidx.compose.runtime.setValue
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.LocalConfiguration
import androidx.compose.ui.res.stringResource
import androidx.compose.ui.semantics.heading
import androidx.compose.ui.semantics.semantics
import androidx.compose.ui.unit.Dp
import androidx.compose.ui.unit.dp
import de.sidebyside.next.design.FrauncesFamily
import de.sidebyside.next.design.MinimumTouchTarget
import de.sidebyside.next.design.SideBySideTheme
import de.sidebyside.next.reference.R
import de.sidebyside.next.shell.UiProblem
import de.sidebyside.next.shell.UiStatePanel
import java.time.LocalDate
import java.time.OffsetDateTime
import java.time.ZoneId
import java.time.format.DateTimeFormatter
import java.time.format.FormatStyle
import java.util.Locale
import java.util.UUID
import sidebyside.api.models.PlanDetail
import sidebyside.api.models.PlanStatus
import sidebyside.api.models.WishDetail

private val ReadingMeasure: Dp = 560.dp

/**
 * Planen.
 *
 * The contract is a lifecycle, not two lists, so the screen shows it as one:
 * ideas at the top, and below them the plans they became, each carrying only
 * the moves that are available from where it stands.
 *
 * A wish that became a plan is deliberately not listed again above; the view
 * model keeps only `OPEN` ones, because showing an intention twice would
 * suggest there are two of them.
 */
@Composable
fun PlanScreen(
    wishes: List<WishDetail>,
    plans: List<PlanDetail>,
    busy: Boolean,
    problem: UiProblem?,
    onAddWish: (String) -> Unit,
    onPlanWish: (UUID) -> Unit,
    onRemoveWish: (UUID) -> Unit,
    onSchedule: (UUID, OffsetDateTime) -> Unit,
    onUnschedule: (UUID) -> Unit,
    onComplete: (UUID, LocalDate) -> Unit,
    onReturnToWish: (UUID) -> Unit,
    onDeletePlan: (UUID) -> Unit,
    /**
     * Opens the couple's shared places.
     *
     * Deliberately without a default, for the same reason every other
     * navigation entry point in this client is: an optional one that a
     * caller forgets to pass disappears from the product without breaking
     * the build.
     */
    onOpenPlaces: () -> Unit,
    /**
     * Opens the couple's shared lists.
     *
     * Deliberately without a default, for the same reason as [onOpenPlaces].
     */
    onOpenCollections: () -> Unit,
    modifier: Modifier = Modifier,
) {
    var draft by rememberSaveable { mutableStateOf("") }
    var returnTarget by rememberSaveable { mutableStateOf<String?>(null) }
    var deleteTarget by rememberSaveable { mutableStateOf<String?>(null) }

    LazyColumn(
        modifier = modifier.fillMaxWidth(),
        contentPadding = androidx.compose.foundation.layout.PaddingValues(
            SideBySideTheme.spacing.pageMargin,
        ),
        verticalArrangement = Arrangement.spacedBy(SideBySideTheme.spacing.step5),
    ) {
        item {
            Column(verticalArrangement = Arrangement.spacedBy(SideBySideTheme.spacing.step2)) {
                Text(
                    text = stringResource(R.string.plan_title),
                    style = MaterialTheme.typography.headlineMedium
                        .copy(fontFamily = FrauncesFamily),
                    color = SideBySideTheme.colors.textPrimary,
                    modifier = Modifier.semantics { heading() },
                )
                Text(
                    text = stringResource(R.string.plan_intro),
                    style = MaterialTheme.typography.bodyMedium,
                    color = SideBySideTheme.colors.textSecondary,
                    modifier = Modifier.widthIn(max = ReadingMeasure),
                )
            }
        }

        problem?.let { item { UiStatePanel(problem = it) } }

        item {
            Surface(
                shape = RoundedCornerShape(SideBySideTheme.radii.card),
                color = SideBySideTheme.colors.surface,
                modifier = Modifier.fillMaxWidth(),
            ) {
                Column(
                    modifier = Modifier.padding(SideBySideTheme.spacing.cardPadding),
                    verticalArrangement = Arrangement.spacedBy(SideBySideTheme.spacing.step3),
                ) {
                    Text(
                        text = stringResource(R.string.places_title),
                        style = MaterialTheme.typography.titleMedium,
                        color = SideBySideTheme.colors.textPrimary,
                        modifier = Modifier.semantics { heading() },
                    )
                    Text(
                        text = stringResource(R.string.places_intro),
                        style = MaterialTheme.typography.bodyMedium,
                        color = SideBySideTheme.colors.textSecondary,
                    )
                    FilledTonalButton(
                        onClick = onOpenPlaces,
                        modifier = Modifier.heightIn(min = MinimumTouchTarget),
                    ) {
                        Text(stringResource(R.string.places_open))
                    }
                }
            }
        }

        item {
            Surface(
                shape = RoundedCornerShape(SideBySideTheme.radii.card),
                color = SideBySideTheme.colors.surface,
                modifier = Modifier.fillMaxWidth(),
            ) {
                Column(
                    modifier = Modifier.padding(SideBySideTheme.spacing.cardPadding),
                    verticalArrangement = Arrangement.spacedBy(SideBySideTheme.spacing.step3),
                ) {
                    Text(
                        text = stringResource(R.string.collections_title),
                        style = MaterialTheme.typography.titleMedium,
                        color = SideBySideTheme.colors.textPrimary,
                        modifier = Modifier.semantics { heading() },
                    )
                    Text(
                        text = stringResource(R.string.collections_intro),
                        style = MaterialTheme.typography.bodyMedium,
                        color = SideBySideTheme.colors.textSecondary,
                    )
                    FilledTonalButton(
                        onClick = onOpenCollections,
                        modifier = Modifier.heightIn(min = MinimumTouchTarget),
                    ) {
                        Text(stringResource(R.string.collections_open))
                    }
                }
            }
        }

        item {
            Text(
                text = stringResource(R.string.plan_wishes_heading),
                style = MaterialTheme.typography.titleMedium,
                color = SideBySideTheme.colors.brandStrong,
                modifier = Modifier.semantics { heading() },
            )
        }

        item {
            Column(verticalArrangement = Arrangement.spacedBy(SideBySideTheme.spacing.step3)) {
                OutlinedTextField(
                    value = draft,
                    onValueChange = { draft = it.take(200) },
                    label = { Text(stringResource(R.string.plan_wish_hint)) },
                    modifier = Modifier.fillMaxWidth(),
                )
                Button(
                    onClick = {
                        onAddWish(draft)
                        draft = ""
                    },
                    enabled = !busy && draft.isNotBlank(),
                    modifier = Modifier.heightIn(min = MinimumTouchTarget),
                ) {
                    Text(stringResource(R.string.plan_wish_add))
                }
            }
        }

        if (wishes.isEmpty() && !busy) {
            item {
                Text(
                    text = stringResource(R.string.plan_wishes_empty),
                    style = MaterialTheme.typography.bodyMedium,
                    color = SideBySideTheme.colors.textSecondary,
                    modifier = Modifier.widthIn(max = ReadingMeasure),
                )
            }
        }

        items(count = wishes.size, key = { index -> "wish-" + wishes[index].id }) { index ->
            WishCard(
                wish = wishes[index],
                busy = busy,
                onPlan = { onPlanWish(wishes[index].id) },
                onRemove = { onRemoveWish(wishes[index].id) },
            )
        }

        item {
            Text(
                text = stringResource(R.string.plan_plans_heading),
                style = MaterialTheme.typography.titleMedium,
                color = SideBySideTheme.colors.brandStrong,
                modifier = Modifier
                    .padding(top = SideBySideTheme.spacing.step4)
                    .semantics { heading() },
            )
        }

        if (plans.isEmpty() && !busy) {
            item {
                Text(
                    text = stringResource(R.string.plan_plans_empty),
                    style = MaterialTheme.typography.bodyMedium,
                    color = SideBySideTheme.colors.textSecondary,
                    modifier = Modifier.widthIn(max = ReadingMeasure),
                )
            }
        }

        items(count = plans.size, key = { index -> "plan-" + plans[index].id }) { index ->
            PlanCard(
                plan = plans[index],
                busy = busy,
                onSchedule = {
                    // A date picker belongs to the slice that adds one; until
                    // then a plan is scheduled for today and moved from there.
                    onSchedule(plans[index].id, OffsetDateTime.now())
                },
                onUnschedule = { onUnschedule(plans[index].id) },
                onComplete = { onComplete(plans[index].id, LocalDate.now()) },
                onReturnToWish = { returnTarget = plans[index].id.toString() },
                onDelete = { deleteTarget = plans[index].id.toString() },
            )
        }
    }

    returnTarget?.let { id ->
        AlertDialog(
            onDismissRequest = { returnTarget = null },
            title = { Text(stringResource(R.string.plan_return_title)) },
            // The wish receives nothing back from the plan, so this loses
            // whatever was written into it. Said before, not after.
            text = { Text(stringResource(R.string.plan_return_body)) },
            confirmButton = {
                TextButton(
                    onClick = {
                        returnTarget = null
                        plans.firstOrNull { it.id.toString() == id }
                            ?.let { onReturnToWish(it.id) }
                    },
                ) {
                    Text(stringResource(R.string.plan_return_to_wish))
                }
            },
            dismissButton = {
                TextButton(onClick = { returnTarget = null }) {
                    Text(stringResource(R.string.plan_cancel))
                }
            },
        )
    }

    deleteTarget?.let { id ->
        AlertDialog(
            onDismissRequest = { deleteTarget = null },
            title = { Text(stringResource(R.string.plan_delete_title)) },
            text = { Text(stringResource(R.string.plan_delete_body)) },
            confirmButton = {
                TextButton(
                    onClick = {
                        deleteTarget = null
                        plans.firstOrNull { it.id.toString() == id }?.let { onDeletePlan(it.id) }
                    },
                ) {
                    Text(stringResource(R.string.plan_delete))
                }
            },
            dismissButton = {
                TextButton(onClick = { deleteTarget = null }) {
                    Text(stringResource(R.string.plan_cancel))
                }
            },
        )
    }
}

@Composable
private fun WishCard(
    wish: WishDetail,
    busy: Boolean,
    onPlan: () -> Unit,
    onRemove: () -> Unit,
) {
    Surface(
        shape = RoundedCornerShape(SideBySideTheme.radii.card),
        color = SideBySideTheme.colors.surface,
        modifier = Modifier.fillMaxWidth(),
    ) {
        Column(
            modifier = Modifier.padding(SideBySideTheme.spacing.cardPadding),
            verticalArrangement = Arrangement.spacedBy(SideBySideTheme.spacing.step3),
        ) {
            Text(
                text = wish.title,
                style = MaterialTheme.typography.titleMedium,
                color = SideBySideTheme.colors.textPrimary,
                modifier = Modifier.widthIn(max = ReadingMeasure),
            )
            Row(horizontalArrangement = Arrangement.spacedBy(SideBySideTheme.spacing.step3)) {
                if (wish.capabilities.canEdit) {
                    FilledTonalButton(
                        onClick = onPlan,
                        enabled = !busy,
                        modifier = Modifier.heightIn(min = MinimumTouchTarget),
                    ) {
                        Text(stringResource(R.string.plan_wish_make_plan))
                    }
                }
                if (wish.capabilities.canDelete) {
                    TextButton(
                        onClick = onRemove,
                        enabled = !busy,
                        modifier = Modifier.heightIn(min = MinimumTouchTarget),
                    ) {
                        Text(stringResource(R.string.plan_wish_remove))
                    }
                }
            }
        }
    }
}

@Composable
private fun PlanCard(
    plan: PlanDetail,
    busy: Boolean,
    onSchedule: () -> Unit,
    onUnschedule: () -> Unit,
    onComplete: () -> Unit,
    onReturnToWish: () -> Unit,
    onDelete: () -> Unit,
) {
    val locale: Locale = LocalConfiguration.current.locales[0]
    val dateFormat = DateTimeFormatter.ofLocalizedDate(FormatStyle.LONG).withLocale(locale)

    Surface(
        shape = RoundedCornerShape(SideBySideTheme.radii.card),
        color = SideBySideTheme.colors.surface,
        modifier = Modifier.fillMaxWidth(),
    ) {
        Column(
            modifier = Modifier.padding(SideBySideTheme.spacing.cardPadding),
            verticalArrangement = Arrangement.spacedBy(SideBySideTheme.spacing.step3),
        ) {
            // The status is a word, not only a colour, so it survives a
            // colour-blind reading and a screen reader.
            Text(
                text = stringResource(plan.status.labelRes()),
                style = MaterialTheme.typography.labelSmall,
                color = plan.status.accent(),
            )
            Text(
                text = plan.title,
                style = MaterialTheme.typography.titleMedium,
                color = SideBySideTheme.colors.textPrimary,
                modifier = Modifier.widthIn(max = ReadingMeasure),
            )
            plan.description?.takeIf { it.isNotBlank() }?.let { text ->
                Text(
                    text = text,
                    style = MaterialTheme.typography.bodyMedium,
                    color = SideBySideTheme.colors.textSecondary,
                    modifier = Modifier.widthIn(max = ReadingMeasure),
                )
            }
            plan.plannedStart?.let { start ->
                Text(
                    text = stringResource(
                        R.string.plan_scheduled_for,
                        start.atZoneSameInstant(ZoneId.systemDefault()).toLocalDate()
                            .format(dateFormat),
                    ),
                    style = MaterialTheme.typography.bodySmall,
                    color = SideBySideTheme.colors.textSecondary,
                )
            }
            plan.experiencedOn?.let { day ->
                Text(
                    text = stringResource(R.string.plan_experienced_on, day.format(dateFormat)),
                    style = MaterialTheme.typography.bodySmall,
                    color = SideBySideTheme.colors.textSecondary,
                )
            }

            if (plan.capabilities.canEdit || plan.capabilities.canDelete) {
                // Only the moves the plan's current status actually allows.
                Row(horizontalArrangement = Arrangement.spacedBy(SideBySideTheme.spacing.step3)) {
                    if (plan.capabilities.canEdit) {
                        when (plan.status) {
                            PlanStatus.IDEA -> {
                                FilledTonalButton(
                                    onClick = onSchedule,
                                    enabled = !busy,
                                    modifier = Modifier.heightIn(min = MinimumTouchTarget),
                                ) {
                                    Text(stringResource(R.string.plan_schedule))
                                }
                                TextButton(onClick = onReturnToWish, enabled = !busy) {
                                    Text(stringResource(R.string.plan_return_to_wish))
                                }
                            }

                            PlanStatus.PLANNED -> {
                                FilledTonalButton(
                                    onClick = onComplete,
                                    enabled = !busy,
                                    modifier = Modifier.heightIn(min = MinimumTouchTarget),
                                ) {
                                    Text(stringResource(R.string.plan_complete))
                                }
                                TextButton(onClick = onUnschedule, enabled = !busy) {
                                    Text(stringResource(R.string.plan_unschedule))
                                }
                            }

                            // Experienced is where it ends; there is nothing
                            // sensible to move it to.
                            PlanStatus.COMPLETED -> Unit
                        }
                    }
                    if (plan.capabilities.canDelete) {
                        TextButton(onClick = onDelete, enabled = !busy) {
                            Text(stringResource(R.string.plan_delete))
                        }
                    }
                }
            }
        }
    }
}

private fun PlanStatus.labelRes(): Int = when (this) {
    PlanStatus.IDEA -> R.string.plan_status_idea
    PlanStatus.PLANNED -> R.string.plan_status_planned
    PlanStatus.COMPLETED -> R.string.plan_status_completed
}

@Composable
private fun PlanStatus.accent() = when (this) {
    PlanStatus.IDEA -> SideBySideTheme.colors.textSecondary
    PlanStatus.PLANNED -> SideBySideTheme.colors.discovery
    PlanStatus.COMPLETED -> SideBySideTheme.colors.success
}
