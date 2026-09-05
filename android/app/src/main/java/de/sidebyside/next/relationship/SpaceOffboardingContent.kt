package de.sidebyside.next.relationship

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.ColumnScope
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.heightIn
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.widthIn
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.Button
import androidx.compose.material3.ButtonDefaults
import androidx.compose.material3.CircularProgressIndicator
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedButton
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.Surface
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableIntStateOf
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.saveable.rememberSaveable
import androidx.compose.runtime.setValue
import androidx.compose.ui.Modifier
import androidx.compose.ui.focus.FocusRequester
import androidx.compose.ui.focus.focusRequester
import androidx.compose.ui.res.stringResource
import androidx.compose.ui.semantics.LiveRegionMode
import androidx.compose.ui.semantics.heading
import androidx.compose.ui.semantics.liveRegion
import androidx.compose.ui.semantics.semantics
import androidx.compose.ui.unit.dp
import androidx.compose.ui.window.Dialog
import de.sidebyside.next.design.MinimumTouchTarget
import de.sidebyside.next.design.SideBySideTheme
import de.sidebyside.next.reference.R
import de.sidebyside.next.shell.UiProblem
import de.sidebyside.next.shell.UiProblemPanel

/** Relationship-level self-offboarding, deliberately separate from Account deletion. */
@Composable
fun SpaceOffboardingContent(
    demoMode: Boolean,
    busy: Boolean,
    problem: UiProblem?,
    onOpenDataExport: () -> Unit,
    onLeaveSpace: () -> Unit,
    modifier: Modifier = Modifier,
) {
    var dialogStep by rememberSaveable { mutableIntStateOf(DialogStepNone) }
    var confirmation by rememberSaveable { mutableStateOf("") }

    Surface(
        shape = RoundedCornerShape(SideBySideTheme.radii.card),
        color = SideBySideTheme.colors.surface,
        modifier = modifier.fillMaxWidth(),
    ) {
        Column(
            modifier = Modifier.padding(SideBySideTheme.spacing.cardPadding),
            verticalArrangement = Arrangement.spacedBy(SideBySideTheme.spacing.step4),
        ) {
            Text(
                text = stringResource(R.string.space_offboarding_title),
                style = MaterialTheme.typography.titleLarge,
                color = SideBySideTheme.colors.textPrimary,
                modifier = Modifier.semantics { heading() },
            )
            Text(
                text = stringResource(R.string.space_offboarding_intro),
                style = MaterialTheme.typography.bodyMedium,
                color = SideBySideTheme.colors.textSecondary,
                modifier = Modifier.widthIn(max = ReadingMeasure),
            )

            if (demoMode) {
                Text(
                    text = stringResource(R.string.space_offboarding_demo_unavailable),
                    style = MaterialTheme.typography.bodyMedium,
                    color = SideBySideTheme.colors.textSecondary,
                )
                OutlinedButton(
                    onClick = {},
                    enabled = false,
                    modifier = Modifier.heightIn(min = MinimumTouchTarget),
                ) {
                    Text(stringResource(R.string.space_offboarding_action))
                }
            } else {
                Button(
                    onClick = { dialogStep = DialogStepConsequences },
                    enabled = !busy,
                    colors = ButtonDefaults.buttonColors(
                        containerColor = SideBySideTheme.colors.error,
                        contentColor = SideBySideTheme.colors.onAccent,
                    ),
                    modifier = Modifier.heightIn(min = MinimumTouchTarget),
                ) {
                    Text(stringResource(R.string.space_offboarding_action))
                }
            }
        }
    }

    when (dialogStep) {
        DialogStepConsequences -> SpaceExitConsequencesDialog(
            busy = busy,
            onDismiss = { if (!busy) dialogStep = DialogStepNone },
            onOpenDataExport = {
                if (!busy) {
                    dialogStep = DialogStepNone
                    onOpenDataExport()
                }
            },
            onContinue = {
                confirmation = ""
                dialogStep = DialogStepConfirmation
            },
        )

        DialogStepConfirmation -> SpaceExitConfirmationDialog(
            confirmation = confirmation,
            busy = busy,
            problem = problem,
            onConfirmationChange = { confirmation = it },
            onBack = {
                if (!busy) {
                    confirmation = ""
                    dialogStep = DialogStepConsequences
                }
            },
            onDismiss = {
                if (!busy) {
                    confirmation = ""
                    dialogStep = DialogStepNone
                }
            },
            onConfirm = onLeaveSpace,
        )
    }
}

@Composable
private fun SpaceExitConsequencesDialog(
    busy: Boolean,
    onDismiss: () -> Unit,
    onOpenDataExport: () -> Unit,
    onContinue: () -> Unit,
) {
    SpaceExitDialog(onDismiss = onDismiss) {
        Text(
            text = stringResource(R.string.space_offboarding_consequences_title),
            style = MaterialTheme.typography.headlineSmall,
            color = SideBySideTheme.colors.textPrimary,
            modifier = Modifier.semantics { heading() },
        )
        Text(
            text = stringResource(R.string.space_offboarding_consequences_intro),
            style = MaterialTheme.typography.bodyMedium,
            color = SideBySideTheme.colors.textSecondary,
        )
        Consequence(R.string.space_offboarding_consequence_access)
        Consequence(R.string.space_offboarding_consequence_account)
        Consequence(R.string.space_offboarding_consequence_private)
        Consequence(R.string.space_offboarding_consequence_shared)
        Consequence(R.string.space_offboarding_consequence_export)

        OutlinedButton(
            onClick = onOpenDataExport,
            enabled = !busy,
            modifier = Modifier.fillMaxWidth().heightIn(min = MinimumTouchTarget),
        ) {
            Text(stringResource(R.string.space_offboarding_export_first))
        }
        OutlinedButton(
            onClick = onDismiss,
            enabled = !busy,
            modifier = Modifier.fillMaxWidth().heightIn(min = MinimumTouchTarget),
        ) {
            Text(stringResource(R.string.space_offboarding_cancel))
        }
        Button(
            onClick = onContinue,
            enabled = !busy,
            modifier = Modifier.fillMaxWidth().heightIn(min = MinimumTouchTarget),
        ) {
            Text(stringResource(R.string.space_offboarding_continue))
        }
    }
}

@Composable
private fun SpaceExitConfirmationDialog(
    confirmation: String,
    busy: Boolean,
    problem: UiProblem?,
    onConfirmationChange: (String) -> Unit,
    onBack: () -> Unit,
    onDismiss: () -> Unit,
    onConfirm: () -> Unit,
) {
    val phrase = stringResource(R.string.space_offboarding_confirmation_phrase)
    val focusRequester = remember { FocusRequester() }

    LaunchedEffect(Unit) { focusRequester.requestFocus() }

    SpaceExitDialog(onDismiss = onDismiss) {
        Text(
            text = stringResource(R.string.space_offboarding_confirmation_title),
            style = MaterialTheme.typography.headlineSmall,
            color = SideBySideTheme.colors.textPrimary,
            modifier = Modifier.semantics { heading() },
        )
        Text(
            text = stringResource(R.string.space_offboarding_confirmation_intro),
            style = MaterialTheme.typography.bodyMedium,
            color = SideBySideTheme.colors.textSecondary,
        )
        Text(
            text = stringResource(R.string.space_offboarding_confirmation_instruction, phrase),
            style = MaterialTheme.typography.bodyMedium,
            color = SideBySideTheme.colors.textSecondary,
        )
        Surface(
            shape = RoundedCornerShape(SideBySideTheme.radii.small),
            color = SideBySideTheme.colors.surfaceSubtle,
            modifier = Modifier.fillMaxWidth(),
        ) {
            Text(
                text = phrase,
                style = MaterialTheme.typography.titleMedium,
                color = SideBySideTheme.colors.textPrimary,
                modifier = Modifier.padding(SideBySideTheme.spacing.step3),
            )
        }
        OutlinedTextField(
            value = confirmation,
            onValueChange = onConfirmationChange,
            label = { Text(stringResource(R.string.space_offboarding_confirmation_label)) },
            supportingText = { Text(stringResource(R.string.space_offboarding_confirmation_help)) },
            singleLine = true,
            enabled = !busy,
            modifier = Modifier.fillMaxWidth().focusRequester(focusRequester),
        )

        if (problem != null) UiProblemPanel(problem = problem)
        if (busy) {
            Column(
                modifier = Modifier.semantics { liveRegion = LiveRegionMode.Polite },
                verticalArrangement = Arrangement.spacedBy(SideBySideTheme.spacing.step2),
            ) {
                CircularProgressIndicator(color = SideBySideTheme.colors.error)
                Text(
                    text = stringResource(R.string.space_offboarding_pending),
                    style = MaterialTheme.typography.bodyMedium,
                    color = SideBySideTheme.colors.textSecondary,
                )
            }
        }

        OutlinedButton(
            onClick = onBack,
            enabled = !busy,
            modifier = Modifier.fillMaxWidth().heightIn(min = MinimumTouchTarget),
        ) {
            Text(stringResource(R.string.space_offboarding_back))
        }
        OutlinedButton(
            onClick = onDismiss,
            enabled = !busy,
            modifier = Modifier.fillMaxWidth().heightIn(min = MinimumTouchTarget),
        ) {
            Text(stringResource(R.string.space_offboarding_cancel))
        }
        Button(
            onClick = onConfirm,
            enabled = !busy && confirmation == phrase,
            colors = ButtonDefaults.buttonColors(
                containerColor = SideBySideTheme.colors.error,
                contentColor = SideBySideTheme.colors.onAccent,
            ),
            modifier = Modifier.fillMaxWidth().heightIn(min = MinimumTouchTarget),
        ) {
            Text(stringResource(R.string.space_offboarding_confirm_action))
        }
    }
}

@Composable
private fun SpaceExitDialog(
    onDismiss: () -> Unit,
    content: @Composable ColumnScope.() -> Unit,
) {
    Dialog(onDismissRequest = onDismiss) {
        Surface(
            shape = RoundedCornerShape(SideBySideTheme.radii.large),
            color = SideBySideTheme.colors.surfaceRaised,
            tonalElevation = 6.dp,
            modifier = Modifier.fillMaxWidth(),
        ) {
            Column(
                modifier = Modifier
                    .verticalScroll(rememberScrollState())
                    .padding(SideBySideTheme.spacing.cardPadding),
                verticalArrangement = Arrangement.spacedBy(SideBySideTheme.spacing.step4),
                content = content,
            )
        }
    }
}

@Composable
private fun Consequence(resourceId: Int) {
    Text(
        text = "• ${stringResource(resourceId)}",
        style = MaterialTheme.typography.bodyMedium,
        color = SideBySideTheme.colors.textSecondary,
        modifier = Modifier.widthIn(max = ReadingMeasure),
    )
}

private val ReadingMeasure = 560.dp
private const val DialogStepNone = 0
private const val DialogStepConsequences = 1
private const val DialogStepConfirmation = 2
