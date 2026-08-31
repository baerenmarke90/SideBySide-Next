package de.sidebyside.next.shell

import androidx.compose.foundation.layout.BoxWithConstraints
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.ui.Modifier
import androidx.navigation.NavGraph.Companion.findStartDestination
import androidx.navigation.NavHostController
import androidx.navigation.compose.NavHost
import androidx.navigation.compose.composable
import androidx.navigation.compose.currentBackStackEntryAsState
import androidx.navigation.compose.rememberNavController

/**
 * The navigation host.
 *
 * Navigation Compose owns the back stack rather than a hand-written one. Its
 * back stack survives process death through saved state, and it integrates with
 * the system back gesture, which `docs/INFORMATION-ARCHITECTURE.md` section 9
 * requires to behave like browser back. Both are exactly the kind of commodity
 * behaviour `docs/REUSE-BEFORE-BUILD.md` says not to reimplement.
 */
@Composable
fun AppNavigation(
    destinations: List<AppDestination>,
    modifier: Modifier = Modifier,
    navController: NavHostController = rememberNavController(),
    destinationContent: @Composable (AppDestination) -> Unit,
) {
    require(destinations.isNotEmpty()) { "The shell needs at least one destination." }
    val start = destinations.first()
    val backStackEntry by navController.currentBackStackEntryAsState()
    val currentDestination =
        destinationForRoute(backStackEntry?.destination?.route, destinations)

    BoxWithConstraints(modifier = modifier.fillMaxSize()) {
        AppShell(
            widthClass = windowWidthClassFor(maxWidth),
            destinations = destinations,
            currentDestination = currentDestination,
            onSelectDestination = { destination ->
                navController.navigateToPrimary(destination)
            },
        ) {
            NavHost(
                navController = navController,
                startDestination = start.route,
                modifier = Modifier.fillMaxSize(),
            ) {
                for (destination in destinations) {
                    composable(destination.route) { destinationContent(destination) }
                }
            }
        }
    }
}

/**
 * Switching primary navigation must not stack history, per
 * `docs/INFORMATION-ARCHITECTURE.md` section 9. Each destination keeps its own
 * state so returning to it does not reset what the user was looking at.
 */
fun NavHostController.navigateToPrimary(destination: AppDestination) {
    navigate(destination.route) {
        popUpTo(graph.findStartDestination().id) { saveState = true }
        launchSingleTop = true
        restoreState = true
    }
}

/**
 * Falls back to the first available destination for an unknown route, which is
 * what a route removed between app versions looks like after a state restore.
 */
fun destinationForRoute(
    route: String?,
    destinations: List<AppDestination> = declaredDestinations,
): AppDestination =
    destinations.firstOrNull { it.route == route } ?: destinations.first()
