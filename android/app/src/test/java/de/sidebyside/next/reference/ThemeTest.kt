package de.sidebyside.next.reference

import androidx.compose.ui.graphics.Color
import kotlin.math.max
import kotlin.math.min
import org.junit.Assert.assertEquals
import org.junit.Assert.assertTrue
import org.junit.Test

class ThemeTest {
    @Test
    fun darkThemeUsesTheSharedDesignTokenSurfaces() {
        assertEquals(Color(0xFF1C1525), SideBySideDarkColorScheme.background)
        assertEquals(Color(0xFF2A2135), SideBySideDarkColorScheme.surface)
        assertEquals(Color(0xFFF7F2FA), SideBySideDarkColorScheme.onBackground)
        assertEquals(Color(0xFFBDA7FF), SideBySideDarkColorScheme.primary)
        assertEquals(Color(0xFF8FE0CE), SideBySideDarkColorScheme.secondary)
    }

    @Test
    fun primaryTextContrastMeetsWcagAaInBothSchemes() {
        assertTrue(
            contrastRatio(
                SideBySideLightColorScheme.onBackground,
                SideBySideLightColorScheme.background,
            ) >= 4.5,
        )
        assertTrue(
            contrastRatio(
                SideBySideLightColorScheme.onSurface,
                SideBySideLightColorScheme.surface,
            ) >= 4.5,
        )
        assertTrue(
            contrastRatio(
                SideBySideDarkColorScheme.onBackground,
                SideBySideDarkColorScheme.background,
            ) >= 4.5,
        )
        assertTrue(
            contrastRatio(
                SideBySideDarkColorScheme.onSurface,
                SideBySideDarkColorScheme.surface,
            ) >= 4.5,
        )
    }

    @Test
    fun secondaryDarkTextRemainsReadableOnDarkSurface() {
        assertTrue(
            contrastRatio(
                SideBySideDarkColorScheme.onSurfaceVariant,
                SideBySideDarkColorScheme.surface,
            ) >= 4.5,
        )
    }
}

private fun contrastRatio(first: Color, second: Color): Double {
    val firstLuminance = relativeLuminance(first)
    val secondLuminance = relativeLuminance(second)
    return (max(firstLuminance, secondLuminance) + 0.05) /
        (min(firstLuminance, secondLuminance) + 0.05)
}

private fun relativeLuminance(color: Color): Double =
    0.2126 * linearChannel(color.red.toDouble()) +
        0.7152 * linearChannel(color.green.toDouble()) +
        0.0722 * linearChannel(color.blue.toDouble())

private fun linearChannel(value: Double): Double =
    if (value <= 0.04045) value / 12.92 else Math.pow((value + 0.055) / 1.055, 2.4)
