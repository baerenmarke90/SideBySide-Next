package de.sidebyside.next.profile

import android.content.Context
import androidx.compose.ui.semantics.SemanticsProperties
import androidx.compose.ui.test.SemanticsMatcher
import androidx.compose.ui.test.hasText
import androidx.compose.ui.test.junit4.createComposeRule
import androidx.compose.ui.test.onNodeWithText
import androidx.test.core.app.ApplicationProvider
import de.sidebyside.next.design.SideBySideTheme
import de.sidebyside.next.reference.R
import java.time.OffsetDateTime
import java.util.UUID
import org.junit.Rule
import org.junit.Test
import org.junit.runner.RunWith
import org.robolectric.RobolectricTestRunner
import org.robolectric.annotation.Config
import sidebyside.api.models.PartnerProfileView

private val isHeading = SemanticsMatcher("has heading semantics") {
    it.config.contains(SemanticsProperties.Heading)
}

/**
 * Direction B moves the person's own name into the identity headline instead
 * of a generic "Profil" label, while loading/error states must keep a stable
 * heading rather than showing nothing.
 */
@RunWith(RobolectricTestRunner::class)
@Config(sdk = [35])
class ProfileSettingsContentTest {
    @get:Rule
    val composeRule = createComposeRule()

    private val context: Context get() = ApplicationProvider.getApplicationContext()

    @Test
    fun showsTheOwnDisplayNameAsTheIdentityHeadlineOnceLoaded() {
        render(state = ProfileUiState(self = partner("Lea Fischer")))

        // The display name also appears in the avatar preview and the
        // pre-filled text field; only the heading node is under test here.
        composeRule.onNode(hasText("Lea Fischer") and isHeading).assertExists()
    }

    @Test
    fun fallsBackToTheGenericTitleWhileLoading() {
        render(state = ProfileUiState(loading = true))

        // "Profil" also appears as the small eyebrow above the heading.
        composeRule
            .onNode(hasText(context.getString(R.string.profile_settings_title)) and isHeading)
            .assertExists()
        composeRule
            .onNodeWithText(context.getString(R.string.profile_settings_loading))
            .assertExists()
    }

    private fun partner(displayName: String) = PartnerProfileView(
        accountId = UUID.fromString("22222222-2222-4222-8222-222222222222"),
        createdAt = OffsetDateTime.now(),
        displayName = displayName,
        id = UUID.fromString("11111111-1111-4111-8111-111111111111"),
        preferences = emptyList(),
        profileAttachmentId = null,
        updatedAt = OffsetDateTime.now(),
        version = 1,
    )

    private fun render(state: ProfileUiState) {
        composeRule.setContent {
            SideBySideTheme {
                ProfileSettingsContent(
                    state = state,
                    onRetry = {},
                    onSaveDisplayName = {},
                    onChooseAvatar = {},
                    onRemoveAvatar = {},
                )
            }
        }
    }
}
