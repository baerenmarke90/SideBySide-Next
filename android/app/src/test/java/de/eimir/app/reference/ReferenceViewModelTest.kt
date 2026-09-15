package de.eimir.app.reference

import de.eimir.app.demo.DemoPersona
import eimir.api.models.AccountMembershipView
import java.time.OffsetDateTime
import java.util.UUID
import kotlinx.coroutines.CompletableDeferred
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.ExperimentalCoroutinesApi
import kotlinx.coroutines.test.UnconfinedTestDispatcher
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
import eimir.api.models.AccountView
import eimir.api.models.AttachmentDetail
import eimir.api.models.AttachmentReadRequest
import eimir.api.models.AttachmentUploadCreate
import eimir.api.models.MemoryAttachmentSet
import eimir.api.models.MemoryCreate
import eimir.api.models.InstanceAccessStatus
import eimir.api.models.MemoryDetail
import eimir.api.models.ReadDescriptor
import eimir.api.models.SessionView
import eimir.api.models.StoryPage
import eimir.api.models.TokenView
import eimir.api.models.UploadDescriptor

@OptIn(ExperimentalCoroutinesApi::class)
class ReferenceViewModelTest {
    private val dispatcher = UnconfinedTestDispatcher()
    private val spaceId = UUID.fromString("00000000-0000-0000-0000-000000000010")

    @Before
    fun setUp() {
        Dispatchers.setMain(dispatcher)
    }

    @After
    fun tearDown() {
        Dispatchers.resetMain()
    }

    @Test
    fun logoutIgnoresLateTimelineAndPickerResultsFromPreviousSession() = runTest(dispatcher) {
        val releaseSecondTimeline = CompletableDeferred<Unit>()
        var timelineCalls = 0
        val api = object : FakeReferenceContract() {
            override suspend fun signIn(email: String, password: String): SessionView = session()


            override suspend fun listMemberships(accessToken: String): List<AccountMembershipView> =
                listOf(
                    AccountMembershipView(
                        role = "PARTNER",
                        spaceId = spaceId,
                        status = "ACTIVE",
                    ),
                )


            override suspend fun getTimeline(
        spaceId: UUID,
        accessToken: String,
        cursor: String?,
    ): StoryPage {
                timelineCalls += 1
                if (timelineCalls == 1) {
                    return StoryPage(hasMore = false, items = emptyList(), nextCursor = null)
                }
                releaseSecondTimeline.await()
                error("late timeline failure")
            }








        }
        val viewModel = ReferenceViewModel(
            config = ReferenceConfig(apiBaseUrl = "https://eimir.invalid"),
            api = api,
        )

        viewModel.signIn("person@example.com", "secret")
        advanceUntilIdle()
        assertEquals(1, timelineCalls)
        val selectionEpoch = checkNotNull(viewModel.beginImageSelection())

        viewModel.refreshStory()
        assertEquals(2, timelineCalls)
        viewModel.logout()
        assertNull(viewModel.beginImageSelection())

        releaseSecondTimeline.complete(Unit)
        advanceUntilIdle()
        viewModel.selectImages(
            listOf(SelectedImage(byteArrayOf(1, 2, 3), "late.jpg", "image/jpeg")),
            selectionEpoch,
        )
        viewModel.setImageSelectionError(IllegalStateException("late picker failure"), selectionEpoch)

        val state = viewModel.uiState.value
        assertFalse(state.loggedIn)
        assertEquals(UiMessage(R.string.ref_status_logged_out), state.status)
        assertNull(state.error)
        assertEquals(emptyList<DraftImageUiItem>(), state.draftImages)
        assertEquals(emptyList<Any>(), state.storyItems)
    }

    @Test
    fun instanceStatusDistinguishesRegistrationPolicyAndMaintenance() = runTest(dispatcher) {
        val disabled = ReferenceViewModel(
            config = ReferenceConfig(apiBaseUrl = "https://eimir.invalid"),
            api = instanceStatusApi(
                InstanceAccessStatus(
                    maintenanceMode = false,
                    registrationAvailable = false,
                    registrationUnavailableReason =
                        InstanceAccessStatus.RegistrationUnavailableReason.administrator,
                ),
            ),
        )
        val maintenance = ReferenceViewModel(
            config = ReferenceConfig(apiBaseUrl = "https://eimir.invalid"),
            api = instanceStatusApi(
                InstanceAccessStatus(
                    maintenanceMode = true,
                    registrationAvailable = false,
                    registrationUnavailableReason =
                        InstanceAccessStatus.RegistrationUnavailableReason.maintenance,
                ),
            ),
        )
        advanceUntilIdle()

        assertEquals(
            InstanceAvailability.REGISTRATION_DISABLED,
            disabled.uiState.value.instanceAvailability,
        )
        assertEquals(
            InstanceAvailability.MAINTENANCE,
            maintenance.uiState.value.instanceAvailability,
        )
        assertTrue(disabled.uiState.value.configured)
        assertTrue(maintenance.uiState.value.configured)
    }

    @Test
    fun instanceStatusKeepsConnectivityFailureDistinct() = runTest(dispatcher) {
        val api = object : FakeReferenceContract() {
            override suspend fun getInstanceStatus(): InstanceAccessStatus =
                throw java.io.IOException("network unavailable")
        }
        val viewModel = ReferenceViewModel(
            config = ReferenceConfig(apiBaseUrl = "https://eimir.invalid"),
            api = api,
        )
        advanceUntilIdle()

        assertEquals(InstanceAvailability.UNREACHABLE, viewModel.uiState.value.instanceAvailability)
        assertTrue(viewModel.uiState.value.configured)
    }

    private fun instanceStatusApi(status: InstanceAccessStatus): FakeReferenceContract =
        object : FakeReferenceContract() {
            override suspend fun getInstanceStatus(): InstanceAccessStatus = status
        }

    private fun session(): SessionView {
        val now = OffsetDateTime.parse("2026-08-26T08:00:00Z")
        return SessionView(
            account = AccountView(
                displayName = "Test Person",
                id = UUID.fromString("00000000-0000-0000-0000-000000000020"),
            ),
            tokens = TokenView(
                accessExpiresAt = now.plusMinutes(15),
                accessToken = "access-token",
                refreshExpiresAt = now.plusDays(30),
                refreshToken = "refresh-token",
            ),
        )
    }
}
