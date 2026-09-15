package de.eimir.app.chapter

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
import de.eimir.app.design.EimirDisplayFamily
import de.eimir.app.design.MinimumTouchTarget
import de.eimir.app.design.EimirTheme
import de.eimir.app.place.RelationTargetItem
import de.eimir.app.place.labelRes
import de.eimir.app.reference.R
import de.eimir.app.shell.UiProblem
import de.eimir.app.shell.UiStatePanel

private val ReadingMeasure: Dp = 560.dp

/**
 * A chapter's own curated content, plus every shared Story item as a
 * possible addition. [linked] arrives already in the server's display
 * order — there is no manual relation position, so this screen never
 * reorders it, unlike a Collection's items.
 */
@Composable
fun ChapterContentScreen(
    chapterTitle: String,
    candidates: List<RelationTargetItem>,
    linked: List<RelationTargetItem>,
    busy: Boolean,
    problem: UiProblem?,
    onBack: () -> Unit,
    onLink: (RelationTargetItem) -> Unit,
    onUnlink: (RelationTargetItem) -> Unit,
    modifier: Modifier = Modifier,
) {
    val linkedIds = linked.map { it.id }.toSet()
    val available = candidates.filter { it.id !in linkedIds }
    var selectedId by rememberSaveable { mutableStateOf<String?>(null) }

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
                    text = stringResource(R.string.chapter_content_title),
                    style = MaterialTheme.typography.headlineMedium.copy(fontFamily = EimirDisplayFamily),
                    color = EimirTheme.colors.textPrimary,
                    modifier = Modifier.semantics { heading() },
                )
                Text(
                    text = chapterTitle,
                    style = MaterialTheme.typography.bodyMedium,
                    color = EimirTheme.colors.textSecondary,
                )
                Text(
                    text = stringResource(R.string.chapter_content_intro),
                    style = MaterialTheme.typography.bodyMedium,
                    color = EimirTheme.colors.textSecondary,
                    modifier = Modifier.widthIn(max = ReadingMeasure),
                )
            }
        }

        problem?.let { item { UiStatePanel(problem = it) } }

        if (linked.isEmpty() && !busy) {
            item {
                Text(
                    text = stringResource(R.string.chapter_content_empty),
                    style = MaterialTheme.typography.bodyMedium,
                    color = EimirTheme.colors.textSecondary,
                )
            }
        }

        items(count = linked.size, key = { index -> "linked-" + linked[index].id }) { index ->
            val target = linked[index]
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
                            text = target.label,
                            style = MaterialTheme.typography.titleMedium,
                            color = EimirTheme.colors.textPrimary,
                        )
                        Text(
                            text = "${stringResource(target.kind.labelRes())} · ${target.date}",
                            style = MaterialTheme.typography.bodySmall,
                            color = EimirTheme.colors.textSecondary,
                        )
                    }
                    TextButton(
                        onClick = { onUnlink(target) },
                        enabled = !busy,
                        modifier = Modifier.heightIn(min = MinimumTouchTarget),
                    ) {
                        Text(stringResource(R.string.chapter_content_unlink))
                    }
                }
            }
        }

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
                    Text(
                        text = stringResource(R.string.chapter_content_add_heading),
                        style = MaterialTheme.typography.titleMedium,
                        color = EimirTheme.colors.textPrimary,
                        modifier = Modifier.semantics { heading() },
                    )
                    if (available.isEmpty() && !busy) {
                        Text(
                            text = stringResource(R.string.chapter_content_none_available),
                            style = MaterialTheme.typography.bodyMedium,
                            color = EimirTheme.colors.textSecondary,
                        )
                    } else {
                        Text(
                            text = stringResource(R.string.chapter_content_choose),
                            style = MaterialTheme.typography.labelLarge,
                            color = EimirTheme.colors.textSecondary,
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
                                    Column(modifier = Modifier.padding(start = EimirTheme.spacing.step3)) {
                                        Text(
                                            text = option.label,
                                            style = MaterialTheme.typography.bodyLarge,
                                            color = EimirTheme.colors.textPrimary,
                                        )
                                        Text(
                                            text = "${stringResource(option.kind.labelRes())} · ${option.date}",
                                            style = MaterialTheme.typography.bodySmall,
                                            color = EimirTheme.colors.textSecondary,
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
                            Text(stringResource(R.string.chapter_content_link))
                        }
                    }
                }
            }
        }
    }
}
