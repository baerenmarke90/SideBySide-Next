package de.sidebyside.next.place

import de.sidebyside.next.reference.FakeReferenceContract
import de.sidebyside.next.reference.ReferenceConfig
import de.sidebyside.next.reference.ReferenceViewModel
import java.math.BigDecimal
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
import sidebyside.api.models.PlaceCreate
import sidebyside.api.models.PlaceDetail
import sidebyside.api.models.PlacePage
import sidebyside.api.models.PlaceUpdate
import sidebyside.api.models.ResourceCapabilities
import sidebyside.api.models.SessionView
import sidebyside.api.models.StoryPage
import sidebyside.api.models.TokenView

private val SPACE: UUID = UUID.fromString("11111111-1111-4111-8111-111111111111")

/**
 * Place CRUD. The one thing worth pinning above the rest is the
 * latitude/longitude pairing #531 named: the server rejects one of the two
 * set without the other, and this client refuses to submit that instead of
 * relying on the 400 alone.
 */
@OptIn(ExperimentalCoroutinesApi::class)
class PlaceTest {
    private val dispatcher = StandardTestDispatcher()

    @Before
    fun setUp() = Dispatchers.setMain(dispatcher)

    @After
    fun tearDown() = Dispatchers.resetMain()

    @Test
    fun loadingPopulatesTheList() = runTest(dispatcher) {
        val place = place("Am See")
        val api = PlaceApi(places = listOf(place))
        val model = ReferenceViewModel(config = ReferenceConfig(BASE_URL), api = api)

        signIn(model)
        model.loadPlaces()
        advanceUntilIdle()

        assertEquals(listOf(place), model.uiState.value.places)
    }

    @Test
    fun addingWithABlankNameMakesNoCall() = runTest(dispatcher) {
        val api = PlaceApi()
        val model = ReferenceViewModel(config = ReferenceConfig(BASE_URL), api = api)

        signIn(model)
        model.addPlace("   ", "", "", "", "")
        advanceUntilIdle()

        assertTrue(api.created.isEmpty())
    }

    @Test
    fun addingWithOnlyOneCoordinateSetMakesNoCall() = runTest(dispatcher) {
        val api = PlaceApi()
        val model = ReferenceViewModel(config = ReferenceConfig(BASE_URL), api = api)

        signIn(model)
        model.addPlace("A place", "", "", "52.5", "")
        advanceUntilIdle()

        assertTrue(api.created.isEmpty())
    }

    @Test
    fun addingWithBothCoordinatesBlankSendsNoCoordinates() = runTest(dispatcher) {
        val api = PlaceApi()
        val model = ReferenceViewModel(config = ReferenceConfig(BASE_URL), api = api)

        signIn(model)
        model.addPlace("A place", "", "", "", "")
        advanceUntilIdle()

        assertEquals(1, api.created.size)
        assertNull(api.created.first().latitude)
        assertNull(api.created.first().longitude)
    }

    @Test
    fun addingWithBothCoordinatesSetParsesThemAsAPair() = runTest(dispatcher) {
        val api = PlaceApi()
        val model = ReferenceViewModel(config = ReferenceConfig(BASE_URL), api = api)

        signIn(model)
        model.addPlace("A place", "Nice spot", "Main St", "52.5", "13.4")
        advanceUntilIdle()

        assertEquals(1, api.created.size)
        assertEquals(BigDecimal("52.5"), api.created.first().latitude)
        assertEquals(BigDecimal("13.4"), api.created.first().longitude)
        assertEquals("Nice spot", api.created.first().description)
        assertEquals("Main St", api.created.first().address)
    }

    @Test
    fun updatingSendsTheCurrentVersionAsIfMatch() = runTest(dispatcher) {
        val target = place("Am See", version = 4)
        val api = PlaceApi(places = listOf(target))
        val model = ReferenceViewModel(config = ReferenceConfig(BASE_URL), api = api)

        signIn(model)
        model.updatePlace(target, "New name", "", "", "", "")
        advanceUntilIdle()

        assertEquals(1, api.updated.size)
        assertEquals(target.id, api.updated.first().first)
        assertEquals(4, api.updated.first().second)
    }

    @Test
    fun deletingSendsTheEntrysOwnVersion() = runTest(dispatcher) {
        val target = place("Am See", version = 2)
        val api = PlaceApi(places = listOf(target))
        val model = ReferenceViewModel(config = ReferenceConfig(BASE_URL), api = api)

        signIn(model)
        model.deletePlace(target)
        advanceUntilIdle()

        assertEquals(listOf(target.id to 2), api.deleted)
    }

    @Test
    fun forgetsPlacesWhenTheSessionEnds() = runTest(dispatcher) {
        val api = PlaceApi(places = listOf(place("Am See")))
        val model = ReferenceViewModel(config = ReferenceConfig(BASE_URL), api = api)

        signIn(model)
        model.loadPlaces()
        advanceUntilIdle()
        assertTrue(model.uiState.value.places.isNotEmpty())

        model.logout()

        assertTrue(model.uiState.value.places.isEmpty())
    }

    private suspend fun TestScope.signIn(model: ReferenceViewModel) {
        model.signIn("someone@example.test", "secret")
        advanceUntilIdle()
    }
}

private const val BASE_URL = "https://sidebyside.example"

private val FULL_CAPABILITIES = ResourceCapabilities(canComment = true, canDelete = true, canEdit = true)

private fun place(name: String, version: Int = 1) = PlaceDetail(
    address = null,
    capabilities = FULL_CAPABILITIES,
    createdAt = OffsetDateTime.now(),
    createdBy = UUID.randomUUID(),
    creator = AuthorSummary(displayName = "Lea", id = UUID.randomUUID()),
    description = null,
    id = UUID.randomUUID(),
    latitude = null,
    longitude = null,
    name = name,
    spaceId = SPACE,
    updatedAt = OffsetDateTime.now(),
    version = version,
)

private class PlaceApi(
    private val places: List<PlaceDetail> = emptyList(),
) : FakeReferenceContract() {
    val created = mutableListOf<PlaceCreate>()
    val updated = mutableListOf<Pair<UUID, Int>>()
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

    override suspend fun getTimeline(spaceId: UUID, accessToken: String, cursor: String?): StoryPage =
        StoryPage(hasMore = false, items = emptyList(), nextCursor = null)

    override suspend fun listPlaces(
        spaceId: UUID,
        accessToken: String,
        cursor: String?,
    ): PlacePage = PlacePage(hasMore = false, items = places, nextCursor = null)

    override suspend fun createPlace(
        spaceId: UUID,
        accessToken: String,
        fields: PlaceCreate,
    ): PlaceDetail {
        created += fields
        return place(fields.name)
    }

    override suspend fun updatePlace(
        spaceId: UUID,
        accessToken: String,
        placeId: UUID,
        ifMatch: Int,
        fields: PlaceUpdate,
    ): PlaceDetail {
        updated += placeId to ifMatch
        return place(fields.name ?: "Updated")
    }

    override suspend fun deletePlace(spaceId: UUID, accessToken: String, placeId: UUID, ifMatch: Int) {
        deleted += placeId to ifMatch
    }
}
