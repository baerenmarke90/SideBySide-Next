package de.sidebyside.next.plan

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.ColumnScope
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.heightIn
import androidx.compose.foundation.layout.imePadding
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.widthIn
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.Button
import androidx.compose.material3.DatePicker
import androidx.compose.material3.DatePickerDialog
import androidx.compose.material3.ExperimentalMaterial3Api
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.ModalBottomSheet
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.Surface
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.material3.TimePicker
import androidx.compose.material3.TimePickerDialog
import androidx.compose.material3.rememberDatePickerState
import androidx.compose.material3.rememberModalBottomSheetState
import androidx.compose.material3.rememberTimePickerState
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.saveable.rememberSaveable
import androidx.compose.runtime.setValue
import androidx.compose.runtime.withFrameNanos
import androidx.compose.ui.Modifier
import androidx.compose.ui.focus.FocusRequester
import androidx.compose.ui.focus.focusRequester
import androidx.compose.ui.res.stringResource
import androidx.compose.ui.semantics.heading
import androidx.compose.ui.semantics.semantics
import androidx.compose.ui.text.font.FontWeight
import de.sidebyside.next.design.MinimumTouchTarget
import de.sidebyside.next.design.SideBySideDisplayFamily
import de.sidebyside.next.design.SideBySideTheme
import de.sidebyside.next.reference.R
import de.sidebyside.next.shell.PlacePicker
import java.time.Instant
import java.time.LocalDate
import java.time.LocalTime
import java.time.ZoneId
import java.time.ZoneOffset
import java.util.UUID
import sidebyside.api.models.PlaceDetail
import sidebyside.api.models.PlanDetail
import sidebyside.api.models.PlanStatus
import sidebyside.api.models.WishDetail

/**
 * The focused planning surfaces.
 *
 * Every one of them does one thing, is entered from the wish or plan it acts
 * on, and closes back into Planning. They are bottom sheets rather than pages
 * because each is short — `docs/UX-PATTERNS.md` section 3.3 — and rather than
 * generic `AlertDialog` forms because none of them is a yes/no question.
 *
 * They deliberately do not sit in the navigation graph: Planning stays one
 * destination, its deep link keeps meaning what it meant, and the sheet that
 * was open survives rotation and process death through the caller's saved
 * focus state.
 */

/**
 * The shared sheet body: one scroll region that the keyboard pushes rather than
 * covers, so no field and no completion button can end up under the IME on a
 * short window or at a large font scale.
 */
@OptIn(ExperimentalMaterial3Api::class)
@Composable
private fun PlanningSheet(
    onDismiss: () -> Unit,
    content: @Composable ColumnScope.() -> Unit,
) {
    ModalBottomSheet(
        onDismissRequest = onDismiss,
        sheetState = rememberModalBottomSheetState(skipPartiallyExpanded = true),
        containerColor = SideBySideTheme.colors.surfaceRaised,
    ) {
        Column(
            modifier = Modifier
                .fillMaxWidth()
                .verticalScroll(rememberScrollState())
                .padding(horizontal = SideBySideTheme.spacing.pageMargin)
                .padding(bottom = SideBySideTheme.spacing.step8)
                .imePadding(),
            verticalArrangement = Arrangement.spacedBy(SideBySideTheme.spacing.step4),
            content = content,
        )
    }
}

@Composable
private fun SheetEyebrow(labelRes: Int) {
    Text(
        text = stringResource(labelRes),
        style = MaterialTheme.typography.labelLarge,
        color = SideBySideTheme.colors.brandStrong,
    )
}

@Composable
private fun SheetHeading(text: String) {
    Text(
        text = text,
        style = MaterialTheme.typography.titleLarge.copy(fontFamily = SideBySideDisplayFamily),
        color = SideBySideTheme.colors.textPrimary,
        modifier = Modifier
            .widthIn(max = ReadingMeasure)
            .semantics { heading() },
    )
}

@Composable
private fun SheetPrimaryAction(labelRes: Int, enabled: Boolean, onClick: () -> Unit) {
    Button(
        onClick = onClick,
        enabled = enabled,
        modifier = Modifier
            .fillMaxWidth()
            .heightIn(min = MinimumTouchTarget),
    ) {
        Text(stringResource(labelRes))
    }
}

@Composable
private fun SheetSecondaryAction(labelRes: Int, enabled: Boolean = true, onClick: () -> Unit) {
    TextButton(
        onClick = onClick,
        enabled = enabled,
        modifier = Modifier
            .fillMaxWidth()
            .heightIn(min = MinimumTouchTarget),
    ) {
        Text(stringResource(labelRes))
    }
}

@Composable
private fun SheetDestructiveAction(labelRes: Int, enabled: Boolean, onClick: () -> Unit) {
    TextButton(
        onClick = onClick,
        enabled = enabled,
        modifier = Modifier
            .fillMaxWidth()
            .heightIn(min = MinimumTouchTarget),
    ) {
        Text(stringResource(labelRes), color = SideBySideTheme.colors.error)
    }
}

/**
 * The keyboard should already be up when a composer opens, because the only
 * reason to open one is to type. Guarded, because a focus request that arrives
 * before the field is attached would otherwise take the sheet down with it.
 */
@Composable
private fun RequestInitialFocus(focusRequester: FocusRequester) {
    LaunchedEffect(focusRequester) {
        withFrameNanos { }
        runCatching { focusRequester.requestFocus() }
    }
}

/**
 * Capturing or renaming a wish: one field, because a wish is one sentence.
 *
 * [onSwitchToPlan] is the only way direct plan creation is reached. It exists
 * so the overview does not have to carry a second create affordance next to
 * the dominant one, and it hands over what has already been typed.
 */
@Composable
internal fun WishComposerSheet(
    initialTitle: String,
    busy: Boolean,
    headingRes: Int,
    submitLabelRes: Int,
    onSwitchToPlan: ((String) -> Unit)?,
    onDismiss: () -> Unit,
    onSubmit: (String) -> Unit,
) {
    PlanningSheet(onDismiss = onDismiss) {
        var title by rememberSaveable(initialTitle) { mutableStateOf(initialTitle) }
        val focusRequester = remember { FocusRequester() }
        RequestInitialFocus(focusRequester)

        SheetEyebrow(R.string.plan_wish_eyebrow)
        SheetHeading(stringResource(headingRes))
        OutlinedTextField(
            value = title,
            onValueChange = { title = it.take(200) },
            label = { Text(stringResource(R.string.plan_wish_hint)) },
            enabled = !busy,
            modifier = Modifier
                .fillMaxWidth()
                .focusRequester(focusRequester),
        )
        SheetPrimaryAction(submitLabelRes, enabled = !busy && title.isNotBlank()) {
            onSubmit(title)
        }
        onSwitchToPlan?.let { switch ->
            SheetSecondaryAction(R.string.plan_wish_direct_plan, enabled = !busy) { switch(title) }
        }
    }
}

/**
 * A wish, opened.
 *
 * The wish itself is the content; the three things that can happen to it are
 * offered here, in the order they matter, instead of on every card.
 */
@Composable
internal fun WishSheet(
    wish: WishDetail,
    busy: Boolean,
    onMakePlan: () -> Unit,
    onEdit: () -> Unit,
    onRemove: () -> Unit,
    onDismiss: () -> Unit,
) {
    PlanningSheet(onDismiss = onDismiss) {
        SheetEyebrow(R.string.plan_wish_eyebrow)
        SheetHeading(wish.title)
        wish.creator.displayName.takeIf { it.isNotBlank() }?.let { name ->
            Text(
                text = stringResource(R.string.plan_wish_by, name),
                style = MaterialTheme.typography.bodySmall,
                color = SideBySideTheme.colors.textSecondary,
            )
        }
        if (wish.capabilities.canEdit) {
            SheetPrimaryAction(R.string.plan_wish_make_plan, enabled = !busy, onClick = onMakePlan)
            SheetSecondaryAction(R.string.plan_wish_edit, enabled = !busy, onClick = onEdit)
        }
        if (wish.capabilities.canDelete) {
            SheetDestructiveAction(R.string.plan_wish_remove, enabled = !busy, onClick = onRemove)
        }
    }
}

/**
 * Wish to plan.
 *
 * The wish stays visible above the fields it is becoming, so the transition
 * reads as one thing turning into another rather than as a new record that
 * happens to be pre-filled. Only the title is asked for; everything else waits
 * behind `Mehr dazu`.
 */
@Composable
internal fun WishToPlanSheet(
    wish: WishDetail,
    places: List<PlaceDetail>,
    busy: Boolean,
    onDismiss: () -> Unit,
    onCreatePlace: (String) -> Unit,
    onSubmit: (
        title: String,
        description: String,
        placeId: UUID?,
        startOn: String?,
        startAt: String?,
    ) -> Unit,
) {
    PlanningSheet(onDismiss = onDismiss) {
        SheetHeading(stringResource(R.string.plan_wish_make_plan_title))
        Surface(
            shape = RoundedCornerShape(SideBySideTheme.radii.card),
            color = SideBySideTheme.colors.brandSurface,
            modifier = Modifier.fillMaxWidth(),
        ) {
            Column(
                modifier = Modifier.padding(SideBySideTheme.spacing.cardPadding),
                verticalArrangement = Arrangement.spacedBy(SideBySideTheme.spacing.step1),
            ) {
                Text(
                    text = stringResource(R.string.plan_wish_make_plan_context),
                    style = MaterialTheme.typography.labelMedium,
                    color = SideBySideTheme.colors.brandStrong,
                )
                Text(
                    text = wish.title,
                    style = MaterialTheme.typography.titleMedium,
                    color = SideBySideTheme.colors.textPrimary,
                    modifier = Modifier.widthIn(max = ReadingMeasure),
                )
            }
        }
        PlanFields(
            key = "wish-plan-" + wish.id,
            places = places,
            busy = busy,
            submitLabelRes = R.string.plan_wish_make_plan_confirm,
            initialTitle = wish.title,
            allowSchedule = true,
            onCreatePlace = onCreatePlace,
            onSubmit = onSubmit,
        )
    }
}

/**
 * Creating or editing a plan directly, with the same fields either way.
 *
 * [allowSchedule] is only true for direct creation: an edit already has its
 * own dedicated schedule sheet reachable from the plan itself, so offering a
 * second path to the same moment here would let the two drift apart.
 */
@Composable
internal fun PlanComposerSheet(
    places: List<PlaceDetail>,
    busy: Boolean,
    headingRes: Int,
    submitLabelRes: Int,
    initialTitle: String = "",
    initialDescription: String = "",
    initialPlaceId: UUID? = null,
    allowSchedule: Boolean = false,
    onDismiss: () -> Unit,
    onCreatePlace: (String) -> Unit,
    onSubmit: (
        title: String,
        description: String,
        placeId: UUID?,
        startOn: String?,
        startAt: String?,
    ) -> Unit,
) {
    PlanningSheet(onDismiss = onDismiss) {
        SheetEyebrow(R.string.plan_eyebrow)
        SheetHeading(stringResource(headingRes))
        PlanFields(
            key = "plan-" + headingRes + "-" + initialTitle,
            places = places,
            busy = busy,
            submitLabelRes = submitLabelRes,
            initialTitle = initialTitle,
            initialDescription = initialDescription,
            initialPlaceId = initialPlaceId,
            allowSchedule = allowSchedule,
            onCreatePlace = onCreatePlace,
            onSubmit = onSubmit,
        )
    }
}

/**
 * Title first; description, place and — for direct creation — a moment only
 * when asked for.
 *
 * Shared by direct plan creation, plan editing and wish conversion, so those
 * three cannot drift into three different sets of fields for one resource. An
 * edit that already has a description or a place opens with them unfolded,
 * because hiding what someone wrote is not progressive disclosure.
 *
 * [allowSchedule] adds a date-first scheduling section next to `Mehr dazu`, so
 * a couple who already knows the day never has to reopen the new plan. Time is
 * deliberately optional: a selected day is a complete date-only schedule, and
 * no wall-clock value is invented when the time remains absent.
 */
@OptIn(ExperimentalMaterial3Api::class)
@Composable
private fun ColumnScope.PlanFields(
    key: String,
    places: List<PlaceDetail>,
    busy: Boolean,
    submitLabelRes: Int,
    initialTitle: String,
    initialDescription: String = "",
    initialPlaceId: UUID? = null,
    allowSchedule: Boolean = false,
    onCreatePlace: (String) -> Unit,
    onSubmit: (
        title: String,
        description: String,
        placeId: UUID?,
        startOn: String?,
        startAt: String?,
    ) -> Unit,
) {
    var title by rememberSaveable(key) { mutableStateOf(initialTitle) }
    var description by rememberSaveable(key) { mutableStateOf(initialDescription) }
    var placeId by rememberSaveable(key) { mutableStateOf(initialPlaceId) }
    var detailsOpen by rememberSaveable(key) {
        mutableStateOf(initialDescription.isNotBlank() || initialPlaceId != null)
    }
    var newPlaceOpen by rememberSaveable(key) { mutableStateOf(false) }
    var newPlaceName by rememberSaveable(key) { mutableStateOf("") }
    var pendingNewPlaceName by rememberSaveable(key) { mutableStateOf<String?>(null) }
    var scheduleOpen by rememberSaveable(key) { mutableStateOf(false) }
    var day by rememberSaveable(key) { mutableStateOf<String?>(null) }
    var time by rememberSaveable(key) { mutableStateOf<String?>(null) }
    var dayPickerOpen by rememberSaveable(key) { mutableStateOf(false) }
    var timePickerOpen by rememberSaveable(key) { mutableStateOf(false) }
    val focusRequester = remember { FocusRequester() }
    RequestInitialFocus(focusRequester)

    // A place just created here is not selected yet — it only exists once the
    // reload that every planning write triggers brings it back. Matching it
    // by name the moment it appears is what lets creating a place read as
    // one step instead of create-then-go-find-it-again.
    LaunchedEffect(places, pendingNewPlaceName) {
        val pendingName = pendingNewPlaceName ?: return@LaunchedEffect
        places.firstOrNull { it.name == pendingName }?.let {
            placeId = it.id
            pendingNewPlaceName = null
        }
    }

    OutlinedTextField(
        value = title,
        onValueChange = { title = it.take(200) },
        label = { Text(stringResource(R.string.plan_title_hint)) },
        enabled = !busy,
        modifier = Modifier
            .fillMaxWidth()
            .focusRequester(focusRequester),
    )
    if (detailsOpen) {
        OutlinedTextField(
            value = description,
            onValueChange = { description = it },
            label = { Text(stringResource(R.string.plan_description_hint)) },
            enabled = !busy,
            modifier = Modifier.fillMaxWidth(),
        )
        PlacePicker(
            places = places,
            selectedPlaceId = placeId,
            onSelect = { placeId = it },
            busy = busy,
            modifier = Modifier.fillMaxWidth(),
        )
        if (newPlaceOpen) {
            OutlinedTextField(
                value = newPlaceName,
                onValueChange = { newPlaceName = it.take(200) },
                label = { Text(stringResource(R.string.plan_place_new_hint)) },
                enabled = !busy,
                modifier = Modifier.fillMaxWidth(),
            )
            SheetSecondaryAction(
                R.string.plan_place_new_confirm,
                enabled = !busy && newPlaceName.isNotBlank(),
            ) {
                val name = newPlaceName.trim()
                pendingNewPlaceName = name
                onCreatePlace(name)
                newPlaceOpen = false
                newPlaceName = ""
            }
        } else {
            SheetSecondaryAction(R.string.plan_place_new, enabled = !busy) {
                newPlaceOpen = true
            }
        }
    } else {
        SheetSecondaryAction(R.string.plan_optional_details, enabled = !busy) {
            detailsOpen = true
        }
    }
    if (allowSchedule) {
        if (scheduleOpen) {
            PickerRow(
                labelRes = R.string.plan_schedule_day,
                value = day?.let { formattedDate(LocalDate.parse(it)) },
                placeholderRes = R.string.plan_schedule_pick_day,
                enabled = !busy,
                onClick = { dayPickerOpen = true },
            )
            if (day != null) {
                SheetSecondaryAction(R.string.plan_schedule_clear_date, enabled = !busy) {
                    day = null
                    time = null
                }
                PickerRow(
                    labelRes = R.string.plan_schedule_time_optional,
                    value = time,
                    placeholderRes = R.string.plan_schedule_pick_time,
                    enabled = !busy,
                    onClick = { timePickerOpen = true },
                )
                if (time != null) {
                    SheetSecondaryAction(R.string.plan_schedule_clear_time, enabled = !busy) {
                        time = null
                    }
                }
            }
        } else {
            SheetSecondaryAction(R.string.plan_schedule, enabled = !busy) {
                scheduleOpen = true
            }
        }
    }
    SheetPrimaryAction(submitLabelRes, enabled = !busy && title.isNotBlank()) {
        onSubmit(title, description, placeId, day, time)
    }

    if (dayPickerOpen) {
        DayPicker(
            initial = day?.let { LocalDate.parse(it) } ?: LocalDate.now(),
            onDismiss = { dayPickerOpen = false },
            onPick = {
                dayPickerOpen = false
                day = it.toString()
            },
        )
    }
    if (timePickerOpen) {
        val initial = time?.let { LocalTime.parse(it) } ?: LocalTime.of(19, 0)
        val state = rememberTimePickerState(
            initialHour = initial.hour,
            initialMinute = initial.minute,
            is24Hour = true,
        )
        TimePickerDialog(
            onDismissRequest = { timePickerOpen = false },
            title = { Text(stringResource(R.string.plan_schedule_pick_time)) },
            confirmButton = {
                TextButton(
                    onClick = {
                        timePickerOpen = false
                        time = LocalTime.of(state.hour, state.minute).toString()
                    },
                ) {
                    Text(stringResource(R.string.plan_picker_take))
                }
            },
            dismissButton = {
                TextButton(onClick = { timePickerOpen = false }) {
                    Text(stringResource(R.string.plan_cancel))
                }
            },
        ) {
            TimePicker(state = state)
        }
    }
}

/**
 * A plan, opened.
 *
 * Content first, then the one move that its current status actually invites,
 * then the quieter ones. The status machine is unchanged: `IDEA` can be given a
 * time or sent back, `PLANNED` can be experienced or loosened again, and what
 * has been experienced has nowhere left to go.
 */
@Composable
internal fun PlanSheet(
    plan: PlanDetail,
    places: List<PlaceDetail>,
    busy: Boolean,
    onEdit: () -> Unit,
    onSchedule: () -> Unit,
    onUnschedule: () -> Unit,
    onComplete: () -> Unit,
    onReturnToWish: () -> Unit,
    onDelete: () -> Unit,
    onDismiss: () -> Unit,
) {
    PlanningSheet(onDismiss = onDismiss) {
        SheetEyebrow(R.string.plan_eyebrow)
        Text(
            text = stringResource(plan.status.labelRes()),
            style = MaterialTheme.typography.labelSmall,
            color = plan.status.accent(),
        )
        SheetHeading(plan.title)
        plan.description?.takeIf { it.isNotBlank() }?.let { text ->
            Text(
                text = text,
                style = MaterialTheme.typography.bodyMedium,
                color = SideBySideTheme.colors.textPrimary,
                modifier = Modifier.widthIn(max = ReadingMeasure),
            )
        }
        places.firstOrNull { it.id == plan.placeId }?.let { place ->
            Text(
                text = stringResource(R.string.plan_at_place, place.name),
                style = MaterialTheme.typography.bodySmall,
                color = SideBySideTheme.colors.textSecondary,
            )
        }
        plan.plannedStart?.let { start ->
            Text(
                text = stringResource(R.string.plan_scheduled_for, formattedDateTime(start)),
                style = MaterialTheme.typography.bodySmall,
                color = SideBySideTheme.colors.textSecondary,
            )
        }
        plan.experiencedOn?.let { day ->
            Text(
                text = stringResource(R.string.plan_experienced_on, formattedDate(day)),
                style = MaterialTheme.typography.bodySmall,
                color = SideBySideTheme.colors.textSecondary,
            )
        }

        if (plan.capabilities.canEdit) {
            when (plan.status) {
                PlanStatus.IDEA -> {
                    SheetPrimaryAction(R.string.plan_schedule, enabled = !busy, onClick = onSchedule)
                    SheetSecondaryAction(R.string.plan_edit, enabled = !busy, onClick = onEdit)
                    SheetSecondaryAction(
                        R.string.plan_return_to_wish,
                        enabled = !busy,
                        onClick = onReturnToWish,
                    )
                }

                PlanStatus.PLANNED -> {
                    SheetPrimaryAction(R.string.plan_complete, enabled = !busy, onClick = onComplete)
                    SheetSecondaryAction(R.string.plan_edit, enabled = !busy, onClick = onEdit)
                    SheetSecondaryAction(
                        R.string.plan_unschedule,
                        enabled = !busy,
                        onClick = onUnschedule,
                    )
                }

                // Experienced is where it ends; there is nothing sensible to
                // move it to, so the sheet says what happened instead of
                // offering another transition.
                PlanStatus.COMPLETED -> {
                    Text(
                        text = stringResource(R.string.plan_complete_lead),
                        style = MaterialTheme.typography.bodyMedium,
                        color = SideBySideTheme.colors.textSecondary,
                        modifier = Modifier.widthIn(max = ReadingMeasure),
                    )
                    SheetSecondaryAction(R.string.plan_edit, enabled = !busy, onClick = onEdit)
                }
            }
        }
        if (plan.capabilities.canDelete) {
            SheetDestructiveAction(R.string.plan_delete, enabled = !busy, onClick = onDelete)
        }
    }
}

/**
 * Giving a plan a time.
 *
 * Day and time are two separate decisions with the day first, and each is made
 * in the platform's own picker rather than in a text field that asks a couple
 * to type `JJJJ-MM-TT`. Both start on a sensible suggestion, but nothing is
 * sent until the couple confirms the combination they can read back in full.
 */
@OptIn(ExperimentalMaterial3Api::class)
@Composable
internal fun PlanScheduleSheet(
    plan: PlanDetail,
    busy: Boolean,
    onDismiss: () -> Unit,
    onSubmit: (startOn: String, startAt: String?) -> Unit,
) {
    val existing = plan.plannedStart?.atZoneSameInstant(ZoneId.systemDefault())
    val suggestedDay = plan.plannedOn ?: existing?.toLocalDate() ?: LocalDate.now()
    val suggestedTime = existing?.toLocalTime()?.withSecond(0)?.withNano(0)
        ?: LocalTime.of(19, 0)

    var day by rememberSaveable(plan.id) {
        mutableStateOf((plan.plannedOn ?: existing?.toLocalDate())?.toString())
    }
    var time by rememberSaveable(plan.id) {
        mutableStateOf(existing?.toLocalTime()?.withSecond(0)?.withNano(0)?.toString())
    }
    var dayPickerOpen by rememberSaveable(plan.id) { mutableStateOf(false) }
    var timePickerOpen by rememberSaveable(plan.id) { mutableStateOf(false) }

    PlanningSheet(onDismiss = onDismiss) {
        SheetEyebrow(R.string.plan_eyebrow)
        SheetHeading(stringResource(R.string.plan_schedule_title))
        Text(
            text = plan.title,
            style = MaterialTheme.typography.bodyMedium,
            color = SideBySideTheme.colors.textSecondary,
            modifier = Modifier.widthIn(max = ReadingMeasure),
        )
        PickerRow(
            labelRes = R.string.plan_schedule_day,
            value = day?.let { formattedDate(LocalDate.parse(it)) },
            placeholderRes = R.string.plan_schedule_pick_day,
            enabled = !busy,
            onClick = { dayPickerOpen = true },
        )
        if (day != null) {
            SheetSecondaryAction(R.string.plan_schedule_clear_date, enabled = !busy) {
                day = null
                time = null
            }
        }
        PickerRow(
            labelRes = R.string.plan_schedule_time_optional,
            value = time,
            placeholderRes = R.string.plan_schedule_pick_time,
            enabled = !busy && day != null,
            onClick = { timePickerOpen = true },
        )
        if (time != null) {
            SheetSecondaryAction(R.string.plan_schedule_clear_time, enabled = !busy) {
                time = null
            }
        }
        SheetPrimaryAction(
            R.string.plan_schedule_confirm_optional,
            enabled = !busy && day != null,
        ) {
            onSubmit(day!!, time)
        }
    }

    if (dayPickerOpen) {
        DayPicker(
            initial = day?.let { LocalDate.parse(it) } ?: suggestedDay,
            onDismiss = { dayPickerOpen = false },
            onPick = {
                dayPickerOpen = false
                day = it.toString()
            },
        )
    }
    if (timePickerOpen) {
        val initial = time?.let { LocalTime.parse(it) } ?: suggestedTime
        // Hoisted above the dialog so the confirm button and the picker share
        // one state, which is what lets the buttons sit where the platform
        // puts them instead of inside the picker's own content.
        val state = rememberTimePickerState(
            initialHour = initial.hour,
            initialMinute = initial.minute,
            is24Hour = true,
        )
        TimePickerDialog(
            onDismissRequest = { timePickerOpen = false },
            title = { Text(stringResource(R.string.plan_schedule_pick_time)) },
            confirmButton = {
                TextButton(
                    onClick = {
                        timePickerOpen = false
                        time = LocalTime.of(state.hour, state.minute).toString()
                    },
                ) {
                    Text(stringResource(R.string.plan_picker_take))
                }
            },
            dismissButton = {
                TextButton(onClick = { timePickerOpen = false }) {
                    Text(stringResource(R.string.plan_cancel))
                }
            },
        ) {
            TimePicker(state = state)
        }
    }
}

/**
 * Closing a plan out.
 *
 * The day is a detail here, not the question: the plan is normally finished on
 * the day it was meant for, or today, so that is offered ready-made and only
 * changed by someone who needs to. The domain still records an actual date.
 */
@Composable
internal fun PlanCompleteSheet(
    plan: PlanDetail,
    busy: Boolean,
    onDismiss: () -> Unit,
    onSubmit: (experiencedOn: String) -> Unit,
) {
    val today = LocalDate.now()
    val suggested = (plan.plannedOn
        ?: plan.plannedStart
            ?.atZoneSameInstant(ZoneId.systemDefault())
            ?.toLocalDate())
        ?.takeIf { !it.isAfter(today) }
        ?: today

    var day by rememberSaveable(plan.id) { mutableStateOf(suggested.toString()) }
    var dayPickerOpen by rememberSaveable(plan.id) { mutableStateOf(false) }

    PlanningSheet(onDismiss = onDismiss) {
        SheetEyebrow(R.string.plan_eyebrow)
        SheetHeading(stringResource(R.string.plan_complete_title))
        Text(
            text = plan.title,
            style = MaterialTheme.typography.titleMedium,
            color = SideBySideTheme.colors.textPrimary,
            modifier = Modifier.widthIn(max = ReadingMeasure),
        )
        Text(
            text = stringResource(R.string.plan_complete_lead),
            style = MaterialTheme.typography.bodyMedium,
            color = SideBySideTheme.colors.textSecondary,
            modifier = Modifier.widthIn(max = ReadingMeasure),
        )
        Text(
            text = stringResource(
                R.string.plan_experienced_on,
                formattedDate(LocalDate.parse(day)),
            ),
            style = MaterialTheme.typography.bodyMedium,
            color = SideBySideTheme.colors.textPrimary,
        )
        SheetPrimaryAction(R.string.plan_complete_confirm, enabled = !busy) { onSubmit(day) }
        SheetSecondaryAction(R.string.plan_complete_other_day, enabled = !busy) {
            dayPickerOpen = true
        }
    }

    if (dayPickerOpen) {
        DayPicker(
            initial = LocalDate.parse(day),
            onDismiss = { dayPickerOpen = false },
            onPick = {
                dayPickerOpen = false
                day = it.toString()
            },
        )
    }
}

/**
 * The platform calendar, opened on the day the flow already suggests.
 *
 * `DatePickerState` counts in UTC milliseconds regardless of where the device
 * is, so the day is read back at that offset. Reading it in the device zone
 * would move the selection by a day for anyone west of Greenwich.
 */
@OptIn(ExperimentalMaterial3Api::class)
@Composable
private fun DayPicker(
    initial: LocalDate,
    onDismiss: () -> Unit,
    onPick: (LocalDate) -> Unit,
) {
    val state = rememberDatePickerState(
        initialSelectedDateMillis = initial.atStartOfDay(ZoneOffset.UTC).toInstant().toEpochMilli(),
    )
    DatePickerDialog(
        onDismissRequest = onDismiss,
        confirmButton = {
            TextButton(
                onClick = {
                    val millis = state.selectedDateMillis ?: return@TextButton
                    onPick(Instant.ofEpochMilli(millis).atZone(ZoneOffset.UTC).toLocalDate())
                },
                enabled = state.selectedDateMillis != null,
            ) {
                Text(stringResource(R.string.plan_picker_take))
            }
        },
        dismissButton = {
            TextButton(onClick = onDismiss) { Text(stringResource(R.string.plan_cancel)) }
        },
    ) {
        DatePicker(state = state)
    }
}

/** One decision of a scheduling flow: what it is, what it currently says. */
@Composable
private fun PickerRow(
    labelRes: Int,
    value: String?,
    placeholderRes: Int,
    enabled: Boolean,
    onClick: () -> Unit,
) {
    Surface(
        onClick = onClick,
        enabled = enabled,
        shape = RoundedCornerShape(SideBySideTheme.radii.card),
        // Deliberately not `surface`: the sheet it sits on is already
        // `surfaceRaised`, and in the light scheme both of those are white, so
        // a row drawn in `surface` would read as plain text rather than as
        // something to tap.
        color = SideBySideTheme.colors.surfaceSubtle,
        modifier = Modifier
            .fillMaxWidth()
            .heightIn(min = MinimumTouchTarget),
    ) {
        Column(
            modifier = Modifier.padding(SideBySideTheme.spacing.cardPadding),
            verticalArrangement = Arrangement.spacedBy(SideBySideTheme.spacing.step1),
        ) {
            Text(
                text = stringResource(labelRes),
                style = MaterialTheme.typography.labelMedium,
                color = SideBySideTheme.colors.textSecondary,
            )
            Text(
                text = value ?: stringResource(placeholderRes),
                style = MaterialTheme.typography.bodyLarge.copy(
                    fontWeight = if (value != null) FontWeight.Medium else FontWeight.Normal,
                ),
                color = if (value != null) {
                    SideBySideTheme.colors.textPrimary
                } else {
                    SideBySideTheme.colors.textSecondary
                },
            )
        }
    }
}
