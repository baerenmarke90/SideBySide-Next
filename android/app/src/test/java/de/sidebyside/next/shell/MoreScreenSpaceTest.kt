package de.sidebyside.next.shell

import android.content.Context
import androidx.compose.ui.test.assertIsSelected
import androidx.compose.ui.test.junit4.createComposeRule
import androidx.compose.ui.test.onNodeWithText
import androidx.compose.ui.test.performClick
import androidx.compose.ui.test.performScrollTo
import androidx.test.core.app.ApplicationProvider
import de.sidebyside.next.design.SideBySideTheme
import de.sidebyside.next.reference.R
import java.util.UUID
import org.junit.Assert.assertEquals
import org.junit.Rule
import org.junit.Test
import org.junit.runner.RunWith
import org.robolectric.RobolectricTestRunner
import org.robolectric.annotation.Config
import sidebyside.api.models.AccountMembershipView

private val FIRST: UUID = UUID.fromString("11111111-1111-4111-8111-111111111111")
private val SECOND: UUID = UUID.fromString("22222222-2222-4222-8222-222222222222")

/**
 * The Space choice is the one place a couple can change which Space they are
 * reading, so what it shows and when it shows at all is worth pinning.
 */
@RunWith(RobolectricTestRunner::class)
@Config(sdk = [35])
class MoreScreenSpaceTest {
    @get:Rule
    val composeRule = createComposeRule()

    private val context: Context get() = ApplicationProvider.getApplicationContext()

    @Test
    fun offersNoChoiceWhereThereIsOnlyOneSpace() {
        // The ordinary couple has exactly one Space and must never be asked to
        // pick it.
        render(spaces = listOf(membership(FIRST)), active = FIRST)

        composeRule
            .onNodeWithText(context.getString(R.string.more_space_title))
            .assertDoesNotExist()
    }

    @Test
    fun marksTheSpaceCurrentlyBeingReadAndSwitchesToTheOther() {
        val chosen = mutableListOf<UUID>()
        render(
            spaces = listOf(membership(FIRST), membership(SECOND)),
            active = FIRST,
            onSelectSpace = { chosen += it },
        )

        composeRule.onNodeWithText(option(1)).assertIsSelected()
        // Mehr scrolls, and the screen has grown since this was written: the
        // click has to reach the row rather than the window it sits below.
        composeRule.onNodeWithText(option(2)).performScrollTo().performClick()

        assertEquals(listOf(SECOND), chosen)
    }

    @Test
    fun namesNoSpaceByItsIdentifier() {
        render(spaces = listOf(membership(FIRST), membership(SECOND)), active = FIRST)

        // A Space ID is a technical value; asking a couple to read one would
        // undo the reason the Space stopped being build configuration.
        composeRule.onNodeWithText(FIRST.toString(), substring = true).assertDoesNotExist()
        composeRule.onNodeWithText(SECOND.toString(), substring = true).assertDoesNotExist()
    }

    private fun option(position: Int): String =
        context.getString(R.string.more_space_option, position)

    private fun membership(spaceId: UUID) =
        AccountMembershipView(role = "PARTNER", spaceId = spaceId, status = "ACTIVE")

    private fun render(
        spaces: List<AccountMembershipView>,
        active: UUID?,
        onSelectSpace: (UUID) -> Unit = {},
    ) {
        composeRule.setContent {
            SideBySideTheme {
                MoreScreen(
                    onSignOut = {},
                    onOpenHeartMoments = {},
                    onOpenInvitations = {},
                    spaces = spaces,
                    activeSpaceId = active,
                    onSelectSpace = onSelectSpace,
                )
            }
        }
    }
}
