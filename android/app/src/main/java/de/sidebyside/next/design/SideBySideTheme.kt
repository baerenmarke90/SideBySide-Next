package de.sidebyside.next.design

import android.app.Activity
import android.content.Context
import android.content.ContextWrapper
import android.os.Build
import android.view.View
import android.view.Window
import android.view.WindowInsetsController
import androidx.compose.foundation.isSystemInDarkTheme
import androidx.compose.material3.ColorScheme
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.darkColorScheme
import androidx.compose.material3.lightColorScheme
import androidx.compose.runtime.Composable
import androidx.compose.runtime.CompositionLocalProvider
import androidx.compose.runtime.ReadOnlyComposable
import androidx.compose.runtime.SideEffect
import androidx.compose.ui.graphics.toArgb
import androidx.compose.ui.platform.LocalView

/**
 * Derives the Material 3 scheme from the semantic roles.
 *
 * The mapping is the only place that decides which product meaning fills which
 * Material role: brand is the primary action, shared is the confirmation
 * secondary, and private is the tertiary that marks restriction. Keeping it in
 * one function means a token change never has to be re-applied per role.
 */
internal fun ColorScheme.applying(colors: SideBySideColors): ColorScheme = copy(
    primary = colors.brandStrong,
    onPrimary = colors.onAccent,
    primaryContainer = colors.brandSurface,
    onPrimaryContainer = colors.textPrimary,
    secondary = colors.shared,
    onSecondary = colors.textInverse,
    secondaryContainer = colors.sharedSurface,
    onSecondaryContainer = colors.textPrimary,
    tertiary = colors.private,
    onTertiary = colors.textInverse,
    tertiaryContainer = colors.privateSurface,
    onTertiaryContainer = colors.textPrimary,
    background = colors.background,
    onBackground = colors.textPrimary,
    surface = colors.surface,
    onSurface = colors.textPrimary,
    surfaceVariant = colors.surfaceSubtle,
    onSurfaceVariant = colors.textSecondary,
    outline = colors.border,
    outlineVariant = colors.borderSubtle,
    error = colors.error,
    onError = colors.textInverse,
    errorContainer = colors.errorSurface,
    onErrorContainer = colors.textPrimary,
    scrim = colors.scrim,
)

internal val SideBySideLightColorScheme: ColorScheme =
    lightColorScheme().applying(lightSideBySideColors)

internal val SideBySideDarkColorScheme: ColorScheme =
    darkColorScheme().applying(darkSideBySideColors).copy(
        // The dark palette inverts which end of the scale carries text, so the
        // container roles take the light text rather than the inverse token.
        onPrimaryContainer = darkSideBySideColors.textPrimary,
        onSecondaryContainer = darkSideBySideColors.textPrimary,
        onTertiaryContainer = darkSideBySideColors.textPrimary,
        onErrorContainer = darkSideBySideColors.textPrimary,
        onSecondary = darkSideBySideColors.background,
        onTertiary = darkSideBySideColors.background,
        onError = darkSideBySideColors.background,
    )

/**
 * Appearance follows the system. A manual override would have to persist a
 * preference, which needs storage this slice deliberately does not add.
 */
@Composable
fun SideBySideTheme(
    darkTheme: Boolean = isSystemInDarkTheme(),
    content: @Composable () -> Unit,
) {
    val colors = if (darkTheme) darkSideBySideColors else lightSideBySideColors
    val colorScheme = if (darkTheme) SideBySideDarkColorScheme else SideBySideLightColorScheme
    val view = LocalView.current

    SideEffect {
        if (!view.isInEditMode) {
            view.context.findActivity()?.window?.let { window ->
                @Suppress("DEPRECATION")
                window.statusBarColor = colorScheme.background.toArgb()
                @Suppress("DEPRECATION")
                window.navigationBarColor = colorScheme.background.toArgb()
                updateSystemBarIconAppearance(window, darkTheme)
            }
        }
    }

    CompositionLocalProvider(
        LocalSideBySideColors provides colors,
        LocalSideBySideSpacing provides sideBySideSpacing,
        LocalSideBySideRadii provides sideBySideRadii,
    ) {
        MaterialTheme(
            colorScheme = colorScheme,
            typography = sideBySideTypography,
            shapes = sideBySideShapes,
            content = content,
        )
    }
}

/** Semantic roles that Material 3 does not carry, addressed by name. */
object SideBySideTheme {
    val colors: SideBySideColors
        @Composable @ReadOnlyComposable get() = LocalSideBySideColors.current

    val spacing: SideBySideSpacing
        @Composable @ReadOnlyComposable get() = LocalSideBySideSpacing.current

    val radii: SideBySideRadii
        @Composable @ReadOnlyComposable get() = LocalSideBySideRadii.current
}

private tailrec fun Context.findActivity(): Activity? = when (this) {
    is Activity -> this
    is ContextWrapper -> baseContext.findActivity()
    else -> null
}

private fun updateSystemBarIconAppearance(window: Window, darkTheme: Boolean) {
    if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.R) {
        val lightAppearance = if (darkTheme) {
            0
        } else {
            WindowInsetsController.APPEARANCE_LIGHT_STATUS_BARS or
                WindowInsetsController.APPEARANCE_LIGHT_NAVIGATION_BARS
        }
        val mask = WindowInsetsController.APPEARANCE_LIGHT_STATUS_BARS or
            WindowInsetsController.APPEARANCE_LIGHT_NAVIGATION_BARS
        window.insetsController?.setSystemBarsAppearance(lightAppearance, mask)
        return
    }

    @Suppress("DEPRECATION")
    val lightMask = View.SYSTEM_UI_FLAG_LIGHT_STATUS_BAR or View.SYSTEM_UI_FLAG_LIGHT_NAVIGATION_BAR
    @Suppress("DEPRECATION")
    window.decorView.systemUiVisibility = if (darkTheme) {
        window.decorView.systemUiVisibility and lightMask.inv()
    } else {
        window.decorView.systemUiVisibility or lightMask
    }
}
