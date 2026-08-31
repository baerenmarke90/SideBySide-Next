package de.sidebyside.next.shell

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.heightIn
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.widthIn
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.CircularProgressIndicator
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedButton
import androidx.compose.material3.Surface
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.res.stringResource
import androidx.compose.ui.semantics.LiveRegionMode
import androidx.compose.ui.semantics.liveRegion
import androidx.compose.ui.semantics.semantics
import androidx.compose.ui.unit.Dp
import androidx.compose.ui.unit.dp
import de.sidebyside.next.design.MinimumTouchTarget
import de.sidebyside.next.design.SideBySideTheme
import de.sidebyside.next.reference.R

/**
 * The shared presentation of every system state.
 *
 * One component rather than one per screen, so a loading state cannot look like
 * an error on one surface and like a hint on another. Every state announces
 * itself: a screen reader user has to learn that something changed without
 * seeing the panel appear.
 */
@Composable
fun UiStatePanel(
    kind: UiStateKind,
    title: String,
    body: String?,
    modifier: Modifier = Modifier,
    onRetry: (() -> Unit)? = null,
    retryLabel: String = stringResource(R.string.state_retry),
) {
    val colors = SideBySideTheme.colors
    val mark = when (kind) {
        UiStateKind.Loading -> colors.brandSurface to colors.brandStrong
        UiStateKind.Empty -> colors.surfaceSubtle to colors.textSecondary
        UiStateKind.Error -> colors.errorSurface to colors.error
        UiStateKind.Permission -> colors.errorSurface to colors.error
        UiStateKind.Conflict -> colors.sharedSurface to colors.shared
        UiStateKind.RateLimit -> colors.discoverySurface to colors.discovery
        UiStateKind.Offline -> colors.discoverySurface to colors.discovery
    }

    Surface(
        modifier = modifier
            .fillMaxWidth()
            .semantics {
                // An error interrupts; everything else is announced politely.
                liveRegion = if (kind == UiStateKind.Error) {
                    LiveRegionMode.Assertive
                } else {
                    LiveRegionMode.Polite
                }
            },
        shape = RoundedCornerShape(SideBySideTheme.radii.card),
        color = colors.surface,
    ) {
        Row(
            modifier = Modifier.padding(SideBySideTheme.spacing.cardPadding),
            horizontalArrangement = Arrangement.spacedBy(
                SideBySideTheme.spacing.step4,
            ),
        ) {
            StateMark(background = mark.first, foreground = mark.second, kind = kind)
            Column(
                verticalArrangement = Arrangement.spacedBy(
                    SideBySideTheme.spacing.step2,
                ),
            ) {
                Text(
                    text = title,
                    style = MaterialTheme.typography.titleMedium,
                    color = colors.textPrimary,
                )
                if (body != null) {
                    Text(
                        text = body,
                        style = MaterialTheme.typography.bodyMedium,
                        color = colors.textSecondary,
                        modifier = Modifier.widthIn(max = ReadingMeasure),
                    )
                }
                if (onRetry != null) {
                    OutlinedButton(
                        onClick = onRetry,
                        modifier = Modifier.heightIn(min = MinimumTouchTarget),
                    ) {
                        Text(retryLabel)
                    }
                }
            }
        }
    }
}

/**
 * Renders a [UiProblem] and offers a retry only where retrying can change the
 * answer.
 */
@Composable
fun UiProblemPanel(
    problem: UiProblem,
    modifier: Modifier = Modifier,
    onRetry: (() -> Unit)? = null,
) {
    UiStatePanel(
        kind = problem.kind,
        title = stringResource(problem.titleRes),
        body = stringResource(problem.bodyRes),
        modifier = modifier,
        onRetry = if (problem.retryable) onRetry else null,
    )
}

@Composable
private fun StateMark(background: Color, foreground: Color, kind: UiStateKind) {
    Surface(
        modifier = Modifier.size(MarkSize),
        shape = RoundedCornerShape(SideBySideTheme.radii.large),
        color = background,
    ) {
        Box(contentAlignment = Alignment.Center) {
            if (kind == UiStateKind.Loading) {
                CircularProgressIndicator(
                    modifier = Modifier.size(MarkIndicatorSize),
                    color = foreground,
                    strokeWidth = 2.dp,
                )
            } else {
                Text(
                    // Decoration beside the title, which carries the meaning.
                    text = markGlyph(kind),
                    style = MaterialTheme.typography.titleLarge,
                    color = foreground,
                )
            }
        }
    }
}

private fun markGlyph(kind: UiStateKind): String = when (kind) {
    UiStateKind.Loading -> ""
    UiStateKind.Empty -> "◇"
    UiStateKind.Error -> "!"
    UiStateKind.Permission -> "○"
    UiStateKind.Conflict -> "↻"
    UiStateKind.RateLimit -> "⌛"
    UiStateKind.Offline -> "↯"
}

private val MarkSize: Dp = 44.dp
private val MarkIndicatorSize: Dp = 22.dp
private val ReadingMeasure: Dp = 560.dp
