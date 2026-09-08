package de.sidebyside.next.place

import android.content.Context
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.setValue
import androidx.compose.ui.test.assertCountEquals
import androidx.compose.ui.test.assertIsEnabled
import androidx.compose.ui.test.assertIsNotEnabled
import androidx.compose.ui.test.hasAnyAncestor
import androidx.compose.ui.test.hasText
import androidx.compose.ui.test.isDialog
import androidx.compose.ui.test.junit4.createComposeRule
import androidx.compose.ui.test.onAllNodesWithText
import androidx.compose.ui.test.onNodeWithText
import androidx.compose.ui.test.performClick
import androidx.compose.ui.test.performScrollTo
import androidx.compose.ui.test.performTextInput
import androidx.test.core.app.ApplicationProvider
import de.sidebyside.next.design.SideBySideTheme
import de.sidebyside.next.reference.R
import de.sidebyside.next.shell.UiProblem
import de.sidebyside.next.shell.UiStateKind
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
import sidebyside.api.models.ResourceCapabilities

private val API_PROBLEM = UiProblem(
    kind = UiStateKind.Error,
    titleRes = R.string.state_validation_title,
    bodyRes = R.string.state_validation_body,
    retryable = false,
)

/**
 * #684: local coordinate validation and the create/edit success-vs-error
 * lifecycle. A validation failure or a server error must never look like a
 * successful submit — the draft must stay on screen with visible feedback,
 * and the form clears / dialog closes only once persistence is confirmed.
 */
@RunWith(RobolectricTestRunner::class)
@Config(sdk = [35], qualifiers = "w320dp-h1200dp")
class PlacesScreenValidationLifecycleTest {
    @get:Rule
    val composeRule = createComposeRule()

    private val context: Context get() = ApplicationProvider.getApplicationContext()

    @Test
    fun nonNumericCoordinatesDisableSubmitAndShowFeedback() {
        composeRule.setContent {
            SideBySideTheme {
                PlacesScreen(
                    places = emptyList(),
                    busy = false,
                    problem = null,
                    onBack = {},
                    onAdd = { _, _, _, _, _ -> },
                    onEdit = { _, _, _, _, _, _ -> },
                    onDelete = {},
                    onOpenRelations = {},
                )
            }
        }

        composeRule.onNodeWithText(context.getString(R.string.place_name_hint)).performTextInput("Am See")
        composeRule.onNodeWithText(context.getString(R.string.place_latitude_hint))
            .performScrollTo().performTextInput("abc")
        composeRule.onNodeWithText(context.getString(R.string.place_longitude_hint))
            .performScrollTo().performTextInput("def")

        composeRule.onNodeWithText(context.getString(R.string.place_add)).performScrollTo().assertIsNotEnabled()
        composeRule.onNodeWithText(context.getString(R.string.place_coordinate_not_numeric)).assertExists()
    }

    @Test
    fun outOfRangeCoordinatesDisableSubmitAndShowFeedback() {
        composeRule.setContent {
            SideBySideTheme {
                PlacesScreen(
                    places = emptyList(),
                    busy = false,
                    problem = null,
                    onBack = {},
                    onAdd = { _, _, _, _, _ -> },
                    onEdit = { _, _, _, _, _, _ -> },
                    onDelete = {},
                    onOpenRelations = {},
                )
            }
        }

        composeRule.onNodeWithText(context.getString(R.string.place_name_hint)).performTextInput("Am See")
        composeRule.onNodeWithText(context.getString(R.string.place_latitude_hint))
            .performScrollTo().performTextInput("999")
        composeRule.onNodeWithText(context.getString(R.string.place_longitude_hint))
            .performScrollTo().performTextInput("999")

        composeRule.onNodeWithText(context.getString(R.string.place_add)).performScrollTo().assertIsNotEnabled()
        composeRule.onNodeWithText(context.getString(R.string.place_coordinate_out_of_range)).assertExists()
    }

    @Test
    fun createApiErrorPreservesTheDraft() {
        var busy by mutableStateOf(false)
        var problem: UiProblem? by mutableStateOf(null)
        var addCalls = 0

        composeRule.setContent {
            SideBySideTheme {
                PlacesScreen(
                    places = emptyList(),
                    busy = busy,
                    problem = problem,
                    onBack = {},
                    onAdd = { _, _, _, _, _ -> addCalls++ },
                    onEdit = { _, _, _, _, _, _ -> },
                    onDelete = {},
                    onOpenRelations = {},
                )
            }
        }

        composeRule.onNodeWithText(context.getString(R.string.place_name_hint)).performTextInput("Am See")
        composeRule.onNodeWithText(context.getString(R.string.place_add)).performScrollTo()
            .assertIsEnabled().performClick()
        assertEquals(1, addCalls)

        composeRule.runOnIdle { busy = true }
        composeRule.runOnIdle {
            busy = false
            problem = API_PROBLEM
        }

        composeRule.onNodeWithText("Am See").assertExists()
    }

    @Test
    fun createSuccessClearsTheForm() {
        var busy by mutableStateOf(false)
        var problem: UiProblem? by mutableStateOf(null)
        var addCalls = 0

        composeRule.setContent {
            SideBySideTheme {
                PlacesScreen(
                    places = emptyList(),
                    busy = busy,
                    problem = problem,
                    onBack = {},
                    onAdd = { _, _, _, _, _ -> addCalls++ },
                    onEdit = { _, _, _, _, _, _ -> },
                    onDelete = {},
                    onOpenRelations = {},
                )
            }
        }

        composeRule.onNodeWithText(context.getString(R.string.place_name_hint)).performTextInput("Am See")
        composeRule.onNodeWithText(context.getString(R.string.place_add)).performScrollTo()
            .assertIsEnabled().performClick()
        assertEquals(1, addCalls)

        composeRule.runOnIdle { busy = true }
        composeRule.runOnIdle { busy = false }

        composeRule.onAllNodesWithText("Am See").assertCountEquals(0)
    }

    @Test
    fun editValidationErrorLeavesEditorOpen() {
        val place = editablePlace()
        composeRule.setContent {
            SideBySideTheme {
                PlacesScreen(
                    places = listOf(place),
                    busy = false,
                    problem = null,
                    onBack = {},
                    onAdd = { _, _, _, _, _ -> },
                    onEdit = { _, _, _, _, _, _ -> },
                    onDelete = {},
                    onOpenRelations = {},
                )
            }
        }

        composeRule.onNodeWithText(context.getString(R.string.place_edit)).performScrollTo().performClick()
        composeRule.onNodeWithText(context.getString(R.string.place_edit_title)).assertExists()

        // The (empty, unrelated) create form is still composed behind the
        // dialog and shares the same field labels, so scope to the dialog.
        composeRule.onNode(hasText(context.getString(R.string.place_latitude_hint)) and hasAnyAncestor(isDialog()))
            .performScrollTo().performTextInput("abc")
        composeRule.onNode(hasText(context.getString(R.string.place_longitude_hint)) and hasAnyAncestor(isDialog()))
            .performScrollTo().performTextInput("def")

        composeRule.onNodeWithText(context.getString(R.string.place_save_changes))
            .performScrollTo().assertIsNotEnabled()
        // Dialog stays open, no way to have closed it.
        composeRule.onNodeWithText(context.getString(R.string.place_edit_title)).assertExists()
    }

    @Test
    fun editApiErrorLeavesEditorOpenWithInput() {
        val place = editablePlace()
        var busy by mutableStateOf(false)
        var problem: UiProblem? by mutableStateOf(null)
        var editCalls = 0

        composeRule.setContent {
            SideBySideTheme {
                PlacesScreen(
                    places = listOf(place),
                    busy = busy,
                    problem = problem,
                    onBack = {},
                    onAdd = { _, _, _, _, _ -> },
                    onEdit = { _, _, _, _, _, _ -> editCalls++ },
                    onDelete = {},
                    onOpenRelations = {},
                )
            }
        }

        composeRule.onNodeWithText(context.getString(R.string.place_edit)).performScrollTo().performClick()
        composeRule.onNodeWithText(context.getString(R.string.place_save_changes))
            .performScrollTo().assertIsEnabled().performClick()
        assertEquals(1, editCalls)

        composeRule.runOnIdle { busy = true }
        composeRule.runOnIdle {
            busy = false
            problem = API_PROBLEM
        }

        composeRule.onNodeWithText(context.getString(R.string.place_edit_title)).assertExists()
    }

    @Test
    fun editSuccessClosesTheDialog() {
        val place = editablePlace()
        var busy by mutableStateOf(false)
        var problem: UiProblem? by mutableStateOf(null)
        var editCalls = 0

        composeRule.setContent {
            SideBySideTheme {
                PlacesScreen(
                    places = listOf(place),
                    busy = busy,
                    problem = problem,
                    onBack = {},
                    onAdd = { _, _, _, _, _ -> },
                    onEdit = { _, _, _, _, _, _ -> editCalls++ },
                    onDelete = {},
                    onOpenRelations = {},
                )
            }
        }

        composeRule.onNodeWithText(context.getString(R.string.place_edit)).performScrollTo().performClick()
        composeRule.onNodeWithText(context.getString(R.string.place_save_changes))
            .performScrollTo().assertIsEnabled().performClick()
        assertEquals(1, editCalls)

        composeRule.runOnIdle { busy = true }
        composeRule.runOnIdle { busy = false }

        composeRule.onAllNodesWithText(context.getString(R.string.place_edit_title)).assertCountEquals(0)
    }

    private fun editablePlace() = PlaceDetail(
        address = null,
        capabilities = ResourceCapabilities(canComment = true, canDelete = true, canEdit = true),
        createdAt = OffsetDateTime.now(),
        createdBy = UUID.randomUUID(),
        creator = AuthorSummary(displayName = "Lea", id = UUID.randomUUID()),
        description = null,
        id = UUID.randomUUID(),
        latitude = null,
        longitude = null,
        name = "Am See",
        spaceId = UUID.randomUUID(),
        updatedAt = OffsetDateTime.now(),
        version = 1,
    )
}
