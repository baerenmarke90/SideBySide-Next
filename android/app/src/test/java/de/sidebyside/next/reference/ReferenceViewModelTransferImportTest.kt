package de.sidebyside.next.reference

import java.io.ByteArrayInputStream
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
import sidebyside.api.models.ImportStatus
import sidebyside.api.models.SessionView
import sidebyside.api.models.TokenView
import sidebyside.api.models.TransferImportDetail
import sidebyside.api.models.TransferScope

private val SPACE: UUID = UUID.fromString("11111111-1111-4111-8111-111111111111")

/**
 * The M2-D17/S6 Transfer Bundle import flow: stage an uploaded archive,
 * poll its validation status, and apply it once validated.
 *
 * Apply is deliberately never triggered by [refreshImport] reaching
 * `READY_TO_APPLY` on its own — the M2-D18 contract requires the client to
 * show the validated summary first, so [ReferenceViewModel.applyImport] is
 * always a separate, explicit call in these tests too.
 */
@OptIn(ExperimentalCoroutinesApi::class)
class ReferenceViewModelTransferImportTest {
    private val dispatcher = StandardTestDispatcher()

    @Before
    fun setUp() = Dispatchers.setMain(dispatcher)

    @After
    fun tearDown() = Dispatchers.resetMain()

    @Test
    fun uploadImportStagesTheArchiveAndTracksTheResult() = runTest(dispatcher) {
        val api = TransferImportApi()
        val model = signedIn(api)
        val archive = byteArrayOf(9, 8, 7, 6)

        model.uploadImport(archive.size.toLong(), ByteArrayInputStream(archive))

        assertTrue(archive.contentEquals(api.uploadedArchiveBytes))
        assertEquals(archive.size.toLong(), api.uploadedArchiveSize)
        assertEquals(ImportStatus.QUEUED, model.uiState.value.import?.status)
        assertNull(model.uiState.value.importProblem)
        assertFalse(model.uiState.value.importBusy)
    }

    @Test
    fun refreshImportUpdatesTheTrackedStatus() = runTest(dispatcher) {
        val api = TransferImportApi()
        val model = signedIn(api)
        model.uploadImport(4, ByteArrayInputStream(byteArrayOf(1, 2, 3, 4)))

        api.nextStatus = ImportStatus.READY_TO_APPLY
        model.refreshImport()
        advanceUntilIdle()

        assertEquals(ImportStatus.READY_TO_APPLY, model.uiState.value.import?.status)
    }

    @Test
    fun refreshImportWithNothingTrackedDoesNothing() = runTest(dispatcher) {
        val api = TransferImportApi()
        val model = signedIn(api)

        model.refreshImport()
        advanceUntilIdle()

        assertNull(model.uiState.value.import)
    }

    @Test
    fun applyImportPostsTheApplyRequestAndTracksTheResult() = runTest(dispatcher) {
        val api = TransferImportApi()
        val model = signedIn(api)
        model.uploadImport(4, ByteArrayInputStream(byteArrayOf(1, 2, 3, 4)))
        api.nextStatus = ImportStatus.COMPLETED

        model.applyImport()
        advanceUntilIdle()

        assertEquals(ImportStatus.COMPLETED, model.uiState.value.import?.status)
    }

    @Test
    fun applyImportWithNothingTrackedDoesNothing() = runTest(dispatcher) {
        val api = TransferImportApi()
        val model = signedIn(api)

        model.applyImport()
        advanceUntilIdle()

        assertNull(model.uiState.value.import)
    }

    @Test
    fun aFailedUploadReportsAProblemAndLeavesNothingTracked() = runTest(dispatcher) {
        val api = TransferImportApi()
        val model = signedIn(api)
        api.nextUploadFailure = java.io.IOException("offline")

        model.uploadImport(4, ByteArrayInputStream(byteArrayOf(1, 2, 3, 4)))

        assertNull(model.uiState.value.import)
        assertNotNull(model.uiState.value.importProblem)
        assertFalse(model.uiState.value.importBusy)
    }

    @Test
    fun clearImportResetsState() = runTest(dispatcher) {
        val api = TransferImportApi()
        val model = signedIn(api)
        model.uploadImport(4, ByteArrayInputStream(byteArrayOf(1, 2, 3, 4)))

        model.clearImport()

        assertNull(model.uiState.value.import)
        assertFalse(model.uiState.value.importBusy)
        assertNull(model.uiState.value.importProblem)
    }

    private suspend fun TestScope.signedIn(api: ReferenceContract): ReferenceViewModel {
        val model = ReferenceViewModel(config = ReferenceConfig(BASE_URL), api = api)
        model.signIn("someone@example.test", "secret")
        advanceUntilIdle()
        return model
    }
}

private const val BASE_URL = "https://sidebyside.example"

private class TransferImportApi : FakeReferenceContract() {
    var nextStatus: ImportStatus = ImportStatus.QUEUED
    var nextUploadFailure: Throwable? = null
    var uploadedArchiveSize: Long? = null
    var uploadedArchiveBytes: ByteArray? = null

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

    override suspend fun createTransferImport(
        spaceId: UUID,
        accessToken: String,
        archiveSize: Long,
        archive: java.io.InputStream,
    ): TransferImportDetail {
        nextUploadFailure?.let {
            nextUploadFailure = null
            throw it
        }
        uploadedArchiveSize = archiveSize
        uploadedArchiveBytes = archive.readBytes()
        return detail(ImportStatus.QUEUED)
    }

    override suspend fun getTransferImport(
        spaceId: UUID,
        accessToken: String,
        importId: UUID,
    ): TransferImportDetail = detail(nextStatus)

    override suspend fun applyTransferImport(
        spaceId: UUID,
        accessToken: String,
        importId: UUID,
    ): TransferImportDetail = detail(nextStatus)

    private fun detail(status: ImportStatus) = TransferImportDetail(
        artifactSize = 4096,
        completedAt = null,
        createdAt = OffsetDateTime.now(),
        errorCode = null,
        expiresAt = OffsetDateTime.now().plusHours(24),
        id = IMPORT_ID,
        scope = TransferScope.SHARED,
        status = status,
        summary = null,
        validatedAt = null,
    )
}

private val IMPORT_ID: UUID = UUID.fromString("33333333-3333-4333-8333-333333333333")
