package de.sidebyside.next.reference

import de.sidebyside.next.demo.DemoPersona
import java.util.UUID
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext
import kotlinx.serialization.KSerializer
import kotlinx.serialization.Serializable
import kotlinx.serialization.builtins.ListSerializer
import kotlinx.serialization.encodeToString
import kotlinx.serialization.json.JsonNull
import kotlinx.serialization.json.JsonPrimitive
import kotlinx.serialization.json.buildJsonObject
import okhttp3.MediaType.Companion.toMediaType
import okhttp3.OkHttpClient
import okhttp3.Request
import okhttp3.RequestBody.Companion.toRequestBody
import okhttp3.Response
import sidebyside.api.models.AccountMembershipView
import sidebyside.api.models.AttachmentDetail
import sidebyside.api.models.AttachmentReadRequest
import sidebyside.api.models.AttachmentUploadCreate
import sidebyside.api.models.CommentCreate
import sidebyside.api.models.CommentDetail
import sidebyside.api.models.CommentPage
import sidebyside.api.models.CommentUpdate
import sidebyside.api.models.ContentVisibility
import sidebyside.api.models.HeartMomentCreate
import sidebyside.api.models.HeartMomentDetail
import sidebyside.api.models.HeartMomentPage
import sidebyside.api.models.HeartMomentUpdate
import sidebyside.api.models.HeartMomentVisibilityChange
import sidebyside.api.models.InstanceAccessStatus
import sidebyside.api.models.MagicLinkConsumeRequest
import sidebyside.api.models.DashboardView
import sidebyside.api.models.MemoryAttachmentSet
import sidebyside.api.models.ThinkingOfYouAccepted
import sidebyside.api.models.ThinkingOfYouCreate
import sidebyside.api.models.MemoryCreate
import sidebyside.api.models.MemoryDetail
import sidebyside.api.models.MemoryUpdate
import sidebyside.api.models.MilestoneDetail
import sidebyside.api.models.MilestoneUpdate
import sidebyside.api.models.PartnerProfileView
import sidebyside.api.models.PlanComplete
import sidebyside.api.models.PlanDetail
import sidebyside.api.models.PlanPage
import sidebyside.api.models.PlanReturnToWishResponse
import sidebyside.api.models.PlanSchedule
import sidebyside.api.models.PlanUpdate
import sidebyside.api.models.ProblemDetails
import sidebyside.api.models.ProfileIdentityUpdate
import sidebyside.api.models.ReadDescriptor
import sidebyside.api.models.SessionView
import sidebyside.api.models.SignInRequest
import sidebyside.api.models.SpaceView
import sidebyside.api.models.StoryPage
import sidebyside.api.models.UploadDescriptor
import sidebyside.api.models.WishCreate
import sidebyside.api.models.WishDetail
import sidebyside.api.models.WishPage
import sidebyside.api.models.WishToPlan
import sidebyside.api.models.WishToPlanResponse
import sidebyside.api.models.WishUpdate

/** The demo entry response. It is not part of the generated contract. */
@Serializable
private data class DemoEntryPayload(val token: String)

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

/**
 * Appends a cursor, encoded, or nothing at all.
 *
 * A cursor is opaque and server-issued; it is passed back exactly as received
 * rather than parsed or rebuilt.
 */
private fun cursorQuery(cursor: String?): String =
    cursor?.let { "&cursor=" + java.net.URLEncoder.encode(it, "UTF-8") }.orEmpty()

/** A transition that carries no body still has to send valid JSON. */
private const val EMPTY_JSON_BODY = "{}"

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

    override suspend fun getInstanceStatus(): InstanceAccessStatus =
        executeJson(
            Request.Builder()
                .url("$baseUrl/api/v1/instance/status")
                .get()
                .build(),
            InstanceAccessStatus.serializer(),
        )

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

    override suspend fun consumeMagicLink(token: String): SessionView {
        val payload = MagicLinkConsumeRequest(
            token = token,
            deviceName = "SideBySide Android",
            platform = "android",
        )
        return executeJson(
            Request.Builder()
                .url("$baseUrl/api/v1/auth/magic-link/consume")
                .post(
                    SideBySideJson
                        .encodeToString(MagicLinkConsumeRequest.serializer(), payload)
                        .toRequestBody(jsonMediaType),
                )
                .build(),
            SessionView.serializer(),
        )
    }

    override suspend fun listMemberships(accessToken: String): List<AccountMembershipView> =
        executeJson(
            authenticatedRequest("$baseUrl/api/v1/auth/memberships", accessToken)
                .get()
                .build(),
            ListSerializer(AccountMembershipView.serializer()),
        )

    /*
     * Hand-written on purpose: the demo entry is excluded from the OpenAPI
     * contract, so no generated call exists. The base URL is passed in rather
     * than taken from this client, because entering the demo must not depend on
     * the configured endpoint and must not overwrite it.
     */
    override suspend fun createDemoEntry(baseUrl: String, persona: DemoPersona): String {
        val payload = buildJsonObject { put("persona", JsonPrimitive(persona.wireValue)) }
        val entry = executeJson(
            Request.Builder()
                .url("${baseUrl.trimEnd('/')}/api/v1/demo/entry")
                .post(payload.toString().toRequestBody(jsonMediaType))
                .build(),
            DemoEntryPayload.serializer(),
        )
        return entry.token
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

    override suspend fun getMemory(
        spaceId: UUID,
        accessToken: String,
        memoryId: UUID,
    ): MemoryDetail = executeJson(
        authenticatedRequest("$baseUrl/api/v1/spaces/$spaceId/memories/$memoryId", accessToken)
            .get()
            .build(),
        MemoryDetail.serializer(),
    )

    override suspend fun updateMemory(
        spaceId: UUID,
        accessToken: String,
        memoryId: UUID,
        ifMatch: Int,
        update: MemoryUpdate,
    ): MemoryDetail = executeJson(
        authenticatedRequest("$baseUrl/api/v1/spaces/$spaceId/memories/$memoryId", accessToken)
            .header("If-Match", ifMatch.toString())
            .patch(
                SideBySideJson.encodeToString(MemoryUpdate.serializer(), update)
                    .toRequestBody(jsonMediaType),
            )
            .build(),
        MemoryDetail.serializer(),
    )

    override suspend fun deleteMemory(
        spaceId: UUID,
        accessToken: String,
        memoryId: UUID,
        ifMatch: Int,
    ) = executeEmpty(
        authenticatedRequest("$baseUrl/api/v1/spaces/$spaceId/memories/$memoryId", accessToken)
            .header("If-Match", ifMatch.toString())
            .delete()
            .build(),
    )

    override suspend fun listComments(
        spaceId: UUID,
        accessToken: String,
        parent: ReferenceContract.CommentParent,
        parentId: UUID,
        cursor: String?,
    ): CommentPage = executeJson(
        authenticatedRequest(
            "$baseUrl/api/v1/spaces/$spaceId/${parent.segment}/$parentId/comments?limit=50" +
                cursorQuery(cursor),
            accessToken,
        ).get().build(),
        CommentPage.serializer(),
    )

    override suspend fun createComment(
        spaceId: UUID,
        accessToken: String,
        parent: ReferenceContract.CommentParent,
        parentId: UUID,
        comment: CommentCreate,
    ): CommentDetail = executeJson(
        authenticatedRequest(
            "$baseUrl/api/v1/spaces/$spaceId/${parent.segment}/$parentId/comments",
            accessToken,
        )
            .post(
                SideBySideJson.encodeToString(CommentCreate.serializer(), comment)
                    .toRequestBody(jsonMediaType),
            )
            .build(),
        CommentDetail.serializer(),
    )

    override suspend fun updateComment(
        spaceId: UUID,
        accessToken: String,
        commentId: UUID,
        ifMatch: Int,
        update: CommentUpdate,
    ): CommentDetail = executeJson(
        authenticatedRequest("$baseUrl/api/v1/spaces/$spaceId/comments/$commentId", accessToken)
            .header("If-Match", ifMatch.toString())
            .patch(
                SideBySideJson.encodeToString(CommentUpdate.serializer(), update)
                    .toRequestBody(jsonMediaType),
            )
            .build(),
        CommentDetail.serializer(),
    )

    override suspend fun deleteComment(
        spaceId: UUID,
        accessToken: String,
        commentId: UUID,
        ifMatch: Int,
    ) = executeEmpty(
        authenticatedRequest("$baseUrl/api/v1/spaces/$spaceId/comments/$commentId", accessToken)
            .header("If-Match", ifMatch.toString())
            .delete()
            .build(),
    )

    override suspend fun getMilestone(
        spaceId: UUID,
        accessToken: String,
        milestoneId: UUID,
    ): MilestoneDetail = executeJson(
        authenticatedRequest(
            "$baseUrl/api/v1/spaces/$spaceId/milestones/$milestoneId",
            accessToken,
        ).get().build(),
        MilestoneDetail.serializer(),
    )

    override suspend fun updateMilestone(
        spaceId: UUID,
        accessToken: String,
        milestoneId: UUID,
        ifMatch: Int,
        update: MilestoneUpdate,
    ): MilestoneDetail = executeJson(
        authenticatedRequest(
            "$baseUrl/api/v1/spaces/$spaceId/milestones/$milestoneId",
            accessToken,
        )
            .header("If-Match", ifMatch.toString())
            .patch(
                SideBySideJson.encodeToString(MilestoneUpdate.serializer(), update)
                    .toRequestBody(jsonMediaType),
            )
            .build(),
        MilestoneDetail.serializer(),
    )

    override suspend fun deleteMilestone(
        spaceId: UUID,
        accessToken: String,
        milestoneId: UUID,
        ifMatch: Int,
    ) = executeEmpty(
        authenticatedRequest(
            "$baseUrl/api/v1/spaces/$spaceId/milestones/$milestoneId",
            accessToken,
        )
            .header("If-Match", ifMatch.toString())
            .delete()
            .build(),
    )

    override suspend fun getHeartMoment(
        spaceId: UUID,
        accessToken: String,
        heartMomentId: UUID,
    ): HeartMomentDetail = executeJson(
        authenticatedRequest(
            "$baseUrl/api/v1/spaces/$spaceId/heart-moments/$heartMomentId",
            accessToken,
        ).get().build(),
        HeartMomentDetail.serializer(),
    )

    override suspend fun listHeartMoments(
        spaceId: UUID,
        accessToken: String,
        visibility: ContentVisibility?,
    ): HeartMomentPage {
        val filter = visibility?.let { "&visibility=${it.value}" }.orEmpty()
        return executeJson(
            authenticatedRequest(
                "$baseUrl/api/v1/spaces/$spaceId/heart-moments?limit=50$filter",
                accessToken,
            ).get().build(),
            HeartMomentPage.serializer(),
        )
    }

    override suspend fun createHeartMoment(
        spaceId: UUID,
        accessToken: String,
        heartMoment: HeartMomentCreate,
    ): HeartMomentDetail = executeJson(
        authenticatedRequest("$baseUrl/api/v1/spaces/$spaceId/heart-moments", accessToken)
            .post(
                SideBySideJson.encodeToString(HeartMomentCreate.serializer(), heartMoment)
                    .toRequestBody(jsonMediaType),
            )
            .build(),
        HeartMomentDetail.serializer(),
    )

    override suspend fun updateHeartMoment(
        spaceId: UUID,
        accessToken: String,
        heartMomentId: UUID,
        ifMatch: Int,
        update: HeartMomentUpdate,
    ): HeartMomentDetail = executeJson(
        authenticatedRequest(
            "$baseUrl/api/v1/spaces/$spaceId/heart-moments/$heartMomentId",
            accessToken,
        )
            .header("If-Match", ifMatch.toString())
            .patch(
                SideBySideJson.encodeToString(HeartMomentUpdate.serializer(), update)
                    .toRequestBody(jsonMediaType),
            )
            .build(),
        HeartMomentDetail.serializer(),
    )

    override suspend fun changeHeartMomentVisibility(
        spaceId: UUID,
        accessToken: String,
        heartMomentId: UUID,
        ifMatch: Int,
        change: HeartMomentVisibilityChange,
    ): HeartMomentDetail = executeJson(
        authenticatedRequest(
            "$baseUrl/api/v1/spaces/$spaceId/heart-moments/$heartMomentId/visibility",
            accessToken,
        )
            .header("If-Match", ifMatch.toString())
            .patch(
                SideBySideJson
                    .encodeToString(HeartMomentVisibilityChange.serializer(), change)
                    .toRequestBody(jsonMediaType),
            )
            .build(),
        HeartMomentDetail.serializer(),
    )

    override suspend fun deleteHeartMoment(
        spaceId: UUID,
        accessToken: String,
        heartMomentId: UUID,
        ifMatch: Int,
    ) = executeEmpty(
        authenticatedRequest(
            "$baseUrl/api/v1/spaces/$spaceId/heart-moments/$heartMomentId",
            accessToken,
        )
            .header("If-Match", ifMatch.toString())
            .delete()
            .build(),
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

    override suspend fun deleteAttachment(
        spaceId: UUID,
        accessToken: String,
        attachmentId: UUID,
        ifMatch: Int,
    ) {
        executeEmpty(
            authenticatedRequest("$baseUrl/api/v1/spaces/$spaceId/attachments/$attachmentId", accessToken)
                .header("If-Match", ifMatch.toString())
                .delete()
                .build(),
        )
    }

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

    override suspend fun listWishes(spaceId: UUID, accessToken: String): WishPage = executeJson(
        authenticatedRequest("$baseUrl/api/v1/spaces/$spaceId/wishes?limit=50", accessToken)
            .get().build(),
        WishPage.serializer(),
    )

    override suspend fun createWish(
        spaceId: UUID,
        accessToken: String,
        wish: WishCreate,
    ): WishDetail = executeJson(
        authenticatedRequest("$baseUrl/api/v1/spaces/$spaceId/wishes", accessToken)
            .post(
                SideBySideJson.encodeToString(WishCreate.serializer(), wish)
                    .toRequestBody(jsonMediaType),
            ).build(),
        WishDetail.serializer(),
    )

    override suspend fun updateWish(
        spaceId: UUID,
        accessToken: String,
        wishId: UUID,
        ifMatch: Int,
        update: WishUpdate,
    ): WishDetail = executeJson(
        authenticatedRequest("$baseUrl/api/v1/spaces/$spaceId/wishes/$wishId", accessToken)
            .header("If-Match", ifMatch.toString())
            .patch(
                SideBySideJson.encodeToString(WishUpdate.serializer(), update)
                    .toRequestBody(jsonMediaType),
            ).build(),
        WishDetail.serializer(),
    )

    override suspend fun deleteWish(
        spaceId: UUID,
        accessToken: String,
        wishId: UUID,
        ifMatch: Int,
    ) = executeEmpty(
        authenticatedRequest("$baseUrl/api/v1/spaces/$spaceId/wishes/$wishId", accessToken)
            .header("If-Match", ifMatch.toString())
            .delete().build(),
    )

    override suspend fun planWish(
        spaceId: UUID,
        accessToken: String,
        wishId: UUID,
        ifMatch: Int,
        conversion: WishToPlan,
    ): WishToPlanResponse = executeJson(
        authenticatedRequest("$baseUrl/api/v1/spaces/$spaceId/wishes/$wishId/plan", accessToken)
            .header("If-Match", ifMatch.toString())
            .post(
                SideBySideJson.encodeToString(WishToPlan.serializer(), conversion)
                    .toRequestBody(jsonMediaType),
            ).build(),
        WishToPlanResponse.serializer(),
    )

    override suspend fun listPlans(spaceId: UUID, accessToken: String): PlanPage = executeJson(
        authenticatedRequest("$baseUrl/api/v1/spaces/$spaceId/plans?limit=50", accessToken)
            .get().build(),
        PlanPage.serializer(),
    )

    override suspend fun updatePlan(
        spaceId: UUID,
        accessToken: String,
        planId: UUID,
        ifMatch: Int,
        update: PlanUpdate,
    ): PlanDetail = executeJson(
        authenticatedRequest("$baseUrl/api/v1/spaces/$spaceId/plans/$planId", accessToken)
            .header("If-Match", ifMatch.toString())
            .patch(
                SideBySideJson.encodeToString(PlanUpdate.serializer(), update)
                    .toRequestBody(jsonMediaType),
            ).build(),
        PlanDetail.serializer(),
    )

    override suspend fun deletePlan(
        spaceId: UUID,
        accessToken: String,
        planId: UUID,
        ifMatch: Int,
    ) = executeEmpty(
        authenticatedRequest("$baseUrl/api/v1/spaces/$spaceId/plans/$planId", accessToken)
            .header("If-Match", ifMatch.toString())
            .delete().build(),
    )

    override suspend fun schedulePlan(
        spaceId: UUID,
        accessToken: String,
        planId: UUID,
        ifMatch: Int,
        schedule: PlanSchedule,
    ): PlanDetail = executeJson(
        authenticatedRequest("$baseUrl/api/v1/spaces/$spaceId/plans/$planId/schedule", accessToken)
            .header("If-Match", ifMatch.toString())
            .post(
                SideBySideJson.encodeToString(PlanSchedule.serializer(), schedule)
                    .toRequestBody(jsonMediaType),
            ).build(),
        PlanDetail.serializer(),
    )

    override suspend fun unschedulePlan(
        spaceId: UUID,
        accessToken: String,
        planId: UUID,
        ifMatch: Int,
    ): PlanDetail = executeJson(
        authenticatedRequest(
            "$baseUrl/api/v1/spaces/$spaceId/plans/$planId/unschedule",
            accessToken,
        )
            .header("If-Match", ifMatch.toString())
            .post(EMPTY_JSON_BODY.toRequestBody(jsonMediaType)).build(),
        PlanDetail.serializer(),
    )

    override suspend fun completePlan(
        spaceId: UUID,
        accessToken: String,
        planId: UUID,
        ifMatch: Int,
        completion: PlanComplete,
    ): PlanDetail = executeJson(
        authenticatedRequest("$baseUrl/api/v1/spaces/$spaceId/plans/$planId/complete", accessToken)
            .header("If-Match", ifMatch.toString())
            .post(
                SideBySideJson.encodeToString(PlanComplete.serializer(), completion)
                    .toRequestBody(jsonMediaType),
            ).build(),
        PlanDetail.serializer(),
    )

    override suspend fun returnPlanToWish(
        spaceId: UUID,
        accessToken: String,
        planId: UUID,
        ifMatch: Int,
    ): PlanReturnToWishResponse = executeJson(
        authenticatedRequest(
            "$baseUrl/api/v1/spaces/$spaceId/plans/$planId/return-to-wish",
            accessToken,
        )
            .header("If-Match", ifMatch.toString())
            .post(EMPTY_JSON_BODY.toRequestBody(jsonMediaType)).build(),
        PlanReturnToWishResponse.serializer(),
    )

    override suspend fun getDashboard(
        spaceId: UUID,
        accessToken: String,
    ): DashboardView = executeJson(
        authenticatedRequest("$baseUrl/api/v1/spaces/$spaceId/dashboard", accessToken)
            .get().build(),
        DashboardView.serializer(),
    )

    override suspend fun sendThinkingOfYou(
        spaceId: UUID,
        accessToken: String,
        gesture: ThinkingOfYouCreate,
    ): ThinkingOfYouAccepted = executeJson(
        authenticatedRequest("$baseUrl/api/v1/spaces/$spaceId/thinking-of-you", accessToken)
            .post(
                SideBySideJson.encodeToString(ThinkingOfYouCreate.serializer(), gesture)
                    .toRequestBody(jsonMediaType),
            ).build(),
        ThinkingOfYouAccepted.serializer(),
    )

    override suspend fun getTimeline(
        spaceId: UUID,
        accessToken: String,
        cursor: String?,
    ): StoryPage = executeJson(
        authenticatedRequest(
            "$baseUrl/api/v1/spaces/$spaceId/timeline?limit=25" + cursorQuery(cursor),
            accessToken,
        ).get().build(),
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

    override suspend fun getSpace(spaceId: UUID, accessToken: String): SpaceView = executeJson(
        authenticatedRequest("$baseUrl/api/v1/spaces/$spaceId", accessToken)
            .get()
            .build(),
        SpaceView.serializer(),
    )

    override suspend fun getProfile(
        spaceId: UUID,
        accessToken: String,
        accountId: UUID,
    ): PartnerProfileView = executeJson(
        authenticatedRequest("$baseUrl/api/v1/spaces/$spaceId/profiles/$accountId", accessToken)
            .get()
            .build(),
        PartnerProfileView.serializer(),
    )

    override suspend fun updateProfileIdentity(
        spaceId: UUID,
        accessToken: String,
        accountId: UUID,
        ifMatch: Int,
        update: ProfileIdentityUpdate,
    ): PartnerProfileView = executeJson(
        authenticatedRequest("$baseUrl/api/v1/spaces/$spaceId/profiles/$accountId", accessToken)
            .header("If-Match", ifMatch.toString())
            .patch(SideBySideJson.encodeToString(ProfileIdentityUpdate.serializer(), update).toRequestBody(jsonMediaType))
            .build(),
        PartnerProfileView.serializer(),
    )

    override suspend fun removeProfileAvatar(
        spaceId: UUID,
        accessToken: String,
        accountId: UUID,
        ifMatch: Int,
    ): PartnerProfileView {
        val payload = buildJsonObject { put("profileAttachmentId", JsonNull) }
        return executeJson(
            authenticatedRequest("$baseUrl/api/v1/spaces/$spaceId/profiles/$accountId", accessToken)
                .header("If-Match", ifMatch.toString())
                .patch(payload.toString().toRequestBody(jsonMediaType))
                .build(),
            PartnerProfileView.serializer(),
        )
    }

    override suspend fun readProfileAvatar(
        spaceId: UUID,
        accessToken: String,
        accountId: UUID,
    ): ByteArray = withContext(Dispatchers.IO) {
        val request = authenticatedRequest(
            "$baseUrl/api/v1/spaces/$spaceId/profiles/$accountId/avatar/content",
            accessToken,
        )
            .get()
            .build()
        client.newCall(request).execute().use { response ->
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
