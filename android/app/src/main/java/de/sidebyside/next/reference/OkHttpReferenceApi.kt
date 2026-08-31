package de.sidebyside.next.reference

import java.util.UUID
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext
import kotlinx.serialization.KSerializer
import kotlinx.serialization.encodeToString
import okhttp3.MediaType.Companion.toMediaType
import okhttp3.OkHttpClient
import okhttp3.Request
import okhttp3.RequestBody.Companion.toRequestBody
import okhttp3.Response
import sidebyside.api.models.AttachmentDetail
import sidebyside.api.models.AttachmentReadRequest
import sidebyside.api.models.AttachmentUploadCreate
import sidebyside.api.models.MemoryAttachmentSet
import sidebyside.api.models.MemoryCreate
import sidebyside.api.models.MemoryDetail
import sidebyside.api.models.ProblemDetails
import sidebyside.api.models.ReadDescriptor
import sidebyside.api.models.SessionView
import sidebyside.api.models.SignInRequest
import sidebyside.api.models.StoryPage
import sidebyside.api.models.UploadDescriptor

/**
 * A failed API call.
 *
 * The HTTP status is carried alongside the ProblemDetails code because the two
 * answer different questions: the code identifies the domain reason, the status
 * decides which system state the user sees. Dropping the status made
 * permission, conflict and rate-limit indistinguishable.
 */
class ReferenceApiException(
    val code: String?,
    override val message: String,
    val status: Int? = null,
) : RuntimeException(message)

class OkHttpReferenceApi(
    apiBaseUrl: String,
    private val client: OkHttpClient = OkHttpClient(),
) : ReferenceContract {
    private val baseUrl = apiBaseUrl.trimEnd('/')
    private val jsonMediaType = "application/json; charset=utf-8".toMediaType()

    init {
        require(baseUrl.startsWith("https://") || baseUrl.startsWith("http://")) {
            "SBS_API_BASE_URL must be a complete HTTP(S) URL."
        }
    }

    override suspend fun signIn(email: String, password: String): SessionView {
        val payload = SignInRequest(
            email = email,
            password = password,
            deviceName = "SideBySide Android M2 reference flow",
            platform = "android",
        )
        return executeJson(
            Request.Builder()
                .url("$baseUrl/api/v1/auth/sign-in")
                .post(SideBySideJson.encodeToString(SignInRequest.serializer(), payload).toRequestBody(jsonMediaType))
                .build(),
            SessionView.serializer(),
        )
    }

    override suspend fun createMemory(
        spaceId: UUID,
        accessToken: String,
        memory: MemoryCreate,
    ): MemoryDetail = executeJson(
        authenticatedRequest("$baseUrl/api/v1/spaces/$spaceId/memories", accessToken)
            .post(SideBySideJson.encodeToString(MemoryCreate.serializer(), memory).toRequestBody(jsonMediaType))
            .build(),
        MemoryDetail.serializer(),
    )

    override suspend fun createAttachmentUpload(
        spaceId: UUID,
        accessToken: String,
        request: AttachmentUploadCreate,
    ): UploadDescriptor = executeJson(
        authenticatedRequest("$baseUrl/api/v1/spaces/$spaceId/attachments", accessToken)
            .post(SideBySideJson.encodeToString(AttachmentUploadCreate.serializer(), request).toRequestBody(jsonMediaType))
            .build(),
        UploadDescriptor.serializer(),
    )

    override suspend fun uploadAttachmentBytes(
        accessToken: String,
        descriptor: UploadDescriptor,
        image: SelectedImage,
    ) {
        val builder = Request.Builder().url(resolveTransportUrl(descriptor.uploadUrl))
        descriptor.requiredHeaders.forEach { (name, value) -> builder.header(name, value) }
        if (descriptor.method == UploadDescriptor.Method.STREAM) {
            builder.header("Authorization", "Bearer $accessToken")
        }
        executeEmpty(
            builder
                .put(image.bytes.toRequestBody(image.mimeType.toMediaType()))
                .build(),
        )
    }

    override suspend fun finalizeAttachment(
        spaceId: UUID,
        accessToken: String,
        attachmentId: UUID,
    ): AttachmentDetail = executeJson(
        authenticatedRequest(
            "$baseUrl/api/v1/spaces/$spaceId/attachments/$attachmentId/finalize",
            accessToken,
        )
            .post("{}".toRequestBody(jsonMediaType))
            .build(),
        AttachmentDetail.serializer(),
    )

    override suspend fun getAttachment(
        spaceId: UUID,
        accessToken: String,
        attachmentId: UUID,
    ): AttachmentDetail = executeJson(
        authenticatedRequest("$baseUrl/api/v1/spaces/$spaceId/attachments/$attachmentId", accessToken)
            .get()
            .build(),
        AttachmentDetail.serializer(),
    )

    override suspend fun replaceMemoryAttachments(
        spaceId: UUID,
        accessToken: String,
        memoryId: UUID,
        ifMatch: Int,
        attachments: MemoryAttachmentSet,
    ): MemoryDetail = executeJson(
        authenticatedRequest(
            "$baseUrl/api/v1/spaces/$spaceId/memories/$memoryId/attachments",
            accessToken,
        )
            .header("If-Match", ifMatch.toString())
            .put(SideBySideJson.encodeToString(MemoryAttachmentSet.serializer(), attachments).toRequestBody(jsonMediaType))
            .build(),
        MemoryDetail.serializer(),
    )

    override suspend fun getTimeline(spaceId: UUID, accessToken: String): StoryPage = executeJson(
        authenticatedRequest("$baseUrl/api/v1/spaces/$spaceId/timeline?limit=25", accessToken)
            .get()
            .build(),
        StoryPage.serializer(),
    )

    override suspend fun createReadAccess(
        spaceId: UUID,
        accessToken: String,
        attachmentId: UUID,
        request: AttachmentReadRequest,
    ): ReadDescriptor = executeJson(
        authenticatedRequest(
            "$baseUrl/api/v1/spaces/$spaceId/attachments/$attachmentId/read-access",
            accessToken,
        )
            .post(SideBySideJson.encodeToString(AttachmentReadRequest.serializer(), request).toRequestBody(jsonMediaType))
            .build(),
        ReadDescriptor.serializer(),
    )

    override suspend fun readImageBytes(accessToken: String, descriptor: ReadDescriptor): ByteArray = withContext(Dispatchers.IO) {
        val builder = Request.Builder().url(resolveTransportUrl(descriptor.url)).get()
        if (descriptor.method == ReadDescriptor.Method.STREAM) {
            builder.header("Authorization", "Bearer $accessToken")
        }
        client.newCall(builder.build()).execute().use { response ->
            assertSuccessful(response)
            response.body.bytes()
        }
    }

    private fun authenticatedRequest(url: String, accessToken: String): Request.Builder =
        Request.Builder()
            .url(url)
            .header("Authorization", "Bearer $accessToken")

    private fun resolveTransportUrl(target: String): String = when {
        target.startsWith("https://") || target.startsWith("http://") -> target
        else -> "$baseUrl/${target.trimStart('/')}"
    }

    private suspend fun <T> executeJson(request: Request, serializer: KSerializer<T>): T = withContext(Dispatchers.IO) {
        client.newCall(request).execute().use { response ->
            assertSuccessful(response)
            val body = response.body.string()
            if (body.isBlank()) throw ReferenceApiException(null, "Empty API response.")
            SideBySideJson.decodeFromString(serializer, body)
        }
    }

    private suspend fun executeEmpty(request: Request) = withContext(Dispatchers.IO) {
        client.newCall(request).execute().use(::assertSuccessful)
    }

    private fun assertSuccessful(response: Response) {
        if (response.isSuccessful) return
        val responseText = response.body.string()
        val problem = runCatching {
            SideBySideJson.decodeFromString(ProblemDetails.serializer(), responseText)
        }.getOrNull()
        throw ReferenceApiException(
            problem?.code,
            problem?.detail ?: "API request failed (HTTP ${response.code}).",
            problem?.status ?: response.code,
        )
    }
}
