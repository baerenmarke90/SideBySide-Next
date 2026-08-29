package de.sidebyside.next.reference

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import java.time.LocalDate
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.launch
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

data class ReferenceUiState(
    val configured: Boolean = false,
    val loggedIn: Boolean = false,
    val busy: Boolean = false,
    val status: UiMessage? = null,
    val error: UiMessage? = null,
    val selectedImageName: String? = null,
    val selectedImageBytes: ByteArray? = null,
    val imageUploadState: DraftUploadState? = null,
    val lastMemoryTitle: String? = null,
    val lastMemoryBody: String? = null,
    val lastImageBytes: ByteArray? = null,
    val storyItems: List<StoryItem> = emptyList(),
)

class ReferenceViewModel(
    private val config: ReferenceConfig = ReferenceConfig.fromBuildConfig(),
    api: ReferenceContract? = null,
) : ViewModel() {
    private val contract: ReferenceContract? = api ?: config.apiBaseUrl.takeIf(String::isNotBlank)?.let(::OkHttpReferenceApi)
    private var session: SessionView? = null
    private var selectedImage: SelectedImage? = null
    private var preparedAttachment: PreparedAttachment? = null
    private var sessionEpoch: Long = 0
    private var imageEpoch: Long = 0

    private val _uiState = MutableStateFlow(ReferenceUiState(configured = config.isConfigured))
    val uiState: StateFlow<ReferenceUiState> = _uiState.asStateFlow()

    fun signIn(email: String, password: String) {
        val api = contract ?: return configurationError()
        if (!config.isConfigured) return configurationError()
        if (email.isBlank() || password.isBlank()) {
            setError(message(R.string.ref_error_credentials_required))
            return
        }

        sessionEpoch += 1
        imageEpoch += 1
        val attemptEpoch = sessionEpoch
        viewModelScope.launch {
            if (attemptEpoch != sessionEpoch) return@launch
            mutate { it.copy(busy = true, error = null, status = message(R.string.ref_login_pending)) }
            runCatching { api.signIn(email.trim(), password) }
                .onSuccess { signedIn ->
                    if (attemptEpoch != sessionEpoch) return@onSuccess
                    session = signedIn
                    selectedImage = null
                    preparedAttachment = null
                    mutate {
                        it.copy(
                            loggedIn = true,
                            busy = false,
                            status = message(R.string.ref_status_logged_in),
                            error = null,
                            selectedImageName = null,
                            selectedImageBytes = null,
                            imageUploadState = null,
                            lastMemoryTitle = null,
                            lastMemoryBody = null,
                            lastImageBytes = null,
                            storyItems = emptyList(),
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

    fun beginImageSelection(): Long? = session?.let { sessionEpoch }

    fun selectImage(image: SelectedImage, selectionEpoch: Long) {
        val api = contract ?: return configurationError()
        val currentSession = session ?: return
        val spaceId = config.spaceId ?: return configurationError()
        if (selectionEpoch != sessionEpoch) return

        imageEpoch += 1
        val draftEpoch = imageEpoch
        selectedImage = image
        preparedAttachment = null
        mutate {
            it.copy(
                selectedImageName = image.displayName,
                selectedImageBytes = image.bytes,
                imageUploadState = DraftUploadState.UPLOADING,
                error = null,
                status = message(R.string.ref_status_image_uploading),
            )
        }

        viewModelScope.launch {
            if (!isCurrentImageSelection(draftEpoch, currentSession, image)) return@launch
            runCatching {
                prepareAttachment(
                    api = api,
                    spaceId = spaceId,
                    accessToken = currentSession.tokens.accessToken,
                    image = image,
                    onPhase = { phase ->
                        if (isCurrentImageSelection(draftEpoch, currentSession, image)) {
                            mutate {
                                it.copy(
                                    imageUploadState = when (phase) {
                                        AttachmentPreparationPhase.UPLOADING -> DraftUploadState.UPLOADING
                                        AttachmentPreparationPhase.VALIDATING -> DraftUploadState.VALIDATING
                                        AttachmentPreparationPhase.READY -> DraftUploadState.READY
                                    },
                                    status = when (phase) {
                                        AttachmentPreparationPhase.UPLOADING -> message(R.string.ref_status_image_uploading)
                                        AttachmentPreparationPhase.VALIDATING -> message(R.string.ref_status_image_validating)
                                        AttachmentPreparationPhase.READY -> message(R.string.ref_status_image_ready)
                                    },
                                )
                            }
                        }
                    },
                )
            }.onSuccess { prepared ->
                if (!isCurrentImageSelection(draftEpoch, currentSession, image)) return@onSuccess
                preparedAttachment = prepared
                mutate {
                    it.copy(
                        imageUploadState = DraftUploadState.READY,
                        status = message(R.string.ref_status_image_ready),
                        error = null,
                    )
                }
            }.onFailure {
                if (!isCurrentImageSelection(draftEpoch, currentSession, image)) return@onFailure
                preparedAttachment = null
                mutate {
                    it.copy(
                        imageUploadState = DraftUploadState.FAILED,
                        status = null,
                        error = message(R.string.ref_error_image_upload_failed),
                    )
                }
            }
        }
    }

    fun setImageError(throwable: Throwable, selectionEpoch: Long) {
        if (session == null || selectionEpoch != sessionEpoch) return
        imageEpoch += 1
        selectedImage = null
        preparedAttachment = null
        val error = throwable.message?.takeIf(String::isNotBlank)?.let {
            message(R.string.ref_error_image_selection_detail, it)
        } ?: message(R.string.ref_error_image_selection_failed)
        mutate {
            it.copy(
                selectedImageName = null,
                selectedImageBytes = null,
                imageUploadState = null,
                error = error,
                status = null,
            )
        }
    }

    fun retrySelectedImage() {
        val image = selectedImage ?: return
        selectImage(image, sessionEpoch)
    }

    fun removeSelectedImage() {
        imageEpoch += 1
        selectedImage = null
        preparedAttachment = null
        mutate {
            it.copy(
                selectedImageName = null,
                selectedImageBytes = null,
                imageUploadState = null,
                error = null,
                status = message(R.string.ref_status_image_removed),
            )
        }
    }

    fun createMemory(title: String, body: String, happenedOnText: String) {
        val api = contract ?: return configurationError()
        val currentSession = session ?: run {
            setError(message(R.string.ref_error_login_required))
            return
        }
        val image = selectedImage
        val attachment = preparedAttachment
        val spaceId = config.spaceId ?: return configurationError()
        if (title.isBlank()) {
            setError(message(R.string.ref_error_memory_fields_required))
            return
        }
        if (image != null && attachment == null) {
            setError(message(R.string.ref_error_image_not_ready))
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
                    attachments = attachment?.let(::listOf).orEmpty(),
                )
            }.onSuccess { result ->
                if (!isCurrentSession(operationEpoch, currentSession)) return@onSuccess
                imageEpoch += 1
                selectedImage = null
                preparedAttachment = null
                mutate {
                    it.copy(
                        busy = false,
                        status = message(R.string.ref_status_save_success),
                        error = null,
                        selectedImageName = null,
                        selectedImageBytes = null,
                        imageUploadState = null,
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
        val spaceId = config.spaceId ?: return
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

    fun logout() {
        sessionEpoch += 1
        imageEpoch += 1
        session = null
        selectedImage = null
        preparedAttachment = null
        _uiState.value = ReferenceUiState(
            configured = config.isConfigured,
            status = message(R.string.ref_status_logged_out),
        )
    }

    private fun isCurrentImageSelection(
        epoch: Long,
        currentSession: SessionView,
        image: SelectedImage,
    ): Boolean =
        imageEpoch == epoch && session === currentSession && selectedImage === image

    private fun isCurrentSession(epoch: Long, currentSession: SessionView): Boolean =
        sessionEpoch == epoch && session === currentSession

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

    private inline fun mutate(update: (ReferenceUiState) -> ReferenceUiState) {
        _uiState.value = update(_uiState.value)
    }

    private fun message(resourceId: Int, vararg args: Any): UiMessage =
        UiMessage(resourceId = resourceId, args = args.toList())
}
