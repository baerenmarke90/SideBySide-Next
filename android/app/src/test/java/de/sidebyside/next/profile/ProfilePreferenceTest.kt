package de.sidebyside.next.profile

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
import sidebyside.api.models.PartnerProfileView
import sidebyside.api.models.PartnerView
import sidebyside.api.models.PreferenceCategory
import sidebyside.api.models.PreferenceSentiment
import sidebyside.api.models.ProfilePreferenceCreate
import sidebyside.api.models.ProfilePreferenceUpdate
import sidebyside.api.models.ProfilePreferenceView
import sidebyside.api.models.ProfileVisibility
import sidebyside.api.models.SessionView
import sidebyside.api.models.SpaceView
import sidebyside.api.models.StoryPage
import sidebyside.api.models.TokenView

private val SPACE: UUID = UUID.fromString("11111111-1111-4111-8111-111111111111")
private val SELF: UUID = UUID.fromString("22222222-2222-4222-8222-222222222222")
private val PARTNER: UUID = UUID.fromString("33333333-3333-4333-8333-333333333333")

/**
 * ProfilePreference: what each partner likes, and the private notes kept
 * about the other. The one thing worth pinning above the rest is that
 * refreshing the profile identity must never wipe out preference state that
 * a concurrent load already populated — found on the device build for the
 * related-persons slice as the same defect in a different field, so it is
 * worth a direct test here rather than trusting it will not recur.
 */
@OptIn(ExperimentalCoroutinesApi::class)
class ProfilePreferenceTest {
    private val dispatcher = StandardTestDispatcher()

    @Before
    fun setUp() = Dispatchers.setMain(dispatcher)

    @After
    fun tearDown() = Dispatchers.resetMain()

    @Test
    fun loadingPopulatesTheFlatPreferenceList() = runTest(dispatcher) {
        val note = privateNote()
        val api = PreferenceApi(privateNotes = listOf(note))
        val model = ReferenceViewModel(config = ReferenceConfig(BASE_URL), api = api)

        signIn(model)
        model.loadProfilePreferences()
        advanceUntilIdle()

        assertEquals(listOf(note), model.uiState.value.profile.preferences)
    }

    @Test
    fun addingASelfPreferenceTargetsTheCallersOwnAccount() = runTest(dispatcher) {
        val api = PreferenceApi()
        val model = ReferenceViewModel(config = ReferenceConfig(BASE_URL), api = api)

        signIn(model)
        model.addProfilePreference(
            SELF,
            ProfileVisibility.SELF_PROFILE,
            PreferenceCategory.MUSIC,
            "Lieblingsband",
            PreferenceSentiment.LOVE,
            "Alles von ihnen",
        )
        advanceUntilIdle()

        assertEquals(1, api.created.size)
        assertEquals(SELF, api.created.first().accountId)
        assertEquals(ProfileVisibility.SELF_PROFILE, api.created.first().visibility)
    }

    @Test
    fun addingAPrivateNoteTargetsThePartnersAccount() = runTest(dispatcher) {
        val api = PreferenceApi()
        val model = ReferenceViewModel(config = ReferenceConfig(BASE_URL), api = api)

        signIn(model)
        model.addProfilePreference(
            PARTNER,
            ProfileVisibility.PRIVATE_PARTNER_NOTE,
            PreferenceCategory.FLOWERS,
            "Geschenkidee",
            PreferenceSentiment.LIKE,
            "Sonnenblumen",
        )
        advanceUntilIdle()

        assertEquals(1, api.created.size)
        assertEquals(PARTNER, api.created.first().accountId)
        assertEquals(ProfileVisibility.PRIVATE_PARTNER_NOTE, api.created.first().visibility)
    }

    @Test
    fun addingWithABlankTopicMakesNoCall() = runTest(dispatcher) {
        val api = PreferenceApi()
        val model = ReferenceViewModel(config = ReferenceConfig(BASE_URL), api = api)

        signIn(model)
        model.addProfilePreference(
            SELF,
            ProfileVisibility.SELF_PROFILE,
            PreferenceCategory.OTHER,
            "   ",
            PreferenceSentiment.NEUTRAL,
            "value",
        )
        advanceUntilIdle()

        assertTrue(api.created.isEmpty())
    }

    @Test
    fun updatingSendsTheCurrentVersionAsIfMatch() = runTest(dispatcher) {
        val note = privateNote(version = 7)
        val api = PreferenceApi(privateNotes = listOf(note))
        val model = ReferenceViewModel(config = ReferenceConfig(BASE_URL), api = api)

        signIn(model)
        model.updateProfilePreference(
            note,
            PreferenceCategory.HOBBIES,
            "Neues Thema",
            PreferenceSentiment.LIKE,
            "Neuer Wert",
        )
        advanceUntilIdle()

        assertEquals(1, api.updated.size)
        assertEquals(note.id, api.updated.first().first)
        assertEquals(7, api.updated.first().second)
    }

    @Test
    fun deletingSendsTheEntrysOwnVersion() = runTest(dispatcher) {
        val note = privateNote(version = 3)
        val api = PreferenceApi(privateNotes = listOf(note))
        val model = ReferenceViewModel(config = ReferenceConfig(BASE_URL), api = api)

        signIn(model)
        model.deleteProfilePreference(note)
        advanceUntilIdle()

        assertEquals(listOf(note.id to 3), api.deleted)
    }

    @Test
    fun refreshingTheProfileNeverWipesOutAConcurrentlyLoadedPreferenceList() = runTest(dispatcher) {
        // The same defect class found in the related-persons slice: a
        // dispose/refresh path rebuilding one nested state object must not
        // silently reset a sibling field it knows nothing about.
        val note = privateNote()
        val api = PreferenceApi(privateNotes = listOf(note))
        val model = ReferenceViewModel(config = ReferenceConfig(BASE_URL), api = api)

        signIn(model)
        model.loadProfilePreferences()
        advanceUntilIdle()
        assertEquals(listOf(note), model.uiState.value.profile.preferences)

        model.refreshProfile()
        advanceUntilIdle()

        assertEquals(listOf(note), model.uiState.value.profile.preferences)
    }

    @Test
    fun forgetsPreferencesWhenTheSessionEnds() = runTest(dispatcher) {
        val api = PreferenceApi(privateNotes = listOf(privateNote()))
        val model = ReferenceViewModel(config = ReferenceConfig(BASE_URL), api = api)

        signIn(model)
        model.loadProfilePreferences()
        advanceUntilIdle()
        assertTrue(model.uiState.value.profile.preferences.isNotEmpty())

        model.logout()

        assertTrue(model.uiState.value.profile.preferences.isEmpty())
    }

    private suspend fun TestScope.signIn(model: ReferenceViewModel) {
        model.signIn("someone@example.test", "secret")
        advanceUntilIdle()
    }
}

private const val BASE_URL = "https://sidebyside.example"

private fun privateNote(version: Int = 1) = ProfilePreferenceView(
    accountId = PARTNER,
    category = PreferenceCategory.FLOWERS,
    createdAt = OffsetDateTime.now(),
    id = UUID.randomUUID(),
    sentiment = PreferenceSentiment.LIKE,
    topic = "Geschenkidee",
    updatedAt = OffsetDateTime.now(),
    value = "Sonnenblumen",
    version = version,
    visibility = ProfileVisibility.PRIVATE_PARTNER_NOTE,
)

private fun profile(accountId: UUID) = PartnerProfileView(
    accountId = accountId,
    createdAt = OffsetDateTime.now(),
    displayName = if (accountId == SELF) "Lea" else "Alex",
    id = UUID.randomUUID(),
    preferences = emptyList(),
    profileAttachmentId = null,
    updatedAt = OffsetDateTime.now(),
    version = 1,
)

private class PreferenceApi(
    private val privateNotes: List<ProfilePreferenceView> = emptyList(),
) : FakeReferenceContract() {
    val created = mutableListOf<ProfilePreferenceCreate>()
    val updated = mutableListOf<Pair<UUID, Int>>()
    val deleted = mutableListOf<Pair<UUID, Int>>()

    override suspend fun signIn(email: String, password: String): SessionView = SessionView(
        account = AccountView(displayName = "Lea", id = SELF),
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

    override suspend fun getSpace(spaceId: UUID, accessToken: String): SpaceView = SpaceView(
        createdAt = OffsetDateTime.now(),
        id = spaceId,
        partners = listOf(
            PartnerView(displayName = "Lea", id = SELF),
            PartnerView(displayName = "Alex", id = PARTNER),
        ),
    )

    override suspend fun getProfile(
        spaceId: UUID,
        accessToken: String,
        accountId: UUID,
    ): PartnerProfileView = profile(accountId)

    override suspend fun listProfilePreferences(
        spaceId: UUID,
        accessToken: String,
    ): List<ProfilePreferenceView> = privateNotes

    override suspend fun createProfilePreference(
        spaceId: UUID,
        accessToken: String,
        fields: ProfilePreferenceCreate,
    ): ProfilePreferenceView {
        created += fields
        return privateNote()
    }

    override suspend fun updateProfilePreference(
        spaceId: UUID,
        accessToken: String,
        preferenceId: UUID,
        ifMatch: Int,
        fields: ProfilePreferenceUpdate,
    ): ProfilePreferenceView {
        updated += preferenceId to ifMatch
        return privateNote()
    }

    override suspend fun deleteProfilePreference(
        spaceId: UUID,
        accessToken: String,
        preferenceId: UUID,
        ifMatch: Int,
    ) {
        deleted += preferenceId to ifMatch
    }
}
