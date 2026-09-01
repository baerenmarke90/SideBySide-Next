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
                    text = stringResource(R.string.places_title),
                    style = MaterialTheme.typography.headlineMedium.copy(fontFamily = FrauncesFamily),
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

        problem?.let { item { UiStatePanel(problem = it) } }

        item {
            Surface(
                shape = RoundedCornerShape(SideBySideTheme.radii.card),
                color = SideBySideTheme.colors.surface,
                modifier = Modifier.fillMaxWidth(),
            ) {
                Column(modifier = Modifier.padding(SideBySideTheme.spacing.cardPadding)) {
                    PlaceForm(
                        submitLabel = stringResource(R.string.place_add),
                        busy = busy,
                        onSubmit = onAdd,
                    )
                }
            }
        }

        if (places.isEmpty() && !busy) {
            item {
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
                    if (place.capabilities.canEdit || place.capabilities.canDelete) {
                        Row(horizontalArrangement = Arrangement.spacedBy(SideBySideTheme.spacing.step3)) {
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
            onDismiss = { editing = null },
            onSave = { name, description, address, latitude, longitude ->
                editing = null
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

    // Mirrors the server's own PLACE_COORDINATE_PAIR_REQUIRED rule: either
    // both set or both blank, never exactly one.
    val coordinatesPaired = latitude.isBlank() == longitude.isBlank()

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
            isError = !coordinatesPaired,
            enabled = !busy,
            modifier = Modifier.fillMaxWidth(),
        )
        OutlinedTextField(
            value = longitude,
            onValueChange = { longitude = it },
            label = { Text(stringResource(R.string.place_longitude_hint)) },
            singleLine = true,
            isError = !coordinatesPaired,
            enabled = !busy,
            modifier = Modifier.fillMaxWidth(),
        )
        Text(
            text = stringResource(
                if (coordinatesPaired) R.string.place_coordinate_help else R.string.place_coordinate_error,
            ),
            style = MaterialTheme.typography.bodySmall,
            color = if (coordinatesPaired) {
                SideBySideTheme.colors.textSecondary
            } else {
                MaterialTheme.colorScheme.error
            },
        )
        Button(
            onClick = {
                onSubmit(name, description, address, latitude, longitude)
                name = ""
                description = ""
                address = ""
                latitude = ""
                longitude = ""
            },
            enabled = !busy && name.isNotBlank() && coordinatesPaired,
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
    onDismiss: () -> Unit,
    onSave: (name: String, description: String, address: String, latitude: String, longitude: String) -> Unit,
) {
    AlertDialog(
        onDismissRequest = onDismiss,
        title = { Text(stringResource(R.string.place_edit_title)) },
        text = {
            LazyColumn(modifier = Modifier.heightIn(max = 420.dp)) {
                item {
                    PlaceForm(
                        submitLabel = stringResource(R.string.place_save_changes),
                        busy = busy,
                        initialName = place.name,
                        initialDescription = place.description.orEmpty(),
                        initialAddress = place.address.orEmpty(),
                        initialLatitude = place.latitude?.toPlainString().orEmpty(),
                        initialLongitude = place.longitude?.toPlainString().orEmpty(),
                        onSubmit = { name, description, address, latitude, longitude ->
                            onSave(name, description, address, latitude, longitude)
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
