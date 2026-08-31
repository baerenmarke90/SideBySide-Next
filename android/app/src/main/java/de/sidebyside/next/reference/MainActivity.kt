package de.sidebyside.next.reference

import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.enableEdgeToEdge
import androidx.activity.compose.rememberLauncherForActivityResult
import androidx.activity.compose.setContent
import androidx.activity.result.PickVisualMediaRequest
import androidx.activity.result.contract.ActivityResultContracts
import androidx.compose.runtime.Composable
import androidx.compose.runtime.collectAsState
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.rememberCoroutineScope
import androidx.compose.runtime.setValue
import androidx.compose.ui.platform.LocalContext
import androidx.lifecycle.viewmodel.compose.viewModel
import kotlinx.coroutines.launch
import de.sidebyside.next.design.SideBySideTheme
import de.sidebyside.next.shell.AppDestination
import de.sidebyside.next.shell.AppNavigation
import de.sidebyside.next.shell.MoreScreen
import de.sidebyside.next.shell.ShellSurface
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.WindowInsets
import androidx.compose.foundation.layout.WindowInsetsSides
import androidx.compose.foundation.layout.only
import androidx.compose.foundation.layout.safeDrawing
import androidx.compose.foundation.layout.windowInsetsPadding
import androidx.compose.ui.Modifier
import de.sidebyside.next.demo.DemoBanner

class MainActivity : ComponentActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        // Declared rather than inherited: targetSdk 36 draws edge to edge
        // anyway, and stating it keeps the behaviour explicit for the shell
        // that consumes the insets.
        enableEdgeToEdge()
        super.onCreate(savedInstanceState)
        setContent {
            SideBySideTheme {
                ReferenceFlowRoute()
            }
        }
    }
}

@Composable
private fun ReferenceFlowRoute(referenceViewModel: ReferenceViewModel = viewModel()) {
    val state by referenceViewModel.uiState.collectAsState()
    val context = LocalContext.current
    val scope = rememberCoroutineScope()
    var imageSelectionEpoch by remember { mutableStateOf<Long?>(null) }
    val imagePicker = rememberLauncherForActivityResult(ActivityResultContracts.PickMultipleVisualMedia()) { uris ->
        val selectionEpoch = imageSelectionEpoch
        imageSelectionEpoch = null
        if (uris.isNotEmpty() && selectionEpoch != null) {
            scope.launch {
                val images = mutableListOf<SelectedImage>()
                var firstFailure: Throwable? = null
                uris.forEach { uri ->
                    runCatching { loadSelectedImage(context, uri) }
                        .onSuccess(images::add)
                        .onFailure { throwable ->
                            if (firstFailure == null) firstFailure = throwable
                        }
                }
                if (images.isNotEmpty()) {
                    referenceViewModel.selectImages(images, selectionEpoch)
                }
                firstFailure?.let { throwable ->
                    referenceViewModel.setImageSelectionError(throwable, selectionEpoch)
                }
            }
        }
    }

    val signOut = {
        imageSelectionEpoch = null
        referenceViewModel.logout()
    }

    val storyFlow = @Composable {
        ReferenceFlowScreen(
            state = state,
            onLogin = referenceViewModel::signIn,
            onLogout = signOut,
            onPickImage = {
                referenceViewModel.beginImageSelection()?.let { selectionEpoch ->
                    imageSelectionEpoch = selectionEpoch
                    imagePicker.launch(
                        PickVisualMediaRequest.Builder()
                            .setMediaType(ActivityResultContracts.PickVisualMedia.ImageOnly)
                            .setOrderedSelection(true)
                            .build(),
                    )
                }
            },
            onCreateMemory = referenceViewModel::createMemory,
            onRefreshStory = referenceViewModel::refreshStory,
            onRetryImage = referenceViewModel::retryImage,
            onRemoveImage = referenceViewModel::removeImage,
            onEnterDemo = referenceViewModel::enterDemo,
        )
    }

    // Signed out there is nothing to navigate between, but the surface still
    // needs the window insets the shell owns.
    if (!state.loggedIn) {
        ShellSurface { storyFlow() }
        return
    }

    val demoPersona = state.demoPersona
    if (state.demoMode && demoPersona != null) {
        Column {
            DemoBanner(
                persona = demoPersona,
                onLeave = referenceViewModel::leaveDemo,
                modifier = Modifier.windowInsetsPadding(
                    WindowInsets.safeDrawing.only(WindowInsetsSides.Top),
                ),
            )
            DemoShell(state, signOut, referenceViewModel::selectSpace, storyFlow)
        }
        return
    }

    DemoShell(state, signOut, referenceViewModel::selectSpace, storyFlow)
}

/**
 * The signed-in shell.
 *
 * Only destinations that have something to show are rendered; the slice
 * contract forbids dead navigation. Heute and Planen join in their slices.
 */
@Composable
private fun DemoShell(
    state: ReferenceUiState,
    onSignOut: () -> Unit,
    onSelectSpace: (java.util.UUID) -> Unit,
    storyFlow: @Composable () -> Unit,
) {
    AppNavigation(
        destinations = listOf(AppDestination.Story, AppDestination.More),
    ) { destination ->
        when (destination) {
            AppDestination.More -> MoreScreen(
                onSignOut = onSignOut,
                signOutEnabled = !state.busy,
                spaces = state.availableSpaces,
                activeSpaceId = state.activeSpaceId,
                onSelectSpace = onSelectSpace,
            )

            else -> storyFlow()
        }
    }
}
