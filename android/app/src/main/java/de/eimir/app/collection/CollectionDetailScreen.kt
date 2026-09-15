package de.eimir.app.collection

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.PaddingValues
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.heightIn
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.widthIn
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.Button
import androidx.compose.material3.Checkbox
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
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.res.stringResource
import androidx.compose.ui.semantics.heading
import androidx.compose.ui.semantics.semantics
import androidx.compose.ui.text.style.TextDecoration
import androidx.compose.ui.unit.Dp
import androidx.compose.ui.unit.dp
import de.eimir.app.design.EimirDisplayFamily
import de.eimir.app.design.MinimumTouchTarget
import de.eimir.app.design.EimirTheme
import de.eimir.app.reference.R
import de.eimir.app.shell.UiProblem
import de.eimir.app.shell.UiStatePanel
import eimir.api.models.CollectionDetail
import eimir.api.models.CollectionItemDetail

private val ReadingMeasure: Dp = 560.dp

/**
 * One list's items. Reordering is up/down buttons rather than drag
 * gestures: each tap swaps one item with its neighbour and sends the whole
 * resulting order, which by construction is always the same set of ids the
 * server already has — the exact-set contract needs no separate check here.
 */
@Composable
fun CollectionDetailScreen(
    collection: CollectionDetail?,
    busy: Boolean,
    problem: UiProblem?,
    onBack: () -> Unit,
    onAddItem: (title: String) -> Unit,
    onRenameItem: (CollectionItemDetail, String) -> Unit,
    onToggleCompleted: (CollectionItemDetail) -> Unit,
    onDeleteItem: (CollectionItemDetail) -> Unit,
    onMoveUp: (CollectionItemDetail) -> Unit,
    onMoveDown: (CollectionItemDetail) -> Unit,
    modifier: Modifier = Modifier,
) {
    val items = collection?.items.orEmpty().sortedBy { it.position }
    var newItemTitle by rememberSaveable { mutableStateOf("") }
    var editingItemId by rememberSaveable { mutableStateOf<String?>(null) }

    LazyColumn(
        modifier = modifier.fillMaxWidth(),
        contentPadding = PaddingValues(EimirTheme.spacing.pageMargin),
        verticalArrangement = Arrangement.spacedBy(EimirTheme.spacing.step5),
    ) {
        item {
            TextButton(onClick = onBack) { Text(stringResource(R.string.memory_back)) }
        }

        item {
            Text(
                text = collection?.title.orEmpty(),
                style = MaterialTheme.typography.headlineMedium.copy(fontFamily = EimirDisplayFamily),
                color = EimirTheme.colors.textPrimary,
                modifier = Modifier.semantics { heading() }.widthIn(max = ReadingMeasure),
            )
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
                        value = newItemTitle,
                        onValueChange = { newItemTitle = it.take(200) },
                        label = { Text(stringResource(R.string.collection_item_title_hint)) },
                        enabled = !busy,
                        singleLine = true,
                        modifier = Modifier.fillMaxWidth(),
                    )
                    Button(
                        onClick = {
                            onAddItem(newItemTitle)
                            newItemTitle = ""
                        },
                        enabled = !busy && newItemTitle.isNotBlank(),
                        modifier = Modifier.heightIn(min = MinimumTouchTarget),
                    ) {
                        Text(stringResource(R.string.collection_item_add))
                    }
                }
            }
        }

        if (items.isEmpty() && !busy) {
            item {
                Text(
                    text = stringResource(R.string.collection_items_empty),
                    style = MaterialTheme.typography.bodyMedium,
                    color = EimirTheme.colors.textSecondary,
                )
            }
        }

        items(count = items.size, key = { index -> items[index].id.toString() }) { index ->
            val entry = items[index]
            Surface(
                shape = RoundedCornerShape(EimirTheme.radii.card),
                color = EimirTheme.colors.surface,
                modifier = Modifier.fillMaxWidth(),
            ) {
                if (editingItemId == entry.id.toString()) {
                    var title by rememberSaveable(entry.id) { mutableStateOf(entry.title) }
                    Row(
                        modifier = Modifier
                            .padding(EimirTheme.spacing.cardPadding)
                            .fillMaxWidth(),
                        verticalAlignment = Alignment.CenterVertically,
                    ) {
                        OutlinedTextField(
                            value = title,
                            onValueChange = { title = it.take(200) },
                            singleLine = true,
                            modifier = Modifier.weight(1f),
                        )
                        Button(
                            onClick = {
                                editingItemId = null
                                onRenameItem(entry, title)
                            },
                            enabled = !busy && title.isNotBlank(),
                            modifier = Modifier
                                .heightIn(min = MinimumTouchTarget)
                                .padding(start = EimirTheme.spacing.step2),
                        ) {
                            Text(stringResource(R.string.collection_item_save_changes))
                        }
                        TextButton(
                            onClick = { editingItemId = null },
                            enabled = !busy,
                            modifier = Modifier.heightIn(min = MinimumTouchTarget),
                        ) {
                            Text(stringResource(R.string.collection_item_cancel))
                        }
                    }
                } else {
                    Row(
                        modifier = Modifier
                            .padding(EimirTheme.spacing.cardPadding)
                            .fillMaxWidth(),
                        verticalAlignment = Alignment.CenterVertically,
                    ) {
                        Checkbox(
                            checked = entry.completed,
                            onCheckedChange = { onToggleCompleted(entry) },
                            enabled = !busy,
                        )
                        Text(
                            text = entry.title,
                            style = MaterialTheme.typography.bodyLarge,
                            color = EimirTheme.colors.textPrimary,
                            textDecoration = if (entry.completed) TextDecoration.LineThrough else null,
                            modifier = Modifier.weight(1f).padding(start = EimirTheme.spacing.step2),
                        )
                        TextButton(
                            onClick = { editingItemId = entry.id.toString() },
                            enabled = !busy,
                            modifier = Modifier.heightIn(min = MinimumTouchTarget),
                        ) {
                            Text(stringResource(R.string.collection_item_edit))
                        }
                        TextButton(
                            onClick = { onMoveUp(entry) },
                            enabled = !busy && index > 0,
                            modifier = Modifier.heightIn(min = MinimumTouchTarget),
                        ) {
                            Text(stringResource(R.string.collection_item_move_up))
                        }
                        TextButton(
                            onClick = { onMoveDown(entry) },
                            enabled = !busy && index < items.lastIndex,
                            modifier = Modifier.heightIn(min = MinimumTouchTarget),
                        ) {
                            Text(stringResource(R.string.collection_item_move_down))
                        }
                        TextButton(
                            onClick = { onDeleteItem(entry) },
                            enabled = !busy,
                            modifier = Modifier.heightIn(min = MinimumTouchTarget),
                        ) {
                            Text(stringResource(R.string.collection_item_delete))
                        }
                    }
                }
            }
        }
    }
}
