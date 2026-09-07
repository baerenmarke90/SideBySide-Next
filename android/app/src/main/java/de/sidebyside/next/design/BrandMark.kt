package de.sidebyside.next.design

import androidx.compose.foundation.Canvas
import androidx.compose.foundation.background
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.geometry.Offset
import androidx.compose.ui.graphics.Brush
import androidx.compose.ui.graphics.drawscope.Stroke
import androidx.compose.ui.res.stringResource
import androidx.compose.ui.semantics.clearAndSetSemantics
import androidx.compose.ui.semantics.contentDescription
import androidx.compose.ui.text.SpanStyle
import androidx.compose.ui.text.buildAnnotatedString
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.withStyle
import androidx.compose.ui.unit.Dp
import androidx.compose.ui.unit.dp
import de.sidebyside.next.reference.R

/**
 * Two interlocking rings: two independent people connected by a shared,
 * protected space. Drawn as vector geometry rather than shipped as a raster
 * so it stays crisp at every density and follows the theme.
 */
@Composable
fun BrandMark(
    modifier: Modifier = Modifier,
    size: Dp = 48.dp,
) {
    val ringColor = MaterialTheme.colorScheme.onPrimary
    val gradientBrush = Brush.linearGradient(
        colors = listOf(SideBySideTheme.colors.brand, SideBySideTheme.colors.brandStrong),
        start = Offset.Zero,
        end = Offset.Infinite,
    )
    Box(
        modifier = modifier
            .size(size)
            .clip(RoundedCornerShape(SideBySideTheme.radii.large))
            .background(gradientBrush),
        contentAlignment = Alignment.Center,
    ) {
        Canvas(modifier = Modifier.matchParentSize()) {
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
 * Mark plus the canonical product name eimir. with the signature brand dot.
 * The whole lockup carries one name for assistive technology; announcing mark
 * and words separately would say the product name twice.
 */
@Composable
fun BrandLockup(
    modifier: Modifier = Modifier,
    markSize: Dp = 48.dp,
) {
    val name = stringResource(R.string.app_name)
    val dotIndex = name.lastIndexOf('.')
    val annotatedName = if (dotIndex != -1) {
        buildAnnotatedString {
            append(name.substring(0, dotIndex))
            withStyle(SpanStyle(color = SideBySideTheme.colors.brandStrong)) {
                append(".")
            }
            append(name.substring(dotIndex + 1))
        }
    } else {
        buildAnnotatedString { append(name) }
    }
    Row(
        modifier = modifier.clearAndSetSemantics { contentDescription = name },
        verticalAlignment = Alignment.CenterVertically,
        horizontalArrangement = Arrangement.spacedBy(SideBySideTheme.spacing.step3),
    ) {
        BrandMark(size = markSize)
        Text(
            text = annotatedName,
            style = MaterialTheme.typography.titleLarge.copy(
                fontWeight = FontWeight.Bold,
            ),
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
