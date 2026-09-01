package de.sidebyside.next.design

import androidx.compose.material3.Typography
import androidx.compose.ui.text.TextStyle
import androidx.compose.ui.text.font.Font
import androidx.compose.ui.text.font.FontFamily
import androidx.compose.ui.text.font.FontWeight
import de.sidebyside.next.reference.R
import androidx.compose.ui.unit.sp

/**
 * The shared typography scale mapped onto Material 3 roles.
 *
 * Token line heights are ratios and letter spacing is in `em`; both are
 * resolved against the token font size so a scale change in
 * `design/tokens.json` propagates without a second edit here.
 *
 * The token file names `Inter` and `Fraunces`. Only Fraunces is delivered, as
 * one variable file bundled with the app. The UI face stays the platform's own:
 * every platform already ships a neutral grotesque, so Inter would have cost
 * bytes for a difference nobody would name. See
 * `docs/decisions/0005-typography-delivery.md`.
 */

/**
 * The display face, from the app's own resources.
 *
 * One variable file rather than static cuts, so the token scale's weights are
 * all covered by a single 360 kB resource. Nothing is fetched at runtime: a
 * font host would put a third party in the path of a product whose premise is
 * that only two people are in it, and Self-Hosted installations have no
 * external access to rely on.
 */
val FrauncesFamily: FontFamily = FontFamily(
    Font(R.font.fraunces, FontWeight.Normal),
    Font(R.font.fraunces, FontWeight.Medium),
    Font(R.font.fraunces, FontWeight.SemiBold),
    Font(R.font.fraunces, FontWeight.Bold),
)
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
        // Reserved for editorial and Story moments, and the only place the
        // delivered face is used.
        fontFamily = FrauncesFamily,
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
