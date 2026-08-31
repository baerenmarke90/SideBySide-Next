package de.sidebyside.next.reference

import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.BackHandler
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
import de.sidebyside.next.design.MinimumTouchTarget
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
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.heightIn
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.material3.FilledTonalButton
import androidx.compose.runtime.saveable.rememberSaveable
import androidx.compose.ui.Alignment
import androidx.compose.ui.res.stringResource
import androidx.compose.ui.semantics.heading
import androidx.compose.ui.semantics.semantics
import de.sidebyside.next.demo.DemoBanner
import de.sidebyside.next.story.StoryScreen

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

    // Shared by the reference flow and the Story's capture step, so a picked
    // image is bound to the same session epoch either way.
    val pickImage = {
        referenceViewModel.beginImageSelection()?.let { selectionEpoch ->
            imageSelectionEpoch = selectionEpoch
            imagePicker.launch(
                PickVisualMediaRequest.Builder()
                    .setMediaType(ActivityResultContracts.PickVisualMedia.ImageOnly)
                    .setOrderedSelection(true)
                    .build(),
            )
        }
        Unit
    }

    val storyFlow = @Composable {
        ReferenceFlowScreen(
            state = state,
            onLogin = referenceViewModel::signIn,
            onLogout = signOut,
            onPickImage = pickImage,
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
        // The inset is consumed once, here, for the banner and the shell
        // together. Applied to the banner alone it would be padding for the
        // banner and then again for the shell beside it.
        Column(
            modifier = Modifier.windowInsetsPadding(
                WindowInsets.safeDrawing.only(WindowInsetsSides.Top),
            ),
        ) {
            DemoBanner(
                persona = demoPersona,
                onLeave = referenceViewModel::leaveDemo,
            )
            DemoShell(state, signOut, referenceViewModel::selectSpace) {
                StoryDestination(
                    state = state,
                    viewModel = referenceViewModel,
                    onPickImage = pickImage,
                    onSignOut = signOut,
                )
            }
        }
        return
    }

    DemoShell(state, signOut, referenceViewModel::selectSpace) {
                StoryDestination(
                    state = state,
                    viewModel = referenceViewModel,
                    onPickImage = pickImage,
                    onSignOut = signOut,
                )
            }
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
    story: @Composable () -> Unit,
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

            else -> story()
        }
    }
}

/**
 * The Story destination.
 *
 * Reading is the default and capturing is a deliberate step away from it,
 * because a couple opens their history far more often than they add to it.
 * The capture form is still the M2 reference form; giving it a product shape
 * belongs to the authoring slice.
 */
@Composable
private fun StoryDestination(
    state: ReferenceUiState,
    viewModel: ReferenceViewModel,
    onPickImage: () -> Unit,
    onSignOut: () -> Unit,
) {
    var capturing by rememberSaveable { mutableStateOf(false) }

    if (capturing) {
        // The system back gesture is how someone leaves a step like this on
        // Android; the visible action exists for anyone who does not use it.
        BackHandler { capturing = false }
        ReferenceFlowScreen(
            state = state,
            onLogin = { _, _ -> },
            onLogout = onSignOut,
            onPickImage = onPickImage,
            onCreateMemory = { title, body, date ->
                viewModel.createMemory(title, body, date)
                capturing = false
            },
            onRefreshStory = viewModel::refreshStory,
            onRetryImage = viewModel::retryImage,
            onRemoveImage = viewModel::removeImage,
            onCancelCapture = { capturing = false },
        )
        return
    }

    StoryScreen(
        items = state.storyItems,
        imageStore = viewModel.storyImages,
        generation = viewModel.storyGeneration,
    ) {
        Column(
            verticalArrangement = Arrangement.spacedBy(SideBySideTheme.spacing.step3),
        ) {
            Text(
                text = stringResource(R.string.story_title),
                style = MaterialTheme.typography.headlineMedium,
                color = SideBySideTheme.colors.textPrimary,
                modifier = Modifier.semantics { heading() },
            )
            // Below the title rather than beside it: the action's label is a
            // whole phrase, and squeezing it next to a headline wrapped both.
            FilledTonalButton(
                onClick = { capturing = true },
                enabled = !state.busy,
                modifier = Modifier.heightIn(min = MinimumTouchTarget),
            ) {
                Text(stringResource(R.string.ref_memory_heading))
            }
        }
    }
}
