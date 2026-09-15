package de.eimir.app.people

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.PaddingValues
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.heightIn
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.widthIn
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.selection.selectable
import androidx.compose.foundation.selection.selectableGroup
import androidx.compose.foundation.selection.toggleable
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.Button
import androidx.compose.material3.Checkbox
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.RadioButton
import androidx.compose.material3.Surface
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.saveable.rememberSaveable
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.res.stringResource
import androidx.compose.ui.semantics.Role
import androidx.compose.ui.semantics.heading
import androidx.compose.ui.semantics.semantics
import androidx.compose.ui.unit.Dp
import androidx.compose.ui.unit.dp
import de.eimir.app.design.EimirDisplayFamily
import de.eimir.app.design.MinimumTouchTarget
import de.eimir.app.design.EimirTheme
import de.eimir.app.reference.R
import de.eimir.app.shell.UiProblem
import de.eimir.app.shell.UiStatePanel
import java.time.LocalDate
import java.util.UUID
import eimir.api.models.ContentVisibility
import eimir.api.models.DateRepeat
import eimir.api.models.ImportantDateType
import eimir.api.models.ImportantDateView

private val ReadingMeasure: Dp = 560.dp

/**
 * The dates remembered for one person: birthdays, anniversaries, anything a
 * couple wants a reminder for later. Deletion here has no confirmation
 * dialog — unlike the person itself, one date carries no cascade risk.
 */
@Composable
fun ImportantDatesScreen(
    personName: String,
    dates: List<ImportantDateView>,
    busy: Boolean,
    problem: UiProblem?,
    onBack: () -> Unit,
    onAdd: (
        label: String,
        type: ImportantDateType,
        date: LocalDate,
        repeats: DateRepeat,
        visibility: ContentVisibility,
    ) -> Unit,
    onDelete: (UUID) -> Unit,
    modifier: Modifier = Modifier,
) {
    var label by rememberSaveable { mutableStateOf("") }
    var type by rememberSaveable { mutableStateOf(ImportantDateType.BIRTHDAY) }
    var dateText by rememberSaveable { mutableStateOf("") }
    var repeatsAnnually by rememberSaveable { mutableStateOf(true) }
    var keepPrivate by rememberSaveable { mutableStateOf(false) }

    LazyColumn(
        modifier = modifier.fillMaxWidth(),
        contentPadding = PaddingValues(EimirTheme.spacing.pageMargin),
        verticalArrangement = Arrangement.spacedBy(EimirTheme.spacing.step5),
    ) {
        item {
            TextButton(onClick = onBack) { Text(stringResource(R.string.memory_back)) }
        }

        item {
            Column(verticalArrangement = Arrangement.spacedBy(EimirTheme.spacing.step2)) {
                Text(
                    text = stringResource(R.string.important_dates_title),
                    style = MaterialTheme.typography.headlineMedium
                        .copy(fontFamily = EimirDisplayFamily),
                    color = EimirTheme.colors.textPrimary,
                    modifier = Modifier.semantics { heading() },
                )
                Text(
                    text = personName,
                    style = MaterialTheme.typography.bodyMedium,
                    color = EimirTheme.colors.textSecondary,
                    modifier = Modifier.widthIn(max = ReadingMeasure),
                )
            }
        }

        problem?.let { item { UiStatePanel(problem = it) } }

        item {
            Surface(
                shape = RoundedCornerShape(EimirTheme.radii.card),
                color = EimirTheme.colors.surface,
                modifier = Modifier.fillMaxWidth(),
            ) {
                Column(
                    modifier = Modifier.padding(EimirTheme.spacing.cardPadding),
                    verticalArrangement = Arrangement.spacedBy(EimirTheme.spacing.step3),
                ) {
                    OutlinedTextField(
                        value = label,
                        onValueChange = { label = it.take(120) },
                        label = { Text(stringResource(R.string.important_date_label_hint)) },
                        modifier = Modifier.fillMaxWidth(),
                    )
                    Text(
                        text = stringResource(R.string.important_date_type),
                        style = MaterialTheme.typography.labelLarge,
                        color = EimirTheme.colors.textSecondary,
                    )
                    Column(Modifier.selectableGroup()) {
                        for (option in ImportantDateType.entries) {
                            Row(
                                modifier = Modifier
                                    .fillMaxWidth()
                                    .heightIn(min = MinimumTouchTarget)
                                    .selectable(
                                        selected = option == type,
                                        enabled = !busy,
                                        role = Role.RadioButton,
                                        onClick = { type = option },
                                    ),
                                verticalAlignment = Alignment.CenterVertically,
                            ) {
                                RadioButton(selected = option == type, onClick = null)
                                Text(
                                    text = stringResource(option.labelRes()),
                                    style = MaterialTheme.typography.bodyLarge,
                                    color = EimirTheme.colors.textPrimary,
                                    modifier = Modifier.padding(start = EimirTheme.spacing.step3),
                                )
                            }
                        }
                    }
                    OutlinedTextField(
                        value = dateText,
                        onValueChange = { dateText = it },
                        label = { Text(stringResource(R.string.important_date_date_hint)) },
                        singleLine = true,
                        modifier = Modifier.fillMaxWidth(),
                    )
                    Row(
                        modifier = Modifier
                            .heightIn(min = MinimumTouchTarget)
                            .toggleable(
                                value = repeatsAnnually,
                                role = Role.Checkbox,
                                onValueChange = { repeatsAnnually = it },
                            ),
                        verticalAlignment = Alignment.CenterVertically,
                    ) {
                        Checkbox(checked = repeatsAnnually, onCheckedChange = null)
                        Text(
                            text = stringResource(R.string.important_date_repeats_annually),
                            modifier = Modifier.padding(start = EimirTheme.spacing.step2),
                        )
                    }
                    Row(
                        modifier = Modifier
                            .heightIn(min = MinimumTouchTarget)
                            .toggleable(
                                value = keepPrivate,
                                role = Role.Checkbox,
                                onValueChange = { keepPrivate = it },
                            ),
                        verticalAlignment = Alignment.CenterVertically,
                    ) {
                        Checkbox(checked = keepPrivate, onCheckedChange = null)
                        Text(
                            text = stringResource(R.string.important_date_keep_private),
                            modifier = Modifier.padding(start = EimirTheme.spacing.step2),
                        )
                    }
                    Button(
                        onClick = {
                            val parsed = runCatching { LocalDate.parse(dateText.trim()) }.getOrNull()
                            if (parsed != null) {
                                onAdd(
                                    label,
                                    type,
                                    parsed,
                                    if (repeatsAnnually) DateRepeat.ANNUALLY else DateRepeat.NONE,
                                    if (keepPrivate) ContentVisibility.PRIVATE else ContentVisibility.SHARED,
                                )
                                label = ""
                                dateText = ""
                            }
                        },
                        enabled = !busy && label.isNotBlank() &&
                            runCatching { LocalDate.parse(dateText.trim()) }.isSuccess,
                        modifier = Modifier.heightIn(min = MinimumTouchTarget),
                    ) {
                        Text(stringResource(R.string.important_date_save))
                    }
                }
            }
        }

        if (dates.isEmpty() && !busy) {
            item {
                Text(
                    text = stringResource(R.string.important_dates_empty),
                    style = MaterialTheme.typography.bodyMedium,
                    color = EimirTheme.colors.textSecondary,
                    modifier = Modifier.widthIn(max = ReadingMeasure),
                )
            }
        }

        items(count = dates.size, key = { index -> dates[index].id.toString() }) { index ->
            val entry = dates[index]
            Surface(
                shape = RoundedCornerShape(EimirTheme.radii.card),
                color = EimirTheme.colors.surface,
                modifier = Modifier.fillMaxWidth(),
            ) {
                Row(
                    modifier = Modifier
                        .padding(EimirTheme.spacing.cardPadding)
                        .fillMaxWidth(),
                    horizontalArrangement = Arrangement.SpaceBetween,
                    verticalAlignment = Alignment.CenterVertically,
                ) {
                    Column {
                        Text(
                            text = entry.label,
                            style = MaterialTheme.typography.titleMedium,
                            color = EimirTheme.colors.textPrimary,
                        )
                        Text(
                            text = entry.date.toString(),
                            style = MaterialTheme.typography.bodySmall,
                            color = EimirTheme.colors.textSecondary,
                        )
                        Text(
                            text = stringResource(
                                if (entry.visibility == ContentVisibility.PRIVATE) {
                                    R.string.important_date_visibility_private
                                } else {
                                    R.string.important_date_visibility_shared
                                },
                            ),
                            style = MaterialTheme.typography.bodySmall,
                            color = EimirTheme.colors.textSecondary,
                        )
                    }
                    TextButton(
                        onClick = { onDelete(entry.id) },
                        enabled = !busy,
                        modifier = Modifier.heightIn(min = MinimumTouchTarget),
                    ) {
                        Text(stringResource(R.string.important_date_delete))
                    }
                }
            }
        }
    }
}

private fun ImportantDateType.labelRes(): Int = when (this) {
    ImportantDateType.BIRTHDAY -> R.string.important_date_type_birthday
    ImportantDateType.ANNIVERSARY -> R.string.important_date_type_anniversary
    ImportantDateType.CUSTOM -> R.string.important_date_type_custom
}
