package de.sidebyside.next.reference

import androidx.compose.material3.MaterialTheme
import androidx.compose.runtime.CompositionLocalProvider
import androidx.compose.ui.platform.LocalDensity
import androidx.compose.ui.test.assertHasClickAction
import androidx.compose.ui.test.assertIsDisplayed
import androidx.compose.ui.test.hasClickAction
import androidx.compose.ui.test.hasScrollToIndexAction
import androidx.compose.ui.test.hasText
import androidx.compose.ui.test.junit4.createComposeRule
import androidx.compose.ui.test.onNode
import androidx.compose.ui.test.onNodeWithText
import androidx.compose.ui.test.performScrollToIndex
import androidx.compose.ui.unit.Density
import org.junit.Rule
import org.junit.Test
import org.junit.runner.RunWith
import org.robolectric.RobolectricTestRunner
import org.robolectric.annotation.Config

@RunWith(RobolectricTestRunner::class)
@Config(sdk = [35])
class ReferenceFlowScreenSemanticsTest {
    @get:Rule
    val composeRule = createComposeRule()

    @Test
    fun loggedInControlsRemainSemanticAtLargeFontScale() {
        composeRule.setContent {
            CompositionLocalProvider(LocalDensity provides Density(density = 1f, fontScale = 2f)) {
                MaterialTheme {
                    ReferenceFlowScreen(
                        state = ReferenceUiState(
                            configured = true,
                            loggedIn = true,
                            selectedImageName = null,
                            storyItems = emptyList(),
                        ),
                        onLogin = { _, _ -> },
                        onLogout = {},
                        onPickImage = {},
                        onCreateMemory = { _, _, _ -> },
                        onRefreshStory = {},
                    )
                }
            }
        }

        val storyList = composeRule.onNode(hasScrollToIndexAction())
        storyList.performScrollToIndex(2)
        composeRule.onNodeWithText("Erinnerung festhalten").assertIsDisplayed()
        composeRule.onNode(hasText("Bild auswählen") and hasClickAction())
            .assertIsDisplayed()
            .assertHasClickAction()
        composeRule.onNode(hasText("Erinnerung mit Bild speichern") and hasClickAction())
            .assertIsDisplayed()
            .assertHasClickAction()

        storyList.performScrollToIndex(3)
        composeRule.onNodeWithText("Gemeinsame Story").assertIsDisplayed()
        storyList.performScrollToIndex(4)
        composeRule.onNodeWithText("Noch keine Einträge in eurer Story.").assertIsDisplayed()
    }

    @Test
    fun loginFormHasNamedFieldsAndAction() {
        composeRule.setContent {
            MaterialTheme {
                ReferenceFlowScreen(
                    state = ReferenceUiState(configured = true),
                    onLogin = { _, _ -> },
                    onLogout = {},
                    onPickImage = {},
                    onCreateMemory = { _, _, _ -> },
                    onRefreshStory = {},
                )
            }
        }

        composeRule.onNode(hasScrollToIndexAction()).performScrollToIndex(1)
        composeRule.onNodeWithText("E-Mail").assertIsDisplayed()
        composeRule.onNodeWithText("Passwort").assertIsDisplayed()
        composeRule.onNode(hasText("Anmelden") and hasClickAction()).assertHasClickAction()
    }
}
