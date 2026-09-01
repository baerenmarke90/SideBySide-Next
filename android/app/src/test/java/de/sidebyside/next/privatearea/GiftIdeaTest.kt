package de.sidebyside.next.privatearea

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
import org.junit.Assert.assertNull
import org.junit.Assert.assertTrue
import org.junit.Before
import org.junit.Test
import sidebyside.api.models.AccountMembershipView
import sidebyside.api.models.AccountView
import sidebyside.api.models.GiftIdeaCreate
import sidebyside.api.models.GiftIdeaDetail
import sidebyside.api.models.GiftIdeaPage
import sidebyside.api.models.GiftIdeaStatus
import sidebyside.api.models.GiftIdeaUpdate
import sidebyside.api.models.ResourceCapabilities
import sidebyside.api.models.SessionView
import sidebyside.api.models.TokenView

private val SPACE: UUID = UUID.fromString("11111111-1111-4111-8111-111111111111")

/**
 * #356: owner-only GiftIdea CRUD, plus the status-change path. The one
 * property worth pinning beyond ordinary CRUD is that a status change never
 * encodes M3-D17's transition graph client-side — it only ever sends the
 * requested target status and lets the server accept or reject it.
 */
@OptIn(ExperimentalCoroutinesApi::class)
class GiftIdeaTest {
    private val dispatcher = StandardTestDispatcher()

    @Before
    fun setUp() = Dispatchers.setMain(dispatcher)

    @After
    fun tearDown() = Dispatchers.resetMain()

    @Test
    fun loadingPopulatesTheList() = runTest(dispatcher) {
        val idea = giftIdea("Cozy blanket")
        val api = GiftIdeaApi(ideas = listOf(idea))
        val model = ReferenceViewModel(config = ReferenceConfig(BASE_URL), api = api)

        signIn(model)
        model.loadGiftIdeas()
        advanceUntilIdle()

        assertEquals(listOf(idea), model.uiState.value.giftIdeas)
    }

    @Test
    fun addingWithABlankTitleMakesNoCall() = runTest(dispatcher) {
        val api = GiftIdeaApi()
        val model = ReferenceViewModel(config = ReferenceConfig(BASE_URL), api = api)

        signIn(model)
        model.addGiftIdea("   ", "", "", "", "", "", "", false)
        advanceUntilIdle()

        assertTrue(api.created.isEmpty())
    }

    @Test
    fun addingSendsBlankOptionalFieldsAsNull() = runTest(dispatcher) {
        val api = GiftIdeaApi()
        val model = ReferenceViewModel(config = ReferenceConfig(BASE_URL), api = api)

        signIn(model)
        model.addGiftIdea("Cozy blanket", "", "", "", "", "", "", true)
        advanceUntilIdle()

        assertEquals(1, api.created.size)
        val sent = api.created.first()
        assertEquals("Cozy blanket", sent.title)
        assertNull(sent.description)
        assertNull(sent.occasion)
        assertNull(sent.recipient)
        assertNull(sent.priceText)
        assertNull(sent.url)
        assertNull(sent.targetOn)
        assertEquals(true, sent.pinned)
    }

    @Test
    fun addingWithAnUnparseableTargetDateSendsNoDate() = runTest(dispatcher) {
        val api = GiftIdeaApi()
        val model = ReferenceViewModel(config = ReferenceConfig(BASE_URL), api = api)

        signIn(model)
        model.addGiftIdea("Cozy blanket", "", "", "", "", "", "not a date", false)
        advanceUntilIdle()

        assertEquals(1, api.created.size)
        assertNull(api.created.first().targetOn)
    }

    @Test
    fun updatingSendsTheCurrentVersionAsIfMatch() = runTest(dispatcher) {
        val target = giftIdea("Old title", version = 4)
        val api = GiftIdeaApi(ideas = listOf(target))
        val model = ReferenceViewModel(config = ReferenceConfig(BASE_URL), api = api)

        signIn(model)
        model.updateGiftIdea(target, "New title", "", "", "", "", "", "", false)
        advanceUntilIdle()

        assertEquals(1, api.updated.size)
        assertEquals(target.id, api.updated.first().first)
        assertEquals(4, api.updated.first().second)
    }

    @Test
    fun changingStatusSendsOnlyTheRequestedTargetStatus() = runTest(dispatcher) {
        val target = giftIdea("Cozy blanket", version = 2)
        val api = GiftIdeaApi(ideas = listOf(target))
        val model = ReferenceViewModel(config = ReferenceConfig(BASE_URL), api = api)

        signIn(model)
        model.changeGiftIdeaStatus(target, GiftIdeaStatus.GIVEN)
        advanceUntilIdle()

        assertEquals(1, api.statusUpdates.size)
        val (id, ifMatch, fields) = api.statusUpdates.first()
        assertEquals(target.id, id)
        assertEquals(2, ifMatch)
        assertEquals(GiftIdeaStatus.GIVEN, fields.status)
        // Only the status field is set; a field-editing update would carry a title too.
        assertNull(fields.title)
    }

    @Test
    fun deletingSendsTheEntrysOwnVersion() = runTest(dispatcher) {
        val target = giftIdea("To delete", version = 3)
        val api = GiftIdeaApi(ideas = listOf(target))
        val model = ReferenceViewModel(config = ReferenceConfig(BASE_URL), api = api)

        signIn(model)
        model.deleteGiftIdea(target)
        advanceUntilIdle()

        assertEquals(listOf(target.id to 3), api.deleted)
    }

    @Test
    fun forgetsGiftIdeasWhenTheSessionEnds() = runTest(dispatcher) {
        val api = GiftIdeaApi(ideas = listOf(giftIdea("Cozy blanket")))
        val model = ReferenceViewModel(config = ReferenceConfig(BASE_URL), api = api)

        signIn(model)
        model.loadGiftIdeas()
        advanceUntilIdle()
        assertTrue(model.uiState.value.giftIdeas.isNotEmpty())

        model.logout()

        assertTrue(model.uiState.value.giftIdeas.isEmpty())
    }

    private suspend fun TestScope.signIn(model: ReferenceViewModel) {
        model.signIn("someone@example.test", "secret")
        advanceUntilIdle()
    }
}

private const val BASE_URL = "https://sidebyside.example"

private val FULL_CAPABILITIES = ResourceCapabilities(canComment = false, canDelete = true, canEdit = true)

private fun giftIdea(title: String, version: Int = 1) = GiftIdeaDetail(
    capabilities = FULL_CAPABILITIES,
    createdAt = OffsetDateTime.now(),
    description = null,
    id = UUID.randomUUID(),
    occasion = null,
    ownerId = UUID.randomUUID(),
    pinned = false,
    priceText = null,
    recipient = null,
    spaceId = SPACE,
    status = GiftIdeaStatus.IDEA,
    targetOn = null,
    title = title,
    updatedAt = OffsetDateTime.now(),
    url = null,
    version = version,
)

private class GiftIdeaApi(
    private val ideas: List<GiftIdeaDetail> = emptyList(),
) : FakeReferenceContract() {
    val created = mutableListOf<GiftIdeaCreate>()
    val updated = mutableListOf<Pair<UUID, Int>>()
    val statusUpdates = mutableListOf<Triple<UUID, Int, GiftIdeaUpdate>>()
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

    override suspend fun listGiftIdeas(
        spaceId: UUID,
        accessToken: String,
        cursor: String?,
    ): GiftIdeaPage = GiftIdeaPage(hasMore = false, items = ideas, nextCursor = null)

    override suspend fun createGiftIdea(
        spaceId: UUID,
        accessToken: String,
        fields: GiftIdeaCreate,
    ): GiftIdeaDetail {
        created += fields
        return giftIdea(fields.title)
    }

    override suspend fun updateGiftIdea(
        spaceId: UUID,
        accessToken: String,
        giftIdeaId: UUID,
        ifMatch: Int,
        fields: GiftIdeaUpdate,
    ): GiftIdeaDetail {
        if (fields.status != null && fields.title == null) {
            statusUpdates += Triple(giftIdeaId, ifMatch, fields)
        } else {
            updated += giftIdeaId to ifMatch
        }
        return giftIdea(fields.title ?: "Updated")
    }

    override suspend fun deleteGiftIdea(spaceId: UUID, accessToken: String, giftIdeaId: UUID, ifMatch: Int) {
        deleted += giftIdeaId to ifMatch
    }
}
