package de.sidebyside.next.shell

import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.material3.DropdownMenu
import androidx.compose.material3.DropdownMenuItem
import androidx.compose.material3.ExperimentalMaterial3Api
import androidx.compose.material3.ExposedDropdownMenuBox
import androidx.compose.material3.ExposedDropdownMenuDefaults
import androidx.compose.material3.MenuAnchorType
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.saveable.rememberSaveable
import androidx.compose.runtime.setValue
import androidx.compose.ui.Modifier
import androidx.compose.ui.res.stringResource
import de.sidebyside.next.reference.R
import java.util.UUID
import sidebyside.api.models.PlaceDetail

/**
 * An optional Place, chosen from the couple's shared Places.
 *
 * Shared by every form that carries a `placeId` — Wish-to-Plan conversion,
 * direct Plan create/edit, Chapter create/edit — rather than each screen
 * inventing its own picker.
 */
@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun PlacePicker(
    places: List<PlaceDetail>,
    selectedPlaceId: UUID?,
    onSelect: (UUID?) -> Unit,
    busy: Boolean,
    modifier: Modifier = Modifier,
) {
    var open by rememberSaveable { mutableStateOf(false) }
    val selectedName = places.firstOrNull { it.id == selectedPlaceId }?.name

    ExposedDropdownMenuBox(expanded = open, onExpandedChange = { open = it }, modifier = modifier) {
        OutlinedTextField(
            value = selectedName ?: stringResource(R.string.place_picker_none),
            onValueChange = {},
            readOnly = true,
            enabled = !busy,
            label = { Text(stringResource(R.string.place_picker_label)) },
            trailingIcon = { ExposedDropdownMenuDefaults.TrailingIcon(expanded = open) },
            modifier = Modifier
                .fillMaxWidth()
                .menuAnchor(MenuAnchorType.PrimaryNotEditable),
        )
        DropdownMenu(expanded = open, onDismissRequest = { open = false }) {
            DropdownMenuItem(
                text = { Text(stringResource(R.string.place_picker_none)) },
                onClick = { onSelect(null); open = false },
            )
            for (place in places) {
                DropdownMenuItem(
                    text = { Text(place.name) },
                    onClick = { onSelect(place.id); open = false },
                )
            }
        }
    }
}
