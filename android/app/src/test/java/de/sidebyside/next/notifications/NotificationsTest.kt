package de.sidebyside.next.notifications

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
import sidebyside.api.models.NotificationItem
import sidebyside.api.models.NotificationKind
import sidebyside.api.models.NotificationPage
import sidebyside.api.models.NotificationUnreadCount
import sidebyside.api.models.NotificationsReadAllResult
import sidebyside.api.models.SessionView
import sidebyside.api.models.TokenView

/**
 * #357: notifications list, unread count, mark-one and mark-all. The
 * property worth pinning beyond ordinary loading is that both mark actions
 * refresh the unread count from the server rather than decrementing a
 * locally held number — the server is authoritative over what counts as
 * unread, same as every other server-authoritative state this delivery has
 * kept out of client hands.
 */
@OptIn(ExperimentalCoroutinesApi::class)
class NotificationsTest {
    private val dispatcher = StandardTestDispatcher()

    @Before
    fun setUp() = Dispatchers.setMain(dispatcher)

    @After
    fun tearDown() = Dispatchers.resetMain()

    @Test
    fun loadingPopulatesTheList() = runTest(dispatcher) {
        val notification = notification()
        val api = NotificationApi(notifications = listOf(notification))
        val model = ReferenceViewModel(config = ReferenceConfig(BASE_URL), api = api)

        signIn(model)
        model.loadNotifications()
        advanceUntilIdle()

        assertEquals(listOf(notification), model.uiState.value.notifications)
    }

    @Test
    fun loadingTheUnreadCountPopulatesIt() = runTest(dispatcher) {
        val api = NotificationApi(unreadCount = 3)
        val model = ReferenceViewModel(config = ReferenceConfig(BASE_URL), api = api)

        signIn(model)
        model.loadUnreadNotificationCount()
        advanceUntilIdle()

        assertEquals(3, model.uiState.value.unreadNotificationCount)
    }

    @Test
    fun markingOneReadSendsItsIdAndReloadsTheListAndCount() = runTest(dispatcher) {
        val target = notification()
        val api = NotificationApi(notifications = listOf(target), unreadCount = 1)
        val model = ReferenceViewModel(config = ReferenceConfig(BASE_URL), api = api)

        signIn(model)
        model.markNotificationRead(target)
        advanceUntilIdle()

        assertEquals(listOf(target.id), api.markedRead)
        assertTrue(api.listCallCount >= 1)
        assertTrue(api.unreadCountCallCount >= 1)
    }

    @Test
    fun markingAllReadCallsTheReadAllEndpointAndReloads() = runTest(dispatcher) {
        val api = NotificationApi(notifications = listOf(notification()), unreadCount = 5)
        val model = ReferenceViewModel(config = ReferenceConfig(BASE_URL), api = api)

        signIn(model)
        model.markAllNotificationsRead()
        advanceUntilIdle()

        assertEquals(1, api.markAllCallCount)
        assertTrue(api.listCallCount >= 1)
        assertTrue(api.unreadCountCallCount >= 1)
    }

    @Test
    fun forgetsNotificationsWhenTheSessionEnds() = runTest(dispatcher) {
        val api = NotificationApi(notifications = listOf(notification()), unreadCount = 2)
        val model = ReferenceViewModel(config = ReferenceConfig(BASE_URL), api = api)

        signIn(model)
        model.loadNotifications()
        model.loadUnreadNotificationCount()
        advanceUntilIdle()
        assertTrue(model.uiState.value.notifications.isNotEmpty())
        assertEquals(2, model.uiState.value.unreadNotificationCount)

        model.logout()

        assertTrue(model.uiState.value.notifications.isEmpty())
        assertEquals(0, model.uiState.value.unreadNotificationCount)
    }

    private suspend fun TestScope.signIn(model: ReferenceViewModel) {
        model.signIn("someone@example.test", "secret")
        advanceUntilIdle()
    }
}

private const val BASE_URL = "https://sidebyside.example"
private val SPACE: UUID = UUID.fromString("11111111-1111-4111-8111-111111111111")

private fun notification() = NotificationItem(
    actorId = UUID.randomUUID(),
    createdAt = OffsetDateTime.now(),
    id = UUID.randomUUID(),
    kind = NotificationKind.COMMENT_CREATED,
    readAt = null,
    sourceEventId = UUID.randomUUID(),
    targetId = null,
    targetType = null,
)

private class NotificationApi(
    private val notifications: List<NotificationItem> = emptyList(),
    private val unreadCount: Int = 0,
) : FakeReferenceContract() {
    val markedRead = mutableListOf<UUID>()
    var markAllCallCount = 0
        private set
    var listCallCount = 0
        private set
    var unreadCountCallCount = 0
        private set

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
        listOf(AccountMembershipView(role = "PARTNER", spaceId = SPACE, status = "ACTIVE"))

    override suspend fun listNotifications(
        spaceId: UUID,
        accessToken: String,
        cursor: String?,
    ): NotificationPage {
        listCallCount += 1
        return NotificationPage(hasMore = false, items = notifications, nextCursor = null)
    }

    override suspend fun getNotificationUnreadCount(spaceId: UUID, accessToken: String): NotificationUnreadCount {
        unreadCountCallCount += 1
        return NotificationUnreadCount(unreadCount = unreadCount)
    }

    override suspend fun markNotificationRead(
        spaceId: UUID,
        accessToken: String,
        notificationId: UUID,
    ): NotificationItem {
        markedRead += notificationId
        return notification()
    }

    override suspend fun markAllNotificationsRead(spaceId: UUID, accessToken: String): NotificationsReadAllResult {
        markAllCallCount += 1
        return NotificationsReadAllResult(readThrough = OffsetDateTime.now(), updated = notifications.size)
    }
}
