package de.sidebyside.next.shell

import androidx.compose.foundation.Canvas
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.heightIn
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.material3.ExperimentalMaterial3Api
import androidx.compose.material3.FloatingActionButton
import androidx.compose.material3.HorizontalDivider
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.ModalBottomSheet
import androidx.compose.material3.Surface
import androidx.compose.material3.Text
import androidx.compose.material3.rememberModalBottomSheetState
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.saveable.rememberSaveable
import androidx.compose.runtime.setValue
import androidx.compose.ui.Modifier
import androidx.compose.ui.geometry.Offset
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.drawscope.Stroke
import androidx.compose.ui.res.stringResource
import androidx.compose.ui.semantics.contentDescription
import androidx.compose.ui.semantics.semantics
import androidx.compose.ui.unit.dp
import de.sidebyside.next.design.MinimumTouchTarget
import de.sidebyside.next.design.SideBySideTheme
import de.sidebyside.next.reference.R

/**
 * The shell-wide quick-create entry point, matching Web's `QuickCreateMenu`.
 *
 * Every list screen already has its own inline creation affordance — the
 * Story header's "Erinnerung festhalten" button, the HeartMoments and
 * PrivateNotes screens' own inline forms — so this does not duplicate any of
 * them. It exists because reaching those requires already being on the right
 * screen; a couple on Heute or Planen has no way to jump straight to
 * creating something shared without first navigating there themselves. This
 * closes that gap by navigating to the right destination, the same as the
 * Web menu's own items do.
 *
 * Milestone is deliberately absent, unlike Web's menu: `ReferenceContract`
 * has `getMilestone`/`updateMilestone`/`deleteMilestone` but no
 * `createMilestone`, even though the generated client's `MilestoneCreate`
 * model exists — the API layer was never wired up. Offering a Milestone
 * option here would be dead navigation.
 */
@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun QuickCreateFab(
    onCreateMemory: () -> Unit,
    onCreateHeartMoment: () -> Unit,
    onCreatePrivateNote: () -> Unit,
    modifier: Modifier = Modifier,
) {
    var open by rememberSaveable { mutableStateOf(false) }

    val triggerLabel = stringResource(R.string.quick_create_trigger)
    FloatingActionButton(
        onClick = { open = true },
        modifier = modifier.semantics { contentDescription = triggerLabel },
    ) {
        PlusGlyph(tint = MaterialTheme.colorScheme.onPrimaryContainer)
    }

    if (open) {
        val sheetState = rememberModalBottomSheetState()
        ModalBottomSheet(onDismissRequest = { open = false }, sheetState = sheetState) {
            Column(
                modifier = Modifier
                    .fillMaxWidth()
                    .padding(SideBySideTheme.spacing.pageMargin),
            ) {
                QuickCreateGroupLabel(R.string.quick_create_shared_group)
                QuickCreateItem(R.string.quick_create_memory) {
                    open = false
                    onCreateMemory()
                }
                QuickCreateItem(R.string.quick_create_heart_moment) {
                    open = false
                    onCreateHeartMoment()
                }

                HorizontalDivider(modifier = Modifier.padding(vertical = SideBySideTheme.spacing.step3))

                QuickCreateGroupLabel(R.string.quick_create_private_group)
                QuickCreateItem(R.string.quick_create_private_note) {
                    open = false
                    onCreatePrivateNote()
                }
            }
        }
    }
}

/**
 * A plus sign, drawn rather than pulled from an icon dependency — the same
 * reasoning [DestinationGlyph] already gives for the destination icons, and
 * the same shape Web's own `DestinationIcon` "add" case draws.
 */
@Composable
private fun PlusGlyph(tint: Color) {
    Canvas(modifier = Modifier.size(24.dp)) {
        val stroke = Stroke(width = this.size.minDimension * 0.08f)
        drawLine(
            color = tint,
            start = Offset(size.width / 2f, size.height * 0.2f),
            end = Offset(size.width / 2f, size.height * 0.8f),
            strokeWidth = stroke.width,
        )
        drawLine(
            color = tint,
            start = Offset(size.width * 0.2f, size.height / 2f),
            end = Offset(size.width * 0.8f, size.height / 2f),
            strokeWidth = stroke.width,
        )
    }
}

@Composable
private fun QuickCreateGroupLabel(labelRes: Int) {
    Text(
        text = stringResource(labelRes),
        style = MaterialTheme.typography.labelLarge,
        color = SideBySideTheme.colors.textSecondary,
        modifier = Modifier.padding(bottom = SideBySideTheme.spacing.step2),
    )
}

@Composable
private fun QuickCreateItem(labelRes: Int, onClick: () -> Unit) {
    Surface(
        onClick = onClick,
        modifier = Modifier
            .fillMaxWidth()
            .heightIn(min = MinimumTouchTarget),
        color = SideBySideTheme.colors.surface,
    ) {
        Text(
            text = stringResource(labelRes),
            style = MaterialTheme.typography.bodyLarge,
            color = SideBySideTheme.colors.textPrimary,
            modifier = Modifier.padding(SideBySideTheme.spacing.cardPadding),
        )
    }
}
