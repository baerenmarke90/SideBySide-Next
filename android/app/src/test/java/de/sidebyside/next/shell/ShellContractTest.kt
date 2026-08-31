package de.sidebyside.next.shell

import androidx.compose.ui.unit.dp
import de.sidebyside.next.reference.ReferenceApiException
import java.io.IOException
import java.net.SocketTimeoutException
import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertNotEquals
import org.junit.Assert.assertTrue
import org.junit.Test

/**
 * The shell is a cross-client contract rather than a local convention, so these
 * tests pin the parts the Web client and the Information Architecture also
 * depend on.
 */
class DestinationRegistryTest {
    @Test
    fun declaresTheDocumentedDestinationsInOrder() {
        assertEquals(
            listOf("today", "story", "plan", "more"),
            declaredDestinations.map { it.route },
        )
    }

    @Test
    fun staysWithinTheFiveDestinationCeiling() {
        assertTrue(declaredDestinations.size <= 5)
    }

    @Test
    fun reservesDiscoverWithoutDeclaringItAsADestination() {
        assertEquals("discover", RESERVED_DISCOVER_ROUTE)
        assertFalse(declaredDestinations.any { it.route == RESERVED_DISCOVER_ROUTE })
    }

    @Test
    fun matchesTheWebRouteIdentitiesSoDeepLinksCanShareOneRegistry() {
        // The Web client serves /today, /story, /plan and /more.
        for (destination in declaredDestinations) {
            assertFalse(destination.route.startsWith("/"))
            assertNotEquals("", destination.route)
        }
    }

    @Test
    fun resolvesAnUnknownRouteToTheFirstAvailableDestination() {
        val available = listOf(AppDestination.Story, AppDestination.More)
        // A route removed between app versions looks like this after a restore.
        assertEquals(AppDestination.Story, destinationForRoute("today", available))
        assertEquals(AppDestination.Story, destinationForRoute(null, available))
        assertEquals(AppDestination.More, destinationForRoute("more", available))
    }
}

class WindowWidthClassTest {
    @Test
    fun classifiesByAvailableWidthRatherThanDeviceCategory() {
        assertEquals(WindowWidthClass.Compact, windowWidthClassFor(320.dp))
        assertEquals(WindowWidthClass.Compact, windowWidthClassFor(599.dp))
        assertEquals(WindowWidthClass.Medium, windowWidthClassFor(600.dp))
        assertEquals(WindowWidthClass.Medium, windowWidthClassFor(839.dp))
        assertEquals(WindowWidthClass.Expanded, windowWidthClassFor(840.dp))
        assertEquals(WindowWidthClass.Expanded, windowWidthClassFor(1280.dp))
    }

    @Test
    fun usesTheThresholdsFromTheScreenTemplates() {
        assertEquals(600.dp, MediumWidthThreshold)
        assertEquals(840.dp, ExpandedWidthThreshold)
    }
}

class ProblemMappingTest {
    @Test
    fun treatsAConnectionFailureAsOfflineRatherThanAnError() {
        val problem = problemFor(SocketTimeoutException("timed out"))
        assertEquals(UiStateKind.Offline, problem.kind)
        assertTrue(problem.retryable)
        assertEquals(UiStateKind.Offline, problemFor(IOException()).kind)
    }

    @Test
    fun doesNotConfirmThatForbiddenContentExists() {
        // 403 and 404 must be indistinguishable, or the difference itself
        // discloses that a resource exists.
        val forbidden = problemFor(apiFailure(403))
        val missing = problemFor(apiFailure(404))
        assertEquals(forbidden.kind, missing.kind)
        assertEquals(forbidden.titleRes, missing.titleRes)
        assertEquals(forbidden.bodyRes, missing.bodyRes)
    }

    @Test
    fun offersRetryOnlyWhereRetryingCanChangeTheAnswer() {
        assertFalse(problemFor(apiFailure(401)).retryable)
        assertFalse(problemFor(apiFailure(403)).retryable)
        assertFalse(problemFor(apiFailure(409)).retryable)
        assertFalse(problemFor(apiFailure(422)).retryable)
        assertTrue(problemFor(apiFailure(429)).retryable)
        assertTrue(problemFor(apiFailure(503)).retryable)
    }

    @Test
    fun mapsEachDocumentedStatusToItsOwnState() {
        assertEquals(UiStateKind.Permission, problemFor(apiFailure(401)).kind)
        assertEquals(UiStateKind.Conflict, problemFor(apiFailure(409)).kind)
        assertEquals(UiStateKind.Conflict, problemFor(apiFailure(412)).kind)
        assertEquals(UiStateKind.RateLimit, problemFor(apiFailure(429)).kind)
        assertEquals(UiStateKind.Error, problemFor(apiFailure(500)).kind)
        assertEquals(UiStateKind.Error, problemFor(apiFailure(599)).kind)
    }

    @Test
    fun fallsBackToAGenericErrorForAnUnknownStatus() {
        assertEquals(UiStateKind.Error, problemFor(apiFailure(null)).kind)
        assertEquals(UiStateKind.Error, problemFor(apiFailure(418)).kind)
        assertEquals(UiStateKind.Error, problemFor(IllegalStateException()).kind)
    }

    @Test
    fun neverCarriesServerTextIntoTheUserFacingState() {
        // The mapping returns string resources only; a ProblemDetails detail may
        // name resources or internal reasons and must not reach the user.
        val problem = problemFor(
            ReferenceApiException(
                code = "MEMORY_NOT_FOUND",
                message = "Memory 01a0-secret is not visible to account 42.",
                status = 404,
            ),
        )
        assertNotEquals(0, problem.titleRes)
        assertNotEquals(0, problem.bodyRes)
    }

    private fun apiFailure(status: Int?) =
        ReferenceApiException(code = null, message = "failed", status = status)
}
