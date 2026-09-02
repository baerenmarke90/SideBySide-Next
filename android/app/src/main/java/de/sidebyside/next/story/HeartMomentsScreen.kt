package de.sidebyside.next.story

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.heightIn
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.widthIn
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.selection.selectable
import androidx.compose.foundation.selection.selectableGroup
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.AlertDialog
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
import androidx.compose.ui.platform.LocalConfiguration
import androidx.compose.ui.res.stringResource
import androidx.compose.ui.semantics.LiveRegionMode
import androidx.compose.ui.semantics.Role
import androidx.compose.ui.semantics.heading
import androidx.compose.ui.semantics.liveRegion
import androidx.compose.ui.semantics.semantics
import androidx.compose.ui.unit.Dp
import androidx.compose.ui.unit.dp
import de.sidebyside.next.design.MinimumTouchTarget
import de.sidebyside.next.design.SideBySideTheme
import de.sidebyside.next.reference.R
import de.sidebyside.next.shell.UiProblem
import de.sidebyside.next.shell.UiStatePanel
import java.time.format.DateTimeFormatter
import java.time.format.FormatStyle
import java.util.Locale
import java.util.UUID
import sidebyside.api.models.ContentVisibility
import sidebyside.api.models.HeartEmotion
import sidebyside.api.models.HeartMomentDetail

private val ReadingMeasure: Dp = 560.dp

/**
 * The account's own HeartMoments, private ones included.
 *
 * Nothing here decides who may see what — the server hands over only what this
 * account may read, and asking for someone else's private moments returns an
 * empty page rather than a refusal. What this screen must avoid is undoing
 * that: no count it works out for itself, no wording that separates "there is
 * none" from "not yours", and nothing kept past the session.
 */
@Composable
fun HeartMomentsScreen(
    moments: List<HeartMomentDetail>,
    busy: Boolean,
    problem: UiProblem?,
    statusMessage: String?,
    onBack: () -> Unit,
    onCreate: (text: String, emotion: HeartEmotion, happenedOn: String, visibility: ContentVisibility) -> Unit,
    onEdit: (id: UUID, text: String, emotion: HeartEmotion, happenedOn: String) -> Unit,
    onChangeVisibility: (UUID, ContentVisibility) -> Unit,
    onDelete: (UUID) -> Unit,
    modifier: Modifier = Modifier,
) {
    var text by rememberSaveable { mutableStateOf("") }
    var emotion by rememberSaveable { mutableStateOf(HeartEmotion.GRATEFUL) }
    var happenedOn by rememberSaveable { mutableStateOf("") }
    var keepPrivate by rememberSaveable { mutableStateOf(false) }
    var visibilityTarget by rememberSaveable { mutableStateOf<String?>(null) }
    var deleteTarget by rememberSaveable { mutableStateOf<String?>(null) }
    var editTarget by rememberSaveable { mutableStateOf<String?>(null) }

    LazyColumn(
        modifier = modifier.fillMaxWidth(),
        contentPadding = androidx.compose.foundation.layout.PaddingValues(
            SideBySideTheme.spacing.pageMargin,
        ),
        verticalArrangement = Arrangement.spacedBy(SideBySideTheme.spacing.step5),
    ) {
        item {
            TextButton(onClick = onBack) { Text(stringResource(R.string.heart_moment_back)) }
        }

        item {
            Column(verticalArrangement = Arrangement.spacedBy(SideBySideTheme.spacing.step2)) {
                Text(
                    text = stringResource(R.string.heart_moments_title),
                    style = MaterialTheme.typography.headlineMedium,
                    color = SideBySideTheme.colors.textPrimary,
                    modifier = Modifier.semantics { heading() },
                )
                Text(
                    text = stringResource(R.string.heart_moments_intro),
                    style = MaterialTheme.typography.bodyMedium,
                    color = SideBySideTheme.colors.textSecondary,
                    modifier = Modifier.widthIn(max = ReadingMeasure),
                )
            }
        }

        statusMessage?.let { message ->
            item {
                Text(
                    text = message,
                    style = MaterialTheme.typography.bodyMedium,
                    color = SideBySideTheme.colors.success,
                    modifier = Modifier.semantics { liveRegion = LiveRegionMode.Polite },
                )
            }
        }

        problem?.let { item { UiStatePanel(problem = it) } }

        item {
            NewHeartMoment(
                text = text,
                emotion = emotion,
                happenedOn = happenedOn,
                keepPrivate = keepPrivate,
                busy = busy,
                onTextChange = { text = it.take(500) },
                onEmotionChange = { emotion = it },
                onHappenedOnChange = { happenedOn = it },
                onKeepPrivateChange = { keepPrivate = it },
                onSave = {
                    onCreate(
                        text,
                        emotion,
                        happenedOn,
                        if (keepPrivate) ContentVisibility.PRIVATE else ContentVisibility.SHARED,
                    )
                    text = ""
                    happenedOn = ""
                },
            )
        }

        if (moments.isEmpty() && !busy) {
            item { EmptyHeartMoments() }
        }

        items(count = moments.size, key = { index -> moments[index].id.toString() }) { index ->
            val moment = moments[index]
            if (editTarget == moment.id.toString()) {
                EditHeartMoment(
                    moment = moment,
                    busy = busy,
                    onCancel = { editTarget = null },
                    onSave = { editedText, editedEmotion, editedHappenedOn ->
                        onEdit(moment.id, editedText, editedEmotion, editedHappenedOn)
                        editTarget = null
                    },
                )
            } else {
                HeartMomentCard(
                    moment = moment,
                    busy = busy,
                    onEdit = { editTarget = moment.id.toString() },
                    onChangeVisibility = { visibilityTarget = moment.id.toString() },
                    onDelete = { deleteTarget = moment.id.toString() },
                )
            }
        }
    }

    visibilityTarget?.let { id ->
        val moment = moments.firstOrNull { it.id.toString() == id }
        if (moment == null) {
            visibilityTarget = null
            return@let
        }
        val toPrivate = moment.visibility == ContentVisibility.SHARED
        AlertDialog(
            onDismissRequest = { visibilityTarget = null },
            title = {
                Text(
                    stringResource(
                        if (toPrivate) {
                            R.string.heart_moment_make_private_title
                        } else {
                            R.string.heart_moment_make_shared_title
                        },
                    ),
                )
            },
            text = {
                // Going private deletes the moment's comments and sharing it
                // again does not bring them back. That is said here, before it
                // happens, rather than reported afterwards.
                Text(
                    stringResource(
                        if (toPrivate) {
                            R.string.heart_moment_make_private_body
                        } else {
                            R.string.heart_moment_make_shared_body
                        },
                    ),
                )
            },
            confirmButton = {
                TextButton(
                    onClick = {
                        visibilityTarget = null
                        onChangeVisibility(
                            moment.id,
                            if (toPrivate) ContentVisibility.PRIVATE else ContentVisibility.SHARED,
                        )
                    },
                ) {
                    Text(
                        stringResource(
                            if (toPrivate) {
                                R.string.heart_moment_make_private
                            } else {
                                R.string.heart_moment_make_shared
                            },
                        ),
                    )
                }
            },
            dismissButton = {
                TextButton(onClick = { visibilityTarget = null }) {
                    Text(stringResource(R.string.heart_moment_cancel))
                }
            },
        )
    }

    deleteTarget?.let { id ->
        AlertDialog(
            onDismissRequest = { deleteTarget = null },
            title = { Text(stringResource(R.string.heart_moment_delete_title)) },
            text = { Text(stringResource(R.string.heart_moment_delete_body)) },
            confirmButton = {
                TextButton(
                    onClick = {
                        deleteTarget = null
                        moments.firstOrNull { it.id.toString() == id }?.let { onDelete(it.id) }
                    },
                ) {
                    Text(stringResource(R.string.heart_moment_delete))
                }
            },
            dismissButton = {
                TextButton(onClick = { deleteTarget = null }) {
                    Text(stringResource(R.string.heart_moment_cancel))
                }
            },
        )
    }
}

@Composable
private fun NewHeartMoment(
    text: String,
    emotion: HeartEmotion,
    happenedOn: String,
    keepPrivate: Boolean,
    busy: Boolean,
    onTextChange: (String) -> Unit,
    onEmotionChange: (HeartEmotion) -> Unit,
    onHappenedOnChange: (String) -> Unit,
    onKeepPrivateChange: (Boolean) -> Unit,
    onSave: () -> Unit,
) {
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
                text = stringResource(R.string.heart_moment_new),
                style = MaterialTheme.typography.titleMedium,
                color = SideBySideTheme.colors.textPrimary,
                modifier = Modifier.semantics { heading() },
            )
            OutlinedTextField(
                value = text,
                onValueChange = onTextChange,
                label = { Text(stringResource(R.string.heart_moment_text)) },
                minLines = 2,
                modifier = Modifier.fillMaxWidth(),
            )
            Text(
                text = stringResource(R.string.heart_moment_emotion),
                style = MaterialTheme.typography.labelLarge,
                color = SideBySideTheme.colors.textSecondary,
            )
            Column(Modifier.selectableGroup()) {
                for (option in HeartEmotion.entries) {
                    Row(
                        modifier = Modifier
                            .fillMaxWidth()
                            .heightIn(min = MinimumTouchTarget)
                            .selectable(
                                selected = option == emotion,
                                enabled = !busy,
                                role = Role.RadioButton,
                                onClick = { onEmotionChange(option) },
                            ),
                        verticalAlignment = Alignment.CenterVertically,
                    ) {
                        RadioButton(selected = option == emotion, onClick = null)
                        Text(
                            text = stringResource(option.labelRes()),
                            style = MaterialTheme.typography.bodyLarge,
                            color = SideBySideTheme.colors.textPrimary,
                            modifier = Modifier.padding(start = SideBySideTheme.spacing.step3),
                        )
                    }
                }
            }
            OutlinedTextField(
                value = happenedOn,
                onValueChange = onHappenedOnChange,
                label = { Text(stringResource(R.string.heart_moment_happened_on)) },
                singleLine = true,
                modifier = Modifier.fillMaxWidth(),
            )
            Row(
                modifier = Modifier
                    .fillMaxWidth()
                    .heightIn(min = MinimumTouchTarget),
                verticalAlignment = Alignment.CenterVertically,
            ) {
                Checkbox(checked = keepPrivate, onCheckedChange = onKeepPrivateChange, enabled = !busy)
                Text(
                    text = stringResource(R.string.heart_moment_keep_private),
                    style = MaterialTheme.typography.bodyLarge,
                    color = SideBySideTheme.colors.textPrimary,
                    modifier = Modifier.padding(start = SideBySideTheme.spacing.step2),
                )
            }
            Button(
                onClick = onSave,
                enabled = !busy && text.isNotBlank() && happenedOn.isNotBlank(),
                modifier = Modifier.heightIn(min = MinimumTouchTarget),
            ) {
                Text(stringResource(R.string.heart_moment_save))
            }
        }
    }
}

/**
 * Inline edit form for an existing HeartMoment, replacing its card in place.
 *
 * Deliberately mirrors [NewHeartMoment]'s text/emotion/date fields without its
 * private-visibility checkbox: visibility is [HeartMomentsScreen.onChangeVisibility]'s
 * own separate, destructive operation, never a side effect of this save.
 */
@Composable
private fun EditHeartMoment(
    moment: HeartMomentDetail,
    busy: Boolean,
    onCancel: () -> Unit,
    onSave: (text: String, emotion: HeartEmotion, happenedOn: String) -> Unit,
) {
    var text by rememberSaveable(moment.id) { mutableStateOf(moment.text) }
    var emotion by rememberSaveable(moment.id) { mutableStateOf(moment.emotion) }
    var happenedOn by rememberSaveable(moment.id) { mutableStateOf(moment.happenedOn.toString()) }

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
                text = stringResource(R.string.heart_moment_edit),
                style = MaterialTheme.typography.titleMedium,
                color = SideBySideTheme.colors.textPrimary,
                modifier = Modifier.semantics { heading() },
            )
            OutlinedTextField(
                value = text,
                onValueChange = { text = it.take(500) },
                label = { Text(stringResource(R.string.heart_moment_text)) },
                minLines = 2,
                modifier = Modifier.fillMaxWidth(),
            )
            Text(
                text = stringResource(R.string.heart_moment_emotion),
                style = MaterialTheme.typography.labelLarge,
                color = SideBySideTheme.colors.textSecondary,
            )
            Column(Modifier.selectableGroup()) {
                for (option in HeartEmotion.entries) {
                    Row(
                        modifier = Modifier
                            .fillMaxWidth()
                            .heightIn(min = MinimumTouchTarget)
                            .selectable(
                                selected = option == emotion,
                                enabled = !busy,
                                role = Role.RadioButton,
                                onClick = { emotion = option },
                            ),
                        verticalAlignment = Alignment.CenterVertically,
                    ) {
                        RadioButton(selected = option == emotion, onClick = null)
                        Text(
                            text = stringResource(option.labelRes()),
                            style = MaterialTheme.typography.bodyLarge,
                            color = SideBySideTheme.colors.textPrimary,
                            modifier = Modifier.padding(start = SideBySideTheme.spacing.step3),
                        )
                    }
                }
            }
            OutlinedTextField(
                value = happenedOn,
                onValueChange = { happenedOn = it },
                label = { Text(stringResource(R.string.heart_moment_happened_on)) },
                singleLine = true,
                modifier = Modifier.fillMaxWidth(),
            )
            Row(horizontalArrangement = Arrangement.spacedBy(SideBySideTheme.spacing.step3)) {
                Button(
                    onClick = { onSave(text, emotion, happenedOn) },
                    enabled = !busy && text.isNotBlank() && happenedOn.isNotBlank(),
                    modifier = Modifier.heightIn(min = MinimumTouchTarget),
                ) {
                    Text(stringResource(R.string.heart_moment_save_changes))
                }
                TextButton(
                    onClick = onCancel,
                    enabled = !busy,
                    modifier = Modifier.heightIn(min = MinimumTouchTarget),
                ) {
                    Text(stringResource(R.string.heart_moment_cancel))
                }
            }
        }
    }
}

@Composable
private fun HeartMomentCard(
    moment: HeartMomentDetail,
    busy: Boolean,
    onEdit: () -> Unit,
    onChangeVisibility: () -> Unit,
    onDelete: () -> Unit,
) {
    val locale: Locale = LocalConfiguration.current.locales[0]
    val private = moment.visibility == ContentVisibility.PRIVATE
    Surface(
        shape = RoundedCornerShape(SideBySideTheme.radii.card),
        color = if (private) SideBySideTheme.colors.privateSurface else SideBySideTheme.colors.surface,
        modifier = Modifier.fillMaxWidth(),
    ) {
        Column(
            modifier = Modifier.padding(SideBySideTheme.spacing.cardPadding),
            verticalArrangement = Arrangement.spacedBy(SideBySideTheme.spacing.step3),
        ) {
            // The state is carried by words, not only by the card's colour, so
            // it survives a colour-blind reading and a screen reader.
            Text(
                text = stringResource(
                    if (private) {
                        R.string.heart_moment_visibility_private
                    } else {
                        R.string.heart_moment_visibility_shared
                    },
                ),
                style = MaterialTheme.typography.labelSmall,
                color = if (private) SideBySideTheme.colors.private else SideBySideTheme.colors.shared,
            )
            Text(
                text = moment.text,
                style = MaterialTheme.typography.bodyLarge,
                color = SideBySideTheme.colors.textPrimary,
                modifier = Modifier.widthIn(max = ReadingMeasure),
            )
            Text(
                text = moment.happenedOn.format(
                    DateTimeFormatter.ofLocalizedDate(FormatStyle.LONG).withLocale(locale),
                ) + " · " + stringResource(moment.emotion.labelRes()),
                style = MaterialTheme.typography.bodySmall,
                color = SideBySideTheme.colors.textSecondary,
            )
            if (moment.capabilities.canEdit || moment.capabilities.canDelete) {
                Row(horizontalArrangement = Arrangement.spacedBy(SideBySideTheme.spacing.step3)) {
                    if (moment.capabilities.canEdit) {
                        TextButton(
                            onClick = onEdit,
                            enabled = !busy,
                            modifier = Modifier.heightIn(min = MinimumTouchTarget),
                        ) {
                            Text(stringResource(R.string.heart_moment_edit))
                        }
                        TextButton(
                            onClick = onChangeVisibility,
                            enabled = !busy,
                            modifier = Modifier.heightIn(min = MinimumTouchTarget),
                        ) {
                            Text(
                                stringResource(
                                    if (private) {
                                        R.string.heart_moment_make_shared
                                    } else {
                                        R.string.heart_moment_make_private
                                    },
                                ),
                            )
                        }
                    }
                    if (moment.capabilities.canDelete) {
                        TextButton(
                            onClick = onDelete,
                            enabled = !busy,
                            modifier = Modifier.heightIn(min = MinimumTouchTarget),
                        ) {
                            Text(stringResource(R.string.heart_moment_delete))
                        }
                    }
                }
            }
        }
    }
}

@Composable
private fun EmptyHeartMoments() {
    Column(
        verticalArrangement = Arrangement.spacedBy(SideBySideTheme.spacing.step2),
        modifier = Modifier.widthIn(max = ReadingMeasure),
    ) {
        Text(
            text = stringResource(R.string.heart_moments_empty_title),
            style = MaterialTheme.typography.titleMedium,
            color = SideBySideTheme.colors.textPrimary,
            modifier = Modifier.semantics { heading() },
        )
        Text(
            text = stringResource(R.string.heart_moments_empty_body),
            style = MaterialTheme.typography.bodyMedium,
            color = SideBySideTheme.colors.textSecondary,
        )
    }
}

internal fun HeartEmotion.labelRes(): Int = when (this) {
    HeartEmotion.LOVED -> R.string.heart_emotion_loved
    HeartEmotion.SEEN -> R.string.heart_emotion_seen
    HeartEmotion.APPRECIATED -> R.string.heart_emotion_appreciated
    HeartEmotion.SUPPORTED -> R.string.heart_emotion_supported
    HeartEmotion.GRATEFUL -> R.string.heart_emotion_grateful
    HeartEmotion.HAPPY -> R.string.heart_emotion_happy
}
