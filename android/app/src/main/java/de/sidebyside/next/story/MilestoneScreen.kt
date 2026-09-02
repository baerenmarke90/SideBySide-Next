package de.sidebyside.next.story

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.heightIn
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.widthIn
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.material3.AlertDialog
import androidx.compose.material3.Button
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedTextField
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
import androidx.compose.ui.semantics.LiveRegionMode
import androidx.compose.ui.semantics.heading
import androidx.compose.ui.semantics.liveRegion
import androidx.compose.ui.semantics.semantics
import androidx.compose.ui.unit.Dp
import androidx.compose.ui.unit.dp
import de.sidebyside.next.design.MinimumTouchTarget
import de.sidebyside.next.design.SideBySideTheme
import de.sidebyside.next.reference.R
import de.sidebyside.next.shell.UiProblem
import de.sidebyside.next.shell.UiStateKind
import de.sidebyside.next.shell.UiStatePanel
import java.time.format.DateTimeFormatter
import java.time.format.FormatStyle
import java.util.Locale
import sidebyside.api.models.MilestoneDetail

private val ReadingMeasure: Dp = 560.dp

/**
 * One milestone, in full.
 *
 * The same shape as a memory minus its photographs, which the contract has no
 * concept of here. It is a separate screen rather than a branch inside the
 * memory's, because the two resources have different types, different endpoints
 * and different futures; sharing a screen would mean threading a discriminator
 * through every part of it.
 */
@Composable
fun MilestoneScreen(
    milestone: MilestoneDetail?,
    busy: Boolean,
    problem: UiProblem?,
    gone: Boolean,
    editing: Boolean,
    savedMessage: String?,
    onBack: () -> Unit,
    onBeginEditing: () -> Unit,
    onCancelEditing: () -> Unit,
    onSave: (title: String, body: String, happenedOn: String) -> Unit,
    onDelete: () -> Unit,
    modifier: Modifier = Modifier,
    /** Non-null only while [milestone] is a stale M2-D18 cache fallback. */
    cachedAt: java.time.Instant? = null,
    comments: (@Composable () -> Unit)? = null,
) {
    if (gone) {
        UiStatePanel(
            problem = UiProblem(
                kind = UiStateKind.Empty,
                titleRes = R.string.milestone_gone_title,
                bodyRes = R.string.milestone_gone_body,
                retryable = false,
            ),
            modifier = modifier,
        )
        return
    }

    if (milestone == null) {
        problem?.let { UiStatePanel(problem = it, modifier = modifier) }
        return
    }

    var title by rememberSaveable(milestone.id) { mutableStateOf(milestone.title) }
    var body by rememberSaveable(milestone.id) { mutableStateOf(milestone.body.orEmpty()) }
    var happenedOn by rememberSaveable(milestone.id) {
        mutableStateOf(milestone.happenedOn.toString())
    }
    var confirmingDelete by rememberSaveable(milestone.id) { mutableStateOf(false) }

    LazyColumn(
        modifier = modifier.fillMaxWidth(),
        contentPadding = androidx.compose.foundation.layout.PaddingValues(
            SideBySideTheme.spacing.pageMargin,
        ),
        verticalArrangement = Arrangement.spacedBy(SideBySideTheme.spacing.step5),
    ) {
        item {
            TextButton(onClick = onBack) { Text(stringResource(R.string.memory_back)) }
        }

        problem?.let { current -> item { UiStatePanel(problem = current) } }

        cachedAt?.let { item { de.sidebyside.next.shell.CachedContentBanner(it) } }

        savedMessage?.let { text ->
            item {
                Text(
                    text = text,
                    style = MaterialTheme.typography.bodyMedium,
                    color = SideBySideTheme.colors.success,
                    modifier = Modifier.semantics { liveRegion = LiveRegionMode.Polite },
                )
            }
        }

        if (editing) {
            item {
                Column(
                    verticalArrangement = Arrangement.spacedBy(SideBySideTheme.spacing.step3),
                ) {
                    OutlinedTextField(
                        value = title,
                        onValueChange = { title = it.take(200) },
                        label = { Text(stringResource(R.string.ref_title)) },
                        modifier = Modifier.fillMaxWidth(),
                    )
                    OutlinedTextField(
                        value = body,
                        onValueChange = { body = it },
                        label = { Text(stringResource(R.string.ref_memory)) },
                        minLines = 4,
                        modifier = Modifier.fillMaxWidth(),
                    )
                    OutlinedTextField(
                        value = happenedOn,
                        onValueChange = { happenedOn = it },
                        label = { Text(stringResource(R.string.ref_date_optional)) },
                        singleLine = true,
                        modifier = Modifier.fillMaxWidth(),
                    )
                    Row(
                        horizontalArrangement = Arrangement.spacedBy(
                            SideBySideTheme.spacing.step3,
                        ),
                    ) {
                        Button(
                            onClick = { onSave(title, body, happenedOn) },
                            enabled = !busy && title.isNotBlank(),
                            modifier = Modifier.heightIn(min = MinimumTouchTarget),
                        ) {
                            Text(stringResource(R.string.memory_save))
                        }
                        TextButton(
                            onClick = {
                                onCancelEditing()
                                title = milestone.title
                                body = milestone.body.orEmpty()
                                happenedOn = milestone.happenedOn.toString()
                            },
                            enabled = !busy,
                        ) {
                            Text(stringResource(R.string.memory_cancel))
                        }
                    }
                }
            }
        } else {
            item { MilestoneHeader(milestone) }
            // A milestone may be a date and a name with nothing more to say.
            milestone.body?.takeIf { it.isNotBlank() }?.let { text ->
                item {
                    Text(
                        text = text,
                        style = MaterialTheme.typography.bodyLarge,
                        color = SideBySideTheme.colors.textPrimary,
                        modifier = Modifier.widthIn(max = ReadingMeasure),
                    )
                }
            }
            if (milestone.capabilities.canEdit || milestone.capabilities.canDelete) {
                item {
                    Row(
                        horizontalArrangement = Arrangement.spacedBy(
                            SideBySideTheme.spacing.step3,
                        ),
                    ) {
                        if (milestone.capabilities.canEdit) {
                            Button(
                                onClick = onBeginEditing,
                                enabled = !busy,
                                modifier = Modifier.heightIn(min = MinimumTouchTarget),
                            ) {
                                Text(stringResource(R.string.memory_edit))
                            }
                        }
                        if (milestone.capabilities.canDelete) {
                            TextButton(
                                onClick = { confirmingDelete = true },
                                enabled = !busy,
                                modifier = Modifier.heightIn(min = MinimumTouchTarget),
                            ) {
                                Text(stringResource(R.string.memory_delete))
                            }
                        }
                    }
                }
            }
            comments?.let { thread -> item { thread() } }
        }
    }

    if (confirmingDelete) {
        AlertDialog(
            onDismissRequest = { confirmingDelete = false },
            title = { Text(stringResource(R.string.milestone_delete_confirm_title)) },
            text = { Text(stringResource(R.string.milestone_delete_confirm_body)) },
            confirmButton = {
                TextButton(
                    onClick = {
                        confirmingDelete = false
                        onDelete()
                    },
                ) {
                    Text(stringResource(R.string.memory_delete_confirm))
                }
            },
            dismissButton = {
                TextButton(onClick = { confirmingDelete = false }) {
                    Text(stringResource(R.string.memory_cancel))
                }
            },
        )
    }
}

@Composable
private fun MilestoneHeader(milestone: MilestoneDetail) {
    val locale: Locale = LocalConfiguration.current.locales[0]
    Column(
        verticalArrangement = Arrangement.spacedBy(SideBySideTheme.spacing.step2),
        modifier = Modifier.padding(top = SideBySideTheme.spacing.step2),
    ) {
        Text(
            text = milestone.happenedOn.format(
                DateTimeFormatter.ofLocalizedDate(FormatStyle.LONG).withLocale(locale),
            ),
            style = MaterialTheme.typography.labelLarge,
            color = SideBySideTheme.colors.brandStrong,
        )
        Text(
            text = milestone.title,
            style = MaterialTheme.typography.headlineMedium,
            color = SideBySideTheme.colors.textPrimary,
            modifier = Modifier
                .widthIn(max = ReadingMeasure)
                .semantics { heading() },
        )
        Text(
            text = stringResource(R.string.milestone_written_by, milestone.author.displayName),
            style = MaterialTheme.typography.bodySmall,
            color = SideBySideTheme.colors.textSecondary,
        )
    }
}
