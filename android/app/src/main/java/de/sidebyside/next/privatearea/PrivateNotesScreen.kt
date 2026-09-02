package de.sidebyside.next.privatearea

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
import androidx.compose.ui.Modifier
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
import sidebyside.api.models.PrivateNoteDetail

private val ReadingMeasure: Dp = 560.dp

/**
 * The account's own notes. Owner-only per #356: the server already filters
 * the list to what this account owns, so nothing here needs a client-side
 * ownership check on top of it.
 */
@Composable
fun PrivateNotesScreen(
    notes: List<PrivateNoteDetail>,
    busy: Boolean,
    problem: UiProblem?,
    onBack: () -> Unit,
    onAdd: (title: String, body: String, pinned: Boolean) -> Unit,
    onEdit: (note: PrivateNoteDetail, title: String, body: String, pinned: Boolean) -> Unit,
    onDelete: (PrivateNoteDetail) -> Unit,
    modifier: Modifier = Modifier,
    /** Non-null only while [notes] is a stale M2-D18 cache fallback. */
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
                    text = stringResource(R.string.private_notes_title),
                    style = MaterialTheme.typography.headlineMedium.copy(fontFamily = FrauncesFamily),
                    color = SideBySideTheme.colors.textPrimary,
                    modifier = Modifier.semantics { heading() },
                )
                Text(
                    text = stringResource(R.string.private_notes_intro),
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
                    PrivateNoteForm(
                        submitLabel = stringResource(R.string.private_note_add),
                        busy = busy,
                        onSubmit = onAdd,
                    )
                }
            }
        }

        if (notes.isEmpty() && !busy) {
            item {
                Text(
                    text = stringResource(R.string.private_notes_empty),
                    style = MaterialTheme.typography.bodyMedium,
                    color = SideBySideTheme.colors.textSecondary,
                )
            }
        }

        items(count = notes.size, key = { index -> notes[index].id.toString() }) { index ->
            val note = notes[index]
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
                        text = note.title,
                        style = MaterialTheme.typography.titleMedium,
                        color = SideBySideTheme.colors.textPrimary,
                    )
                    note.body.takeIf { it.isNotBlank() }?.let {
                        Text(
                            text = it,
                            style = MaterialTheme.typography.bodyMedium,
                            color = SideBySideTheme.colors.textSecondary,
                        )
                    }
                    Row(horizontalArrangement = Arrangement.spacedBy(SideBySideTheme.spacing.step3)) {
                        TextButton(
                            onClick = { editing = note.id.toString() },
                            enabled = !busy,
                            modifier = Modifier.heightIn(min = MinimumTouchTarget),
                        ) {
                            Text(stringResource(R.string.private_note_edit))
                        }
                        TextButton(
                            onClick = { deleting = note.id.toString() },
                            enabled = !busy,
                            modifier = Modifier.heightIn(min = MinimumTouchTarget),
                        ) {
                            Text(stringResource(R.string.private_note_delete))
                        }
                    }
                }
            }
        }
    }

    editing?.let { id ->
        val target = notes.firstOrNull { it.id.toString() == id }
        if (target == null) {
            editing = null
            return@let
        }
        EditPrivateNoteDialog(
            note = target,
            busy = busy,
            onDismiss = { editing = null },
            onSave = { title, body, pinned ->
                editing = null
                onEdit(target, title, body, pinned)
            },
        )
    }

    deleting?.let { id ->
        val target = notes.firstOrNull { it.id.toString() == id }
        if (target == null) {
            deleting = null
            return@let
        }
        AlertDialog(
            onDismissRequest = { deleting = null },
            title = { Text(stringResource(R.string.private_note_delete_title, target.title)) },
            text = { Text(stringResource(R.string.private_note_delete_warning)) },
            confirmButton = {
                TextButton(
                    onClick = {
                        deleting = null
                        onDelete(target)
                    },
                ) {
                    Text(stringResource(R.string.private_note_delete_confirm))
                }
            },
            dismissButton = {
                TextButton(onClick = { deleting = null }) { Text(stringResource(R.string.private_note_cancel)) }
            },
        )
    }
}

@Composable
private fun PrivateNoteForm(
    submitLabel: String,
    busy: Boolean,
    initialTitle: String = "",
    initialBody: String = "",
    initialPinned: Boolean = false,
    onSubmit: (title: String, body: String, pinned: Boolean) -> Unit,
) {
    var title by rememberSaveable { mutableStateOf(initialTitle) }
    var body by rememberSaveable { mutableStateOf(initialBody) }
    var pinned by rememberSaveable { mutableStateOf(initialPinned) }

    Column(verticalArrangement = Arrangement.spacedBy(SideBySideTheme.spacing.step3)) {
        OutlinedTextField(
            value = title,
            onValueChange = { title = it.take(200) },
            label = { Text(stringResource(R.string.private_note_title_hint)) },
            enabled = !busy,
            modifier = Modifier.fillMaxWidth(),
        )
        OutlinedTextField(
            value = body,
            onValueChange = { body = it },
            label = { Text(stringResource(R.string.private_note_body_hint)) },
            enabled = !busy,
            modifier = Modifier.fillMaxWidth(),
        )
        Row(
            verticalAlignment = androidx.compose.ui.Alignment.CenterVertically,
        ) {
            Checkbox(checked = pinned, onCheckedChange = { pinned = it }, enabled = !busy)
            Text(
                text = stringResource(R.string.private_note_pinned),
                style = MaterialTheme.typography.bodyMedium,
                color = SideBySideTheme.colors.textPrimary,
            )
        }
        Button(
            onClick = {
                onSubmit(title, body, pinned)
                title = ""
                body = ""
                pinned = false
            },
            enabled = !busy && title.isNotBlank(),
            modifier = Modifier.heightIn(min = MinimumTouchTarget),
        ) {
            Text(submitLabel)
        }
    }
}

@Composable
private fun EditPrivateNoteDialog(
    note: PrivateNoteDetail,
    busy: Boolean,
    onDismiss: () -> Unit,
    onSave: (title: String, body: String, pinned: Boolean) -> Unit,
) {
    AlertDialog(
        onDismissRequest = onDismiss,
        title = { Text(stringResource(R.string.private_note_edit_title)) },
        text = {
            LazyColumn(modifier = Modifier.heightIn(max = 420.dp)) {
                item {
                    PrivateNoteForm(
                        submitLabel = stringResource(R.string.private_note_save_changes),
                        busy = busy,
                        initialTitle = note.title,
                        initialBody = note.body,
                        initialPinned = note.pinned,
                        onSubmit = { title, body, pinned -> onSave(title, body, pinned) },
                    )
                }
            }
        },
        confirmButton = {},
        dismissButton = {
            TextButton(onClick = onDismiss) { Text(stringResource(R.string.private_note_cancel)) }
        },
    )
}
