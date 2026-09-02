package de.sidebyside.next.reference

import de.sidebyside.next.demo.DemoPersona
import java.util.UUID
import sidebyside.api.models.AccountMembershipView
import sidebyside.api.models.AttachmentDetail
import sidebyside.api.models.AttachmentReadRequest
import sidebyside.api.models.ActivityPage
import sidebyside.api.models.AttachmentUploadCreate
import sidebyside.api.models.CommentCreate
import sidebyside.api.models.CommentDetail
import sidebyside.api.models.CommentPage
import sidebyside.api.models.CollectionCreate
import sidebyside.api.models.CollectionDetail
import sidebyside.api.models.CollectionItemCreate
import sidebyside.api.models.CollectionItemDetail
import sidebyside.api.models.CollectionItemUpdate
import sidebyside.api.models.CollectionPage
import sidebyside.api.models.ChapterCreate
import sidebyside.api.models.ChapterDetail
import sidebyside.api.models.ChapterPage
import sidebyside.api.models.ChapterContent
import sidebyside.api.models.ChapterUpdate
import sidebyside.api.models.CollectionUpdate
import sidebyside.api.models.CommentUpdate
import sidebyside.api.models.ContentVisibility
import sidebyside.api.models.HeartMomentCreate
import sidebyside.api.models.HeartMomentDetail
import sidebyside.api.models.HeartMomentPage
import sidebyside.api.models.HeartMomentUpdate
import sidebyside.api.models.HeartMomentVisibilityChange
import sidebyside.api.models.InstanceAccessStatus
import sidebyside.api.models.DashboardView
import sidebyside.api.models.AcceptRequest
import sidebyside.api.models.IssuedInvitationView
import sidebyside.api.models.InvitationView
import sidebyside.api.models.MembershipView
import sidebyside.api.models.ImportantDateFields
import sidebyside.api.models.ImportantDateView
import sidebyside.api.models.MemoryAttachmentSet
import sidebyside.api.models.PlaceCreate
import sidebyside.api.models.PlaceDetail
import sidebyside.api.models.PlacePage
import sidebyside.api.models.PlaceUpdate
import sidebyside.api.models.GiftIdeaCreate
import sidebyside.api.models.GiftIdeaDetail
import sidebyside.api.models.GiftIdeaPage
import sidebyside.api.models.GiftIdeaUpdate
import sidebyside.api.models.PrivateCollectionCreate
import sidebyside.api.models.PrivateCollectionDetail
import sidebyside.api.models.PrivateCollectionItemCreate
import sidebyside.api.models.PrivateCollectionItemDetail
import sidebyside.api.models.PrivateCollectionItemUpdate
import sidebyside.api.models.PrivateCollectionPage
import sidebyside.api.models.PrivateCollectionUpdate
import sidebyside.api.models.PrivateNoteCreate
import sidebyside.api.models.PrivateNoteDetail
import sidebyside.api.models.PrivateNotePage
import sidebyside.api.models.PrivateNoteUpdate
import sidebyside.api.models.ProfilePreferenceCreate
import sidebyside.api.models.ProfilePreferenceUpdate
import sidebyside.api.models.ProfilePreferenceView
import sidebyside.api.models.RelatedPersonDeletePolicy
import sidebyside.api.models.RelatedPersonFields
import sidebyside.api.models.RelatedPersonView
import sidebyside.api.models.SearchPage
import sidebyside.api.models.ThinkingOfYouAccepted
import sidebyside.api.models.ThinkingOfYouCreate
import sidebyside.api.models.MemoryCreate
import sidebyside.api.models.MemoryDetail
import sidebyside.api.models.MemoryUpdate
import sidebyside.api.models.MilestoneDetail
import sidebyside.api.models.MilestoneUpdate
import sidebyside.api.models.NotificationItem
import sidebyside.api.models.NotificationPage
import sidebyside.api.models.NotificationUnreadCount
import sidebyside.api.models.NotificationsReadAllResult
import sidebyside.api.models.PlanComplete
import sidebyside.api.models.PlanDetail
import sidebyside.api.models.PlanPage
import sidebyside.api.models.PlanReturnToWishResponse
import sidebyside.api.models.PlanSchedule
import sidebyside.api.models.PlanUpdate
import sidebyside.api.models.ReadDescriptor
import sidebyside.api.models.SessionView
import sidebyside.api.models.StoryPage
import sidebyside.api.models.UploadDescriptor
import sidebyside.api.models.WishCreate
import sidebyside.api.models.WishDetail
import sidebyside.api.models.WishPage
import sidebyside.api.models.WishToPlan
import sidebyside.api.models.WishToPlanResponse
import sidebyside.api.models.WishUpdate

/**
 * A [ReferenceContract] whose every call fails until a test says otherwise.
 *
 * Each test double used to restate the whole contract, so most of them carried
 * a dozen `error("not used")` bodies and every new endpoint broke all of them
 * at once. Overriding only what a test exercises also makes the double say what
 * the test is actually about.
 *
 * The failure names the method, so a call a test did not expect is reported as
 * itself rather than as a null or a silent default.
 */
abstract class FakeReferenceContract : ReferenceContract {
    override suspend fun getInstanceStatus(): InstanceAccessStatus =
        InstanceAccessStatus(
            maintenanceMode = false,
            registrationAvailable = true,
            registrationUnavailableReason = null,
        )

    override suspend fun signIn(email: String, password: String): SessionView =
        notExercised("signIn")

    override suspend fun consumeMagicLink(token: String): SessionView =
        notExercised("consumeMagicLink")

    override suspend fun listMemberships(accessToken: String): List<AccountMembershipView> =
        notExercised("listMemberships")

    override suspend fun createDemoEntry(baseUrl: String, persona: DemoPersona): String =
        notExercised("createDemoEntry")

    override suspend fun createMemory(
        spaceId: UUID,
        accessToken: String,
        memory: MemoryCreate,
    ): MemoryDetail = notExercised("createMemory")

    override suspend fun getMemory(
        spaceId: UUID,
        accessToken: String,
        memoryId: UUID,
    ): MemoryDetail = notExercised("getMemory")

    override suspend fun updateMemory(
        spaceId: UUID,
        accessToken: String,
        memoryId: UUID,
        ifMatch: Int,
        update: MemoryUpdate,
    ): MemoryDetail = notExercised("updateMemory")

    override suspend fun deleteMemory(
        spaceId: UUID,
        accessToken: String,
        memoryId: UUID,
        ifMatch: Int,
    ): Unit = notExercised("deleteMemory")

    override suspend fun listComments(
        spaceId: UUID,
        accessToken: String,
        parent: ReferenceContract.CommentParent,
        parentId: UUID,
        cursor: String?,
    ): CommentPage = notExercised("listComments")

    override suspend fun createComment(
        spaceId: UUID,
        accessToken: String,
        parent: ReferenceContract.CommentParent,
        parentId: UUID,
        comment: CommentCreate,
    ): CommentDetail = notExercised("createComment")

    override suspend fun createMilestone(
        spaceId: UUID,
        accessToken: String,
        fields: sidebyside.api.models.MilestoneCreate,
    ): MilestoneDetail = notExercised("createMilestone")

    override suspend fun getMilestone(
        spaceId: UUID,
        accessToken: String,
        milestoneId: UUID,
    ): MilestoneDetail = notExercised("getMilestone")

    override suspend fun updateMilestone(
        spaceId: UUID,
        accessToken: String,
        milestoneId: UUID,
        ifMatch: Int,
        update: MilestoneUpdate,
    ): MilestoneDetail = notExercised("updateMilestone")

    override suspend fun deleteMilestone(
        spaceId: UUID,
        accessToken: String,
        milestoneId: UUID,
        ifMatch: Int,
    ): Unit = notExercised("deleteMilestone")

    override suspend fun getHeartMoment(
        spaceId: UUID,
        accessToken: String,
        heartMomentId: UUID,
    ): HeartMomentDetail = notExercised("getHeartMoment")

    override suspend fun updateComment(
        spaceId: UUID,
        accessToken: String,
        commentId: UUID,
        ifMatch: Int,
        update: CommentUpdate,
    ): CommentDetail = notExercised("updateComment")

    override suspend fun deleteComment(
        spaceId: UUID,
        accessToken: String,
        commentId: UUID,
        ifMatch: Int,
    ): Unit = notExercised("deleteComment")

    override suspend fun listHeartMoments(
        spaceId: UUID,
        accessToken: String,
        visibility: ContentVisibility?,
    ): HeartMomentPage = notExercised("listHeartMoments")

    override suspend fun createHeartMoment(
        spaceId: UUID,
        accessToken: String,
        heartMoment: HeartMomentCreate,
    ): HeartMomentDetail = notExercised("createHeartMoment")

    override suspend fun updateHeartMoment(
        spaceId: UUID,
        accessToken: String,
        heartMomentId: UUID,
        ifMatch: Int,
        update: HeartMomentUpdate,
    ): HeartMomentDetail = notExercised("updateHeartMoment")

    override suspend fun changeHeartMomentVisibility(
        spaceId: UUID,
        accessToken: String,
        heartMomentId: UUID,
        ifMatch: Int,
        change: HeartMomentVisibilityChange,
    ): HeartMomentDetail = notExercised("changeHeartMomentVisibility")

    override suspend fun deleteHeartMoment(
        spaceId: UUID,
        accessToken: String,
        heartMomentId: UUID,
        ifMatch: Int,
    ): Unit = notExercised("deleteHeartMoment")

    override suspend fun createAttachmentUpload(
        spaceId: UUID,
        accessToken: String,
        request: AttachmentUploadCreate,
    ): UploadDescriptor = notExercised("createAttachmentUpload")

    override suspend fun uploadAttachmentBytes(
        accessToken: String,
        descriptor: UploadDescriptor,
        image: SelectedImage,
    ): Unit = notExercised("uploadAttachmentBytes")

    override suspend fun finalizeAttachment(
        spaceId: UUID,
        accessToken: String,
        attachmentId: UUID,
    ): AttachmentDetail = notExercised("finalizeAttachment")

    override suspend fun getAttachment(
        spaceId: UUID,
        accessToken: String,
        attachmentId: UUID,
    ): AttachmentDetail = notExercised("getAttachment")

    override suspend fun replaceMemoryAttachments(
        spaceId: UUID,
        accessToken: String,
        memoryId: UUID,
        ifMatch: Int,
        attachments: MemoryAttachmentSet,
    ): MemoryDetail = notExercised("replaceMemoryAttachments")

    override suspend fun listWishes(spaceId: UUID, accessToken: String): WishPage =
        notExercised("listWishes")

    override suspend fun createWish(
        spaceId: UUID,
        accessToken: String,
        wish: WishCreate,
    ): WishDetail = notExercised("createWish")

    override suspend fun updateWish(
        spaceId: UUID,
        accessToken: String,
        wishId: UUID,
        ifMatch: Int,
        update: WishUpdate,
    ): WishDetail = notExercised("updateWish")

    override suspend fun deleteWish(
        spaceId: UUID,
        accessToken: String,
        wishId: UUID,
        ifMatch: Int,
    ): Unit = notExercised("deleteWish")

    override suspend fun planWish(
        spaceId: UUID,
        accessToken: String,
        wishId: UUID,
        ifMatch: Int,
        conversion: WishToPlan,
    ): WishToPlanResponse = notExercised("planWish")

    override suspend fun listPlans(spaceId: UUID, accessToken: String): PlanPage =
        notExercised("listPlans")

    override suspend fun updatePlan(
        spaceId: UUID,
        accessToken: String,
        planId: UUID,
        ifMatch: Int,
        update: PlanUpdate,
    ): PlanDetail = notExercised("updatePlan")

    override suspend fun deletePlan(
        spaceId: UUID,
        accessToken: String,
        planId: UUID,
        ifMatch: Int,
    ): Unit = notExercised("deletePlan")

    override suspend fun schedulePlan(
        spaceId: UUID,
        accessToken: String,
        planId: UUID,
        ifMatch: Int,
        schedule: PlanSchedule,
    ): PlanDetail = notExercised("schedulePlan")

    override suspend fun unschedulePlan(
        spaceId: UUID,
        accessToken: String,
        planId: UUID,
        ifMatch: Int,
    ): PlanDetail = notExercised("unschedulePlan")

    override suspend fun completePlan(
        spaceId: UUID,
        accessToken: String,
        planId: UUID,
        ifMatch: Int,
        completion: PlanComplete,
    ): PlanDetail = notExercised("completePlan")

    override suspend fun returnPlanToWish(
        spaceId: UUID,
        accessToken: String,
        planId: UUID,
        ifMatch: Int,
    ): PlanReturnToWishResponse = notExercised("returnPlanToWish")

    override suspend fun getDashboard(spaceId: UUID, accessToken: String): DashboardView =
        notExercised("getDashboard")

    override suspend fun sendThinkingOfYou(
        spaceId: UUID,
        accessToken: String,
        gesture: ThinkingOfYouCreate,
    ): ThinkingOfYouAccepted = notExercised("sendThinkingOfYou")

    override suspend fun acceptInvitation(accessToken: String, token: String): MembershipView =
        notExercised("acceptInvitation")

    override suspend fun listInvitations(spaceId: UUID, accessToken: String): List<InvitationView> =
        notExercised("listInvitations")

    override suspend fun createInvitation(spaceId: UUID, accessToken: String): IssuedInvitationView =
        notExercised("createInvitation")

    override suspend fun revokeInvitation(
        spaceId: UUID,
        accessToken: String,
        invitationId: UUID,
    ): Unit = notExercised("revokeInvitation")

    override suspend fun listRelatedPersons(
        spaceId: UUID,
        accessToken: String,
    ): List<RelatedPersonView> = notExercised("listRelatedPersons")

    override suspend fun createRelatedPerson(
        spaceId: UUID,
        accessToken: String,
        fields: RelatedPersonFields,
    ): RelatedPersonView = notExercised("createRelatedPerson")

    override suspend fun updateRelatedPerson(
        spaceId: UUID,
        accessToken: String,
        personId: UUID,
        ifMatch: Int,
        fields: RelatedPersonFields,
    ): RelatedPersonView = notExercised("updateRelatedPerson")

    override suspend fun deleteRelatedPerson(
        spaceId: UUID,
        accessToken: String,
        personId: UUID,
        deletePolicy: RelatedPersonDeletePolicy,
        ifMatch: Int,
    ): Unit = notExercised("deleteRelatedPerson")

    override suspend fun listImportantDates(
        spaceId: UUID,
        accessToken: String,
        relatedPersonId: UUID?,
    ): List<ImportantDateView> = notExercised("listImportantDates")

    override suspend fun createImportantDate(
        spaceId: UUID,
        accessToken: String,
        fields: ImportantDateFields,
    ): ImportantDateView = notExercised("createImportantDate")

    override suspend fun updateImportantDate(
        spaceId: UUID,
        accessToken: String,
        dateId: UUID,
        ifMatch: Int,
        fields: ImportantDateFields,
    ): ImportantDateView = notExercised("updateImportantDate")

    override suspend fun deleteImportantDate(
        spaceId: UUID,
        accessToken: String,
        dateId: UUID,
        ifMatch: Int,
    ): Unit = notExercised("deleteImportantDate")

    override suspend fun getTimeline(
        spaceId: UUID,
        accessToken: String,
        cursor: String?,
    ): StoryPage = notExercised("getTimeline")

    override suspend fun createReadAccess(
        spaceId: UUID,
        accessToken: String,
        attachmentId: UUID,
        request: AttachmentReadRequest,
    ): ReadDescriptor = notExercised("createReadAccess")

    override suspend fun readImageBytes(
        accessToken: String,
        descriptor: ReadDescriptor,
    ): ByteArray = notExercised("readImageBytes")

    override suspend fun listProfilePreferences(
        spaceId: UUID,
        accessToken: String,
    ): List<ProfilePreferenceView> = notExercised("listProfilePreferences")

    override suspend fun createProfilePreference(
        spaceId: UUID,
        accessToken: String,
        fields: ProfilePreferenceCreate,
    ): ProfilePreferenceView = notExercised("createProfilePreference")

    override suspend fun updateProfilePreference(
        spaceId: UUID,
        accessToken: String,
        preferenceId: UUID,
        ifMatch: Int,
        fields: ProfilePreferenceUpdate,
    ): ProfilePreferenceView = notExercised("updateProfilePreference")

    override suspend fun deleteProfilePreference(
        spaceId: UUID,
        accessToken: String,
        preferenceId: UUID,
        ifMatch: Int,
    ): Unit = notExercised("deleteProfilePreference")

    override suspend fun listPlaces(
        spaceId: UUID,
        accessToken: String,
        cursor: String?,
    ): PlacePage = notExercised("listPlaces")

    override suspend fun createPlace(
        spaceId: UUID,
        accessToken: String,
        fields: PlaceCreate,
    ): PlaceDetail = notExercised("createPlace")

    override suspend fun updatePlace(
        spaceId: UUID,
        accessToken: String,
        placeId: UUID,
        ifMatch: Int,
        fields: PlaceUpdate,
    ): PlaceDetail = notExercised("updatePlace")

    override suspend fun deletePlace(
        spaceId: UUID,
        accessToken: String,
        placeId: UUID,
        ifMatch: Int,
    ): Unit = notExercised("deletePlace")

    override suspend fun listPlaceRelationTargets(
        spaceId: UUID,
        accessToken: String,
        placeId: UUID,
        kind: ReferenceContract.RelationTargetKind,
    ): List<UUID> = notExercised("listPlaceRelationTargets")

    override suspend fun linkPlaceTarget(
        spaceId: UUID,
        accessToken: String,
        placeId: UUID,
        kind: ReferenceContract.RelationTargetKind,
        targetId: UUID,
    ): Unit = notExercised("linkPlaceTarget")

    override suspend fun unlinkPlaceTarget(
        spaceId: UUID,
        accessToken: String,
        placeId: UUID,
        kind: ReferenceContract.RelationTargetKind,
        targetId: UUID,
    ): Unit = notExercised("unlinkPlaceTarget")

    override suspend fun listPrivateNotes(
        spaceId: UUID,
        accessToken: String,
        cursor: String?,
    ): PrivateNotePage = notExercised("listPrivateNotes")

    override suspend fun createPrivateNote(
        spaceId: UUID,
        accessToken: String,
        fields: PrivateNoteCreate,
    ): PrivateNoteDetail = notExercised("createPrivateNote")

    override suspend fun updatePrivateNote(
        spaceId: UUID,
        accessToken: String,
        noteId: UUID,
        ifMatch: Int,
        fields: PrivateNoteUpdate,
    ): PrivateNoteDetail = notExercised("updatePrivateNote")

    override suspend fun deletePrivateNote(
        spaceId: UUID,
        accessToken: String,
        noteId: UUID,
        ifMatch: Int,
    ): Unit = notExercised("deletePrivateNote")

    override suspend fun listGiftIdeas(
        spaceId: UUID,
        accessToken: String,
        cursor: String?,
    ): GiftIdeaPage = notExercised("listGiftIdeas")

    override suspend fun createGiftIdea(
        spaceId: UUID,
        accessToken: String,
        fields: GiftIdeaCreate,
    ): GiftIdeaDetail = notExercised("createGiftIdea")

    override suspend fun updateGiftIdea(
        spaceId: UUID,
        accessToken: String,
        giftIdeaId: UUID,
        ifMatch: Int,
        fields: GiftIdeaUpdate,
    ): GiftIdeaDetail = notExercised("updateGiftIdea")

    override suspend fun deleteGiftIdea(
        spaceId: UUID,
        accessToken: String,
        giftIdeaId: UUID,
        ifMatch: Int,
    ): Unit = notExercised("deleteGiftIdea")

    override suspend fun listPrivateCollections(
        spaceId: UUID,
        accessToken: String,
        cursor: String?,
    ): PrivateCollectionPage = notExercised("listPrivateCollections")

    override suspend fun createPrivateCollection(
        spaceId: UUID,
        accessToken: String,
        fields: PrivateCollectionCreate,
    ): PrivateCollectionDetail = notExercised("createPrivateCollection")

    override suspend fun updatePrivateCollection(
        spaceId: UUID,
        accessToken: String,
        collectionId: UUID,
        ifMatch: Int,
        fields: PrivateCollectionUpdate,
    ): PrivateCollectionDetail = notExercised("updatePrivateCollection")

    override suspend fun deletePrivateCollection(
        spaceId: UUID,
        accessToken: String,
        collectionId: UUID,
        ifMatch: Int,
    ): Unit = notExercised("deletePrivateCollection")

    override suspend fun createPrivateCollectionItem(
        spaceId: UUID,
        accessToken: String,
        collectionId: UUID,
        fields: PrivateCollectionItemCreate,
    ): PrivateCollectionItemDetail = notExercised("createPrivateCollectionItem")

    override suspend fun updatePrivateCollectionItem(
        spaceId: UUID,
        accessToken: String,
        collectionId: UUID,
        itemId: UUID,
        ifMatch: Int,
        fields: PrivateCollectionItemUpdate,
    ): PrivateCollectionItemDetail = notExercised("updatePrivateCollectionItem")

    override suspend fun deletePrivateCollectionItem(
        spaceId: UUID,
        accessToken: String,
        collectionId: UUID,
        itemId: UUID,
        ifMatch: Int,
    ): Unit = notExercised("deletePrivateCollectionItem")

    override suspend fun reorderPrivateCollectionItems(
        spaceId: UUID,
        accessToken: String,
        collectionId: UUID,
        ifMatch: Int,
        itemIds: List<UUID>,
    ): PrivateCollectionDetail = notExercised("reorderPrivateCollectionItems")

    override suspend fun listNotifications(
        spaceId: UUID,
        accessToken: String,
        cursor: String?,
    ): NotificationPage = notExercised("listNotifications")

    override suspend fun getNotificationUnreadCount(
        spaceId: UUID,
        accessToken: String,
    ): NotificationUnreadCount = notExercised("getNotificationUnreadCount")

    override suspend fun markNotificationRead(
        spaceId: UUID,
        accessToken: String,
        notificationId: UUID,
    ): NotificationItem = notExercised("markNotificationRead")

    override suspend fun markAllNotificationsRead(
        spaceId: UUID,
        accessToken: String,
    ): NotificationsReadAllResult = notExercised("markAllNotificationsRead")

    override suspend fun getActivity(
        spaceId: UUID,
        accessToken: String,
        cursor: String?,
    ): ActivityPage = notExercised("getActivity")

    override suspend fun search(
        spaceId: UUID,
        accessToken: String,
        query: String,
        cursor: String?,
    ): SearchPage = notExercised("search")

    override suspend fun listCollections(
        spaceId: UUID,
        accessToken: String,
        cursor: String?,
    ): CollectionPage = notExercised("listCollections")

    override suspend fun createCollection(
        spaceId: UUID,
        accessToken: String,
        fields: CollectionCreate,
    ): CollectionDetail = notExercised("createCollection")

    override suspend fun updateCollection(
        spaceId: UUID,
        accessToken: String,
        collectionId: UUID,
        ifMatch: Int,
        fields: CollectionUpdate,
    ): CollectionDetail = notExercised("updateCollection")

    override suspend fun deleteCollection(
        spaceId: UUID,
        accessToken: String,
        collectionId: UUID,
        ifMatch: Int,
    ): Unit = notExercised("deleteCollection")

    override suspend fun createCollectionItem(
        spaceId: UUID,
        accessToken: String,
        collectionId: UUID,
        fields: CollectionItemCreate,
    ): CollectionItemDetail = notExercised("createCollectionItem")

    override suspend fun updateCollectionItem(
        spaceId: UUID,
        accessToken: String,
        collectionId: UUID,
        itemId: UUID,
        ifMatch: Int,
        fields: CollectionItemUpdate,
    ): CollectionItemDetail = notExercised("updateCollectionItem")

    override suspend fun deleteCollectionItem(
        spaceId: UUID,
        accessToken: String,
        collectionId: UUID,
        itemId: UUID,
        ifMatch: Int,
    ): Unit = notExercised("deleteCollectionItem")

    override suspend fun reorderCollectionItems(
        spaceId: UUID,
        accessToken: String,
        collectionId: UUID,
        ifMatch: Int,
        itemIds: List<UUID>,
    ): CollectionDetail = notExercised("reorderCollectionItems")

    override suspend fun listChapters(
        spaceId: UUID,
        accessToken: String,
        cursor: String?,
    ): ChapterPage = notExercised("listChapters")

    override suspend fun createChapter(
        spaceId: UUID,
        accessToken: String,
        fields: ChapterCreate,
    ): ChapterDetail = notExercised("createChapter")

    override suspend fun updateChapter(
        spaceId: UUID,
        accessToken: String,
        chapterId: UUID,
        ifMatch: Int,
        fields: ChapterUpdate,
    ): ChapterDetail = notExercised("updateChapter")

    override suspend fun deleteChapter(
        spaceId: UUID,
        accessToken: String,
        chapterId: UUID,
        ifMatch: Int,
    ): Unit = notExercised("deleteChapter")

    override suspend fun getChapterContent(
        spaceId: UUID,
        accessToken: String,
        chapterId: UUID,
    ): ChapterContent = notExercised("getChapterContent")

    override suspend fun linkChapterTarget(
        spaceId: UUID,
        accessToken: String,
        chapterId: UUID,
        kind: ReferenceContract.RelationTargetKind,
        targetId: UUID,
    ): Unit = notExercised("linkChapterTarget")

    override suspend fun unlinkChapterTarget(
        spaceId: UUID,
        accessToken: String,
        chapterId: UUID,
        kind: ReferenceContract.RelationTargetKind,
        targetId: UUID,
    ): Unit = notExercised("unlinkChapterTarget")

    override suspend fun createTransferExport(
        spaceId: UUID,
        accessToken: String,
        scope: sidebyside.api.models.TransferScope,
    ): sidebyside.api.models.TransferExportDetail = notExercised("createTransferExport")

    override suspend fun getTransferExport(
        spaceId: UUID,
        accessToken: String,
        exportId: UUID,
    ): sidebyside.api.models.TransferExportDetail = notExercised("getTransferExport")

    override suspend fun downloadTransferExport(
        spaceId: UUID,
        accessToken: String,
        exportId: UUID,
        sink: java.io.OutputStream,
    ): Unit = notExercised("downloadTransferExport")

    override suspend fun createTransferImport(
        spaceId: UUID,
        accessToken: String,
        archiveSize: Long,
        archive: java.io.InputStream,
    ): sidebyside.api.models.TransferImportDetail = notExercised("createTransferImport")

    override suspend fun getTransferImport(
        spaceId: UUID,
        accessToken: String,
        importId: UUID,
    ): sidebyside.api.models.TransferImportDetail = notExercised("getTransferImport")

    override suspend fun applyTransferImport(
        spaceId: UUID,
        accessToken: String,
        importId: UUID,
    ): sidebyside.api.models.TransferImportDetail = notExercised("applyTransferImport")

    private fun notExercised(name: String): Nothing =
        error("$name is not exercised by this test.")
}
