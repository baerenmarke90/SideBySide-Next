package de.sidebyside.next.reference

import org.junit.Assert.assertFalse
import org.junit.Assert.assertTrue
import org.junit.Test

/**
 * The predicate [AppNavigation][de.sidebyside.next.shell.AppNavigation]'s
 * `secureWhen` is wired to for #356 — pinned on its own, since a mistake
 * here would silently widen or narrow which screens get `FLAG_SECURE`
 * without any other test noticing.
 */
class PrivateAreaRouteTest {
    @Test
    fun matchesTheHubRouteItself() {
        assertTrue(isPrivateAreaRoute("more/private"))
    }

    @Test
    fun matchesEveryRouteUnderTheHub() {
        assertTrue(isPrivateAreaRoute("more/private/notes"))
        assertTrue(isPrivateAreaRoute("more/private/gift-ideas"))
        assertTrue(isPrivateAreaRoute("more/private/collections/123/items"))
    }

    @Test
    fun doesNotMatchAnUnrelatedRouteThatMerelyStartsTheSameWay() {
        assertFalse(isPrivateAreaRoute("more/privateer"))
        assertFalse(isPrivateAreaRoute("more"))
        assertFalse(isPrivateAreaRoute("planning/places"))
    }

    @Test
    fun doesNotMatchANullRoute() {
        assertFalse(isPrivateAreaRoute(null))
    }
}

/**
 * The full `secureWhen` decision, including #357's Search addition: a
 * `SearchResult` can carry a private `SearchKind`, so the whole screen
 * needs the same `FLAG_SECURE` protection as the Private Area subtree.
 */
class SecureRouteTest {
    @Test
    fun matchesTheSearchRoute() {
        assertTrue(isSecureRoute("search"))
    }

    @Test
    fun stillMatchesThePrivateAreaSubtree() {
        assertTrue(isSecureRoute("more/private"))
        assertTrue(isSecureRoute("more/private/notes"))
    }

    @Test
    fun doesNotMatchOrdinarySharedRoutes() {
        assertFalse(isSecureRoute("today/activity"))
        assertFalse(isSecureRoute("more/notifications"))
        assertFalse(isSecureRoute("planning/places"))
    }

    @Test
    fun doesNotMatchANullRoute() {
        assertFalse(isSecureRoute(null))
    }
}
