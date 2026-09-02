package de.sidebyside.next.reference

import androidx.lifecycle.viewModelScope
import de.sidebyside.next.connectivity.ConnectivityTracker
import java.io.IOException
import java.time.OffsetDateTime
import java.util.UUID
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.ExperimentalCoroutinesApi
import kotlinx.coroutines.cancel
import kotlinx.coroutines.test.StandardTestDispatcher
import kotlinx.coroutines.test.TestScope
import kotlinx.coroutines.test.advanceUntilIdle
import kotlinx.coroutines.test.resetMain
import kotlinx.coroutines.test.runTest
import kotlinx.coroutines.test.setMain
import org.junit.After
import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertNull
import org.junit.Assert.assertTrue
import org.junit.Before
import org.junit.Test
import sidebyside.api.models.AccountMembershipView
import sidebyside.api.models.AccountView
import sidebyside.api.models.SessionView
import sidebyside.api.models.TokenView

private val SPACE: UUID = UUID.fromString("11111111-1111-4111-8111-111111111111")
private val OTHER_SPACE: UUID = UUID.fromString("55555555-5555-4555-8555-555555555555")

/**
 * The proactive half of #328's "membership/authorization changes are
 * reconciled after reconnect": [ReferenceViewModel] re-lists memberships
 * once per genuine offline-to-online transition and reacts if the active
 * Space is no longer active for this account, reusing the exact
 * `awaitingSpace`/[ReferenceViewModel.selectSpace] states sign-in itself
 * already has, rather than a bespoke revoked-access flow.
 */
@OptIn(ExperimentalCoroutinesApi::class)
class ReferenceViewModelMembershipReconciliationTest {
    private val dispatcher = StandardTestDispatcher()

    @Before
    fun setUp() = Dispatchers.setMain(dispatcher)

    @After
    fun tearDown() = Dispatchers.resetMain()

    @Test
    fun reconnectingWhileStillAMemberOfTheActiveSpaceJustRefreshesAvailableSpaces() = runTest(dispatcher) {
        val tracker = ConnectivityTracker()
        val api = MembershipApi()
        val model = signedIn(api, tracker)

        tracker.recordFailure(IOException("offline"))
        advanceUntilIdle()
        tracker.recordSuccess()
        advanceUntilIdle()

        assertEquals(SPACE, model.uiState.value.activeSpaceId)
        assertTrue(model.uiState.value.loggedIn)
        assertFalse(model.uiState.value.awaitingSpace)
        assertTrue(model.uiState.value.availableSpaces.any { it.spaceId == SPACE })

        model.viewModelScope.cancel()
        advanceUntilIdle()
    }

    @Test
    fun reconnectingAfterLosingTheActiveSpaceSwitchesToAnotherStillActiveOne() = runTest(dispatcher) {
        val tracker = ConnectivityTracker()
        val api = MembershipApi()
        val model = signedIn(api, tracker)

        tracker.recordFailure(IOException("offline"))
        advanceUntilIdle()
        api.nextMemberships = listOf(
            AccountMembershipView(role = "PARTNER", spaceId = OTHER_SPACE, status = "ACTIVE"),
        )
        tracker.recordSuccess()
        advanceUntilIdle()

        assertEquals(OTHER_SPACE, model.uiState.value.activeSpaceId)
        assertTrue(model.uiState.value.loggedIn)
        assertFalse(model.uiState.value.awaitingSpace)

        model.viewModelScope.cancel()
        advanceUntilIdle()
    }

    @Test
    fun reconnectingAfterLosingEveryActiveSpaceFallsBackToAwaitingSpace() = runTest(dispatcher) {
        val tracker = ConnectivityTracker()
        val api = MembershipApi()
        val model = signedIn(api, tracker)

        tracker.recordFailure(IOException("offline"))
        advanceUntilIdle()
        api.nextMemberships = emptyList()
        tracker.recordSuccess()
        advanceUntilIdle()

        assertTrue(model.uiState.value.awaitingSpace)
        assertFalse(model.uiState.value.loggedIn)
        assertNull(model.uiState.value.activeSpaceId)

        model.viewModelScope.cancel()
        advanceUntilIdle()
    }

    @Test
    fun aFailedReconciliationCallLeavesTheActiveSpaceUnchanged() = runTest(dispatcher) {
        val tracker = ConnectivityTracker()
        val api = MembershipApi()
        val model = signedIn(api, tracker)

        tracker.recordFailure(IOException("offline"))
        advanceUntilIdle()
        api.listMembershipsFailure = IOException("still flaky right after reconnect")
        tracker.recordSuccess()
        advanceUntilIdle()

        assertEquals(SPACE, model.uiState.value.activeSpaceId)
        assertTrue(model.uiState.value.loggedIn)
        assertFalse(model.uiState.value.awaitingSpace)

        model.viewModelScope.cancel()
        advanceUntilIdle()
    }

    private suspend fun TestScope.signedIn(api: ReferenceContract, tracker: ConnectivityTracker): ReferenceViewModel {
        val model = ReferenceViewModel(config = ReferenceConfig(BASE_URL), api = api, connectivityTracker = tracker)
        model.signIn("someone@example.test", "secret")
        advanceUntilIdle()
        return model
    }
}

private const val BASE_URL = "https://sidebyside.example"

private class MembershipApi : FakeReferenceContract() {
    var nextMemberships: List<AccountMembershipView> = listOf(
        AccountMembershipView(role = "PARTNER", spaceId = SPACE, status = "ACTIVE"),
    )
    var listMembershipsFailure: Throwable? = null

    override suspend fun signIn(email: String, password: String): SessionView = SessionView(
        account = AccountView(displayName = email, id = UUID.randomUUID()),
        tokens = TokenView(
            accessExpiresAt = OffsetDateTime.now(),
            accessToken = "access",
            refreshExpiresAt = OffsetDateTime.now(),
            refreshToken = "refresh",
        ),
    )

    override suspend fun listMemberships(accessToken: String): List<AccountMembershipView> {
        listMembershipsFailure?.let { throw it }
        return nextMemberships
    }
}
