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

/** A clock face: what is relevant now. */
private fun DrawScope.drawToday(tint: Color, stroke: Stroke) {
    val radius = size.minDimension * 0.36f
    drawCircle(color = tint, radius = radius, style = stroke)
    drawLine(
        color = tint,
        start = Offset(size.width / 2f, size.height / 2f),
        end = Offset(size.width / 2f, size.height * 0.28f),
        strokeWidth = stroke.width,
    )
    drawLine(
        color = tint,
        start = Offset(size.width / 2f, size.height / 2f),
        end = Offset(size.width * 0.68f, size.height * 0.58f),
        strokeWidth = stroke.width,
    )
}

/** A house: the shared history is where the couple lives. */
private fun DrawScope.drawStory(tint: Color, stroke: Stroke) {
    val path = Path().apply {
        moveTo(size.width * 0.2f, size.height * 0.48f)
        lineTo(size.width * 0.5f, size.height * 0.2f)
        lineTo(size.width * 0.8f, size.height * 0.48f)
        lineTo(size.width * 0.8f, size.height * 0.8f)
        lineTo(size.width * 0.2f, size.height * 0.8f)
        close()
    }
    drawPath(path = path, color = tint, style = stroke)
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
