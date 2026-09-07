package de.sidebyside.next.design

import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.res.stringResource
import androidx.compose.ui.semantics.Role
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import de.sidebyside.next.reference.R

/**
 * Renders the shared space identity with partner avatars, presence indicator,
 * and relationship duration.
 */
@Composable
fun CouplePresence(
    spaceName: String,
    userName: String,
    partnerName: String?,
    modifier: Modifier = Modifier,
    presenceState: PartnerPresenceState = PartnerPresenceState.CONNECTED,
    statusText: String? = null,
    relationshipDuration: String? = null,
    onDurationClick: (() -> Unit)? = null,
    onInviteClick: (() -> Unit)? = null,
    actionContent: (@Composable () -> Unit)? = null,
) {
    val displayStatus = statusText ?: when (presenceState) {
        PartnerPresenceState.CONNECTED -> stringResource(R.string.relationship_presence_connected)
        PartnerPresenceState.WAITING -> stringResource(R.string.relationship_presence_waiting)
        PartnerPresenceState.OFFLINE -> stringResource(R.string.relationship_presence_offline)
    }

    val statusColor = when (presenceState) {
        PartnerPresenceState.CONNECTED -> SideBySideTheme.colors.shared
        PartnerPresenceState.WAITING -> SideBySideTheme.colors.brand
        PartnerPresenceState.OFFLINE -> SideBySideTheme.colors.textMuted
    }

    Box(
        modifier = modifier
            .fillMaxWidth()
            .clip(RoundedCornerShape(SideBySideTheme.radii.large))
            .background(SideBySideTheme.colors.surface)
            .border(
                1.dp,
                SideBySideTheme.colors.borderSubtle,
                RoundedCornerShape(SideBySideTheme.radii.large),
            )
            .padding(16.dp),
    ) {
        Row(
            modifier = Modifier.fillMaxWidth(),
            horizontalArrangement = Arrangement.SpaceBetween,
            verticalAlignment = Alignment.CenterVertically,
        ) {
            Row(
                verticalAlignment = Alignment.CenterVertically,
                modifier = Modifier.weight(1f, fill = false),
            ) {
                PartnerAvatarPair(
                    userName = userName,
                    partnerName = partnerName,
                    presenceState = presenceState,
                    size = 52.dp,
                    onInviteClick = onInviteClick,
                )

                Spacer(modifier = Modifier.width(16.dp))

                Column {
                    Text(
                        text = spaceName,
                        style = SideBySideTheme.typography.titleLarge,
                        color = SideBySideTheme.colors.textPrimary,
                    )

                    Row(
                        verticalAlignment = Alignment.CenterVertically,
                        modifier = Modifier.padding(top = 2.dp),
                    ) {
                        Box(
                            modifier = Modifier
                                .size(8.dp)
                                .clip(CircleShape)
                                .background(statusColor),
                        )

                        Spacer(modifier = Modifier.width(6.dp))

                        Text(
                            text = displayStatus,
                            style = SideBySideTheme.typography.bodySmall,
                            color = SideBySideTheme.colors.textSecondary,
                        )

                        if (relationshipDuration != null) {
                            Text(
                                text = " · ",
                                style = SideBySideTheme.typography.bodySmall,
                                color = SideBySideTheme.colors.border,
                            )

                            Text(
                                text = relationshipDuration,
                                style = SideBySideTheme.typography.bodySmall,
                                color = SideBySideTheme.colors.brand,
                                fontWeight = FontWeight.SemiBold,
                                modifier = if (onDurationClick != null) {
                                    Modifier.clickable(
                                        role = Role.Button,
                                        onClickLabel = stringResource(R.string.relationship_presence_view_duration),
                                        onClick = onDurationClick,
                                    )
                                } else Modifier,
                            )
                        }
                    }
                }
            }

            if (actionContent != null) {
                Spacer(modifier = Modifier.width(12.dp))
                actionContent()
            }
        }
    }
}
