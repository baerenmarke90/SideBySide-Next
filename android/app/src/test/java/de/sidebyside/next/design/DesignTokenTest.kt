package de.sidebyside.next.design

import androidx.compose.ui.graphics.Color
import java.io.File
import kotlin.math.max
import kotlin.math.min
import kotlinx.serialization.json.Json
import kotlinx.serialization.json.JsonElement
import kotlinx.serialization.json.JsonObject
import kotlinx.serialization.json.JsonPrimitive
import kotlinx.serialization.json.float
import kotlinx.serialization.json.int
import kotlinx.serialization.json.jsonObject
import kotlinx.serialization.json.jsonPrimitive
import org.junit.Assert.assertEquals
import org.junit.Assert.assertTrue
import org.junit.Test

/**
 * The generated token layer is only worth having if it really comes from
 * `design/tokens.json`. These tests read the token file directly and compare it
 * against what the build generated, so a generator regression fails here rather
 * than silently shipping a stale palette.
 */
class DesignTokenTest {
    private val tokens: JsonObject = parseTokenFile()

    @Test
    fun lightSchemeMatchesTheSharedTokenFile() {
        assertSchemeMatchesTokens("light", lightSideBySideColors)
    }

    @Test
    fun darkSchemeMatchesTheSharedTokenFile() {
        assertSchemeMatchesTokens("dark", darkSideBySideColors)
    }

    @Test
    fun spacingScaleMatchesTheSharedTokenFile() {
        val spacing = tokens.child("spacing")
        assertEquals(spacing.dimension("1"), sideBySideSpacing.step1.value, 0.001f)
        assertEquals(spacing.dimension("4"), sideBySideSpacing.step4.value, 0.001f)
        assertEquals(spacing.dimension("16"), sideBySideSpacing.step16.value, 0.001f)
    }

    @Test
    fun radiusScaleMatchesTheSharedTokenFile() {
        val radius = tokens.child("radius")
        assertEquals(radius.dimension("card"), sideBySideRadii.card.value, 0.001f)
        assertEquals(radius.dimension("sheet"), sideBySideRadii.sheet.value, 0.001f)
    }

    @Test
    fun typographyScaleMatchesTheSharedTokenFile() {
        val heading1 = tokens.child("typography").child("heading1").child("\u0024value")
        assertEquals(
            heading1.text("fontSize").removeSuffix("px").toFloat(),
            heading1Style.fontSize.value,
            0.001f,
        )
        assertEquals(
            heading1.getValue("fontWeight").jsonPrimitive.int,
            heading1Style.fontWeight?.weight,
        )
    }

    @Test
    fun primaryTextContrastMeetsWcagAaInBothSchemes() {
        assertContrast(SideBySideLightColorScheme.onBackground, SideBySideLightColorScheme.background)
        assertContrast(SideBySideLightColorScheme.onSurface, SideBySideLightColorScheme.surface)
        assertContrast(SideBySideDarkColorScheme.onBackground, SideBySideDarkColorScheme.background)
        assertContrast(SideBySideDarkColorScheme.onSurface, SideBySideDarkColorScheme.surface)
    }

    @Test
    fun secondaryTextContrastMeetsWcagAaInBothSchemes() {
        assertContrast(SideBySideLightColorScheme.onSurfaceVariant, SideBySideLightColorScheme.surface)
        assertContrast(SideBySideDarkColorScheme.onSurfaceVariant, SideBySideDarkColorScheme.surface)
    }

    @Test
    fun actionContrastMeetsWcagAaInBothSchemes() {
        assertContrast(SideBySideLightColorScheme.onPrimary, SideBySideLightColorScheme.primary)
        assertContrast(SideBySideDarkColorScheme.onPrimary, SideBySideDarkColorScheme.primary)
        assertContrast(SideBySideLightColorScheme.onSecondary, SideBySideLightColorScheme.secondary)
        assertContrast(SideBySideDarkColorScheme.onSecondary, SideBySideDarkColorScheme.secondary)
        assertContrast(SideBySideLightColorScheme.onTertiary, SideBySideLightColorScheme.tertiary)
        assertContrast(SideBySideDarkColorScheme.onTertiary, SideBySideDarkColorScheme.tertiary)
        assertContrast(SideBySideLightColorScheme.onError, SideBySideLightColorScheme.error)
        assertContrast(SideBySideDarkColorScheme.onError, SideBySideDarkColorScheme.error)
    }

    @Test
    fun containerTextContrastMeetsWcagAaInBothSchemes() {
        assertContrast(
            SideBySideLightColorScheme.onPrimaryContainer,
            SideBySideLightColorScheme.primaryContainer,
        )
        assertContrast(
            SideBySideDarkColorScheme.onPrimaryContainer,
            SideBySideDarkColorScheme.primaryContainer,
        )
        assertContrast(
            SideBySideLightColorScheme.onSecondaryContainer,
            SideBySideLightColorScheme.secondaryContainer,
        )
        assertContrast(
            SideBySideDarkColorScheme.onSecondaryContainer,
            SideBySideDarkColorScheme.secondaryContainer,
        )
        assertContrast(
            SideBySideLightColorScheme.onTertiaryContainer,
            SideBySideLightColorScheme.tertiaryContainer,
        )
        assertContrast(
            SideBySideDarkColorScheme.onTertiaryContainer,
            SideBySideDarkColorScheme.tertiaryContainer,
        )
    }

    @Test
    fun materialRolesCarryTheDocumentedProductMeaning() {
        // Purple is the only standard colour for primary actions; mint means
        // shared, pink means restricted. See docs/DESIGN-PRINCIPLES.md 3.1.
        assertEquals(lightSideBySideColors.brandStrong, SideBySideLightColorScheme.primary)
        assertEquals(lightSideBySideColors.shared, SideBySideLightColorScheme.secondary)
        assertEquals(lightSideBySideColors.private, SideBySideLightColorScheme.tertiary)
    }

    private fun assertSchemeMatchesTokens(name: String, colors: SideBySideColors) {
        val semantic = tokens.child("color").child("semantic")
        val scheme = tokens.child("color").child("scheme").child(name)

        fun expected(role: String): Color {
            val raw = scheme.child(role).text("\u0024value")
            val hex = if (raw.startsWith("{")) {
                semantic.child(raw.trim('{', '}').substringAfterLast('.')).text("\u0024value")
            } else {
                raw
            }
            return hex.toComposeColor()
        }

        assertEquals(expected("background"), colors.background)
        assertEquals(expected("surface"), colors.surface)
        assertEquals(expected("textPrimary"), colors.textPrimary)
        assertEquals(expected("textSecondary"), colors.textSecondary)
        assertEquals(expected("brand"), colors.brand)
        assertEquals(expected("brandStrong"), colors.brandStrong)
        assertEquals(expected("shared"), colors.shared)
        assertEquals(expected("private"), colors.private)
        assertEquals(expected("error"), colors.error)
        assertEquals(expected("focus"), colors.focus)
        // An eight-digit token carries alpha and must not be read as opaque.
        assertEquals(expected("scrim"), colors.scrim)
        assertEquals(expected("brandGlow"), colors.brandGlow)
    }
}

private fun assertContrast(foreground: Color, background: Color) {
    val ratio = contrastRatio(foreground, background)
    assertTrue("Contrast ratio is only $ratio", ratio >= 4.5)
}

/**
 * The token file sits outside the Gradle module, so the test walks up from the
 * module directory rather than assuming a working directory.
 */
private fun parseTokenFile(): JsonObject {
    var directory: File? = File("").absoluteFile
    while (directory != null) {
        val candidate = File(directory, "design/tokens.json")
        if (candidate.isFile) {
            return Json.parseToJsonElement(candidate.readText()).jsonObject
        }
        directory = directory.parentFile
    }
    throw IllegalStateException("design/tokens.json was not found above the module directory.")
}

private fun JsonObject.child(key: String): JsonObject =
    (this[key] as? JsonObject)
        ?: throw IllegalStateException("Token object is missing: " + key)

private fun JsonObject.text(key: String): String =
    (this[key] as? JsonPrimitive)?.content
        ?: throw IllegalStateException("Token value is missing: " + key)

private fun JsonObject.dimension(key: String): Float =
    child(key).text("\u0024value").removeSuffix("px").toFloat()

/** Token colours are `#RRGGBB` or `#RRGGBBAA`; Compose expects `AARRGGBB`. */
private fun String.toComposeColor(): Color {
    val value = removePrefix("#").uppercase()
    val argb = when (value.length) {
        6 -> "FF$value"
        8 -> value.substring(6, 8) + value.substring(0, 6)
        else -> throw IllegalArgumentException("Unsupported colour token: $this")
    }
    return Color(argb.toLong(16))
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
