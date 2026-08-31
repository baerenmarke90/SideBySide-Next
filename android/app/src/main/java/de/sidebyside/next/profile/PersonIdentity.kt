package de.sidebyside.next.profile

import android.graphics.Bitmap
import androidx.compose.foundation.Image
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Surface
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.produceState
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.asImageBitmap
import androidx.compose.ui.layout.ContentScale
import androidx.compose.ui.semantics.contentDescription
import androidx.compose.ui.semantics.semantics
import androidx.compose.ui.unit.Dp
import androidx.compose.ui.unit.dp
import de.sidebyside.next.design.SideBySideTheme
import de.sidebyside.next.story.decodeBounded
import java.util.Locale
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext

private const val AVATAR_MAX_DECODED_EDGE = 512

internal enum class PersonIdentitySize(val diameter: Dp) {
    SMALL(32.dp),
    MEDIUM(48.dp),
    LARGE(80.dp),
}

internal fun personInitials(displayName: String): String {
    val parts = displayName.trim().split(Regex("\\s+")).filter(String::isNotBlank)
    if (parts.isEmpty()) return "?"
    if (parts.size == 1) return parts.first().take(2).uppercase(Locale.GERMAN)
    return "${parts.first().take(1)}${parts.last().take(1)}".uppercase(Locale.GERMAN)
}

/**
 * One presentation primitive for self and partner identity.
 *
 * Avatar bytes never become a public URL. Decoding is bounded and runs away
 * from the UI thread. If decoding fails or no avatar is present, the same
 * deterministic initials fallback is used everywhere.
 */
@Composable
internal fun PersonIdentity(
    displayName: String,
    avatarBytes: ByteArray?,
    contentDescription: String,
    modifier: Modifier = Modifier,
    size: PersonIdentitySize = PersonIdentitySize.MEDIUM,
    showName: Boolean = true,
) {
    val bitmap by produceState<Bitmap?>(initialValue = null, avatarBytes) {
        value = null
        if (avatarBytes != null) {
            value = withContext(Dispatchers.Default) {
                decodeBounded(avatarBytes, AVATAR_MAX_DECODED_EDGE)
            }
        }
    }

    Row(
        modifier = modifier,
        horizontalArrangement = Arrangement.spacedBy(SideBySideTheme.spacing.step3),
        verticalAlignment = Alignment.CenterVertically,
    ) {
        Surface(
            modifier = Modifier
                .size(size.diameter)
                .clip(CircleShape),
            shape = CircleShape,
            color = SideBySideTheme.colors.surfaceSubtle,
            contentColor = SideBySideTheme.colors.textPrimary,
        ) {
            if (bitmap != null) {
                Image(
                    bitmap = bitmap!!.asImageBitmap(),
                    contentDescription = contentDescription,
                    contentScale = ContentScale.Crop,
                    modifier = Modifier.size(size.diameter),
                )
            } else {
                Box(
                    modifier = Modifier
                        .size(size.diameter)
                        .semantics { this.contentDescription = contentDescription },
                    contentAlignment = Alignment.Center,
                ) {
                    Text(
                        text = personInitials(displayName),
                        style = MaterialTheme.typography.titleMedium,
                        color = SideBySideTheme.colors.textPrimary,
                    )
                }
            }
        }
        if (showName) {
            Text(
                text = displayName,
                style = MaterialTheme.typography.titleMedium,
                color = SideBySideTheme.colors.textPrimary,
            )
        }
    }
}
