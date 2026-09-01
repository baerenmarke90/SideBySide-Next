package de.sidebyside.next.activity

import de.sidebyside.next.reference.FakeReferenceContract
import de.sidebyside.next.reference.ReferenceConfig
import de.sidebyside.next.reference.ReferenceViewModel
import java.time.OffsetDateTime
import java.util.UUID
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.ExperimentalCoroutinesApi
import kotlinx.coroutines.test.StandardTestDispatcher
import kotlinx.coroutines.test.TestScope
import kotlinx.coroutines.test.advanceUntilIdle
import kotlinx.coroutines.test.resetMain
import kotlinx.coroutines.test.runTest
import kotlinx.coroutines.test.setMain
import org.junit.After
import org.junit.Assert.assertEquals
import org.junit.Assert.assertTrue
import org.junit.Before
import org.junit.Test
import sidebyside.api.models.AccountMembershipView
import sidebyside.api.models.AccountView
import sidebyside.api.models.ActivityItem
import sidebyside.api.models.ActivityKind
import sidebyside.api.models.ActivityPage
import sidebyside.api.models.SessionView
import sidebyside.api.models.TokenView

private val SPACE: UUID = UUID.fromString("11111111-1111-4111-8111-111111111111")

/** #357: the shared, read-only Activity feed. */
@OptIn(ExperimentalCoroutinesApi::class)
class ActivityTest {
    private val dispatcher = StandardTestDispatcher()

    @Before
    fun setUp() = Dispatchers.setMain(dispatcher)

    @After
    fun tearDown() = Dispatchers.resetMain()

    @Test
    fun loadingPopulatesTheList() = runTest(dispatcher) {
        val entry = activityItem()
        val api = ActivityApi(entries = listOf(entry))
        val model = ReferenceViewModel(config = ReferenceConfig(BASE_URL), api = api)

        signIn(model)
        model.loadActivity()
        advanceUntilIdle()

        assertEquals(listOf(entry), model.uiState.value.activity)
    }

    @Test
    fun forgetsActivityWhenTheSessionEnds() = runTest(dispatcher) {
        val api = ActivityApi(entries = listOf(activityItem()))
        val model = ReferenceViewModel(config = ReferenceConfig(BASE_URL), api = api)

        signIn(model)
        model.loadActivity()
        advanceUntilIdle()
        assertTrue(model.uiState.value.activity.isNotEmpty())

        model.logout()

        assertTrue(model.uiState.value.activity.isEmpty())
    }

    @Test
    fun forgetsActivityWhenTheSpaceChanges() = runTest(dispatcher) {
        val otherSpace = UUID.fromString("22222222-2222-4222-8222-222222222222")
        val api = ActivityApi(entries = listOf(activityItem()), otherSpaces = listOf(otherSpace))
        val model = ReferenceViewModel(config = ReferenceConfig(BASE_URL), api = api)

        signIn(model)
        model.loadActivity()
        advanceUntilIdle()
        assertTrue(model.uiState.value.activity.isNotEmpty())

        model.selectSpace(otherSpace)
        advanceUntilIdle()

        assertTrue(model.uiState.value.activity.isEmpty())
    }

    private suspend fun TestScope.signIn(model: ReferenceViewModel) {
        model.signIn("someone@example.test", "secret")
        advanceUntilIdle()
    }
}

private const val BASE_URL = "https://sidebyside.example"

private fun activityItem() = ActivityItem(
    actorId = UUID.randomUUID(),
    createdAt = OffsetDateTime.now(),
    id = UUID.randomUUID(),
    kind = ActivityKind.MEMORY_CREATED,
    occurredAt = OffsetDateTime.now(),
    sourceEventId = UUID.randomUUID(),
    targetId = null,
    targetType = null,
)

private class ActivityApi(
    private val entries: List<ActivityItem> = emptyList(),
    private val otherSpaces: List<UUID> = emptyList(),
) : FakeReferenceContract() {
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
        listOf(AccountMembershipView(role = "PARTNER", spaceId = SPACE, status = "ACTIVE")) +
            otherSpaces.map { AccountMembershipView(role = "PARTNER", spaceId = it, status = "ACTIVE") }

    override suspend fun getActivity(spaceId: UUID, accessToken: String, cursor: String?): ActivityPage =
        ActivityPage(hasMore = false, items = if (spaceId == SPACE) entries else emptyList(), nextCursor = null)
}
