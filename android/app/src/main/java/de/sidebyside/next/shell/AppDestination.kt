package de.sidebyside.next.shell

import de.sidebyside.next.reference.R

/**
 * The destination registry.
 *
 * Route IDs and order come from
 * `docs/decisions/0003-primary-navigation-and-route-model.md` and
 * `docs/INFORMATION-ARCHITECTURE.md` section 2, which both clients share. The
 * route strings match the Web paths so a Deep Link registry can be built on
 * them in #328 without a second mapping.
 */
enum class AppDestination(
    val route: String,
    val labelRes: Int,
    val icon: DestinationIcon,
) {
    Today("today", R.string.destination_today, DestinationIcon.Today),
    Story("story", R.string.destination_story, DestinationIcon.Story),
    Plan("plan", R.string.destination_plan, DestinationIcon.Plan),
    More("more", R.string.destination_more, DestinationIcon.More),
}

/**
 * Reserved for the M7 Discover domain.
 *
 * Declared so the route and label cannot be reused for anything else, and not
 * part of [AppDestination]: a visible area with no Core behind it is dead
 * navigation.
 */
const val RESERVED_DISCOVER_ROUTE: String = "discover"

enum class DestinationIcon { Today, Story, Plan, More }

/**
 * The full contract, in the order fixed by the Information Architecture.
 *
 * A destination is only *rendered* once it has something to show: the slice
 * contract forbids dead navigation, so the shell is given the implemented
 * subset rather than this list. Each later slice adds its own destination.
 */
val declaredDestinations: List<AppDestination> = AppDestination.entries
