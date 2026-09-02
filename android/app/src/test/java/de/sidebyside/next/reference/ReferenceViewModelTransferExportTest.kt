package de.sidebyside.next.reference

import java.io.ByteArrayOutputStream
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
import org.junit.Assert.assertNotNull
import org.junit.Assert.assertNull
import org.junit.Assert.assertTrue
import org.junit.Before
import org.junit.Test
import sidebyside.api.models.AccountMembershipView
import sidebyside.api.models.AccountView
import sidebyside.api.models.ExportStatus
import sidebyside.api.models.SessionView
import sidebyside.api.models.TokenView
import sidebyside.api.models.TransferExportDetail
import sidebyside.api.models.TransferScope

private val SPACE: UUID = UUID.fromString("11111111-1111-4111-8111-111111111111")

/**
 * The M2-D17/S6 Transfer Bundle export flow: create, poll status, and
 * stream a ready export into a caller-owned sink.
 */
@OptIn(ExperimentalCoroutinesApi::class)
class ReferenceViewModelTransferExportTest {
    private val dispatcher = StandardTestDispatcher()

    @Before
    fun setUp() = Dispatchers.setMain(dispatcher)

    @After
    fun tearDown() = Dispatchers.resetMain()

    @Test
    fun createExportSendsTheChosenScopeAndTracksTheResult() = runTest(dispatcher) {
        val api = TransferApi()
        val model = signedIn(api)

        model.createExport(TransferScope.SHARED)
        advanceUntilIdle()

        assertEquals(TransferScope.SHARED, api.lastRequestedScope)
        assertEquals(ExportStatus.QUEUED, model.uiState.value.export?.status)
        assertNull(model.uiState.value.exportProblem)
    }

    @Test
    fun refreshExportUpdatesTheTrackedStatus() = runTest(dispatcher) {
        val api = TransferApi()
        val model = signedIn(api)

        model.createExport(TransferScope.SHARED)
        advanceUntilIdle()
        assertEquals(ExportStatus.QUEUED, model.uiState.value.export?.status)

        api.nextStatus = ExportStatus.READY
        model.refreshExport()
        advanceUntilIdle()

        assertEquals(ExportStatus.READY, model.uiState.value.export?.status)
    }

    @Test
    fun refreshExportWithNothingTrackedDoesNothing() = runTest(dispatcher) {
        val api = TransferApi()
        val model = signedIn(api)

        model.refreshExport()
        advanceUntilIdle()

        assertNull(model.uiState.value.export)
    }

    @Test
    fun downloadExportStreamsIntoTheGivenSinkAndMarksItDownloaded() = runTest(dispatcher) {
        val api = TransferApi()
        val model = signedIn(api)

        model.createExport(TransferScope.SHARED)
        advanceUntilIdle()
        val sink = ByteArrayOutputStream()

        model.downloadExport(sink)

        assertTrue(api.downloadedArchive.contentEquals(sink.toByteArray()))
        assertTrue(model.uiState.value.exportDownloaded)
        assertFalse(model.uiState.value.exportBusy)
    }

    @Test
    fun aFailedDownloadReportsAProblemAndLeavesExportNotDownloaded() = runTest(dispatcher) {
        val api = TransferApi()
        val model = signedIn(api)

        model.createExport(TransferScope.SHARED)
        advanceUntilIdle()
        api.nextDownloadFailure = java.io.IOException("offline")

        model.downloadExport(ByteArrayOutputStream())

        assertFalse(model.uiState.value.exportDownloaded)
        assertNotNull(model.uiState.value.exportProblem)
    }

    @Test
    fun startingANewExportResetsTheDownloadedFlag() = runTest(dispatcher) {
        val api = TransferApi()
        val model = signedIn(api)

        model.createExport(TransferScope.SHARED)
        advanceUntilIdle()
        model.downloadExport(ByteArrayOutputStream())
        assertTrue(model.uiState.value.exportDownloaded)

        model.createExport(TransferScope.PERSONAL)
        advanceUntilIdle()

        assertFalse(model.uiState.value.exportDownloaded)
    }

    private suspend fun TestScope.signedIn(api: ReferenceContract): ReferenceViewModel {
        val model = ReferenceViewModel(config = ReferenceConfig(BASE_URL), api = api)
        model.signIn("someone@example.test", "secret")
        advanceUntilIdle()
        return model
    }
}

private const val BASE_URL = "https://sidebyside.example"

private class TransferApi : FakeReferenceContract() {
    var nextStatus: ExportStatus = ExportStatus.QUEUED
    var nextDownloadFailure: Throwable? = null
    var lastRequestedScope: TransferScope? = null
    val downloadedArchive: ByteArray = byteArrayOf(1, 2, 3, 4, 5)

    override suspend fun signIn(email: String, password: String): SessionView = SessionView(
        account = AccountView(displayName = email, id = UUID.randomUUID()),
        tokens = TokenView(
            accessExpiresAt = OffsetDateTime.now(),
            accessToken = "access",
            refreshExpiresAt = OffsetDateTime.now(),
            refreshToken = "refresh",
        ),
    )

    override suspend fun listMemberships(accessToken: String): List<AccountMembershipView> =
        listOf(AccountMembershipView(role = "PARTNER", spaceId = SPACE, status = "ACTIVE"))

    override suspend fun createTransferExport(
        spaceId: UUID,
        accessToken: String,
        scope: TransferScope,
    ): TransferExportDetail {
        lastRequestedScope = scope
        return detail(scope, ExportStatus.QUEUED)
    }

    override suspend fun getTransferExport(
        spaceId: UUID,
        accessToken: String,
        exportId: UUID,
    ): TransferExportDetail = detail(lastRequestedScope ?: TransferScope.SHARED, nextStatus)

    override suspend fun downloadTransferExport(
        spaceId: UUID,
        accessToken: String,
        exportId: UUID,
        sink: java.io.OutputStream,
    ) {
        nextDownloadFailure?.let {
            nextDownloadFailure = null
            throw it
        }
        sink.write(downloadedArchive)
    }

    private fun detail(scope: TransferScope, status: ExportStatus) = TransferExportDetail(
        artifactSize = null,
        createdAt = OffsetDateTime.now(),
        downloadUrl = null,
        errorCode = null,
        expiresAt = OffsetDateTime.now().plusHours(24),
        id = EXPORT_ID,
        readyAt = null,
        scope = scope,
        status = status,
    )
}

private val EXPORT_ID: UUID = UUID.fromString("22222222-2222-4222-8222-222222222222")
