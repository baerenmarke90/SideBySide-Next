package de.sidebyside.next.plan

import android.content.Context
import androidx.compose.ui.test.assertIsEnabled
import androidx.compose.ui.test.assertIsNotEnabled
import androidx.compose.ui.test.hasSetTextAction
import androidx.compose.ui.test.hasText
import androidx.compose.ui.test.junit4.createComposeRule
import androidx.compose.ui.test.onNodeWithText
import androidx.compose.ui.test.performClick
import androidx.compose.ui.test.performScrollTo
import androidx.compose.ui.test.performTextInput
import androidx.compose.ui.test.performTextReplacement
import androidx.test.core.app.ApplicationProvider
import de.sidebyside.next.design.SideBySideTheme
import de.sidebyside.next.reference.R
import java.time.OffsetDateTime
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
 * The gaps #605 closes: Wish editing, Wish-to-Plan conversion with a real
 * title/description/place, direct Plan creation, Plan editing, and a real
 * date instead of always "now"/"today" for schedule/complete.
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

    @Test
    fun creatingAPlanDirectlySubmitsTitleDescriptionAndPlace() {
        var submitted: Triple<String, String, UUID?>? = null
        render(onCreatePlan = { title, description, placeId -> submitted = Triple(title, description, placeId) })

        composeRule.onNodeWithText(context.getString(R.string.plan_title_hint))
            .performScrollTo()
            .performTextInput("A weekend away")
        composeRule.onNodeWithText(context.getString(R.string.plan_description_hint))
            .performScrollTo()
            .performTextInput("Somewhere quiet")
        composeRule.onNodeWithText(context.getString(R.string.place_picker_none))
            .performScrollTo()
            .performClick()
        composeRule.onNodeWithText("The coast").performClick()
        composeRule.onNodeWithText(context.getString(R.string.plan_add))
            .performScrollTo()
            .performClick()

        assertEquals(Triple("A weekend away", "Somewhere quiet", place.id), submitted)
    }

    @Test
    fun editingAWishPrefillsTheCurrentTitle() {
        var edited: Pair<UUID, String>? = null
        render(
            wishes = listOf(aWish("A weekend by the sea")),
            onEditWish = { id, title -> edited = id to title },
        )

        composeRule.onNodeWithText(context.getString(R.string.plan_wish_edit))
            .performScrollTo()
            .performClick()
        // Matched by the editable field specifically — the card's own,
        // non-editable title Text behind the dialog carries the same text.
        // A single replacement, not clear-then-input: clearing would leave
        // this same selector unable to re-match its own now-empty field.
        composeRule.onNode(hasText("A weekend by the sea") and hasSetTextAction())
            .performTextReplacement("A weekend inland")
        composeRule.onNodeWithText(context.getString(R.string.plan_wish_save_changes)).performClick()

        assertEquals("A weekend inland", edited?.second)
    }

    @Test
    fun planningAWishDefaultsTheTitleToTheWishAndSubmitsAPlace() {
        val wish = aWish("A weekend by the sea")
        var planned: List<Any?>? = null
        render(
            wishes = listOf(wish),
            onPlanWish = { id, title, _, placeId -> planned = listOf(id, title, placeId) },
        )

        composeRule.onNodeWithText(context.getString(R.string.plan_wish_make_plan))
            .performScrollTo()
            .performClick()
        // Pre-filled from the wish: the dialog's own editable title field
        // carries it, distinct from the card's non-editable title behind it.
        composeRule.onNode(hasText("A weekend by the sea") and hasSetTextAction()).assertIsEnabled()
        composeRule.onNodeWithText(context.getString(R.string.plan_wish_make_plan_confirm))
            .performClick()

        assertEquals(listOf(wish.id, "A weekend by the sea", null), planned)
    }

    @Test
    fun editingAPlanPrefillsItsCurrentFields() {
        val plan = aPlan(PlanStatus.IDEA, title = "A weekend away", description = "Somewhere quiet")
        var edited: List<Any?>? = null
        render(
            plans = listOf(plan),
            onEditPlan = { id, title, description, placeId -> edited = listOf(id, title, description, placeId) },
        )

        composeRule.onNodeWithText(context.getString(R.string.plan_edit))
            .performScrollTo()
            .performClick()
        composeRule.onNodeWithText(context.getString(R.string.plan_save_changes)).performClick()

        assertEquals(listOf(plan.id, "A weekend away", "Somewhere quiet", null), edited)
    }

    @Test
    fun schedulingRequiresADateBeforeSubmitEnablesAndSendsIt() {
        val plan = aPlan(PlanStatus.IDEA)
        var scheduled: Pair<UUID, String>? = null
        render(plans = listOf(plan), onSchedule = { id, startOn -> scheduled = id to startOn })

        composeRule.onNodeWithText(context.getString(R.string.plan_schedule))
            .performScrollTo()
            .performClick()
        composeRule.onNodeWithText(context.getString(R.string.plan_schedule_confirm))
            .assertIsNotEnabled()

        composeRule.onNodeWithText(context.getString(R.string.plan_schedule_date_hint))
            .performTextInput("2026-09-20")
        composeRule.onNodeWithText(context.getString(R.string.plan_schedule_confirm))
            .assertIsEnabled()
            .performClick()

        assertEquals(plan.id to "2026-09-20", scheduled)
    }

    @Test
    fun completingRequiresADateBeforeSubmitEnablesAndSendsIt() {
        val plan = aPlan(PlanStatus.PLANNED)
        var completed: Pair<UUID, String>? = null
        render(plans = listOf(plan), onComplete = { id, experiencedOn -> completed = id to experiencedOn })

        composeRule.onNodeWithText(context.getString(R.string.plan_complete))
            .performScrollTo()
            .performClick()
        composeRule.onNodeWithText(context.getString(R.string.plan_complete_confirm))
            .assertIsNotEnabled()

        composeRule.onNodeWithText(context.getString(R.string.plan_complete_date_hint))
            .performTextInput("2026-08-30")
        composeRule.onNodeWithText(context.getString(R.string.plan_complete_confirm))
            .assertIsEnabled()
            .performClick()

        assertEquals(plan.id to "2026-08-30", completed)
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
        onSchedule: (UUID, String) -> Unit = { _, _ -> },
        onUnschedule: (UUID) -> Unit = {},
        onComplete: (UUID, String) -> Unit = { _, _ -> },
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
                    onReturnToWish = {},
                    onDeletePlan = {},
                    onOpenPlaces = {},
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
    }
}
