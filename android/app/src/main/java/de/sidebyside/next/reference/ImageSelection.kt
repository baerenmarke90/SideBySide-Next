package de.sidebyside.next.reference

import android.content.Context
import android.net.Uri
import android.provider.OpenableColumns
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext

private const val MAX_REFERENCE_IMAGE_BYTES = 25 * 1024 * 1024

suspend fun loadSelectedImage(context: Context, uri: Uri): SelectedImage = withContext(Dispatchers.IO) {
    val resolver = context.contentResolver
    val mimeType = resolver.getType(uri)?.lowercase()
        ?: throw IllegalArgumentException("Der Bildtyp konnte nicht bestimmt werden.")
    require(mimeType.startsWith("image/")) { "Bitte ein Bild auswählen." }

    var displayName = "bild"
    var declaredSize: Long? = null
    resolver.query(uri, arrayOf(OpenableColumns.DISPLAY_NAME, OpenableColumns.SIZE), null, null, null)?.use { cursor ->
        if (cursor.moveToFirst()) {
            val nameIndex = cursor.getColumnIndex(OpenableColumns.DISPLAY_NAME)
            val sizeIndex = cursor.getColumnIndex(OpenableColumns.SIZE)
            if (nameIndex >= 0) displayName = cursor.getString(nameIndex) ?: displayName
            if (sizeIndex >= 0 && !cursor.isNull(sizeIndex)) declaredSize = cursor.getLong(sizeIndex)
        }
    }

    declaredSize?.let { size ->
        require(size <= MAX_REFERENCE_IMAGE_BYTES) { "Das Bild ist größer als 25 MiB." }
    }

    val bytes = resolver.openInputStream(uri)?.use { it.readBytes() }
        ?: throw IllegalArgumentException("Das Bild konnte nicht geöffnet werden.")
    require(bytes.isNotEmpty()) { "Das ausgewählte Bild ist leer." }
    require(bytes.size <= MAX_REFERENCE_IMAGE_BYTES) { "Das Bild ist größer als 25 MiB." }

    SelectedImage(bytes = bytes, displayName = displayName, mimeType = mimeType)
}
