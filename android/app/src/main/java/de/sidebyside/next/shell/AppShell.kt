package de.sidebyside.next.shell

import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.WindowInsets
import androidx.compose.foundation.layout.consumeWindowInsets
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.safeDrawing
import androidx.compose.foundation.layout.windowInsetsPadding
import androidx.compose.material3.LocalContentColor
import androidx.compose.material3.NavigationBar
import androidx.compose.material3.NavigationBarItem
import androidx.compose.material3.NavigationBarItemColors
import androidx.compose.material3.NavigationBarItemDefaults
import androidx.compose.material3.NavigationRail
import androidx.compose.material3.NavigationRailItem
import androidx.compose.material3.NavigationRailItemColors
import androidx.compose.material3.NavigationRailItemDefaults
import androidx.compose.material3.Scaffold
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Modifier
import androidx.compose.ui.res.stringResource
import androidx.compose.ui.unit.Dp
import androidx.compose.ui.unit.dp
import de.sidebyside.next.design.SideBySideTheme

/**
 * Window size classes from `docs/SCREEN-TEMPLATES.md` section 1.
 *
 * Derived from the available width rather than from a device category, which is
 * what the document requires and what keeps a folded and an unfolded device
 * correct without the app knowing which is which.
 */
enum class WindowWidthClass { Compact, Medium, Expanded }

val MediumWidthThreshold: Dp = 600.dp
val ExpandedWidthThreshold: Dp = 840.dp

fun windowWidthClassFor(width: Dp): WindowWidthClass = when {
    width < MediumWidthThreshold -> WindowWidthClass.Compact
    width < ExpandedWidthThreshold -> WindowWidthClass.Medium
    else -> WindowWidthClass.Expanded
}

/**
 * Applies the window insets to a surface that has no navigation.
 *
 * The entry screen is shown before there is anything to navigate between, but
 * it still draws edge to edge and still has a status bar and a display cutout
 * above it. Routing it around [AppShell] is what put the brand lockup
 * underneath the clock.
 */
@Composable
fun ShellSurface(
    modifier: Modifier = Modifier,
    content: @Composable () -> Unit,
) {
    Box(
        modifier = modifier
            .fillMaxSize()
            .windowInsetsPadding(WindowInsets.safeDrawing),
    ) {
        content()
    }
}

/**
 * The application shell.
 *
 * It owns the two things every screen would otherwise get wrong on its own.
 *
 * **Window insets.** `targetSdk` 36 means the system draws the app edge to edge
 * and hands back responsibility for the status bar, the navigation bar, the
 * display cutout and the keyboard. Content laid out without them ends up
 * underneath the clock, which is exactly what happened before this slice.
 *
 * **The navigation surface.** Bottom navigation on a compact window, a
 * navigation rail from the medium class upwards, from one destination list so
 * the two cannot drift.
 */
@Composable
fun AppShell(
    widthClass: WindowWidthClass,
    destinations: List<AppDestination>,
    currentDestination: AppDestination,
    onSelectDestination: (AppDestination) -> Unit,
    modifier: Modifier = Modifier,
    content: @Composable () -> Unit,
) {
    val compact = widthClass == WindowWidthClass.Compact
    // A single destination is not a choice, so no navigation surface is drawn
    // for it. This also keeps the shell honest while later slices are still
    // filling their areas.
    val navigable = destinations.size > 1

    Scaffold(
        modifier = modifier.fillMaxSize(),
        contentWindowInsets = WindowInsets.safeDrawing,
        bottomBar = {
            if (compact && navigable) {
                CompactNavigation(destinations, currentDestination, onSelectDestination)
            }
        },
    ) { padding ->
        Row(modifier = Modifier.fillMaxSize()) {
            if (!compact && navigable) {
                MediumNavigation(
                    destinations = destinations,
                    currentDestination = currentDestination,
                    onSelectDestination = onSelectDestination,
                    modifier = Modifier.windowInsetsPadding(WindowInsets.safeDrawing),
                )
            }
            Box(
                modifier = Modifier
                    .fillMaxSize()
                    .padding(padding)
                    // The content area must not apply the same insets again.
                    .consumeWindowInsets(padding),
            ) {
                content()
            }
        }
    }
}

/*
 * Material fills the selection indicator from `secondaryContainer`, which this
 * product maps to the shared mint. Mint means shared and confirmed
 * (`docs/DESIGN-PRINCIPLES.md` 3.1), so an active destination must not borrow
 * it; brand purple is the product's own active state, as on the Web client.
 */
@Composable
private fun navigationBarItemColors(): NavigationBarItemColors =
    NavigationBarItemDefaults.colors(
        selectedIconColor = SideBySideTheme.colors.brandStrong,
        selectedTextColor = SideBySideTheme.colors.brandStrong,
        indicatorColor = SideBySideTheme.colors.brandSurface,
        unselectedIconColor = SideBySideTheme.colors.textSecondary,
        unselectedTextColor = SideBySideTheme.colors.textSecondary,
    )

@Composable
private fun navigationRailItemColors(): NavigationRailItemColors =
    NavigationRailItemDefaults.colors(
        selectedIconColor = SideBySideTheme.colors.brandStrong,
        selectedTextColor = SideBySideTheme.colors.brandStrong,
        indicatorColor = SideBySideTheme.colors.brandSurface,
        unselectedIconColor = SideBySideTheme.colors.textSecondary,
        unselectedTextColor = SideBySideTheme.colors.textSecondary,
    )

@Composable
private fun CompactNavigation(
    destinations: List<AppDestination>,
    currentDestination: AppDestination,
    onSelectDestination: (AppDestination) -> Unit,
) {
    NavigationBar(containerColor = SideBySideTheme.colors.surface) {
        val colors = navigationBarItemColors()
        for (destination in destinations) {
            NavigationBarItem(
                selected = destination == currentDestination,
                onClick = { onSelectDestination(destination) },
                icon = { DestinationGlyph(destination.icon, LocalContentColor.current) },
                label = { Text(stringResource(destination.labelRes)) },
                alwaysShowLabel = true,
                colors = colors,
            )
        }
    }
}

@Composable
private fun MediumNavigation(
    destinations: List<AppDestination>,
    currentDestination: AppDestination,
    onSelectDestination: (AppDestination) -> Unit,
    modifier: Modifier = Modifier,
) {
    NavigationRail(
        modifier = modifier,
        containerColor = SideBySideTheme.colors.surface,
    ) {
        val colors = navigationRailItemColors()
        for (destination in destinations) {
            NavigationRailItem(
                selected = destination == currentDestination,
                onClick = { onSelectDestination(destination) },
                icon = { DestinationGlyph(destination.icon, LocalContentColor.current) },
                label = { Text(stringResource(destination.labelRes)) },
                alwaysShowLabel = true,
                colors = colors,
            )
        }
    }
}
