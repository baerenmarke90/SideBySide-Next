package de.sidebyside.next.shell

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.heightIn
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.widthIn
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.selection.selectable
import androidx.compose.foundation.selection.selectableGroup
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedButton
import androidx.compose.material3.RadioButton
import androidx.compose.material3.Surface
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.res.stringResource
import androidx.compose.ui.semantics.Role
import androidx.compose.ui.semantics.heading
import androidx.compose.ui.semantics.semantics
import androidx.compose.ui.unit.Dp
import de.sidebyside.next.design.MinimumTouchTarget
import de.sidebyside.next.design.SideBySideTheme
import de.sidebyside.next.reference.R
import java.util.UUID
import sidebyside.api.models.AccountMembershipView

/**
 * The Mehr area.
 *
 * It owns the existing signed-in utility surface. Personal settings can insert
 * their real content through [profileContent] without creating a new top-level
 * destination or pre-empting the later header/navigation slice.
 */
@Composable
fun MoreScreen(
    onSignOut: () -> Unit,
    /**
     * Opens the account's own HeartMoments.
     *
     * Deliberately without a default. An optional navigation entry that a
     * caller forgets to pass disappears from the product without breaking the
     * build, which is how this one was lost once already.
     */
    onOpenHeartMoments: () -> Unit,
    modifier: Modifier = Modifier,
    signOutEnabled: Boolean = true,
    spaces: List<AccountMembershipView> = emptyList(),
    activeSpaceId: UUID? = null,
    onSelectSpace: (UUID) -> Unit = {},
    profileContent: @Composable () -> Unit = {},
) {
    Column(
        modifier = modifier
            .fillMaxWidth()
            .verticalScroll(rememberScrollState())
            .padding(SideBySideTheme.spacing.pageMargin),
        verticalArrangement = Arrangement.spacedBy(SideBySideTheme.spacing.step6),
    ) {
        Column(
            verticalArrangement = Arrangement.spacedBy(SideBySideTheme.spacing.step2),
        ) {
            Text(
                text = stringResource(R.string.more_eyebrow),
                style = MaterialTheme.typography.labelSmall,
                color = SideBySideTheme.colors.brandStrong,
            )
            Text(
                text = stringResource(R.string.more_title),
                style = MaterialTheme.typography.headlineMedium,
                color = SideBySideTheme.colors.textPrimary,
                modifier = Modifier.semantics { heading() },
            )
            Text(
                text = stringResource(R.string.more_intro),
                style = MaterialTheme.typography.bodyLarge,
                color = SideBySideTheme.colors.textSecondary,
                modifier = Modifier.widthIn(max = ReadingMeasure),
            )
        }

        run {
            val open = onOpenHeartMoments
            Surface(
                shape = RoundedCornerShape(SideBySideTheme.radii.card),
                color = SideBySideTheme.colors.surface,
                modifier = Modifier.fillMaxWidth(),
            ) {
                Column(
                    modifier = Modifier.padding(SideBySideTheme.spacing.cardPadding),
                    verticalArrangement = Arrangement.spacedBy(SideBySideTheme.spacing.step3),
                ) {
                    Text(
                        text = stringResource(R.string.heart_moments_title),
                        style = MaterialTheme.typography.titleMedium,
                        color = SideBySideTheme.colors.textPrimary,
                        modifier = Modifier.semantics { heading() },
                    )
                    Text(
                        text = stringResource(R.string.heart_moments_intro),
                        style = MaterialTheme.typography.bodyMedium,
                        color = SideBySideTheme.colors.textSecondary,
                    )
                    OutlinedButton(
                        onClick = open,
                        modifier = Modifier.heightIn(min = MinimumTouchTarget),
                    ) {
                        Text(stringResource(R.string.heart_moments_open))
                    }
                }
            }
        }

        if (spaces.size > 1) {
            SpaceChoice(
                spaces = spaces,
                activeSpaceId = activeSpaceId,
                enabled = signOutEnabled,
                onSelectSpace = onSelectSpace,
            )
        }

        profileContent()

        Surface(
            shape = RoundedCornerShape(SideBySideTheme.radii.card),
            color = SideBySideTheme.colors.surface,
            modifier = Modifier.fillMaxWidth(),
        ) {
            Column(
                modifier = Modifier.padding(SideBySideTheme.spacing.cardPadding),
                verticalArrangement = Arrangement.spacedBy(
                    SideBySideTheme.spacing.step4,
                ),
            ) {
                Text(
                    text = stringResource(R.string.more_session_title),
                    style = MaterialTheme.typography.titleMedium,
                    color = SideBySideTheme.colors.textPrimary,
                    modifier = Modifier.semantics { heading() },
                )
                Text(
                    text = stringResource(R.string.more_session_body),
                    style = MaterialTheme.typography.bodyMedium,
                    color = SideBySideTheme.colors.textSecondary,
                )
                OutlinedButton(
                    onClick = onSignOut,
                    enabled = signOutEnabled,
                    modifier = Modifier.heightIn(min = MinimumTouchTarget),
                ) {
                    Text(stringResource(R.string.more_sign_out))
                }
            }
        }
    }
}

/**
 * Offered only where the account really is active in more than one Space, so
 * the ordinary couple never meets a choice they do not have.
 *
 * The Spaces are numbered rather than named: a Space ID is a technical value a
 * couple must never be asked to read, and the human name belongs to the Space
 * resource, which arrives with the identity surfaces slice.
 */
@Composable
private fun SpaceChoice(
    spaces: List<AccountMembershipView>,
    activeSpaceId: UUID?,
    enabled: Boolean,
    onSelectSpace: (UUID) -> Unit,
) {
    Surface(
        shape = RoundedCornerShape(SideBySideTheme.radii.card),
        color = SideBySideTheme.colors.surface,
        modifier = Modifier.fillMaxWidth(),
    ) {
        Column(
            modifier = Modifier.padding(SideBySideTheme.spacing.cardPadding),
            verticalArrangement = Arrangement.spacedBy(SideBySideTheme.spacing.step4),
        ) {
            Text(
                text = stringResource(R.string.more_space_title),
                style = MaterialTheme.typography.titleMedium,
                color = SideBySideTheme.colors.textPrimary,
                modifier = Modifier.semantics { heading() },
            )
            Text(
                text = stringResource(R.string.more_space_body),
                style = MaterialTheme.typography.bodyMedium,
                color = SideBySideTheme.colors.textSecondary,
                modifier = Modifier.widthIn(max = ReadingMeasure),
            )
            Column(Modifier.selectableGroup()) {
                spaces.forEachIndexed { index, membership ->
                    val selected = membership.spaceId == activeSpaceId
                    Row(
                        modifier = Modifier
                            .fillMaxWidth()
                            .heightIn(min = MinimumTouchTarget)
                            .selectable(
                                selected = selected,
                                enabled = enabled,
                                role = Role.RadioButton,
                                onClick = { onSelectSpace(membership.spaceId) },
                            ),
                        verticalAlignment = Alignment.CenterVertically,
                    ) {
                        // The row carries the click; the button must not take
                        // a second stop in the screen reader's order.
                        RadioButton(selected = selected, onClick = null)
                        Text(
                            text = stringResource(R.string.more_space_option, index + 1),
                            style = MaterialTheme.typography.bodyLarge,
                            color = SideBySideTheme.colors.textPrimary,
                            modifier = Modifier.padding(
                                start = SideBySideTheme.spacing.step3,
                            ),
                        )
                    }
                }
            }
        }
    }
}

private val ReadingMeasure: Dp = androidx.compose.ui.unit.Dp(560f)
