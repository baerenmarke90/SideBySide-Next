package de.sidebyside.next.design

import androidx.compose.foundation.Canvas
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Surface
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.geometry.Offset
import androidx.compose.ui.graphics.drawscope.Stroke
import androidx.compose.ui.res.stringResource
import androidx.compose.ui.semantics.clearAndSetSemantics
import androidx.compose.ui.semantics.contentDescription
import androidx.compose.ui.unit.Dp
import androidx.compose.ui.unit.dp
import de.sidebyside.next.reference.R

/**
 * Two interlocking rings: the product is two people side by side, and the mark
 * says only that. Drawn rather than shipped as a raster so it stays crisp at
 * every density and follows the theme instead of carrying baked-in colour.
 */
@Composable
fun BrandMark(
    modifier: Modifier = Modifier,
    size: Dp = 48.dp,
) {
    val ringColor = MaterialTheme.colorScheme.onPrimary
    Surface(
        modifier = modifier.size(size),
        shape = RoundedCornerShape(SideBySideTheme.radii.large),
        color = MaterialTheme.colorScheme.primary,
    ) {
        Canvas(modifier = Modifier.clip(RoundedCornerShape(SideBySideTheme.radii.large))) {
            val radius = this.size.minDimension * 0.22f
            val strokeWidth = this.size.minDimension * 0.085f
            val centerY = this.size.height / 2f
            val offsetX = radius * 0.72f
            drawCircle(
                color = ringColor,
                radius = radius,
                center = Offset(this.size.width / 2f - offsetX, centerY),
                style = Stroke(width = strokeWidth),
            )
            drawCircle(
                color = ringColor,
                radius = radius,
                center = Offset(this.size.width / 2f + offsetX, centerY),
                style = Stroke(width = strokeWidth),
            )
        }
    }
}

/**
 * Mark plus the canonical product name. The whole lockup carries one name for
 * assistive technology; announcing mark and words separately would say the
 * product name twice.
 */
@Composable
fun BrandLockup(
    modifier: Modifier = Modifier,
    markSize: Dp = 48.dp,
) {
    val name = stringResource(R.string.app_name)
    Row(
        modifier = modifier.clearAndSetSemantics { contentDescription = name },
        verticalAlignment = Alignment.CenterVertically,
        horizontalArrangement = Arrangement.spacedBy(SideBySideTheme.spacing.step3),
    ) {
        BrandMark(size = markSize)
        Text(
            text = name,
            style = MaterialTheme.typography.titleLarge,
            color = MaterialTheme.colorScheme.onBackground,
        )
    }
}

/**
 * A calm accent band behind the entry heading. It carries mood, not
 * information, so it is hidden from assistive technology.
 */
@Composable
fun BrandAura(modifier: Modifier = Modifier) {
    val glow = SideBySideTheme.colors.brandGlow
    Box(
        modifier = modifier.clearAndSetSemantics { },
    ) {
        Canvas(modifier = Modifier.matchParentSize()) {
            drawCircle(
                color = glow,
                radius = size.minDimension * 0.75f,
                center = Offset(size.width * 0.18f, size.height * 0.1f),
            )
        }
    }
}
