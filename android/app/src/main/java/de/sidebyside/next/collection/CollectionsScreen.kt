package de.sidebyside.next.collection

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
import androidx.compose.material3.AlertDialog
import androidx.compose.material3.Button
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
import androidx.compose.ui.res.stringResource
import androidx.compose.ui.semantics.heading
import androidx.compose.ui.semantics.semantics
import androidx.compose.ui.unit.Dp
import androidx.compose.ui.unit.dp
import de.sidebyside.next.design.SideBySideDisplayFamily
import de.sidebyside.next.design.MinimumTouchTarget
import de.sidebyside.next.design.SideBySideTheme
import de.sidebyside.next.reference.R
import de.sidebyside.next.shell.UiProblem
import de.sidebyside.next.shell.UiStatePanel
import sidebyside.api.models.CollectionDetail

private val ReadingMeasure: Dp = 560.dp

/**
 * The couple's shared lists, visible to both partners. Each card opens onto
 * [CollectionDetailScreen] for its items.
 */
@Composable
fun CollectionsScreen(
    collections: List<CollectionDetail>,
    busy: Boolean,
    problem: UiProblem?,
    onBack: () -> Unit,
    onOpen: (CollectionDetail) -> Unit,
    onAdd: (title: String) -> Unit,
    onEdit: (collection: CollectionDetail, title: String) -> Unit,
    onDelete: (CollectionDetail) -> Unit,
    modifier: Modifier = Modifier,
    /** Non-null only while [collections] is a stale M2-D18 cache fallback. */
    cachedAt: java.time.Instant? = null,
) {
    var editing by rememberSaveable { mutableStateOf<String?>(null) }
    var deleting by rememberSaveable { mutableStateOf<String?>(null) }

    LazyColumn(
        modifier = modifier.fillMaxWidth(),
        contentPadding = PaddingValues(SideBySideTheme.spacing.pageMargin),
        verticalArrangement = Arrangement.spacedBy(SideBySideTheme.spacing.step5),
    ) {
        item {
            TextButton(onClick = onBack) { Text(stringResource(R.string.memory_back)) }
        }

        cachedAt?.let { item { de.sidebyside.next.shell.CachedContentBanner(it) } }

        item {
            Column(verticalArrangement = Arrangement.spacedBy(SideBySideTheme.spacing.step2)) {
                Text(
                    text = stringResource(R.string.collections_title),
                    style = MaterialTheme.typography.headlineMedium.copy(fontFamily = SideBySideDisplayFamily),
                    color = SideBySideTheme.colors.textPrimary,
                    modifier = Modifier.semantics { heading() },
                )
                Text(
                    text = stringResource(R.string.collections_intro),
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
                Column(modifier = Modifier.padding(SideBySideTheme.spacing.cardPadding)) {
                    CollectionForm(
                        submitLabel = stringResource(R.string.collection_add),
                        busy = busy,
                        onSubmit = onAdd,
                    )
                }
            }
        }

        if (collections.isEmpty() && !busy) {
            item {
                Text(
                    text = stringResource(R.string.collections_empty),
                    style = MaterialTheme.typography.bodyMedium,
                    color = SideBySideTheme.colors.textSecondary,
                )
            }
        }

        items(count = collections.size, key = { index -> collections[index].id.toString() }) { index ->
            val collection = collections[index]
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
                        text = collection.title,
                        style = MaterialTheme.typography.titleMedium,
                        color = SideBySideTheme.colors.textPrimary,
                    )
                    Text(
                        text = stringResource(R.string.collection_item_count, collection.items.size),
                        style = MaterialTheme.typography.bodyMedium,
                        color = SideBySideTheme.colors.textSecondary,
                    )
                    Row(horizontalArrangement = Arrangement.spacedBy(SideBySideTheme.spacing.step3)) {
                        TextButton(
                            onClick = { onOpen(collection) },
                            enabled = !busy,
                            modifier = Modifier.heightIn(min = MinimumTouchTarget),
                        ) {
                            Text(stringResource(R.string.collection_open))
                        }
                        TextButton(
                            onClick = { editing = collection.id.toString() },
                            enabled = !busy,
                            modifier = Modifier.heightIn(min = MinimumTouchTarget),
                        ) {
                            Text(stringResource(R.string.collection_edit))
                        }
                        TextButton(
                            onClick = { deleting = collection.id.toString() },
                            enabled = !busy,
                            modifier = Modifier.heightIn(min = MinimumTouchTarget),
                        ) {
                            Text(stringResource(R.string.collection_delete))
                        }
                    }
                }
            }
        }
    }

    editing?.let { id ->
        val target = collections.firstOrNull { it.id.toString() == id }
        if (target == null) {
            editing = null
            return@let
        }
        AlertDialog(
            onDismissRequest = { editing = null },
            title = { Text(stringResource(R.string.collection_edit_title)) },
            text = {
                CollectionForm(
                    submitLabel = stringResource(R.string.collection_save_changes),
                    busy = busy,
                    initialTitle = target.title,
                    onSubmit = { title ->
                        editing = null
                        onEdit(target, title)
                    },
                )
            },
            confirmButton = {},
            dismissButton = {
                TextButton(onClick = { editing = null }) { Text(stringResource(R.string.collection_cancel)) }
            },
        )
    }

    deleting?.let { id ->
        val target = collections.firstOrNull { it.id.toString() == id }
        if (target == null) {
            deleting = null
            return@let
        }
        AlertDialog(
            onDismissRequest = { deleting = null },
            title = { Text(stringResource(R.string.collection_delete_title, target.title)) },
            text = { Text(stringResource(R.string.collection_delete_warning)) },
            confirmButton = {
                TextButton(
                    onClick = {
                        deleting = null
                        onDelete(target)
                    },
                ) {
                    Text(stringResource(R.string.collection_delete_confirm))
                }
            },
            dismissButton = {
                TextButton(onClick = { deleting = null }) { Text(stringResource(R.string.collection_cancel)) }
            },
        )
    }
}

@Composable
private fun CollectionForm(
    submitLabel: String,
    busy: Boolean,
    initialTitle: String = "",
    onSubmit: (title: String) -> Unit,
) {
    var title by rememberSaveable { mutableStateOf(initialTitle) }

    Column(verticalArrangement = Arrangement.spacedBy(SideBySideTheme.spacing.step3)) {
        OutlinedTextField(
            value = title,
            onValueChange = { title = it.take(200) },
            label = { Text(stringResource(R.string.collection_title_hint)) },
            enabled = !busy,
            modifier = Modifier.fillMaxWidth(),
        )
        Button(
            onClick = {
                onSubmit(title)
                title = ""
            },
            enabled = !busy && title.isNotBlank(),
            modifier = Modifier.heightIn(min = MinimumTouchTarget),
        ) {
            Text(submitLabel)
        }
    }
}
