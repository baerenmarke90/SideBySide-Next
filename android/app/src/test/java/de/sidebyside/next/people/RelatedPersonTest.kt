package de.sidebyside.next.people

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
import org.junit.Assert.assertFalse
import org.junit.Assert.assertTrue
import org.junit.Before
import org.junit.Test
import sidebyside.api.models.AccountMembershipView
import sidebyside.api.models.AccountView
import sidebyside.api.models.ContentVisibility
import sidebyside.api.models.ImportantDateFields
import sidebyside.api.models.ImportantDateType
import sidebyside.api.models.ImportantDateView
import sidebyside.api.models.DateRepeat
import sidebyside.api.models.PersonRelationship
import sidebyside.api.models.RelatedPersonDeletePolicy
import sidebyside.api.models.RelatedPersonFields
import sidebyside.api.models.RelatedPersonView
import sidebyside.api.models.SessionView
import sidebyside.api.models.StoryPage
import sidebyside.api.models.TokenView

private val SPACE: UUID = UUID.fromString("11111111-1111-4111-8111-111111111111")

/**
 * RelatedPerson and ImportantDate management.
 *
 * The one thing worth pinning above the rest is #65: deleting a person must
 * never be preceded by any call that could reveal what ImportantDates are
 * linked to them, because even an already-filtered count would disclose the
 * gap between what this account can see and what `cascade` actually removes.
 */
@OptIn(ExperimentalCoroutinesApi::class)
class RelatedPersonTest {
    private val dispatcher = StandardTestDispatcher()

    @Before
    fun setUp() = Dispatchers.setMain(dispatcher)

    @After
    fun tearDown() = Dispatchers.resetMain()

    @Test
    fun loadingListsThePeopleInTheActiveSpace() = runTest(dispatcher) {
        val person = person("Mira")
        val api = PeopleApi(people = listOf(person))
        val model = ReferenceViewModel(config = ReferenceConfig(BASE_URL), api = api)

        signIn(model)
        model.loadRelatedPersons()
        advanceUntilIdle()

        assertEquals(listOf(person), model.uiState.value.relatedPersons)
    }

    @Test
    fun addingABlankNameMakesNoCall() = runTest(dispatcher) {
        val api = PeopleApi()
        val model = ReferenceViewModel(config = ReferenceConfig(BASE_URL), api = api)

        signIn(model)
        model.addRelatedPerson("   ", PersonRelationship.OTHER, null, true, ContentVisibility.SHARED)
        advanceUntilIdle()

        assertTrue(api.created.isEmpty())
    }

    @Test
    fun addingAPersonReloadsTheList() = runTest(dispatcher) {
        val mira = person("Mira")
        val api = PeopleApi(people = listOf(mira))
        val model = ReferenceViewModel(config = ReferenceConfig(BASE_URL), api = api)

        signIn(model)
        model.addRelatedPerson(
            "Mira",
            PersonRelationship.FRIEND,
            LocalDate.of(1990, 5, 1),
            true,
            ContentVisibility.SHARED,
        )
        advanceUntilIdle()

        assertEquals(1, api.created.size)
        assertEquals("Mira", api.created.first().displayName)
        assertEquals(listOf(mira), model.uiState.value.relatedPersons)
    }

    @Test
    fun deletingAPersonNeverReadsTheirImportantDatesFirst() = runTest(dispatcher) {
        // The whole point of #65: the confirmation must already carry the
        // policy the user picked, so nothing here may ask the server what a
        // cascade delete would remove before doing it.
        val target = person("Mira")
        val api = PeopleApi(people = listOf(target))
        val model = ReferenceViewModel(config = ReferenceConfig(BASE_URL), api = api)

        signIn(model)
        model.loadRelatedPersons()
        advanceUntilIdle()

        model.deleteRelatedPerson(target.id, RelatedPersonDeletePolicy.cascade)
        advanceUntilIdle()

        assertEquals(0, api.listImportantDatesCalls)
        assertEquals(listOf(target.id to RelatedPersonDeletePolicy.cascade), api.deleted)
    }

    @Test
    fun deletingWithPreserveSendsThatExactPolicy() = runTest(dispatcher) {
        val target = person("Mira")
        val api = PeopleApi(people = listOf(target))
        val model = ReferenceViewModel(config = ReferenceConfig(BASE_URL), api = api)

        signIn(model)
        model.loadRelatedPersons()
        advanceUntilIdle()

        model.deleteRelatedPerson(target.id, RelatedPersonDeletePolicy.preserve)
        advanceUntilIdle()

        assertEquals(listOf(target.id to RelatedPersonDeletePolicy.preserve), api.deleted)
    }

    @Test
    fun deletingClearsAnyOpenImportantDatesForThatPerson() = runTest(dispatcher) {
        val target = person("Mira")
        val date = importantDate(target.id)
        val api = PeopleApi(people = listOf(target), dates = listOf(date))
        val model = ReferenceViewModel(config = ReferenceConfig(BASE_URL), api = api)

        signIn(model)
        model.loadRelatedPersons()
        advanceUntilIdle()
        model.loadImportantDates(target.id)
        advanceUntilIdle()
        assertTrue(model.uiState.value.personImportantDates.isNotEmpty())

        model.deleteRelatedPerson(target.id, RelatedPersonDeletePolicy.preserve)
        advanceUntilIdle()

        assertTrue(model.uiState.value.personImportantDates.isEmpty())
    }

    @Test
    fun loadingImportantDatesScopesToTheRequestedPerson() = runTest(dispatcher) {
        val target = person("Mira")
        val date = importantDate(target.id)
        val api = PeopleApi(people = listOf(target), dates = listOf(date))
        val model = ReferenceViewModel(config = ReferenceConfig(BASE_URL), api = api)

        signIn(model)
        model.loadImportantDates(target.id)
        advanceUntilIdle()

        assertEquals(listOf(target.id), api.listImportantDatesFilters)
        assertEquals(listOf(date), model.uiState.value.personImportantDates)
    }

    @Test
    fun addingAnImportantDateReloadsThePersonsDates() = runTest(dispatcher) {
        val target = person("Mira")
        val date = importantDate(target.id)
        val api = PeopleApi(people = listOf(target), dates = listOf(date))
        val model = ReferenceViewModel(config = ReferenceConfig(BASE_URL), api = api)

        signIn(model)
        model.addImportantDate(
            target.id,
            "Geburtstag",
            ImportantDateType.BIRTHDAY,
            LocalDate.of(2020, 1, 1),
            DateRepeat.ANNUALLY,
            ContentVisibility.SHARED,
        )
        advanceUntilIdle()

        assertEquals(1, api.createdDates.size)
        assertEquals(listOf(date), model.uiState.value.personImportantDates)
    }

    @Test
    fun forgetsRelatedPersonsWhenTheSessionEnds() = runTest(dispatcher) {
        val api = PeopleApi(people = listOf(person("Mira")))
        val model = ReferenceViewModel(config = ReferenceConfig(BASE_URL), api = api)

        signIn(model)
        model.loadRelatedPersons()
        advanceUntilIdle()
        assertTrue(model.uiState.value.relatedPersons.isNotEmpty())

        model.logout()

        assertTrue(model.uiState.value.relatedPersons.isEmpty())
    }

    private suspend fun TestScope.signIn(model: ReferenceViewModel) {
        model.signIn("someone@example.test", "secret")
        advanceUntilIdle()
    }
}

private const val BASE_URL = "https://sidebyside.example"

private fun person(name: String) = RelatedPersonView(
    birthday = null,
    birthdayYearKnown = true,
    createdAt = OffsetDateTime.now(),
    displayName = name,
    id = UUID.nameUUIDFromBytes(name.toByteArray()),
    relationship = PersonRelationship.FRIEND,
    updatedAt = OffsetDateTime.now(),
    version = 1,
    visibility = ContentVisibility.SHARED,
)

private fun importantDate(relatedPersonId: UUID) = ImportantDateView(
    createdAt = OffsetDateTime.now(),
    date = LocalDate.of(2020, 1, 1),
    id = UUID.randomUUID(),
    label = "Geburtstag",
    relatedPersonId = relatedPersonId,
    repeats = DateRepeat.ANNUALLY,
    type = ImportantDateType.BIRTHDAY,
    updatedAt = OffsetDateTime.now(),
    version = 1,
    visibility = ContentVisibility.SHARED,
)

private class PeopleApi(
    private val people: List<RelatedPersonView> = emptyList(),
    private val dates: List<ImportantDateView> = emptyList(),
) : FakeReferenceContract() {
    val created = mutableListOf<RelatedPersonFields>()
    val deleted = mutableListOf<Pair<UUID, RelatedPersonDeletePolicy>>()
    val createdDates = mutableListOf<ImportantDateFields>()
    var listImportantDatesCalls = 0
    val listImportantDatesFilters = mutableListOf<UUID?>()

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

    override suspend fun listRelatedPersons(
        spaceId: UUID,
        accessToken: String,
    ): List<RelatedPersonView> = people

    override suspend fun createRelatedPerson(
        spaceId: UUID,
        accessToken: String,
        fields: RelatedPersonFields,
    ): RelatedPersonView {
        created += fields
        return person(fields.displayName)
    }

    override suspend fun deleteRelatedPerson(
        spaceId: UUID,
        accessToken: String,
        personId: UUID,
        deletePolicy: RelatedPersonDeletePolicy,
        ifMatch: Int,
    ) {
        deleted += personId to deletePolicy
    }

    override suspend fun listImportantDates(
        spaceId: UUID,
        accessToken: String,
        relatedPersonId: UUID?,
    ): List<ImportantDateView> {
        listImportantDatesCalls += 1
        listImportantDatesFilters += relatedPersonId
        return dates.filter { relatedPersonId == null || it.relatedPersonId == relatedPersonId }
    }

    override suspend fun createImportantDate(
        spaceId: UUID,
        accessToken: String,
        fields: ImportantDateFields,
    ): ImportantDateView {
        createdDates += fields
        return dates.first()
    }
}
