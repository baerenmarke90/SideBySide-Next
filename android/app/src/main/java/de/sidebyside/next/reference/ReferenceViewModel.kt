package de.sidebyside.next.reference

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import de.sidebyside.next.demo.DemoEndpoint
import de.sidebyside.next.demo.DemoPersona
import de.sidebyside.next.profile.ProfileUiState
import de.sidebyside.next.profile.loadProfileIdentity
import de.sidebyside.next.profile.removeProfileAvatar
import de.sidebyside.next.profile.updateProfileAvatar
import de.sidebyside.next.profile.updateProfileDisplayName
import de.sidebyside.next.story.StoryImageRef
import de.sidebyside.next.story.StoryImageStore
import java.time.LocalDate
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.launch
import sidebyside.api.models.AccountMembershipView
import sidebyside.api.models.AttachmentReadRequest
import sidebyside.api.models.SessionView
import sidebyside.api.models.StoryItem

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

data class DraftImageUiItem(
    val id: Long,
    val displayName: String,
    val bytes: ByteArray,
    val uploadState: DraftUploadState,
)

data class ReferenceUiState(
    val configured: Boolean = false,
    val loggedIn: Boolean = false,
    /** True while the session belongs to the public demo rather than the configured server. */
    val demoMode: Boolean = false,
    val demoPersona: DemoPersona? = null,
    /** Every Space the account may open; a choice only exists above one. */
    val availableSpaces: List<AccountMembershipView> = emptyList(),
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
    private var nextAttemptId: Long = 1

    private val _uiState = MutableStateFlow(ReferenceUiState(configured = config.isConfigured))
    val uiState: StateFlow<ReferenceUiState> = _uiState.asStateFlow()

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
                    val space = activeSpaceOf(memberships)
                    if (space == null) {
                        // Authenticated, but the account has no Space to open.
                        // That is a product state, not a sign-in failure.
                        session = null
                        return@onSuccess failure(R.string.error_no_active_space)
                    }
                    activeSpaceId = space
                    session = signedIn
                    imageDrafts = emptyList()
                    mutate {
                        it.copy(
                            loggedIn = true,
                            busy = false,
                            status = message(R.string.ref_status_logged_in),
                            error = null,
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
        session = null
        imageDrafts = emptyList()
        _uiState.value = ReferenceUiState(
            configured = config.isConfigured,
            status = message(R.string.demo_left),
        )
    }

    /**
     * The Space to open, as the server authorises it.
     *
     * Only an active membership counts; an invited or removed one must not
     * silently become the working context.
     */
    private fun activeSpaceOf(memberships: List<AccountMembershipView>): java.util.UUID? =
        activeMemberships(memberships).firstOrNull()?.spaceId

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

        sessionEpoch += 1
        storyImages.reset()
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
                        mutate { it.copy(storyItems = story.items, error = null) }
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
                        mutate { it.copy(profile = profile) }
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

    fun logout() {
        // Leaving the demo is a different exit: it also has to put the endpoint
        // back, so a later normal sign-in does not silently reach the demo.
        if (_uiState.value.demoMode) return leaveDemo()

        sessionEpoch += 1
        storyImages.reset()
        session = null
        activeSpaceId = null
        imageDrafts = emptyList()
        _uiState.value = ReferenceUiState(
            configured = config.isConfigured,
            status = message(R.string.ref_status_logged_out),
        )
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

    private fun message(resourceId: Int, vararg args: Any): UiMessage =
        UiMessage(resourceId = resourceId, args = args.toList())
}
