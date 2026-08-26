package de.sidebyside.next.reference

import androidx.compose.material3.MaterialTheme
import androidx.compose.runtime.CompositionLocalProvider
import androidx.compose.ui.platform.LocalDensity
import androidx.compose.ui.test.assertHasClickAction
import androidx.compose.ui.test.assertIsDisplayed
import androidx.compose.ui.test.junit4.createComposeRule
import androidx.compose.ui.test.onNodeWithText
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

        composeRule.onNodeWithText("Erinnerung festhalten").assertIsDisplayed()
        composeRule.onNodeWithText("Bild auswählen").assertIsDisplayed().assertHasClickAction()
        composeRule.onNodeWithText("Erinnerung mit Bild speichern").assertIsDisplayed().assertHasClickAction()
        composeRule.onNodeWithText("Gemeinsame Story").assertIsDisplayed()
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

        composeRule.onNodeWithText("E-Mail").assertIsDisplayed()
        composeRule.onNodeWithText("Passwort").assertIsDisplayed()
        composeRule.onNodeWithText("Anmelden").assertHasClickAction()
    }
}
