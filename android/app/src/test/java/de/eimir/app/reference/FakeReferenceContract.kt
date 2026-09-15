package de.eimir.app.reference

import de.eimir.app.demo.DemoPersona
import java.util.UUID
import eimir.api.models.AccountDeletionAccepted
import eimir.api.models.AccountDeletionRequest
import eimir.api.models.AccountMembershipView
import eimir.api.models.AttachmentDetail
import eimir.api.models.AttachmentReadRequest
import eimir.api.models.ActivityPage
import eimir.api.models.AttachmentUploadCreate
import eimir.api.models.CommentCreate
import eimir.api.models.CommentDetail
import eimir.api.models.CommentPage
import eimir.api.models.CollectionCreate
import eimir.api.models.CollectionDetail
import eimir.api.models.CollectionItemCreate
import eimir.api.models.CollectionItemDetail
import eimir.api.models.CollectionItemUpdate
import eimir.api.models.CollectionPage
import eimir.api.models.ChapterCreate
import eimir.api.models.ChapterDetail
import eimir.api.models.ChapterPage
import eimir.api.models.ChapterContent
import eimir.api.models.ChapterUpdate
import eimir.api.models.CollectionUpdate
import eimir.api.models.CommentUpdate
import eimir.api.models.ContentVisibility
import eimir.api.models.HeartMomentCreate
import eimir.api.models.HeartMomentDetail
import eimir.api.models.HeartMomentPage
import eimir.api.models.HeartMomentUpdate
import eimir.api.models.HeartMomentVisibilityChange
import eimir.api.models.InstanceAccessStatus
import eimir.api.models.DashboardView
import eimir.api.models.AcceptRequest
import eimir.api.models.IssuedInvitationView
import eimir.api.models.InvitationView
import eimir.api.models.MembershipView
import eimir.api.models.ImportantDateFields
import eimir.api.models.ImportantDateView
import eimir.api.models.MemoryAttachmentSet
import eimir.api.models.PlaceCreate
import eimir.api.models.PlaceDetail
import eimir.api.models.PlacePage
import eimir.api.models.PlaceUpdate
import eimir.api.models.GiftIdeaCreate
import eimir.api.models.GiftIdeaDetail
import eimir.api.models.GiftIdeaPage
import eimir.api.models.GiftIdeaUpdate
import eimir.api.models.PrivateCollectionCreate
import eimir.api.models.PrivateCollectionDetail
import eimir.api.models.PrivateCollectionItemCreate
import eimir.api.models.PrivateCollectionItemDetail
import eimir.api.models.PrivateCollectionItemUpdate
import eimir.api.models.PrivateCollectionPage
import eimir.api.models.PrivateCollectionUpdate
import eimir.api.models.PrivateNoteCreate
import eimir.api.models.PrivateNoteDetail
import eimir.api.models.PrivateNotePage
import eimir.api.models.PrivateNoteUpdate
import eimir.api.models.ProfilePreferenceCreate
import eimir.api.models.ProfilePreferenceUpdate
import eimir.api.models.ProfilePreferenceView
import eimir.api.models.RelatedPersonDeletePolicy
import eimir.api.models.RelatedPersonFields
import eimir.api.models.RelatedPersonView
import eimir.api.models.SearchPage
import eimir.api.models.ThinkingOfYouAccepted
import eimir.api.models.ThinkingOfYouCreate
import eimir.api.models.MemoryCreate
import eimir.api.models.MemoryDetail
import eimir.api.models.MemoryUpdate
import eimir.api.models.MilestoneDetail
import eimir.api.models.MilestoneUpdate
import eimir.api.models.NotificationItem
import eimir.api.models.NotificationPage
import eimir.api.models.NotificationUnreadCount
import eimir.api.models.NotificationsReadAllResult
import eimir.api.models.PlanComplete
import eimir.api.models.PlanDetail
import eimir.api.models.PlanPage
import eimir.api.models.PlanReturnToWishResponse
import eimir.api.models.PlanSchedule
import eimir.api.models.PlanUpdate
import eimir.api.models.ReadDescriptor
import eimir.api.models.SessionView
import eimir.api.models.SpaceMembershipExitView
import eimir.api.models.StoryPage
import eimir.api.models.UploadDescriptor
import eimir.api.models.WishCreate
import eimir.api.models.WishDetail
import eimir.api.models.WishPage
import eimir.api.models.WishToPlan
import eimir.api.models.WishToPlanResponse
import eimir.api.models.WishUpdate

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

    override suspend fun leaveSpace(
        spaceId: UUID,
        accessToken: String,
    ): SpaceMembershipExitView = notExercised("leaveSpace")

    override suspend fun deleteOwnAccount(
        accessToken: String,
        request: AccountDeletionRequest,
    ): AccountDeletionAccepted = notExercised("deleteOwnAccount")

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
        fields: eimir.api.models.MilestoneCreate,
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

    override suspend fun createPlan(
        spaceId: UUID,
        accessToken: String,
        fields: eimir.api.models.PlanCreate,
    ): PlanDetail = notExercised("createPlan")

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
        kind: eimir.api.models.SearchKind?,
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
        scope: eimir.api.models.TransferScope,
    ): eimir.api.models.TransferExportDetail = notExercised("createTransferExport")

    override suspend fun getTransferExport(
        spaceId: UUID,
        accessToken: String,
        exportId: UUID,
    ): eimir.api.models.TransferExportDetail = notExercised("getTransferExport")

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
    ): eimir.api.models.TransferImportDetail = notExercised("createTransferImport")

    override suspend fun getTransferImport(
        spaceId: UUID,
        accessToken: String,
        importId: UUID,
    ): eimir.api.models.TransferImportDetail = notExercised("getTransferImport")

    override suspend fun applyTransferImport(
        spaceId: UUID,
        accessToken: String,
        importId: UUID,
    ): eimir.api.models.TransferImportDetail = notExercised("applyTransferImport")

    private fun notExercised(name: String): Nothing =
        error("$name is not exercised by this test.")
}
