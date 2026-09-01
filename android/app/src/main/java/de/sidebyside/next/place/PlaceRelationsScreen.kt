package de.sidebyside.next.place

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
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.Button
import androidx.compose.material3.MaterialTheme
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
import de.sidebyside.next.design.FrauncesFamily
import de.sidebyside.next.design.MinimumTouchTarget
import de.sidebyside.next.design.SideBySideTheme
import de.sidebyside.next.reference.R
import de.sidebyside.next.reference.ReferenceContract
import de.sidebyside.next.shell.UiProblem
import de.sidebyside.next.shell.UiStatePanel

private val ReadingMeasure: Dp = 560.dp

/**
 * What a place is linked to: a Memory, Milestone or HeartMoment already on
 * the shared Story.
 *
 * [targets] and [linkedIds] arrive raw and are filtered here into "linked"
 * and "available to link" — not because the ViewModel could not do it, but
 * because the split is pure presentation, and [linkedIds] already carries
 * the one fact that matters privacy-wise: only Story items the caller can
 * already see ever reach [targets] to begin with.
 */
@Composable
fun PlaceRelationsScreen(
    placeName: String,
    targets: List<RelationTargetItem>,
    linkedIds: Set<java.util.UUID>,
    busy: Boolean,
    problem: UiProblem?,
    onBack: () -> Unit,
    onLink: (RelationTargetItem) -> Unit,
    onUnlink: (RelationTargetItem) -> Unit,
    modifier: Modifier = Modifier,
) {
    val linked = targets.filter { it.id in linkedIds }
    val available = targets.filter { it.id !in linkedIds }
    var selectedId by rememberSaveable { mutableStateOf<String?>(null) }

    LazyColumn(
        modifier = modifier.fillMaxWidth(),
        contentPadding = PaddingValues(SideBySideTheme.spacing.pageMargin),
        verticalArrangement = Arrangement.spacedBy(SideBySideTheme.spacing.step5),
    ) {
        item {
            TextButton(onClick = onBack) { Text(stringResource(R.string.memory_back)) }
        }

        item {
            Column(verticalArrangement = Arrangement.spacedBy(SideBySideTheme.spacing.step2)) {
                Text(
                    text = stringResource(R.string.place_relations_title),
                    style = MaterialTheme.typography.headlineMedium.copy(fontFamily = FrauncesFamily),
                    color = SideBySideTheme.colors.textPrimary,
                    modifier = Modifier.semantics { heading() },
                )
                Text(
                    text = placeName,
                    style = MaterialTheme.typography.bodyMedium,
                    color = SideBySideTheme.colors.textSecondary,
                )
                Text(
                    text = stringResource(R.string.place_relations_intro),
                    style = MaterialTheme.typography.bodyMedium,
                    color = SideBySideTheme.colors.textSecondary,
                    modifier = Modifier.widthIn(max = ReadingMeasure),
                )
            }
        }

        problem?.let { item { UiStatePanel(problem = it) } }

        if (linked.isEmpty() && !busy) {
            item {
                Text(
                    text = stringResource(R.string.place_relations_empty),
                    style = MaterialTheme.typography.bodyMedium,
                    color = SideBySideTheme.colors.textSecondary,
                )
            }
        }

        items(count = linked.size, key = { index -> "linked-" + linked[index].id }) { index ->
            val target = linked[index]
            Surface(
                shape = RoundedCornerShape(SideBySideTheme.radii.card),
                color = SideBySideTheme.colors.surface,
                modifier = Modifier.fillMaxWidth(),
            ) {
                Row(
                    modifier = Modifier
                        .padding(SideBySideTheme.spacing.cardPadding)
                        .fillMaxWidth(),
                    horizontalArrangement = Arrangement.SpaceBetween,
                    verticalAlignment = Alignment.CenterVertically,
                ) {
                    Column {
                        Text(
                            text = target.label,
                            style = MaterialTheme.typography.titleMedium,
                            color = SideBySideTheme.colors.textPrimary,
                        )
                        Text(
                            text = "${stringResource(target.kind.labelRes())} · ${target.date}",
                            style = MaterialTheme.typography.bodySmall,
                            color = SideBySideTheme.colors.textSecondary,
                        )
                    }
                    TextButton(
                        onClick = { onUnlink(target) },
                        enabled = !busy,
                        modifier = Modifier.heightIn(min = MinimumTouchTarget),
                    ) {
                        Text(stringResource(R.string.place_relation_unlink))
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
                        text = stringResource(R.string.place_relation_add_heading),
                        style = MaterialTheme.typography.titleMedium,
                        color = SideBySideTheme.colors.textPrimary,
                        modifier = Modifier.semantics { heading() },
                    )
                    if (available.isEmpty() && !busy) {
                        Text(
                            text = stringResource(R.string.place_relation_none_available),
                            style = MaterialTheme.typography.bodyMedium,
                            color = SideBySideTheme.colors.textSecondary,
                        )
                    } else {
                        Text(
                            text = stringResource(R.string.place_relation_choose),
                            style = MaterialTheme.typography.labelLarge,
                            color = SideBySideTheme.colors.textSecondary,
                        )
                        Column(Modifier.selectableGroup()) {
                            for (option in available) {
                                val optionId = option.id.toString()
                                Row(
                                    modifier = Modifier
                                        .fillMaxWidth()
                                        .heightIn(min = MinimumTouchTarget)
                                        .selectable(
                                            selected = optionId == selectedId,
                                            enabled = !busy,
                                            role = Role.RadioButton,
                                            onClick = { selectedId = optionId },
                                        ),
                                    verticalAlignment = Alignment.CenterVertically,
                                ) {
                                    RadioButton(selected = optionId == selectedId, onClick = null)
                                    Column(modifier = Modifier.padding(start = SideBySideTheme.spacing.step3)) {
                                        Text(
                                            text = option.label,
                                            style = MaterialTheme.typography.bodyLarge,
                                            color = SideBySideTheme.colors.textPrimary,
                                        )
                                        Text(
                                            text = "${stringResource(option.kind.labelRes())} · ${option.date}",
                                            style = MaterialTheme.typography.bodySmall,
                                            color = SideBySideTheme.colors.textSecondary,
                                        )
                                    }
                                }
                            }
                        }
                        Button(
                            onClick = {
                                available.firstOrNull { it.id.toString() == selectedId }?.let(onLink)
                                selectedId = null
                            },
                            enabled = !busy && selectedId != null,
                            modifier = Modifier.heightIn(min = MinimumTouchTarget),
                        ) {
                            Text(stringResource(R.string.place_relation_link))
                        }
                    }
                }
            }
        }
    }
}

private fun ReferenceContract.RelationTargetKind.labelRes(): Int = when (this) {
    ReferenceContract.RelationTargetKind.MEMORY -> R.string.place_relation_kind_memory
    ReferenceContract.RelationTargetKind.MILESTONE -> R.string.place_relation_kind_milestone
    ReferenceContract.RelationTargetKind.HEART_MOMENT -> R.string.place_relation_kind_heart_moment
}
