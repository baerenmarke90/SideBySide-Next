package de.sidebyside.next.design

import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.offset
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.semantics.Role
import androidx.compose.ui.semantics.contentDescription
import androidx.compose.ui.semantics.semantics
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.Dp
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.compose.ui.res.stringResource
import de.sidebyside.next.reference.R
import de.sidebyside.next.profile.personInitials

enum class PartnerPresenceState {
    CONNECTED,
    WAITING,
    OFFLINE,
}

/**
 * Renders an overlapping pair of partner avatars with accessible group semantics
 * and an optional presence state pip.
 */
@Composable
fun PartnerAvatarPair(
    userName: String,
    partnerName: String?,
    modifier: Modifier = Modifier,
    presenceState: PartnerPresenceState = PartnerPresenceState.CONNECTED,
    size: Dp = 48.dp,
    onInviteClick: (() -> Unit)? = null,
) {
    val description = if (partnerName != null) {
        stringResource(R.string.relationship_partner_pair_connected, userName, partnerName)
    } else {
        stringResource(R.string.relationship_partner_pair_waiting, userName)
    }

    Box(
        modifier = modifier.semantics(mergeDescendants = true) {
            contentDescription = description
        },
        contentAlignment = Alignment.CenterStart,
    ) {
        Row(verticalAlignment = Alignment.CenterVertically) {
            // Primary avatar (User)
            SingleAvatarCircle(
                name = userName,
                size = size,
                backgroundColor = SideBySideTheme.colors.brandSurface,
                textColor = SideBySideTheme.colors.brandStrong,
                borderColor = SideBySideTheme.colors.surface,
            )

            // Secondary avatar (Partner or Waiting placeholder)
            if (partnerName != null) {
                Box(modifier = Modifier.offset(x = (-size * 0.28f))) {
                    SingleAvatarCircle(
                        name = partnerName,
                        size = size,
                        backgroundColor = SideBySideTheme.colors.surfaceSubtle,
                        textColor = SideBySideTheme.colors.textPrimary,
                        borderColor = SideBySideTheme.colors.surface,
                    )
                }
            } else {
                Box(
                    modifier = Modifier
                        .offset(x = (-size * 0.28f))
                        .size(size)
                        .clip(CircleShape)
                        .background(SideBySideTheme.colors.brandSurface)
                        .border(1.5.dp, SideBySideTheme.colors.brand, CircleShape)
                        .then(
                            if (onInviteClick != null) {
                                Modifier.clickable(
                                    role = Role.Button,
                                    onClickLabel = stringResource(R.string.relationship_partner_pair_invite),
                                    onClick = onInviteClick,
                                )
                            } else Modifier,
                        ),
                    contentAlignment = Alignment.Center,
                ) {
                    Text(
                        text = "+",
                        color = SideBySideTheme.colors.brandStrong,
                        style = SideBySideTheme.typography.titleMedium,
                    )
                }
            }
        }

        // Connected status indicator pip
        if (presenceState == PartnerPresenceState.CONNECTED) {
            val pipSize = (size * 0.26f).coerceIn(8.dp, 14.dp)
            Box(
                modifier = Modifier
                    .size(pipSize)
                    .align(Alignment.BottomEnd)
                    .clip(CircleShape)
                    .background(SideBySideTheme.colors.shared)
                    .border(2.dp, SideBySideTheme.colors.surface, CircleShape),
            )
        }
    }
}

@Composable
private fun SingleAvatarCircle(
    name: String,
    size: Dp,
    backgroundColor: Color,
    textColor: Color,
    borderColor: Color,
) {
    Box(
        modifier = Modifier
            .size(size)
            .clip(CircleShape)
            .background(backgroundColor)
            .border(2.dp, borderColor, CircleShape),
        contentAlignment = Alignment.Center,
    ) {
        val initials = personInitials(name)
        val fontSize = (size.value * 0.38f).sp
        Text(
            text = initials,
            color = textColor,
            fontSize = fontSize,
            fontWeight = FontWeight.Bold,
        )
    }
}
