package de.sidebyside.next.story

import de.sidebyside.next.reference.FakeReferenceContract
import de.sidebyside.next.reference.ReferenceApiException
import de.sidebyside.next.reference.ReferenceConfig
import de.sidebyside.next.reference.ReferenceContract
import de.sidebyside.next.reference.ReferenceViewModel
import de.sidebyside.next.shell.UiStateKind
import java.time.LocalDate
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
import org.junit.Assert.assertNull
import org.junit.Assert.assertTrue
import org.junit.Before
import org.junit.Test
import sidebyside.api.models.AccountMembershipView
import sidebyside.api.models.AccountView
import sidebyside.api.models.AuthorSummary
import sidebyside.api.models.ContentVisibility
import sidebyside.api.models.HeartEmotion
import sidebyside.api.models.HeartMomentCreate
import sidebyside.api.models.HeartMomentDetail
import sidebyside.api.models.HeartMomentPage
import sidebyside.api.models.HeartMomentUpdate
import sidebyside.api.models.HeartMomentVisibilityChange
import sidebyside.api.models.ResourceCapabilities
import sidebyside.api.models.SessionView
import sidebyside.api.models.StoryPage
import sidebyside.api.models.TokenView

private val SPACE: UUID = UUID.fromString("11111111-1111-4111-8111-111111111111")
private val MOMENT: UUID = UUID.fromString("44444444-4444-4444-8444-444444444444")

/**
 * HeartMoments, and the boundary that makes them different from a Memory.
 *
 * `SHARED -> PRIVATE` deletes the moment's comments and going back does not
 * restore them, so the client must never let that ride along with an edit. The
 * server keeps the two apart; these tests keep the client honest about it.
 */
@OptIn(ExperimentalCoroutinesApi::class)
class HeartMomentTest {
    private val dispatcher = StandardTestDispatcher()

    @Before
    fun setUp() = Dispatchers.setMain(dispatcher)

    @After
    fun tearDown() = Dispatchers.resetMain()

    @Test
    fun showsWhatTheServerReturnsWithoutFilteringItAgain() = runTest(dispatcher) {
        // The server already narrows this to what the account may read. A
        // second filter here would be a second, divergent rule.
        val api = HeartMomentApi(page = listOf(moment(ContentVisibility.PRIVATE), moment(ContentVisibility.SHARED)))
        val model = signedIn(api)

        model.loadHeartMoments()
        advanceUntilIdle()

        assertEquals(2, model.uiState.value.heartMoments.size)
        assertNull(api.listedVisibility.singleOrNull())
    }

    @Test
    fun anEditNeverCarriesVisibility() = runTest(dispatcher) {
        // The one that matters: a text change must not be able to make a
        // shared moment private, because that deletes its comments for good.
        val api = HeartMomentApi(page = listOf(moment(ContentVisibility.SHARED)))
        val model = signedIn(api)

        model.loadHeartMoments()
        advanceUntilIdle()
        model.updateHeartMoment(MOMENT, "New words", HeartEmotion.LOVED)
        advanceUntilIdle()

        assertEquals(1, api.updates.size)
        assertTrue(api.visibilityChanges.isEmpty())
    }

    @Test
    fun changingVisibilityUsesItsOwnCallAndTheCurrentVersion() = runTest(dispatcher) {
        val api = HeartMomentApi(page = listOf(moment(ContentVisibility.SHARED, version = 3)))
        val model = signedIn(api)

        model.loadHeartMoments()
        advanceUntilIdle()
        model.changeHeartMomentVisibility(MOMENT, ContentVisibility.PRIVATE)
        advanceUntilIdle()

        assertEquals(listOf(ContentVisibility.PRIVATE), api.visibilityChanges.map { it.visibility })
        assertEquals(listOf(3), api.visibilityVersions)
        assertTrue(api.updates.isEmpty())
    }

    @Test
    fun rereadsTheStoryWhenVisibilityChanges() = runTest(dispatcher) {
        // A moment enters or leaves the shared history with this change; a
        // Story left as it was would keep showing something now private.
        val api = HeartMomentApi(page = listOf(moment(ContentVisibility.SHARED)))
        val model = signedIn(api)

        model.loadHeartMoments()
        advanceUntilIdle()
        val before = api.timelineCalls
        model.changeHeartMomentVisibility(MOMENT, ContentVisibility.PRIVATE)
        advanceUntilIdle()

        assertTrue(api.timelineCalls > before)
    }

    @Test
    fun createsAPrivateMomentAsPrivate() = runTest(dispatcher) {
        val api = HeartMomentApi()
        val model = signedIn(api)

        model.createHeartMoment("Kept to myself", HeartEmotion.GRATEFUL, "", ContentVisibility.PRIVATE)
        advanceUntilIdle()

        assertEquals(ContentVisibility.PRIVATE, api.created.single().visibility)
    }

    @Test
    fun refusesAnEmptyMomentWithoutSendingAnything() = runTest(dispatcher) {
        val api = HeartMomentApi()
        val model = signedIn(api)

        model.createHeartMoment("   ", HeartEmotion.LOVED, "", ContentVisibility.SHARED)
        advanceUntilIdle()

        assertTrue(api.created.isEmpty())
    }

    @Test
    fun reportsAConflictRatherThanOverwritingThePartnersChange() = runTest(dispatcher) {
        val api = HeartMomentApi(
            page = listOf(moment(ContentVisibility.SHARED)),
            visibilityFailure = ReferenceApiException(null, "conflict", 409),
        )
        val model = signedIn(api)

        model.loadHeartMoments()
        advanceUntilIdle()
        model.changeHeartMomentVisibility(MOMENT, ContentVisibility.PRIVATE)
        advanceUntilIdle()

        assertEquals(UiStateKind.Conflict, model.uiState.value.heartMomentsProblem?.kind)
    }

    @Test
    fun forgetsPrivateMomentsWhenTheSpaceChanges() = runTest(dispatcher) {
        // Private text must not survive into a session that is not the one it
        // was read in.
        val api = HeartMomentApi(page = listOf(moment(ContentVisibility.PRIVATE)))
        val model = signedIn(api)

        model.loadHeartMoments()
        advanceUntilIdle()
        assertTrue(model.uiState.value.heartMoments.isNotEmpty())

        model.logout()

        assertTrue(model.uiState.value.heartMoments.isEmpty())
    }

    private fun TestScope.signedIn(api: ReferenceContract): ReferenceViewModel {
        val model = ReferenceViewModel(config = ReferenceConfig(BASE_URL), api = api)
        model.signIn("someone@example.test", "secret")
        advanceUntilIdle()
        return model
    }
}

private const val BASE_URL = "https://sidebyside.example"

private fun moment(visibility: ContentVisibility, version: Int = 1) = HeartMomentDetail(
    attachment = null,
    author = AuthorSummary(displayName = "Lea", id = UUID.randomUUID()),
    authorId = UUID.randomUUID(),
    capabilities = ResourceCapabilities(canComment = true, canDelete = true, canEdit = true),
    createdAt = OffsetDateTime.now(),
    emotion = HeartEmotion.GRATEFUL,
    happenedOn = LocalDate.of(2026, 8, 18),
    id = MOMENT,
    spaceId = SPACE,
    text = "A moment worth keeping",
    updatedAt = OffsetDateTime.now(),
    version = version,
    visibility = visibility,
)

private class HeartMomentApi(
    private val page: List<HeartMomentDetail> = emptyList(),
    private val visibilityFailure: Throwable? = null,
) : FakeReferenceContract() {
    val created = mutableListOf<HeartMomentCreate>()
    val updates = mutableListOf<HeartMomentUpdate>()
    val visibilityChanges = mutableListOf<HeartMomentVisibilityChange>()
    val visibilityVersions = mutableListOf<Int>()
    val listedVisibility = mutableListOf<ContentVisibility?>()
    var timelineCalls = 0

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

    override suspend fun getTimeline(
        spaceId: UUID,
        accessToken: String,
        cursor: String?,
    ): StoryPage {
        timelineCalls += 1
        return StoryPage(hasMore = false, items = emptyList(), nextCursor = null)
    }

    override suspend fun listHeartMoments(
        spaceId: UUID,
        accessToken: String,
        visibility: ContentVisibility?,
    ): HeartMomentPage {
        listedVisibility += visibility
        return HeartMomentPage(hasMore = false, items = page, nextCursor = null)
    }

    override suspend fun createHeartMoment(
        spaceId: UUID,
        accessToken: String,
        heartMoment: HeartMomentCreate,
    ): HeartMomentDetail {
        created += heartMoment
        return moment(heartMoment.visibility)
    }

    override suspend fun updateHeartMoment(
        spaceId: UUID,
        accessToken: String,
        heartMomentId: UUID,
        ifMatch: Int,
        update: HeartMomentUpdate,
    ): HeartMomentDetail {
        updates += update
        return moment(ContentVisibility.SHARED, version = ifMatch + 1)
    }

    override suspend fun changeHeartMomentVisibility(
        spaceId: UUID,
        accessToken: String,
        heartMomentId: UUID,
        ifMatch: Int,
        change: HeartMomentVisibilityChange,
    ): HeartMomentDetail {
        visibilityVersions += ifMatch
        visibilityChanges += change
        visibilityFailure?.let { throw it }
        return moment(change.visibility, version = ifMatch + 1)
    }

    override suspend fun deleteHeartMoment(
        spaceId: UUID,
        accessToken: String,
        heartMomentId: UUID,
        ifMatch: Int,
    ) = Unit
}
