package de.sidebyside.next.collection

import android.content.Context
import androidx.compose.ui.test.hasSetTextAction
import androidx.compose.ui.test.hasText
import androidx.compose.ui.test.junit4.createComposeRule
import androidx.compose.ui.test.onNodeWithText
import androidx.compose.ui.test.performClick
import androidx.compose.ui.test.performScrollTo
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
import sidebyside.api.models.CollectionDetail
import sidebyside.api.models.CollectionItemDetail
import sidebyside.api.models.ResourceCapabilities

/** Item renaming in place (#607): #356 shipped without it. */
@RunWith(RobolectricTestRunner::class)
@Config(sdk = [35], qualifiers = "w320dp-h1200dp")
class CollectionDetailScreenTest {
    @get:Rule
    val composeRule = createComposeRule()

    private val context: Context get() = ApplicationProvider.getApplicationContext()
    private val itemId: UUID = UUID.randomUUID()

    @Test
    fun editingRenamesTheItemInPlace() {
        var renamed: String? = null
        render(onRenameItem = { _, title -> renamed = title })

        composeRule.onNodeWithText(context.getString(R.string.collection_item_edit))
            .performScrollTo()
            .performClick()
        composeRule.onNode(hasText("Passport") and hasSetTextAction())
            .performTextReplacement("Passport (renew soon)")
        composeRule.onNodeWithText(context.getString(R.string.collection_item_save_changes))
            .performClick()

        assertEquals("Passport (renew soon)", renamed)
    }

    @Test
    fun cancellingDiscardsWithoutRenaming() {
        var renameCalls = 0
        render(onRenameItem = { _, _ -> renameCalls++ })

        composeRule.onNodeWithText(context.getString(R.string.collection_item_edit))
            .performScrollTo()
            .performClick()
        composeRule.onNodeWithText(context.getString(R.string.collection_item_cancel))
            .performClick()

        assertEquals(0, renameCalls)
        composeRule.onNodeWithText(context.getString(R.string.collection_item_edit)).performScrollTo()
    }

    private fun render(onRenameItem: (CollectionItemDetail, String) -> Unit) {
        val capabilities = ResourceCapabilities(canComment = false, canDelete = true, canEdit = true)
        val collection = CollectionDetail(
            capabilities = capabilities,
            createdAt = OffsetDateTime.now(),
            icon = null,
            id = UUID.randomUUID(),
            items = listOf(
                CollectionItemDetail(
                    capabilities = capabilities,
                    collectionId = UUID.randomUUID(),
                    completed = false,
                    createdAt = OffsetDateTime.now(),
                    createdBy = UUID.randomUUID(),
                    creator = AuthorSummary(displayName = "Lea", id = UUID.randomUUID()),
                    id = itemId,
                    position = 0,
                    title = "Passport",
                    updatedAt = OffsetDateTime.now(),
                    version = 1,
                ),
            ),
            createdBy = UUID.randomUUID(),
            creator = AuthorSummary(displayName = "Lea", id = UUID.randomUUID()),
            spaceId = UUID.randomUUID(),
            title = "Packing list",
            updatedAt = OffsetDateTime.now(),
            version = 1,
        )

        composeRule.setContent {
            SideBySideTheme {
                CollectionDetailScreen(
                    collection = collection,
                    busy = false,
                    problem = null,
                    onBack = {},
                    onAddItem = {},
                    onRenameItem = onRenameItem,
                    onToggleCompleted = {},
                    onDeleteItem = {},
                    onMoveUp = {},
                    onMoveDown = {},
                )
            }
        }
    }
}
