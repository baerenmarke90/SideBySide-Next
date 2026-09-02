package de.sidebyside.next.reference

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import de.sidebyside.next.demo.DemoEndpoint
import de.sidebyside.next.demo.DemoPersona
import de.sidebyside.next.place.toRelationTargetItem
import de.sidebyside.next.profile.ProfileUiState
import de.sidebyside.next.profile.loadProfileIdentity
import de.sidebyside.next.profile.removeProfileAvatar
import de.sidebyside.next.profile.updateProfileAvatar
import de.sidebyside.next.profile.updateProfileDisplayName
import de.sidebyside.next.shell.UiProblem
import de.sidebyside.next.shell.UiStateKind
import de.sidebyside.next.shell.problemFor
import de.sidebyside.next.story.StoryImageRef
import de.sidebyside.next.story.StoryImageStore
import java.time.LocalDate
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.launch
import sidebyside.api.models.AccountMembershipView
import sidebyside.api.models.ActivityItem
import sidebyside.api.models.AttachmentReadRequest
import sidebyside.api.models.CommentCreate
import sidebyside.api.models.CommentDetail
import sidebyside.api.models.CollectionCreate
import sidebyside.api.models.CollectionDetail
import sidebyside.api.models.CollectionItemCreate
import sidebyside.api.models.CollectionItemDetail
import sidebyside.api.models.CollectionItemUpdate
import sidebyside.api.models.ChapterCreate
import sidebyside.api.models.ChapterDetail
import sidebyside.api.models.ChapterUpdate
import sidebyside.api.models.CollectionUpdate
import sidebyside.api.models.CommentUpdate
import sidebyside.api.models.ContentVisibility
import sidebyside.api.models.HeartEmotion
import sidebyside.api.models.HeartMomentCreate
import sidebyside.api.models.HeartMomentDetail
import sidebyside.api.models.HeartMomentUpdate
import sidebyside.api.models.HeartMomentVisibilityChange
import sidebyside.api.models.InstanceAccessStatus
import sidebyside.api.models.DashboardView
import sidebyside.api.models.DateRepeat
import sidebyside.api.models.ImportantDateFields
import sidebyside.api.models.ImportantDateType
import sidebyside.api.models.ImportantDateView
import sidebyside.api.models.MemoryDetail
import sidebyside.api.models.PersonRelationship
import sidebyside.api.models.PlaceCreate
import sidebyside.api.models.PlaceDetail
import sidebyside.api.models.PlaceUpdate
import sidebyside.api.models.GiftIdeaCreate
import sidebyside.api.models.GiftIdeaDetail
import sidebyside.api.models.GiftIdeaStatus
import sidebyside.api.models.GiftIdeaUpdate
import sidebyside.api.models.PrivateCollectionCreate
import sidebyside.api.models.PrivateCollectionDetail
import sidebyside.api.models.PrivateCollectionItemCreate
import sidebyside.api.models.PrivateCollectionItemDetail
import sidebyside.api.models.PrivateCollectionItemUpdate
import sidebyside.api.models.PrivateCollectionUpdate
import sidebyside.api.models.PrivateNoteCreate
import sidebyside.api.models.PrivateNoteDetail
import sidebyside.api.models.PrivateNoteUpdate
import sidebyside.api.models.PreferenceCategory
import sidebyside.api.models.PreferenceSentiment
import sidebyside.api.models.ProfilePreferenceCreate
import sidebyside.api.models.ProfilePreferenceUpdate
import sidebyside.api.models.ProfilePreferenceView
import sidebyside.api.models.ProfileVisibility
import sidebyside.api.models.RelatedPersonDeletePolicy
import sidebyside.api.models.RelatedPersonFields
import sidebyside.api.models.RelatedPersonView
import sidebyside.api.models.SearchResult
import sidebyside.api.models.ThinkingOfYouCreate
import sidebyside.api.models.MemoryUpdate
import sidebyside.api.models.MilestoneDetail
import sidebyside.api.models.MilestoneUpdate
import sidebyside.api.models.NotificationItem
import sidebyside.api.models.PlanComplete
import sidebyside.api.models.PlanDetail
import sidebyside.api.models.InvitationView
import sidebyside.api.models.IssuedInvitationView
import sidebyside.api.models.MembershipView
import sidebyside.api.models.PlanSchedule
import sidebyside.api.models.SessionView
import sidebyside.api.models.StoryItem
import sidebyside.api.models.WishCreate
import sidebyside.api.models.WishDetail
import sidebyside.api.models.WishStatus
import sidebyside.api.models.WishToPlan

data class UiMessage(
    val resourceId: Int,
    val args: List<Any> = emptyList(),
)

enum class DraftUploadState {
    UPLOADING,
    VALIDATING,
    READY,
    FAILED,
}

enum class InstanceAvailability {
    CHECKING,
    AVAILABLE,
    REGISTRATION_DISABLED,
    MAINTENANCE,
    UNREACHABLE,
}

internal fun instanceAvailabilityOf(status: InstanceAccessStatus): InstanceAvailability = when {
    status.maintenanceMode ||
        status.registrationUnavailableReason == InstanceAccessStatus.RegistrationUnavailableReason.maintenance ->
        InstanceAvailability.MAINTENANCE
    status.registrationAvailable -> InstanceAvailability.AVAILABLE
    status.registrationUnavailableReason == InstanceAccessStatus.RegistrationUnavailableReason.administrator ->
        InstanceAvailability.REGISTRATION_DISABLED
    else -> InstanceAvailability.UNREACHABLE
}

data class DraftImageUiItem(
    val id: Long,
    val displayName: String,
    val bytes: ByteArray,
    val uploadState: DraftUploadState,
)

data class ReferenceUiState(
    val configured: Boolean = false,
    val instanceAvailability: InstanceAvailability = InstanceAvailability.CHECKING,
    val loggedIn: Boolean = false,
    /**
     * Authenticated, but with no Space to open yet.
     *
     * Distinct from [loggedIn]: the session is real and held, only
     * `activeSpaceId` is absent. The one thing this state offers is entering
     * an invitation.
     */
    val awaitingSpace: Boolean = false,
    val invitationBusy: Boolean = false,
    val invitationProblem: UiProblem? = null,
    val issuedInvitations: List<InvitationView> = emptyList(),
    /** The token from a just-created invitation; shown once, per the contract. */
    val issuedInvitationToken: String? = null,
    /** True while the session belongs to the public demo rather than the configured server. */
    val demoMode: Boolean = false,
    val demoPersona: DemoPersona? = null,
    /** Every Space the account may open; a choice only exists above one. */
    val availableSpaces: List<AccountMembershipView> = emptyList(),
    /**
     * The other partner's name per Space, where it is known.
     *
     * A Space a couple is a member of is not the same as a Space whose name
     * has been resolved; this stays empty until [ReferenceViewModel] fetches
     * it, and a Space missing from it falls back to a position rather than
     * blocking the picker on a network round trip.
     */
    val spacePartnerNames: Map<java.util.UUID, String> = emptyMap(),
    val activeSpaceId: java.util.UUID? = null,
    val profile: ProfileUiState = ProfileUiState(),
    val busy: Boolean = false,
    val status: UiMessage? = null,
    val error: UiMessage? = null,
    val draftImages: List<DraftImageUiItem> = emptyList(),
    val lastMemoryTitle: String? = null,
    val lastMemoryBody: String? = null,
    val lastImageBytes: ByteArray? = null,
    val storyItems: List<StoryItem> = emptyList(),
    /** Whether the server says there is more Story past what is loaded. */
    val storyHasMore: Boolean = false,
    val storyLoadingMore: Boolean = false,
    val commentsHaveMore: Boolean = false,
    /** The memory currently open, if any. */
    val openMemory: MemoryDetail? = null,
    val memoryBusy: Boolean = false,
    /**
     * Whether the open memory is being changed.
     *
     * Owned here rather than by the screen because only this knows how a save
     * ended: success closes the form, a conflict deliberately leaves it open
     * with the text still in it.
     */
    val editingMemory: Boolean = false,
    /**
     * Confirmation belonging to the open memory alone.
     *
     * Separate from [status], which carries messages from signing in, entering
     * the demo and switching Space. Reusing it put the demo-entry notice on a
     * memory screen dressed as a save confirmation.
     */
    val memoryStatus: UiMessage? = null,
    /**
     * The account's own HeartMoments, private ones included.
     *
     * The server decides what is in here; asking for someone else's private
     * moments returns an empty page rather than a refusal, so nothing this
     * screen can render discloses that they exist.
     */
    val heartMoments: List<HeartMomentDetail> = emptyList(),
    val heartMomentsBusy: Boolean = false,
    val heartMomentsProblem: UiProblem? = null,
    val heartMomentStatus: UiMessage? = null,
    /**
     * The signed-in account.
     *
     * A comment carries no `capabilities`, unlike a Memory or a HeartMoment, so
     * this is the only signal for whose comment it is. It decides what is
     * offered, never what is allowed — the server still refuses what it should.
     */
    val accountId: java.util.UUID? = null,
    val comments: List<CommentDetail> = emptyList(),
    /**
     * Only the wishes nobody has acted on yet.
     *
     * A wish that became a plan is still there and still `PLANNED`, but showing
     * it beside its plan would list one intention twice.
     */
    val dashboard: DashboardView? = null,
    val todayBusy: Boolean = false,
    val todayProblem: UiProblem? = null,
    /** Set once the gesture has been accepted, so the screen can say so. */
    val thinkingOfYouSent: Boolean = false,
    val openWishes: List<WishDetail> = emptyList(),
    val plans: List<PlanDetail> = emptyList(),
    val planningBusy: Boolean = false,
    val planningProblem: UiProblem? = null,
    val relatedPersons: List<RelatedPersonView> = emptyList(),
    val relatedPersonsBusy: Boolean = false,
    val relatedPersonsProblem: UiProblem? = null,
    /** Dates for whichever person's screen is currently open. */
    val personImportantDates: List<ImportantDateView> = emptyList(),
    val places: List<PlaceDetail> = emptyList(),
    val placesBusy: Boolean = false,
    val placesProblem: UiProblem? = null,
    /** Every shared Story item, as a possible link target for whichever place's relations are open. */
    val placeRelationTargets: List<de.sidebyside.next.place.RelationTargetItem> = emptyList(),
    /** Ids already linked to that place, across all three kinds. */
    val placeLinkedTargetIds: Set<java.util.UUID> = emptySet(),
    val placeRelationsBusy: Boolean = false,
    val placeRelationsProblem: UiProblem? = null,
    /** Owner-only: the server already filters this to the caller's own notes. */
    val privateNotes: List<PrivateNoteDetail> = emptyList(),
    val privateNotesBusy: Boolean = false,
    val privateNotesProblem: UiProblem? = null,
    /** Owner-only: the server already filters this to the caller's own gift ideas. */
    val giftIdeas: List<GiftIdeaDetail> = emptyList(),
    val giftIdeasBusy: Boolean = false,
    val giftIdeasProblem: UiProblem? = null,
    /** Owner-only: items ride along inside each [PrivateCollectionDetail]. */
    val privateCollections: List<PrivateCollectionDetail> = emptyList(),
    val privateCollectionsBusy: Boolean = false,
    val privateCollectionsProblem: UiProblem? = null,
    val notifications: List<NotificationItem> = emptyList(),
    val unreadNotificationCount: Int = 0,
    val notificationsBusy: Boolean = false,
    val notificationsProblem: UiProblem? = null,
    val activity: List<ActivityItem> = emptyList(),
    val activityBusy: Boolean = false,
    val activityProblem: UiProblem? = null,
    val searchResults: List<SearchResult> = emptyList(),
    val searchBusy: Boolean = false,
    val searchProblem: UiProblem? = null,
    val collections: List<CollectionDetail> = emptyList(),
    val collectionsBusy: Boolean = false,
    val collectionsProblem: UiProblem? = null,
    val chapters: List<ChapterDetail> = emptyList(),
    val chaptersBusy: Boolean = false,
    val chaptersProblem: UiProblem? = null,
    /** The Story item currently open that is not a memory. */
    val openMilestone: MilestoneDetail? = null,
    val openSharedHeartMoment: HeartMomentDetail? = null,
    val commentsBusy: Boolean = false,
    val commentsProblem: UiProblem? = null,
    /** A problem belonging to the open memory rather than to the whole screen. */
    val memoryProblem: UiProblem? = null,
    /**
     * Set once the open memory no longer exists, so its screen can close
     * instead of showing a memory that was just deleted.
     */
    val openMemoryGone: Boolean = false,
)

private data class ImageDraft(
    val id: Long,
    val image: SelectedImage,
    val attemptId: Long,
    val uploadState: DraftUploadState,
    val preparedAttachment: PreparedAttachment? = null,
)

class ReferenceViewModel(
    private val config: ReferenceConfig = ReferenceConfig.fromBuildConfig(),
    api: ReferenceContract? = null,
    private val apiFactory: (String) -> ReferenceContract = ::OkHttpReferenceApi,
    private val spaceStore: SpacePreferenceStore = InMemorySpacePreferenceStore(),
) : ViewModel() {
    private val injectedApi: ReferenceContract? = api

    /**
     * The endpoint the current session talks to.
     *
     * Entering the demo points this at the demo deployment for the duration of
     * that session only; the configured production or Self-Hosted endpoint is
     * never rewritten, so leaving the demo returns to it unchanged.
     */
    private var contract: ReferenceContract? = apiFor(config.apiBaseUrl)

    /**
     * The Space the current session works in.
     *
     * Always resolved from the account's Memberships after authentication, for
     * a normal sign-in as much as for a demo persona. Nothing about a Space is
     * known before someone signs in.
     */
    private var activeSpaceId: java.util.UUID? = null
    private var session: SessionView? = null
    private var imageDrafts: List<ImageDraft> = emptyList()
    private var sessionEpoch: Long = 0
    private var nextDraftId: Long = 1

    /** Where the next page continues from; opaque and server-issued. */
    private var storyCursor: String? = null
    private var commentsCursor: String? = null

    /** Kept across a failed attempt so a retry is the same gesture, not a second one. */
    private var pendingGestureId: java.util.UUID? = null
    private var nextAttemptId: Long = 1

    private val _uiState = MutableStateFlow(ReferenceUiState(configured = config.isConfigured))
    val uiState: StateFlow<ReferenceUiState> = _uiState.asStateFlow()

    init {
        if (config.isConfigured) refreshInstanceAvailability()
    }

    fun refreshInstanceAvailability() {
        val api = contract ?: return
        if (!config.isConfigured) return
        mutate { it.copy(instanceAvailability = InstanceAvailability.CHECKING) }
        viewModelScope.launch {
            val availability = runCatching { api.getInstanceStatus() }
                .fold(
                    onSuccess = ::instanceAvailabilityOf,
                    onFailure = { InstanceAvailability.UNREACHABLE },
                )
            mutate { it.copy(instanceAvailability = availability) }
        }
    }

    /**
     * Story photographs, held in memory for the current Space only.
     *
     * It is given the session's own read path rather than an endpoint, so it
     * cannot outlive the session it was filled from: once [sessionEpoch] moves
     * on, both the cache and anything still in flight are void.
     */
    val storyImages: StoryImageStore = StoryImageStore(scope = viewModelScope) { ref ->
        readStoryImage(ref)
    }

    /**
     * Changes whenever the Space or the session does, so the screen re-asks
     * for every image instead of showing the previous couple's.
     */
    val storyGeneration: Long get() = sessionEpoch

    private suspend fun readStoryImage(ref: StoryImageRef): ByteArray {
        val api = checkNotNull(contract) { "A Story image is only read inside a session." }
        val currentSession = checkNotNull(session) { "A Story image needs a session." }
        val spaceId = checkNotNull(activeSpaceId) { "A Story image belongs to a Space." }
        val accessToken = currentSession.tokens.accessToken

        val descriptor = api.createReadAccess(
            spaceId,
            accessToken,
            ref.attachmentId,
            AttachmentReadRequest(parentId = ref.parentId, parentType = ref.parentType),
        )
        return api.readImageBytes(accessToken, descriptor)
    }

    fun signIn(email: String, password: String) {
        val api = contract ?: return configurationError()
        if (!config.isConfigured) return configurationError()
        if (email.isBlank() || password.isBlank()) {
            setError(message(R.string.ref_error_credentials_required))
            return
        }

        sessionEpoch += 1
        storyImages.reset()
        clearHeartMoments()
        clearComments()
        clearPlanning()
        clearToday()
        clearInvitations()
        clearRelatedPersons()
        clearProfilePreferences()
        clearPlaces()
        clearPlaceRelations()
        clearPrivateNotes()
        clearGiftIdeas()
        clearPrivateCollections()
        clearNotifications()
        clearActivity()
        clearSearch()
        clearCollections()
        clearChapters()
        closeStoryItem()
        val attemptEpoch = sessionEpoch
        viewModelScope.launch {
            if (attemptEpoch != sessionEpoch) return@launch
            mutate { it.copy(busy = true, error = null, status = message(R.string.ref_login_pending)) }
            runCatching {
                val signedIn = api.signIn(email.trim(), password)
                val memberships = api.listMemberships(signedIn.tokens.accessToken)
                signedIn to memberships
            }
                .onSuccess { (signedIn, memberships) ->
                    if (attemptEpoch != sessionEpoch) return@onSuccess
                    val space = activeSpaceOf(memberships, signedIn.account.id)
                    if (space == null) {
                        // Authenticated, with nothing to open yet — a product
                        // state, not a sign-in failure. The session is kept
                        // rather than discarded: entering an invitation needs
                        // this account's own token, and there is no other way
                        // to reach it.
                        session = signedIn
                        mutate {
                            it.copy(
                                loggedIn = false,
                                awaitingSpace = true,
                                accountId = signedIn.account.id,
                                busy = false,
                                error = null,
                                status = null,
                                spacePartnerNames = emptyMap(),
                            )
                        }
                        return@onSuccess
                    }
                    activeSpaceId = space
                    session = signedIn
                    imageDrafts = emptyList()
                    mutate {
                        it.copy(
                            loggedIn = true,
                            awaitingSpace = false,
                            accountId = signedIn.account.id,
                            busy = false,
                            status = message(R.string.ref_status_logged_in),
                            error = null,
                            spacePartnerNames = emptyMap(),
                            profile = ProfileUiState(),
                            draftImages = emptyList(),
                            lastMemoryTitle = null,
                            lastMemoryBody = null,
                            lastImageBytes = null,
                            storyItems = emptyList(),
                            availableSpaces = activeMemberships(memberships),
                            activeSpaceId = space,
                        )
                    }
                    refreshStory()
                }
                .onFailure {
                    if (attemptEpoch == sessionEpoch) {
                        failure(R.string.ref_error_login_failed)
                    }
                }
        }
    }

    /**
     * Enters the public demo as one of the canonical personas.
     *
     * The server issues a one-time proof rather than a password, so nothing
     * reusable is stored in the app. The Space comes from the account's
     * memberships, because a demo persona's Space cannot be configured at build
     * time.
     */
    fun enterDemo(persona: DemoPersona) {
        val demoApi = apiFor(DemoEndpoint.BASE_URL) ?: return configurationError()

        sessionEpoch += 1
        storyImages.reset()
        clearHeartMoments()
        clearComments()
        clearPlanning()
        clearToday()
        clearInvitations()
        clearRelatedPersons()
        clearProfilePreferences()
        clearPlaces()
        clearPlaceRelations()
        clearPrivateNotes()
        clearGiftIdeas()
        clearPrivateCollections()
        clearNotifications()
        clearActivity()
        clearSearch()
        clearCollections()
        clearChapters()
        closeStoryItem()
        val attemptEpoch = sessionEpoch
        viewModelScope.launch {
            if (attemptEpoch != sessionEpoch) return@launch
            mutate { it.copy(busy = true, error = null, status = message(R.string.demo_entering)) }
            runCatching {
                val token = demoApi.createDemoEntry(DemoEndpoint.BASE_URL, persona)
                val signedIn = demoApi.consumeMagicLink(token)
                val memberships = demoApi.listMemberships(signedIn.tokens.accessToken)
                val space = activeSpaceOf(memberships)
                    ?: throw IllegalStateException("The demo account has no active Space.")
                Triple(signedIn, space, demoApi)
            }
                .onSuccess { (signedIn, space, activeApi) ->
                    if (attemptEpoch != sessionEpoch) return@onSuccess
                    contract = activeApi
                    activeSpaceId = space
                    session = signedIn
                    imageDrafts = emptyList()
                    _uiState.value = ReferenceUiState(
                        configured = true,
                        loggedIn = true,
                        accountId = signedIn.account.id,
                        demoMode = true,
                        demoPersona = persona,
                        activeSpaceId = space,
                        status = message(R.string.demo_entered),
                    )
                    refreshStory()
                }
                .onFailure {
                    if (attemptEpoch == sessionEpoch) {
                        contract = apiFor(config.apiBaseUrl)
                        activeSpaceId = null
                        failure(R.string.demo_entry_failed)
                    }
                }
        }
    }

    /** Leaves the demo and returns to the configured server, carrying nothing over. */
    fun leaveDemo() {
        contract = apiFor(config.apiBaseUrl)
        activeSpaceId = null
        sessionEpoch += 1
        storyImages.reset()
        clearHeartMoments()
        clearComments()
        clearPlanning()
        clearToday()
        clearInvitations()
        clearRelatedPersons()
        clearProfilePreferences()
        clearPlaces()
        clearPlaceRelations()
        clearPrivateNotes()
        clearGiftIdeas()
        clearPrivateCollections()
        clearNotifications()
        clearActivity()
        clearSearch()
        clearCollections()
        clearChapters()
        closeStoryItem()
        session = null
        imageDrafts = emptyList()
        _uiState.value = ReferenceUiState(
            configured = config.isConfigured,
            status = message(R.string.demo_left),
        )
        refreshInstanceAvailability()
    }

    /**
     * The Space to open, as the server authorises it.
     *
     * Only an active membership counts; an invited or removed one must not
     * silently become the working context.
     */
    /**
     * The Space to resolve to, preferring [accountId]'s remembered choice.
     *
     * [accountId] defaults to null for demo entry, where a fresh persona
     * account has no launch history worth remembering and gets the same
     * first-active pick it always has.
     */
    private fun activeSpaceOf(
        memberships: List<AccountMembershipView>,
        accountId: java.util.UUID? = null,
    ): java.util.UUID? {
        val active = activeMemberships(memberships)
        val remembered = accountId?.let(spaceStore::rememberedSpace)
        return (active.firstOrNull { it.spaceId == remembered } ?: active.firstOrNull())?.spaceId
    }

    /**
     * Switches to another authorized Space.
     *
     * Everything bound to the previous Space is dropped rather than filtered:
     * a draft, a loaded Story or a pending upload belongs to the Space it was
     * made in. Bumping the session epoch also makes any request still in flight
     * against the old Space discard its result.
     */
    fun selectSpace(spaceId: java.util.UUID) {
        val state = _uiState.value
        if (spaceId == activeSpaceId) return
        if (state.availableSpaces.none { it.spaceId == spaceId }) return

        // Only an explicit choice is remembered — the automatic first-active
        // pick on sign-in must not become sticky before the account ever
        // chose anything.
        state.accountId?.let { spaceStore.rememberSpace(it, spaceId) }

        sessionEpoch += 1
        storyImages.reset()
        clearHeartMoments()
        clearComments()
        clearPlanning()
        clearToday()
        clearInvitations()
        clearRelatedPersons()
        clearProfilePreferences()
        clearPlaces()
        clearPlaceRelations()
        clearPrivateNotes()
        clearGiftIdeas()
        clearPrivateCollections()
        clearNotifications()
        clearActivity()
        clearSearch()
        clearCollections()
        clearChapters()
        closeStoryItem()
        activeSpaceId = spaceId
        imageDrafts = emptyList()
        mutate {
            it.copy(
                activeSpaceId = spaceId,
                profile = ProfileUiState(),
                busy = false,
                error = null,
                status = message(R.string.space_switched),
                draftImages = emptyList(),
                lastMemoryTitle = null,
                lastMemoryBody = null,
                lastImageBytes = null,
                storyItems = emptyList(),
            )
        }
        refreshStory()
    }

    private fun activeMemberships(
        memberships: List<AccountMembershipView>,
    ): List<AccountMembershipView> =
        memberships.filter { it.status.equals("ACTIVE", ignoreCase = true) }

    private fun apiFor(baseUrl: String): ReferenceContract? =
        injectedApi ?: baseUrl.takeIf(String::isNotBlank)?.let(apiFactory)

    fun beginImageSelection(): Long? = session?.let { sessionEpoch }

    fun selectImages(images: List<SelectedImage>, selectionEpoch: Long) {
        val api = contract ?: return configurationError()
        val currentSession = session ?: return
        val spaceId = activeSpaceId ?: return configurationError()
        if (selectionEpoch != sessionEpoch || images.isEmpty()) return

        val newDrafts = images.map { image ->
            ImageDraft(
                id = nextDraftId++,
                image = image,
                attemptId = nextAttemptId++,
                uploadState = DraftUploadState.UPLOADING,
            )
        }
        imageDrafts = imageDrafts + newDrafts
        publishDrafts()
        newDrafts.forEach { draft ->
            startAttachmentPreparation(api, spaceId, currentSession, draft)
        }
    }

    fun setImageSelectionError(throwable: Throwable, selectionEpoch: Long) {
        if (session == null || selectionEpoch != sessionEpoch) return
        val error = throwable.message?.takeIf(String::isNotBlank)?.let {
            message(R.string.ref_error_image_selection_detail, it)
        } ?: message(R.string.ref_error_image_selection_failed)
        mutate { it.copy(error = error, status = null) }
    }

    fun retryImage(draftId: Long) {
        val api = contract ?: return configurationError()
        val currentSession = session ?: return
        val spaceId = activeSpaceId ?: return configurationError()
        val index = imageDrafts.indexOfFirst { it.id == draftId }
        if (index < 0) return

        val draft = imageDrafts[index].copy(
            attemptId = nextAttemptId++,
            uploadState = DraftUploadState.UPLOADING,
            preparedAttachment = null,
        )
        imageDrafts = imageDrafts.toMutableList().also { it[index] = draft }
        publishDrafts()
        startAttachmentPreparation(api, spaceId, currentSession, draft)
    }

    fun removeImage(draftId: Long) {
        val previousSize = imageDrafts.size
        imageDrafts = imageDrafts.filterNot { it.id == draftId }
        if (imageDrafts.size == previousSize) return
        val nextStatus = draftStatus() ?: message(R.string.ref_status_image_removed)
        publishDrafts(status = nextStatus)
    }

    fun createMemory(title: String, body: String, happenedOnText: String) {
        val api = contract ?: return configurationError()
        val currentSession = session ?: run {
            setError(message(R.string.ref_error_login_required))
            return
        }
        val drafts = imageDrafts.toList()
        val spaceId = activeSpaceId ?: return configurationError()
        if (title.isBlank()) {
            setError(message(R.string.ref_error_memory_fields_required))
            return
        }
        if (drafts.any { it.uploadState != DraftUploadState.READY || it.preparedAttachment == null }) {
            setError(message(R.string.ref_error_images_not_ready))
            return
        }
        val happenedOn = if (happenedOnText.isBlank()) {
            null
        } else {
            runCatching { LocalDate.parse(happenedOnText.trim()) }.getOrElse {
                setError(message(R.string.ref_error_date_format))
                return
            }
        }
        val operationEpoch = sessionEpoch
        val attachments = drafts.map { checkNotNull(it.preparedAttachment) }

        viewModelScope.launch {
            if (!isCurrentSession(operationEpoch, currentSession)) return@launch
            mutate {
                it.copy(
                    busy = true,
                    error = null,
                    status = message(R.string.ref_status_save_pending),
                    lastMemoryTitle = null,
                    lastMemoryBody = null,
                    lastImageBytes = null,
                )
            }
            runCatching {
                createMemoryWithPreparedAttachments(
                    api = api,
                    spaceId = spaceId,
                    accessToken = currentSession.tokens.accessToken,
                    title = title.trim(),
                    body = body.trim(),
                    happenedOn = happenedOn,
                    attachments = attachments,
                )
            }.onSuccess { result ->
                if (!isCurrentSession(operationEpoch, currentSession)) return@onSuccess
                imageDrafts = emptyList()
                mutate {
                    it.copy(
                        busy = false,
                        status = message(R.string.ref_status_save_success),
                        error = null,
                        draftImages = emptyList(),
                        lastMemoryTitle = result.memory.title,
                        lastMemoryBody = result.memory.body,
                        lastImageBytes = result.imageBytes,
                        storyItems = result.story.items,
                    )
                }
            }.onFailure {
                if (isCurrentSession(operationEpoch, currentSession)) {
                    failure(R.string.ref_error_save_failed)
                }
            }
        }
    }

    /**
     * Loads one memory for its own screen.
     *
     * The Story carries a summary; the full text and every photograph come from
     * here, as does the version a change has to be written against.
     */
    fun openMemory(memoryId: java.util.UUID) {
        mutate { it.copy(memoryProblem = null, memoryStatus = null, openMemoryGone = false) }
        reloadMemory(memoryId)
    }

    /**
     * Reads the memory again without clearing what is already being reported.
     *
     * A conflict reloads to pick up the partner's version, and clearing the
     * problem on the way would make the explanation flash past: the write would
     * have been refused and the screen would look as though nothing happened.
     */
    private fun reloadMemory(memoryId: java.util.UUID) {
        val api = contract ?: return
        val currentSession = session ?: return
        val spaceId = activeSpaceId ?: return
        val operationEpoch = sessionEpoch

        mutate { it.copy(memoryBusy = true) }
        viewModelScope.launch {
            if (!isCurrentSession(operationEpoch, currentSession)) return@launch
            runCatching { api.getMemory(spaceId, currentSession.tokens.accessToken, memoryId) }
                .onSuccess { memory ->
                    if (!isCurrentSession(operationEpoch, currentSession)) return@onSuccess
                    mutate { it.copy(openMemory = memory, memoryBusy = false) }
                }
                .onFailure { throwable ->
                    if (!isCurrentSession(operationEpoch, currentSession)) return@onFailure
                    mutate {
                        it.copy(memoryBusy = false, memoryProblem = problemFor(throwable))
                    }
                }
        }
    }

    fun beginEditingMemory() {
        mutate { it.copy(editingMemory = true, memoryProblem = null, memoryStatus = null) }
    }

    fun cancelEditingMemory() {
        mutate { it.copy(editingMemory = false, memoryProblem = null) }
    }

    /** Forgets the open memory when its screen is left. */
    fun closeMemory() {
        mutate {
            it.copy(
                openMemory = null,
                memoryBusy = false,
                memoryProblem = null,
                openMemoryGone = false,
                editingMemory = false,
                memoryStatus = null,
            )
        }
    }

    /**
     * Writes a change to the open memory.
     *
     * The change is sent against the version it was written from. If the
     * partner changed the memory meanwhile the server refuses, and the refusal
     * is reported **without** touching what was typed — the newly written text
     * is the thing worth protecting here, not the request. The memory is then
     * reloaded so a second attempt carries the current version.
     */
    fun saveMemory(title: String, body: String, happenedOn: String) {
        val api = contract ?: return
        val currentSession = session ?: return
        val spaceId = activeSpaceId ?: return
        val memory = _uiState.value.openMemory ?: return
        val operationEpoch = sessionEpoch

        val happenedOnDate = parseHappenedOn(happenedOn)
        if (happenedOn.isNotBlank() && happenedOnDate == null) {
            mutate { it.copy(error = message(R.string.ref_error_date_format)) }
            return
        }

        mutate { it.copy(memoryBusy = true, memoryProblem = null) }
        viewModelScope.launch {
            if (!isCurrentSession(operationEpoch, currentSession)) return@launch
            runCatching {
                api.updateMemory(
                    spaceId,
                    currentSession.tokens.accessToken,
                    memory.id,
                    memory.version,
                    MemoryUpdate(
                        body = body,
                        happenedOn = happenedOnDate,
                        title = title,
                    ),
                )
            }
                .onSuccess { updated ->
                    if (!isCurrentSession(operationEpoch, currentSession)) return@onSuccess
                    mutate {
                        it.copy(
                            openMemory = updated,
                            memoryBusy = false,
                            memoryProblem = null,
                            // The change is written, so the form has done its
                            // job; leaving it open would look as if nothing had
                            // happened.
                            editingMemory = false,
                            memoryStatus = message(R.string.memory_saved),
                        )
                    }
                    refreshStory()
                }
                .onFailure { throwable ->
                    if (!isCurrentSession(operationEpoch, currentSession)) return@onFailure
                    mutate {
                        it.copy(memoryBusy = false, memoryProblem = problemFor(throwable))
                    }
                    // Reload so a retry carries the version the partner left
                    // behind. The typed text lives in the form and is untouched,
                    // and the refusal stays on screen.
                    reloadMemory(memory.id)
                }
        }
    }

    /** Removes the open memory, and the Story entry that showed it. */
    fun deleteMemory() {
        val api = contract ?: return
        val currentSession = session ?: return
        val spaceId = activeSpaceId ?: return
        val memory = _uiState.value.openMemory ?: return
        val operationEpoch = sessionEpoch

        mutate { it.copy(memoryBusy = true, memoryProblem = null) }
        viewModelScope.launch {
            if (!isCurrentSession(operationEpoch, currentSession)) return@launch
            runCatching {
                api.deleteMemory(
                    spaceId,
                    currentSession.tokens.accessToken,
                    memory.id,
                    memory.version,
                )
            }
                .onSuccess {
                    if (!isCurrentSession(operationEpoch, currentSession)) return@onSuccess
                    mutate {
                        it.copy(
                            openMemory = null,
                            memoryBusy = false,
                            openMemoryGone = true,
                            status = message(R.string.memory_deleted),
                        )
                    }
                    refreshStory()
                }
                .onFailure { throwable ->
                    if (!isCurrentSession(operationEpoch, currentSession)) return@onFailure
                    mutate {
                        it.copy(memoryBusy = false, memoryProblem = problemFor(throwable))
                    }
                }
        }
    }

    fun openMilestone(milestoneId: java.util.UUID) {
        mutate { it.copy(memoryProblem = null, memoryStatus = null, openMemoryGone = false) }
        reloadMilestone(milestoneId)
    }

    /**
     * Reads the milestone again without clearing what is already being
     * reported, for the same reason [reloadMemory] does: a conflict reloads to
     * pick up the partner's version, and clearing the problem on the way would
     * make the refusal look like nothing having happened.
     */
    private fun reloadMilestone(milestoneId: java.util.UUID) {
        val api = contract ?: return
        val currentSession = session ?: return
        val spaceId = activeSpaceId ?: return
        val operationEpoch = sessionEpoch

        mutate { it.copy(memoryBusy = true) }
        viewModelScope.launch {
            if (!isCurrentSession(operationEpoch, currentSession)) return@launch
            runCatching {
                api.getMilestone(spaceId, currentSession.tokens.accessToken, milestoneId)
            }
                .onSuccess { milestone ->
                    if (!isCurrentSession(operationEpoch, currentSession)) return@onSuccess
                    mutate { it.copy(openMilestone = milestone, memoryBusy = false) }
                }
                .onFailure { throwable ->
                    if (!isCurrentSession(operationEpoch, currentSession)) return@onFailure
                    mutate { it.copy(memoryBusy = false, memoryProblem = problemFor(throwable)) }
                }
        }
    }

    /**
     * Reads one HeartMoment for its own screen.
     *
     * Only a shared one is reachable this way, because only a shared one is in
     * the Story. A private moment is not filtered out here — the server never
     * puts it in the timeline the id came from.
     */
    fun openSharedHeartMoment(heartMomentId: java.util.UUID) {
        val api = contract ?: return
        val currentSession = session ?: return
        val spaceId = activeSpaceId ?: return
        val operationEpoch = sessionEpoch

        mutate { it.copy(memoryBusy = true, memoryProblem = null, openMemoryGone = false) }
        viewModelScope.launch {
            if (!isCurrentSession(operationEpoch, currentSession)) return@launch
            runCatching {
                api.getHeartMoment(spaceId, currentSession.tokens.accessToken, heartMomentId)
            }
                .onSuccess { moment ->
                    if (!isCurrentSession(operationEpoch, currentSession)) return@onSuccess
                    mutate { it.copy(openSharedHeartMoment = moment, memoryBusy = false) }
                }
                .onFailure { throwable ->
                    if (!isCurrentSession(operationEpoch, currentSession)) return@onFailure
                    mutate { it.copy(memoryBusy = false, memoryProblem = problemFor(throwable)) }
                }
        }
    }

    fun closeStoryItem() {
        mutate {
            it.copy(
                openMilestone = null,
                openSharedHeartMoment = null,
                memoryBusy = false,
                memoryProblem = null,
                memoryStatus = null,
                editingMemory = false,
            )
        }
    }

    fun saveMilestone(title: String, body: String, happenedOn: String) {
        val api = contract ?: return
        val currentSession = session ?: return
        val spaceId = activeSpaceId ?: return
        val milestone = _uiState.value.openMilestone ?: return
        val operationEpoch = sessionEpoch

        val day = parseHappenedOn(happenedOn)
        if (happenedOn.isNotBlank() && day == null) {
            mutate { it.copy(error = message(R.string.ref_error_date_format)) }
            return
        }

        mutate { it.copy(memoryBusy = true, memoryProblem = null) }
        viewModelScope.launch {
            if (!isCurrentSession(operationEpoch, currentSession)) return@launch
            runCatching {
                api.updateMilestone(
                    spaceId,
                    currentSession.tokens.accessToken,
                    milestone.id,
                    milestone.version,
                    MilestoneUpdate(body = body, happenedOn = day, title = title),
                )
            }
                .onSuccess { updated ->
                    if (!isCurrentSession(operationEpoch, currentSession)) return@onSuccess
                    mutate {
                        it.copy(
                            openMilestone = updated,
                            memoryBusy = false,
                            memoryProblem = null,
                            editingMemory = false,
                            memoryStatus = message(R.string.memory_saved),
                        )
                    }
                    refreshStory()
                }
                .onFailure { throwable ->
                    if (!isCurrentSession(operationEpoch, currentSession)) return@onFailure
                    mutate { it.copy(memoryBusy = false, memoryProblem = problemFor(throwable)) }
                    reloadMilestone(milestone.id)
                }
        }
    }

    fun deleteMilestone() {
        val api = contract ?: return
        val currentSession = session ?: return
        val spaceId = activeSpaceId ?: return
        val milestone = _uiState.value.openMilestone ?: return
        val operationEpoch = sessionEpoch

        mutate { it.copy(memoryBusy = true, memoryProblem = null) }
        viewModelScope.launch {
            if (!isCurrentSession(operationEpoch, currentSession)) return@launch
            runCatching {
                api.deleteMilestone(
                    spaceId,
                    currentSession.tokens.accessToken,
                    milestone.id,
                    milestone.version,
                )
            }
                .onSuccess {
                    if (!isCurrentSession(operationEpoch, currentSession)) return@onSuccess
                    mutate {
                        it.copy(
                            openMilestone = null,
                            memoryBusy = false,
                            openMemoryGone = true,
                            memoryStatus = message(R.string.memory_deleted),
                        )
                    }
                    refreshStory()
                }
                .onFailure { throwable ->
                    if (!isCurrentSession(operationEpoch, currentSession)) return@onFailure
                    mutate { it.copy(memoryBusy = false, memoryProblem = problemFor(throwable)) }
                }
        }
    }

    fun loadComments(parent: ReferenceContract.CommentParent, parentId: java.util.UUID) {
        val api = contract ?: return
        val currentSession = session ?: return
        val spaceId = activeSpaceId ?: return
        val operationEpoch = sessionEpoch

        mutate { it.copy(commentsBusy = true, commentsProblem = null) }
        viewModelScope.launch {
            if (!isCurrentSession(operationEpoch, currentSession)) return@launch
            runCatching {
                api.listComments(spaceId, currentSession.tokens.accessToken, parent, parentId)
            }
                .onSuccess { page ->
                    if (!isCurrentSession(operationEpoch, currentSession)) return@onSuccess
                    commentsCursor = page.nextCursor
                    mutate {
                        it.copy(
                            comments = page.items,
                            commentsHaveMore = page.hasMore,
                            commentsBusy = false,
                        )
                    }
                }
                .onFailure { throwable -> reportCommentFailure(operationEpoch, currentSession, throwable) }
        }
    }

    fun addComment(
        parent: ReferenceContract.CommentParent,
        parentId: java.util.UUID,
        body: String,
    ) {
        val api = contract ?: return
        val currentSession = session ?: return
        val spaceId = activeSpaceId ?: return
        if (body.isBlank()) return
        val operationEpoch = sessionEpoch

        mutate { it.copy(commentsBusy = true, commentsProblem = null) }
        viewModelScope.launch {
            if (!isCurrentSession(operationEpoch, currentSession)) return@launch
            runCatching {
                api.createComment(
                    spaceId,
                    currentSession.tokens.accessToken,
                    parent,
                    parentId,
                    CommentCreate(body = body),
                )
            }
                .onSuccess {
                    if (!isCurrentSession(operationEpoch, currentSession)) return@onSuccess
                    loadComments(parent, parentId)
                }
                .onFailure { throwable -> reportCommentFailure(operationEpoch, currentSession, throwable) }
        }
    }

    fun editComment(
        parent: ReferenceContract.CommentParent,
        parentId: java.util.UUID,
        commentId: java.util.UUID,
        body: String,
    ) {
        val api = contract ?: return
        val currentSession = session ?: return
        val spaceId = activeSpaceId ?: return
        val current = _uiState.value.comments.firstOrNull { it.id == commentId } ?: return
        if (body.isBlank()) return
        val operationEpoch = sessionEpoch

        mutate { it.copy(commentsBusy = true, commentsProblem = null) }
        viewModelScope.launch {
            if (!isCurrentSession(operationEpoch, currentSession)) return@launch
            runCatching {
                api.updateComment(
                    spaceId,
                    currentSession.tokens.accessToken,
                    commentId,
                    current.version,
                    CommentUpdate(body = body),
                )
            }
                .onSuccess {
                    if (!isCurrentSession(operationEpoch, currentSession)) return@onSuccess
                    loadComments(parent, parentId)
                }
                .onFailure { throwable -> reportCommentFailure(operationEpoch, currentSession, throwable) }
        }
    }

    fun removeComment(
        parent: ReferenceContract.CommentParent,
        parentId: java.util.UUID,
        commentId: java.util.UUID,
    ) {
        val api = contract ?: return
        val currentSession = session ?: return
        val spaceId = activeSpaceId ?: return
        val current = _uiState.value.comments.firstOrNull { it.id == commentId } ?: return
        val operationEpoch = sessionEpoch

        mutate { it.copy(commentsBusy = true, commentsProblem = null) }
        viewModelScope.launch {
            if (!isCurrentSession(operationEpoch, currentSession)) return@launch
            runCatching {
                api.deleteComment(
                    spaceId,
                    currentSession.tokens.accessToken,
                    commentId,
                    current.version,
                )
            }
                .onSuccess {
                    if (!isCurrentSession(operationEpoch, currentSession)) return@onSuccess
                    loadComments(parent, parentId)
                }
                .onFailure { throwable -> reportCommentFailure(operationEpoch, currentSession, throwable) }
        }
    }

    fun clearComments() {
        commentsCursor = null
        mutate {
            it.copy(
                comments = emptyList(),
                commentsBusy = false,
                commentsProblem = null,
                commentsHaveMore = false,
            )
        }
    }

    private fun reportCommentFailure(
        operationEpoch: Long,
        currentSession: SessionView,
        throwable: Throwable,
    ) {
        if (!isCurrentSession(operationEpoch, currentSession)) return
        mutate { it.copy(commentsBusy = false, commentsProblem = problemFor(throwable)) }
    }

    fun loadHeartMoments() {
        val api = contract ?: return
        val currentSession = session ?: return
        val spaceId = activeSpaceId ?: return
        val operationEpoch = sessionEpoch

        mutate { it.copy(heartMomentsBusy = true, heartMomentsProblem = null) }
        viewModelScope.launch {
            if (!isCurrentSession(operationEpoch, currentSession)) return@launch
            runCatching { api.listHeartMoments(spaceId, currentSession.tokens.accessToken) }
                .onSuccess { page ->
                    if (!isCurrentSession(operationEpoch, currentSession)) return@onSuccess
                    mutate { it.copy(heartMoments = page.items, heartMomentsBusy = false) }
                }
                .onFailure { throwable ->
                    if (!isCurrentSession(operationEpoch, currentSession)) return@onFailure
                    mutate {
                        it.copy(
                            heartMomentsBusy = false,
                            heartMomentsProblem = problemFor(throwable),
                        )
                    }
                }
        }
    }

    fun createHeartMoment(
        text: String,
        emotion: HeartEmotion,
        happenedOn: String,
        visibility: ContentVisibility,
    ) {
        val api = contract ?: return
        val currentSession = session ?: return
        val spaceId = activeSpaceId ?: return

        if (text.isBlank()) {
            mutate { it.copy(heartMomentStatus = null, heartMomentsProblem = null) }
            setError(message(R.string.heart_moment_error_text_required))
            return
        }
        val day = parseHappenedOn(happenedOn) ?: LocalDate.now()
        val operationEpoch = sessionEpoch

        mutate { it.copy(heartMomentsBusy = true, heartMomentsProblem = null) }
        viewModelScope.launch {
            if (!isCurrentSession(operationEpoch, currentSession)) return@launch
            runCatching {
                api.createHeartMoment(
                    spaceId,
                    currentSession.tokens.accessToken,
                    HeartMomentCreate(
                        emotion = emotion,
                        happenedOn = day,
                        text = text,
                        visibility = visibility,
                    ),
                )
            }
                .onSuccess {
                    if (!isCurrentSession(operationEpoch, currentSession)) return@onSuccess
                    mutate {
                        it.copy(
                            heartMomentsBusy = false,
                            heartMomentStatus = message(R.string.heart_moment_created),
                        )
                    }
                    loadHeartMoments()
                    // A shared moment belongs in the Story straight away; a
                    // private one will simply not be in what comes back.
                    refreshStory()
                }
                .onFailure { throwable -> reportHeartMomentFailure(operationEpoch, currentSession, throwable) }
        }
    }

    fun updateHeartMoment(heartMomentId: java.util.UUID, text: String, emotion: HeartEmotion) {
        val api = contract ?: return
        val currentSession = session ?: return
        val spaceId = activeSpaceId ?: return
        val current = _uiState.value.heartMoments.firstOrNull { it.id == heartMomentId } ?: return
        val operationEpoch = sessionEpoch

        mutate { it.copy(heartMomentsBusy = true, heartMomentsProblem = null) }
        viewModelScope.launch {
            if (!isCurrentSession(operationEpoch, currentSession)) return@launch
            runCatching {
                api.updateHeartMoment(
                    spaceId,
                    currentSession.tokens.accessToken,
                    heartMomentId,
                    current.version,
                    // Deliberately without visibility: the contract keeps that
                    // a separate operation because it destroys comments.
                    HeartMomentUpdate(emotion = emotion, text = text),
                )
            }
                .onSuccess {
                    if (!isCurrentSession(operationEpoch, currentSession)) return@onSuccess
                    mutate {
                        it.copy(
                            heartMomentsBusy = false,
                            heartMomentStatus = message(R.string.heart_moment_saved),
                        )
                    }
                    loadHeartMoments()
                    refreshStory()
                }
                .onFailure { throwable -> reportHeartMomentFailure(operationEpoch, currentSession, throwable) }
        }
    }

    /**
     * Changes who may see a HeartMoment.
     *
     * Separate from [updateHeartMoment] because the server makes it separate:
     * `SHARED -> PRIVATE` deletes the moment's comments and going back does not
     * bring them back. The screen names that before calling this.
     */
    fun changeHeartMomentVisibility(
        heartMomentId: java.util.UUID,
        visibility: ContentVisibility,
    ) {
        val api = contract ?: return
        val currentSession = session ?: return
        val spaceId = activeSpaceId ?: return
        val current = _uiState.value.heartMoments.firstOrNull { it.id == heartMomentId } ?: return
        val operationEpoch = sessionEpoch

        mutate { it.copy(heartMomentsBusy = true, heartMomentsProblem = null) }
        viewModelScope.launch {
            if (!isCurrentSession(operationEpoch, currentSession)) return@launch
            runCatching {
                api.changeHeartMomentVisibility(
                    spaceId,
                    currentSession.tokens.accessToken,
                    heartMomentId,
                    current.version,
                    HeartMomentVisibilityChange(visibility = visibility),
                )
            }
                .onSuccess {
                    if (!isCurrentSession(operationEpoch, currentSession)) return@onSuccess
                    mutate {
                        it.copy(
                            heartMomentsBusy = false,
                            heartMomentStatus = message(
                                if (visibility == ContentVisibility.PRIVATE) {
                                    R.string.heart_moment_now_private
                                } else {
                                    R.string.heart_moment_now_shared
                                },
                            ),
                        )
                    }
                    loadHeartMoments()
                    // The Story gains or loses the moment with this change.
                    refreshStory()
                }
                .onFailure { throwable -> reportHeartMomentFailure(operationEpoch, currentSession, throwable) }
        }
    }

    fun deleteHeartMoment(heartMomentId: java.util.UUID) {
        val api = contract ?: return
        val currentSession = session ?: return
        val spaceId = activeSpaceId ?: return
        val current = _uiState.value.heartMoments.firstOrNull { it.id == heartMomentId } ?: return
        val operationEpoch = sessionEpoch

        mutate { it.copy(heartMomentsBusy = true, heartMomentsProblem = null) }
        viewModelScope.launch {
            if (!isCurrentSession(operationEpoch, currentSession)) return@launch
            runCatching {
                api.deleteHeartMoment(
                    spaceId,
                    currentSession.tokens.accessToken,
                    heartMomentId,
                    current.version,
                )
            }
                .onSuccess {
                    if (!isCurrentSession(operationEpoch, currentSession)) return@onSuccess
                    mutate {
                        it.copy(
                            heartMomentsBusy = false,
                            heartMomentStatus = message(R.string.heart_moment_deleted),
                        )
                    }
                    loadHeartMoments()
                    refreshStory()
                }
                .onFailure { throwable -> reportHeartMomentFailure(operationEpoch, currentSession, throwable) }
        }
    }

    fun clearHeartMoments() {
        mutate {
            it.copy(
                heartMoments = emptyList(),
                heartMomentsBusy = false,
                heartMomentsProblem = null,
                heartMomentStatus = null,
            )
        }
    }

    private fun reportHeartMomentFailure(
        operationEpoch: Long,
        currentSession: SessionView,
        throwable: Throwable,
    ) {
        if (!isCurrentSession(operationEpoch, currentSession)) return
        mutate {
            it.copy(heartMomentsBusy = false, heartMomentsProblem = problemFor(throwable))
        }
    }

    /**
     * Appends the next Story page.
     *
     * Appends rather than replaces: a couple reading their history back must
     * not lose what they already scrolled past.
     */
    fun loadMoreStory() {
        val api = contract ?: return
        val currentSession = session ?: return
        val spaceId = activeSpaceId ?: return
        val cursor = storyCursor ?: return
        if (_uiState.value.storyLoadingMore) return
        val operationEpoch = sessionEpoch

        mutate { it.copy(storyLoadingMore = true) }
        viewModelScope.launch {
            if (!isCurrentSession(operationEpoch, currentSession)) return@launch
            runCatching {
                api.getTimeline(spaceId, currentSession.tokens.accessToken, cursor)
            }
                .onSuccess { page ->
                    if (!isCurrentSession(operationEpoch, currentSession)) return@onSuccess
                    storyCursor = page.nextCursor
                    mutate {
                        it.copy(
                            storyItems = it.storyItems + page.items,
                            storyHasMore = page.hasMore,
                            storyLoadingMore = false,
                        )
                    }
                }
                .onFailure {
                    if (isCurrentSession(operationEpoch, currentSession)) {
                        mutate { it.copy(storyLoadingMore = false) }
                        failure(R.string.ref_error_story_load_failed, clearBusy = false)
                    }
                }
        }
    }

    fun loadMoreComments(parent: ReferenceContract.CommentParent, parentId: java.util.UUID) {
        val api = contract ?: return
        val currentSession = session ?: return
        val spaceId = activeSpaceId ?: return
        val cursor = commentsCursor ?: return
        if (_uiState.value.commentsBusy) return
        val operationEpoch = sessionEpoch

        mutate { it.copy(commentsBusy = true) }
        viewModelScope.launch {
            if (!isCurrentSession(operationEpoch, currentSession)) return@launch
            runCatching {
                api.listComments(
                    spaceId,
                    currentSession.tokens.accessToken,
                    parent,
                    parentId,
                    cursor,
                )
            }
                .onSuccess { page ->
                    if (!isCurrentSession(operationEpoch, currentSession)) return@onSuccess
                    commentsCursor = page.nextCursor
                    mutate {
                        it.copy(
                            comments = it.comments + page.items,
                            commentsHaveMore = page.hasMore,
                            commentsBusy = false,
                        )
                    }
                }
                .onFailure { throwable -> reportCommentFailure(operationEpoch, currentSession, throwable) }
        }
    }

    fun loadToday() {
        val api = contract ?: return
        val currentSession = session ?: return
        val spaceId = activeSpaceId ?: return
        val operationEpoch = sessionEpoch

        mutate { it.copy(todayBusy = true, todayProblem = null) }
        viewModelScope.launch {
            if (!isCurrentSession(operationEpoch, currentSession)) return@launch
            runCatching { api.getDashboard(spaceId, currentSession.tokens.accessToken) }
                .onSuccess { view ->
                    if (!isCurrentSession(operationEpoch, currentSession)) return@onSuccess
                    mutate { it.copy(dashboard = view, todayBusy = false) }
                }
                .onFailure { throwable ->
                    if (!isCurrentSession(operationEpoch, currentSession)) return@onFailure
                    mutate { it.copy(todayBusy = false, todayProblem = problemFor(throwable)) }
                }
        }
    }

    /**
     * Sends the partner a sign, once.
     *
     * The request id is kept until the server accepts it, so a second tap after
     * a failure repeats the *same* gesture rather than sending a new one. That
     * is the whole point of an idempotency key: the tap a person repeats is the
     * tap that looked like it failed.
     */
    fun sendThinkingOfYou() {
        val api = contract ?: return
        val currentSession = session ?: return
        val spaceId = activeSpaceId ?: return
        if (_uiState.value.todayBusy) return
        val operationEpoch = sessionEpoch

        val requestId = pendingGestureId ?: java.util.UUID.randomUUID().also {
            pendingGestureId = it
        }

        mutate { it.copy(todayBusy = true, todayProblem = null, thinkingOfYouSent = false) }
        viewModelScope.launch {
            if (!isCurrentSession(operationEpoch, currentSession)) return@launch
            runCatching {
                api.sendThinkingOfYou(
                    spaceId,
                    currentSession.tokens.accessToken,
                    ThinkingOfYouCreate(clientRequestId = requestId),
                )
            }
                .onSuccess {
                    if (!isCurrentSession(operationEpoch, currentSession)) return@onSuccess
                    pendingGestureId = null
                    mutate { it.copy(todayBusy = false, thinkingOfYouSent = true) }
                }
                .onFailure { throwable ->
                    if (!isCurrentSession(operationEpoch, currentSession)) return@onFailure
                    // A 429 means it was already sent recently, which the
                    // problem mapping renders as its own state rather than as
                    // a failure. The id is kept either way.
                    mutate { it.copy(todayBusy = false, todayProblem = problemFor(throwable)) }
                }
        }
    }

    fun acknowledgeThinkingOfYou() {
        mutate { it.copy(thinkingOfYouSent = false) }
    }

    fun clearToday() {
        pendingGestureId = null
        mutate {
            it.copy(
                dashboard = null,
                todayBusy = false,
                todayProblem = null,
                thinkingOfYouSent = false,
            )
        }
    }

    /**
     * Accepts an invitation while `awaitingSpace`.
     *
     * Uses the session held from sign-in rather than asking for one again —
     * that session is the entire reason this state keeps it. Success re-lists
     * memberships and resolves a Space the same way sign-in itself does.
     */
    fun acceptInvitation(token: String) {
        val api = contract ?: return
        val currentSession = session ?: return
        if (!_uiState.value.awaitingSpace) return
        if (token.isBlank()) return
        val operationEpoch = sessionEpoch

        mutate { it.copy(invitationBusy = true, invitationProblem = null) }
        viewModelScope.launch {
            if (!isCurrentSession(operationEpoch, currentSession)) return@launch
            runCatching {
                api.acceptInvitation(currentSession.tokens.accessToken, token)
                api.listMemberships(currentSession.tokens.accessToken)
            }
                .onSuccess { memberships ->
                    if (!isCurrentSession(operationEpoch, currentSession)) return@onSuccess
                    val space = activeSpaceOf(memberships, currentSession.account.id)
                    if (space == null) {
                        // The server accepted the token but the membership is
                        // not active yet by this account's own rules; stay in
                        // the same waiting state rather than guessing.
                        mutate {
                            it.copy(
                                invitationBusy = false,
                                invitationProblem = problemFor(
                                    ReferenceApiException(null, "not active", 409),
                                ),
                            )
                        }
                        return@onSuccess
                    }
                    activeSpaceId = space
                    imageDrafts = emptyList()
                    mutate {
                        it.copy(
                            loggedIn = true,
                            awaitingSpace = false,
                            activeSpaceId = space,
                            invitationBusy = false,
                            invitationProblem = null,
                            status = message(R.string.invitation_accepted),
                        )
                    }
                    refreshStory()
                }
                .onFailure { throwable ->
                    if (!isCurrentSession(operationEpoch, currentSession)) return@onFailure
                    mutate {
                        it.copy(invitationBusy = false, invitationProblem = acceptInvitationProblem(throwable))
                    }
                }
        }
    }

    /**
     * The server deliberately answers every bad-token case — unknown, expired,
     * revoked, already used — the same way, so as not to disclose which tokens
     * exist. `ACCOUNT_ALREADY_MEMBER` is a different, safe-to-name case: the
     * account already knows it is a member, so saying so leaks nothing.
     */
    private fun acceptInvitationProblem(throwable: Throwable): UiProblem {
        val code = (throwable as? ReferenceApiException)?.code
        return when (code) {
            "ACCOUNT_ALREADY_MEMBER" -> UiProblem(
                kind = UiStateKind.Conflict,
                titleRes = R.string.invitation_already_member_title,
                bodyRes = R.string.invitation_already_member,
                retryable = false,
            )

            "INVITATION_INVALID", "CANNOT_ACCEPT_OWN_INVITATION" -> UiProblem(
                kind = UiStateKind.Conflict,
                titleRes = R.string.invitation_expired_title,
                bodyRes = R.string.invitation_expired,
                retryable = false,
            )

            else -> problemFor(throwable)
        }
    }

    fun loadInvitations() {
        val api = contract ?: return
        val currentSession = session ?: return
        val spaceId = activeSpaceId ?: return
        val operationEpoch = sessionEpoch

        mutate { it.copy(invitationBusy = true, invitationProblem = null) }
        viewModelScope.launch {
            if (!isCurrentSession(operationEpoch, currentSession)) return@launch
            runCatching { api.listInvitations(spaceId, currentSession.tokens.accessToken) }
                .onSuccess { invitations ->
                    if (!isCurrentSession(operationEpoch, currentSession)) return@onSuccess
                    mutate { it.copy(issuedInvitations = invitations, invitationBusy = false) }
                }
                .onFailure { throwable ->
                    if (!isCurrentSession(operationEpoch, currentSession)) return@onFailure
                    mutate { it.copy(invitationBusy = false, invitationProblem = problemFor(throwable)) }
                }
        }
    }

    /**
     * Issues a new invitation.
     *
     * The token is kept in state so the screen can offer it once; nothing
     * about it is written to storage or logged, and it is gone from state as
     * soon as [dismissIssuedInvitationToken] is called.
     */
    fun createInvitation() {
        val api = contract ?: return
        val currentSession = session ?: return
        val spaceId = activeSpaceId ?: return
        val operationEpoch = sessionEpoch

        mutate { it.copy(invitationBusy = true, invitationProblem = null) }
        viewModelScope.launch {
            if (!isCurrentSession(operationEpoch, currentSession)) return@launch
            runCatching { api.createInvitation(spaceId, currentSession.tokens.accessToken) }
                .onSuccess { issued ->
                    if (!isCurrentSession(operationEpoch, currentSession)) return@onSuccess
                    mutate {
                        it.copy(invitationBusy = false, issuedInvitationToken = issued.token)
                    }
                    loadInvitations()
                }
                .onFailure { throwable ->
                    if (!isCurrentSession(operationEpoch, currentSession)) return@onFailure
                    // The server refuses a third partner rather than issuing an
                    // invitation nobody could ever accept — a specific, named
                    // state, not a version conflict a retry would fix.
                    val problem = if ((throwable as? ReferenceApiException)?.code == "SPACE_FULL") {
                        UiProblem(
                            kind = UiStateKind.Conflict,
                            titleRes = R.string.invitation_space_full_title,
                            bodyRes = R.string.invitation_space_full,
                            retryable = false,
                        )
                    } else {
                        problemFor(throwable)
                    }
                    mutate { it.copy(invitationBusy = false, invitationProblem = problem) }
                }
        }
    }

    fun dismissIssuedInvitationToken() {
        mutate { it.copy(issuedInvitationToken = null) }
    }

    fun revokeInvitation(invitationId: java.util.UUID) {
        val api = contract ?: return
        val currentSession = session ?: return
        val spaceId = activeSpaceId ?: return
        val operationEpoch = sessionEpoch

        mutate { it.copy(invitationBusy = true, invitationProblem = null) }
        viewModelScope.launch {
            if (!isCurrentSession(operationEpoch, currentSession)) return@launch
            runCatching {
                api.revokeInvitation(spaceId, currentSession.tokens.accessToken, invitationId)
            }
                .onSuccess {
                    if (!isCurrentSession(operationEpoch, currentSession)) return@onSuccess
                    mutate { it.copy(invitationBusy = false) }
                    loadInvitations()
                }
                .onFailure { throwable ->
                    if (!isCurrentSession(operationEpoch, currentSession)) return@onFailure
                    mutate { it.copy(invitationBusy = false, invitationProblem = problemFor(throwable)) }
                }
        }
    }

    fun loadRelatedPersons() {
        val api = contract ?: return
        val currentSession = session ?: return
        val spaceId = activeSpaceId ?: return
        val operationEpoch = sessionEpoch

        mutate { it.copy(relatedPersonsBusy = true, relatedPersonsProblem = null) }
        viewModelScope.launch {
            if (!isCurrentSession(operationEpoch, currentSession)) return@launch
            runCatching { api.listRelatedPersons(spaceId, currentSession.tokens.accessToken) }
                .onSuccess { people ->
                    if (!isCurrentSession(operationEpoch, currentSession)) return@onSuccess
                    mutate { it.copy(relatedPersons = people, relatedPersonsBusy = false) }
                }
                .onFailure { throwable ->
                    if (!isCurrentSession(operationEpoch, currentSession)) return@onFailure
                    mutate {
                        it.copy(relatedPersonsBusy = false, relatedPersonsProblem = problemFor(throwable))
                    }
                }
        }
    }

    fun addRelatedPerson(
        displayName: String,
        relationship: PersonRelationship,
        birthday: LocalDate?,
        birthdayYearKnown: Boolean,
        visibility: ContentVisibility,
    ) {
        if (displayName.isBlank()) return
        val api = contract ?: return
        val currentSession = session ?: return
        val spaceId = activeSpaceId ?: return
        val operationEpoch = sessionEpoch

        mutate { it.copy(relatedPersonsBusy = true, relatedPersonsProblem = null) }
        viewModelScope.launch {
            if (!isCurrentSession(operationEpoch, currentSession)) return@launch
            runCatching {
                api.createRelatedPerson(
                    spaceId,
                    currentSession.tokens.accessToken,
                    RelatedPersonFields(
                        birthday = birthday,
                        birthdayYearKnown = birthdayYearKnown,
                        displayName = displayName,
                        relationship = relationship,
                        visibility = visibility,
                    ),
                )
            }
                .onSuccess {
                    if (!isCurrentSession(operationEpoch, currentSession)) return@onSuccess
                    mutate { it.copy(relatedPersonsBusy = false) }
                    loadRelatedPersons()
                }
                .onFailure { throwable ->
                    if (!isCurrentSession(operationEpoch, currentSession)) return@onFailure
                    mutate {
                        it.copy(relatedPersonsBusy = false, relatedPersonsProblem = problemFor(throwable))
                    }
                }
        }
    }

    fun updateRelatedPerson(
        personId: java.util.UUID,
        displayName: String,
        relationship: PersonRelationship,
        birthday: LocalDate?,
        birthdayYearKnown: Boolean,
        visibility: ContentVisibility,
    ) {
        if (displayName.isBlank()) return
        val api = contract ?: return
        val currentSession = session ?: return
        val spaceId = activeSpaceId ?: return
        val person = _uiState.value.relatedPersons.firstOrNull { it.id == personId } ?: return
        val operationEpoch = sessionEpoch

        mutate { it.copy(relatedPersonsBusy = true, relatedPersonsProblem = null) }
        viewModelScope.launch {
            if (!isCurrentSession(operationEpoch, currentSession)) return@launch
            runCatching {
                api.updateRelatedPerson(
                    spaceId,
                    currentSession.tokens.accessToken,
                    personId,
                    person.version,
                    RelatedPersonFields(
                        birthday = birthday,
                        birthdayYearKnown = birthdayYearKnown,
                        displayName = displayName,
                        relationship = relationship,
                        visibility = visibility,
                    ),
                )
            }
                .onSuccess {
                    if (!isCurrentSession(operationEpoch, currentSession)) return@onSuccess
                    mutate { it.copy(relatedPersonsBusy = false) }
                    loadRelatedPersons()
                }
                .onFailure { throwable ->
                    if (!isCurrentSession(operationEpoch, currentSession)) return@onFailure
                    mutate {
                        it.copy(relatedPersonsBusy = false, relatedPersonsProblem = problemFor(throwable))
                    }
                }
        }
    }

    /**
     * Resolves the other partner's name for every Space this account may
     * open, so the picker can show who a Space is with instead of its
     * position in a list.
     *
     * Best-effort: a Space that fails to resolve simply falls back to its
     * position, rather than the whole picker failing over one request.
     */
    fun loadSpaceNames() {
        val api = contract ?: return
        val currentSession = session ?: return
        val spaces = _uiState.value.availableSpaces
        if (spaces.size <= 1) return
        val operationEpoch = sessionEpoch
        val selfId = _uiState.value.accountId

        viewModelScope.launch {
            spaces.forEach { membership ->
                if (!isCurrentSession(operationEpoch, currentSession)) return@launch
                if (_uiState.value.spacePartnerNames.containsKey(membership.spaceId)) return@forEach
                runCatching {
                    api.getSpace(membership.spaceId, currentSession.tokens.accessToken)
                }.onSuccess { space ->
                    if (!isCurrentSession(operationEpoch, currentSession)) return@launch
                    val partner = space.partners.firstOrNull { it.id != selfId }
                        ?: space.partners.firstOrNull()
                    partner?.let { view ->
                        mutate {
                            it.copy(
                                spacePartnerNames = it.spacePartnerNames +
                                    (membership.spaceId to view.displayName),
                            )
                        }
                    }
                }
            }
        }
    }

    fun clearInvitations() {
        mutate {
            it.copy(
                invitationBusy = false,
                invitationProblem = null,
                issuedInvitations = emptyList(),
                issuedInvitationToken = null,
            )
        }
    }

    /**
     * Deletes a person under an explicit, already-decided policy.
     *
     * Deliberately does not read [personImportantDates] or call
     * [loadImportantDates] first: per #65, the confirmation that led here must
     * never be built from a query of what is affected, because even a correct,
     * already-filtered count would disclose the gap between what this account
     * can see and what `cascade` actually removes.
     */
    fun deleteRelatedPerson(personId: java.util.UUID, deletePolicy: RelatedPersonDeletePolicy) {
        val api = contract ?: return
        val currentSession = session ?: return
        val spaceId = activeSpaceId ?: return
        val person = _uiState.value.relatedPersons.firstOrNull { it.id == personId } ?: return
        val operationEpoch = sessionEpoch

        mutate { it.copy(relatedPersonsBusy = true, relatedPersonsProblem = null) }
        viewModelScope.launch {
            if (!isCurrentSession(operationEpoch, currentSession)) return@launch
            runCatching {
                api.deleteRelatedPerson(
                    spaceId,
                    currentSession.tokens.accessToken,
                    personId,
                    deletePolicy,
                    person.version,
                )
            }
                .onSuccess {
                    if (!isCurrentSession(operationEpoch, currentSession)) return@onSuccess
                    mutate {
                        it.copy(
                            relatedPersonsBusy = false,
                            personImportantDates = emptyList(),
                        )
                    }
                    loadRelatedPersons()
                }
                .onFailure { throwable ->
                    if (!isCurrentSession(operationEpoch, currentSession)) return@onFailure
                    mutate {
                        it.copy(relatedPersonsBusy = false, relatedPersonsProblem = problemFor(throwable))
                    }
                }
        }
    }

    fun clearRelatedPersons() {
        mutate {
            it.copy(
                relatedPersons = emptyList(),
                relatedPersonsBusy = false,
                relatedPersonsProblem = null,
                personImportantDates = emptyList(),
            )
        }
    }

    /**
     * Reads a person's ImportantDates for their own screen.
     *
     * Only called from that screen, never from the delete confirmation — see
     * [deleteRelatedPerson].
     */
    fun loadImportantDates(relatedPersonId: java.util.UUID) {
        val api = contract ?: return
        val currentSession = session ?: return
        val spaceId = activeSpaceId ?: return
        val operationEpoch = sessionEpoch

        mutate { it.copy(relatedPersonsBusy = true, relatedPersonsProblem = null) }
        viewModelScope.launch {
            if (!isCurrentSession(operationEpoch, currentSession)) return@launch
            runCatching {
                api.listImportantDates(spaceId, currentSession.tokens.accessToken, relatedPersonId)
            }
                .onSuccess { dates ->
                    if (!isCurrentSession(operationEpoch, currentSession)) return@onSuccess
                    mutate { it.copy(personImportantDates = dates, relatedPersonsBusy = false) }
                }
                .onFailure { throwable ->
                    if (!isCurrentSession(operationEpoch, currentSession)) return@onFailure
                    mutate {
                        it.copy(relatedPersonsBusy = false, relatedPersonsProblem = problemFor(throwable))
                    }
                }
        }
    }

    fun addImportantDate(
        relatedPersonId: java.util.UUID,
        label: String,
        type: ImportantDateType,
        date: LocalDate,
        repeats: DateRepeat,
        visibility: ContentVisibility,
    ) {
        if (label.isBlank()) return
        val api = contract ?: return
        val currentSession = session ?: return
        val spaceId = activeSpaceId ?: return
        val operationEpoch = sessionEpoch

        mutate { it.copy(relatedPersonsBusy = true, relatedPersonsProblem = null) }
        viewModelScope.launch {
            if (!isCurrentSession(operationEpoch, currentSession)) return@launch
            runCatching {
                api.createImportantDate(
                    spaceId,
                    currentSession.tokens.accessToken,
                    ImportantDateFields(
                        date = date,
                        label = label,
                        relatedPersonId = relatedPersonId,
                        repeats = repeats,
                        type = type,
                        visibility = visibility,
                    ),
                )
            }
                .onSuccess {
                    if (!isCurrentSession(operationEpoch, currentSession)) return@onSuccess
                    mutate { it.copy(relatedPersonsBusy = false) }
                    loadImportantDates(relatedPersonId)
                }
                .onFailure { throwable ->
                    if (!isCurrentSession(operationEpoch, currentSession)) return@onFailure
                    mutate {
                        it.copy(relatedPersonsBusy = false, relatedPersonsProblem = problemFor(throwable))
                    }
                }
        }
    }

    fun deleteImportantDate(relatedPersonId: java.util.UUID, dateId: java.util.UUID) {
        val api = contract ?: return
        val currentSession = session ?: return
        val spaceId = activeSpaceId ?: return
        val date = _uiState.value.personImportantDates.firstOrNull { it.id == dateId } ?: return
        val operationEpoch = sessionEpoch

        mutate { it.copy(relatedPersonsBusy = true, relatedPersonsProblem = null) }
        viewModelScope.launch {
            if (!isCurrentSession(operationEpoch, currentSession)) return@launch
            runCatching {
                api.deleteImportantDate(spaceId, currentSession.tokens.accessToken, dateId, date.version)
            }
                .onSuccess {
                    if (!isCurrentSession(operationEpoch, currentSession)) return@onSuccess
                    mutate { it.copy(relatedPersonsBusy = false) }
                    loadImportantDates(relatedPersonId)
                }
                .onFailure { throwable ->
                    if (!isCurrentSession(operationEpoch, currentSession)) return@onFailure
                    mutate {
                        it.copy(relatedPersonsBusy = false, relatedPersonsProblem = problemFor(throwable))
                    }
                }
        }
    }

    fun loadPlanning() {
        val api = contract ?: return
        val currentSession = session ?: return
        val spaceId = activeSpaceId ?: return
        val operationEpoch = sessionEpoch

        mutate { it.copy(planningBusy = true, planningProblem = null) }
        viewModelScope.launch {
            if (!isCurrentSession(operationEpoch, currentSession)) return@launch
            runCatching {
                val token = currentSession.tokens.accessToken
                api.listWishes(spaceId, token).items to api.listPlans(spaceId, token).items
            }
                .onSuccess { (wishes, plans) ->
                    if (!isCurrentSession(operationEpoch, currentSession)) return@onSuccess
                    mutate {
                        it.copy(
                            openWishes = wishes.filter { wish ->
                                wish.status == WishStatus.OPEN
                            },
                            plans = plans,
                            planningBusy = false,
                        )
                    }
                }
                .onFailure { throwable -> reportPlanningFailure(operationEpoch, currentSession, throwable) }
        }
    }

    fun addWish(title: String) {
        if (title.isBlank()) return
        planningCall { api, spaceId, token -> api.createWish(spaceId, token, WishCreate(title = title)) }
    }

    fun removeWish(wishId: java.util.UUID) {
        val wish = _uiState.value.openWishes.firstOrNull { it.id == wishId } ?: return
        planningCall { api, spaceId, token -> api.deleteWish(spaceId, token, wishId, wish.version) }
    }

    /** Turns a wish into a plan; both survive, the wish as `PLANNED`. */
    fun planWish(wishId: java.util.UUID, title: String, description: String) {
        val wish = _uiState.value.openWishes.firstOrNull { it.id == wishId } ?: return
        planningCall { api, spaceId, token ->
            api.planWish(
                spaceId,
                token,
                wishId,
                wish.version,
                WishToPlan(
                    description = description.takeIf { it.isNotBlank() },
                    title = title.ifBlank { wish.title },
                ),
            )
        }
    }

    fun schedulePlan(planId: java.util.UUID, start: java.time.OffsetDateTime) {
        val plan = _uiState.value.plans.firstOrNull { it.id == planId } ?: return
        planningCall { api, spaceId, token ->
            api.schedulePlan(spaceId, token, planId, plan.version, PlanSchedule(plannedStart = start))
        }
    }

    fun unschedulePlan(planId: java.util.UUID) {
        val plan = _uiState.value.plans.firstOrNull { it.id == planId } ?: return
        planningCall { api, spaceId, token ->
            api.unschedulePlan(spaceId, token, planId, plan.version)
        }
    }

    fun completePlan(planId: java.util.UUID, experiencedOn: LocalDate) {
        val plan = _uiState.value.plans.firstOrNull { it.id == planId } ?: return
        planningCall { api, spaceId, token ->
            api.completePlan(
                spaceId,
                token,
                planId,
                plan.version,
                PlanComplete(experiencedOn = experiencedOn),
            )
        }
    }

    /**
     * Sends a plan back to being a wish.
     *
     * Destructive: the wish receives nothing back from the plan, so its
     * description is gone. The screen says so before calling this.
     */
    fun returnPlanToWish(planId: java.util.UUID) {
        val plan = _uiState.value.plans.firstOrNull { it.id == planId } ?: return
        planningCall { api, spaceId, token ->
            api.returnPlanToWish(spaceId, token, planId, plan.version)
        }
    }

    fun deletePlan(planId: java.util.UUID) {
        val plan = _uiState.value.plans.firstOrNull { it.id == planId } ?: return
        planningCall { api, spaceId, token -> api.deletePlan(spaceId, token, planId, plan.version) }
    }

    fun clearPlanning() {
        mutate {
            it.copy(
                openWishes = emptyList(),
                plans = emptyList(),
                planningBusy = false,
                planningProblem = null,
            )
        }
    }

    /**
     * Every planning write has the same shape: do it, then re-read both lists.
     *
     * Re-reading rather than patching locally, because one transition moves two
     * resources — planning a wish changes the wish as well as creating the plan
     * — and a client that guessed at that would drift from the server.
     */
    private fun planningCall(
        block: suspend (ReferenceContract, java.util.UUID, String) -> Unit,
    ) {
        val api = contract ?: return
        val currentSession = session ?: return
        val spaceId = activeSpaceId ?: return
        val operationEpoch = sessionEpoch

        mutate { it.copy(planningBusy = true, planningProblem = null) }
        viewModelScope.launch {
            if (!isCurrentSession(operationEpoch, currentSession)) return@launch
            runCatching { block(api, spaceId, currentSession.tokens.accessToken) }
                .onSuccess {
                    if (!isCurrentSession(operationEpoch, currentSession)) return@onSuccess
                    loadPlanning()
                }
                .onFailure { throwable -> reportPlanningFailure(operationEpoch, currentSession, throwable) }
        }
    }

    private fun reportPlanningFailure(
        operationEpoch: Long,
        currentSession: SessionView,
        throwable: Throwable,
    ) {
        if (!isCurrentSession(operationEpoch, currentSession)) return
        mutate { it.copy(planningBusy = false, planningProblem = problemFor(throwable)) }
    }

    fun refreshStory() {
        val api = contract ?: return
        val currentSession = session ?: return
        val spaceId = activeSpaceId ?: return
        val operationEpoch = sessionEpoch
        viewModelScope.launch {
            if (!isCurrentSession(operationEpoch, currentSession)) return@launch
            runCatching { api.getTimeline(spaceId, currentSession.tokens.accessToken) }
                .onSuccess { story ->
                    if (isCurrentSession(operationEpoch, currentSession)) {
                        storyCursor = story.nextCursor
                        mutate {
                            it.copy(
                                storyItems = story.items,
                                storyHasMore = story.hasMore,
                                error = null,
                            )
                        }
                    }
                }
                .onFailure {
                    if (isCurrentSession(operationEpoch, currentSession)) {
                        failure(R.string.ref_error_story_load_failed, clearBusy = false)
                    }
                }
        }
    }

    /** Profile data is lazy: older test fakes and normal Story startup need no profile calls. */
    fun refreshProfile() {
        val api = contract ?: return
        val currentSession = session ?: return
        val spaceId = activeSpaceId ?: return
        val operationEpoch = sessionEpoch
        mutate {
            it.copy(
                profile = it.profile.copy(
                    loading = true,
                    busy = false,
                    status = null,
                    error = null,
                ),
            )
        }
        viewModelScope.launch {
            if (!isCurrentSession(operationEpoch, currentSession)) return@launch
            runCatching { loadProfileIdentity(api, spaceId, currentSession) }
                .onSuccess { profile ->
                    if (isCurrentSession(operationEpoch, currentSession)) {
                        // loadProfileIdentity builds a fresh ProfileUiState
                        // that knows nothing about ProfilePreference; carry
                        // that part of the state forward rather than
                        // clobbering it back to defaults.
                        mutate {
                            it.copy(
                                profile = profile.copy(
                                    preferences = it.profile.preferences,
                                    preferencesBusy = it.profile.preferencesBusy,
                                    preferencesProblem = it.profile.preferencesProblem,
                                ),
                            )
                        }
                    }
                }
                .onFailure {
                    if (isCurrentSession(operationEpoch, currentSession)) {
                        mutate {
                            it.copy(
                                profile = it.profile.copy(
                                    loading = false,
                                    busy = false,
                                    status = null,
                                    error = message(R.string.profile_loading_failed),
                                ),
                            )
                        }
                    }
                }
        }
    }

    fun saveProfileDisplayName(displayName: String) {
        val api = contract ?: return
        val currentSession = session ?: return
        val spaceId = activeSpaceId ?: return
        val currentProfile = _uiState.value.profile.self ?: return refreshProfile()
        if (displayName.isBlank()) {
            mutate {
                it.copy(
                    profile = it.profile.copy(
                        error = message(R.string.profile_display_name_required),
                        status = null,
                    ),
                )
            }
            return
        }
        val operationEpoch = sessionEpoch
        mutate {
            it.copy(
                profile = it.profile.copy(
                    busy = true,
                    status = null,
                    error = null,
                ),
            )
        }
        viewModelScope.launch {
            if (!isCurrentSession(operationEpoch, currentSession)) return@launch
            runCatching {
                updateProfileDisplayName(
                    api = api,
                    spaceId = spaceId,
                    session = currentSession,
                    current = currentProfile,
                    displayName = displayName,
                )
            }.onSuccess { updated ->
                if (!isCurrentSession(operationEpoch, currentSession)) return@onSuccess
                session = currentSession.copy(
                    account = currentSession.account.copy(displayName = updated.displayName),
                )
                mutate {
                    it.copy(
                        profile = it.profile.copy(
                            self = updated,
                            busy = false,
                            status = message(R.string.profile_saved),
                            error = null,
                        ),
                    )
                }
                refreshStory()
            }.onFailure {
                if (sessionEpoch == operationEpoch) profileFailure(R.string.profile_save_failed)
            }
        }
    }

    fun beginProfileAvatarSelection(): Long? = session?.let { sessionEpoch }

    fun setProfileAvatar(image: SelectedImage, selectionEpoch: Long) {
        val api = contract ?: return
        val currentSession = session ?: return
        val spaceId = activeSpaceId ?: return
        val currentProfile = _uiState.value.profile.self ?: return refreshProfile()
        if (selectionEpoch != sessionEpoch) return
        val operationEpoch = sessionEpoch
        mutate {
            it.copy(
                profile = it.profile.copy(
                    busy = true,
                    status = message(R.string.profile_avatar_uploading),
                    error = null,
                ),
            )
        }
        viewModelScope.launch {
            if (!isCurrentSession(operationEpoch, currentSession)) return@launch
            runCatching {
                val updated = updateProfileAvatar(
                    api = api,
                    spaceId = spaceId,
                    session = currentSession,
                    current = currentProfile,
                    image = image,
                )
                val bytes = runCatching {
                    api.readProfileAvatar(spaceId, currentSession.tokens.accessToken, currentSession.account.id)
                }.getOrNull()
                updated to bytes
            }.onSuccess { (updated, bytes) ->
                if (!isCurrentSession(operationEpoch, currentSession)) return@onSuccess
                mutate {
                    it.copy(
                        profile = it.profile.copy(
                            self = updated,
                            selfAvatarBytes = bytes,
                            busy = false,
                            status = message(R.string.profile_saved),
                            error = null,
                        ),
                    )
                }
            }.onFailure {
                if (isCurrentSession(operationEpoch, currentSession)) {
                    profileFailure(R.string.profile_avatar_failed)
                }
            }
        }
    }

    fun setProfileAvatarSelectionError(throwable: Throwable, selectionEpoch: Long) {
        if (session == null || selectionEpoch != sessionEpoch) return
        mutate {
            it.copy(
                profile = it.profile.copy(
                    busy = false,
                    status = null,
                    error = message(
                        R.string.profile_avatar_failed,
                        throwable.message.orEmpty(),
                    ),
                ),
            )
        }
    }

    fun removeProfileAvatar() {
        val api = contract ?: return
        val currentSession = session ?: return
        val spaceId = activeSpaceId ?: return
        val currentProfile = _uiState.value.profile.self ?: return refreshProfile()
        val operationEpoch = sessionEpoch
        mutate {
            it.copy(profile = it.profile.copy(busy = true, status = null, error = null))
        }
        viewModelScope.launch {
            if (!isCurrentSession(operationEpoch, currentSession)) return@launch
            runCatching {
                removeProfileAvatar(api, spaceId, currentSession, currentProfile)
            }.onSuccess { updated ->
                if (!isCurrentSession(operationEpoch, currentSession)) return@onSuccess
                mutate {
                    it.copy(
                        profile = it.profile.copy(
                            self = updated,
                            selfAvatarBytes = null,
                            busy = false,
                            status = message(R.string.profile_saved),
                            error = null,
                        ),
                    )
                }
            }.onFailure {
                if (isCurrentSession(operationEpoch, currentSession)) {
                    profileFailure(R.string.profile_avatar_failed)
                }
            }
        }
    }

    /**
     * Every ProfilePreference visible to this account.
     *
     * SELF_PROFILE rows already arrive embedded on [ProfileUiState.self] and
     * [ProfileUiState.partner] via [refreshProfile]; this call exists for the
     * PRIVATE_PARTNER_NOTE rows, which the server never attaches to either
     * profile. The server applies no accountId filter, so this list also
     * contains SELF_PROFILE rows again — callers read [ProfileUiState.self]
     * and [ProfileUiState.partner] for those instead of this list.
     */
    fun loadProfilePreferences() {
        val api = contract ?: return
        val currentSession = session ?: return
        val spaceId = activeSpaceId ?: return
        val operationEpoch = sessionEpoch

        mutate { it.copy(profile = it.profile.copy(preferencesBusy = true, preferencesProblem = null)) }
        viewModelScope.launch {
            if (!isCurrentSession(operationEpoch, currentSession)) return@launch
            runCatching { api.listProfilePreferences(spaceId, currentSession.tokens.accessToken) }
                .onSuccess { preferences ->
                    if (!isCurrentSession(operationEpoch, currentSession)) return@onSuccess
                    mutate {
                        it.copy(profile = it.profile.copy(preferences = preferences, preferencesBusy = false))
                    }
                }
                .onFailure { throwable ->
                    if (!isCurrentSession(operationEpoch, currentSession)) return@onFailure
                    mutate {
                        it.copy(
                            profile = it.profile.copy(
                                preferencesBusy = false,
                                preferencesProblem = problemFor(throwable),
                            ),
                        )
                    }
                }
        }
    }

    fun addProfilePreference(
        accountId: java.util.UUID,
        visibility: ProfileVisibility,
        category: PreferenceCategory,
        topic: String,
        sentiment: PreferenceSentiment,
        value: String,
    ) {
        if (topic.isBlank() || value.isBlank()) return
        val api = contract ?: return
        val currentSession = session ?: return
        val spaceId = activeSpaceId ?: return
        val operationEpoch = sessionEpoch

        mutate { it.copy(profile = it.profile.copy(preferencesBusy = true, preferencesProblem = null)) }
        viewModelScope.launch {
            if (!isCurrentSession(operationEpoch, currentSession)) return@launch
            runCatching {
                api.createProfilePreference(
                    spaceId,
                    currentSession.tokens.accessToken,
                    ProfilePreferenceCreate(
                        accountId = accountId,
                        category = category,
                        sentiment = sentiment,
                        topic = topic,
                        value = value,
                        visibility = visibility,
                    ),
                )
            }
                .onSuccess {
                    if (!isCurrentSession(operationEpoch, currentSession)) return@onSuccess
                    mutate { it.copy(profile = it.profile.copy(preferencesBusy = false)) }
                    refreshProfile()
                    loadProfilePreferences()
                }
                .onFailure { throwable ->
                    if (!isCurrentSession(operationEpoch, currentSession)) return@onFailure
                    mutate {
                        it.copy(
                            profile = it.profile.copy(
                                preferencesBusy = false,
                                preferencesProblem = problemFor(throwable),
                            ),
                        )
                    }
                }
        }
    }

    fun updateProfilePreference(
        preference: ProfilePreferenceView,
        category: PreferenceCategory,
        topic: String,
        sentiment: PreferenceSentiment,
        value: String,
    ) {
        if (topic.isBlank() || value.isBlank()) return
        val api = contract ?: return
        val currentSession = session ?: return
        val spaceId = activeSpaceId ?: return
        val operationEpoch = sessionEpoch

        mutate { it.copy(profile = it.profile.copy(preferencesBusy = true, preferencesProblem = null)) }
        viewModelScope.launch {
            if (!isCurrentSession(operationEpoch, currentSession)) return@launch
            runCatching {
                api.updateProfilePreference(
                    spaceId,
                    currentSession.tokens.accessToken,
                    preference.id,
                    preference.version,
                    ProfilePreferenceUpdate(
                        category = category,
                        sentiment = sentiment,
                        topic = topic,
                        value = value,
                    ),
                )
            }
                .onSuccess {
                    if (!isCurrentSession(operationEpoch, currentSession)) return@onSuccess
                    mutate { it.copy(profile = it.profile.copy(preferencesBusy = false)) }
                    refreshProfile()
                    loadProfilePreferences()
                }
                .onFailure { throwable ->
                    if (!isCurrentSession(operationEpoch, currentSession)) return@onFailure
                    mutate {
                        it.copy(
                            profile = it.profile.copy(
                                preferencesBusy = false,
                                preferencesProblem = problemFor(throwable),
                            ),
                        )
                    }
                }
        }
    }

    fun deleteProfilePreference(preference: ProfilePreferenceView) {
        val api = contract ?: return
        val currentSession = session ?: return
        val spaceId = activeSpaceId ?: return
        val operationEpoch = sessionEpoch

        mutate { it.copy(profile = it.profile.copy(preferencesBusy = true, preferencesProblem = null)) }
        viewModelScope.launch {
            if (!isCurrentSession(operationEpoch, currentSession)) return@launch
            runCatching {
                api.deleteProfilePreference(
                    spaceId,
                    currentSession.tokens.accessToken,
                    preference.id,
                    preference.version,
                )
            }
                .onSuccess {
                    if (!isCurrentSession(operationEpoch, currentSession)) return@onSuccess
                    mutate { it.copy(profile = it.profile.copy(preferencesBusy = false)) }
                    refreshProfile()
                    loadProfilePreferences()
                }
                .onFailure { throwable ->
                    if (!isCurrentSession(operationEpoch, currentSession)) return@onFailure
                    mutate {
                        it.copy(
                            profile = it.profile.copy(
                                preferencesBusy = false,
                                preferencesProblem = problemFor(throwable),
                            ),
                        )
                    }
                }
        }
    }

    fun clearProfilePreferences() {
        mutate {
            it.copy(
                profile = it.profile.copy(
                    preferences = emptyList(),
                    preferencesBusy = false,
                    preferencesProblem = null,
                ),
            )
        }
    }

    /**
     * Enforces the same latitude/longitude pairing the server enforces as
     * `PLACE_COORDINATE_PAIR_REQUIRED`, so a client mistake is refused before
     * the request rather than surfacing only as a 400.
     *
     * Returns `null` when the pairing is invalid (exactly one of the two set,
     * or either unparsable); both blank is valid and yields `null to null`.
     */
    private fun pairedCoordinates(
        latitude: String,
        longitude: String,
    ): Pair<java.math.BigDecimal?, java.math.BigDecimal?>? {
        val lat = latitude.trim()
        val lng = longitude.trim()
        if (lat.isBlank() && lng.isBlank()) return null to null
        if (lat.isBlank() || lng.isBlank()) return null
        val parsedLat = runCatching { java.math.BigDecimal(lat) }.getOrNull() ?: return null
        val parsedLng = runCatching { java.math.BigDecimal(lng) }.getOrNull() ?: return null
        return parsedLat to parsedLng
    }

    fun loadPlaces() {
        val api = contract ?: return
        val currentSession = session ?: return
        val spaceId = activeSpaceId ?: return
        val operationEpoch = sessionEpoch

        mutate { it.copy(placesBusy = true, placesProblem = null) }
        viewModelScope.launch {
            if (!isCurrentSession(operationEpoch, currentSession)) return@launch
            runCatching { api.listPlaces(spaceId, currentSession.tokens.accessToken) }
                .onSuccess { page ->
                    if (!isCurrentSession(operationEpoch, currentSession)) return@onSuccess
                    mutate { it.copy(places = page.items, placesBusy = false) }
                }
                .onFailure { throwable ->
                    if (!isCurrentSession(operationEpoch, currentSession)) return@onFailure
                    mutate { it.copy(placesBusy = false, placesProblem = problemFor(throwable)) }
                }
        }
    }

    fun addPlace(
        name: String,
        description: String,
        address: String,
        latitude: String,
        longitude: String,
    ) {
        if (name.isBlank()) return
        val coordinates = pairedCoordinates(latitude, longitude) ?: return
        val api = contract ?: return
        val currentSession = session ?: return
        val spaceId = activeSpaceId ?: return
        val operationEpoch = sessionEpoch

        mutate { it.copy(placesBusy = true, placesProblem = null) }
        viewModelScope.launch {
            if (!isCurrentSession(operationEpoch, currentSession)) return@launch
            runCatching {
                api.createPlace(
                    spaceId,
                    currentSession.tokens.accessToken,
                    PlaceCreate(
                        name = name,
                        address = address.trim().takeIf { it.isNotBlank() },
                        description = description.trim().takeIf { it.isNotBlank() },
                        latitude = coordinates.first,
                        longitude = coordinates.second,
                    ),
                )
            }
                .onSuccess {
                    if (!isCurrentSession(operationEpoch, currentSession)) return@onSuccess
                    mutate { it.copy(placesBusy = false) }
                    loadPlaces()
                }
                .onFailure { throwable ->
                    if (!isCurrentSession(operationEpoch, currentSession)) return@onFailure
                    mutate { it.copy(placesBusy = false, placesProblem = problemFor(throwable)) }
                }
        }
    }

    fun updatePlace(
        place: PlaceDetail,
        name: String,
        description: String,
        address: String,
        latitude: String,
        longitude: String,
    ) {
        if (name.isBlank()) return
        val coordinates = pairedCoordinates(latitude, longitude) ?: return
        val api = contract ?: return
        val currentSession = session ?: return
        val spaceId = activeSpaceId ?: return
        val operationEpoch = sessionEpoch

        mutate { it.copy(placesBusy = true, placesProblem = null) }
        viewModelScope.launch {
            if (!isCurrentSession(operationEpoch, currentSession)) return@launch
            runCatching {
                api.updatePlace(
                    spaceId,
                    currentSession.tokens.accessToken,
                    place.id,
                    place.version,
                    PlaceUpdate(
                        name = name,
                        address = address.trim().takeIf { it.isNotBlank() },
                        description = description.trim().takeIf { it.isNotBlank() },
                        latitude = coordinates.first,
                        longitude = coordinates.second,
                    ),
                )
            }
                .onSuccess {
                    if (!isCurrentSession(operationEpoch, currentSession)) return@onSuccess
                    mutate { it.copy(placesBusy = false) }
                    loadPlaces()
                }
                .onFailure { throwable ->
                    if (!isCurrentSession(operationEpoch, currentSession)) return@onFailure
                    mutate { it.copy(placesBusy = false, placesProblem = problemFor(throwable)) }
                }
        }
    }

    fun deletePlace(place: PlaceDetail) {
        val api = contract ?: return
        val currentSession = session ?: return
        val spaceId = activeSpaceId ?: return
        val operationEpoch = sessionEpoch

        mutate { it.copy(placesBusy = true, placesProblem = null) }
        viewModelScope.launch {
            if (!isCurrentSession(operationEpoch, currentSession)) return@launch
            runCatching {
                api.deletePlace(spaceId, currentSession.tokens.accessToken, place.id, place.version)
            }
                .onSuccess {
                    if (!isCurrentSession(operationEpoch, currentSession)) return@onSuccess
                    mutate { it.copy(placesBusy = false) }
                    loadPlaces()
                }
                .onFailure { throwable ->
                    if (!isCurrentSession(operationEpoch, currentSession)) return@onFailure
                    mutate { it.copy(placesBusy = false, placesProblem = problemFor(throwable)) }
                }
        }
    }

    fun clearPlaces() {
        mutate { it.copy(places = emptyList(), placesBusy = false, placesProblem = null) }
    }

    /**
     * Loads what a place's relations screen needs: the shared Story as
     * possible targets, and which of them are already linked to [placeId].
     *
     * Reads the Story timeline rather than any place-specific endpoint for
     * the target list, because the typed-relation endpoints return only
     * linked ids, never content — a second, separately authorized read path
     * for content was deliberately not built. This is also why a private
     * HeartMoment can never appear here: the timeline itself never carries
     * one that is not the caller's own or shared.
     */
    fun loadPlaceRelations(placeId: java.util.UUID) {
        val api = contract ?: return
        val currentSession = session ?: return
        val spaceId = activeSpaceId ?: return
        val operationEpoch = sessionEpoch

        mutate { it.copy(placeRelationsBusy = true, placeRelationsProblem = null) }
        viewModelScope.launch {
            if (!isCurrentSession(operationEpoch, currentSession)) return@launch
            runCatching {
                val accessToken = currentSession.tokens.accessToken
                val timeline = api.getTimeline(spaceId, accessToken)
                val linkedIds = ReferenceContract.RelationTargetKind.entries
                    .flatMap { kind -> api.listPlaceRelationTargets(spaceId, accessToken, placeId, kind) }
                    .toSet()
                timeline.items.map { it.toRelationTargetItem() } to linkedIds
            }
                .onSuccess { (targets, linkedIds) ->
                    if (!isCurrentSession(operationEpoch, currentSession)) return@onSuccess
                    mutate {
                        it.copy(
                            placeRelationTargets = targets,
                            placeLinkedTargetIds = linkedIds,
                            placeRelationsBusy = false,
                        )
                    }
                }
                .onFailure { throwable ->
                    if (!isCurrentSession(operationEpoch, currentSession)) return@onFailure
                    mutate {
                        it.copy(placeRelationsBusy = false, placeRelationsProblem = problemFor(throwable))
                    }
                }
        }
    }

    fun linkPlaceRelation(
        placeId: java.util.UUID,
        kind: ReferenceContract.RelationTargetKind,
        targetId: java.util.UUID,
    ) {
        val api = contract ?: return
        val currentSession = session ?: return
        val spaceId = activeSpaceId ?: return
        val operationEpoch = sessionEpoch

        mutate { it.copy(placeRelationsBusy = true, placeRelationsProblem = null) }
        viewModelScope.launch {
            if (!isCurrentSession(operationEpoch, currentSession)) return@launch
            runCatching {
                api.linkPlaceTarget(spaceId, currentSession.tokens.accessToken, placeId, kind, targetId)
            }
                .onSuccess {
                    if (!isCurrentSession(operationEpoch, currentSession)) return@onSuccess
                    mutate { it.copy(placeRelationsBusy = false) }
                    loadPlaceRelations(placeId)
                }
                .onFailure { throwable ->
                    if (!isCurrentSession(operationEpoch, currentSession)) return@onFailure
                    mutate {
                        it.copy(placeRelationsBusy = false, placeRelationsProblem = problemFor(throwable))
                    }
                }
        }
    }

    fun unlinkPlaceRelation(
        placeId: java.util.UUID,
        kind: ReferenceContract.RelationTargetKind,
        targetId: java.util.UUID,
    ) {
        val api = contract ?: return
        val currentSession = session ?: return
        val spaceId = activeSpaceId ?: return
        val operationEpoch = sessionEpoch

        mutate { it.copy(placeRelationsBusy = true, placeRelationsProblem = null) }
        viewModelScope.launch {
            if (!isCurrentSession(operationEpoch, currentSession)) return@launch
            runCatching {
                api.unlinkPlaceTarget(spaceId, currentSession.tokens.accessToken, placeId, kind, targetId)
            }
                .onSuccess {
                    if (!isCurrentSession(operationEpoch, currentSession)) return@onSuccess
                    mutate { it.copy(placeRelationsBusy = false) }
                    loadPlaceRelations(placeId)
                }
                .onFailure { throwable ->
                    if (!isCurrentSession(operationEpoch, currentSession)) return@onFailure
                    mutate {
                        it.copy(placeRelationsBusy = false, placeRelationsProblem = problemFor(throwable))
                    }
                }
        }
    }

    fun clearPlaceRelations() {
        mutate {
            it.copy(
                placeRelationTargets = emptyList(),
                placeLinkedTargetIds = emptySet(),
                placeRelationsBusy = false,
                placeRelationsProblem = null,
            )
        }
    }

    fun loadPrivateNotes() {
        val api = contract ?: return
        val currentSession = session ?: return
        val spaceId = activeSpaceId ?: return
        val operationEpoch = sessionEpoch

        mutate { it.copy(privateNotesBusy = true, privateNotesProblem = null) }
        viewModelScope.launch {
            if (!isCurrentSession(operationEpoch, currentSession)) return@launch
            runCatching { api.listPrivateNotes(spaceId, currentSession.tokens.accessToken) }
                .onSuccess { page ->
                    if (!isCurrentSession(operationEpoch, currentSession)) return@onSuccess
                    mutate { it.copy(privateNotes = page.items, privateNotesBusy = false) }
                }
                .onFailure { throwable ->
                    if (!isCurrentSession(operationEpoch, currentSession)) return@onFailure
                    mutate { it.copy(privateNotesBusy = false, privateNotesProblem = problemFor(throwable)) }
                }
        }
    }

    fun addPrivateNote(title: String, body: String, pinned: Boolean) {
        if (title.isBlank()) return
        val api = contract ?: return
        val currentSession = session ?: return
        val spaceId = activeSpaceId ?: return
        val operationEpoch = sessionEpoch

        mutate { it.copy(privateNotesBusy = true, privateNotesProblem = null) }
        viewModelScope.launch {
            if (!isCurrentSession(operationEpoch, currentSession)) return@launch
            runCatching {
                api.createPrivateNote(
                    spaceId,
                    currentSession.tokens.accessToken,
                    PrivateNoteCreate(title = title, body = body, pinned = pinned),
                )
            }
                .onSuccess {
                    if (!isCurrentSession(operationEpoch, currentSession)) return@onSuccess
                    mutate { it.copy(privateNotesBusy = false) }
                    loadPrivateNotes()
                }
                .onFailure { throwable ->
                    if (!isCurrentSession(operationEpoch, currentSession)) return@onFailure
                    mutate { it.copy(privateNotesBusy = false, privateNotesProblem = problemFor(throwable)) }
                }
        }
    }

    fun updatePrivateNote(note: PrivateNoteDetail, title: String, body: String, pinned: Boolean) {
        if (title.isBlank()) return
        val api = contract ?: return
        val currentSession = session ?: return
        val spaceId = activeSpaceId ?: return
        val operationEpoch = sessionEpoch

        mutate { it.copy(privateNotesBusy = true, privateNotesProblem = null) }
        viewModelScope.launch {
            if (!isCurrentSession(operationEpoch, currentSession)) return@launch
            runCatching {
                api.updatePrivateNote(
                    spaceId,
                    currentSession.tokens.accessToken,
                    note.id,
                    note.version,
                    PrivateNoteUpdate(title = title, body = body, pinned = pinned),
                )
            }
                .onSuccess {
                    if (!isCurrentSession(operationEpoch, currentSession)) return@onSuccess
                    mutate { it.copy(privateNotesBusy = false) }
                    loadPrivateNotes()
                }
                .onFailure { throwable ->
                    if (!isCurrentSession(operationEpoch, currentSession)) return@onFailure
                    mutate { it.copy(privateNotesBusy = false, privateNotesProblem = problemFor(throwable)) }
                }
        }
    }

    fun deletePrivateNote(note: PrivateNoteDetail) {
        val api = contract ?: return
        val currentSession = session ?: return
        val spaceId = activeSpaceId ?: return
        val operationEpoch = sessionEpoch

        mutate { it.copy(privateNotesBusy = true, privateNotesProblem = null) }
        viewModelScope.launch {
            if (!isCurrentSession(operationEpoch, currentSession)) return@launch
            runCatching {
                api.deletePrivateNote(spaceId, currentSession.tokens.accessToken, note.id, note.version)
            }
                .onSuccess {
                    if (!isCurrentSession(operationEpoch, currentSession)) return@onSuccess
                    mutate { it.copy(privateNotesBusy = false) }
                    loadPrivateNotes()
                }
                .onFailure { throwable ->
                    if (!isCurrentSession(operationEpoch, currentSession)) return@onFailure
                    mutate { it.copy(privateNotesBusy = false, privateNotesProblem = problemFor(throwable)) }
                }
        }
    }

    fun clearPrivateNotes() {
        mutate { it.copy(privateNotes = emptyList(), privateNotesBusy = false, privateNotesProblem = null) }
    }

    fun loadGiftIdeas() {
        val api = contract ?: return
        val currentSession = session ?: return
        val spaceId = activeSpaceId ?: return
        val operationEpoch = sessionEpoch

        mutate { it.copy(giftIdeasBusy = true, giftIdeasProblem = null) }
        viewModelScope.launch {
            if (!isCurrentSession(operationEpoch, currentSession)) return@launch
            runCatching { api.listGiftIdeas(spaceId, currentSession.tokens.accessToken) }
                .onSuccess { page ->
                    if (!isCurrentSession(operationEpoch, currentSession)) return@onSuccess
                    mutate { it.copy(giftIdeas = page.items, giftIdeasBusy = false) }
                }
                .onFailure { throwable ->
                    if (!isCurrentSession(operationEpoch, currentSession)) return@onFailure
                    mutate { it.copy(giftIdeasBusy = false, giftIdeasProblem = problemFor(throwable)) }
                }
        }
    }

    fun addGiftIdea(
        title: String,
        description: String,
        occasion: String,
        recipient: String,
        priceText: String,
        url: String,
        targetOn: String,
        pinned: Boolean,
    ) {
        if (title.isBlank()) return
        val api = contract ?: return
        val currentSession = session ?: return
        val spaceId = activeSpaceId ?: return
        val operationEpoch = sessionEpoch

        mutate { it.copy(giftIdeasBusy = true, giftIdeasProblem = null) }
        viewModelScope.launch {
            if (!isCurrentSession(operationEpoch, currentSession)) return@launch
            runCatching {
                api.createGiftIdea(
                    spaceId,
                    currentSession.tokens.accessToken,
                    GiftIdeaCreate(
                        title = title,
                        description = description.trim().takeIf { it.isNotBlank() },
                        occasion = occasion.trim().takeIf { it.isNotBlank() },
                        pinned = pinned,
                        priceText = priceText.trim().takeIf { it.isNotBlank() },
                        recipient = recipient.trim().takeIf { it.isNotBlank() },
                        targetOn = parseHappenedOn(targetOn),
                        url = url.trim().takeIf { it.isNotBlank() },
                    ),
                )
            }
                .onSuccess {
                    if (!isCurrentSession(operationEpoch, currentSession)) return@onSuccess
                    mutate { it.copy(giftIdeasBusy = false) }
                    loadGiftIdeas()
                }
                .onFailure { throwable ->
                    if (!isCurrentSession(operationEpoch, currentSession)) return@onFailure
                    mutate { it.copy(giftIdeasBusy = false, giftIdeasProblem = problemFor(throwable)) }
                }
        }
    }

    fun updateGiftIdea(
        idea: GiftIdeaDetail,
        title: String,
        description: String,
        occasion: String,
        recipient: String,
        priceText: String,
        url: String,
        targetOn: String,
        pinned: Boolean,
    ) {
        if (title.isBlank()) return
        val api = contract ?: return
        val currentSession = session ?: return
        val spaceId = activeSpaceId ?: return
        val operationEpoch = sessionEpoch

        mutate { it.copy(giftIdeasBusy = true, giftIdeasProblem = null) }
        viewModelScope.launch {
            if (!isCurrentSession(operationEpoch, currentSession)) return@launch
            runCatching {
                api.updateGiftIdea(
                    spaceId,
                    currentSession.tokens.accessToken,
                    idea.id,
                    idea.version,
                    GiftIdeaUpdate(
                        title = title,
                        description = description.trim().takeIf { it.isNotBlank() },
                        occasion = occasion.trim().takeIf { it.isNotBlank() },
                        pinned = pinned,
                        priceText = priceText.trim().takeIf { it.isNotBlank() },
                        recipient = recipient.trim().takeIf { it.isNotBlank() },
                        targetOn = parseHappenedOn(targetOn),
                        url = url.trim().takeIf { it.isNotBlank() },
                    ),
                )
            }
                .onSuccess {
                    if (!isCurrentSession(operationEpoch, currentSession)) return@onSuccess
                    mutate { it.copy(giftIdeasBusy = false) }
                    loadGiftIdeas()
                }
                .onFailure { throwable ->
                    if (!isCurrentSession(operationEpoch, currentSession)) return@onFailure
                    mutate { it.copy(giftIdeasBusy = false, giftIdeasProblem = problemFor(throwable)) }
                }
        }
    }

    /**
     * A status change alone, sent as its own partial update rather than
     * folded into [updateGiftIdea]: the server owns M3-D17's transition
     * graph and rejects an invalid one, so this client never encodes which
     * transitions are allowed — it only ever proposes a target status.
     */
    fun changeGiftIdeaStatus(idea: GiftIdeaDetail, status: GiftIdeaStatus) {
        val api = contract ?: return
        val currentSession = session ?: return
        val spaceId = activeSpaceId ?: return
        val operationEpoch = sessionEpoch

        mutate { it.copy(giftIdeasBusy = true, giftIdeasProblem = null) }
        viewModelScope.launch {
            if (!isCurrentSession(operationEpoch, currentSession)) return@launch
            runCatching {
                api.updateGiftIdea(
                    spaceId,
                    currentSession.tokens.accessToken,
                    idea.id,
                    idea.version,
                    GiftIdeaUpdate(status = status),
                )
            }
                .onSuccess {
                    if (!isCurrentSession(operationEpoch, currentSession)) return@onSuccess
                    mutate { it.copy(giftIdeasBusy = false) }
                    loadGiftIdeas()
                }
                .onFailure { throwable ->
                    if (!isCurrentSession(operationEpoch, currentSession)) return@onFailure
                    mutate { it.copy(giftIdeasBusy = false, giftIdeasProblem = problemFor(throwable)) }
                }
        }
    }

    fun deleteGiftIdea(idea: GiftIdeaDetail) {
        val api = contract ?: return
        val currentSession = session ?: return
        val spaceId = activeSpaceId ?: return
        val operationEpoch = sessionEpoch

        mutate { it.copy(giftIdeasBusy = true, giftIdeasProblem = null) }
        viewModelScope.launch {
            if (!isCurrentSession(operationEpoch, currentSession)) return@launch
            runCatching {
                api.deleteGiftIdea(spaceId, currentSession.tokens.accessToken, idea.id, idea.version)
            }
                .onSuccess {
                    if (!isCurrentSession(operationEpoch, currentSession)) return@onSuccess
                    mutate { it.copy(giftIdeasBusy = false) }
                    loadGiftIdeas()
                }
                .onFailure { throwable ->
                    if (!isCurrentSession(operationEpoch, currentSession)) return@onFailure
                    mutate { it.copy(giftIdeasBusy = false, giftIdeasProblem = problemFor(throwable)) }
                }
        }
    }

    fun clearGiftIdeas() {
        mutate { it.copy(giftIdeas = emptyList(), giftIdeasBusy = false, giftIdeasProblem = null) }
    }

    fun loadPrivateCollections() {
        val api = contract ?: return
        val currentSession = session ?: return
        val spaceId = activeSpaceId ?: return
        val operationEpoch = sessionEpoch

        mutate { it.copy(privateCollectionsBusy = true, privateCollectionsProblem = null) }
        viewModelScope.launch {
            if (!isCurrentSession(operationEpoch, currentSession)) return@launch
            runCatching { api.listPrivateCollections(spaceId, currentSession.tokens.accessToken) }
                .onSuccess { page ->
                    if (!isCurrentSession(operationEpoch, currentSession)) return@onSuccess
                    mutate { it.copy(privateCollections = page.items, privateCollectionsBusy = false) }
                }
                .onFailure { throwable ->
                    if (!isCurrentSession(operationEpoch, currentSession)) return@onFailure
                    mutate {
                        it.copy(privateCollectionsBusy = false, privateCollectionsProblem = problemFor(throwable))
                    }
                }
        }
    }

    fun addPrivateCollection(title: String, icon: String) {
        if (title.isBlank()) return
        val api = contract ?: return
        val currentSession = session ?: return
        val spaceId = activeSpaceId ?: return
        val operationEpoch = sessionEpoch

        mutate { it.copy(privateCollectionsBusy = true, privateCollectionsProblem = null) }
        viewModelScope.launch {
            if (!isCurrentSession(operationEpoch, currentSession)) return@launch
            runCatching {
                api.createPrivateCollection(
                    spaceId,
                    currentSession.tokens.accessToken,
                    PrivateCollectionCreate(title = title, icon = icon.trim().takeIf { it.isNotBlank() }),
                )
            }
                .onSuccess {
                    if (!isCurrentSession(operationEpoch, currentSession)) return@onSuccess
                    mutate { it.copy(privateCollectionsBusy = false) }
                    loadPrivateCollections()
                }
                .onFailure { throwable ->
                    if (!isCurrentSession(operationEpoch, currentSession)) return@onFailure
                    mutate {
                        it.copy(privateCollectionsBusy = false, privateCollectionsProblem = problemFor(throwable))
                    }
                }
        }
    }

    fun updatePrivateCollection(collection: PrivateCollectionDetail, title: String, icon: String) {
        if (title.isBlank()) return
        val api = contract ?: return
        val currentSession = session ?: return
        val spaceId = activeSpaceId ?: return
        val operationEpoch = sessionEpoch

        mutate { it.copy(privateCollectionsBusy = true, privateCollectionsProblem = null) }
        viewModelScope.launch {
            if (!isCurrentSession(operationEpoch, currentSession)) return@launch
            runCatching {
                api.updatePrivateCollection(
                    spaceId,
                    currentSession.tokens.accessToken,
                    collection.id,
                    collection.version,
                    PrivateCollectionUpdate(title = title, icon = icon.trim().takeIf { it.isNotBlank() }),
                )
            }
                .onSuccess {
                    if (!isCurrentSession(operationEpoch, currentSession)) return@onSuccess
                    mutate { it.copy(privateCollectionsBusy = false) }
                    loadPrivateCollections()
                }
                .onFailure { throwable ->
                    if (!isCurrentSession(operationEpoch, currentSession)) return@onFailure
                    mutate {
                        it.copy(privateCollectionsBusy = false, privateCollectionsProblem = problemFor(throwable))
                    }
                }
        }
    }

    fun deletePrivateCollection(collection: PrivateCollectionDetail) {
        val api = contract ?: return
        val currentSession = session ?: return
        val spaceId = activeSpaceId ?: return
        val operationEpoch = sessionEpoch

        mutate { it.copy(privateCollectionsBusy = true, privateCollectionsProblem = null) }
        viewModelScope.launch {
            if (!isCurrentSession(operationEpoch, currentSession)) return@launch
            runCatching {
                api.deletePrivateCollection(spaceId, currentSession.tokens.accessToken, collection.id, collection.version)
            }
                .onSuccess {
                    if (!isCurrentSession(operationEpoch, currentSession)) return@onSuccess
                    mutate { it.copy(privateCollectionsBusy = false) }
                    loadPrivateCollections()
                }
                .onFailure { throwable ->
                    if (!isCurrentSession(operationEpoch, currentSession)) return@onFailure
                    mutate {
                        it.copy(privateCollectionsBusy = false, privateCollectionsProblem = problemFor(throwable))
                    }
                }
        }
    }

    fun addPrivateCollectionItem(collection: PrivateCollectionDetail, title: String) {
        if (title.isBlank()) return
        val api = contract ?: return
        val currentSession = session ?: return
        val spaceId = activeSpaceId ?: return
        val operationEpoch = sessionEpoch

        mutate { it.copy(privateCollectionsBusy = true, privateCollectionsProblem = null) }
        viewModelScope.launch {
            if (!isCurrentSession(operationEpoch, currentSession)) return@launch
            runCatching {
                api.createPrivateCollectionItem(
                    spaceId,
                    currentSession.tokens.accessToken,
                    collection.id,
                    PrivateCollectionItemCreate(title = title),
                )
            }
                .onSuccess {
                    if (!isCurrentSession(operationEpoch, currentSession)) return@onSuccess
                    mutate { it.copy(privateCollectionsBusy = false) }
                    loadPrivateCollections()
                }
                .onFailure { throwable ->
                    if (!isCurrentSession(operationEpoch, currentSession)) return@onFailure
                    mutate {
                        it.copy(privateCollectionsBusy = false, privateCollectionsProblem = problemFor(throwable))
                    }
                }
        }
    }

    fun toggleCollectionItemCompleted(collection: PrivateCollectionDetail, item: PrivateCollectionItemDetail) {
        val api = contract ?: return
        val currentSession = session ?: return
        val spaceId = activeSpaceId ?: return
        val operationEpoch = sessionEpoch

        mutate { it.copy(privateCollectionsBusy = true, privateCollectionsProblem = null) }
        viewModelScope.launch {
            if (!isCurrentSession(operationEpoch, currentSession)) return@launch
            runCatching {
                api.updatePrivateCollectionItem(
                    spaceId,
                    currentSession.tokens.accessToken,
                    collection.id,
                    item.id,
                    item.version,
                    PrivateCollectionItemUpdate(completed = !item.completed),
                )
            }
                .onSuccess {
                    if (!isCurrentSession(operationEpoch, currentSession)) return@onSuccess
                    mutate { it.copy(privateCollectionsBusy = false) }
                    loadPrivateCollections()
                }
                .onFailure { throwable ->
                    if (!isCurrentSession(operationEpoch, currentSession)) return@onFailure
                    mutate {
                        it.copy(privateCollectionsBusy = false, privateCollectionsProblem = problemFor(throwable))
                    }
                }
        }
    }

    fun deletePrivateCollectionItem(collection: PrivateCollectionDetail, item: PrivateCollectionItemDetail) {
        val api = contract ?: return
        val currentSession = session ?: return
        val spaceId = activeSpaceId ?: return
        val operationEpoch = sessionEpoch

        mutate { it.copy(privateCollectionsBusy = true, privateCollectionsProblem = null) }
        viewModelScope.launch {
            if (!isCurrentSession(operationEpoch, currentSession)) return@launch
            runCatching {
                api.deletePrivateCollectionItem(
                    spaceId,
                    currentSession.tokens.accessToken,
                    collection.id,
                    item.id,
                    item.version,
                )
            }
                .onSuccess {
                    if (!isCurrentSession(operationEpoch, currentSession)) return@onSuccess
                    mutate { it.copy(privateCollectionsBusy = false) }
                    loadPrivateCollections()
                }
                .onFailure { throwable ->
                    if (!isCurrentSession(operationEpoch, currentSession)) return@onFailure
                    mutate {
                        it.copy(privateCollectionsBusy = false, privateCollectionsProblem = problemFor(throwable))
                    }
                }
        }
    }

    fun moveCollectionItemUp(collection: PrivateCollectionDetail, item: PrivateCollectionItemDetail) {
        reorderCollectionItem(collection, item, offset = -1)
    }

    fun moveCollectionItemDown(collection: PrivateCollectionDetail, item: PrivateCollectionItemDetail) {
        reorderCollectionItem(collection, item, offset = 1)
    }

    /**
     * Swaps [item] with its neighbour [offset] positions away and sends the
     * whole resulting order. A swap always keeps the same set of ids the
     * collection already has, so it satisfies the server's exact-set order
     * contract by construction rather than by re-checking it here.
     */
    private fun reorderCollectionItem(collection: PrivateCollectionDetail, item: PrivateCollectionItemDetail, offset: Int) {
        val api = contract ?: return
        val currentSession = session ?: return
        val spaceId = activeSpaceId ?: return
        val operationEpoch = sessionEpoch

        val currentOrder = collection.items.sortedBy { it.position }.map { it.id }
        val index = currentOrder.indexOf(item.id)
        val targetIndex = index + offset
        if (index < 0 || targetIndex < 0 || targetIndex >= currentOrder.size) return
        val newOrder = currentOrder.toMutableList()
        val moved = newOrder.removeAt(index)
        newOrder.add(targetIndex, moved)

        mutate { it.copy(privateCollectionsBusy = true, privateCollectionsProblem = null) }
        viewModelScope.launch {
            if (!isCurrentSession(operationEpoch, currentSession)) return@launch
            runCatching {
                api.reorderPrivateCollectionItems(
                    spaceId,
                    currentSession.tokens.accessToken,
                    collection.id,
                    collection.version,
                    newOrder,
                )
            }
                .onSuccess {
                    if (!isCurrentSession(operationEpoch, currentSession)) return@onSuccess
                    mutate { it.copy(privateCollectionsBusy = false) }
                    loadPrivateCollections()
                }
                .onFailure { throwable ->
                    if (!isCurrentSession(operationEpoch, currentSession)) return@onFailure
                    mutate {
                        it.copy(privateCollectionsBusy = false, privateCollectionsProblem = problemFor(throwable))
                    }
                }
        }
    }

    fun clearPrivateCollections() {
        mutate {
            it.copy(privateCollections = emptyList(), privateCollectionsBusy = false, privateCollectionsProblem = null)
        }
    }

    fun loadNotifications() {
        val api = contract ?: return
        val currentSession = session ?: return
        val spaceId = activeSpaceId ?: return
        val operationEpoch = sessionEpoch

        mutate { it.copy(notificationsBusy = true, notificationsProblem = null) }
        viewModelScope.launch {
            if (!isCurrentSession(operationEpoch, currentSession)) return@launch
            runCatching { api.listNotifications(spaceId, currentSession.tokens.accessToken) }
                .onSuccess { page ->
                    if (!isCurrentSession(operationEpoch, currentSession)) return@onSuccess
                    mutate { it.copy(notifications = page.items, notificationsBusy = false) }
                }
                .onFailure { throwable ->
                    if (!isCurrentSession(operationEpoch, currentSession)) return@onFailure
                    mutate { it.copy(notificationsBusy = false, notificationsProblem = problemFor(throwable)) }
                }
        }
    }

    fun loadUnreadNotificationCount() {
        val api = contract ?: return
        val currentSession = session ?: return
        val spaceId = activeSpaceId ?: return
        val operationEpoch = sessionEpoch

        viewModelScope.launch {
            if (!isCurrentSession(operationEpoch, currentSession)) return@launch
            runCatching { api.getNotificationUnreadCount(spaceId, currentSession.tokens.accessToken) }
                .onSuccess { count ->
                    if (!isCurrentSession(operationEpoch, currentSession)) return@onSuccess
                    mutate { it.copy(unreadNotificationCount = count.unreadCount) }
                }
        }
    }

    fun markNotificationRead(notification: NotificationItem) {
        val api = contract ?: return
        val currentSession = session ?: return
        val spaceId = activeSpaceId ?: return
        val operationEpoch = sessionEpoch

        mutate { it.copy(notificationsBusy = true, notificationsProblem = null) }
        viewModelScope.launch {
            if (!isCurrentSession(operationEpoch, currentSession)) return@launch
            runCatching {
                api.markNotificationRead(spaceId, currentSession.tokens.accessToken, notification.id)
            }
                .onSuccess {
                    if (!isCurrentSession(operationEpoch, currentSession)) return@onSuccess
                    mutate { it.copy(notificationsBusy = false) }
                    loadNotifications()
                    loadUnreadNotificationCount()
                }
                .onFailure { throwable ->
                    if (!isCurrentSession(operationEpoch, currentSession)) return@onFailure
                    mutate { it.copy(notificationsBusy = false, notificationsProblem = problemFor(throwable)) }
                }
        }
    }

    fun markAllNotificationsRead() {
        val api = contract ?: return
        val currentSession = session ?: return
        val spaceId = activeSpaceId ?: return
        val operationEpoch = sessionEpoch

        mutate { it.copy(notificationsBusy = true, notificationsProblem = null) }
        viewModelScope.launch {
            if (!isCurrentSession(operationEpoch, currentSession)) return@launch
            runCatching { api.markAllNotificationsRead(spaceId, currentSession.tokens.accessToken) }
                .onSuccess {
                    if (!isCurrentSession(operationEpoch, currentSession)) return@onSuccess
                    mutate { it.copy(notificationsBusy = false) }
                    loadNotifications()
                    loadUnreadNotificationCount()
                }
                .onFailure { throwable ->
                    if (!isCurrentSession(operationEpoch, currentSession)) return@onFailure
                    mutate { it.copy(notificationsBusy = false, notificationsProblem = problemFor(throwable)) }
                }
        }
    }

    fun clearNotifications() {
        mutate {
            it.copy(
                notifications = emptyList(),
                unreadNotificationCount = 0,
                notificationsBusy = false,
                notificationsProblem = null,
            )
        }
    }

    fun loadActivity() {
        val api = contract ?: return
        val currentSession = session ?: return
        val spaceId = activeSpaceId ?: return
        val operationEpoch = sessionEpoch

        mutate { it.copy(activityBusy = true, activityProblem = null) }
        viewModelScope.launch {
            if (!isCurrentSession(operationEpoch, currentSession)) return@launch
            runCatching { api.getActivity(spaceId, currentSession.tokens.accessToken) }
                .onSuccess { page ->
                    if (!isCurrentSession(operationEpoch, currentSession)) return@onSuccess
                    mutate { it.copy(activity = page.items, activityBusy = false) }
                }
                .onFailure { throwable ->
                    if (!isCurrentSession(operationEpoch, currentSession)) return@onFailure
                    mutate { it.copy(activityBusy = false, activityProblem = problemFor(throwable)) }
                }
        }
    }

    fun clearActivity() {
        mutate { it.copy(activity = emptyList(), activityBusy = false, activityProblem = null) }
    }

    fun search(query: String) {
        if (query.isBlank()) {
            clearSearch()
            return
        }
        val api = contract ?: return
        val currentSession = session ?: return
        val spaceId = activeSpaceId ?: return
        val operationEpoch = sessionEpoch

        mutate { it.copy(searchBusy = true, searchProblem = null) }
        viewModelScope.launch {
            if (!isCurrentSession(operationEpoch, currentSession)) return@launch
            runCatching { api.search(spaceId, currentSession.tokens.accessToken, query.trim()) }
                .onSuccess { page ->
                    if (!isCurrentSession(operationEpoch, currentSession)) return@onSuccess
                    mutate { it.copy(searchResults = page.items, searchBusy = false) }
                }
                .onFailure { throwable ->
                    if (!isCurrentSession(operationEpoch, currentSession)) return@onFailure
                    mutate { it.copy(searchBusy = false, searchProblem = problemFor(throwable)) }
                }
        }
    }

    fun clearSearch() {
        mutate { it.copy(searchResults = emptyList(), searchBusy = false, searchProblem = null) }
    }

    fun loadCollections() {
        val api = contract ?: return
        val currentSession = session ?: return
        val spaceId = activeSpaceId ?: return
        val operationEpoch = sessionEpoch

        mutate { it.copy(collectionsBusy = true, collectionsProblem = null) }
        viewModelScope.launch {
            if (!isCurrentSession(operationEpoch, currentSession)) return@launch
            runCatching { api.listCollections(spaceId, currentSession.tokens.accessToken) }
                .onSuccess { page ->
                    if (!isCurrentSession(operationEpoch, currentSession)) return@onSuccess
                    mutate { it.copy(collections = page.items, collectionsBusy = false) }
                }
                .onFailure { throwable ->
                    if (!isCurrentSession(operationEpoch, currentSession)) return@onFailure
                    mutate { it.copy(collectionsBusy = false, collectionsProblem = problemFor(throwable)) }
                }
        }
    }

    fun addCollection(title: String, icon: String) {
        if (title.isBlank()) return
        val api = contract ?: return
        val currentSession = session ?: return
        val spaceId = activeSpaceId ?: return
        val operationEpoch = sessionEpoch

        mutate { it.copy(collectionsBusy = true, collectionsProblem = null) }
        viewModelScope.launch {
            if (!isCurrentSession(operationEpoch, currentSession)) return@launch
            runCatching {
                api.createCollection(
                    spaceId,
                    currentSession.tokens.accessToken,
                    CollectionCreate(title = title, icon = icon.trim().takeIf { it.isNotBlank() }),
                )
            }
                .onSuccess {
                    if (!isCurrentSession(operationEpoch, currentSession)) return@onSuccess
                    mutate { it.copy(collectionsBusy = false) }
                    loadCollections()
                }
                .onFailure { throwable ->
                    if (!isCurrentSession(operationEpoch, currentSession)) return@onFailure
                    mutate { it.copy(collectionsBusy = false, collectionsProblem = problemFor(throwable)) }
                }
        }
    }

    fun updateCollection(collection: CollectionDetail, title: String, icon: String) {
        if (title.isBlank()) return
        val api = contract ?: return
        val currentSession = session ?: return
        val spaceId = activeSpaceId ?: return
        val operationEpoch = sessionEpoch

        mutate { it.copy(collectionsBusy = true, collectionsProblem = null) }
        viewModelScope.launch {
            if (!isCurrentSession(operationEpoch, currentSession)) return@launch
            runCatching {
                api.updateCollection(
                    spaceId,
                    currentSession.tokens.accessToken,
                    collection.id,
                    collection.version,
                    CollectionUpdate(title = title, icon = icon.trim().takeIf { it.isNotBlank() }),
                )
            }
                .onSuccess {
                    if (!isCurrentSession(operationEpoch, currentSession)) return@onSuccess
                    mutate { it.copy(collectionsBusy = false) }
                    loadCollections()
                }
                .onFailure { throwable ->
                    if (!isCurrentSession(operationEpoch, currentSession)) return@onFailure
                    mutate { it.copy(collectionsBusy = false, collectionsProblem = problemFor(throwable)) }
                }
        }
    }

    fun deleteCollection(collection: CollectionDetail) {
        val api = contract ?: return
        val currentSession = session ?: return
        val spaceId = activeSpaceId ?: return
        val operationEpoch = sessionEpoch

        mutate { it.copy(collectionsBusy = true, collectionsProblem = null) }
        viewModelScope.launch {
            if (!isCurrentSession(operationEpoch, currentSession)) return@launch
            runCatching {
                api.deleteCollection(spaceId, currentSession.tokens.accessToken, collection.id, collection.version)
            }
                .onSuccess {
                    if (!isCurrentSession(operationEpoch, currentSession)) return@onSuccess
                    mutate { it.copy(collectionsBusy = false) }
                    loadCollections()
                }
                .onFailure { throwable ->
                    if (!isCurrentSession(operationEpoch, currentSession)) return@onFailure
                    mutate { it.copy(collectionsBusy = false, collectionsProblem = problemFor(throwable)) }
                }
        }
    }

    fun addCollectionItem(collection: CollectionDetail, title: String) {
        if (title.isBlank()) return
        val api = contract ?: return
        val currentSession = session ?: return
        val spaceId = activeSpaceId ?: return
        val operationEpoch = sessionEpoch

        mutate { it.copy(collectionsBusy = true, collectionsProblem = null) }
        viewModelScope.launch {
            if (!isCurrentSession(operationEpoch, currentSession)) return@launch
            runCatching {
                api.createCollectionItem(
                    spaceId,
                    currentSession.tokens.accessToken,
                    collection.id,
                    CollectionItemCreate(title = title),
                )
            }
                .onSuccess {
                    if (!isCurrentSession(operationEpoch, currentSession)) return@onSuccess
                    mutate { it.copy(collectionsBusy = false) }
                    loadCollections()
                }
                .onFailure { throwable ->
                    if (!isCurrentSession(operationEpoch, currentSession)) return@onFailure
                    mutate { it.copy(collectionsBusy = false, collectionsProblem = problemFor(throwable)) }
                }
        }
    }

    fun toggleCollectionItemCompleted(collection: CollectionDetail, item: CollectionItemDetail) {
        val api = contract ?: return
        val currentSession = session ?: return
        val spaceId = activeSpaceId ?: return
        val operationEpoch = sessionEpoch

        mutate { it.copy(collectionsBusy = true, collectionsProblem = null) }
        viewModelScope.launch {
            if (!isCurrentSession(operationEpoch, currentSession)) return@launch
            runCatching {
                api.updateCollectionItem(
                    spaceId,
                    currentSession.tokens.accessToken,
                    collection.id,
                    item.id,
                    item.version,
                    CollectionItemUpdate(completed = !item.completed),
                )
            }
                .onSuccess {
                    if (!isCurrentSession(operationEpoch, currentSession)) return@onSuccess
                    mutate { it.copy(collectionsBusy = false) }
                    loadCollections()
                }
                .onFailure { throwable ->
                    if (!isCurrentSession(operationEpoch, currentSession)) return@onFailure
                    mutate { it.copy(collectionsBusy = false, collectionsProblem = problemFor(throwable)) }
                }
        }
    }

    fun deleteCollectionItem(collection: CollectionDetail, item: CollectionItemDetail) {
        val api = contract ?: return
        val currentSession = session ?: return
        val spaceId = activeSpaceId ?: return
        val operationEpoch = sessionEpoch

        mutate { it.copy(collectionsBusy = true, collectionsProblem = null) }
        viewModelScope.launch {
            if (!isCurrentSession(operationEpoch, currentSession)) return@launch
            runCatching {
                api.deleteCollectionItem(
                    spaceId,
                    currentSession.tokens.accessToken,
                    collection.id,
                    item.id,
                    item.version,
                )
            }
                .onSuccess {
                    if (!isCurrentSession(operationEpoch, currentSession)) return@onSuccess
                    mutate { it.copy(collectionsBusy = false) }
                    loadCollections()
                }
                .onFailure { throwable ->
                    if (!isCurrentSession(operationEpoch, currentSession)) return@onFailure
                    mutate { it.copy(collectionsBusy = false, collectionsProblem = problemFor(throwable)) }
                }
        }
    }

    fun moveCollectionItemUp(collection: CollectionDetail, item: CollectionItemDetail) {
        reorderCollectionItem(collection, item, offset = -1)
    }

    fun moveCollectionItemDown(collection: CollectionDetail, item: CollectionItemDetail) {
        reorderCollectionItem(collection, item, offset = 1)
    }

    /** Same by-construction exact-set reasoning as [reorderCollectionItem] for PrivateCollection. */
    private fun reorderCollectionItem(collection: CollectionDetail, item: CollectionItemDetail, offset: Int) {
        val api = contract ?: return
        val currentSession = session ?: return
        val spaceId = activeSpaceId ?: return
        val operationEpoch = sessionEpoch

        val currentOrder = collection.items.sortedBy { it.position }.map { it.id }
        val index = currentOrder.indexOf(item.id)
        val targetIndex = index + offset
        if (index < 0 || targetIndex < 0 || targetIndex >= currentOrder.size) return
        val newOrder = currentOrder.toMutableList()
        val moved = newOrder.removeAt(index)
        newOrder.add(targetIndex, moved)

        mutate { it.copy(collectionsBusy = true, collectionsProblem = null) }
        viewModelScope.launch {
            if (!isCurrentSession(operationEpoch, currentSession)) return@launch
            runCatching {
                api.reorderCollectionItems(
                    spaceId,
                    currentSession.tokens.accessToken,
                    collection.id,
                    collection.version,
                    newOrder,
                )
            }
                .onSuccess {
                    if (!isCurrentSession(operationEpoch, currentSession)) return@onSuccess
                    mutate { it.copy(collectionsBusy = false) }
                    loadCollections()
                }
                .onFailure { throwable ->
                    if (!isCurrentSession(operationEpoch, currentSession)) return@onFailure
                    mutate { it.copy(collectionsBusy = false, collectionsProblem = problemFor(throwable)) }
                }
        }
    }

    fun clearCollections() {
        mutate { it.copy(collections = emptyList(), collectionsBusy = false, collectionsProblem = null) }
    }

    fun loadChapters() {
        val api = contract ?: return
        val currentSession = session ?: return
        val spaceId = activeSpaceId ?: return
        val operationEpoch = sessionEpoch

        mutate { it.copy(chaptersBusy = true, chaptersProblem = null) }
        viewModelScope.launch {
            if (!isCurrentSession(operationEpoch, currentSession)) return@launch
            runCatching { api.listChapters(spaceId, currentSession.tokens.accessToken) }
                .onSuccess { page ->
                    if (!isCurrentSession(operationEpoch, currentSession)) return@onSuccess
                    mutate { it.copy(chapters = page.items, chaptersBusy = false) }
                }
                .onFailure { throwable ->
                    if (!isCurrentSession(operationEpoch, currentSession)) return@onFailure
                    mutate { it.copy(chaptersBusy = false, chaptersProblem = problemFor(throwable)) }
                }
        }
    }

    fun addChapter(title: String, description: String, startOn: String, endOn: String) {
        if (title.isBlank()) return
        val api = contract ?: return
        val currentSession = session ?: return
        val spaceId = activeSpaceId ?: return
        val operationEpoch = sessionEpoch

        mutate { it.copy(chaptersBusy = true, chaptersProblem = null) }
        viewModelScope.launch {
            if (!isCurrentSession(operationEpoch, currentSession)) return@launch
            runCatching {
                api.createChapter(
                    spaceId,
                    currentSession.tokens.accessToken,
                    ChapterCreate(
                        title = title,
                        description = description.trim().takeIf { it.isNotBlank() },
                        startOn = parseHappenedOn(startOn),
                        endOn = parseHappenedOn(endOn),
                    ),
                )
            }
                .onSuccess {
                    if (!isCurrentSession(operationEpoch, currentSession)) return@onSuccess
                    mutate { it.copy(chaptersBusy = false) }
                    loadChapters()
                }
                .onFailure { throwable ->
                    if (!isCurrentSession(operationEpoch, currentSession)) return@onFailure
                    mutate { it.copy(chaptersBusy = false, chaptersProblem = problemFor(throwable)) }
                }
        }
    }

    fun updateChapter(chapter: ChapterDetail, title: String, description: String, startOn: String, endOn: String) {
        if (title.isBlank()) return
        val api = contract ?: return
        val currentSession = session ?: return
        val spaceId = activeSpaceId ?: return
        val operationEpoch = sessionEpoch

        mutate { it.copy(chaptersBusy = true, chaptersProblem = null) }
        viewModelScope.launch {
            if (!isCurrentSession(operationEpoch, currentSession)) return@launch
            runCatching {
                api.updateChapter(
                    spaceId,
                    currentSession.tokens.accessToken,
                    chapter.id,
                    chapter.version,
                    ChapterUpdate(
                        title = title,
                        description = description.trim().takeIf { it.isNotBlank() },
                        startOn = parseHappenedOn(startOn),
                        endOn = parseHappenedOn(endOn),
                    ),
                )
            }
                .onSuccess {
                    if (!isCurrentSession(operationEpoch, currentSession)) return@onSuccess
                    mutate { it.copy(chaptersBusy = false) }
                    loadChapters()
                }
                .onFailure { throwable ->
                    if (!isCurrentSession(operationEpoch, currentSession)) return@onFailure
                    mutate { it.copy(chaptersBusy = false, chaptersProblem = problemFor(throwable)) }
                }
        }
    }

    fun deleteChapter(chapter: ChapterDetail) {
        val api = contract ?: return
        val currentSession = session ?: return
        val spaceId = activeSpaceId ?: return
        val operationEpoch = sessionEpoch

        mutate { it.copy(chaptersBusy = true, chaptersProblem = null) }
        viewModelScope.launch {
            if (!isCurrentSession(operationEpoch, currentSession)) return@launch
            runCatching {
                api.deleteChapter(spaceId, currentSession.tokens.accessToken, chapter.id, chapter.version)
            }
                .onSuccess {
                    if (!isCurrentSession(operationEpoch, currentSession)) return@onSuccess
                    mutate { it.copy(chaptersBusy = false) }
                    loadChapters()
                }
                .onFailure { throwable ->
                    if (!isCurrentSession(operationEpoch, currentSession)) return@onFailure
                    mutate { it.copy(chaptersBusy = false, chaptersProblem = problemFor(throwable)) }
                }
        }
    }

    fun clearChapters() {
        mutate { it.copy(chapters = emptyList(), chaptersBusy = false, chaptersProblem = null) }
    }

    fun logout() {
        // Leaving the demo is a different exit: it also has to put the endpoint
        // back, so a later normal sign-in does not silently reach the demo.
        if (_uiState.value.demoMode) return leaveDemo()

        sessionEpoch += 1
        storyImages.reset()
        clearHeartMoments()
        clearComments()
        closeStoryItem()
        session = null
        activeSpaceId = null
        imageDrafts = emptyList()
        _uiState.value = ReferenceUiState(
            configured = config.isConfigured,
            status = message(R.string.ref_status_logged_out),
        )
        refreshInstanceAvailability()
    }

    private fun startAttachmentPreparation(
        api: ReferenceContract,
        spaceId: java.util.UUID,
        currentSession: SessionView,
        draft: ImageDraft,
    ) {
        viewModelScope.launch {
            if (!isCurrentDraft(draft.id, draft.attemptId, currentSession)) return@launch
            runCatching {
                prepareAttachment(
                    api = api,
                    spaceId = spaceId,
                    accessToken = currentSession.tokens.accessToken,
                    image = draft.image,
                    onPhase = { phase ->
                        val state = when (phase) {
                            AttachmentPreparationPhase.UPLOADING -> DraftUploadState.UPLOADING
                            AttachmentPreparationPhase.VALIDATING -> DraftUploadState.VALIDATING
                            AttachmentPreparationPhase.READY -> DraftUploadState.VALIDATING
                        }
                        updateDraft(draft.id, draft.attemptId, currentSession) {
                            it.copy(uploadState = state)
                        }
                    },
                )
            }.onSuccess { prepared ->
                updateDraft(draft.id, draft.attemptId, currentSession) {
                    it.copy(
                        uploadState = DraftUploadState.READY,
                        preparedAttachment = prepared,
                    )
                }
            }.onFailure {
                updateDraft(draft.id, draft.attemptId, currentSession) {
                    it.copy(
                        uploadState = DraftUploadState.FAILED,
                        preparedAttachment = null,
                    )
                }
            }
        }
    }

    private fun updateDraft(
        draftId: Long,
        attemptId: Long,
        currentSession: SessionView,
        update: (ImageDraft) -> ImageDraft,
    ): Boolean {
        if (!isCurrentSession(sessionEpoch, currentSession)) return false
        val index = imageDrafts.indexOfFirst { it.id == draftId && it.attemptId == attemptId }
        if (index < 0) return false
        imageDrafts = imageDrafts.toMutableList().also { drafts ->
            drafts[index] = update(drafts[index])
        }
        publishDrafts()
        return true
    }

    private fun isCurrentDraft(
        draftId: Long,
        attemptId: Long,
        currentSession: SessionView,
    ): Boolean =
        session === currentSession && imageDrafts.any { it.id == draftId && it.attemptId == attemptId }

    private fun isCurrentSession(epoch: Long, currentSession: SessionView): Boolean =
        sessionEpoch == epoch && session === currentSession

    private fun publishDrafts(
        status: UiMessage? = draftStatus(),
        error: UiMessage? = draftError(),
    ) {
        mutate {
            it.copy(
                draftImages = imageDrafts.map { draft ->
                    DraftImageUiItem(
                        id = draft.id,
                        displayName = draft.image.displayName,
                        bytes = draft.image.bytes,
                        uploadState = draft.uploadState,
                    )
                },
                status = status,
                error = error,
            )
        }
    }

    private fun draftStatus(): UiMessage? = when {
        imageDrafts.any { it.uploadState == DraftUploadState.UPLOADING } ->
            message(R.string.ref_status_images_uploading)
        imageDrafts.any { it.uploadState == DraftUploadState.VALIDATING } ->
            message(R.string.ref_status_images_validating)
        imageDrafts.isNotEmpty() && imageDrafts.all { it.uploadState == DraftUploadState.READY } ->
            message(R.string.ref_status_images_ready)
        else -> null
    }

    private fun draftError(): UiMessage? =
        if (imageDrafts.any { it.uploadState == DraftUploadState.FAILED }) {
            message(R.string.ref_error_image_upload_failed)
        } else {
            null
        }

    private fun configurationError() {
        setError(message(R.string.ref_not_configured))
    }

    private fun setError(message: UiMessage) {
        mutate { it.copy(busy = false, error = message, status = null) }
    }

    private fun failure(resourceId: Int, clearBusy: Boolean = true) {
        mutate {
            it.copy(
                busy = if (clearBusy) false else it.busy,
                error = message(resourceId),
                status = null,
            )
        }
    }

    private fun profileFailure(resourceId: Int) {
        mutate {
            it.copy(
                profile = it.profile.copy(
                    loading = false,
                    busy = false,
                    error = message(resourceId),
                    status = null,
                ),
            )
        }
    }

    private inline fun mutate(update: (ReferenceUiState) -> ReferenceUiState) {
        _uiState.value = update(_uiState.value)
    }

    /** Null for a blank date, which is allowed, and for an unparseable one. */
    private fun parseHappenedOn(text: String): LocalDate? =
        if (text.isBlank()) null else runCatching { LocalDate.parse(text.trim()) }.getOrNull()

    private fun message(resourceId: Int, vararg args: Any): UiMessage =
        UiMessage(resourceId = resourceId, args = args.toList())
}
