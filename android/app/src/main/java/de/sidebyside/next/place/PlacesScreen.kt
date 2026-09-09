package de.sidebyside.next.place

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
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.saveable.rememberSaveable
import androidx.compose.runtime.setValue
import androidx.compose.ui.Modifier
import androidx.compose.ui.res.stringResource
import androidx.compose.ui.semantics.error
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
import sidebyside.api.models.PlaceDetail

private val ReadingMeasure: Dp = 560.dp

/**
 * The couple's shared places — a name is enough; coordinates are optional
 * and, per #355, never come from a map or the device's own location.
 */
@Composable
fun PlacesScreen(
    places: List<PlaceDetail>,
    busy: Boolean,
    problem: UiProblem?,
    onBack: () -> Unit,
    onAdd: (name: String, description: String, address: String, latitude: String, longitude: String) -> Unit,
    onEdit: (
        place: PlaceDetail,
        name: String,
        description: String,
        address: String,
        latitude: String,
        longitude: String,
    ) -> Unit,
    onDelete: (PlaceDetail) -> Unit,
    onOpenRelations: (PlaceDetail) -> Unit,
    modifier: Modifier = Modifier,
    /** Non-null only while [places] is a stale M2-D18 cache fallback. */
    cachedAt: java.time.Instant? = null,
) {
    var editing by rememberSaveable { mutableStateOf<String?>(null) }
    var deleting by rememberSaveable { mutableStateOf<String?>(null) }

    LazyColumn(
        modifier = modifier.fillMaxWidth(),
        contentPadding = PaddingValues(SideBySideTheme.spacing.pageMargin),
        verticalArrangement = Arrangement.spacedBy(SideBySideTheme.spacing.step5),
    ) {
        item(key = "back") {
            TextButton(onClick = onBack) { Text(stringResource(R.string.memory_back)) }
        }

        cachedAt?.let { item(key = "cachedAt") { de.sidebyside.next.shell.CachedContentBanner(it) } }

        item(key = "header") {
            Column(verticalArrangement = Arrangement.spacedBy(SideBySideTheme.spacing.step2)) {
                Text(
                    text = stringResource(R.string.places_title),
                    style = MaterialTheme.typography.headlineMedium.copy(fontFamily = SideBySideDisplayFamily),
                    color = SideBySideTheme.colors.textPrimary,
                    modifier = Modifier.semantics { heading() },
                )
                Text(
                    text = stringResource(R.string.places_intro),
                    style = MaterialTheme.typography.bodyMedium,
                    color = SideBySideTheme.colors.textSecondary,
                    modifier = Modifier.widthIn(max = ReadingMeasure),
                )
            }
        }

        // Keyed explicitly (like every other top-level item here): without a
        // stable key, this conditional item shifts every later item's
        // position-derived identity when `problem` toggles, which disposed
        // and recreated PlaceForm — including the in-flight `submitting`
        // state this fix (#684) depends on — right as an API error arrived.
        problem?.let { item(key = "problem") { UiStatePanel(problem = it) } }

        item(key = "form") {
            Surface(
                shape = RoundedCornerShape(SideBySideTheme.radii.card),
                color = SideBySideTheme.colors.surface,
                modifier = Modifier.fillMaxWidth(),
            ) {
                Column(modifier = Modifier.padding(SideBySideTheme.spacing.cardPadding)) {
                    PlaceForm(
                        submitLabel = stringResource(R.string.place_add),
                        busy = busy,
                        problem = problem,
                        onSubmit = onAdd,
                    )
                }
            }
        }

        if (places.isEmpty() && !busy) {
            item(key = "empty") {
                Text(
                    text = stringResource(R.string.places_empty),
                    style = MaterialTheme.typography.bodyMedium,
                    color = SideBySideTheme.colors.textSecondary,
                )
            }
        }

        items(count = places.size, key = { index -> places[index].id.toString() }) { index ->
            val place = places[index]
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
                        text = place.name,
                        style = MaterialTheme.typography.titleMedium,
                        color = SideBySideTheme.colors.textPrimary,
                    )
                    Text(
                        text = place.address?.takeIf { it.isNotBlank() }
                            ?: stringResource(R.string.place_no_address),
                        style = MaterialTheme.typography.bodyMedium,
                        color = SideBySideTheme.colors.textSecondary,
                    )
                    place.description?.takeIf { it.isNotBlank() }?.let {
                        Text(
                            text = it,
                            style = MaterialTheme.typography.bodyMedium,
                            color = SideBySideTheme.colors.textSecondary,
                        )
                    }
                    val latitude = place.latitude
                    val longitude = place.longitude
                    Text(
                        text = if (latitude != null && longitude != null) {
                            stringResource(R.string.place_coordinates, latitude.toPlainString(), longitude.toPlainString())
                        } else {
                            stringResource(R.string.place_no_coordinates)
                        },
                        style = MaterialTheme.typography.labelMedium,
                        color = SideBySideTheme.colors.textSecondary,
                    )
                    Row(horizontalArrangement = Arrangement.spacedBy(SideBySideTheme.spacing.step3)) {
                        TextButton(
                            onClick = { onOpenRelations(place) },
                            enabled = !busy,
                            modifier = Modifier.heightIn(min = MinimumTouchTarget),
                        ) {
                            Text(stringResource(R.string.place_relations))
                        }
                        if (place.capabilities.canEdit) {
                            TextButton(
                                onClick = { editing = place.id.toString() },
                                enabled = !busy,
                                modifier = Modifier.heightIn(min = MinimumTouchTarget),
                            ) {
                                Text(stringResource(R.string.place_edit))
                            }
                        }
                        if (place.capabilities.canDelete) {
                            TextButton(
                                onClick = { deleting = place.id.toString() },
                                enabled = !busy,
                                modifier = Modifier.heightIn(min = MinimumTouchTarget),
                            ) {
                                Text(stringResource(R.string.place_delete))
                            }
                        }
                    }
                }
            }
        }
    }

    editing?.let { id ->
        val target = places.firstOrNull { it.id.toString() == id }
        if (target == null) {
            editing = null
            return@let
        }
        EditPlaceDialog(
            place = target,
            busy = busy,
            problem = problem,
            onDismiss = { editing = null },
            onSave = { name, description, address, latitude, longitude ->
                onEdit(target, name, description, address, latitude, longitude)
            },
        )
    }

    deleting?.let { id ->
        val target = places.firstOrNull { it.id.toString() == id }
        if (target == null) {
            deleting = null
            return@let
        }
        AlertDialog(
            onDismissRequest = { deleting = null },
            title = { Text(stringResource(R.string.place_delete_title, target.name)) },
            text = { Text(stringResource(R.string.place_delete_warning)) },
            confirmButton = {
                TextButton(
                    onClick = {
                        deleting = null
                        onDelete(target)
                    },
                ) {
                    Text(stringResource(R.string.place_delete_confirm))
                }
            },
            dismissButton = {
                TextButton(onClick = { deleting = null }) { Text(stringResource(R.string.place_cancel)) }
            },
        )
    }
}

@Composable
private fun PlaceForm(
    submitLabel: String,
    busy: Boolean,
    problem: UiProblem?,
    initialName: String = "",
    initialDescription: String = "",
    initialAddress: String = "",
    initialLatitude: String = "",
    initialLongitude: String = "",
    onSubmit: (name: String, description: String, address: String, latitude: String, longitude: String) -> Unit,
) {
    var name by rememberSaveable { mutableStateOf(initialName) }
    var description by rememberSaveable { mutableStateOf(initialDescription) }
    var address by rememberSaveable { mutableStateOf(initialAddress) }
    var latitude by rememberSaveable { mutableStateOf(initialLatitude) }
    var longitude by rememberSaveable { mutableStateOf(initialLongitude) }

    // Tracks a submission this form itself started, so the draft is only
    // cleared once persistence is confirmed — never merely because the
    // button was tapped (#684). `busy`/`problem` are the ViewModel's shared
    // async-mutation state (also used by load/delete); this form only acts
    // on their transition while it is the one that set `submitting`.
    var submitting by rememberSaveable { mutableStateOf(false) }
    LaunchedEffect(busy, problem) {
        if (submitting && !busy) {
            submitting = false
            if (problem == null) {
                name = ""
                description = ""
                address = ""
                latitude = ""
                longitude = ""
            }
        }
    }

    val coordinateResult = parsePlaceCoordinates(latitude, longitude)
    val coordinatesValid = coordinateResult is PlaceCoordinatesResult.Valid
    val coordinateErrorText = when (coordinateResult) {
        is PlaceCoordinatesResult.Valid -> null
        PlaceCoordinatesResult.Unpaired -> stringResource(R.string.place_coordinate_error)
        PlaceCoordinatesResult.NotNumeric -> stringResource(R.string.place_coordinate_not_numeric)
        PlaceCoordinatesResult.OutOfRange -> stringResource(R.string.place_coordinate_out_of_range)
    }

    Column(verticalArrangement = Arrangement.spacedBy(SideBySideTheme.spacing.step3)) {
        OutlinedTextField(
            value = name,
            onValueChange = { name = it.take(200) },
            label = { Text(stringResource(R.string.place_name_hint)) },
            enabled = !busy,
            modifier = Modifier.fillMaxWidth(),
        )
        OutlinedTextField(
            value = description,
            onValueChange = { description = it },
            label = { Text(stringResource(R.string.place_description_hint)) },
            enabled = !busy,
            modifier = Modifier.fillMaxWidth(),
        )
        OutlinedTextField(
            value = address,
            onValueChange = { address = it },
            label = { Text(stringResource(R.string.place_address_hint)) },
            enabled = !busy,
            modifier = Modifier.fillMaxWidth(),
        )
        OutlinedTextField(
            value = latitude,
            onValueChange = { latitude = it },
            label = { Text(stringResource(R.string.place_latitude_hint)) },
            singleLine = true,
            isError = !coordinatesValid,
            enabled = !busy,
            modifier = Modifier.fillMaxWidth().semantics {
                coordinateErrorText?.let { error(it) }
            },
        )
        OutlinedTextField(
            value = longitude,
            onValueChange = { longitude = it },
            label = { Text(stringResource(R.string.place_longitude_hint)) },
            singleLine = true,
            isError = !coordinatesValid,
            enabled = !busy,
            modifier = Modifier.fillMaxWidth().semantics {
                coordinateErrorText?.let { error(it) }
            },
        )
        Text(
            text = coordinateErrorText ?: stringResource(R.string.place_coordinate_help),
            style = MaterialTheme.typography.bodySmall,
            color = if (coordinatesValid) {
                SideBySideTheme.colors.textSecondary
            } else {
                MaterialTheme.colorScheme.error
            },
        )
        Button(
            onClick = {
                if (name.isNotBlank() && coordinatesValid) {
                    onSubmit(name, description, address, latitude, longitude)
                    submitting = true
                }
            },
            enabled = !busy && name.isNotBlank() && coordinatesValid,
            modifier = Modifier.heightIn(min = MinimumTouchTarget),
        ) {
            Text(submitLabel)
        }
    }
}

@Composable
private fun EditPlaceDialog(
    place: PlaceDetail,
    busy: Boolean,
    problem: UiProblem?,
    onDismiss: () -> Unit,
    onSave: (name: String, description: String, address: String, latitude: String, longitude: String) -> Unit,
) {
    // The dialog itself decides when to close: only once a save it started
    // is confirmed to have persisted. A validation or API error leaves it
    // open with the entered values still visible (#684).
    var submitting by rememberSaveable { mutableStateOf(false) }
    LaunchedEffect(busy, problem) {
        if (submitting && !busy) {
            submitting = false
            if (problem == null) onDismiss()
        }
    }

    AlertDialog(
        onDismissRequest = onDismiss,
        title = { Text(stringResource(R.string.place_edit_title)) },
        text = {
            LazyColumn(modifier = Modifier.heightIn(max = 420.dp)) {
                item {
                    PlaceForm(
                        submitLabel = stringResource(R.string.place_save_changes),
                        busy = busy,
                        problem = problem,
                        initialName = place.name,
                        initialDescription = place.description.orEmpty(),
                        initialAddress = place.address.orEmpty(),
                        initialLatitude = place.latitude?.toPlainString().orEmpty(),
                        initialLongitude = place.longitude?.toPlainString().orEmpty(),
                        onSubmit = { name, description, address, latitude, longitude ->
                            onSave(name, description, address, latitude, longitude)
                            submitting = true
                        },
                    )
                }
            }
        },
        confirmButton = {},
        dismissButton = {
            TextButton(onClick = onDismiss) { Text(stringResource(R.string.place_cancel)) }
        },
    )
}
