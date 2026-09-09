package de.sidebyside.next.plan

import android.content.Context
import androidx.compose.ui.test.assertCountEquals
import androidx.compose.ui.test.assertIsEnabled
import androidx.compose.ui.test.assertIsNotEnabled
import androidx.compose.ui.test.hasSetTextAction
import androidx.compose.ui.test.hasText
import androidx.compose.ui.test.junit4.createComposeRule
import androidx.compose.ui.test.onAllNodesWithText
import androidx.compose.ui.test.onFirst
import androidx.compose.ui.test.onNodeWithText
import androidx.compose.ui.test.performClick
import androidx.compose.ui.test.performScrollTo
import androidx.compose.ui.test.performTextInput
import androidx.compose.ui.test.performTextReplacement
import androidx.test.core.app.ApplicationProvider
import de.sidebyside.next.design.SideBySideTheme
import de.sidebyside.next.reference.R
import java.time.LocalDate
import java.time.OffsetDateTime
import java.time.ZoneId
import java.time.format.DateTimeFormatter
import java.time.format.FormatStyle
import java.util.TimeZone
import java.util.UUID
import org.junit.Assert.assertEquals
import org.junit.Rule
import org.junit.Test
import org.junit.runner.RunWith
import org.robolectric.RobolectricTestRunner
import org.robolectric.annotation.Config
import sidebyside.api.models.AuthorSummary
import sidebyside.api.models.PlaceDetail
import sidebyside.api.models.PlanDetail
import sidebyside.api.models.PlanStatus
import sidebyside.api.models.ResourceCapabilities
import sidebyside.api.models.WishDetail
import sidebyside.api.models.WishStatus

/**
 * What #830 changed about Planning, pinned at the level it was changed on.
 *
 * The subject is the product model, not the pixels: the overview carries
 * content and one dominant action, every lifecycle move is reached through the
 * wish or plan it belongs to, and the destructive confirmations that were
 * already correct still ask before they act. A wider window changes none of
 * that.
 */
@RunWith(RobolectricTestRunner::class)
@Config(sdk = [35], qualifiers = "w320dp-h1600dp")
class PlanScreenTest {
    @get:Rule
    val composeRule = createComposeRule()

    private val context: Context get() = ApplicationProvider.getApplicationContext()
    private val place = PlaceDetail(
        address = null,
        capabilities = CAPABILITIES,
        createdAt = OffsetDateTime.now(),
        createdBy = UUID.randomUUID(),
        creator = AUTHOR,
        description = null,
        id = UUID.randomUUID(),
        latitude = null,
        longitude = null,
        name = "The coast",
        spaceId = SPACE,
        updatedAt = OffsetDateTime.now(),
        version = 1,
    )

    // --- Overview composition -------------------------------------------

    @Test
    fun theOverviewCarriesNoCreateFormAtAll() {
        render(wishes = listOf(aWish("A weekend by the sea")), plans = listOf(aPlan(PlanStatus.IDEA)))

        // Neither the wish field nor the plan form is on the overview, so the
        // two cannot be open at the same time on it either.
        composeRule.onAllNodes(hasSetTextAction()).assertCountEquals(0)
    }

    @Test
    fun theOverviewHasOneDominantActionAndNoLifecycleButtons() {
        render(wishes = listOf(aWish("A weekend by the sea")), plans = listOf(aPlan(PlanStatus.IDEA)))

        composeRule.onNodeWithText(context.getString(R.string.plan_capture))
            .performScrollTo()
            .assertIsEnabled()

        for (hidden in LIFECYCLE_LABELS) {
            composeRule.onNodeWithText(context.getString(hidden)).assertDoesNotExist()
        }
    }

    @Test
    fun placesCollectionsAndChaptersAreQuietNavigationRatherThanEqualBoxes() {
        render()

        // The three utility Surfaces with their own intro paragraph and their
        // own button are gone — the buttons' labels no longer exist as
        // resources at all — and what is left is one grouped set of quiet
        // navigation rows.
        composeRule.onNodeWithText(context.getString(R.string.places_intro)).assertDoesNotExist()
        composeRule.onNodeWithText(context.getString(R.string.places_title))
            .performScrollTo()
            .assertExists()
    }

    @Test
    fun openingPlacesFromTheQuietGroupStillNavigates() {
        var opened = false
        render(onOpenPlaces = { opened = true })

        composeRule.onNodeWithText(context.getString(R.string.places_title))
            .performScrollTo()
            .performClick()

        assertEquals(true, opened)
    }

    @Test
    @Config(qualifiers = "w840dp-h1600dp")
    fun aLargeWindowShowsTheSameProductModelWithoutExtraControls() {
        render(wishes = listOf(aWish("A weekend by the sea")), plans = listOf(aPlan(PlanStatus.IDEA)))

        composeRule.onNodeWithText(context.getString(R.string.plan_capture))
            .performScrollTo()
            .assertIsEnabled()
        composeRule.onAllNodes(hasSetTextAction()).assertCountEquals(0)
        for (hidden in LIFECYCLE_LABELS) {
            composeRule.onNodeWithText(context.getString(hidden)).assertDoesNotExist()
        }
    }

    // --- Wishes ----------------------------------------------------------

    @Test
    fun capturingAWishGoesThroughTheFocusedComposer() {
        var captured: String? = null
        render(onAddWish = { captured = it })

        composeRule.onNodeWithText(context.getString(R.string.plan_capture))
            .performScrollTo()
            .performClick()
        composeRule.onNode(hasSetTextAction()).performTextInput("A weekend by the sea")
        composeRule.onNodeWithText(context.getString(R.string.plan_wish_save)).performClick()

        assertEquals("A weekend by the sea", captured)
    }

    @Test
    fun tappingAWishOpensItRatherThanActingOnIt() {
        render(wishes = listOf(aWish("A weekend by the sea")))

        composeRule.onNodeWithText("A weekend by the sea").performScrollTo().performClick()

        // The moves a wish allows live in the wish, not on its card.
        composeRule.onNodeWithText(context.getString(R.string.plan_wish_make_plan)).assertIsEnabled()
        composeRule.onNodeWithText(context.getString(R.string.plan_wish_edit)).assertIsEnabled()
        composeRule.onNodeWithText(context.getString(R.string.plan_wish_remove)).assertIsEnabled()
    }

    @Test
    fun editingAWishPrefillsTheCurrentTitle() {
        var edited: Pair<UUID, String>? = null
        render(
            wishes = listOf(aWish("A weekend by the sea")),
            onEditWish = { id, title -> edited = id to title },
        )

        composeRule.onNodeWithText("A weekend by the sea").performScrollTo().performClick()
        composeRule.onNodeWithText(context.getString(R.string.plan_wish_edit)).performClick()
        // Matched by the editable field specifically — the card and the sheet
        // heading behind it carry the same text as non-editable Text nodes.
        composeRule.onNode(hasText("A weekend by the sea") and hasSetTextAction())
            .performTextReplacement("A weekend inland")
        composeRule.onNodeWithText(context.getString(R.string.plan_wish_save_changes)).performClick()

        assertEquals("A weekend inland", edited?.second)
    }

    @Test
    fun discardingAWishIsConfirmedBeforeItHappens() {
        var removed: UUID? = null
        val wish = aWish("A weekend by the sea")
        render(wishes = listOf(wish), onRemoveWish = { removed = it })

        composeRule.onNodeWithText("A weekend by the sea").performScrollTo().performClick()
        composeRule.onNodeWithText(context.getString(R.string.plan_wish_remove)).performClick()

        assertEquals(null, removed)
        composeRule.onNodeWithText(context.getString(R.string.plan_wish_remove_body)).assertExists()
        composeRule.onAllNodesWithText(context.getString(R.string.plan_wish_remove))
            .onFirst()
            .performClick()

        assertEquals(wish.id, removed)
    }

    @Test
    fun turningAWishIntoAPlanKeepsTheWishInViewAndDefaultsItsTitle() {
        val wish = aWish("A weekend by the sea")
        var planned: List<Any?>? = null
        render(
            wishes = listOf(wish),
            onPlanWish = { id, title, description, placeId ->
                planned = listOf(id, title, description, placeId)
            },
        )

        composeRule.onNodeWithText("A weekend by the sea").performScrollTo().performClick()
        composeRule.onNodeWithText(context.getString(R.string.plan_wish_make_plan)).performClick()

        // The wish the plan comes from stays visible above the fields.
        composeRule.onNodeWithText(context.getString(R.string.plan_wish_make_plan_context))
            .assertExists()
        composeRule.onNode(hasText("A weekend by the sea") and hasSetTextAction()).assertIsEnabled()
        composeRule.onNodeWithText(context.getString(R.string.plan_wish_make_plan_confirm))
            .performScrollTo()
            .performClick()

        assertEquals(listOf(wish.id, "A weekend by the sea", "", null), planned)
    }

    @Test
    fun optionalPlanFieldsStayFoldedUntilTheyAreAskedFor() {
        val wish = aWish("A weekend by the sea")
        var planned: List<Any?>? = null
        render(
            wishes = listOf(wish),
            onPlanWish = { _, _, description, placeId -> planned = listOf(description, placeId) },
        )

        composeRule.onNodeWithText("A weekend by the sea").performScrollTo().performClick()
        composeRule.onNodeWithText(context.getString(R.string.plan_wish_make_plan)).performClick()

        composeRule.onNodeWithText(context.getString(R.string.plan_description_hint))
            .assertDoesNotExist()
        composeRule.onNodeWithText(context.getString(R.string.plan_optional_details))
            .performScrollTo()
            .performClick()
        composeRule.onNodeWithText(context.getString(R.string.plan_description_hint))
            .performScrollTo()
            .performTextInput("Somewhere quiet")
        composeRule.onNodeWithText(context.getString(R.string.place_picker_none))
            .performScrollTo()
            .performClick()
        composeRule.onNodeWithText("The coast").performClick()
        composeRule.onNodeWithText(context.getString(R.string.plan_wish_make_plan_confirm))
            .performScrollTo()
            .performClick()

        assertEquals(listOf("Somewhere quiet", place.id), planned)
    }

    // --- Plans -----------------------------------------------------------

    @Test
    fun creatingAPlanDirectlyIsReachedFromInsideTheWishComposer() {
        var submitted: Triple<String, String, UUID?>? = null
        render(onCreatePlan = { title, description, placeId ->
            submitted = Triple(title, description, placeId)
        })

        composeRule.onNodeWithText(context.getString(R.string.plan_capture))
            .performScrollTo()
            .performClick()
        composeRule.onNode(hasSetTextAction()).performTextInput("A weekend away")
        composeRule.onNodeWithText(context.getString(R.string.plan_wish_direct_plan))
            .performScrollTo()
            .performClick()

        // What was already typed comes along rather than being asked for twice.
        composeRule.onNode(hasText("A weekend away") and hasSetTextAction()).assertIsEnabled()
        composeRule.onNodeWithText(context.getString(R.string.plan_optional_details))
            .performScrollTo()
            .performClick()
        composeRule.onNodeWithText(context.getString(R.string.plan_description_hint))
            .performScrollTo()
            .performTextInput("Somewhere quiet")
        composeRule.onNodeWithText(context.getString(R.string.plan_add))
            .performScrollTo()
            .performClick()

        assertEquals(Triple("A weekend away", "Somewhere quiet", null), submitted)
    }

    @Test
    fun tappingAPlanOpensItRatherThanActingOnIt() {
        render(plans = listOf(aPlan(PlanStatus.IDEA, title = "A weekend away")))

        composeRule.onNodeWithText("A weekend away").performScrollTo().performClick()

        // An idea can be given a time, corrected, or sent back — and that is
        // all, exactly as the status machine allows.
        composeRule.onNodeWithText(context.getString(R.string.plan_schedule)).assertIsEnabled()
        composeRule.onNodeWithText(context.getString(R.string.plan_edit)).assertIsEnabled()
        composeRule.onNodeWithText(context.getString(R.string.plan_return_to_wish)).assertIsEnabled()
        composeRule.onNodeWithText(context.getString(R.string.plan_complete)).assertDoesNotExist()
    }

    @Test
    fun aCompletedPlanOffersNoFurtherTransition() {
        render(
            plans = listOf(
                aPlan(PlanStatus.COMPLETED, title = "A weekend away")
                    .copy(experiencedOn = LocalDate.parse("2026-08-30")),
            ),
        )

        composeRule.onNodeWithText("A weekend away").performScrollTo().performClick()

        composeRule.onNodeWithText(context.getString(R.string.plan_schedule)).assertDoesNotExist()
        composeRule.onNodeWithText(context.getString(R.string.plan_complete)).assertDoesNotExist()
        composeRule.onNodeWithText(context.getString(R.string.plan_return_to_wish))
            .assertDoesNotExist()
    }

    @Test
    fun editingAPlanPrefillsItsCurrentFields() {
        val plan = aPlan(PlanStatus.IDEA, title = "A weekend away", description = "Somewhere quiet")
        var edited: List<Any?>? = null
        render(
            plans = listOf(plan),
            onEditPlan = { id, title, description, placeId ->
                edited = listOf(id, title, description, placeId)
            },
        )

        composeRule.onNodeWithText("A weekend away").performScrollTo().performClick()
        composeRule.onNodeWithText(context.getString(R.string.plan_edit)).performClick()
        // What is already written is not hidden behind progressive disclosure.
        composeRule.onNode(hasText("Somewhere quiet") and hasSetTextAction()).assertIsEnabled()
        composeRule.onNodeWithText(context.getString(R.string.plan_save_changes))
            .performScrollTo()
            .performClick()

        assertEquals(listOf(plan.id, "A weekend away", "Somewhere quiet", null), edited)
    }

    @Test
    fun schedulingPicksADayAndATimeBeforeItCanBeConfirmed() {
        val plan = aPlan(PlanStatus.IDEA, title = "A weekend away")
        var scheduled: Triple<UUID, String, String>? = null
        render(
            plans = listOf(plan),
            onSchedule = { id, startOn, startAt -> scheduled = Triple(id, startOn, startAt) },
        )

        composeRule.onNodeWithText("A weekend away").performScrollTo().performClick()
        composeRule.onNodeWithText(context.getString(R.string.plan_schedule)).performClick()
        composeRule.onNodeWithText(context.getString(R.string.plan_schedule_confirm))
            .assertIsNotEnabled()

        composeRule.onNodeWithText(context.getString(R.string.plan_schedule_pick_day))
            .performScrollTo()
            .performClick()
        composeRule.onNodeWithText(context.getString(R.string.plan_picker_take)).performClick()
        composeRule.onNodeWithText(context.getString(R.string.plan_schedule_confirm))
            .assertIsNotEnabled()

        composeRule.onNodeWithText(context.getString(R.string.plan_schedule_pick_time))
            .performScrollTo()
            .performClick()
        composeRule.onNodeWithText(context.getString(R.string.plan_picker_take)).performClick()
        composeRule.onNodeWithText(context.getString(R.string.plan_schedule_confirm))
            .performScrollTo()
            .assertIsEnabled()
            .performClick()

        assertEquals(Triple(plan.id, LocalDate.now().toString(), "19:00"), scheduled)
    }

    @Test
    fun scheduledPlanShowsThePersistedLocalDateAndTime() {
        val previousZone = TimeZone.getDefault()
        try {
            TimeZone.setDefault(TimeZone.getTimeZone("Europe/Berlin"))
            val plan = aPlan(PlanStatus.PLANNED).copy(
                plannedStart = OffsetDateTime.parse("2026-12-20T18:30:00+01:00"),
            )
            val locale = context.resources.configuration.locales[0]
            val expected = plan.plannedStart!!
                .atZoneSameInstant(ZoneId.systemDefault())
                .format(
                    DateTimeFormatter.ofLocalizedDateTime(FormatStyle.LONG, FormatStyle.SHORT)
                        .withLocale(locale),
                )

            render(plans = listOf(plan))

            // The nearest scheduled plan leads the screen rather than sitting
            // in the stack as one more row.
            composeRule.onNodeWithText(context.getString(R.string.plan_focus_next)).assertExists()
            composeRule.onNodeWithText(
                context.getString(R.string.plan_scheduled_for, expected),
            ).assertExists()
        } finally {
            TimeZone.setDefault(previousZone)
        }
    }

    @Test
    fun completingOffersTheDayReadyMadeAndRecordsIt() {
        val plan = aPlan(PlanStatus.PLANNED, title = "A weekend away")
        var completed: Pair<UUID, String>? = null
        render(plans = listOf(plan), onComplete = { id, experiencedOn -> completed = id to experiencedOn })

        composeRule.onNodeWithText("A weekend away").performScrollTo().performClick()
        composeRule.onNodeWithText(context.getString(R.string.plan_complete)).performClick()
        composeRule.onNodeWithText(context.getString(R.string.plan_complete_lead)).assertExists()
        composeRule.onNodeWithText(context.getString(R.string.plan_complete_confirm))
            .performScrollTo()
            .assertIsEnabled()
            .performClick()

        assertEquals(plan.id to LocalDate.now().toString(), completed)
    }

    @Test
    fun looseningAScheduledPlanNeedsNoConfirmationAndKeepsThePlan() {
        val plan = aPlan(PlanStatus.PLANNED, title = "A weekend away")
        var unscheduled: UUID? = null
        render(plans = listOf(plan), onUnschedule = { unscheduled = it })

        composeRule.onNodeWithText("A weekend away").performScrollTo().performClick()
        composeRule.onNodeWithText(context.getString(R.string.plan_unschedule)).performClick()

        assertEquals(plan.id, unscheduled)
    }

    // --- Destructive semantics, unchanged --------------------------------

    @Test
    fun sendingAPlanBackToAWishStillNamesWhatIsLostFirst() {
        val plan = aPlan(PlanStatus.IDEA, title = "A weekend away")
        var returned: UUID? = null
        render(plans = listOf(plan), onReturnToWish = { returned = it })

        composeRule.onNodeWithText("A weekend away").performScrollTo().performClick()
        composeRule.onNodeWithText(context.getString(R.string.plan_return_to_wish)).performClick()

        assertEquals(null, returned)
        composeRule.onNodeWithText(context.getString(R.string.plan_return_body)).assertExists()
        composeRule.onAllNodesWithText(context.getString(R.string.plan_return_to_wish))
            .onFirst()
            .performClick()

        assertEquals(plan.id, returned)
    }

    @Test
    fun deletingAPlanStillNamesTheConsequenceFirst() {
        val plan = aPlan(PlanStatus.IDEA, title = "A weekend away")
        var deleted: UUID? = null
        render(plans = listOf(plan), onDeletePlan = { deleted = it })

        composeRule.onNodeWithText("A weekend away").performScrollTo().performClick()
        composeRule.onNodeWithText(context.getString(R.string.plan_delete)).performClick()

        assertEquals(null, deleted)
        composeRule.onNodeWithText(context.getString(R.string.plan_delete_body)).assertExists()
        composeRule.onAllNodesWithText(context.getString(R.string.plan_delete))
            .onFirst()
            .performClick()

        assertEquals(plan.id, deleted)
    }

    @Test
    fun aWishNobodyMayChangeOffersNothingToChange() {
        render(
            wishes = listOf(
                aWish("A weekend by the sea").copy(
                    capabilities = ResourceCapabilities(
                        canComment = false,
                        canDelete = false,
                        canEdit = false,
                    ),
                ),
            ),
        )

        composeRule.onNodeWithText("A weekend by the sea").performScrollTo().performClick()

        composeRule.onNodeWithText(context.getString(R.string.plan_wish_make_plan))
            .assertDoesNotExist()
        composeRule.onNodeWithText(context.getString(R.string.plan_wish_edit)).assertDoesNotExist()
        composeRule.onNodeWithText(context.getString(R.string.plan_wish_remove)).assertDoesNotExist()
    }

    private fun render(
        wishes: List<WishDetail> = emptyList(),
        plans: List<PlanDetail> = emptyList(),
        onAddWish: (String) -> Unit = {},
        onEditWish: (UUID, String) -> Unit = { _, _ -> },
        onPlanWish: (UUID, String, String, UUID?) -> Unit = { _, _, _, _ -> },
        onRemoveWish: (UUID) -> Unit = {},
        onCreatePlan: (String, String, UUID?) -> Unit = { _, _, _ -> },
        onEditPlan: (UUID, String, String, UUID?) -> Unit = { _, _, _, _ -> },
        onSchedule: (UUID, String, String) -> Unit = { _, _, _ -> },
        onUnschedule: (UUID) -> Unit = {},
        onComplete: (UUID, String) -> Unit = { _, _ -> },
        onReturnToWish: (UUID) -> Unit = {},
        onDeletePlan: (UUID) -> Unit = {},
        onOpenPlaces: () -> Unit = {},
    ) {
        composeRule.setContent {
            SideBySideTheme {
                PlanScreen(
                    wishes = wishes,
                    plans = plans,
                    places = listOf(place),
                    busy = false,
                    problem = null,
                    onAddWish = onAddWish,
                    onEditWish = onEditWish,
                    onPlanWish = onPlanWish,
                    onRemoveWish = onRemoveWish,
                    onCreatePlan = onCreatePlan,
                    onEditPlan = onEditPlan,
                    onSchedule = onSchedule,
                    onUnschedule = onUnschedule,
                    onComplete = onComplete,
                    onReturnToWish = onReturnToWish,
                    onDeletePlan = onDeletePlan,
                    onOpenPlaces = onOpenPlaces,
                    onOpenCollections = {},
                    onOpenChapters = {},
                )
            }
        }
    }

    private fun aWish(title: String) = WishDetail(
        capabilities = CAPABILITIES,
        createdAt = OffsetDateTime.now(),
        createdBy = UUID.randomUUID(),
        creator = AUTHOR,
        id = UUID.randomUUID(),
        spaceId = SPACE,
        status = WishStatus.OPEN,
        title = title,
        updatedAt = OffsetDateTime.now(),
        version = 1,
    )

    private fun aPlan(status: PlanStatus, title: String = "A plan", description: String? = null) = PlanDetail(
        capabilities = CAPABILITIES,
        createdAt = OffsetDateTime.now(),
        createdBy = UUID.randomUUID(),
        creator = AUTHOR,
        description = description,
        experiencedOn = null,
        id = UUID.randomUUID(),
        placeId = null,
        plannedEnd = null,
        plannedStart = null,
        sourceWishId = null,
        spaceId = SPACE,
        status = status,
        title = title,
        updatedAt = OffsetDateTime.now(),
        version = 1,
    )

    private companion object {
        val SPACE: UUID = UUID.randomUUID()
        val AUTHOR = AuthorSummary(displayName = "Lea", id = UUID.randomUUID())
        val CAPABILITIES = ResourceCapabilities(canComment = true, canDelete = true, canEdit = true)

        /** Every management action that used to sit permanently on a card. */
        val LIFECYCLE_LABELS = listOf(
            R.string.plan_wish_edit,
            R.string.plan_wish_make_plan,
            R.string.plan_wish_remove,
            R.string.plan_edit,
            R.string.plan_schedule,
            R.string.plan_complete,
            R.string.plan_unschedule,
            R.string.plan_return_to_wish,
            R.string.plan_delete,
        )
    }
}
