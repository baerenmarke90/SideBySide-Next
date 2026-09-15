package de.eimir.app.design

import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.FlowRow
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.heightIn
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
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.unit.dp
import de.eimir.app.reference.R

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
    unboxed: Boolean = false,
    isCompact: Boolean = false,
) {
    val displayStatus = statusText ?: when (presenceState) {
        PartnerPresenceState.CONNECTED -> stringResource(R.string.relationship_presence_connected)
        PartnerPresenceState.WAITING -> stringResource(R.string.relationship_presence_waiting)
        PartnerPresenceState.OFFLINE -> stringResource(R.string.relationship_presence_offline)
    }

    val statusColor = when (presenceState) {
        PartnerPresenceState.CONNECTED -> EimirTheme.colors.shared
        PartnerPresenceState.WAITING -> EimirTheme.colors.brand
        PartnerPresenceState.OFFLINE -> EimirTheme.colors.textMuted
    }

    val containerModifier = if (unboxed) {
        modifier
            .fillMaxWidth()
            .padding(vertical = 12.dp)
    } else {
        modifier
            .fillMaxWidth()
            .clip(RoundedCornerShape(EimirTheme.radii.large))
            .background(EimirTheme.colors.surface)
            .border(
                1.dp,
                EimirTheme.colors.borderSubtle,
                RoundedCornerShape(EimirTheme.radii.large),
            )
            .padding(16.dp)
    }

    Box(
        modifier = containerModifier,
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
                    size = if (unboxed) (if (isCompact) 48.dp else 56.dp) else 52.dp,
                    onInviteClick = onInviteClick,
                )

                Spacer(modifier = Modifier.width(if (isCompact) 12.dp else 16.dp))

                Column {
                    Text(
                        text = spaceName,
                        style = if (unboxed) {
                            if (isCompact) {
                                EimirTheme.typography.titleLarge.copy(
                                    fontFamily = EimirDisplayFamily,
                                    fontWeight = FontWeight.Bold,
                                )
                            } else {
                                EimirTheme.typography.headlineMedium.copy(
                                    fontFamily = EimirDisplayFamily,
                                    fontWeight = FontWeight.Bold,
                                )
                            }
                        } else {
                            EimirTheme.typography.titleLarge.copy(
                                fontFamily = EimirDisplayFamily,
                                fontWeight = FontWeight.SemiBold,
                            )
                        },
                        color = EimirTheme.colors.textPrimary,
                        maxLines = 2,
                        overflow = TextOverflow.Ellipsis,
                    )

                    FlowRow(
                        verticalArrangement = Arrangement.spacedBy(0.dp),
                        horizontalArrangement = Arrangement.spacedBy(0.dp),
                        modifier = Modifier.padding(top = 2.dp),
                    ) {
                        Row(verticalAlignment = Alignment.CenterVertically) {
                            Box(
                                modifier = Modifier
                                    .size(8.dp)
                                    .clip(CircleShape)
                                    .background(statusColor),
                            )

                            Spacer(modifier = Modifier.width(6.dp))

                            Text(
                                text = displayStatus,
                                style = EimirTheme.typography.bodySmall,
                                color = EimirTheme.colors.textSecondary,
                            )

                            if (relationshipDuration != null) {
                                Text(
                                    text = " · ",
                                    style = EimirTheme.typography.bodySmall,
                                    color = EimirTheme.colors.border,
                                )
                            }
                        }

                        if (relationshipDuration != null) {
                            Text(
                                text = relationshipDuration,
                                style = EimirTheme.typography.bodySmall,
                                color = EimirTheme.colors.brand,
                                fontWeight = FontWeight.SemiBold,
                                modifier = if (onDurationClick != null) {
                                    Modifier
                                        .heightIn(min = 48.dp)
                                        .clickable(
                                            role = Role.Button,
                                            onClickLabel = stringResource(R.string.relationship_presence_view_duration),
                                            onClick = onDurationClick,
                                        )
                                        .padding(horizontal = 4.dp, vertical = 12.dp)
                                } else {
                                    Modifier
                                },
                            )
                        }
                    }
                }
            }

            if (actionContent != null) {
                Spacer(modifier = Modifier.width(if (isCompact) 8.dp else 12.dp))
                actionContent()
            }
        }
    }
}
