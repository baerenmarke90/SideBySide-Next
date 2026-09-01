package de.sidebyside.next.reference

import android.content.Context
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
import androidx.lifecycle.ViewModelProvider
import androidx.lifecycle.viewmodel.compose.viewModel
import androidx.lifecycle.viewmodel.initializer
import androidx.lifecycle.viewmodel.viewModelFactory
import androidx.navigation.NavType
import androidx.navigation.compose.composable
import androidx.navigation.compose.rememberNavController
import androidx.navigation.navArgument
import de.sidebyside.next.demo.DemoBanner
import de.sidebyside.next.invitation.AwaitingSpaceScreen
import de.sidebyside.next.invitation.InvitationsScreen
import de.sidebyside.next.design.MinimumTouchTarget
import de.sidebyside.next.design.FrauncesFamily
import de.sidebyside.next.design.SideBySideTheme
import de.sidebyside.next.people.ImportantDatesScreen
import de.sidebyside.next.people.RelatedPersonsScreen
import de.sidebyside.next.profile.ProfilePreferencesScreen
import de.sidebyside.next.profile.ProfileSettingsContent
import de.sidebyside.next.shell.AppDestination
import de.sidebyside.next.shell.AppNavigation
import de.sidebyside.next.plan.PlanScreen
import de.sidebyside.next.today.TodayScreen
import de.sidebyside.next.shell.MoreScreen
import de.sidebyside.next.shell.ShellSurface
import de.sidebyside.next.story.HeartMomentsScreen
import de.sidebyside.next.story.MemoryComments
import de.sidebyside.next.story.MemoryScreen
import de.sidebyside.next.story.MilestoneScreen
import de.sidebyside.next.story.SharedHeartMomentScreen
import de.sidebyside.next.story.StoryScreen
import kotlinx.coroutines.launch
import sidebyside.api.models.ProfileVisibility

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

/**
 * Wires a real, Context-backed [SharedPreferencesSpaceStore] into the
 * ViewModel default construction path used by `viewModel()`, which — unlike
 * every other constructor default here — cannot be a plain default parameter
 * because it needs a [Context] the ViewModel class itself never holds.
 */
private fun referenceViewModelFactory(context: Context): ViewModelProvider.Factory =
    viewModelFactory {
        initializer {
            ReferenceViewModel(spaceStore = SharedPreferencesSpaceStore(context))
        }
    }

@Composable
private fun ReferenceFlowRoute(
    referenceViewModel: ReferenceViewModel = viewModel(factory = referenceViewModelFactory(LocalContext.current)),
) {
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

    // An authenticated account with no Space yet is neither signed out nor
    // signed in in the sense the rest of the shell means; it gets its own
    // surface rather than falling into the entry form or the navigated shell.
    if (state.awaitingSpace) {
        ShellSurface {
            AwaitingSpaceScreen(
                busy = state.invitationBusy,
                problem = state.invitationProblem,
                onAcceptInvitation = referenceViewModel::acceptInvitation,
                onSignOut = signOut,
            )
        }
        return
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
            ) { openMemory, openMilestone, openHeartMoment ->
                StoryDestination(
                    state = state,
                    viewModel = referenceViewModel,
                    onPickImage = pickImage,
                    onSignOut = signOut,
                    onOpenMemory = openMemory,
                    onOpenMilestone = openMilestone,
                    onOpenHeartMoment = openHeartMoment,
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
    ) { openMemory, openMilestone, openHeartMoment ->
        StoryDestination(
            state = state,
            viewModel = referenceViewModel,
            onPickImage = pickImage,
            onSignOut = signOut,
            onOpenMemory = openMemory,
            onOpenMilestone = openMilestone,
            onOpenHeartMoment = openHeartMoment,
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
    story: @Composable (
        onOpenMemory: (java.util.UUID) -> Unit,
        onOpenMilestone: (java.util.UUID) -> Unit,
        onOpenHeartMoment: (java.util.UUID) -> Unit,
    ) -> Unit,
) {
    val navController = rememberNavController()
    AppNavigation(
        // Planen joins now that #419 put something behind it; a destination
        // with nothing behind it would be dead navigation.
        // Heute leads, as the Information Architecture has it; #421 put
        // something behind it.
        destinations = listOf(
            AppDestination.Today,
            AppDestination.Story,
            AppDestination.Plan,
            AppDestination.More,
        ),
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
                    memoryId?.let { viewModel.loadComments(MEMORY_COMMENTS, it) }
                }
                DisposableEffect(memoryId) {
                    onDispose {
                        viewModel.closeMemory()
                        viewModel.clearComments()
                    }
                }

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
                    comments = memoryId?.let { id ->
                        {
                            MemoryComments(
                                comments = state.comments,
                                accountId = state.accountId,
                                busy = state.commentsBusy,
                                problem = state.commentsProblem,
                                onAdd = { body ->
                                    viewModel.addComment(MEMORY_COMMENTS, id, body)
                                },
                                onEdit = { commentId, body ->
                                    viewModel.editComment(MEMORY_COMMENTS, id, commentId, body)
                                },
                                onDelete = { commentId ->
                                    viewModel.removeComment(MEMORY_COMMENTS, id, commentId)
                                },
                                onLoadMore = { viewModel.loadMoreComments(MEMORY_COMMENTS, id) }
                                    .takeIf { state.commentsHaveMore },
                            )
                        }
                    },
                )
            }

            composable(
                route = MILESTONE_ROUTE,
                arguments = listOf(navArgument(ITEM_ID_ARGUMENT) { type = NavType.StringType }),
            ) { entry ->
                val id = entry.arguments?.getString(ITEM_ID_ARGUMENT)
                    ?.let { runCatching { java.util.UUID.fromString(it) }.getOrNull() }

                LaunchedEffect(id, state.activeSpaceId) {
                    id?.let(viewModel::openMilestone)
                    id?.let { viewModel.loadComments(MILESTONE_COMMENTS, it) }
                }
                DisposableEffect(id) {
                    onDispose {
                        viewModel.closeStoryItem()
                        viewModel.clearComments()
                    }
                }

                MilestoneScreen(
                    milestone = state.openMilestone,
                    busy = state.memoryBusy,
                    problem = state.memoryProblem,
                    gone = state.openMemoryGone,
                    editing = state.editingMemory,
                    savedMessage = state.memoryStatus
                        ?.let { stringResource(it.resourceId, *it.args.toTypedArray()) },
                    onBack = { controller.popBackStack() },
                    onBeginEditing = viewModel::beginEditingMemory,
                    onCancelEditing = viewModel::cancelEditingMemory,
                    onSave = viewModel::saveMilestone,
                    onDelete = viewModel::deleteMilestone,
                    comments = id?.let { parentId ->
                        {
                            MemoryComments(
                                comments = state.comments,
                                accountId = state.accountId,
                                busy = state.commentsBusy,
                                problem = state.commentsProblem,
                                onAdd = { body ->
                                    viewModel.addComment(MILESTONE_COMMENTS, parentId, body)
                                },
                                onEdit = { commentId, body ->
                                    viewModel.editComment(
                                        MILESTONE_COMMENTS,
                                        parentId,
                                        commentId,
                                        body,
                                    )
                                },
                                onDelete = { commentId ->
                                    viewModel.removeComment(
                                        MILESTONE_COMMENTS,
                                        parentId,
                                        commentId,
                                    )
                                },
                                onLoadMore = {
                                    viewModel.loadMoreComments(MILESTONE_COMMENTS, parentId)
                                }.takeIf { state.commentsHaveMore },
                            )
                        }
                    },
                )
            }

            composable(
                route = HEART_MOMENT_ROUTE,
                arguments = listOf(navArgument(ITEM_ID_ARGUMENT) { type = NavType.StringType }),
            ) { entry ->
                val id = entry.arguments?.getString(ITEM_ID_ARGUMENT)
                    ?.let { runCatching { java.util.UUID.fromString(it) }.getOrNull() }

                LaunchedEffect(id, state.activeSpaceId) {
                    id?.let(viewModel::openSharedHeartMoment)
                    id?.let { viewModel.loadComments(HEART_MOMENT_COMMENTS, it) }
                }
                DisposableEffect(id) {
                    onDispose {
                        viewModel.closeStoryItem()
                        viewModel.clearComments()
                    }
                }

                SharedHeartMomentScreen(
                    moment = state.openSharedHeartMoment,
                    imageStore = viewModel.storyImages,
                    generation = viewModel.storyGeneration,
                    problem = state.memoryProblem,
                    onBack = { controller.popBackStack() },
                    comments = id?.let { parentId ->
                        {
                            MemoryComments(
                                comments = state.comments,
                                accountId = state.accountId,
                                busy = state.commentsBusy,
                                problem = state.commentsProblem,
                                onAdd = { body ->
                                    viewModel.addComment(HEART_MOMENT_COMMENTS, parentId, body)
                                },
                                onEdit = { commentId, body ->
                                    viewModel.editComment(
                                        HEART_MOMENT_COMMENTS,
                                        parentId,
                                        commentId,
                                        body,
                                    )
                                },
                                onDelete = { commentId ->
                                    viewModel.removeComment(
                                        HEART_MOMENT_COMMENTS,
                                        parentId,
                                        commentId,
                                    )
                                },
                                onLoadMore = {
                                    viewModel.loadMoreComments(HEART_MOMENT_COMMENTS, parentId)
                                }.takeIf { state.commentsHaveMore },
                            )
                        }
                    },
                )
            }

            composable(INVITATIONS_ROUTE) {
                LaunchedEffect(state.activeSpaceId) { viewModel.loadInvitations() }
                DisposableEffect(Unit) { onDispose(viewModel::clearInvitations) }

                InvitationsScreen(
                    invitations = state.issuedInvitations,
                    issuedToken = state.issuedInvitationToken,
                    busy = state.invitationBusy,
                    problem = state.invitationProblem,
                    onBack = { controller.popBackStack() },
                    onCreate = viewModel::createInvitation,
                    onDismissToken = viewModel::dismissIssuedInvitationToken,
                    onRevoke = viewModel::revokeInvitation,
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

            composable(RELATED_PERSONS_ROUTE) {
                // Deliberately no dispose-time clear here, unlike HeartMoments:
                // opening a person's ImportantDates navigates forward to a
                // child route that reads this same list for the person's
                // name, and clearing on leave wiped it before that screen
                // could render. Every session-changing event already calls
                // clearRelatedPersons() directly, so nothing leaks across
                // sign-in/demo/Space boundaries without this.
                LaunchedEffect(state.activeSpaceId) { viewModel.loadRelatedPersons() }

                RelatedPersonsScreen(
                    people = state.relatedPersons,
                    busy = state.relatedPersonsBusy,
                    problem = state.relatedPersonsProblem,
                    onBack = { controller.popBackStack() },
                    onAdd = viewModel::addRelatedPerson,
                    onOpenDates = { personId ->
                        controller.navigate("people/related-persons/$personId/important-dates")
                    },
                    onDelete = viewModel::deleteRelatedPerson,
                )
            }

            composable(
                route = IMPORTANT_DATES_ROUTE,
                arguments = listOf(navArgument(PERSON_ID_ARGUMENT) { type = NavType.StringType }),
            ) { entry ->
                val personId = entry.arguments?.getString(PERSON_ID_ARGUMENT)
                    ?.let { runCatching { java.util.UUID.fromString(it) }.getOrNull() }
                val person = state.relatedPersons.firstOrNull { it.id == personId }

                LaunchedEffect(personId, state.activeSpaceId) {
                    personId?.let(viewModel::loadImportantDates)
                }

                ImportantDatesScreen(
                    personName = person?.displayName.orEmpty(),
                    dates = state.personImportantDates,
                    busy = state.relatedPersonsBusy,
                    problem = state.relatedPersonsProblem,
                    onBack = { controller.popBackStack() },
                    onAdd = { label, type, date, repeats, visibility ->
                        personId?.let {
                            viewModel.addImportantDate(it, label, type, date, repeats, visibility)
                        }
                    },
                    onDelete = { dateId ->
                        personId?.let { viewModel.deleteImportantDate(it, dateId) }
                    },
                )
            }

            composable(PREFERENCES_ROUTE) {
                LaunchedEffect(state.activeSpaceId) { viewModel.loadProfilePreferences() }

                val selfId = state.accountId
                val partnerAccountId = state.profile.partner?.accountId

                ProfilePreferencesScreen(
                    selfPreferences = state.profile.self?.preferences.orEmpty(),
                    partnerPreferences = state.profile.partner?.preferences.orEmpty(),
                    privateNotes = state.profile.preferences.filter {
                        it.visibility == ProfileVisibility.PRIVATE_PARTNER_NOTE
                    },
                    partnerName = state.profile.partner?.displayName,
                    busy = state.profile.preferencesBusy,
                    problem = state.profile.preferencesProblem,
                    onBack = { controller.popBackStack() },
                    onAddSelf = { category, topic, sentiment, value ->
                        selfId?.let {
                            viewModel.addProfilePreference(
                                it,
                                ProfileVisibility.SELF_PROFILE,
                                category,
                                topic,
                                sentiment,
                                value,
                            )
                        }
                    },
                    onAddPrivateNote = { category, topic, sentiment, value ->
                        partnerAccountId?.let {
                            viewModel.addProfilePreference(
                                it,
                                ProfileVisibility.PRIVATE_PARTNER_NOTE,
                                category,
                                topic,
                                sentiment,
                                value,
                            )
                        }
                    },
                    onEdit = { preference, category, topic, sentiment, value ->
                        viewModel.updateProfilePreference(preference, category, topic, sentiment, value)
                    },
                    onDelete = viewModel::deleteProfilePreference,
                )
            }
        },
    ) { destination ->
        when (destination) {
            AppDestination.Today -> {
                LaunchedEffect(state.activeSpaceId) { viewModel.loadToday() }
                TodayScreen(
                    dashboard = state.dashboard,
                    busy = state.todayBusy,
                    problem = state.todayProblem,
                    gestureSent = state.thinkingOfYouSent,
                    onSendThinkingOfYou = viewModel::sendThinkingOfYou,
                )
            }

            AppDestination.Plan -> {
                LaunchedEffect(state.activeSpaceId) { viewModel.loadPlanning() }
                PlanScreen(
                    wishes = state.openWishes,
                    plans = state.plans,
                    busy = state.planningBusy,
                    problem = state.planningProblem,
                    onAddWish = viewModel::addWish,
                    onPlanWish = { wishId ->
                        // The plan starts from the wish's own words; giving it
                        // more belongs to the plan, not to this tap.
                        viewModel.planWish(wishId, "", "")
                    },
                    onRemoveWish = viewModel::removeWish,
                    onSchedule = viewModel::schedulePlan,
                    onUnschedule = viewModel::unschedulePlan,
                    onComplete = viewModel::completePlan,
                    onReturnToWish = viewModel::returnPlanToWish,
                    onDeletePlan = viewModel::deletePlan,
                )
            }

            AppDestination.More -> {
                LaunchedEffect(state.activeSpaceId) {
                    if (state.activeSpaceId != null) viewModel.refreshProfile()
                }
                LaunchedEffect(state.availableSpaces) { viewModel.loadSpaceNames() }
                MoreScreen(
                    onSignOut = onSignOut,
                    onOpenHeartMoments = { navController.navigate(HEART_MOMENTS_ROUTE) },
                    onOpenInvitations = { navController.navigate(INVITATIONS_ROUTE) },
                    onOpenRelatedPersons = { navController.navigate(RELATED_PERSONS_ROUTE) },
                    onOpenPreferences = { navController.navigate(PREFERENCES_ROUTE) },
                    signOutEnabled = !state.busy && !state.profile.busy,
                    spaces = state.availableSpaces,
                    spacePartnerNames = state.spacePartnerNames,
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

            else -> story(
                { memoryId -> navController.navigate("story/memories/$memoryId") },
                { id -> navController.navigate("story/milestones/$id") },
                { id -> navController.navigate("story/heart-moments/$id") },
            )
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
private const val INVITATIONS_ROUTE = "more/invitations"

private const val ITEM_ID_ARGUMENT = "itemId"
private const val MILESTONE_ROUTE = "story/milestones/{$ITEM_ID_ARGUMENT}"
private const val HEART_MOMENT_ROUTE = "story/heart-moments/{$ITEM_ID_ARGUMENT}"

private const val RELATED_PERSONS_ROUTE = "people/related-persons"
private const val PERSON_ID_ARGUMENT = "personId"
private const val IMPORTANT_DATES_ROUTE =
    "people/related-persons/{$PERSON_ID_ARGUMENT}/important-dates"

private const val PREFERENCES_ROUTE = "profile/preferences"

private val MEMORY_COMMENTS = ReferenceContract.CommentParent.MEMORY
private val MILESTONE_COMMENTS = ReferenceContract.CommentParent.MILESTONE
private val HEART_MOMENT_COMMENTS = ReferenceContract.CommentParent.HEART_MOMENT

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
    onOpenMilestone: (java.util.UUID) -> Unit,
    onOpenHeartMoment: (java.util.UUID) -> Unit,
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
        onOpenMilestone = onOpenMilestone,
        onOpenHeartMoment = onOpenHeartMoment,
        onLoadMore = viewModel::loadMoreStory.takeIf { state.storyHasMore },
        loadingMore = state.storyLoadingMore,
    ) {
        Column(
            verticalArrangement = Arrangement.spacedBy(SideBySideTheme.spacing.step3),
        ) {
            Text(
                text = stringResource(R.string.story_title),
                // An editorial moment, which is what the delivered display face
                // is for. The size stays the token scale's; only the family
                // changes.
                style = MaterialTheme.typography.headlineMedium
                    .copy(fontFamily = FrauncesFamily),
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
