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
        ?: throw IllegalArgumentException(context.getString(R.string.ref_image_type_unknown))
    require(mimeType.startsWith("image/")) { context.getString(R.string.ref_image_required) }

    var displayName = context.getString(R.string.ref_image_default_name)
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
        require(size <= MAX_REFERENCE_IMAGE_BYTES) { context.getString(R.string.ref_image_too_large) }
    }

    val bytes = resolver.openInputStream(uri)?.use { it.readBytes() }
        ?: throw IllegalArgumentException(context.getString(R.string.ref_image_open_failed))
    require(bytes.isNotEmpty()) { context.getString(R.string.ref_image_empty) }
    require(bytes.size <= MAX_REFERENCE_IMAGE_BYTES) { context.getString(R.string.ref_image_too_large) }

    SelectedImage(bytes = bytes, displayName = displayName, mimeType = mimeType)
}
