package de.sidebyside.next.reference

import android.content.Context
import androidx.test.core.app.ApplicationProvider
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
import org.junit.runner.RunWith
import org.robolectric.RobolectricTestRunner
import org.robolectric.annotation.Config
import sidebyside.api.models.AccountDeletionAccepted
import sidebyside.api.models.AccountDeletionRequest
import sidebyside.api.models.AccountDeletionStatus
import sidebyside.api.models.AccountMembershipView
import sidebyside.api.models.AccountView
import sidebyside.api.models.SessionView
import sidebyside.api.models.StoryPage
import sidebyside.api.models.TokenView

private const val SPACE_PREFERENCE_DELETION_BASE_URL = "https://sidebyside.example"
private val SPACE_PREFERENCE_DELETION_SPACE: UUID = UUID.fromString("11111111-1111-4111-8111-111111111111")
private val OTHER_SPACE_PREFERENCE_DELETION_SPACE: UUID = UUID.fromString("22222222-2222-4222-8222-222222222222")

@OptIn(ExperimentalCoroutinesApi::class)
@RunWith(RobolectricTestRunner::class)
@Config(sdk = [35])
class SpacePreferenceDeletionTest {
    private val dispatcher = StandardTestDispatcher()
    private val context: Context get() = ApplicationProvider.getApplicationContext()

    @Before
    fun setUp() = Dispatchers.setMain(dispatcher)

    @After
    fun tearDown() = Dispatchers.resetMain()

    @Test
    fun acceptedDeletionRemovesOnlyDeletedAccountsPersistentPreference() = runTest(dispatcher) {
        val api = PreferenceDeletionApi(accountId = UUID.randomUUID())
        val otherAccountId = UUID.randomUUID()
        val store = SharedPreferencesSpaceStore(context)
        store.rememberSpace(api.accountId, SPACE_PREFERENCE_DELETION_SPACE)
        store.rememberSpace(otherAccountId, OTHER_SPACE_PREFERENCE_DELETION_SPACE)
        val model = model(api, store)

        model.signIn("someone@example.test", "secret")
        advanceUntilIdle()
        model.deleteOwnAccount()
        advanceUntilIdle()

        assertNull(store.rememberedSpace(api.accountId))
        assertEquals(
            OTHER_SPACE_PREFERENCE_DELETION_SPACE,
            store.rememberedSpace(otherAccountId),
        )
        assertFalse(model.uiState.value.loggedIn)

        store.forgetAccount(api.accountId)
        assertNull(store.rememberedSpace(api.accountId))
    }

    @Test
    fun rejectedDeletionRetainsPersistentPreference() = runTest(dispatcher) {
        val api = PreferenceDeletionApi(
            accountId = UUID.randomUUID(),
            deletionFailure = ReferenceApiException(
                code = "ACCOUNT_DELETION_AUTHORITY_UNAVAILABLE",
                message = "unavailable",
                status = 503,
            ),
        )
        val store = SharedPreferencesSpaceStore(context)
        store.rememberSpace(api.accountId, SPACE_PREFERENCE_DELETION_SPACE)
        val model = model(api, store)

        model.signIn("someone@example.test", "secret")
        advanceUntilIdle()
        model.deleteOwnAccount()
        advanceUntilIdle()

        assertEquals(
            SPACE_PREFERENCE_DELETION_SPACE,
            store.rememberedSpace(api.accountId),
        )
        assertTrue(model.uiState.value.loggedIn)
    }

    @Test
    fun ordinaryLogoutRetainsPersistentPreference() = runTest(dispatcher) {
        val api = PreferenceDeletionApi(accountId = UUID.randomUUID())
        val store = SharedPreferencesSpaceStore(context)
        store.rememberSpace(api.accountId, SPACE_PREFERENCE_DELETION_SPACE)
        val model = model(api, store)

        model.signIn("someone@example.test", "secret")
        advanceUntilIdle()
        model.logout()

        assertEquals(
            SPACE_PREFERENCE_DELETION_SPACE,
            store.rememberedSpace(api.accountId),
        )
        assertFalse(model.uiState.value.loggedIn)
    }

    @Test
    fun inMemoryForgetIsIdempotentAndAccountScoped() {
        val deletedAccountId = UUID.randomUUID()
        val otherAccountId = UUID.randomUUID()
        val store = InMemorySpacePreferenceStore()
        store.rememberSpace(deletedAccountId, SPACE_PREFERENCE_DELETION_SPACE)
        store.rememberSpace(otherAccountId, OTHER_SPACE_PREFERENCE_DELETION_SPACE)

        store.forgetAccount(deletedAccountId)
        store.forgetAccount(deletedAccountId)

        assertNull(store.rememberedSpace(deletedAccountId))
        assertEquals(
            OTHER_SPACE_PREFERENCE_DELETION_SPACE,
            store.rememberedSpace(otherAccountId),
        )
    }

    private fun model(
        api: ReferenceContract,
        store: SpacePreferenceStore,
    ) = ReferenceViewModel(
        config = ReferenceConfig(SPACE_PREFERENCE_DELETION_BASE_URL),
        api = api,
        spaceStore = store,
    )
}

private class PreferenceDeletionApi(
    val accountId: UUID,
    private val deletionFailure: Throwable? = null,
) : FakeReferenceContract() {
    override suspend fun signIn(email: String, password: String): SessionView = SessionView(
        account = AccountView(displayName = "Someone", id = accountId),
        tokens = TokenView(
            accessExpiresAt = java.time.OffsetDateTime.now(),
            accessToken = "access",
            refreshExpiresAt = java.time.OffsetDateTime.now(),
            refreshToken = "refresh",
        ),
    )

    override suspend fun listMemberships(accessToken: String): List<AccountMembershipView> =
        listOf(
            AccountMembershipView(
                role = "PARTNER",
                spaceId = SPACE_PREFERENCE_DELETION_SPACE,
                status = "ACTIVE",
            ),
        )

    override suspend fun getTimeline(
        spaceId: UUID,
        accessToken: String,
        cursor: String?,
    ): StoryPage = StoryPage(hasMore = false, items = emptyList(), nextCursor = null)

    override suspend fun deleteOwnAccount(
        accessToken: String,
        request: AccountDeletionRequest,
    ): AccountDeletionAccepted {
        deletionFailure?.let { throw it }
        return AccountDeletionAccepted(
            acceptedAt = java.time.OffsetDateTime.now(),
            status = AccountDeletionStatus.PENDING,
        )
    }
}
