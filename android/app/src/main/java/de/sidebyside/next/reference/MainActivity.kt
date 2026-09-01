package de.sidebyside.next.reference

import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.BackHandler
import androidx.activity.compose.rememberLauncherForActivityResult
import androidx.activity.compose.setContent
import androidx.activity.enableEdgeToEdge
import androidx.activity.result.PickVisualMediaRequest
import androidx.activity.result.contract.ActivityResultContracts
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.WindowInsets
import androidx.compose.foundation.layout.WindowInsetsSides
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.heightIn
import androidx.compose.foundation.layout.only
import androidx.compose.foundation.layout.safeDrawing
import androidx.compose.foundation.layout.windowInsetsPadding
import androidx.compose.material3.FilledTonalButton
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.DisposableEffect
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.collectAsState
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.rememberCoroutineScope
import androidx.compose.runtime.saveable.rememberSaveable
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.res.stringResource
import androidx.compose.ui.semantics.heading
import androidx.compose.ui.semantics.semantics
import androidx.lifecycle.viewmodel.compose.viewModel
import androidx.navigation.NavType
import androidx.navigation.compose.composable
import androidx.navigation.compose.rememberNavController
import androidx.navigation.navArgument
import de.sidebyside.next.demo.DemoBanner
import de.sidebyside.next.design.MinimumTouchTarget
import de.sidebyside.next.design.SideBySideTheme
import de.sidebyside.next.profile.ProfileSettingsContent
import de.sidebyside.next.shell.AppDestination
import de.sidebyside.next.shell.AppNavigation
import de.sidebyside.next.shell.MoreScreen
import de.sidebyside.next.shell.ShellSurface
import de.sidebyside.next.story.HeartMomentsScreen
import de.sidebyside.next.story.MemoryScreen
import de.sidebyside.next.story.StoryScreen
import kotlinx.coroutines.launch

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
    var profileAvatarSelectionEpoch by remember { mutableStateOf<Long?>(null) }
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
    val profileAvatarPicker = rememberLauncherForActivityResult(ActivityResultContracts.PickVisualMedia()) { uri ->
        val selectionEpoch = profileAvatarSelectionEpoch
        profileAvatarSelectionEpoch = null
        if (uri != null && selectionEpoch != null) {
            scope.launch {
                runCatching { loadSelectedImage(context, uri) }
                    .onSuccess { image ->
                        referenceViewModel.setProfileAvatar(image, selectionEpoch)
                    }
                    .onFailure { throwable ->
                        referenceViewModel.setProfileAvatarSelectionError(throwable, selectionEpoch)
                    }
            }
        }
    }

    val signOut = {
        imageSelectionEpoch = null
        profileAvatarSelectionEpoch = null
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
    val pickProfileAvatar = {
        referenceViewModel.beginProfileAvatarSelection()?.let { selectionEpoch ->
            profileAvatarSelectionEpoch = selectionEpoch
            profileAvatarPicker.launch(
                PickVisualMediaRequest.Builder()
                    .setMediaType(ActivityResultContracts.PickVisualMedia.ImageOnly)
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
            DemoShell(
                state = state,
                viewModel = referenceViewModel,
                onSignOut = signOut,
                onSelectSpace = referenceViewModel::selectSpace,
                onPickProfileAvatar = pickProfileAvatar,
            ) { open ->
                StoryDestination(
                    state = state,
                    viewModel = referenceViewModel,
                    onPickImage = pickImage,
                    onSignOut = signOut,
                    onOpenMemory = open,
                )
            }
        }
        return
    }

    DemoShell(
        state = state,
        viewModel = referenceViewModel,
        onSignOut = signOut,
        onSelectSpace = referenceViewModel::selectSpace,
        onPickProfileAvatar = pickProfileAvatar,
    ) { open ->
        StoryDestination(
            state = state,
            viewModel = referenceViewModel,
            onPickImage = pickImage,
            onSignOut = signOut,
            onOpenMemory = open,
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
    viewModel: ReferenceViewModel,
    onSignOut: () -> Unit,
    onSelectSpace: (java.util.UUID) -> Unit,
    onPickProfileAvatar: () -> Unit,
    story: @Composable (onOpenMemory: (java.util.UUID) -> Unit) -> Unit,
) {
    val navController = rememberNavController()
    AppNavigation(
        destinations = listOf(AppDestination.Story, AppDestination.More),
        navController = navController,
        detailRoutes = { controller ->
            composable(
                route = MEMORY_ROUTE,
                arguments = listOf(navArgument(MEMORY_ID_ARGUMENT) { type = NavType.StringType }),
            ) { entry ->
                val memoryId = entry.arguments?.getString(MEMORY_ID_ARGUMENT)
                    ?.let { runCatching { java.util.UUID.fromString(it) }.getOrNull() }

                // Loading is tied to the route rather than to the tap, so
                // returning to this screen after process death still shows the
                // memory instead of an empty one.
                LaunchedEffect(memoryId, state.activeSpaceId) {
                    memoryId?.let(viewModel::openMemory)
                }
                DisposableEffect(memoryId) { onDispose(viewModel::closeMemory) }

                MemoryScreen(
                    memory = state.openMemory,
                    imageStore = viewModel.storyImages,
                    generation = viewModel.storyGeneration,
                    busy = state.memoryBusy,
                    problem = state.memoryProblem,
                    gone = state.openMemoryGone,
                    editing = state.editingMemory,
                    savedMessage = state.memoryStatus
                        ?.let { stringResource(it.resourceId, *it.args.toTypedArray()) },
                    onBack = { controller.popBackStack() },
                    onBeginEditing = viewModel::beginEditingMemory,
                    onCancelEditing = viewModel::cancelEditingMemory,
                    onSave = viewModel::saveMemory,
                    onDelete = viewModel::deleteMemory,
                )
            }

            composable(HEART_MOMENTS_ROUTE) {
                // Tied to the route, so returning here after process death
                // loads again instead of showing an empty list.
                LaunchedEffect(state.activeSpaceId) { viewModel.loadHeartMoments() }
                DisposableEffect(Unit) { onDispose(viewModel::clearHeartMoments) }

                HeartMomentsScreen(
                    moments = state.heartMoments,
                    busy = state.heartMomentsBusy,
                    problem = state.heartMomentsProblem,
                    statusMessage = state.heartMomentStatus
                        ?.let { stringResource(it.resourceId, *it.args.toTypedArray()) },
                    onBack = { controller.popBackStack() },
                    onCreate = { text, emotion, visibility ->
                        viewModel.createHeartMoment(text, emotion, "", visibility)
                    },
                    onChangeVisibility = viewModel::changeHeartMomentVisibility,
                    onDelete = viewModel::deleteHeartMoment,
                )
            }
        },
    ) { destination ->
        when (destination) {
            AppDestination.More -> {
                LaunchedEffect(state.activeSpaceId) {
                    if (state.activeSpaceId != null) viewModel.refreshProfile()
                }
                MoreScreen(
                    onSignOut = onSignOut,
                    onOpenHeartMoments = { navController.navigate(HEART_MOMENTS_ROUTE) },
                    signOutEnabled = !state.busy && !state.profile.busy,
                    spaces = state.availableSpaces,
                    activeSpaceId = state.activeSpaceId,
                    onSelectSpace = onSelectSpace,
                    profileContent = {
                        ProfileSettingsContent(
                            state = state.profile,
                            onRetry = viewModel::refreshProfile,
                            onSaveDisplayName = viewModel::saveProfileDisplayName,
                            onChooseAvatar = onPickProfileAvatar,
                            onRemoveAvatar = viewModel::removeProfileAvatar,
                        )
                    },
                )
            }

            else -> story { memoryId -> navController.navigate("story/memories/$memoryId") }
        }
    }
}

/**
 * Matches the Web path from
 * `docs/decisions/0003-primary-navigation-and-route-model.md`, so the Deep Link
 * registry can be built on it without a second mapping.
 */
private const val MEMORY_ID_ARGUMENT = "memoryId"
private const val MEMORY_ROUTE = "story/memories/{$MEMORY_ID_ARGUMENT}"

/** The account's own HeartMoments, private ones included. */
private const val HEART_MOMENTS_ROUTE = "story/heart-moments"

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
    onOpenMemory: (java.util.UUID) -> Unit,
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
        onOpenMemory = onOpenMemory,
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
