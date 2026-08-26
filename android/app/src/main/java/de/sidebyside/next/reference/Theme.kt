package de.sidebyside.next.reference

import android.app.Activity
import android.content.Context
import android.content.ContextWrapper
import android.os.Build
import android.view.View
import android.view.Window
import android.view.WindowInsetsController
import androidx.compose.foundation.isSystemInDarkTheme
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.darkColorScheme
import androidx.compose.material3.lightColorScheme
import androidx.compose.runtime.Composable
import androidx.compose.runtime.SideEffect
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.toArgb
import androidx.compose.ui.platform.LocalView

internal val SideBySideLightColorScheme = lightColorScheme(
    primary = Color(0xFF6638DC),
    onPrimary = Color(0xFFFFFFFF),
    primaryContainer = Color(0xFFEEE7FF),
    onPrimaryContainer = Color(0xFF211A2B),
    secondary = Color(0xFF237A65),
    onSecondary = Color(0xFFFFFFFF),
    secondaryContainer = Color(0xFFE3F6F1),
    onSecondaryContainer = Color(0xFF173A31),
    tertiary = Color(0xFFA61F51),
    onTertiary = Color(0xFFFFFFFF),
    tertiaryContainer = Color(0xFFFFE7EE),
    onTertiaryContainer = Color(0xFF5B1731),
    background = Color(0xFFFAF8FC),
    onBackground = Color(0xFF211A2B),
    surface = Color(0xFFFFFFFF),
    onSurface = Color(0xFF211A2B),
    surfaceVariant = Color(0xFFF2EEF5),
    onSurfaceVariant = Color(0xFF51485C),
    outline = Color(0xFFCFC7D7),
    outlineVariant = Color(0xFFE6E0EB),
    error = Color(0xFFA4133C),
    onError = Color(0xFFFFFFFF),
    errorContainer = Color(0xFFFFE7EE),
    onErrorContainer = Color(0xFF5B1028),
    scrim = Color(0xCC211A2B),
)

internal val SideBySideDarkColorScheme = darkColorScheme(
    primary = Color(0xFFBDA7FF),
    onPrimary = Color(0xFF2E145D),
    primaryContainer = Color(0xFF3D2E55),
    onPrimaryContainer = Color(0xFFF1EAFF),
    secondary = Color(0xFF8FE0CE),
    onSecondary = Color(0xFF07372D),
    secondaryContainer = Color(0xFF183C34),
    onSecondaryContainer = Color(0xFFC0F3E6),
    tertiary = Color(0xFFFF9BB8),
    onTertiary = Color(0xFF5A1730),
    tertiaryContainer = Color(0xFF4A2432),
    onTertiaryContainer = Color(0xFFFFD9E4),
    background = Color(0xFF1C1525),
    onBackground = Color(0xFFF7F2FA),
    surface = Color(0xFF2A2135),
    onSurface = Color(0xFFF7F2FA),
    surfaceVariant = Color(0xFF34283F),
    onSurfaceVariant = Color(0xFFD9D0E0),
    outline = Color(0xFF8F819C),
    outlineVariant = Color(0xFF493D55),
    error = Color(0xFFFFB1C1),
    onError = Color(0xFF650020),
    errorContainer = Color(0xFF44202D),
    onErrorContainer = Color(0xFFFFD9E2),
    scrim = Color(0xB3000000),
)

@Composable
fun SideBySideTheme(
    darkTheme: Boolean = isSystemInDarkTheme(),
    content: @Composable () -> Unit,
) {
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

    MaterialTheme(
        colorScheme = colorScheme,
        content = content,
    )
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
