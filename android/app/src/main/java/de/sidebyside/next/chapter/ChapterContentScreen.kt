package de.sidebyside.next.chapter

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
import de.sidebyside.next.place.RelationTargetItem
import de.sidebyside.next.place.labelRes
import de.sidebyside.next.reference.R
import de.sidebyside.next.shell.UiProblem
import de.sidebyside.next.shell.UiStatePanel

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
        contentPadding = PaddingValues(SideBySideTheme.spacing.pageMargin),
        verticalArrangement = Arrangement.spacedBy(SideBySideTheme.spacing.step5),
    ) {
        item {
            TextButton(onClick = onBack) { Text(stringResource(R.string.memory_back)) }
        }

        item {
            Column(verticalArrangement = Arrangement.spacedBy(SideBySideTheme.spacing.step2)) {
                Text(
                    text = stringResource(R.string.chapter_content_title),
                    style = MaterialTheme.typography.headlineMedium.copy(fontFamily = FrauncesFamily),
                    color = SideBySideTheme.colors.textPrimary,
                    modifier = Modifier.semantics { heading() },
                )
                Text(
                    text = chapterTitle,
                    style = MaterialTheme.typography.bodyMedium,
                    color = SideBySideTheme.colors.textSecondary,
                )
                Text(
                    text = stringResource(R.string.chapter_content_intro),
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
                    text = stringResource(R.string.chapter_content_empty),
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
                        Text(stringResource(R.string.chapter_content_unlink))
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
                        text = stringResource(R.string.chapter_content_add_heading),
                        style = MaterialTheme.typography.titleMedium,
                        color = SideBySideTheme.colors.textPrimary,
                        modifier = Modifier.semantics { heading() },
                    )
                    if (available.isEmpty() && !busy) {
                        Text(
                            text = stringResource(R.string.chapter_content_none_available),
                            style = MaterialTheme.typography.bodyMedium,
                            color = SideBySideTheme.colors.textSecondary,
                        )
                    } else {
                        Text(
                            text = stringResource(R.string.chapter_content_choose),
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
                            Text(stringResource(R.string.chapter_content_link))
                        }
                    }
                }
            }
        }
    }
}
