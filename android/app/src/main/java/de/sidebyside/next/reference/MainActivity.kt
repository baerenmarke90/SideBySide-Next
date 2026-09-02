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
import androidx.compose.material3.SnackbarHostState
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
import de.sidebyside.next.shell.QuickCreateFab
import de.sidebyside.next.shell.navigateToPrimary
import de.sidebyside.next.chapter.ChapterContentScreen
import de.sidebyside.next.chapter.ChaptersScreen
import de.sidebyside.next.collection.CollectionDetailScreen
import de.sidebyside.next.collection.CollectionsScreen
import de.sidebyside.next.place.PlaceRelationsScreen
import de.sidebyside.next.place.PlacesScreen
import de.sidebyside.next.notifications.NotificationsScreen
import de.sidebyside.next.privatearea.GiftIdeasScreen
import de.sidebyside.next.privatearea.PrivateAreaScreen
import de.sidebyside.next.privatearea.PrivateCollectionDetailScreen
import de.sidebyside.next.privatearea.PrivateCollectionsScreen
import de.sidebyside.next.privatearea.PrivateNotesScreen
import de.sidebyside.next.search.SearchScreen
import de.sidebyside.next.plan.PlanScreen
import de.sidebyside.next.activity.ActivityScreen
import de.sidebyside.next.today.TodayScreen
import de.sidebyside.next.shell.MoreScreen
import de.sidebyside.next.shell.ShellSurface
import de.sidebyside.next.story.HeartMomentsScreen
import de.sidebyside.next.story.MemoryComments
import de.sidebyside.next.story.MemoryScreen
import de.sidebyside.next.story.MilestoneCreateScreen
import de.sidebyside.next.story.MilestoneScreen
import de.sidebyside.next.story.SharedHeartMomentScreen
import de.sidebyside.next.story.StoryScreen
import kotlinx.coroutines.launch
import sidebyside.api.models.EngagementTarget
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
            val database = de.sidebyside.next.cache.ReadCacheDatabase.getInstance(context)
            val connectivityTracker = de.sidebyside.next.connectivity.ConnectivityTracker()
            ReferenceViewModel(
                spaceStore = SharedPreferencesSpaceStore(context),
                productReadCache = de.sidebyside.next.cache.ProductReadCache(
                    database.productCacheDao(),
                    database.cacheContextDao(),
                    database.protectedCacheDao(),
                    de.sidebyside.next.cache.AndroidKeystoreProtectedPayloadCipher(),
                ),
                connectivityTracker = connectivityTracker,
                apiFactory = { baseUrl -> OkHttpReferenceApi(baseUrl, connectivityTracker = connectivityTracker) },
            )
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
    val snackbarHostState = remember { SnackbarHostState() }
    // Resolved here, in composition, since UiMessage.resolve() calls the
    // @Composable stringResource() — the LaunchedEffect body below cannot
    // call it itself. Keyed on the event's own id, not its text, so the
    // exact same message posted twice in a row is still shown twice.
    val pendingSnackbar = state.snackbarMessage
    val pendingSnackbarText = pendingSnackbar?.text?.resolve()
    LaunchedEffect(pendingSnackbar?.id) {
        if (pendingSnackbar != null && pendingSnackbarText != null) {
            snackbarHostState.showSnackbar(pendingSnackbarText)
            viewModel.snackbarShown(pendingSnackbar.id)
        }
    }
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
        secureWhen = ::isSecureRoute,
        snackbarHostState = snackbarHostState,
        banner = {
            de.sidebyside.next.shell.OfflineStatusBanner(
                offline = state.offline,
                lastSyncedAt = state.lastSyncedAt,
            )
        },
        floatingActionButton = {
            QuickCreateFab(
                // The Story screen's own inline "Erinnerung festhalten"
                // button is one tap further from here — see
                // QuickCreateFab's own doc comment for why this does not
                // also reach into StoryDestination's local capture state.
                onCreateMemory = { navController.navigateToPrimary(AppDestination.Story) },
                onCreateHeartMoment = { navController.navigate(HEART_MOMENTS_ROUTE) },
                onCreateMilestone = { navController.navigate(MILESTONE_CREATE_ROUTE) },
                onCreatePrivateNote = { navController.navigate(PRIVATE_NOTES_ROUTE) },
            )
        },
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
                LaunchedEffect(memoryId, state.activeSpaceId, state.reconnectEpoch) {
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
                    cachedAt = state.openMemoryCachedAt,
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

            composable(MILESTONE_CREATE_ROUTE) {
                LaunchedEffect(state.milestoneCreated) {
                    if (state.milestoneCreated) {
                        controller.popBackStack()
                        viewModel.clearMilestoneCreated()
                    }
                }

                MilestoneCreateScreen(
                    busy = state.memoryBusy,
                    problem = state.memoryProblem,
                    onBack = { controller.popBackStack() },
                    onCreate = viewModel::createMilestone,
                )
            }

            composable(
                route = MILESTONE_ROUTE,
                arguments = listOf(navArgument(ITEM_ID_ARGUMENT) { type = NavType.StringType }),
            ) { entry ->
                val id = entry.arguments?.getString(ITEM_ID_ARGUMENT)
                    ?.let { runCatching { java.util.UUID.fromString(it) }.getOrNull() }

                LaunchedEffect(id, state.activeSpaceId, state.reconnectEpoch) {
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
                    cachedAt = state.openMilestoneCachedAt,
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

                LaunchedEffect(id, state.activeSpaceId, state.reconnectEpoch) {
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
                    cachedAt = state.openSharedHeartMomentCachedAt,
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
                LaunchedEffect(state.activeSpaceId, state.reconnectEpoch) { viewModel.loadInvitations() }
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
                LaunchedEffect(state.activeSpaceId, state.reconnectEpoch) { viewModel.loadHeartMoments() }
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
                LaunchedEffect(state.activeSpaceId, state.reconnectEpoch) { viewModel.loadRelatedPersons() }

                RelatedPersonsScreen(
                    people = state.relatedPersons,
                    busy = state.relatedPersonsBusy,
                    problem = state.relatedPersonsProblem,
                    onBack = { controller.popBackStack() },
                    onAdd = viewModel::addRelatedPerson,
                    onEdit = viewModel::updateRelatedPerson,
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

                LaunchedEffect(personId, state.activeSpaceId, state.reconnectEpoch) {
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
                LaunchedEffect(state.activeSpaceId, state.reconnectEpoch) { viewModel.loadProfilePreferences() }

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

            composable(PLACES_ROUTE) {
                LaunchedEffect(state.activeSpaceId, state.reconnectEpoch) { viewModel.loadPlaces() }

                PlacesScreen(
                    places = state.places,
                    busy = state.placesBusy,
                    problem = state.placesProblem,
                    onBack = { controller.popBackStack() },
                    onAdd = { name, description, address, latitude, longitude ->
                        viewModel.addPlace(name, description, address, latitude, longitude)
                    },
                    onEdit = { place, name, description, address, latitude, longitude ->
                        viewModel.updatePlace(place, name, description, address, latitude, longitude)
                    },
                    onDelete = viewModel::deletePlace,
                    onOpenRelations = { place ->
                        controller.navigate("planning/places/${place.id}/relations")
                    },
                    cachedAt = state.placesCachedAt,
                )
            }

            composable(
                route = PLACE_RELATIONS_ROUTE,
                arguments = listOf(navArgument(PLACE_ID_ARGUMENT) { type = NavType.StringType }),
            ) { entry ->
                val placeId = entry.arguments?.getString(PLACE_ID_ARGUMENT)
                    ?.let { runCatching { java.util.UUID.fromString(it) }.getOrNull() }
                val place = state.places.firstOrNull { it.id == placeId }

                LaunchedEffect(placeId, state.activeSpaceId, state.reconnectEpoch) {
                    placeId?.let(viewModel::loadPlaceRelations)
                }

                PlaceRelationsScreen(
                    placeName = place?.name.orEmpty(),
                    targets = state.placeRelationTargets,
                    linkedIds = state.placeLinkedTargetIds,
                    busy = state.placeRelationsBusy,
                    problem = state.placeRelationsProblem,
                    onBack = { controller.popBackStack() },
                    onLink = { target ->
                        placeId?.let { viewModel.linkPlaceRelation(it, target.kind, target.id) }
                    },
                    onUnlink = { target ->
                        placeId?.let { viewModel.unlinkPlaceRelation(it, target.kind, target.id) }
                    },
                )
            }

            composable(COLLECTIONS_ROUTE) {
                LaunchedEffect(state.activeSpaceId, state.reconnectEpoch) { viewModel.loadCollections() }

                CollectionsScreen(
                    collections = state.collections,
                    busy = state.collectionsBusy,
                    problem = state.collectionsProblem,
                    onBack = { controller.popBackStack() },
                    onOpen = { collection ->
                        controller.navigate("planning/collections/${collection.id}")
                    },
                    onAdd = viewModel::addCollection,
                    onEdit = viewModel::updateCollection,
                    onDelete = viewModel::deleteCollection,
                    cachedAt = state.collectionsCachedAt,
                )
            }

            composable(
                route = COLLECTION_DETAIL_ROUTE,
                arguments = listOf(navArgument(COLLECTION_ID_ARGUMENT) { type = NavType.StringType }),
            ) { entry ->
                val collectionId = entry.arguments?.getString(COLLECTION_ID_ARGUMENT)
                    ?.let { runCatching { java.util.UUID.fromString(it) }.getOrNull() }
                val collection = state.collections.firstOrNull { it.id == collectionId }

                LaunchedEffect(state.activeSpaceId, state.reconnectEpoch) { viewModel.loadCollections() }

                CollectionDetailScreen(
                    collection = collection,
                    busy = state.collectionsBusy,
                    problem = state.collectionsProblem,
                    onBack = { controller.popBackStack() },
                    onAddItem = { title -> collection?.let { viewModel.addCollectionItem(it, title) } },
                    onToggleCompleted = { item ->
                        collection?.let { viewModel.toggleCollectionItemCompleted(it, item) }
                    },
                    onDeleteItem = { item ->
                        collection?.let { viewModel.deleteCollectionItem(it, item) }
                    },
                    onMoveUp = { item -> collection?.let { viewModel.moveCollectionItemUp(it, item) } },
                    onMoveDown = { item -> collection?.let { viewModel.moveCollectionItemDown(it, item) } },
                )
            }

            composable(CHAPTERS_ROUTE) {
                LaunchedEffect(state.activeSpaceId, state.reconnectEpoch) { viewModel.loadChapters() }

                ChaptersScreen(
                    chapters = state.chapters,
                    busy = state.chaptersBusy,
                    problem = state.chaptersProblem,
                    onBack = { controller.popBackStack() },
                    onOpen = { chapter -> controller.navigate("planning/chapters/${chapter.id}/content") },
                    onAdd = { title, description, startOn, endOn ->
                        viewModel.addChapter(title, description, startOn, endOn)
                    },
                    onEdit = { chapter, title, description, startOn, endOn ->
                        viewModel.updateChapter(chapter, title, description, startOn, endOn)
                    },
                    onDelete = viewModel::deleteChapter,
                    cachedAt = state.chaptersCachedAt,
                )
            }

            composable(
                route = CHAPTER_CONTENT_ROUTE,
                arguments = listOf(navArgument(CHAPTER_ID_ARGUMENT) { type = NavType.StringType }),
            ) { entry ->
                val chapterId = entry.arguments?.getString(CHAPTER_ID_ARGUMENT)
                    ?.let { runCatching { java.util.UUID.fromString(it) }.getOrNull() }
                val chapter = state.chapters.firstOrNull { it.id == chapterId }

                LaunchedEffect(chapterId, state.activeSpaceId, state.reconnectEpoch) {
                    chapterId?.let(viewModel::loadChapterContent)
                }

                ChapterContentScreen(
                    chapterTitle = chapter?.title.orEmpty(),
                    candidates = state.chapterContentCandidates,
                    linked = state.chapterLinkedContent,
                    busy = state.chapterContentBusy,
                    problem = state.chapterContentProblem,
                    onBack = { controller.popBackStack() },
                    onLink = { target ->
                        chapterId?.let { viewModel.linkChapterContent(it, target) }
                    },
                    onUnlink = { target ->
                        chapterId?.let { viewModel.unlinkChapterContent(it, target) }
                    },
                )
            }

            composable(PRIVATE_AREA_ROUTE) {
                PrivateAreaScreen(
                    onBack = { controller.popBackStack() },
                    onOpenNotes = { controller.navigate(PRIVATE_NOTES_ROUTE) },
                    onOpenGiftIdeas = { controller.navigate(GIFT_IDEAS_ROUTE) },
                    onOpenCollections = { controller.navigate(PRIVATE_COLLECTIONS_ROUTE) },
                )
            }

            composable(PRIVATE_NOTES_ROUTE) {
                LaunchedEffect(state.activeSpaceId, state.reconnectEpoch) { viewModel.loadPrivateNotes() }

                PrivateNotesScreen(
                    notes = state.privateNotes,
                    busy = state.privateNotesBusy,
                    problem = state.privateNotesProblem,
                    onBack = { controller.popBackStack() },
                    onAdd = viewModel::addPrivateNote,
                    onEdit = viewModel::updatePrivateNote,
                    onDelete = viewModel::deletePrivateNote,
                    cachedAt = state.privateNotesCachedAt,
                )
            }

            composable(GIFT_IDEAS_ROUTE) {
                LaunchedEffect(state.activeSpaceId, state.reconnectEpoch) { viewModel.loadGiftIdeas() }

                GiftIdeasScreen(
                    ideas = state.giftIdeas,
                    busy = state.giftIdeasBusy,
                    problem = state.giftIdeasProblem,
                    onBack = { controller.popBackStack() },
                    onAdd = viewModel::addGiftIdea,
                    onEdit = viewModel::updateGiftIdea,
                    onChangeStatus = viewModel::changeGiftIdeaStatus,
                    onDelete = viewModel::deleteGiftIdea,
                    cachedAt = state.giftIdeasCachedAt,
                )
            }

            composable(PRIVATE_COLLECTIONS_ROUTE) {
                LaunchedEffect(state.activeSpaceId, state.reconnectEpoch) { viewModel.loadPrivateCollections() }

                PrivateCollectionsScreen(
                    collections = state.privateCollections,
                    busy = state.privateCollectionsBusy,
                    problem = state.privateCollectionsProblem,
                    onBack = { controller.popBackStack() },
                    onOpen = { collection ->
                        controller.navigate("more/private/collections/${collection.id}")
                    },
                    onAdd = viewModel::addPrivateCollection,
                    onEdit = viewModel::updatePrivateCollection,
                    onDelete = viewModel::deletePrivateCollection,
                    cachedAt = state.privateCollectionsCachedAt,
                )
            }

            composable(
                route = PRIVATE_COLLECTION_DETAIL_ROUTE,
                arguments = listOf(navArgument(COLLECTION_ID_ARGUMENT) { type = NavType.StringType }),
            ) { entry ->
                val collectionId = entry.arguments?.getString(COLLECTION_ID_ARGUMENT)
                    ?.let { runCatching { java.util.UUID.fromString(it) }.getOrNull() }
                val collection = state.privateCollections.firstOrNull { it.id == collectionId }

                LaunchedEffect(state.activeSpaceId, state.reconnectEpoch) { viewModel.loadPrivateCollections() }

                PrivateCollectionDetailScreen(
                    collection = collection,
                    busy = state.privateCollectionsBusy,
                    problem = state.privateCollectionsProblem,
                    onBack = { controller.popBackStack() },
                    onAddItem = { title -> collection?.let { viewModel.addPrivateCollectionItem(it, title) } },
                    onToggleCompleted = { item ->
                        collection?.let { viewModel.toggleCollectionItemCompleted(it, item) }
                    },
                    onDeleteItem = { item ->
                        collection?.let { viewModel.deletePrivateCollectionItem(it, item) }
                    },
                    onMoveUp = { item -> collection?.let { viewModel.moveCollectionItemUp(it, item) } },
                    onMoveDown = { item -> collection?.let { viewModel.moveCollectionItemDown(it, item) } },
                )
            }

            composable(NOTIFICATIONS_ROUTE) {
                LaunchedEffect(state.activeSpaceId, state.reconnectEpoch) {
                    viewModel.loadNotifications()
                    viewModel.loadUnreadNotificationCount()
                }

                NotificationsScreen(
                    notifications = state.notifications,
                    unreadCount = state.unreadNotificationCount,
                    busy = state.notificationsBusy,
                    problem = state.notificationsProblem,
                    onBack = { controller.popBackStack() },
                    onMarkRead = viewModel::markNotificationRead,
                    onMarkAllRead = viewModel::markAllNotificationsRead,
                    onOpen = { notification ->
                        engagementTargetRoute(notification.targetType, notification.targetId)?.let {
                            viewModel.markNotificationRead(notification)
                            controller.navigate(it)
                        }
                    },
                    onLoadMore = viewModel::loadMoreNotifications.takeIf { state.notificationsHasMore },
                    loadingMore = state.notificationsLoadingMore,
                )
            }

            composable(ACTIVITY_ROUTE) {
                LaunchedEffect(state.activeSpaceId, state.reconnectEpoch) { viewModel.loadActivity() }

                ActivityScreen(
                    entries = state.activity,
                    busy = state.activityBusy,
                    problem = state.activityProblem,
                    onBack = { controller.popBackStack() },
                    onOpen = { entry ->
                        engagementTargetRoute(entry.targetType, entry.targetId)?.let { controller.navigate(it) }
                    },
                    onLoadMore = viewModel::loadMoreActivity.takeIf { state.activityHasMore },
                    loadingMore = state.activityLoadingMore,
                )
            }

            composable(DATA_EXPORT_ROUTE) {
                val exportContext = LocalContext.current
                val exportScope = rememberCoroutineScope()
                val exportDownloadLauncher = rememberLauncherForActivityResult(
                    ActivityResultContracts.CreateDocument("application/zip"),
                ) { uri ->
                    if (uri != null) {
                        exportScope.launch {
                            exportContext.contentResolver.openOutputStream(uri)?.use { stream ->
                                viewModel.downloadExport(stream)
                            }
                        }
                    }
                }

                de.sidebyside.next.transfer.DataExportScreen(
                    export = state.export,
                    busy = state.exportBusy,
                    problem = state.exportProblem,
                    downloaded = state.exportDownloaded,
                    onBack = { controller.popBackStack() },
                    onCreateExport = viewModel::createExport,
                    onRefreshExport = viewModel::refreshExport,
                    onDownloadExport = {
                        val exportId = state.export?.id
                        if (exportId != null) {
                            exportDownloadLauncher.launch("sidebyside-export-$exportId.zip")
                        }
                    },
                )
            }

            composable(DATA_IMPORT_ROUTE) {
                val importContext = LocalContext.current
                val importScope = rememberCoroutineScope()
                val importPickerLauncher = rememberLauncherForActivityResult(
                    ActivityResultContracts.OpenDocument(),
                ) { uri ->
                    if (uri != null) {
                        importScope.launch {
                            val size = importContext.contentResolver
                                .openFileDescriptor(uri, "r")
                                ?.use { it.statSize } ?: -1L
                            importContext.contentResolver.openInputStream(uri)?.use { stream ->
                                viewModel.uploadImport(size, stream)
                            }
                        }
                    }
                }

                de.sidebyside.next.transfer.DataImportScreen(
                    import = state.import,
                    busy = state.importBusy,
                    problem = state.importProblem,
                    onBack = { controller.popBackStack() },
                    onPickArchive = { importPickerLauncher.launch(arrayOf("application/zip")) },
                    onRefreshImport = viewModel::refreshImport,
                    onApplyImport = viewModel::applyImport,
                    onStartOver = viewModel::clearImport,
                )
            }

            composable(SEARCH_ROUTE) {
                DisposableEffect(Unit) { onDispose(viewModel::clearSearch) }

                SearchScreen(
                    results = state.searchResults,
                    busy = state.searchBusy,
                    problem = state.searchProblem,
                    onBack = { controller.popBackStack() },
                    onSearch = viewModel::search,
                    onLoadMore = viewModel::loadMoreSearch.takeIf { state.searchHasMore },
                    loadingMore = state.searchLoadingMore,
                )
            }
        },
    ) { destination ->
        when (destination) {
            AppDestination.Today -> {
                LaunchedEffect(state.activeSpaceId, state.reconnectEpoch) { viewModel.loadToday() }
                TodayScreen(
                    dashboard = state.dashboard,
                    busy = state.todayBusy,
                    problem = state.todayProblem,
                    gestureSent = state.thinkingOfYouSent,
                    onSendThinkingOfYou = viewModel::sendThinkingOfYou,
                    onOpenActivity = { navController.navigate(ACTIVITY_ROUTE) },
                    cachedAt = state.todayCachedAt,
                )
            }

            AppDestination.Plan -> {
                LaunchedEffect(state.activeSpaceId, state.reconnectEpoch) { viewModel.loadPlanning() }
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
                    onOpenPlaces = { navController.navigate(PLACES_ROUTE) },
                    onOpenCollections = { navController.navigate(COLLECTIONS_ROUTE) },
                    onOpenChapters = { navController.navigate(CHAPTERS_ROUTE) },
                    cachedAt = state.planningCachedAt,
                )
            }

            AppDestination.More -> {
                LaunchedEffect(state.activeSpaceId, state.reconnectEpoch) {
                    if (state.activeSpaceId != null) viewModel.refreshProfile()
                }
                LaunchedEffect(state.availableSpaces) { viewModel.loadSpaceNames() }
                LaunchedEffect(state.activeSpaceId, state.reconnectEpoch) { viewModel.loadUnreadNotificationCount() }
                MoreScreen(
                    onSignOut = onSignOut,
                    onOpenHeartMoments = { navController.navigate(HEART_MOMENTS_ROUTE) },
                    onOpenInvitations = { navController.navigate(INVITATIONS_ROUTE) },
                    onOpenRelatedPersons = { navController.navigate(RELATED_PERSONS_ROUTE) },
                    onOpenPreferences = { navController.navigate(PREFERENCES_ROUTE) },
                    onOpenPrivateArea = { navController.navigate(PRIVATE_AREA_ROUTE) },
                    onOpenDataExport = { navController.navigate(DATA_EXPORT_ROUTE) },
                    onOpenDataImport = { navController.navigate(DATA_IMPORT_ROUTE) },
                    onOpenNotifications = { navController.navigate(NOTIFICATIONS_ROUTE) },
                    onOpenSearch = { navController.navigate(SEARCH_ROUTE) },
                    unreadNotificationCount = state.unreadNotificationCount,
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

/**
 * Matches the Web path from `web/src/client/routes.ts`
 * (`MILESTONE_CREATE_ROUTE`). Registered ahead of [MILESTONE_ROUTE] in the
 * Nav graph, since Navigation Compose scores a literal path segment above a
 * `{itemId}` wildcard when both could otherwise match "new".
 */
private const val MILESTONE_CREATE_ROUTE = "story/milestones/new"
private const val HEART_MOMENT_ROUTE = "story/heart-moments/{$ITEM_ID_ARGUMENT}"

private const val RELATED_PERSONS_ROUTE = "people/related-persons"
private const val PERSON_ID_ARGUMENT = "personId"
private const val IMPORTANT_DATES_ROUTE =
    "people/related-persons/{$PERSON_ID_ARGUMENT}/important-dates"

private const val PREFERENCES_ROUTE = "profile/preferences"

private const val PLACES_ROUTE = "planning/places"
private const val PLACE_ID_ARGUMENT = "placeId"
private const val PLACE_RELATIONS_ROUTE = "planning/places/{$PLACE_ID_ARGUMENT}/relations"

private const val COLLECTIONS_ROUTE = "planning/collections"

private const val CHAPTERS_ROUTE = "planning/chapters"
private const val CHAPTER_ID_ARGUMENT = "chapterId"
private const val CHAPTER_CONTENT_ROUTE = "planning/chapters/{$CHAPTER_ID_ARGUMENT}/content"

private const val PRIVATE_AREA_ROUTE = "more/private"

/** No Web equivalent exists yet to match — this UI is Android-first. */
private const val DATA_EXPORT_ROUTE = "more/data-export"

/** No Web equivalent exists yet to match — this UI is Android-first. */
private const val DATA_IMPORT_ROUTE = "more/data-import"
private const val PRIVATE_NOTES_ROUTE = "more/private/notes"
private const val GIFT_IDEAS_ROUTE = "more/private/gift-ideas"
private const val PRIVATE_COLLECTIONS_ROUTE = "more/private/collections"
private const val COLLECTION_ID_ARGUMENT = "collectionId"
private const val PRIVATE_COLLECTION_DETAIL_ROUTE = "more/private/collections/{$COLLECTION_ID_ARGUMENT}"
private const val COLLECTION_DETAIL_ROUTE = "planning/collections/{$COLLECTION_ID_ARGUMENT}"

/** Matches the Web path from `web/src/client/routes.ts` (`MORE_NOTIFICATIONS_ROUTE`). */
private const val NOTIFICATIONS_ROUTE = "more/notifications"

/** Matches the Web path from `web/src/client/routes.ts` (`ACTIVITY_ROUTE`). */
private const val ACTIVITY_ROUTE = "today/activity"

/**
 * Matches the Web path from `web/src/client/routes.ts` (`SEARCH_ROUTE`).
 * Secured the same way as the Private Area subtree (see `secureWhen`
 * above): a result's `SearchKind` can be `PRIVATE_NOTE`, `GIFT_IDEA`, or a
 * PrivateCollection kind just as easily as a shared one, so the screen as a
 * whole gets the same screenshot/Recents protection rather than only the
 * routes with "private" in their path.
 */
private const val SEARCH_ROUTE = "search"

/**
 * The M2-D18 cross-client Deep Link contract's "small logical target
 * tuple... maps to the current client's canonical route," applied to
 * Notifications and Activity: each entry names a resource kind and id
 * rather than a client-specific path, and this is where that tuple becomes
 * an actual in-app route. Reuses the route templates above rather than a
 * second copy of the same path shapes.
 *
 * `null` for [targetId] being absent, or for a kind with no per-resource
 * route on Android yet — Wish and Plan both live in one shared list screen,
 * not a route of their own. A caller's tap on such an entry does nothing
 * rather than navigating to a route that cannot be built.
 */
internal fun engagementTargetRoute(targetType: EngagementTarget?, targetId: java.util.UUID?): String? {
    if (targetId == null) return null
    return when (targetType) {
        EngagementTarget.MEMORY -> MEMORY_ROUTE.replace("{$MEMORY_ID_ARGUMENT}", targetId.toString())
        EngagementTarget.MILESTONE -> MILESTONE_ROUTE.replace("{$ITEM_ID_ARGUMENT}", targetId.toString())
        EngagementTarget.HEART_MOMENT -> HEART_MOMENT_ROUTE.replace("{$ITEM_ID_ARGUMENT}", targetId.toString())
        EngagementTarget.PLACE -> PLACE_RELATIONS_ROUTE.replace("{$PLACE_ID_ARGUMENT}", targetId.toString())
        EngagementTarget.CHAPTER -> CHAPTER_CONTENT_ROUTE.replace("{$CHAPTER_ID_ARGUMENT}", targetId.toString())
        EngagementTarget.COLLECTION -> COLLECTION_DETAIL_ROUTE.replace("{$COLLECTION_ID_ARGUMENT}", targetId.toString())
        EngagementTarget.WISH, EngagementTarget.PLAN, null -> null
    }
}

/**
 * Whether [route] is inside the owner-only Private Area subtree — the hub
 * and every screen under it, matched by prefix so a new private-area screen
 * is secure by default rather than needing to opt in.
 */
internal fun isPrivateAreaRoute(route: String?): Boolean =
    route != null && (route == PRIVATE_AREA_ROUTE || route.startsWith("$PRIVATE_AREA_ROUTE/"))

/**
 * Every route that gets [de.sidebyside.next.shell.SecureWindowEffect]: the
 * Private Area subtree, and Search — a result's `SearchKind` can be a
 * private one just as easily as a shared one.
 */
internal fun isSecureRoute(route: String?): Boolean = isPrivateAreaRoute(route) || route == SEARCH_ROUTE

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

    LaunchedEffect(state.activeSpaceId, state.reconnectEpoch) { viewModel.refreshStory() }

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
        cachedAt = state.storyCachedAt,
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
