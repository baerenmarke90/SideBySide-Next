package de.sidebyside.next.plan

import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.heightIn
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.widthIn
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.AlertDialog
import androidx.compose.material3.Button
import androidx.compose.material3.HorizontalDivider
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Surface
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.saveable.rememberSaveable
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.LocalConfiguration
import androidx.compose.ui.res.stringResource
import androidx.compose.ui.semantics.Role
import androidx.compose.ui.semantics.heading
import androidx.compose.ui.semantics.semantics
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.unit.Dp
import androidx.compose.ui.unit.dp
import de.sidebyside.next.design.MinimumTouchTarget
import de.sidebyside.next.design.SideBySideDisplayFamily
import de.sidebyside.next.design.SideBySideTheme
import de.sidebyside.next.reference.R
import de.sidebyside.next.shell.UiProblem
import de.sidebyside.next.shell.UiStatePanel
import de.sidebyside.next.shell.WindowWidthClass
import de.sidebyside.next.shell.windowWidthClassFor
import java.util.UUID
import sidebyside.api.models.PlaceDetail
import sidebyside.api.models.PlanDetail
import sidebyside.api.models.PlanStatus
import sidebyside.api.models.WishDetail

internal val ReadingMeasure: Dp = 560.dp

/**
 * The widest the planning stream is allowed to become on a Foldable or any
 * other large window.
 *
 * `docs/PARTNER-APP-EXPERIENCE-STANDARD.md` section 0/11: a wider window buys
 * calmer measure and more breathing room around the same product, not a second
 * management column and not more permanently visible actions. Planning shows
 * the identical composition at every width; only the measure changes.
 */
private val ExpandedContentMeasure: Dp = 720.dp

/**
 * Planning.
 *
 * A shared future map rather than two record lists: what the couple dreams
 * about, what they have actually taken on, and — first of all — the one thing
 * that is coming up next.
 *
 * Everything that manages a wish or a plan lives behind the content it belongs
 * to. Tapping a wish or a plan opens that one thing; nothing on the overview
 * carries a row of lifecycle buttons, and no create form is permanently
 * unfolded on it. The overview therefore has exactly one dominant action —
 * capturing a wish — and every other move starts from the thing it acts on.
 *
 * A wish that became a plan is deliberately not listed again above; the view
 * model keeps only `OPEN` ones, because showing an intention twice would
 * suggest there are two of them. The same reasoning removes the focal plan
 * from the plan stack below it.
 */
@Composable
fun PlanScreen(
    wishes: List<WishDetail>,
    plans: List<PlanDetail>,
    places: List<PlaceDetail>,
    busy: Boolean,
    problem: UiProblem?,
    onAddWish: (String) -> Unit,
    onEditWish: (id: UUID, title: String) -> Unit,
    onPlanWish: (
        id: UUID,
        title: String,
        description: String,
        placeId: UUID?,
        startOn: String?,
        startAt: String?,
    ) -> Unit,
    onRemoveWish: (UUID) -> Unit,
    onCreatePlan: (
        title: String,
        description: String,
        placeId: UUID?,
        startOn: String?,
        startAt: String?,
    ) -> Unit,
    onEditPlan: (id: UUID, title: String, description: String, placeId: UUID?) -> Unit,
    onSchedule: (id: UUID, startOn: String, startAt: String) -> Unit,
    onUnschedule: (UUID) -> Unit,
    onComplete: (id: UUID, experiencedOn: String) -> Unit,
    onReturnToWish: (UUID) -> Unit,
    onDeletePlan: (UUID) -> Unit,
    /** Creates a new shared Place with just a name, from inside Planning. */
    onCreatePlace: (String) -> Unit,
    /**
     * Opens the couple's shared places.
     *
     * Deliberately without a default, for the same reason every other
     * navigation entry point in this client is: an optional one that a
     * caller forgets to pass disappears from the product without breaking
     * the build.
     */
    onOpenPlaces: () -> Unit,
    /**
     * Opens the couple's shared lists.
     *
     * Deliberately without a default, for the same reason as [onOpenPlaces].
     */
    onOpenCollections: () -> Unit,
    /**
     * Opens the couple's shared Chapters.
     *
     * Deliberately without a default, for the same reason as [onOpenPlaces].
     */
    onOpenChapters: () -> Unit,
    modifier: Modifier = Modifier,
    /** Non-null only while [wishes]/[plans] are a stale M2-D18 cache fallback. */
    cachedAt: java.time.Instant? = null,
) {
    // At most one focused surface is open at a time, and which one survives a
    // rotation and process death. Encoded as a string rather than held as a
    // parcelable, because `rememberSaveable` then needs no custom saver and
    // the screen keeps the same shape it had when the targets were plain ids.
    var focus by rememberSaveable { mutableStateOf<String?>(null) }
    // Destructive confirmations are deliberately a separate slot: one is
    // raised *from* an open focused surface, and closing the confirmation must
    // not also close what raised it.
    var confirm by rememberSaveable { mutableStateOf<String?>(null) }

    val compact = windowWidthClassFor(LocalConfiguration.current.screenWidthDp.dp) ==
        WindowWidthClass.Compact
    val contentMeasure = if (compact) Dp.Unspecified else ExpandedContentMeasure
    val itemModifier = Modifier.widthIn(max = contentMeasure).fillMaxWidth()

    // The one plan that is actually coming up. It leads the screen and is not
    // repeated in the stack below.
    val focal = plans
        .filter { it.status == PlanStatus.PLANNED && it.plannedStart != null }
        .minByOrNull { it.plannedStart!! }
    val remainingPlans = plans.filter { it.id != focal?.id }

    LazyColumn(
        modifier = modifier.fillMaxWidth(),
        contentPadding = androidx.compose.foundation.layout.PaddingValues(
            SideBySideTheme.spacing.pageMargin,
        ),
        horizontalAlignment = Alignment.CenterHorizontally,
        verticalArrangement = Arrangement.spacedBy(SideBySideTheme.spacing.step5),
    ) {
        item(key = "masthead") {
            Column(
                modifier = itemModifier,
                verticalArrangement = Arrangement.spacedBy(SideBySideTheme.spacing.step2),
            ) {
                Text(
                    text = stringResource(R.string.plan_title),
                    style = MaterialTheme.typography.headlineMedium
                        .copy(fontFamily = SideBySideDisplayFamily),
                    color = SideBySideTheme.colors.textPrimary,
                    modifier = Modifier.semantics { heading() },
                )
                Text(
                    text = stringResource(planningLeadFor(focal, plans, wishes)),
                    style = MaterialTheme.typography.bodyMedium,
                    color = SideBySideTheme.colors.textSecondary,
                    modifier = Modifier.widthIn(max = ReadingMeasure),
                )
            }
        }

        cachedAt?.let {
            item(key = "cached-banner") {
                de.sidebyside.next.shell.CachedContentBanner(it)
            }
        }

        problem?.let { item(key = "problem") { UiStatePanel(problem = it, modifier = itemModifier) } }

        focal?.let { plan ->
            item(key = "focal") {
                FocalPlanCard(
                    plan = plan,
                    onOpen = { focus = "plan:" + plan.id },
                    modifier = itemModifier,
                )
            }
        }

        // The single dominant action. Direct plan creation is reachable from
        // inside the composer it opens, so the overview never carries two
        // competing create affordances.
        item(key = "capture") {
            Button(
                onClick = { focus = NEW_WISH },
                enabled = !busy,
                modifier = itemModifier.heightIn(min = MinimumTouchTarget),
            ) {
                Text(stringResource(R.string.plan_capture))
            }
        }

        item(key = "wishes-heading") {
            SectionHeading(R.string.plan_wishes_heading, itemModifier)
        }

        if (wishes.isEmpty() && !busy) {
            item(key = "wishes-empty") {
                QuietLine(R.string.plan_wishes_empty, itemModifier)
            }
        }

        items(count = wishes.size, key = { index -> "wish-" + wishes[index].id }) { index ->
            val wish = wishes[index]
            WishCard(
                wish = wish,
                onOpen = { focus = "wish:" + wish.id },
                modifier = itemModifier,
            )
        }

        item(key = "plans-heading") {
            SectionHeading(R.string.plan_plans_heading, itemModifier)
        }

        if (plans.isEmpty() && !busy) {
            item(key = "plans-empty") {
                QuietLine(R.string.plan_plans_empty, itemModifier)
            }
        }

        items(
            count = remainingPlans.size,
            key = { index -> "plan-" + remainingPlans[index].id },
        ) { index ->
            val plan = remainingPlans[index]
            PlanCard(
                plan = plan,
                compact = compact,
                onOpen = { focus = "plan:" + plan.id },
                modifier = itemModifier,
            )
        }

        item(key = "elsewhere") {
            PlanningElsewhere(
                onOpenPlaces = onOpenPlaces,
                onOpenCollections = onOpenCollections,
                onOpenChapters = onOpenChapters,
                modifier = itemModifier,
            )
        }
    }

    FocusedPlanningSurface(
        focus = focus,
        wishes = wishes,
        plans = plans,
        places = places,
        busy = busy,
        setFocus = { focus = it },
        setConfirm = { confirm = it },
        onAddWish = onAddWish,
        onEditWish = onEditWish,
        onPlanWish = onPlanWish,
        onCreatePlan = onCreatePlan,
        onEditPlan = onEditPlan,
        onSchedule = onSchedule,
        onUnschedule = onUnschedule,
        onComplete = onComplete,
        onCreatePlace = onCreatePlace,
    )

    PlanningConfirmation(
        confirm = confirm,
        wishes = wishes,
        plans = plans,
        setFocus = { focus = it },
        setConfirm = { confirm = it },
        onRemoveWish = onRemoveWish,
        onReturnToWish = onReturnToWish,
        onDeletePlan = onDeletePlan,
    )
}

/** The focused surface currently open, resolved against live data. */
@Composable
private fun FocusedPlanningSurface(
    focus: String?,
    wishes: List<WishDetail>,
    plans: List<PlanDetail>,
    places: List<PlaceDetail>,
    busy: Boolean,
    setFocus: (String?) -> Unit,
    setConfirm: (String?) -> Unit,
    onAddWish: (String) -> Unit,
    onEditWish: (id: UUID, title: String) -> Unit,
    onPlanWish: (
        id: UUID,
        title: String,
        description: String,
        placeId: UUID?,
        startOn: String?,
        startAt: String?,
    ) -> Unit,
    onCreatePlan: (
        title: String,
        description: String,
        placeId: UUID?,
        startOn: String?,
        startAt: String?,
    ) -> Unit,
    onEditPlan: (id: UUID, title: String, description: String, placeId: UUID?) -> Unit,
    onSchedule: (id: UUID, startOn: String, startAt: String) -> Unit,
    onUnschedule: (UUID) -> Unit,
    onComplete: (id: UUID, experiencedOn: String) -> Unit,
    onCreatePlace: (String) -> Unit,
) {
    val target = focus ?: return
    val kind = target.substringBefore(':')
    val argument = target.substringAfter(':', "")
    val dismiss = { setFocus(null) }

    // A wish or plan can disappear underneath an open surface — the partner
    // deleted it, or a re-read dropped it. Closing is the only honest answer;
    // guessing at the missing object would show stale content as if it were
    // still there.
    fun wish(): WishDetail? = wishes.firstOrNull { it.id.toString() == argument }
    fun plan(): PlanDetail? = plans.firstOrNull { it.id.toString() == argument }

    when (kind) {
        NEW_WISH -> WishComposerSheet(
            initialTitle = "",
            busy = busy,
            headingRes = R.string.plan_wish_new_title,
            submitLabelRes = R.string.plan_wish_save,
            onSwitchToPlan = { draft -> setFocus(NEW_PLAN + ":" + draft) },
            onDismiss = dismiss,
            onSubmit = { title ->
                setFocus(null)
                onAddWish(title)
            },
        )

        "wish-edit" -> {
            val wish = wish() ?: return dismiss()
            WishComposerSheet(
                initialTitle = wish.title,
                busy = busy,
                headingRes = R.string.plan_wish_edit_title,
                submitLabelRes = R.string.plan_wish_save_changes,
                onSwitchToPlan = null,
                onDismiss = dismiss,
                onSubmit = { title ->
                    setFocus(null)
                    onEditWish(wish.id, title)
                },
            )
        }

        "wish" -> {
            val wish = wish() ?: return dismiss()
            WishSheet(
                wish = wish,
                busy = busy,
                onMakePlan = { setFocus("wish-plan:" + wish.id) },
                onEdit = { setFocus("wish-edit:" + wish.id) },
                onRemove = {
                    setFocus(null)
                    setConfirm("wish-remove:" + wish.id)
                },
                onDismiss = dismiss,
            )
        }

        "wish-plan" -> {
            val wish = wish() ?: return dismiss()
            WishToPlanSheet(
                wish = wish,
                places = places,
                busy = busy,
                onDismiss = dismiss,
                onCreatePlace = onCreatePlace,
                onSubmit = { title, description, placeId, startOn, startAt ->
                    setFocus(null)
                    onPlanWish(wish.id, title, description, placeId, startOn, startAt)
                },
            )
        }

        NEW_PLAN -> PlanComposerSheet(
            places = places,
            busy = busy,
            headingRes = R.string.plan_new_title,
            submitLabelRes = R.string.plan_add,
            initialTitle = argument,
            allowSchedule = true,
            onDismiss = dismiss,
            onCreatePlace = onCreatePlace,
            onSubmit = { title, description, placeId, startOn, startAt ->
                setFocus(null)
                onCreatePlan(title, description, placeId, startOn, startAt)
            },
        )

        "plan-edit" -> {
            val plan = plan() ?: return dismiss()
            PlanComposerSheet(
                places = places,
                busy = busy,
                headingRes = R.string.plan_edit_title,
                submitLabelRes = R.string.plan_save_changes,
                initialTitle = plan.title,
                initialDescription = plan.description.orEmpty(),
                initialPlaceId = plan.placeId,
                onDismiss = dismiss,
                onCreatePlace = onCreatePlace,
                onSubmit = { title, description, placeId, _, _ ->
                    setFocus(null)
                    onEditPlan(plan.id, title, description, placeId)
                },
            )
        }

        "plan" -> {
            val plan = plan() ?: return dismiss()
            PlanSheet(
                plan = plan,
                places = places,
                busy = busy,
                onEdit = { setFocus("plan-edit:" + plan.id) },
                onSchedule = { setFocus("plan-schedule:" + plan.id) },
                onUnschedule = {
                    setFocus(null)
                    onUnschedule(plan.id)
                },
                onComplete = { setFocus("plan-complete:" + plan.id) },
                onReturnToWish = {
                    setFocus(null)
                    setConfirm("plan-return:" + plan.id)
                },
                onDelete = {
                    setFocus(null)
                    setConfirm("plan-delete:" + plan.id)
                },
                onDismiss = dismiss,
            )
        }

        "plan-schedule" -> {
            val plan = plan() ?: return dismiss()
            PlanScheduleSheet(
                plan = plan,
                busy = busy,
                onDismiss = dismiss,
                onSubmit = { startOn, startAt ->
                    setFocus(null)
                    onSchedule(plan.id, startOn, startAt)
                },
            )
        }

        "plan-complete" -> {
            val plan = plan() ?: return dismiss()
            PlanCompleteSheet(
                plan = plan,
                busy = busy,
                onDismiss = dismiss,
                onSubmit = { experiencedOn ->
                    setFocus(null)
                    onComplete(plan.id, experiencedOn)
                },
            )
        }

        else -> dismiss()
    }
}

/**
 * The three bounded destructive confirmations, unchanged in substance.
 *
 * Each names the object's fate before it happens, and none of them is reachable
 * without first having opened the thing it acts on.
 */
@Composable
private fun PlanningConfirmation(
    confirm: String?,
    wishes: List<WishDetail>,
    plans: List<PlanDetail>,
    setFocus: (String?) -> Unit,
    setConfirm: (String?) -> Unit,
    onRemoveWish: (UUID) -> Unit,
    onReturnToWish: (UUID) -> Unit,
    onDeletePlan: (UUID) -> Unit,
) {
    val target = confirm ?: return
    val kind = target.substringBefore(':')
    val argument = target.substringAfter(':', "")
    val dismiss = { setConfirm(null) }

    when (kind) {
        // Discarding a wish is small but irreversible, so it is confirmed like
        // the two plan reversals rather than firing straight off a tap.
        "wish-remove" -> {
            val wish = wishes.firstOrNull { it.id.toString() == argument } ?: return dismiss()
            DestructiveConfirmation(
                titleRes = R.string.plan_wish_remove_title,
                bodyRes = R.string.plan_wish_remove_body,
                confirmRes = R.string.plan_wish_remove,
                onDismiss = dismiss,
                onConfirm = {
                    setConfirm(null)
                    onRemoveWish(wish.id)
                },
            )
        }

        "plan-return" -> {
            val plan = plans.firstOrNull { it.id.toString() == argument } ?: return dismiss()
            DestructiveConfirmation(
                titleRes = R.string.plan_return_title,
                // The wish receives nothing back from the plan, so this loses
                // whatever was written into it. Said before, not after.
                bodyRes = R.string.plan_return_body,
                confirmRes = R.string.plan_return_to_wish,
                onDismiss = dismiss,
                onConfirm = {
                    setConfirm(null)
                    setFocus(null)
                    onReturnToWish(plan.id)
                },
            )
        }

        "plan-delete" -> {
            val plan = plans.firstOrNull { it.id.toString() == argument } ?: return dismiss()
            DestructiveConfirmation(
                titleRes = R.string.plan_delete_title,
                bodyRes = R.string.plan_delete_body,
                confirmRes = R.string.plan_delete,
                onDismiss = dismiss,
                onConfirm = {
                    setConfirm(null)
                    setFocus(null)
                    onDeletePlan(plan.id)
                },
            )
        }

        else -> dismiss()
    }
}

@Composable
private fun DestructiveConfirmation(
    titleRes: Int,
    bodyRes: Int,
    confirmRes: Int,
    onDismiss: () -> Unit,
    onConfirm: () -> Unit,
) {
    AlertDialog(
        onDismissRequest = onDismiss,
        title = { Text(stringResource(titleRes)) },
        text = { Text(stringResource(bodyRes)) },
        confirmButton = { TextButton(onClick = onConfirm) { Text(stringResource(confirmRes)) } },
        dismissButton = {
            TextButton(onClick = onDismiss) { Text(stringResource(R.string.plan_cancel)) }
        },
    )
}

/**
 * The one thing coming up next, given the weight of a focal point rather than
 * the weight of the next row in a list.
 */
@Composable
private fun FocalPlanCard(plan: PlanDetail, onOpen: () -> Unit, modifier: Modifier = Modifier) {
    val openLabel = stringResource(R.string.plan_open)
    Surface(
        shape = RoundedCornerShape(SideBySideTheme.radii.hero),
        color = SideBySideTheme.colors.brandSurface,
        modifier = modifier,
    ) {
        Column(
            modifier = Modifier
                .clickable(onClickLabel = openLabel, role = Role.Button, onClick = onOpen)
                .padding(SideBySideTheme.spacing.cardPadding),
            verticalArrangement = Arrangement.spacedBy(SideBySideTheme.spacing.step2),
        ) {
            Text(
                text = stringResource(R.string.plan_focus_next),
                style = MaterialTheme.typography.labelLarge,
                color = SideBySideTheme.colors.brandStrong,
            )
            Text(
                text = plan.title,
                style = MaterialTheme.typography.headlineSmall
                    .copy(fontFamily = SideBySideDisplayFamily),
                color = SideBySideTheme.colors.textPrimary,
                modifier = Modifier.widthIn(max = ReadingMeasure),
            )
            plan.plannedStart?.let { start ->
                Text(
                    text = stringResource(R.string.plan_scheduled_for, formattedDateTime(start)),
                    style = MaterialTheme.typography.bodyMedium,
                    color = SideBySideTheme.colors.textSecondary,
                )
            }
        }
    }
}

/**
 * A wish, as content.
 *
 * No edit, convert or discard button: the whole card opens the wish, and every
 * move it allows lives there.
 */
@Composable
private fun WishCard(wish: WishDetail, onOpen: () -> Unit, modifier: Modifier = Modifier) {
    val openLabel = stringResource(R.string.plan_wish_open)
    Surface(
        shape = RoundedCornerShape(SideBySideTheme.radii.card),
        color = SideBySideTheme.colors.surface,
        modifier = modifier,
    ) {
        Column(
            modifier = Modifier
                .clickable(onClickLabel = openLabel, role = Role.Button, onClick = onOpen)
                .padding(SideBySideTheme.spacing.cardPadding)
                .heightIn(min = MinimumTouchTarget),
            verticalArrangement = Arrangement.spacedBy(SideBySideTheme.spacing.step1),
        ) {
            Text(
                text = wish.title,
                style = MaterialTheme.typography.titleMedium,
                color = SideBySideTheme.colors.textPrimary,
                modifier = Modifier.widthIn(max = ReadingMeasure),
            )
            wish.creator.displayName.takeIf { it.isNotBlank() }?.let { name ->
                Text(
                    text = stringResource(R.string.plan_wish_by, name),
                    style = MaterialTheme.typography.bodySmall,
                    color = SideBySideTheme.colors.textSecondary,
                )
            }
        }
    }
}

/**
 * A plan, as content and current state.
 *
 * The status word survives a colour-blind reading and a screen reader; the
 * lifecycle itself is not a row of buttons here but lives inside the plan.
 */
@Composable
private fun PlanCard(
    plan: PlanDetail,
    compact: Boolean,
    onOpen: () -> Unit,
    modifier: Modifier = Modifier,
) {
    val openLabel = stringResource(R.string.plan_open)
    Surface(
        shape = RoundedCornerShape(SideBySideTheme.radii.card),
        color = SideBySideTheme.colors.surface,
        modifier = modifier,
    ) {
        Column(
            modifier = Modifier
                .clickable(onClickLabel = openLabel, role = Role.Button, onClick = onOpen)
                .padding(SideBySideTheme.spacing.cardPadding)
                .heightIn(min = MinimumTouchTarget),
            verticalArrangement = Arrangement.spacedBy(SideBySideTheme.spacing.step2),
        ) {
            Text(
                text = stringResource(plan.status.labelRes()),
                style = MaterialTheme.typography.labelSmall,
                color = plan.status.accent(),
            )
            Text(
                text = plan.title,
                style = MaterialTheme.typography.titleMedium,
                color = SideBySideTheme.colors.textPrimary,
                modifier = Modifier.widthIn(max = ReadingMeasure),
            )
            plan.description?.takeIf { it.isNotBlank() }?.let { text ->
                Text(
                    text = text,
                    style = MaterialTheme.typography.bodyMedium,
                    color = SideBySideTheme.colors.textSecondary,
                    // A wider window spends its room on more of what the couple
                    // wrote, not on more controls.
                    maxLines = if (compact) 2 else 3,
                    overflow = TextOverflow.Ellipsis,
                    modifier = Modifier.widthIn(max = ReadingMeasure),
                )
            }
            planTimingLine(plan)?.let { line ->
                Text(
                    text = line,
                    style = MaterialTheme.typography.bodySmall,
                    color = SideBySideTheme.colors.textSecondary,
                )
            }
        }
    }
}

/**
 * Places, Collections and Chapters.
 *
 * They belong to planning but are not the planning lifecycle, so they sit
 * below it as one quiet group of navigation rows instead of three equally
 * weighted boxes competing with the couple's own wishes and plans.
 */
@Composable
private fun PlanningElsewhere(
    onOpenPlaces: () -> Unit,
    onOpenCollections: () -> Unit,
    onOpenChapters: () -> Unit,
    modifier: Modifier = Modifier,
) {
    Column(
        modifier = modifier,
        verticalArrangement = Arrangement.spacedBy(SideBySideTheme.spacing.step3),
    ) {
        Text(
            text = stringResource(R.string.plan_elsewhere_heading),
            style = MaterialTheme.typography.labelLarge,
            color = SideBySideTheme.colors.textSecondary,
            modifier = Modifier.semantics { heading() },
        )
        Surface(
            shape = RoundedCornerShape(SideBySideTheme.radii.card),
            color = SideBySideTheme.colors.surfaceSubtle,
            modifier = Modifier.fillMaxWidth(),
        ) {
            Column {
                ElsewhereRow(R.string.places_title, onOpenPlaces)
                HorizontalDivider(color = SideBySideTheme.colors.borderSubtle)
                ElsewhereRow(R.string.collections_title, onOpenCollections)
                HorizontalDivider(color = SideBySideTheme.colors.borderSubtle)
                ElsewhereRow(R.string.chapters_title, onOpenChapters)
            }
        }
    }
}

@Composable
private fun ElsewhereRow(labelRes: Int, onClick: () -> Unit) {
    Surface(
        onClick = onClick,
        color = SideBySideTheme.colors.surfaceSubtle,
        modifier = Modifier
            .fillMaxWidth()
            .heightIn(min = MinimumTouchTarget),
    ) {
        Text(
            text = stringResource(labelRes),
            style = MaterialTheme.typography.bodyLarge,
            color = SideBySideTheme.colors.textPrimary,
            modifier = Modifier.padding(SideBySideTheme.spacing.cardPadding),
        )
    }
}

@Composable
private fun SectionHeading(labelRes: Int, modifier: Modifier = Modifier) {
    Text(
        text = stringResource(labelRes),
        style = MaterialTheme.typography.titleMedium,
        color = SideBySideTheme.colors.brandStrong,
        modifier = modifier
            .padding(top = SideBySideTheme.spacing.step4)
            .semantics { heading() },
    )
}

@Composable
private fun QuietLine(labelRes: Int, modifier: Modifier = Modifier) {
    Text(
        text = stringResource(labelRes),
        style = MaterialTheme.typography.bodyMedium,
        color = SideBySideTheme.colors.textSecondary,
        modifier = modifier.widthIn(max = ReadingMeasure),
    )
}

/**
 * The one line under the title, chosen from where the couple actually stands.
 *
 * Not decoration: it is what tells someone opening Planning whether anything is
 * waiting for them before they read a single card.
 */
private fun planningLeadFor(
    focal: PlanDetail?,
    plans: List<PlanDetail>,
    wishes: List<WishDetail>,
): Int = when {
    focal != null -> R.string.plan_intro
    plans.any { it.status == PlanStatus.IDEA } -> R.string.plan_focus_undated
    wishes.isNotEmpty() -> R.string.plan_focus_wishes_only
    plans.isNotEmpty() -> R.string.plan_focus_all_experienced
    else -> R.string.plan_focus_empty
}

internal const val NEW_WISH: String = "wish-new"
internal const val NEW_PLAN: String = "plan-new"
