package de.sidebyside.next.collection

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
import sidebyside.api.models.AuthorSummary
import sidebyside.api.models.CollectionCreate
import sidebyside.api.models.CollectionDetail
import sidebyside.api.models.CollectionItemCreate
import sidebyside.api.models.CollectionItemDetail
import sidebyside.api.models.CollectionItemUpdate
import sidebyside.api.models.CollectionPage
import sidebyside.api.models.CollectionUpdate
import sidebyside.api.models.ResourceCapabilities
import sidebyside.api.models.SessionView
import sidebyside.api.models.TokenView

private val SPACE: UUID = UUID.fromString("11111111-1111-4111-8111-111111111111")
private val COLLECTION: UUID = UUID.fromString("22222222-2222-4222-8222-222222222222")

/**
 * #356: the shared Collection + Item CRUD, and #355's shared
 * exact-set reorder contract. The property worth pinning beyond ordinary
 * CRUD is that a move-up/move-down always sends the full, same-set item
 * order — never a partial list — so it can never trip the server's
 * exact-set validation by construction.
 */
@OptIn(ExperimentalCoroutinesApi::class)
class CollectionTest {
    private val dispatcher = StandardTestDispatcher()

    @Before
    fun setUp() = Dispatchers.setMain(dispatcher)

    @After
    fun tearDown() = Dispatchers.resetMain()

    @Test
    fun loadingPopulatesTheList() = runTest(dispatcher) {
        val collection = collection("Packing list")
        val api = CollectionApi(collections = listOf(collection))
        val model = ReferenceViewModel(config = ReferenceConfig(BASE_URL), api = api)

        signIn(model)
        model.loadCollections()
        advanceUntilIdle()

        assertEquals(listOf(collection), model.uiState.value.collections)
    }

    @Test
    fun addingWithABlankTitleMakesNoCall() = runTest(dispatcher) {
        val api = CollectionApi()
        val model = ReferenceViewModel(config = ReferenceConfig(BASE_URL), api = api)

        signIn(model)
        model.addCollection("   ", "")
        advanceUntilIdle()

        assertTrue(api.createdCollections.isEmpty())
    }

    @Test
    fun addingAnItemSendsItsTitle() = runTest(dispatcher) {
        val target = collection("Packing list")
        val api = CollectionApi(collections = listOf(target))
        val model = ReferenceViewModel(config = ReferenceConfig(BASE_URL), api = api)

        signIn(model)
        model.addCollectionItem(target, "Passport")
        advanceUntilIdle()

        assertEquals(1, api.createdItems.size)
        assertEquals(COLLECTION, api.createdItems.first().first)
        assertEquals("Passport", api.createdItems.first().second.title)
    }

    @Test
    fun togglingCompletedFlipsTheCurrentValue() = runTest(dispatcher) {
        val target = collection("Packing list", items = listOf(item("Passport", completed = false)))
        val api = CollectionApi(collections = listOf(target))
        val model = ReferenceViewModel(config = ReferenceConfig(BASE_URL), api = api)

        signIn(model)
        model.toggleCollectionItemCompleted(target, target.items.first())
        advanceUntilIdle()

        assertEquals(1, api.itemUpdates.size)
        assertEquals(true, api.itemUpdates.first().third.completed)
    }

    @Test
    fun movingAnItemUpSwapsItWithItsPredecessorAndSendsTheWholeOrder() = runTest(dispatcher) {
        val a = item("A", position = 0)
        val b = item("B", position = 1)
        val c = item("C", position = 2)
        val target = collection("Packing list", items = listOf(a, b, c))
        val api = CollectionApi(collections = listOf(target))
        val model = ReferenceViewModel(config = ReferenceConfig(BASE_URL), api = api)

        signIn(model)
        model.moveCollectionItemUp(target, c)
        advanceUntilIdle()

        assertEquals(1, api.reorders.size)
        val (id, ifMatch, order) = api.reorders.first()
        assertEquals(COLLECTION, id)
        assertEquals(target.version, ifMatch)
        assertEquals(listOf(a.id, c.id, b.id), order)
        assertEquals(setOf(a.id, b.id, c.id), order.toSet())
    }

    @Test
    fun movingTheFirstItemUpMakesNoCall() = runTest(dispatcher) {
        val a = item("A", position = 0)
        val b = item("B", position = 1)
        val target = collection("Packing list", items = listOf(a, b))
        val api = CollectionApi(collections = listOf(target))
        val model = ReferenceViewModel(config = ReferenceConfig(BASE_URL), api = api)

        signIn(model)
        model.moveCollectionItemUp(target, a)
        advanceUntilIdle()

        assertTrue(api.reorders.isEmpty())
    }

    @Test
    fun movingTheLastItemDownMakesNoCall() = runTest(dispatcher) {
        val a = item("A", position = 0)
        val b = item("B", position = 1)
        val target = collection("Packing list", items = listOf(a, b))
        val api = CollectionApi(collections = listOf(target))
        val model = ReferenceViewModel(config = ReferenceConfig(BASE_URL), api = api)

        signIn(model)
        model.moveCollectionItemDown(target, b)
        advanceUntilIdle()

        assertTrue(api.reorders.isEmpty())
    }

    @Test
    fun deletingACollectionSendsItsOwnVersion() = runTest(dispatcher) {
        val target = collection("Packing list", version = 5)
        val api = CollectionApi(collections = listOf(target))
        val model = ReferenceViewModel(config = ReferenceConfig(BASE_URL), api = api)

        signIn(model)
        model.deleteCollection(target)
        advanceUntilIdle()

        assertEquals(listOf(COLLECTION to 5), api.deletedCollections)
    }

    @Test
    fun forgetsCollectionsWhenTheSessionEnds() = runTest(dispatcher) {
        val api = CollectionApi(collections = listOf(collection("Packing list")))
        val model = ReferenceViewModel(config = ReferenceConfig(BASE_URL), api = api)

        signIn(model)
        model.loadCollections()
        advanceUntilIdle()
        assertTrue(model.uiState.value.collections.isNotEmpty())

        model.logout()

        assertTrue(model.uiState.value.collections.isEmpty())
    }

    private suspend fun TestScope.signIn(model: ReferenceViewModel) {
        model.signIn("someone@example.test", "secret")
        advanceUntilIdle()
    }
}

private const val BASE_URL = "https://sidebyside.example"

private val FULL_CAPABILITIES = ResourceCapabilities(canComment = false, canDelete = true, canEdit = true)

private fun collection(
    title: String,
    version: Int = 1,
    items: List<CollectionItemDetail> = emptyList(),
) = CollectionDetail(
    capabilities = FULL_CAPABILITIES,
    createdAt = OffsetDateTime.now(),
    icon = null,
    id = COLLECTION,
    items = items,
    createdBy = UUID.randomUUID(),
    creator = AuthorSummary(displayName = "Lea", id = UUID.randomUUID()),
    spaceId = SPACE,
    title = title,
    updatedAt = OffsetDateTime.now(),
    version = version,
)

private fun item(title: String, position: Int = 0, completed: Boolean = false, version: Int = 1) =
    CollectionItemDetail(
        capabilities = FULL_CAPABILITIES,
        collectionId = COLLECTION,
        completed = completed,
        createdAt = OffsetDateTime.now(),
        createdBy = UUID.randomUUID(),
        creator = AuthorSummary(displayName = "Lea", id = UUID.randomUUID()),
        id = UUID.randomUUID(),
        position = position,
        title = title,
        updatedAt = OffsetDateTime.now(),
        version = version,
    )

private class CollectionApi(
    private val collections: List<CollectionDetail> = emptyList(),
) : FakeReferenceContract() {
    val createdCollections = mutableListOf<CollectionCreate>()
    val deletedCollections = mutableListOf<Pair<UUID, Int>>()
    val createdItems = mutableListOf<Pair<UUID, CollectionItemCreate>>()
    val itemUpdates = mutableListOf<Triple<UUID, UUID, CollectionItemUpdate>>()
    val reorders = mutableListOf<Triple<UUID, Int, List<UUID>>>()

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

    override suspend fun listCollections(
        spaceId: UUID,
        accessToken: String,
        cursor: String?,
    ): CollectionPage = CollectionPage(hasMore = false, items = collections, nextCursor = null)

    override suspend fun createCollection(
        spaceId: UUID,
        accessToken: String,
        fields: CollectionCreate,
    ): CollectionDetail {
        createdCollections += fields
        return collection(fields.title)
    }

    override suspend fun updateCollection(
        spaceId: UUID,
        accessToken: String,
        collectionId: UUID,
        ifMatch: Int,
        fields: CollectionUpdate,
    ): CollectionDetail = collection(fields.title ?: "Updated")

    override suspend fun deleteCollection(spaceId: UUID, accessToken: String, collectionId: UUID, ifMatch: Int) {
        deletedCollections += collectionId to ifMatch
    }

    override suspend fun createCollectionItem(
        spaceId: UUID,
        accessToken: String,
        collectionId: UUID,
        fields: CollectionItemCreate,
    ): CollectionItemDetail {
        createdItems += collectionId to fields
        return item(fields.title)
    }

    override suspend fun updateCollectionItem(
        spaceId: UUID,
        accessToken: String,
        collectionId: UUID,
        itemId: UUID,
        ifMatch: Int,
        fields: CollectionItemUpdate,
    ): CollectionItemDetail {
        itemUpdates += Triple(collectionId, itemId, fields)
        return item(fields.title ?: "Updated", completed = fields.completed ?: false)
    }

    override suspend fun deleteCollectionItem(
        spaceId: UUID,
        accessToken: String,
        collectionId: UUID,
        itemId: UUID,
        ifMatch: Int,
    ) = Unit

    override suspend fun reorderCollectionItems(
        spaceId: UUID,
        accessToken: String,
        collectionId: UUID,
        ifMatch: Int,
        itemIds: List<UUID>,
    ): CollectionDetail {
        reorders += Triple(collectionId, ifMatch, itemIds)
        return collections.first { it.id == collectionId }
    }
}
