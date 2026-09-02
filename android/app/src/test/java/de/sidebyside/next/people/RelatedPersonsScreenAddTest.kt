package de.sidebyside.next.people

import android.content.Context
import androidx.compose.ui.test.junit4.createComposeRule
import androidx.compose.ui.test.onNodeWithText
import androidx.compose.ui.test.performClick
import androidx.compose.ui.test.performScrollTo
import androidx.compose.ui.test.performTextInput
import androidx.test.core.app.ApplicationProvider
import de.sidebyside.next.design.SideBySideTheme
import de.sidebyside.next.reference.R
import java.time.LocalDate
import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertTrue
import org.junit.Rule
import org.junit.Test
import org.junit.runner.RunWith
import org.robolectric.RobolectricTestRunner
import org.robolectric.annotation.Config
import sidebyside.api.models.ContentVisibility
import sidebyside.api.models.PersonRelationship

/**
 * The add-person form.
 *
 * Found on the device: leaving the birthday blank still sent
 * `birthdayYearKnown = true` by default, which the server rejects outright
 * (a known year needs a birthday). The form must never claim a known year
 * when no birthday was given.
 */
@RunWith(RobolectricTestRunner::class)
@Config(sdk = [35])
class RelatedPersonsScreenAddTest {
    @get:Rule
    val composeRule = createComposeRule()

    private val context: Context get() = ApplicationProvider.getApplicationContext()

    @Test
    fun leavingTheBirthdayBlankNeverClaimsAKnownYear() {
        var addedBirthday: LocalDate? = null
        var addedYearKnown: Boolean? = null
        composeRule.setContent {
            SideBySideTheme {
                RelatedPersonsScreen(
                    people = emptyList(),
                    busy = false,
                    problem = null,
                    onBack = {},
                    onAdd = { _, _, birthday, yearKnown, _ ->
                        addedBirthday = birthday
                        addedYearKnown = yearKnown
                    },
                    onEdit = { _, _, _, _, _, _ -> },
                    onOpenDates = {},
                    onDelete = { _, _ -> },
                )
            }
        }

        composeRule.onNodeWithText(context.getString(R.string.related_person_name_hint))
            .performTextInput("Mira")
        composeRule
            .onNodeWithText(context.getString(R.string.related_person_add))
            .performScrollTo()
            .performClick()

        assertEquals(null, addedBirthday)
        assertEquals(false, addedYearKnown)
    }

    @Test
    fun aTypedBirthdayCanCarryAKnownYear() {
        var addedBirthday: LocalDate? = null
        var addedYearKnown: Boolean? = null
        composeRule.setContent {
            SideBySideTheme {
                RelatedPersonsScreen(
                    people = emptyList(),
                    busy = false,
                    problem = null,
                    onBack = {},
                    onAdd = { _, _, birthday, yearKnown, _ ->
                        addedBirthday = birthday
                        addedYearKnown = yearKnown
                    },
                    onEdit = { _, _, _, _, _, _ -> },
                    onOpenDates = {},
                    onDelete = { _, _ -> },
                )
            }
        }

        composeRule.onNodeWithText(context.getString(R.string.related_person_name_hint))
            .performTextInput("Mira")
        composeRule.onNodeWithText(context.getString(R.string.related_person_birthday_hint))
            .performTextInput("1990-05-01")
        composeRule
            .onNodeWithText(context.getString(R.string.related_person_add))
            .performScrollTo()
            .performClick()

        assertEquals(LocalDate.of(1990, 5, 1), addedBirthday)
        assertTrue(addedYearKnown == true)
    }

    @Test
    fun checkingYearUnknownWithATypedBirthdayKeepsTheDateButDropsTheYear() {
        var addedBirthday: LocalDate? = null
        var addedYearKnown: Boolean? = null
        composeRule.setContent {
            SideBySideTheme {
                RelatedPersonsScreen(
                    people = emptyList(),
                    busy = false,
                    problem = null,
                    onBack = {},
                    onAdd = { _, _, birthday, yearKnown, _ ->
                        addedBirthday = birthday
                        addedYearKnown = yearKnown
                    },
                    onEdit = { _, _, _, _, _, _ -> },
                    onOpenDates = {},
                    onDelete = { _, _ -> },
                )
            }
        }

        composeRule.onNodeWithText(context.getString(R.string.related_person_name_hint))
            .performTextInput("Mira")
        composeRule.onNodeWithText(context.getString(R.string.related_person_birthday_hint))
            .performTextInput("1990-05-01")
        composeRule.onNodeWithText(context.getString(R.string.related_person_birthday_year_unknown))
            .performScrollTo()
            .performClick()
        composeRule
            .onNodeWithText(context.getString(R.string.related_person_add))
            .performScrollTo()
            .performClick()

        assertEquals(LocalDate.of(1990, 5, 1), addedBirthday)
        assertFalse(addedYearKnown == true)
    }
}
