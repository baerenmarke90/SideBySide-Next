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
import de.sidebyside.next.design.FrauncesFamily
import de.sidebyside.next.design.MinimumTouchTarget
import de.sidebyside.next.design.SideBySideTheme
import de.sidebyside.next.reference.R
import de.sidebyside.next.shell.UiProblem
import de.sidebyside.next.shell.UiStatePanel
import sidebyside.api.models.ChapterDetail

private val ReadingMeasure: Dp = 560.dp

/**
 * The couple's shared Chapters — a curated span of their Story. Each card
 * opens onto [ChapterContentScreen] for its content.
 */
@Composable
fun ChaptersScreen(
    chapters: List<ChapterDetail>,
    busy: Boolean,
    problem: UiProblem?,
    onBack: () -> Unit,
    onOpen: (ChapterDetail) -> Unit,
    onAdd: (title: String, description: String, startOn: String, endOn: String) -> Unit,
    onEdit: (chapter: ChapterDetail, title: String, description: String, startOn: String, endOn: String) -> Unit,
    onDelete: (ChapterDetail) -> Unit,
    modifier: Modifier = Modifier,
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

        item {
            Column(verticalArrangement = Arrangement.spacedBy(SideBySideTheme.spacing.step2)) {
                Text(
                    text = stringResource(R.string.chapters_title),
                    style = MaterialTheme.typography.headlineMedium.copy(fontFamily = FrauncesFamily),
                    color = SideBySideTheme.colors.textPrimary,
                    modifier = Modifier.semantics { heading() },
                )
                Text(
                    text = stringResource(R.string.chapters_intro),
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
                    ChapterForm(
                        submitLabel = stringResource(R.string.chapter_add),
                        busy = busy,
                        onSubmit = onAdd,
                    )
                }
            }
        }

        if (chapters.isEmpty() && !busy) {
            item {
                Text(
                    text = stringResource(R.string.chapters_empty),
                    style = MaterialTheme.typography.bodyMedium,
                    color = SideBySideTheme.colors.textSecondary,
                )
            }
        }

        items(count = chapters.size, key = { index -> chapters[index].id.toString() }) { index ->
            val chapter = chapters[index]
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
                        text = chapter.title,
                        style = MaterialTheme.typography.titleMedium,
                        color = SideBySideTheme.colors.textPrimary,
                    )
                    chapter.description?.takeIf { it.isNotBlank() }?.let {
                        Text(
                            text = it,
                            style = MaterialTheme.typography.bodyMedium,
                            color = SideBySideTheme.colors.textSecondary,
                        )
                    }
                    val startOn = chapter.startOn
                    val endOn = chapter.endOn
                    Text(
                        text = if (startOn != null && endOn != null) {
                            stringResource(R.string.chapter_period, startOn.toString(), endOn.toString())
                        } else {
                            stringResource(R.string.chapter_no_period)
                        },
                        style = MaterialTheme.typography.labelMedium,
                        color = SideBySideTheme.colors.textSecondary,
                    )
                    Row(horizontalArrangement = Arrangement.spacedBy(SideBySideTheme.spacing.step3)) {
                        TextButton(
                            onClick = { onOpen(chapter) },
                            enabled = !busy,
                            modifier = Modifier.heightIn(min = MinimumTouchTarget),
                        ) {
                            Text(stringResource(R.string.chapter_open))
                        }
                        TextButton(
                            onClick = { editing = chapter.id.toString() },
                            enabled = !busy,
                            modifier = Modifier.heightIn(min = MinimumTouchTarget),
                        ) {
                            Text(stringResource(R.string.chapter_edit))
                        }
                        TextButton(
                            onClick = { deleting = chapter.id.toString() },
                            enabled = !busy,
                            modifier = Modifier.heightIn(min = MinimumTouchTarget),
                        ) {
                            Text(stringResource(R.string.chapter_delete))
                        }
                    }
                }
            }
        }
    }

    editing?.let { id ->
        val target = chapters.firstOrNull { it.id.toString() == id }
        if (target == null) {
            editing = null
            return@let
        }
        AlertDialog(
            onDismissRequest = { editing = null },
            title = { Text(stringResource(R.string.chapter_edit_title)) },
            text = {
                ChapterForm(
                    submitLabel = stringResource(R.string.chapter_save_changes),
                    busy = busy,
                    initialTitle = target.title,
                    initialDescription = target.description.orEmpty(),
                    initialStartOn = target.startOn?.toString().orEmpty(),
                    initialEndOn = target.endOn?.toString().orEmpty(),
                    onSubmit = { title, description, startOn, endOn ->
                        editing = null
                        onEdit(target, title, description, startOn, endOn)
                    },
                )
            },
            confirmButton = {},
            dismissButton = {
                TextButton(onClick = { editing = null }) { Text(stringResource(R.string.chapter_cancel)) }
            },
        )
    }

    deleting?.let { id ->
        val target = chapters.firstOrNull { it.id.toString() == id }
        if (target == null) {
            deleting = null
            return@let
        }
        AlertDialog(
            onDismissRequest = { deleting = null },
            title = { Text(stringResource(R.string.chapter_delete_title, target.title)) },
            text = { Text(stringResource(R.string.chapter_delete_warning)) },
            confirmButton = {
                TextButton(
                    onClick = {
                        deleting = null
                        onDelete(target)
                    },
                ) {
                    Text(stringResource(R.string.chapter_delete_confirm))
                }
            },
            dismissButton = {
                TextButton(onClick = { deleting = null }) { Text(stringResource(R.string.chapter_cancel)) }
            },
        )
    }
}

@Composable
private fun ChapterForm(
    submitLabel: String,
    busy: Boolean,
    initialTitle: String = "",
    initialDescription: String = "",
    initialStartOn: String = "",
    initialEndOn: String = "",
    onSubmit: (title: String, description: String, startOn: String, endOn: String) -> Unit,
) {
    var title by rememberSaveable { mutableStateOf(initialTitle) }
    var description by rememberSaveable { mutableStateOf(initialDescription) }
    var startOn by rememberSaveable { mutableStateOf(initialStartOn) }
    var endOn by rememberSaveable { mutableStateOf(initialEndOn) }

    Column(verticalArrangement = Arrangement.spacedBy(SideBySideTheme.spacing.step3)) {
        OutlinedTextField(
            value = title,
            onValueChange = { title = it.take(200) },
            label = { Text(stringResource(R.string.chapter_title_hint)) },
            enabled = !busy,
            modifier = Modifier.fillMaxWidth(),
        )
        OutlinedTextField(
            value = description,
            onValueChange = { description = it },
            label = { Text(stringResource(R.string.chapter_description_hint)) },
            enabled = !busy,
            modifier = Modifier.fillMaxWidth(),
        )
        OutlinedTextField(
            value = startOn,
            onValueChange = { startOn = it },
            label = { Text(stringResource(R.string.chapter_start_on_hint)) },
            singleLine = true,
            enabled = !busy,
            modifier = Modifier.fillMaxWidth(),
        )
        OutlinedTextField(
            value = endOn,
            onValueChange = { endOn = it },
            label = { Text(stringResource(R.string.chapter_end_on_hint)) },
            singleLine = true,
            enabled = !busy,
            modifier = Modifier.fillMaxWidth(),
        )
        Button(
            onClick = {
                onSubmit(title, description, startOn, endOn)
                title = ""
                description = ""
                startOn = ""
                endOn = ""
            },
            enabled = !busy && title.isNotBlank(),
            modifier = Modifier.heightIn(min = MinimumTouchTarget),
        ) {
            Text(submitLabel)
        }
    }
}
