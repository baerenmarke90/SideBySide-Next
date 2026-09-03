package de.sidebyside.next.shell

import androidx.compose.foundation.Canvas
import androidx.compose.foundation.layout.size
import androidx.compose.runtime.Composable
import androidx.compose.ui.Modifier
import androidx.compose.ui.geometry.Offset
import androidx.compose.ui.geometry.Size
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.Path
import androidx.compose.ui.graphics.drawscope.DrawScope
import androidx.compose.ui.graphics.drawscope.Stroke
import androidx.compose.ui.unit.Dp
import androidx.compose.ui.unit.dp

/**
 * Destination icons, drawn rather than pulled from an icon dependency.
 *
 * They repeat the shapes the Web client uses, so the two navigations read as
 * the same product. Every icon is decoration beside a text label and is
 * therefore never given a content description by its caller.
 */
@Composable
fun DestinationGlyph(
    icon: DestinationIcon,
    tint: Color,
    modifier: Modifier = Modifier,
    size: Dp = IconSize,
) {
    Canvas(modifier = modifier.size(size)) {
        val stroke = Stroke(width = this.size.minDimension * StrokeRatio)
        when (icon) {
            DestinationIcon.Today -> drawToday(tint, stroke)
            DestinationIcon.Story -> drawStory(tint, stroke)
            DestinationIcon.Plan -> drawPlan(tint, stroke)
            DestinationIcon.More -> drawMore(tint, stroke)
        }
    }
}

/** An affectionate heart: Wir / our place today. */
private fun DrawScope.drawToday(tint: Color, stroke: Stroke) {
    val path = Path().apply {
        moveTo(size.width * 0.5f, size.height * 0.78f)
        cubicTo(
            size.width * 0.15f, size.height * 0.52f,
            size.width * 0.15f, size.height * 0.22f,
            size.width * 0.35f, size.height * 0.22f,
        )
        cubicTo(
            size.width * 0.45f, size.height * 0.22f,
            size.width * 0.5f, size.height * 0.32f,
            size.width * 0.5f, size.height * 0.32f,
        )
        cubicTo(
            size.width * 0.5f, size.height * 0.32f,
            size.width * 0.55f, size.height * 0.22f,
            size.width * 0.65f, size.height * 0.22f,
        )
        cubicTo(
            size.width * 0.85f, size.height * 0.22f,
            size.width * 0.85f, size.height * 0.52f,
            size.width * 0.5f, size.height * 0.78f,
        )
        close()
    }
    drawPath(path = path, color = tint, style = stroke)
}

/** A camera frame: Momente / shared history. */
private fun DrawScope.drawStory(tint: Color, stroke: Stroke) {
    val path = Path().apply {
        moveTo(size.width * 0.2f, size.height * 0.35f)
        lineTo(size.width * 0.32f, size.height * 0.35f)
        lineTo(size.width * 0.38f, size.height * 0.24f)
        lineTo(size.width * 0.62f, size.height * 0.24f)
        lineTo(size.width * 0.68f, size.height * 0.35f)
        lineTo(size.width * 0.8f, size.height * 0.35f)
        lineTo(size.width * 0.8f, size.height * 0.78f)
        lineTo(size.width * 0.2f, size.height * 0.78f)
        close()
    }
    drawPath(path = path, color = tint, style = stroke)
    drawCircle(
        color = tint,
        radius = size.minDimension * 0.16f,
        center = Offset(size.width * 0.5f, size.height * 0.56f),
        style = stroke,
    )
}

/** A checklist board. */
private fun DrawScope.drawPlan(tint: Color, stroke: Stroke) {
    drawRoundRectOutline(tint, stroke)
    for (index in 0..1) {
        val y = size.height * (0.46f + index * 0.16f)
        drawLine(
            color = tint,
            start = Offset(size.width * 0.36f, y),
            end = Offset(size.width * 0.68f, y),
            strokeWidth = stroke.width,
        )
    }
}

/** Three stacked lines: everything else. */
private fun DrawScope.drawMore(tint: Color, stroke: Stroke) {
    for (index in 0..2) {
        val y = size.height * (0.3f + index * 0.2f)
        val end = if (index == 2) size.width * 0.62f else size.width * 0.8f
        drawLine(
            color = tint,
            start = Offset(size.width * 0.2f, y),
            end = Offset(end, y),
            strokeWidth = stroke.width,
        )
    }
}

private fun DrawScope.drawRoundRectOutline(tint: Color, stroke: Stroke) {
    drawRoundRect(
        color = tint,
        topLeft = Offset(size.width * 0.26f, size.height * 0.22f),
        size = Size(size.width * 0.48f, size.height * 0.6f),
        cornerRadius = androidx.compose.ui.geometry.CornerRadius(
            size.minDimension * 0.1f,
        ),
        style = stroke,
    )
}

private val IconSize: Dp = 24.dp
private const val StrokeRatio = 0.08f
