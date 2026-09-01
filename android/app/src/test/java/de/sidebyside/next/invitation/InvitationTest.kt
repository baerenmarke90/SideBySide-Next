package de.sidebyside.next.invitation

import de.sidebyside.next.reference.FakeReferenceContract
import de.sidebyside.next.reference.R
import de.sidebyside.next.reference.ReferenceApiException
import de.sidebyside.next.reference.ReferenceConfig
import de.sidebyside.next.reference.ReferenceContract
import de.sidebyside.next.reference.ReferenceViewModel
import java.time.OffsetDateTime
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
import org.junit.Assert.assertNull
import org.junit.Assert.assertTrue
import org.junit.Before
import org.junit.Test
import sidebyside.api.models.AccountMembershipView
import sidebyside.api.models.AccountView
import sidebyside.api.models.InvitationView
import sidebyside.api.models.IssuedInvitationView
import sidebyside.api.models.MembershipView
import sidebyside.api.models.SessionView
import sidebyside.api.models.StoryPage
import sidebyside.api.models.TokenView

private val SPACE: UUID = UUID.fromString("11111111-1111-4111-8111-111111111111")

/**
 * Accepting and issuing invitations.
 *
 * The one thing worth pinning above the rest: an account with no active Space
 * keeps its session, because accepting an invitation needs that session's own
 * token and there is no other way to reach it.
 */
@OptIn(ExperimentalCoroutinesApi::class)
class InvitationTest {
    private val dispatcher = StandardTestDispatcher()

    @Before
    fun setUp() = Dispatchers.setMain(dispatcher)

    @After
    fun tearDown() = Dispatchers.resetMain()

    @Test
    fun awaitingASpaceKeepsTheSessionUsableForAccepting() = runTest(dispatcher) {
        // The old behaviour discarded the session here, which made accepting
        // an invitation impossible: there was no token left to call it with.
        val api = InvitationApi(memberships = emptyList())
        val model = ReferenceViewModel(config = ReferenceConfig(BASE_URL), api = api)

        model.signIn("someone@example.test", "secret")
        advanceUntilIdle()
        model.acceptInvitation("a-real-token")
        advanceUntilIdle()

        assertEquals(listOf("a-real-token"), api.acceptedTokens)
    }

    @Test
    fun acceptingAValidInvitationResolvesTheSpaceItWasIssuedFor() = runTest(dispatcher) {
        val api = InvitationApi(
            memberships = emptyList(),
            membershipsAfterAccept = listOf(active(SPACE)),
        )
        val model = ReferenceViewModel(config = ReferenceConfig(BASE_URL), api = api)

        model.signIn("someone@example.test", "secret")
        advanceUntilIdle()
        model.acceptInvitation("a-real-token")
        advanceUntilIdle()

        assertTrue(model.uiState.value.loggedIn)
        assertFalse(model.uiState.value.awaitingSpace)
        assertEquals(SPACE, model.uiState.value.activeSpaceId)
    }

    @Test
    fun anExpiredTokenIsReportedRatherThanSilentlyDoingNothing() = runTest(dispatcher) {
        val api = InvitationApi(
            memberships = emptyList(),
            acceptFailure = ReferenceApiException(null, "gone", 409),
        )
        val model = ReferenceViewModel(config = ReferenceConfig(BASE_URL), api = api)

        model.signIn("someone@example.test", "secret")
        advanceUntilIdle()
        model.acceptInvitation("an-old-token")
        advanceUntilIdle()

        assertTrue(model.uiState.value.invitationProblem != null)
        assertTrue(model.uiState.value.awaitingSpace)
    }

    @Test
    fun blankCodeIsRefusedWithoutACall() = runTest(dispatcher) {
        val api = InvitationApi(memberships = emptyList())
        val model = ReferenceViewModel(config = ReferenceConfig(BASE_URL), api = api)

        model.signIn("someone@example.test", "secret")
        advanceUntilIdle()
        model.acceptInvitation("   ")
        advanceUntilIdle()

        assertTrue(api.acceptedTokens.isEmpty())
    }

    @Test
    fun aFullSpaceIsReportedByNameRatherThanAsAVersionConflict() = runTest(dispatcher) {
        // Found on the device: SPACE_FULL was falling through to the generic
        // "the data changed, reload and retry" wording, which is wrong here —
        // no reload makes room for a third partner.
        val api = InvitationApi(
            memberships = listOf(active(SPACE)),
            createFailure = ReferenceApiException("SPACE_FULL", "full", 409),
        )
        val model = ReferenceViewModel(config = ReferenceConfig(BASE_URL), api = api)

        model.signIn("someone@example.test", "secret")
        advanceUntilIdle()
        model.createInvitation()
        advanceUntilIdle()

        assertEquals(R.string.invitation_space_full_title, model.uiState.value.invitationProblem?.titleRes)
    }

    @Test
    fun acceptingACodeForASpaceAlreadySharedNamesThatRatherThanCallingItInvalid() =
        runTest(dispatcher) {
            val api = InvitationApi(
                memberships = emptyList(),
                acceptFailure = ReferenceApiException("ACCOUNT_ALREADY_MEMBER", "member", 409),
            )
            val model = ReferenceViewModel(config = ReferenceConfig(BASE_URL), api = api)

            model.signIn("someone@example.test", "secret")
            advanceUntilIdle()
            model.acceptInvitation("a-code")
            advanceUntilIdle()

            assertEquals(
                R.string.invitation_already_member_title,
                model.uiState.value.invitationProblem?.titleRes,
            )
        }

    @Test
    fun issuingAnInvitationExposesTheTokenExactlyOnce() = runTest(dispatcher) {
        val api = InvitationApi(memberships = listOf(active(SPACE)))
        val model = ReferenceViewModel(config = ReferenceConfig(BASE_URL), api = api)

        model.signIn("someone@example.test", "secret")
        advanceUntilIdle()
        model.createInvitation()
        advanceUntilIdle()

        assertEquals("fresh-token", model.uiState.value.issuedInvitationToken)

        model.dismissIssuedInvitationToken()
        assertNull(model.uiState.value.issuedInvitationToken)
    }

    @Test
    fun revokingRereadsTheList() = runTest(dispatcher) {
        val invitationId = UUID.randomUUID()
        val api = InvitationApi(
            memberships = listOf(active(SPACE)),
            invitations = listOf(invitation(invitationId)),
        )
        val model = ReferenceViewModel(config = ReferenceConfig(BASE_URL), api = api)

        model.signIn("someone@example.test", "secret")
        advanceUntilIdle()
        model.loadInvitations()
        advanceUntilIdle()
        model.revokeInvitation(invitationId)
        advanceUntilIdle()

        assertEquals(listOf(invitationId), api.revokedIds)
        assertTrue(api.listCalls >= 2)
    }

    @Test
    fun forgetsInvitationsWhenTheSessionEnds() = runTest(dispatcher) {
        val api = InvitationApi(
            memberships = listOf(active(SPACE)),
            invitations = listOf(invitation(UUID.randomUUID())),
        )
        val model = ReferenceViewModel(config = ReferenceConfig(BASE_URL), api = api)

        model.signIn("someone@example.test", "secret")
        advanceUntilIdle()
        model.loadInvitations()
        advanceUntilIdle()
        assertTrue(model.uiState.value.issuedInvitations.isNotEmpty())

        model.logout()

        assertTrue(model.uiState.value.issuedInvitations.isEmpty())
    }
}

private const val BASE_URL = "https://sidebyside.example"

private fun active(spaceId: UUID) =
    AccountMembershipView(role = "PARTNER", spaceId = spaceId, status = "ACTIVE")

private fun invitation(id: UUID) = InvitationView(
    createdAt = OffsetDateTime.now(),
    expiresAt = OffsetDateTime.now().plusDays(7),
    id = id,
)

private class InvitationApi(
    private val memberships: List<AccountMembershipView>,
    private val membershipsAfterAccept: List<AccountMembershipView>? = null,
    private val acceptFailure: Throwable? = null,
    private val createFailure: Throwable? = null,
    private val invitations: List<InvitationView> = emptyList(),
) : FakeReferenceContract() {
    val acceptedTokens = mutableListOf<String>()
    val revokedIds = mutableListOf<UUID>()
    var listCalls = 0
    private var accepted = false

    override suspend fun signIn(email: String, password: String): SessionView = SessionView(
        account = AccountView(displayName = "Lea", id = UUID.randomUUID()),
        tokens = TokenView(
            accessExpiresAt = OffsetDateTime.now(),
            accessToken = "access",
            refreshExpiresAt = OffsetDateTime.now(),
            refreshToken = "refresh",
        ),
    )

    override suspend fun listMemberships(accessToken: String): List<AccountMembershipView> =
        if (accepted && membershipsAfterAccept != null) membershipsAfterAccept else memberships

    override suspend fun getTimeline(spaceId: UUID, accessToken: String, cursor: String?): StoryPage =
        StoryPage(hasMore = false, items = emptyList(), nextCursor = null)

    override suspend fun acceptInvitation(accessToken: String, token: String): MembershipView {
        acceptedTokens += token
        acceptFailure?.let { throw it }
        accepted = true
        return MembershipView(role = "PARTNER", spaceId = SPACE, status = "ACTIVE")
    }

    override suspend fun listInvitations(spaceId: UUID, accessToken: String): List<InvitationView> {
        listCalls += 1
        return invitations
    }

    override suspend fun createInvitation(
        spaceId: UUID,
        accessToken: String,
    ): IssuedInvitationView {
        createFailure?.let { throw it }
        return IssuedInvitationView(
        createdAt = OffsetDateTime.now(),
        expiresAt = OffsetDateTime.now().plusDays(7),
            id = UUID.randomUUID(),
            token = "fresh-token",
        )
    }

    override suspend fun revokeInvitation(spaceId: UUID, accessToken: String, invitationId: UUID) {
        revokedIds += invitationId
    }
}
