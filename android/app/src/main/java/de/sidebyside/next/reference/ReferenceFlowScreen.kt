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
import androidx.compose.ui.semantics.LiveRegionMode
import androidx.compose.ui.semantics.heading
import androidx.compose.ui.semantics.liveRegion
import androidx.compose.ui.semantics.semantics
import androidx.compose.ui.text.input.PasswordVisualTransformation
import androidx.compose.ui.unit.dp
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
) {
    var email by remember { mutableStateOf("") }
    var password by remember { mutableStateOf("") }
    var title by remember { mutableStateOf("") }
    var body by remember { mutableStateOf("") }
    var happenedOn by remember { mutableStateOf("") }

    LazyColumn(
        modifier = modifier.fillMaxSize().padding(20.dp),
        verticalArrangement = Arrangement.spacedBy(16.dp),
    ) {
        item {
            Column(verticalArrangement = Arrangement.spacedBy(8.dp)) {
                Text(
                    text = "SideBySide Next",
                    style = MaterialTheme.typography.headlineLarge,
                    modifier = Modifier.semantics { heading() },
                )
                Text(
                    text = "M2 · technischer Android-Referenzflow",
                    style = MaterialTheme.typography.labelLarge,
                )
                Text("Eine Erinnerung mit Bild in eurer gemeinsamen Story.")
            }
        }

        if (!state.configured) {
            item {
                Text(
                    text = "Der M2-Referenzflow ist operatorseitig noch nicht konfiguriert.",
                    color = MaterialTheme.colorScheme.error,
                    modifier = Modifier.semantics { liveRegion = LiveRegionMode.Assertive },
                )
            }
        } else if (!state.loggedIn) {
            item {
                Column(verticalArrangement = Arrangement.spacedBy(12.dp)) {
                    Text(
                        text = "Anmelden",
                        style = MaterialTheme.typography.headlineSmall,
                        modifier = Modifier.semantics { heading() },
                    )
                    OutlinedTextField(
                        value = email,
                        onValueChange = { email = it },
                        label = { Text("E-Mail") },
                        singleLine = true,
                        modifier = Modifier.fillMaxWidth(),
                    )
                    OutlinedTextField(
                        value = password,
                        onValueChange = { password = it },
                        label = { Text("Passwort") },
                        singleLine = true,
                        visualTransformation = PasswordVisualTransformation(),
                        modifier = Modifier.fillMaxWidth(),
                    )
                    Button(
                        onClick = { onLogin(email, password) },
                        enabled = !state.busy,
                        modifier = Modifier.fillMaxWidth().heightIn(min = 48.dp),
                    ) {
                        Text(if (state.busy) "Anmeldung läuft …" else "Anmelden")
                    }
                }
            }
        } else {
            item {
                Row(
                    modifier = Modifier.fillMaxWidth(),
                    horizontalArrangement = Arrangement.SpaceBetween,
                ) {
                    Text("Authentifiziert")
                    TextButton(onClick = onLogout, enabled = !state.busy) { Text("Abmelden") }
                }
            }

            item {
                Column(verticalArrangement = Arrangement.spacedBy(12.dp)) {
                    Text(
                        text = "Erinnerung festhalten",
                        style = MaterialTheme.typography.headlineSmall,
                        modifier = Modifier.semantics { heading() },
                    )
                    OutlinedTextField(
                        value = title,
                        onValueChange = { title = it.take(200) },
                        label = { Text("Titel") },
                        modifier = Modifier.fillMaxWidth(),
                    )
                    OutlinedTextField(
                        value = body,
                        onValueChange = { body = it },
                        label = { Text("Erinnerung") },
                        minLines = 3,
                        modifier = Modifier.fillMaxWidth(),
                    )
                    OutlinedTextField(
                        value = happenedOn,
                        onValueChange = { happenedOn = it },
                        label = { Text("Datum (JJJJ-MM-TT, optional)") },
                        singleLine = true,
                        modifier = Modifier.fillMaxWidth(),
                    )
                    Button(
                        onClick = onPickImage,
                        enabled = !state.busy,
                        modifier = Modifier.fillMaxWidth().heightIn(min = 48.dp),
                    ) {
                        Text(state.selectedImageName?.let { "Bild ausgewählt: $it" } ?: "Bild auswählen")
                    }
                    Button(
                        onClick = { onCreateMemory(title, body, happenedOn) },
                        enabled = !state.busy && state.selectedImageName != null,
                        modifier = Modifier.fillMaxWidth().heightIn(min = 48.dp),
                    ) {
                        Text(if (state.busy) "Wird gespeichert …" else "Erinnerung mit Bild speichern")
                    }
                }
            }

            if (state.lastMemoryTitle != null && state.lastImageBytes != null) {
                item {
                    Column(verticalArrangement = Arrangement.spacedBy(8.dp)) {
                        Text(
                            text = "Zuletzt gespeichert",
                            style = MaterialTheme.typography.headlineSmall,
                            modifier = Modifier.semantics { heading() },
                        )
                        val bitmap = remember(state.lastImageBytes) {
                            BitmapFactory.decodeByteArray(state.lastImageBytes, 0, state.lastImageBytes.size)
                        }
                        if (bitmap != null) {
                            Image(
                                bitmap = bitmap.asImageBitmap(),
                                contentDescription = "Bild zur zuletzt gespeicherten Erinnerung",
                                modifier = Modifier.fillMaxWidth(),
                            )
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
                        text = "Gemeinsame Story",
                        style = MaterialTheme.typography.headlineSmall,
                        modifier = Modifier.semantics { heading() },
                    )
                    TextButton(onClick = onRefreshStory, enabled = !state.busy) { Text("Aktualisieren") }
                }
            }

            if (state.storyItems.isEmpty()) {
                item { Text("Noch keine Einträge in eurer Story.") }
            } else {
                itemsIndexed(state.storyItems) { _, storyItem ->
                    Column(modifier = Modifier.fillMaxWidth().padding(vertical = 4.dp)) {
                        Text(storyItemLabel(storyItem), style = MaterialTheme.typography.titleSmall)
                        Text(storyItemDate(storyItem))
                    }
                }
            }
        }

        if (state.status.isNotBlank()) {
            item {
                Text(
                    text = state.status,
                    modifier = Modifier.semantics { liveRegion = LiveRegionMode.Polite },
                )
            }
        }
        state.error?.let { message ->
            item {
                Text(
                    text = message,
                    color = MaterialTheme.colorScheme.error,
                    modifier = Modifier.semantics { liveRegion = LiveRegionMode.Assertive },
                )
            }
        }
    }
}

internal fun storyItemLabel(item: StoryItem): String = when (item) {
    is StoryItem.MemoryWrapper -> "Erinnerung: ${item.value.memory.title}"
    is StoryItem.HeartMomentWrapper -> "Herzmoment"
    is StoryItem.MilestoneWrapper -> "Meilenstein: ${item.value.milestone.title}"
}

private fun storyItemDate(item: StoryItem): String = when (item) {
    is StoryItem.MemoryWrapper -> item.value.effectiveDate.toString()
    is StoryItem.HeartMomentWrapper -> item.value.effectiveDate.toString()
    is StoryItem.MilestoneWrapper -> item.value.effectiveDate.toString()
}
