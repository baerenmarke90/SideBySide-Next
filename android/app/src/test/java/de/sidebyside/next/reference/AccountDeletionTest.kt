package de.sidebyside.next.reference

import java.util.UUID
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.ExperimentalCoroutinesApi
import kotlinx.coroutines.test.StandardTestDispatcher
import kotlinx.coroutines.test.advanceUntilIdle
import kotlinx.coroutines.test.resetMain
import kotlinx.coroutines.test.runTest
import kotlinx.coroutines.test.setMain
import org.junit.After
import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertNotNull
import org.junit.Assert.assertTrue
import org.junit.Before
import org.junit.Test
import sidebyside.api.models.AccountDeletionAccepted
import sidebyside.api.models.AccountDeletionRequest
import sidebyside.api.models.AccountDeletionStatus
import sidebyside.api.models.AccountMembershipView
import sidebyside.api.models.AccountView
import sidebyside.api.models.SessionView
import sidebyside.api.models.StoryPage
import sidebyside.api.models.TokenView

private const val ACCOUNT_DELETION_BASE_URL = "https://sidebyside.example"
private val ACCOUNT_DELETION_SPACE: UUID = UUID.fromString("11111111-1111-4111-8111-111111111111")

@OptIn(ExperimentalCoroutinesApi::class)
class AccountDeletionTest {
    private val dispatcher = StandardTestDispatcher()

    @Before
    fun setUp() = Dispatchers.setMain(dispatcher)

    @After
    fun tearDown() = Dispatchers.resetMain()

    @Test
    fun acceptedDeletionUsesTheSignedInAccountAndReusesLogoutInvalidation() =
        runTest(dispatcher) {
            val api = DeletionApi()
            val model = model(api)

            model.signIn("someone@example.test", "secret")
            advanceUntilIdle()
            assertTrue(model.uiState.value.loggedIn)

            model.deleteOwnAccount()
            advanceUntilIdle()

            assertEquals(listOf("access"), api.deletionTokens)
            assertEquals(
                listOf(AccountDeletionRequest.Confirmation.DELETE_ACCOUNT),
                api.deletionRequests.map { it.confirmation },
            )
            val state = model.uiState.value
            assertFalse(state.loggedIn)
            assertFalse(state.awaitingSpace)
            assertTrue(state.draftImages.isEmpty())
            assertEquals(null, state.activeSpaceId)
        }

    @Test
    fun rejectedDeletionKeepsTheSessionAndSurfacesTheProblem() = runTest(dispatcher) {
        val api = DeletionApi(
            deletionFailure = ReferenceApiException(
                code = "ACCOUNT_DELETION_AUTHORITY_UNAVAILABLE",
                message = "unavailable",
                status = 503,
            ),
        )
        val model = model(api)

        model.signIn("someone@example.test", "secret")
        advanceUntilIdle()
        model.deleteOwnAccount()
        advanceUntilIdle()

        val state = model.uiState.value
        assertTrue(state.loggedIn)
        assertFalse(state.accountDeletionBusy)
        assertNotNull(state.accountDeletionProblem)
        assertEquals(1, api.deletionRequests.size)
    }

    private fun model(api: ReferenceContract) = ReferenceViewModel(
        config = ReferenceConfig(ACCOUNT_DELETION_BASE_URL),
        api = api,
    )
}

private class DeletionApi(
    private val deletionFailure: Throwable? = null,
) : FakeReferenceContract() {
    val deletionTokens = mutableListOf<String>()
    val deletionRequests = mutableListOf<AccountDeletionRequest>()

    override suspend fun signIn(email: String, password: String): SessionView = SessionView(
        account = AccountView(displayName = "Someone", id = UUID.randomUUID()),
        tokens = TokenView(
            accessExpiresAt = java.time.OffsetDateTime.now(),
            accessToken = "access",
            refreshExpiresAt = java.time.OffsetDateTime.now(),
            refreshToken = "refresh",
        ),
    )

    override suspend fun listMemberships(accessToken: String): List<AccountMembershipView> =
        listOf(AccountMembershipView(role = "PARTNER", spaceId = ACCOUNT_DELETION_SPACE, status = "ACTIVE"))

    override suspend fun getTimeline(
        spaceId: UUID,
        accessToken: String,
        cursor: String?,
    ): StoryPage = StoryPage(hasMore = false, items = emptyList(), nextCursor = null)

    override suspend fun deleteOwnAccount(
        accessToken: String,
        request: AccountDeletionRequest,
    ): AccountDeletionAccepted {
        deletionTokens += accessToken
        deletionRequests += request
        deletionFailure?.let { throw it }
        return AccountDeletionAccepted(
            acceptedAt = java.time.OffsetDateTime.now(),
            status = AccountDeletionStatus.PENDING,
        )
    }
}
