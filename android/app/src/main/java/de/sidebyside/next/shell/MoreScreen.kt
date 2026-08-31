package de.sidebyside.next.shell

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.heightIn
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.widthIn
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedButton
import androidx.compose.material3.Surface
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Modifier
import androidx.compose.ui.res.stringResource
import androidx.compose.ui.semantics.heading
import androidx.compose.ui.semantics.semantics
import androidx.compose.ui.unit.Dp
import de.sidebyside.next.design.MinimumTouchTarget
import de.sidebyside.next.design.SideBySideTheme
import de.sidebyside.next.reference.R

/**
 * The Mehr area.
 *
 * It carries only what exists today: who is signed in, and how to sign out.
 * Space and partner, people, the owner-only area, notifications and profile
 * join it in their own slices rather than appearing here as empty rows.
 */
@Composable
fun MoreScreen(
    onSignOut: () -> Unit,
    modifier: Modifier = Modifier,
    signOutEnabled: Boolean = true,
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

private val ReadingMeasure: Dp = androidx.compose.ui.unit.Dp(560f)
