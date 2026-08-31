package de.sidebyside.next.reference

import android.graphics.BitmapFactory
import androidx.compose.foundation.Image
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.heightIn
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.itemsIndexed
import androidx.compose.material3.Button
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.asImageBitmap
import androidx.compose.ui.res.stringResource
import androidx.compose.ui.semantics.LiveRegionMode
import androidx.compose.ui.semantics.heading
import androidx.compose.ui.semantics.liveRegion
import androidx.compose.ui.semantics.semantics
import androidx.compose.ui.unit.dp
import de.sidebyside.next.entry.EntryScreen
import java.time.format.DateTimeFormatter
import java.time.format.FormatStyle
import java.util.Locale
import sidebyside.api.models.StoryItem

@Composable
fun ReferenceFlowScreen(
    state: ReferenceUiState,
    onLogin: (String, String) -> Unit,
    onLogout: () -> Unit,
    onPickImage: () -> Unit,
    onCreateMemory: (String, String, String) -> Unit,
    onRefreshStory: () -> Unit,
    modifier: Modifier = Modifier,
    onRetryImage: (Long) -> Unit = { _ -> },
    onRemoveImage: (Long) -> Unit = { _ -> },
) {
    var title by remember { mutableStateOf("") }
    var body by remember { mutableStateOf("") }
    var happenedOn by remember { mutableStateOf("") }

    // Signed out, the product entry surface is the whole screen. It scrolls
    // itself, so it must not be nested inside the lazy list below.
    if (!state.loggedIn) {
        EntryScreen(
            onSignIn = onLogin,
            busy = state.busy,
            signInEnabled = state.configured,
            notice = if (state.configured) null else stringResource(R.string.ref_not_configured),
            modifier = modifier.fillMaxSize(),
        )
        return
    }

    LazyColumn(
        modifier = modifier.fillMaxSize().padding(20.dp),
        verticalArrangement = Arrangement.spacedBy(16.dp),
    ) {
        run {
            item {
                Column(verticalArrangement = Arrangement.spacedBy(8.dp)) {
                    Text(
                        text = stringResource(R.string.app_name),
                        style = MaterialTheme.typography.headlineSmall,
                        modifier = Modifier.semantics { heading() },
                    )
                    Text(
                        text = stringResource(R.string.ref_flow_subtitle),
                        style = MaterialTheme.typography.labelLarge,
                    )
                    Text(stringResource(R.string.ref_flow_intro))
                }
            }

            item {
                Row(
                    modifier = Modifier.fillMaxWidth(),
                    horizontalArrangement = Arrangement.SpaceBetween,
                ) {
                    Text(stringResource(R.string.ref_authenticated))
                    TextButton(onClick = onLogout, enabled = !state.busy) {
                        Text(stringResource(R.string.ref_logout))
                    }
                }
            }

            item {
                Column(verticalArrangement = Arrangement.spacedBy(12.dp)) {
                    Text(
                        text = stringResource(R.string.ref_memory_heading),
                        style = MaterialTheme.typography.headlineSmall,
                        modifier = Modifier.semantics { heading() },
                    )
                    OutlinedTextField(
                        value = title,
                        onValueChange = { title = it.take(200) },
                        label = { Text(stringResource(R.string.ref_title)) },
                        modifier = Modifier.fillMaxWidth(),
                    )
                    OutlinedTextField(
                        value = body,
                        onValueChange = { body = it },
                        label = { Text(stringResource(R.string.ref_memory)) },
                        minLines = 3,
                        modifier = Modifier.fillMaxWidth(),
                    )
                    OutlinedTextField(
                        value = happenedOn,
                        onValueChange = { happenedOn = it },
                        label = { Text(stringResource(R.string.ref_date_optional)) },
                        singleLine = true,
                        modifier = Modifier.fillMaxWidth(),
                    )
                    Button(
                        onClick = onPickImage,
                        enabled = !state.busy,
                        modifier = Modifier.fillMaxWidth().heightIn(min = 48.dp),
                    ) {
                        Text(
                            stringResource(
                                if (state.draftImages.isEmpty()) {
                                    R.string.ref_images_select
                                } else {
                                    R.string.ref_images_add
                                },
                            ),
                        )
                    }

                    if (state.draftImages.isNotEmpty()) {
                        Text(stringResource(R.string.ref_images_selected_count, state.draftImages.size))
                        Text(stringResource(R.string.ref_image_preview_notice))
                        state.draftImages.forEachIndexed { index, draft ->
                            Column(
                                modifier = Modifier.fillMaxWidth().padding(vertical = 4.dp),
                                verticalArrangement = Arrangement.spacedBy(8.dp),
                            ) {
                                Text(
                                    text = stringResource(
                                        R.string.ref_image_item_title,
                                        index + 1,
                                        draft.displayName,
                                    ),
                                    style = MaterialTheme.typography.titleSmall,
                                )
                                val selectedBitmap = remember(draft.id, draft.bytes) {
                                    BitmapFactory.decodeByteArray(draft.bytes, 0, draft.bytes.size)
                                }
                                if (selectedBitmap != null) {
                                    Image(
                                        bitmap = selectedBitmap.asImageBitmap(),
                                        contentDescription = stringResource(
                                            R.string.ref_image_preview_description,
                                            draft.displayName,
                                        ),
                                        modifier = Modifier.fillMaxWidth(),
                                    )
                                }
                                Text(
                                    text = stringResource(
                                        when (draft.uploadState) {
                                            DraftUploadState.UPLOADING -> R.string.ref_image_uploading
                                            DraftUploadState.VALIDATING -> R.string.ref_image_validating
                                            DraftUploadState.READY -> R.string.ref_image_ready
                                            DraftUploadState.FAILED -> R.string.ref_image_failed
                                        },
                                    ),
                                    color = if (draft.uploadState == DraftUploadState.FAILED) {
                                        MaterialTheme.colorScheme.error
                                    } else {
                                        MaterialTheme.colorScheme.onSurfaceVariant
                                    },
                                    modifier = Modifier.semantics { liveRegion = LiveRegionMode.Polite },
                                )
                                Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                                    if (draft.uploadState == DraftUploadState.FAILED) {
                                        TextButton(
                                            onClick = { onRetryImage(draft.id) },
                                            enabled = !state.busy,
                                        ) {
                                            Text(stringResource(R.string.ref_image_retry))
                                        }
                                    }
                                    TextButton(
                                        onClick = { onRemoveImage(draft.id) },
                                        enabled = !state.busy,
                                    ) {
                                        Text(stringResource(R.string.ref_image_remove))
                                    }
                                }
                            }
                        }
                    }

                    val imagesReadyToSave = state.draftImages.all {
                        it.uploadState == DraftUploadState.READY
                    }
                    Button(
                        onClick = { onCreateMemory(title, body, happenedOn) },
                        enabled = !state.busy && title.isNotBlank() && imagesReadyToSave,
                        modifier = Modifier.fillMaxWidth().heightIn(min = 48.dp),
                    ) {
                        Text(
                            stringResource(
                                if (state.busy) R.string.ref_memory_saving else R.string.ref_memory_save,
                            ),
                        )
                    }
                }
            }

            if (state.lastMemoryTitle != null) {
                item {
                    Column(verticalArrangement = Arrangement.spacedBy(8.dp)) {
                        Text(
                            text = stringResource(R.string.ref_last_saved),
                            style = MaterialTheme.typography.headlineSmall,
                            modifier = Modifier.semantics { heading() },
                        )
                        state.lastImageBytes?.let { imageBytes ->
                            val bitmap = remember(imageBytes) {
                                BitmapFactory.decodeByteArray(imageBytes, 0, imageBytes.size)
                            }
                            if (bitmap != null) {
                                Image(
                                    bitmap = bitmap.asImageBitmap(),
                                    contentDescription = stringResource(R.string.ref_last_saved_image_description),
                                    modifier = Modifier.fillMaxWidth(),
                                )
                            }
                        }
                        Text(state.lastMemoryTitle, style = MaterialTheme.typography.titleMedium)
                        state.lastMemoryBody?.let { Text(it) }
                    }
                }
            }

            item {
                Row(
                    modifier = Modifier.fillMaxWidth(),
                    horizontalArrangement = Arrangement.SpaceBetween,
                ) {
                    Text(
                        text = stringResource(R.string.ref_story_heading),
                        style = MaterialTheme.typography.headlineSmall,
                        modifier = Modifier.semantics { heading() },
                    )
                    TextButton(onClick = onRefreshStory, enabled = !state.busy) {
                        Text(stringResource(R.string.ref_refresh))
                    }
                }
            }

            if (state.storyItems.isEmpty()) {
                item { Text(stringResource(R.string.ref_story_empty)) }
            } else {
                itemsIndexed(state.storyItems) { _, storyItem ->
                    Column(modifier = Modifier.fillMaxWidth().padding(vertical = 4.dp)) {
                        Text(storyItemLabel(storyItem).resolve(), style = MaterialTheme.typography.titleSmall)
                        Text(storyItemDate(storyItem))
                    }
                }
            }
        }

        state.status?.let { message ->
            item {
                Text(
                    text = message.resolve(),
                    modifier = Modifier.semantics { liveRegion = LiveRegionMode.Polite },
                )
            }
        }
        state.error?.let { message ->
            item {
                Text(
                    text = message.resolve(),
                    color = MaterialTheme.colorScheme.error,
                    modifier = Modifier.semantics { liveRegion = LiveRegionMode.Assertive },
                )
            }
        }
    }
}

@Composable
private fun UiMessage.resolve(): String = stringResource(resourceId, *args.toTypedArray())

internal fun storyItemLabel(item: StoryItem): UiMessage = when (item) {
    is StoryItem.MemoryWrapper -> UiMessage(R.string.ref_story_memory, listOf(item.value.memory.title))
    is StoryItem.HeartMomentWrapper -> UiMessage(R.string.ref_story_heart_moment)
    is StoryItem.MilestoneWrapper -> UiMessage(R.string.ref_story_milestone, listOf(item.value.milestone.title))
}

internal fun storyItemDate(item: StoryItem, locale: Locale = Locale.getDefault()): String {
    val date = when (item) {
        is StoryItem.MemoryWrapper -> item.value.effectiveDate
        is StoryItem.HeartMomentWrapper -> item.value.effectiveDate
        is StoryItem.MilestoneWrapper -> item.value.effectiveDate
    }
    return DateTimeFormatter.ofLocalizedDate(FormatStyle.MEDIUM).withLocale(locale).format(date)
}
