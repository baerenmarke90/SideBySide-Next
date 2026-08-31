package de.sidebyside.next.design

import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.Shapes
import androidx.compose.runtime.Immutable
import androidx.compose.runtime.staticCompositionLocalOf
import androidx.compose.ui.unit.Dp
import androidx.compose.ui.unit.dp

/**
 * Spacing steps of the shared 4-unit grid, named by step rather than by their
 * current value. Values come from `design/tokens.json`.
 */
@Immutable
data class SideBySideSpacing(
    val none: Dp,
    val step1: Dp,
    val step2: Dp,
    val step3: Dp,
    val step4: Dp,
    val step5: Dp,
    val step6: Dp,
    val step8: Dp,
    val step10: Dp,
    val step12: Dp,
    val step16: Dp,
) {
    /** Outer page margin on a compact window per `docs/SCREEN-TEMPLATES.md`. */
    val pageMargin: Dp get() = step5

    /** Standard spacing inside a card. */
    val cardPadding: Dp get() = step6

    /** Gap between related elements inside a group. */
    val groupGap: Dp get() = step3

    /** Gap between separate sections. */
    val sectionGap: Dp get() = step8
}

@Immutable
data class SideBySideRadii(
    val none: Dp,
    val small: Dp,
    val medium: Dp,
    val large: Dp,
    val card: Dp,
    val sheet: Dp,
    val hero: Dp,
    val pill: Dp,
)

internal val sideBySideSpacing = with(GeneratedDimensionTokens) {
    SideBySideSpacing(
        none = SPACING_0.dp,
        step1 = SPACING_1.dp,
        step2 = SPACING_2.dp,
        step3 = SPACING_3.dp,
        step4 = SPACING_4.dp,
        step5 = SPACING_5.dp,
        step6 = SPACING_6.dp,
        step8 = SPACING_8.dp,
        step10 = SPACING_10.dp,
        step12 = SPACING_12.dp,
        step16 = SPACING_16.dp,
    )
}

internal val sideBySideRadii = with(GeneratedDimensionTokens) {
    SideBySideRadii(
        none = RADIUS_NONE.dp,
        small = RADIUS_SMALL.dp,
        medium = RADIUS_MEDIUM.dp,
        large = RADIUS_LARGE.dp,
        card = RADIUS_CARD.dp,
        sheet = RADIUS_SHEET.dp,
        hero = RADIUS_HERO.dp,
        pill = RADIUS_PILL.dp,
    )
}

internal val sideBySideShapes = Shapes(
    extraSmall = RoundedCornerShape(sideBySideRadii.small),
    small = RoundedCornerShape(sideBySideRadii.medium),
    medium = RoundedCornerShape(sideBySideRadii.large),
    large = RoundedCornerShape(sideBySideRadii.card),
    extraLarge = RoundedCornerShape(sideBySideRadii.sheet),
)

/**
 * Minimum interactive size. Material and the Android accessibility guidance
 * both put this at 48 dp, above the 44 px the Web client uses.
 */
val MinimumTouchTarget: Dp = 48.dp

val LocalSideBySideSpacing = staticCompositionLocalOf { sideBySideSpacing }

val LocalSideBySideRadii = staticCompositionLocalOf { sideBySideRadii }
