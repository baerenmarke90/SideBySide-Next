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

data class ReferenceUiState(
    val configured: Boolean = false,
    val loggedIn: Boolean = false,
    val busy: Boolean = false,
    val status: String = "",
    val error: String? = null,
    val selectedImageName: String? = null,
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
    private var sessionEpoch: Long = 0

    private val _uiState = MutableStateFlow(ReferenceUiState(configured = config.isConfigured))
    val uiState: StateFlow<ReferenceUiState> = _uiState.asStateFlow()

    fun signIn(email: String, password: String) {
        val api = contract ?: return configurationError()
        if (!config.isConfigured) return configurationError()
        if (email.isBlank() || password.isBlank()) {
            setError("E-Mail und Passwort werden benötigt.")
            return
        }

        sessionEpoch += 1
        val attemptEpoch = sessionEpoch
        viewModelScope.launch {
            if (attemptEpoch != sessionEpoch) return@launch
            mutate { it.copy(busy = true, error = null, status = "Anmeldung läuft …") }
            runCatching { api.signIn(email.trim(), password) }
                .onSuccess { signedIn ->
                    if (attemptEpoch != sessionEpoch) return@onSuccess
                    session = signedIn
                    mutate {
                        it.copy(
                            loggedIn = true,
                            busy = false,
                            status = "Angemeldet.",
                            error = null,
                            storyItems = emptyList(),
                        )
                    }
                    refreshStory()
                }
                .onFailure { throwable ->
                    if (attemptEpoch == sessionEpoch) {
                        failure("Anmeldung fehlgeschlagen", throwable)
                    }
                }
        }
    }

    fun selectImage(image: SelectedImage) {
        selectedImage = image
        mutate {
            it.copy(
                selectedImageName = image.displayName,
                error = null,
                status = "Bild ausgewählt: ${image.displayName}",
            )
        }
    }

    fun setImageError(throwable: Throwable) {
        selectedImage = null
        mutate {
            it.copy(
                selectedImageName = null,
                error = throwable.message ?: "Das Bild konnte nicht ausgewählt werden.",
                status = "",
            )
        }
    }

    fun createMemory(title: String, body: String, happenedOnText: String) {
        val api = contract ?: return configurationError()
        val currentSession = session ?: run {
            setError("Bitte zuerst anmelden.")
            return
        }
        val image = selectedImage ?: run {
            setError("Bitte zuerst ein Bild auswählen.")
            return
        }
        val spaceId = config.spaceId ?: return configurationError()
        if (title.isBlank() || body.isBlank()) {
            setError("Titel und Erinnerung werden benötigt.")
            return
        }
        val happenedOn = if (happenedOnText.isBlank()) {
            null
        } else {
            runCatching { LocalDate.parse(happenedOnText.trim()) }.getOrElse {
                setError("Datum bitte als JJJJ-MM-TT eingeben.")
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
                    status = "Erinnerung und Bild werden gespeichert …",
                    lastMemoryTitle = null,
                    lastMemoryBody = null,
                    lastImageBytes = null,
                )
            }
            runCatching {
                runMemoryMediaStoryFlow(
                    api = api,
                    spaceId = spaceId,
                    accessToken = currentSession.tokens.accessToken,
                    title = title.trim(),
                    body = body.trim(),
                    happenedOn = happenedOn,
                    image = image,
                )
            }.onSuccess { result ->
                if (!isCurrentSession(operationEpoch, currentSession)) return@onSuccess
                mutate {
                    it.copy(
                        busy = false,
                        status = "Erinnerung und Bild wurden über den M2-Vertrag gespeichert.",
                        error = null,
                        lastMemoryTitle = result.memory.title,
                        lastMemoryBody = result.memory.body,
                        lastImageBytes = result.imageBytes,
                        storyItems = result.story.items,
                    )
                }
            }.onFailure { throwable ->
                if (isCurrentSession(operationEpoch, currentSession)) {
                    failure("Speichern fehlgeschlagen", throwable)
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
                .onFailure { throwable ->
                    if (isCurrentSession(operationEpoch, currentSession)) {
                        failure("Story konnte nicht geladen werden", throwable, clearBusy = false)
                    }
                }
        }
    }

    fun logout() {
        sessionEpoch += 1
        session = null
        selectedImage = null
        _uiState.value = ReferenceUiState(configured = config.isConfigured, status = "Abgemeldet.")
    }

    private fun isCurrentSession(epoch: Long, currentSession: SessionView): Boolean =
        sessionEpoch == epoch && session === currentSession

    private fun configurationError() {
        setError("Der M2-Referenzflow ist operatorseitig noch nicht konfiguriert.")
    }

    private fun setError(message: String) {
        mutate { it.copy(busy = false, error = message, status = "") }
    }

    private fun failure(prefix: String, throwable: Throwable, clearBusy: Boolean = true) {
        val detail = throwable.message?.takeIf(String::isNotBlank) ?: "Unbekannter Fehler."
        mutate {
            it.copy(
                busy = if (clearBusy) false else it.busy,
                error = "$prefix: $detail",
                status = "",
            )
        }
    }

    private inline fun mutate(update: (ReferenceUiState) -> ReferenceUiState) {
        _uiState.value = update(_uiState.value)
    }
}
