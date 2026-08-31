package de.sidebyside.next.design

import androidx.compose.material3.Typography
import androidx.compose.ui.text.TextStyle
import androidx.compose.ui.text.font.FontFamily
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.sp

/**
 * The shared typography scale mapped onto Material 3 roles.
 *
 * Token line heights are ratios and letter spacing is in `em`; both are
 * resolved against the token font size so a scale change in
 * `design/tokens.json` propagates without a second edit here.
 *
 * The token file names `Inter` and `Fraunces`. Neither face is delivered with
 * the app, so both resolve to their documented fallbacks. Delivering them is a
 * provider decision with licensing and size consequences and is deliberately
 * not made in this slice.
 */
private fun tokenTextStyle(
    fontSizeSp: Float,
    lineHeightRatio: Float,
    fontWeight: Int,
    letterSpacingEm: Float,
    fontFamily: FontFamily = FontFamily.SansSerif,
): TextStyle = TextStyle(
    fontFamily = fontFamily,
    fontSize = fontSizeSp.sp,
    lineHeight = (fontSizeSp * lineHeightRatio).sp,
    fontWeight = FontWeight(fontWeight),
    letterSpacing = (fontSizeSp * letterSpacingEm).sp,
)

internal val displayStyle = with(GeneratedTypographyTokens.Display) {
    tokenTextStyle(
        FONT_SIZE_SP,
        LINE_HEIGHT_RATIO,
        FONT_WEIGHT,
        LETTER_SPACING_EM,
        // The display face is reserved for editorial and Story moments.
        fontFamily = FontFamily.Serif,
    )
}

internal val heading1Style = with(GeneratedTypographyTokens.Heading1) {
    tokenTextStyle(FONT_SIZE_SP, LINE_HEIGHT_RATIO, FONT_WEIGHT, LETTER_SPACING_EM)
}

internal val heading2Style = with(GeneratedTypographyTokens.Heading2) {
    tokenTextStyle(FONT_SIZE_SP, LINE_HEIGHT_RATIO, FONT_WEIGHT, LETTER_SPACING_EM)
}

internal val heading3Style = with(GeneratedTypographyTokens.Heading3) {
    tokenTextStyle(FONT_SIZE_SP, LINE_HEIGHT_RATIO, FONT_WEIGHT, LETTER_SPACING_EM)
}

internal val titleStyle = with(GeneratedTypographyTokens.Title) {
    tokenTextStyle(FONT_SIZE_SP, LINE_HEIGHT_RATIO, FONT_WEIGHT, LETTER_SPACING_EM)
}

internal val bodyStyle = with(GeneratedTypographyTokens.Body) {
    tokenTextStyle(FONT_SIZE_SP, LINE_HEIGHT_RATIO, FONT_WEIGHT, LETTER_SPACING_EM)
}

internal val bodySmallStyle = with(GeneratedTypographyTokens.BodySmall) {
    tokenTextStyle(FONT_SIZE_SP, LINE_HEIGHT_RATIO, FONT_WEIGHT, LETTER_SPACING_EM)
}

internal val labelStyle = with(GeneratedTypographyTokens.Label) {
    tokenTextStyle(FONT_SIZE_SP, LINE_HEIGHT_RATIO, FONT_WEIGHT, LETTER_SPACING_EM)
}

internal val metaStyle = with(GeneratedTypographyTokens.Meta) {
    tokenTextStyle(FONT_SIZE_SP, LINE_HEIGHT_RATIO, FONT_WEIGHT, LETTER_SPACING_EM)
}

/**
 * Android carries a wider Material role set than the token scale defines. Roles
 * without their own token reuse the closest documented step rather than
 * inventing an undocumented size.
 */
internal val sideBySideTypography = Typography(
    displayLarge = displayStyle,
    displayMedium = displayStyle,
    displaySmall = heading1Style,
    headlineLarge = heading1Style,
    headlineMedium = heading2Style,
    headlineSmall = heading3Style,
    titleLarge = heading3Style,
    titleMedium = titleStyle,
    titleSmall = labelStyle,
    bodyLarge = bodyStyle,
    bodyMedium = bodyStyle,
    bodySmall = bodySmallStyle,
    labelLarge = labelStyle,
    labelMedium = labelStyle,
    labelSmall = metaStyle,
)
