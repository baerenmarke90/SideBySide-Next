package de.sidebyside.next.privatearea

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
import androidx.compose.material3.TextButton
import androidx.compose.runtime.Composable
import androidx.compose.ui.Modifier
import androidx.compose.ui.res.stringResource
import androidx.compose.ui.semantics.heading
import androidx.compose.ui.semantics.semantics
import androidx.compose.ui.unit.Dp
import androidx.compose.ui.unit.dp
import de.sidebyside.next.design.FrauncesFamily
import de.sidebyside.next.design.MinimumTouchTarget
import de.sidebyside.next.design.SideBySideTheme
import de.sidebyside.next.reference.R

private val ReadingMeasure: Dp = 560.dp

/**
 * Entry point for the owner-only surfaces. A hub rather than a flat list of
 * cards on [de.sidebyside.next.shell.MoreScreen], because #356 groups
 * several domains (notes today, Gift Ideas and Collections join in their own
 * slices) that all share the same isolation and Recents/screenshot policy;
 * one shared "you are in the private area now" moment says that once rather
 * than on every card.
 *
 */
@Composable
fun PrivateAreaScreen(
    onBack: () -> Unit,
    onOpenNotes: () -> Unit,
    onOpenGiftIdeas: () -> Unit,
    onOpenCollections: () -> Unit,
    modifier: Modifier = Modifier,
) {
    Column(
        modifier = modifier
            .fillMaxWidth()
            .verticalScroll(rememberScrollState())
            .padding(SideBySideTheme.spacing.pageMargin),
        verticalArrangement = Arrangement.spacedBy(SideBySideTheme.spacing.step5),
    ) {
        TextButton(onClick = onBack) { Text(stringResource(R.string.memory_back)) }

        Column(verticalArrangement = Arrangement.spacedBy(SideBySideTheme.spacing.step2)) {
            Text(
                text = stringResource(R.string.private_area_title),
                style = MaterialTheme.typography.headlineMedium.copy(fontFamily = FrauncesFamily),
                color = SideBySideTheme.colors.textPrimary,
                modifier = Modifier.semantics { heading() },
            )
            Text(
                text = stringResource(R.string.private_area_intro),
                style = MaterialTheme.typography.bodyMedium,
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
                verticalArrangement = Arrangement.spacedBy(SideBySideTheme.spacing.step3),
            ) {
                Text(
                    text = stringResource(R.string.private_notes_title),
                    style = MaterialTheme.typography.titleMedium,
                    color = SideBySideTheme.colors.textPrimary,
                    modifier = Modifier.semantics { heading() },
                )
                Text(
                    text = stringResource(R.string.private_notes_intro),
                    style = MaterialTheme.typography.bodyMedium,
                    color = SideBySideTheme.colors.textSecondary,
                )
                OutlinedButton(
                    onClick = onOpenNotes,
                    modifier = Modifier.heightIn(min = MinimumTouchTarget),
                ) {
                    Text(stringResource(R.string.private_notes_open))
                }
            }
        }

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
                    text = stringResource(R.string.gift_ideas_title),
                    style = MaterialTheme.typography.titleMedium,
                    color = SideBySideTheme.colors.textPrimary,
                    modifier = Modifier.semantics { heading() },
                )
                Text(
                    text = stringResource(R.string.gift_ideas_intro),
                    style = MaterialTheme.typography.bodyMedium,
                    color = SideBySideTheme.colors.textSecondary,
                )
                OutlinedButton(
                    onClick = onOpenGiftIdeas,
                    modifier = Modifier.heightIn(min = MinimumTouchTarget),
                ) {
                    Text(stringResource(R.string.gift_ideas_open))
                }
            }
        }

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
                    text = stringResource(R.string.private_collections_title),
                    style = MaterialTheme.typography.titleMedium,
                    color = SideBySideTheme.colors.textPrimary,
                    modifier = Modifier.semantics { heading() },
                )
                Text(
                    text = stringResource(R.string.private_collections_intro),
                    style = MaterialTheme.typography.bodyMedium,
                    color = SideBySideTheme.colors.textSecondary,
                )
                OutlinedButton(
                    onClick = onOpenCollections,
                    modifier = Modifier.heightIn(min = MinimumTouchTarget),
                ) {
                    Text(stringResource(R.string.private_collections_open))
                }
            }
        }
    }
}
