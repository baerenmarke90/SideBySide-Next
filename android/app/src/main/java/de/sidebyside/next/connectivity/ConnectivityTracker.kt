package de.sidebyside.next.connectivity

import de.sidebyside.next.cache.isServerAvailabilityFailure
import java.time.Instant
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow

/** [offline] is `true` only after a transport/server-availability failure, per M2-D18. */
data class ConnectivityState(
    val offline: Boolean = false,
    val lastSyncedAt: Instant? = null,
)

/**
 * The M2-D18 "one coherent application-level connectivity state" this client
 * shows instead of a dialog per failed request. Every request this client
 * makes funnels through [de.sidebyside.next.reference.OkHttpReferenceApi]'s
 * two internal executors, which report here — so no individual screen has to
 * say anything about connectivity itself.
 *
 * Shares [isServerAvailabilityFailure] with the read cache: what counts as
 * "the server is unreachable" must not differ between the two, or a cache
 * fallback could appear while the app still claims to be online, or the
 * reverse.
 */
class ConnectivityTracker {
    private val _state = MutableStateFlow(ConnectivityState())
    val state: StateFlow<ConnectivityState> = _state.asStateFlow()

    fun recordSuccess() {
        _state.value = ConnectivityState(offline = false, lastSyncedAt = Instant.now())
    }

    /** A 401/403/validation/409 failure says nothing about reachability and leaves [state] untouched. */
    fun recordFailure(throwable: Throwable) {
        if (!isServerAvailabilityFailure(throwable)) return
        _state.value = _state.value.copy(offline = true)
    }
}
