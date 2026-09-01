package de.sidebyside.next.place

import android.content.Context
import androidx.compose.ui.test.assertIsEnabled
import androidx.compose.ui.test.assertIsNotEnabled
import androidx.compose.ui.test.junit4.createComposeRule
import androidx.compose.ui.test.onNodeWithText
import androidx.compose.ui.test.performClick
import androidx.compose.ui.test.performScrollTo
import androidx.compose.ui.test.performTextInput
import androidx.test.core.app.ApplicationProvider
import de.sidebyside.next.design.SideBySideTheme
import de.sidebyside.next.reference.R
import org.junit.Assert.assertEquals
import org.junit.Rule
import org.junit.Test
import org.junit.runner.RunWith
import org.robolectric.RobolectricTestRunner
import org.robolectric.annotation.Config

/**
 * The add-place form's coordinate pairing.
 *
 * Found the hard way on an earlier slice: a picker that looks enabled but
 * silently does nothing, or a submit that fires with an invalid pairing,
 * only shows up in a rendered Compose tree — a ViewModel-level test cannot
 * see either. This pins the button's enabled state directly rather than
 * trusting the ViewModel guard alone.
 */
@RunWith(RobolectricTestRunner::class)
@Config(sdk = [35])
class PlacesScreenAddTest {
    @get:Rule
    val composeRule = createComposeRule()

    private val context: Context get() = ApplicationProvider.getApplicationContext()

    @Test
    fun aNameAloneIsEnoughToSubmit() {
        var added: List<String>? = null
        composeRule.setContent {
            SideBySideTheme {
                PlacesScreen(
                    places = emptyList(),
                    busy = false,
                    problem = null,
                    onBack = {},
                    onAdd = { name, description, address, latitude, longitude ->
                        added = listOf(name, description, address, latitude, longitude)
                    },
                    onEdit = { _, _, _, _, _, _ -> },
                    onDelete = {},
                    onOpenRelations = {},
                )
            }
        }

        composeRule.onNodeWithText(context.getString(R.string.place_name_hint))
            .performTextInput("Am See")
        composeRule
            .onNodeWithText(context.getString(R.string.place_add))
            .performScrollTo()
            .assertIsEnabled()
            .performClick()

        assertEquals(listOf("Am See", "", "", "", ""), added)
    }

    @Test
    fun exactlyOneCoordinateSetDisablesSubmit() {
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

        composeRule.onNodeWithText(context.getString(R.string.place_name_hint))
            .performTextInput("Am See")
        composeRule.onNodeWithText(context.getString(R.string.place_latitude_hint))
            .performScrollTo()
            .performTextInput("52.5")

        composeRule
            .onNodeWithText(context.getString(R.string.place_add))
            .performScrollTo()
            .assertIsNotEnabled()
    }

    @Test
    fun bothCoordinatesSetSubmitsThePair() {
        var added: List<String>? = null
        composeRule.setContent {
            SideBySideTheme {
                PlacesScreen(
                    places = emptyList(),
                    busy = false,
                    problem = null,
                    onBack = {},
                    onAdd = { name, description, address, latitude, longitude ->
                        added = listOf(name, description, address, latitude, longitude)
                    },
                    onEdit = { _, _, _, _, _, _ -> },
                    onDelete = {},
                    onOpenRelations = {},
                )
            }
        }

        composeRule.onNodeWithText(context.getString(R.string.place_name_hint))
            .performTextInput("Am See")
        composeRule.onNodeWithText(context.getString(R.string.place_latitude_hint))
            .performScrollTo()
            .performTextInput("52.5")
        composeRule.onNodeWithText(context.getString(R.string.place_longitude_hint))
            .performScrollTo()
            .performTextInput("13.4")

        composeRule
            .onNodeWithText(context.getString(R.string.place_add))
            .performScrollTo()
            .assertIsEnabled()
            .performClick()

        assertEquals(listOf("Am See", "", "", "52.5", "13.4"), added)
    }
}
