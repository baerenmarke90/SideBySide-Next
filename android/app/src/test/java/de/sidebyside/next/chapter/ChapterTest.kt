package de.sidebyside.next.chapter

import de.sidebyside.next.reference.FakeReferenceContract
import de.sidebyside.next.reference.ReferenceConfig
import de.sidebyside.next.reference.ReferenceViewModel
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
import sidebyside.api.models.ChapterCreate
import sidebyside.api.models.ChapterDetail
import sidebyside.api.models.ChapterPage
import sidebyside.api.models.ChapterUpdate
import sidebyside.api.models.ResourceCapabilities
import sidebyside.api.models.SessionView
import sidebyside.api.models.TokenView

private val SPACE: UUID = UUID.fromString("11111111-1111-4111-8111-111111111111")

/**
 * #355: Chapter CRUD. This slice is deliberately just CRUD for the chapter
 * itself — the typed content relations (which Memories, HeartMoments and
 * Milestones belong to a chapter) are their own slice, mirroring how
 * #531/#532 sequenced Place CRUD before Place relations.
 */
@OptIn(ExperimentalCoroutinesApi::class)
class ChapterTest {
    private val dispatcher = StandardTestDispatcher()

    @Before
    fun setUp() = Dispatchers.setMain(dispatcher)

    @After
    fun tearDown() = Dispatchers.resetMain()

    @Test
    fun loadingPopulatesTheList() = runTest(dispatcher) {
        val chapter = chapter("Our first year")
        val api = ChapterApi(chapters = listOf(chapter))
        val model = ReferenceViewModel(config = ReferenceConfig(BASE_URL), api = api)

        signIn(model)
        model.loadChapters()
        advanceUntilIdle()

        assertEquals(listOf(chapter), model.uiState.value.chapters)
    }

    @Test
    fun addingWithABlankTitleMakesNoCall() = runTest(dispatcher) {
        val api = ChapterApi()
        val model = ReferenceViewModel(config = ReferenceConfig(BASE_URL), api = api)

        signIn(model)
        model.addChapter("   ", "", "", "")
        advanceUntilIdle()

        assertTrue(api.created.isEmpty())
    }

    @Test
    fun addingParsesTheOptionalDates() = runTest(dispatcher) {
        val api = ChapterApi()
        val model = ReferenceViewModel(config = ReferenceConfig(BASE_URL), api = api)

        signIn(model)
        model.addChapter("Our first year", "Moving in and settling down", "2025-01-01", "2025-12-31")
        advanceUntilIdle()

        assertEquals(1, api.created.size)
        assertEquals("Our first year", api.created.first().title)
        assertEquals("Moving in and settling down", api.created.first().description)
        assertEquals(LocalDate.of(2025, 1, 1), api.created.first().startOn)
        assertEquals(LocalDate.of(2025, 12, 31), api.created.first().endOn)
    }

    @Test
    fun addingWithAnUnparseableDateSendsNoDate() = runTest(dispatcher) {
        val api = ChapterApi()
        val model = ReferenceViewModel(config = ReferenceConfig(BASE_URL), api = api)

        signIn(model)
        model.addChapter("Our first year", "", "not a date", "")
        advanceUntilIdle()

        assertEquals(1, api.created.size)
        assertNull(api.created.first().startOn)
        assertNull(api.created.first().endOn)
    }

    @Test
    fun addingCarriesTheChosenPlace() = runTest(dispatcher) {
        val place = UUID.fromString("dddddddd-dddd-4ddd-8ddd-dddddddddddd")
        val api = ChapterApi()
        val model = ReferenceViewModel(config = ReferenceConfig(BASE_URL), api = api)

        signIn(model)
        model.addChapter("Our first year", "", "", "", place)
        advanceUntilIdle()

        assertEquals(place, api.created.single().placeId)
    }

    @Test
    fun editingCanChangeThePlace() = runTest(dispatcher) {
        val place = UUID.fromString("dddddddd-dddd-4ddd-8ddd-dddddddddddd")
        val target = chapter("Our first year", version = 3)
        val api = ChapterApi(chapters = listOf(target))
        val model = ReferenceViewModel(config = ReferenceConfig(BASE_URL), api = api)

        signIn(model)
        model.updateChapter(target, "Our first year", "", "", "", place)
        advanceUntilIdle()

        assertEquals(place, api.updatedFields.single().placeId)
    }

    @Test
    fun updatingSendsTheCurrentVersionAsIfMatch() = runTest(dispatcher) {
        val target = chapter("Old title", version = 4)
        val api = ChapterApi(chapters = listOf(target))
        val model = ReferenceViewModel(config = ReferenceConfig(BASE_URL), api = api)

        signIn(model)
        model.updateChapter(target, "New title", "", "", "")
        advanceUntilIdle()

        assertEquals(1, api.updated.size)
        assertEquals(target.id, api.updated.first().first)
        assertEquals(4, api.updated.first().second)
    }

    @Test
    fun deletingSendsTheEntrysOwnVersion() = runTest(dispatcher) {
        val target = chapter("To delete", version = 2)
        val api = ChapterApi(chapters = listOf(target))
        val model = ReferenceViewModel(config = ReferenceConfig(BASE_URL), api = api)

        signIn(model)
        model.deleteChapter(target)
        advanceUntilIdle()

        assertEquals(listOf(target.id to 2), api.deleted)
    }

    @Test
    fun forgetsChaptersWhenTheSessionEnds() = runTest(dispatcher) {
        val api = ChapterApi(chapters = listOf(chapter("Our first year")))
        val model = ReferenceViewModel(config = ReferenceConfig(BASE_URL), api = api)

        signIn(model)
        model.loadChapters()
        advanceUntilIdle()
        assertTrue(model.uiState.value.chapters.isNotEmpty())

        model.logout()

        assertTrue(model.uiState.value.chapters.isEmpty())
    }

    private suspend fun TestScope.signIn(model: ReferenceViewModel) {
        model.signIn("someone@example.test", "secret")
        advanceUntilIdle()
    }
}

private const val BASE_URL = "https://sidebyside.example"

private val FULL_CAPABILITIES = ResourceCapabilities(canComment = false, canDelete = true, canEdit = true)

private fun chapter(title: String, version: Int = 1) = ChapterDetail(
    capabilities = FULL_CAPABILITIES,
    createdAt = OffsetDateTime.now(),
    createdBy = UUID.randomUUID(),
    creator = AuthorSummary(displayName = "Lea", id = UUID.randomUUID()),
    description = null,
    endOn = null,
    id = UUID.randomUUID(),
    placeId = null,
    spaceId = SPACE,
    startOn = null,
    title = title,
    updatedAt = OffsetDateTime.now(),
    version = version,
)

private class ChapterApi(
    private val chapters: List<ChapterDetail> = emptyList(),
) : FakeReferenceContract() {
    val created = mutableListOf<ChapterCreate>()
    val updated = mutableListOf<Pair<UUID, Int>>()
    val updatedFields = mutableListOf<ChapterUpdate>()
    val deleted = mutableListOf<Pair<UUID, Int>>()

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

    override suspend fun listChapters(
        spaceId: UUID,
        accessToken: String,
        cursor: String?,
    ): ChapterPage = ChapterPage(hasMore = false, items = chapters, nextCursor = null)

    override suspend fun createChapter(
        spaceId: UUID,
        accessToken: String,
        fields: ChapterCreate,
    ): ChapterDetail {
        created += fields
        return chapter(fields.title)
    }

    override suspend fun updateChapter(
        spaceId: UUID,
        accessToken: String,
        chapterId: UUID,
        ifMatch: Int,
        fields: ChapterUpdate,
    ): ChapterDetail {
        updated += chapterId to ifMatch
        updatedFields += fields
        return chapter(fields.title ?: "Updated")
    }

    override suspend fun deleteChapter(spaceId: UUID, accessToken: String, chapterId: UUID, ifMatch: Int) {
        deleted += chapterId to ifMatch
    }
}
