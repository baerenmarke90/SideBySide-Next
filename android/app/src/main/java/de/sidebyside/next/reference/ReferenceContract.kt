package de.sidebyside.next.reference

import de.sidebyside.next.demo.DemoPersona
import java.util.UUID
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
import sidebyside.api.models.ProfileIdentityUpdate
import sidebyside.api.models.ReadDescriptor
import sidebyside.api.models.SessionView
import sidebyside.api.models.SpaceView
import sidebyside.api.models.StoryPage
import sidebyside.api.models.UploadDescriptor
import sidebyside.api.models.WishCreate
import sidebyside.api.models.WishDetail
import sidebyside.api.models.WishPage
import sidebyside.api.models.WishToPlan
import sidebyside.api.models.WishToPlanResponse
import sidebyside.api.models.WishUpdate

data class SelectedImage(
    val bytes: ByteArray,
    val displayName: String,
    val mimeType: String,
)

data class ReferenceFlowResult(
    val memory: MemoryDetail,
    val story: StoryPage,
    val imageBytes: ByteArray?,
)

interface ReferenceContract {
    suspend fun getInstanceStatus(): InstanceAccessStatus

    suspend fun signIn(email: String, password: String): SessionView

    /**
     * Exchanges a one-time entry proof for a session.
     *
     * The demo entry issues such a proof, so the demo never needs a password
     * that could be embedded in the app.
     */
    suspend fun consumeMagicLink(token: String): SessionView

    /**
     * The Spaces this account may open, as the server sees them.
     *
     * The active Space is derived from this rather than configured, because a
     * demo persona's Space is not known at build time.
     */
    suspend fun listMemberships(accessToken: String): List<AccountMembershipView>

    /**
     * Requests a one-time entry proof for a canonical demo persona.
     *
     * `POST /api/v1/demo/entry` is deliberately absent from the OpenAPI
     * contract: it is a facility of the isolated demo deployment, not a
     * supported authentication method for a normal installation. It is
     * therefore declared here by hand instead of through the generated client,
     * and it is the only call in this client that is.
     */
    suspend fun createDemoEntry(baseUrl: String, persona: DemoPersona): String

    suspend fun createMemory(spaceId: UUID, accessToken: String, memory: MemoryCreate): MemoryDetail

    suspend fun getMemory(spaceId: UUID, accessToken: String, memoryId: UUID): MemoryDetail

    /**
     * Changes a memory.
     *
     * [ifMatch] is the version the change was written against. The server
     * answers 409 when the partner changed the memory in the meantime, which is
     * the point: without it the later write would silently overwrite the
     * earlier one.
     */
    suspend fun updateMemory(
        spaceId: UUID,
        accessToken: String,
        memoryId: UUID,
        ifMatch: Int,
        update: MemoryUpdate,
    ): MemoryDetail

    suspend fun deleteMemory(spaceId: UUID, accessToken: String, memoryId: UUID, ifMatch: Int)

    suspend fun getMilestone(
        spaceId: UUID,
        accessToken: String,
        milestoneId: UUID,
    ): MilestoneDetail

    suspend fun updateMilestone(
        spaceId: UUID,
        accessToken: String,
        milestoneId: UUID,
        ifMatch: Int,
        update: MilestoneUpdate,
    ): MilestoneDetail

    suspend fun deleteMilestone(
        spaceId: UUID,
        accessToken: String,
        milestoneId: UUID,
        ifMatch: Int,
    )

    suspend fun getHeartMoment(
        spaceId: UUID,
        accessToken: String,
        heartMomentId: UUID,
    ): HeartMomentDetail

    /**
     * What a comment hangs on.
     *
     * The contract has a separate list and create path per kind, but one update
     * and one delete for all of them, so only reading and writing need to know
     * the parent.
     */
    enum class CommentParent(val segment: String) {
        MEMORY("memories"),
        MILESTONE("milestones"),
        HEART_MOMENT("heart-moments"),
    }

    suspend fun listComments(
        spaceId: UUID,
        accessToken: String,
        parent: CommentParent,
        parentId: UUID,
        cursor: String? = null,
    ): CommentPage

    suspend fun createComment(
        spaceId: UUID,
        accessToken: String,
        parent: CommentParent,
        parentId: UUID,
        comment: CommentCreate,
    ): CommentDetail

    /**
     * Comments are addressed by their own id, not through their parent: the
     * contract has one update and one delete for all three kinds.
     */
    suspend fun updateComment(
        spaceId: UUID,
        accessToken: String,
        commentId: UUID,
        ifMatch: Int,
        update: CommentUpdate,
    ): CommentDetail

    suspend fun deleteComment(
        spaceId: UUID,
        accessToken: String,
        commentId: UUID,
        ifMatch: Int,
    )

    /**
     * The HeartMoments this account may read.
     *
     * The server narrows this to what the caller is authorised for, and the
     * [visibility] filter narrows it further — it never widens it. Asking for
     * `PRIVATE` therefore returns the caller's own private moments, and an
     * empty page for anyone else's, rather than a refusal that would confirm
     * that someone else's exist.
     */
    suspend fun listHeartMoments(
        spaceId: UUID,
        accessToken: String,
        visibility: ContentVisibility? = null,
    ): HeartMomentPage

    suspend fun createHeartMoment(
        spaceId: UUID,
        accessToken: String,
        heartMoment: HeartMomentCreate,
    ): HeartMomentDetail

    suspend fun updateHeartMoment(
        spaceId: UUID,
        accessToken: String,
        heartMomentId: UUID,
        ifMatch: Int,
        update: HeartMomentUpdate,
    ): HeartMomentDetail

    /**
     * Changes who may see a HeartMoment.
     *
     * Its own call, not a field on [updateHeartMoment], because the server
     * makes it one: `SHARED -> PRIVATE` deletes the moment's comments in the
     * same transaction, and going back does not restore them. That must never
     * happen as a side effect of editing text.
     */
    suspend fun changeHeartMomentVisibility(
        spaceId: UUID,
        accessToken: String,
        heartMomentId: UUID,
        ifMatch: Int,
        change: HeartMomentVisibilityChange,
    ): HeartMomentDetail

    suspend fun deleteHeartMoment(
        spaceId: UUID,
        accessToken: String,
        heartMomentId: UUID,
        ifMatch: Int,
    )

    suspend fun createAttachmentUpload(
        spaceId: UUID,
        accessToken: String,
        request: AttachmentUploadCreate,
    ): UploadDescriptor

    suspend fun uploadAttachmentBytes(accessToken: String, descriptor: UploadDescriptor, image: SelectedImage)

    suspend fun finalizeAttachment(spaceId: UUID, accessToken: String, attachmentId: UUID): AttachmentDetail

    suspend fun getAttachment(spaceId: UUID, accessToken: String, attachmentId: UUID): AttachmentDetail

    suspend fun deleteAttachment(
        spaceId: UUID,
        accessToken: String,
        attachmentId: UUID,
        ifMatch: Int,
    ) {
        unsupportedProfileOperation()
    }

    suspend fun replaceMemoryAttachments(
        spaceId: UUID,
        accessToken: String,
        memoryId: UUID,
        ifMatch: Int,
        attachments: MemoryAttachmentSet,
    ): MemoryDetail

    suspend fun listWishes(spaceId: UUID, accessToken: String): WishPage

    suspend fun createWish(spaceId: UUID, accessToken: String, wish: WishCreate): WishDetail

    suspend fun updateWish(
        spaceId: UUID,
        accessToken: String,
        wishId: UUID,
        ifMatch: Int,
        update: WishUpdate,
    ): WishDetail

    suspend fun deleteWish(spaceId: UUID, accessToken: String, wishId: UUID, ifMatch: Int)

    /**
     * Turns a wish into a plan.
     *
     * Both survive: the wish moves `OPEN -> PLANNED` and goes on recording that
     * someone wanted this, while the plan records the doing. The answer carries
     * both, which is why it is not simply a plan.
     */
    suspend fun planWish(
        spaceId: UUID,
        accessToken: String,
        wishId: UUID,
        ifMatch: Int,
        conversion: WishToPlan,
    ): WishToPlanResponse

    suspend fun listPlans(spaceId: UUID, accessToken: String): PlanPage

    suspend fun updatePlan(
        spaceId: UUID,
        accessToken: String,
        planId: UUID,
        ifMatch: Int,
        update: PlanUpdate,
    ): PlanDetail

    suspend fun deletePlan(spaceId: UUID, accessToken: String, planId: UUID, ifMatch: Int)

    /** `IDEA -> PLANNED`. */
    suspend fun schedulePlan(
        spaceId: UUID,
        accessToken: String,
        planId: UUID,
        ifMatch: Int,
        schedule: PlanSchedule,
    ): PlanDetail

    /** `PLANNED -> IDEA`, keeping the plan. */
    suspend fun unschedulePlan(
        spaceId: UUID,
        accessToken: String,
        planId: UUID,
        ifMatch: Int,
    ): PlanDetail

    /** `-> COMPLETED`, with the day it actually happened. */
    suspend fun completePlan(
        spaceId: UUID,
        accessToken: String,
        planId: UUID,
        ifMatch: Int,
        completion: PlanComplete,
    ): PlanDetail

    /**
     * All the way back: the plan is removed and its wish reopens.
     *
     * The wish deliberately receives nothing back from the plan (M3-D03), so
     * whatever was written into the plan is lost. The screen says so first.
     */
    suspend fun returnPlanToWish(
        spaceId: UUID,
        accessToken: String,
        planId: UUID,
        ifMatch: Int,
    ): PlanReturnToWishResponse

    suspend fun getDashboard(spaceId: UUID, accessToken: String): DashboardView

    /**
     * Sends the partner a sign that you are thinking of them.
     *
     * [gesture] carries a client request id, so the same tap sent twice is one
     * gesture rather than two — which matters, because a tap that looks like it
     * failed is exactly the tap someone repeats. The server answers 429 when it
     * has been sent too often; that is a product state, not a failure.
     */
    suspend fun sendThinkingOfYou(
        spaceId: UUID,
        accessToken: String,
        gesture: ThinkingOfYouCreate,
    ): ThinkingOfYouAccepted

    /**
     * One page of the Story.
     *
     * [cursor] continues from a previous page's `nextCursor`. Without paging a
     * couple simply stops seeing their own history past the first page, which
     * is the kind of loss nothing on screen would announce.
     */
    suspend fun getTimeline(
        spaceId: UUID,
        accessToken: String,
        cursor: String? = null,
    ): StoryPage

    suspend fun createReadAccess(
        spaceId: UUID,
        accessToken: String,
        attachmentId: UUID,
        request: AttachmentReadRequest,
    ): ReadDescriptor

    suspend fun readImageBytes(accessToken: String, descriptor: ReadDescriptor): ByteArray

    /** Profile APIs are optional for older test fakes and loaded lazily by the UI. */
    suspend fun getSpace(spaceId: UUID, accessToken: String): SpaceView = unsupportedProfileOperation()

    suspend fun getProfile(
        spaceId: UUID,
        accessToken: String,
        accountId: UUID,
    ): PartnerProfileView = unsupportedProfileOperation()

    suspend fun updateProfileIdentity(
        spaceId: UUID,
        accessToken: String,
        accountId: UUID,
        ifMatch: Int,
        update: ProfileIdentityUpdate,
    ): PartnerProfileView = unsupportedProfileOperation()

    /**
     * Explicit avatar removal is separate because the generated nullable DTO is
     * encoded with `explicitNulls = false`; the wire contract still requires a
     * literal JSON null to distinguish removal from omission.
     */
    suspend fun removeProfileAvatar(
        spaceId: UUID,
        accessToken: String,
        accountId: UUID,
        ifMatch: Int,
    ): PartnerProfileView = unsupportedProfileOperation()

    suspend fun readProfileAvatar(
        spaceId: UUID,
        accessToken: String,
        accountId: UUID,
    ): ByteArray = unsupportedProfileOperation()
}

private fun unsupportedProfileOperation(): Nothing =
    throw UnsupportedOperationException("This ReferenceContract fake does not implement profile identity.")
