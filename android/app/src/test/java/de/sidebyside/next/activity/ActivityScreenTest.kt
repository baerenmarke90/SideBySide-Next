package de.sidebyside.next.activity

import android.content.Context
import androidx.compose.ui.test.assertIsNotEnabled
import androidx.compose.ui.test.junit4.createComposeRule
import androidx.compose.ui.test.onNodeWithText
import androidx.compose.ui.test.performClick
import androidx.compose.ui.test.performScrollTo
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
 * The load-more affordance (#608): #357 shipped the Activity feed capped at
 * one server page with no way to reach older entries.
 */
@RunWith(RobolectricTestRunner::class)
@Config(sdk = [35], qualifiers = "w320dp-h1200dp")
class ActivityScreenTest {
    @get:Rule
    val composeRule = createComposeRule()

    private val context: Context get() = ApplicationProvider.getApplicationContext()

    @Test
    fun loadMoreIsAbsentWithoutACallback() {
        render(onLoadMore = null)

        composeRule.onNodeWithText(context.getString(R.string.load_more)).assertDoesNotExist()
    }

    @Test
    fun loadMoreInvokesTheCallback() {
        var calls = 0
        render(onLoadMore = { calls++ })

        composeRule.onNodeWithText(context.getString(R.string.load_more))
            .performScrollTo()
            .performClick()

        assertEquals(1, calls)
    }

    @Test
    fun loadMoreIsDisabledWhileLoadingMore() {
        render(onLoadMore = {}, loadingMore = true)

        composeRule.onNodeWithText(context.getString(R.string.load_more_busy))
            .performScrollTo()
            .assertIsNotEnabled()
    }

    private fun render(onLoadMore: (() -> Unit)?, loadingMore: Boolean = false) {
        composeRule.setContent {
            SideBySideTheme {
                ActivityScreen(
                    entries = emptyList(),
                    busy = false,
                    problem = null,
                    onBack = {},
                    onOpen = {},
                    onLoadMore = onLoadMore,
                    loadingMore = loadingMore,
                )
            }
        }
    }
}
