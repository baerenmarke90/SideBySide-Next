package de.sidebyside.next.story

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.heightIn
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.widthIn
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
import de.sidebyside.next.design.MinimumTouchTarget
import de.sidebyside.next.design.SideBySideTheme
import de.sidebyside.next.reference.R
import de.sidebyside.next.shell.UiProblem
import de.sidebyside.next.shell.UiStatePanel
import java.util.UUID
import sidebyside.api.models.CommentDetail

private val ReadingMeasure: Dp = 560.dp

/**
 * What has been said about a memory.
 *
 * A comment carries no `capabilities`, unlike the memory it hangs on, so
 * whether editing is offered is decided by comparing [accountId] with the
 * comment's author. That is a display hint and not an authorisation: the server
 * still refuses what it should, and such a refusal surfaces as a refusal rather
 * than as a defect.
 */
@Composable
fun MemoryComments(
    comments: List<CommentDetail>,
    accountId: UUID?,
    busy: Boolean,
    problem: UiProblem?,
    onAdd: (String) -> Unit,
    onEdit: (UUID, String) -> Unit,
    onDelete: (UUID) -> Unit,
    modifier: Modifier = Modifier,
    /** Null where the thread has no further pages. */
    onLoadMore: (() -> Unit)? = null,
) {
    var draft by rememberSaveable { mutableStateOf("") }
    var editingId by rememberSaveable { mutableStateOf<String?>(null) }
    var editingBody by rememberSaveable { mutableStateOf("") }
    var deleteTarget by rememberSaveable { mutableStateOf<String?>(null) }

    Column(
        modifier = modifier.fillMaxWidth(),
        verticalArrangement = Arrangement.spacedBy(SideBySideTheme.spacing.step4),
    ) {
        Text(
            text = stringResource(R.string.comments_title),
            style = MaterialTheme.typography.titleMedium,
            color = SideBySideTheme.colors.textPrimary,
            modifier = Modifier.semantics { heading() },
        )

        problem?.let { UiStatePanel(problem = it) }

        // An empty thread and a thread that failed to load must not look alike.
        if (comments.isEmpty() && problem == null && !busy) {
            Text(
                text = stringResource(R.string.comments_empty),
                style = MaterialTheme.typography.bodyMedium,
                color = SideBySideTheme.colors.textSecondary,
                modifier = Modifier.widthIn(max = ReadingMeasure),
            )
        }

        for (comment in comments) {
            val mine = accountId != null && comment.authorId == accountId
            Surface(
                shape = RoundedCornerShape(SideBySideTheme.radii.card),
                color = SideBySideTheme.colors.surfaceSubtle,
                modifier = Modifier.fillMaxWidth(),
            ) {
                Column(
                    modifier = Modifier.padding(SideBySideTheme.spacing.cardPadding),
                    verticalArrangement = Arrangement.spacedBy(SideBySideTheme.spacing.step2),
                ) {
                    Text(
                        text = comment.author.displayName,
                        style = MaterialTheme.typography.labelSmall,
                        color = SideBySideTheme.colors.brandStrong,
                    )
                    if (editingId == comment.id.toString()) {
                        OutlinedTextField(
                            value = editingBody,
                            onValueChange = { editingBody = it.take(2000) },
                            modifier = Modifier.fillMaxWidth(),
                            minLines = 2,
                        )
                        Row(
                            horizontalArrangement = Arrangement.spacedBy(
                                SideBySideTheme.spacing.step3,
                            ),
                        ) {
                            Button(
                                onClick = {
                                    onEdit(comment.id, editingBody)
                                    editingId = null
                                },
                                enabled = !busy && editingBody.isNotBlank(),
                                modifier = Modifier.heightIn(min = MinimumTouchTarget),
                            ) {
                                Text(stringResource(R.string.comments_save))
                            }
                            TextButton(onClick = { editingId = null }, enabled = !busy) {
                                Text(stringResource(R.string.comments_cancel))
                            }
                        }
                    } else {
                        Text(
                            text = comment.body,
                            style = MaterialTheme.typography.bodyMedium,
                            color = SideBySideTheme.colors.textPrimary,
                            modifier = Modifier.widthIn(max = ReadingMeasure),
                        )
                        if (mine) {
                            Row(
                                horizontalArrangement = Arrangement.spacedBy(
                                    SideBySideTheme.spacing.step3,
                                ),
                            ) {
                                TextButton(
                                    onClick = {
                                        editingId = comment.id.toString()
                                        editingBody = comment.body
                                    },
                                    enabled = !busy,
                                    modifier = Modifier.heightIn(min = MinimumTouchTarget),
                                ) {
                                    Text(stringResource(R.string.comments_edit))
                                }
                                TextButton(
                                    onClick = { deleteTarget = comment.id.toString() },
                                    enabled = !busy,
                                    modifier = Modifier.heightIn(min = MinimumTouchTarget),
                                ) {
                                    Text(stringResource(R.string.comments_delete))
                                }
                            }
                        }
                    }
                }
            }
        }

        onLoadMore?.let { more ->
            TextButton(onClick = more, enabled = !busy) {
                Text(
                    stringResource(if (busy) R.string.load_more_busy else R.string.load_more),
                )
            }
        }

        OutlinedTextField(
            value = draft,
            onValueChange = { draft = it.take(2000) },
            label = { Text(stringResource(R.string.comments_write)) },
            minLines = 2,
            modifier = Modifier.fillMaxWidth(),
        )
        Button(
            onClick = {
                onAdd(draft)
                draft = ""
            },
            enabled = !busy && draft.isNotBlank(),
            modifier = Modifier.heightIn(min = MinimumTouchTarget),
        ) {
            Text(stringResource(R.string.comments_send))
        }
    }

    deleteTarget?.let { id ->
        AlertDialog(
            onDismissRequest = { deleteTarget = null },
            title = { Text(stringResource(R.string.comments_delete_title)) },
            text = { Text(stringResource(R.string.comments_delete_body)) },
            confirmButton = {
                TextButton(
                    onClick = {
                        deleteTarget = null
                        comments.firstOrNull { it.id.toString() == id }?.let { onDelete(it.id) }
                    },
                ) {
                    Text(stringResource(R.string.comments_delete))
                }
            },
            dismissButton = {
                TextButton(onClick = { deleteTarget = null }) {
                    Text(stringResource(R.string.comments_cancel))
                }
            },
        )
    }
}
