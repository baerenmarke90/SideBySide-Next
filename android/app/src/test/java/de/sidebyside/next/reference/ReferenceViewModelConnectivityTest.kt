package de.sidebyside.next.reference

import androidx.lifecycle.viewModelScope
import de.sidebyside.next.connectivity.ConnectivityTracker
import java.io.IOException
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.ExperimentalCoroutinesApi
import kotlinx.coroutines.cancel
import kotlinx.coroutines.test.StandardTestDispatcher
import kotlinx.coroutines.test.advanceUntilIdle
import kotlinx.coroutines.test.resetMain
import kotlinx.coroutines.test.runTest
import kotlinx.coroutines.test.setMain
import org.junit.After
import org.junit.Assert.assertFalse
import org.junit.Assert.assertNotNull
import org.junit.Assert.assertNull
import org.junit.Assert.assertTrue
import org.junit.Before
import org.junit.Test

/**
 * [ReferenceViewModel] mirrors a configured [ConnectivityTracker]'s state
 * into [ReferenceUiState.offline]/[ReferenceUiState.lastSyncedAt] — the
 * integration point the ViewModel's own network call sites cannot prove,
 * since the tracker is fed by [OkHttpReferenceApi] rather than by the
 * ViewModel directly.
 *
 * Two easy-to-repeat mistakes shaped every test here, both found via CI
 * runs this exact file's first version crashed elsewhere in:
 *
 * 1. [ReferenceConfig.apiBaseUrl] must never be a real-looking, non-blank
 *    URL without also injecting an [api], or [ReferenceViewModel.init]'s
 *    `refreshInstanceAvailability()` builds a real `OkHttpReferenceApi` and
 *    attempts a real network call on `Dispatchers.IO` — invisible to
 *    `advanceUntilIdle()`, which only drives this test's own dispatcher, so
 *    it resolves at an arbitrary later moment and can crash whatever
 *    unrelated test happens to be running when `Dispatchers.Main` is
 *    touched outside any test's own `setMain()`/`resetMain()` window.
 * 2. Unlike every other call site's one-shot coroutines, the connectivity
 *    collector this ViewModel starts in `init` never completes on its own —
 *    it lives for the ViewModel's whole lifetime, ended in production by
 *    `onCleared()`. Nothing calls that here, so every test cancels its own
 *    model's scope and drains that cancellation with `advanceUntilIdle()`
 *    before returning; left dangling past `Dispatchers.resetMain()`, it
 *    crashes a later, unrelated test the same way.
 */
@OptIn(ExperimentalCoroutinesApi::class)
class ReferenceViewModelConnectivityTest {
    private val dispatcher = StandardTestDispatcher()

    @Before
    fun setUp() = Dispatchers.setMain(dispatcher)

    @After
    fun tearDown() = Dispatchers.resetMain()

    @Test
    fun startsOnlineWithNoConfiguredTracker() = runTest(dispatcher) {
        val model = ReferenceViewModel(config = ReferenceConfig(BASE_URL), api = object : FakeReferenceContract() {})

        assertFalse(model.uiState.value.offline)
        assertNull(model.uiState.value.lastSyncedAt)

        model.viewModelScope.cancel()
        advanceUntilIdle()
    }

    @Test
    fun aTrackerFailureMarksTheUiStateOffline() = runTest(dispatcher) {
        val tracker = ConnectivityTracker()
        val model = ReferenceViewModel(
            config = ReferenceConfig(BASE_URL),
            api = object : FakeReferenceContract() {},
            connectivityTracker = tracker,
        )

        tracker.recordFailure(IOException("no connection"))
        advanceUntilIdle()

        assertTrue(model.uiState.value.offline)

        model.viewModelScope.cancel()
        advanceUntilIdle()
    }

    @Test
    fun aTrackerSuccessClearsOfflineAndRecordsTheSyncTime() = runTest(dispatcher) {
        val tracker = ConnectivityTracker()
        val model = ReferenceViewModel(
            config = ReferenceConfig(BASE_URL),
            api = object : FakeReferenceContract() {},
            connectivityTracker = tracker,
        )

        tracker.recordFailure(IOException("no connection"))
        advanceUntilIdle()
        tracker.recordSuccess()
        advanceUntilIdle()

        assertFalse(model.uiState.value.offline)
        assertNotNull(model.uiState.value.lastSyncedAt)

        model.viewModelScope.cancel()
        advanceUntilIdle()
    }
}

private const val BASE_URL = "https://sidebyside.example"
