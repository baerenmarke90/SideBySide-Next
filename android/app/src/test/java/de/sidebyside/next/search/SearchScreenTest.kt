package de.sidebyside.next.search

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
import sidebyside.api.models.SearchKind

/**
 * The type filter and load-more affordance (#608): #357 shipped Search with
 * neither, deferring both — this pins that a chosen kind reaches [onSearch]
 * and that [onLoadMore] is only ever offered when the caller says there is
 * a next page.
 */
@RunWith(RobolectricTestRunner::class)
@Config(sdk = [35], qualifiers = "w320dp-h1200dp")
class SearchScreenTest {
    @get:Rule
    val composeRule = createComposeRule()

    private val context: Context get() = ApplicationProvider.getApplicationContext()

    @Test
    fun choosingAKindSendsItAlongTheQueryOnSubmit() {
        var submitted: Pair<String, SearchKind?>? = null
        render(onSearch = { query, kind -> submitted = query to kind })

        composeRule.onNodeWithText(context.getString(R.string.search_query_hint))
            .performScrollTo()
            .performTextInput("sea")
        composeRule.onNodeWithText(context.getString(R.string.search_kind_all))
            .performScrollTo()
            .performClick()
        composeRule.onNodeWithText(context.getString(R.string.search_result_kind_gift_idea))
            .performClick()
        composeRule.onNodeWithText(context.getString(R.string.search_submit))
            .performScrollTo()
            .performClick()

        assertEquals("sea" to SearchKind.GIFT_IDEA, submitted)
    }

    @Test
    fun theAllOptionSearchesWithoutAKind() {
        var submitted: Pair<String, SearchKind?>? = null
        render(onSearch = { query, kind -> submitted = query to kind })

        composeRule.onNodeWithText(context.getString(R.string.search_query_hint))
            .performScrollTo()
            .performTextInput("sea")
        composeRule.onNodeWithText(context.getString(R.string.search_submit))
            .performScrollTo()
            .performClick()

        assertEquals("sea" to null, submitted)
    }

    @Test
    fun loadMoreIsOfferedOnlyWhenTheCallerProvidesIt() {
        render(onLoadMore = null)

        composeRule.onNodeWithText(context.getString(R.string.load_more)).assertDoesNotExist()
    }

    @Test
    fun loadMoreInvokesTheCallbackAndReflectsBusyState() {
        var loadMoreCalls = 0
        render(onLoadMore = { loadMoreCalls++ })

        composeRule.onNodeWithText(context.getString(R.string.load_more))
            .performScrollTo()
            .assertIsEnabled()
            .performClick()

        assertEquals(1, loadMoreCalls)
    }

    @Test
    fun loadMoreIsDisabledWhileLoadingMore() {
        render(onLoadMore = {}, loadingMore = true)

        composeRule.onNodeWithText(context.getString(R.string.load_more_busy))
            .performScrollTo()
            .assertIsNotEnabled()
    }

    private fun render(
        onSearch: (String, SearchKind?) -> Unit = { _, _ -> },
        onLoadMore: (() -> Unit)? = null,
        loadingMore: Boolean = false,
    ) {
        composeRule.setContent {
            SideBySideTheme {
                SearchScreen(
                    results = emptyList(),
                    busy = false,
                    problem = null,
                    onBack = {},
                    onSearch = onSearch,
                    onLoadMore = onLoadMore,
                    loadingMore = loadingMore,
                )
            }
        }
    }
}
