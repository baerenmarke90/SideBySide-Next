package de.sidebyside.next.story

import android.graphics.Bitmap
import android.graphics.BitmapFactory
import androidx.compose.foundation.Image
import androidx.compose.foundation.background
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.produceState
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.asImageBitmap
import androidx.compose.ui.layout.ContentScale
import androidx.compose.ui.res.stringResource
import androidx.compose.ui.semantics.clearAndSetSemantics
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.ui.text.style.TextAlign
import de.sidebyside.next.design.SideBySideTheme
import de.sidebyside.next.reference.R
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext

/** Bounds how much of a photograph is decoded, whatever the camera produced. */
private const val MAX_DECODED_EDGE = 1440

/**
 * One Story photograph.
 *
 * A failed image is a placeholder, never an error that removes the entry it
 * belongs to: the title and the day are the record, and losing them because a
 * photograph would not load would be the worse failure.
 */
@Composable
fun StoryImage(
    image: StoryImageRef,
    store: StoryImageStore,
    generation: Long,
    modifier: Modifier = Modifier,
) {
    val bitmap by produceState<Bitmap?>(initialValue = null, image, generation) {
        val bytes = store.image(image)
        value = bytes?.let { withContext(Dispatchers.Default) { decodeBounded(it) } }
    }

    Box(
        modifier = modifier
            .clip(RoundedCornerShape(SideBySideTheme.radii.card))
            .background(SideBySideTheme.colors.surfaceSubtle),
        contentAlignment = Alignment.Center,
    ) {
        val loaded = bitmap
        if (loaded != null) {
            Image(
                bitmap = loaded.asImageBitmap(),
                // The photograph is described by the entry it sits in; naming
                // it again would read the same thing twice aloud.
                contentDescription = null,
                contentScale = ContentScale.Crop,
                modifier = Modifier.fillMaxSize(),
            )
        } else {
            Text(
                text = stringResource(R.string.story_image_unavailable),
                style = MaterialTheme.typography.labelSmall,
                color = SideBySideTheme.colors.textSecondary,
                textAlign = TextAlign.Center,
                modifier = Modifier.clearAndSetSemantics { },
            )
        }
    }
}

/**
 * Decodes at a bounded size.
 *
 * Phone cameras produce images far larger than any Story row, and decoding
 * them at full size is how a list of photographs becomes an out-of-memory
 * crash.
 */
internal fun decodeBounded(bytes: ByteArray, maxEdge: Int = MAX_DECODED_EDGE): Bitmap? {
    val bounds = BitmapFactory.Options().apply { inJustDecodeBounds = true }
    BitmapFactory.decodeByteArray(bytes, 0, bytes.size, bounds)

    val longestEdge = maxOf(bounds.outWidth, bounds.outHeight)
    if (longestEdge <= 0) return null

    var sample = 1
    while (longestEdge / sample > maxEdge) {
        sample *= 2
    }

    return BitmapFactory.decodeByteArray(
        bytes,
        0,
        bytes.size,
        BitmapFactory.Options().apply { inSampleSize = sample },
    )
}
