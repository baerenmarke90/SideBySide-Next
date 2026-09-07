package de.sidebyside.next.design

import androidx.compose.animation.animateColorAsState
import androidx.compose.animation.core.animateFloatAsState
import androidx.compose.animation.core.spring
import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.clickable
import androidx.compose.foundation.interaction.MutableInteractionSource
import androidx.compose.foundation.interaction.collectIsPressedAsState
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.sizeIn
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.rememberCoroutineScope
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.draw.scale
import androidx.compose.ui.hapticfeedback.HapticFeedbackType
import androidx.compose.ui.platform.LocalHapticFeedback
import androidx.compose.ui.res.stringResource
import androidx.compose.ui.semantics.Role
import androidx.compose.ui.semantics.contentDescription
import androidx.compose.ui.semantics.semantics
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import de.sidebyside.next.reference.R
import kotlinx.coroutines.delay
import kotlinx.coroutines.launch

enum class ThinkingOfYouState {
    IDLE,
    SENDING,
    SENT,
}

/**
 * Tactile relationship micro-interaction button to send a quick
 * loving impulse to the partner with haptic and visual feedback.
 */
@Composable
fun ThinkingOfYouButton(
    partnerName: String?,
    modifier: Modifier = Modifier,
    isCompact: Boolean = false,
    enabled: Boolean = true,
    externalState: ThinkingOfYouState? = null,
    onSend: (suspend () -> Unit)? = null,
    onClick: (() -> Unit)? = null,
) {
    var internalState by remember { mutableStateOf(ThinkingOfYouState.IDLE) }
    val buttonState = externalState ?: internalState
    val coroutineScope = rememberCoroutineScope()
    val haptics = LocalHapticFeedback.current
    val interactionSource = remember { MutableInteractionSource() }
    val isPressed by interactionSource.collectIsPressedAsState()

    val scale by animateFloatAsState(
        targetValue = when {
            isPressed -> 0.95f
            buttonState == ThinkingOfYouState.SENT -> 1.04f
            else -> 1.0f
        },
        animationSpec = spring(),
        label = "ThinkingOfYouScale",
    )

    val backgroundColor by animateColorAsState(
        targetValue = when (buttonState) {
            ThinkingOfYouState.IDLE -> SideBySideTheme.colors.brandSurface
            ThinkingOfYouState.SENDING -> SideBySideTheme.colors.surfaceSubtle
            ThinkingOfYouState.SENT -> SideBySideTheme.colors.sharedSurface
        },
        label = "ThinkingOfYouBg",
    )

    val contentColor by animateColorAsState(
        targetValue = when (buttonState) {
            ThinkingOfYouState.IDLE -> SideBySideTheme.colors.brandStrong
            ThinkingOfYouState.SENDING -> SideBySideTheme.colors.brand
            ThinkingOfYouState.SENT -> SideBySideTheme.colors.shared
        },
        label = "ThinkingOfYouContent",
    )

    val actionLabel = when (buttonState) {
        ThinkingOfYouState.IDLE -> if (partnerName != null) {
            stringResource(R.string.relationship_thinking_of_you_send, partnerName)
        } else {
            stringResource(R.string.relationship_thinking_of_you_default)
        }
        ThinkingOfYouState.SENDING -> stringResource(R.string.relationship_thinking_of_you_sending)
        ThinkingOfYouState.SENT -> stringResource(R.string.relationship_thinking_of_you_sent)
    }

    Box(
        modifier = modifier
            .sizeIn(minWidth = 48.dp, minHeight = 48.dp)
            .scale(scale)
            .clip(CircleShape)
            .background(backgroundColor)
            .border(1.dp, contentColor, CircleShape)
            .semantics { contentDescription = actionLabel }
            .clickable(
                interactionSource = interactionSource,
                indication = null,
                enabled = enabled && buttonState == ThinkingOfYouState.IDLE,
                role = Role.Button,
            ) {
                haptics.performHapticFeedback(HapticFeedbackType.LongPress)
                if (onClick != null) {
                    onClick()
                } else {
                    internalState = ThinkingOfYouState.SENDING
                    coroutineScope.launch {
                        try {
                            onSend?.invoke()
                            internalState = ThinkingOfYouState.SENT
                            delay(2500)
                        } catch (e: Exception) {
                            // Reset gracefully on error without crashing
                        } finally {
                            internalState = ThinkingOfYouState.IDLE
                        }
                    }
                }
            }
            .padding(horizontal = if (isCompact) 12.dp else 16.dp, vertical = 10.dp),
        contentAlignment = Alignment.Center,
    ) {
        Row(
            verticalAlignment = Alignment.CenterVertically,
            horizontalArrangement = Arrangement.Center,
        ) {
            Text(
                text = if (buttonState == ThinkingOfYouState.SENT) "✓" else "♥",
                color = contentColor,
                fontWeight = FontWeight.Bold,
            )

            if (!isCompact) {
                Spacer(modifier = Modifier.width(8.dp))
                Text(
                    text = when (buttonState) {
                        ThinkingOfYouState.IDLE -> stringResource(R.string.relationship_thinking_of_you_default)
                        ThinkingOfYouState.SENDING -> stringResource(R.string.relationship_thinking_of_you_sending)
                        ThinkingOfYouState.SENT -> stringResource(R.string.relationship_thinking_of_you_sent)
                    },
                    color = contentColor,
                    style = SideBySideTheme.typography.labelLarge,
                    fontWeight = FontWeight.SemiBold,
                )
            }
        }
    }
}
