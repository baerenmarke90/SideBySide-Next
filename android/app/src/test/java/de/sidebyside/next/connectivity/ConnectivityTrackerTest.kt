package de.sidebyside.next.connectivity

import de.sidebyside.next.reference.ReferenceApiException
import java.io.IOException
import org.junit.Assert.assertFalse
import org.junit.Assert.assertNotNull
import org.junit.Assert.assertNull
import org.junit.Assert.assertTrue
import org.junit.Test

class ConnectivityTrackerTest {
    @Test
    fun startsOnlineWithNoSyncTimestamp() {
        val tracker = ConnectivityTracker()
        assertFalse(tracker.state.value.offline)
        assertNull(tracker.state.value.lastSyncedAt)
    }

    @Test
    fun anIOExceptionMarksTheAppOffline() {
        val tracker = ConnectivityTracker()
        tracker.recordFailure(IOException("no connection"))
        assertTrue(tracker.state.value.offline)
    }

    @Test
    fun a503MarksTheAppOffline() {
        val tracker = ConnectivityTracker()
        tracker.recordFailure(ReferenceApiException(code = null, message = "maintenance", status = 503))
        assertTrue(tracker.state.value.offline)
    }

    @Test
    fun aPlain500NeverMarksTheAppOffline() {
        // Matches the read cache's own boundary: a plain 500 is a server bug,
        // not evidence the server is unreachable.
        val tracker = ConnectivityTracker()
        tracker.recordFailure(ReferenceApiException(code = null, message = "bug", status = 500))
        assertFalse(tracker.state.value.offline)
    }

    @Test
    fun a401NeverMarksTheAppOffline() {
        val tracker = ConnectivityTracker()
        tracker.recordFailure(ReferenceApiException(code = "unauthenticated", message = "expired", status = 401))
        assertFalse(tracker.state.value.offline)
    }

    @Test
    fun aSuccessAfterAFailureClearsOfflineAndRecordsTheSyncTime() {
        val tracker = ConnectivityTracker()
        tracker.recordFailure(IOException("no connection"))
        assertTrue(tracker.state.value.offline)

        tracker.recordSuccess()

        assertFalse(tracker.state.value.offline)
        assertNotNull(tracker.state.value.lastSyncedAt)
    }
}
