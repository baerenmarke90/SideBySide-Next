package de.sidebyside.next.account

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.ColumnScope
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.heightIn
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.widthIn
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.verticalScroll
import androidx.compose.foundation.shape.RoundedCornerShape
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

/**
 * Account-level settings inside the existing More destination.
 *
 * Relationship/Space actions intentionally live elsewhere. This surface owns
 * only the signed-in Account and delegates the destructive authority to the
 * server-side deletion contract.
 */
@Composable
fun AccountSettingsContent(
    demoMode: Boolean,
    busy: Boolean,
    problem: UiProblem?,
    onOpenDataExport: () -> Unit,
    onDeleteAccount: () -> Unit,
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
            Column(verticalArrangement = Arrangement.spacedBy(SideBySideTheme.spacing.step2)) {
                Text(
                    text = stringResource(R.string.account_settings_title),
                    style = MaterialTheme.typography.titleLarge,
                    color = SideBySideTheme.colors.textPrimary,
                    modifier = Modifier.semantics { heading() },
                )
                Text(
                    text = stringResource(R.string.account_settings_intro),
                    style = MaterialTheme.typography.bodyMedium,
                    color = SideBySideTheme.colors.textSecondary,
                    modifier = Modifier.widthIn(max = ReadingMeasure),
                )
            }

            Surface(
                shape = RoundedCornerShape(SideBySideTheme.radii.medium),
                color = SideBySideTheme.colors.errorSurface,
                modifier = Modifier.fillMaxWidth(),
            ) {
                Column(
                    modifier = Modifier.padding(SideBySideTheme.spacing.step4),
                    verticalArrangement = Arrangement.spacedBy(SideBySideTheme.spacing.step3),
                ) {
                    Text(
                        text = stringResource(R.string.account_delete_danger_label),
                        style = MaterialTheme.typography.labelLarge,
                        color = SideBySideTheme.colors.error,
                    )
                    Text(
                        text = stringResource(R.string.account_delete_title),
                        style = MaterialTheme.typography.titleMedium,
                        color = SideBySideTheme.colors.textPrimary,
                        modifier = Modifier.semantics { heading() },
                    )
                    Text(
                        text = stringResource(R.string.account_delete_intro),
                        style = MaterialTheme.typography.bodyMedium,
                        color = SideBySideTheme.colors.textSecondary,
                        modifier = Modifier.widthIn(max = ReadingMeasure),
                    )

                    if (demoMode) {
                        Text(
                            text = stringResource(R.string.account_delete_demo_unavailable),
                            style = MaterialTheme.typography.bodyMedium,
                            color = SideBySideTheme.colors.textSecondary,
                        )
                        OutlinedButton(
                            onClick = {},
                            enabled = false,
                            modifier = Modifier.heightIn(min = MinimumTouchTarget),
                        ) {
                            Text(stringResource(R.string.account_delete_action))
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
                            Text(stringResource(R.string.account_delete_action))
                        }
                    }
                }
            }
        }
    }

    when (dialogStep) {
        DialogStepConsequences -> AccountDeletionConsequencesDialog(
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

        DialogStepConfirmation -> AccountDeletionConfirmationDialog(
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
            onConfirm = onDeleteAccount,
        )
    }
}

@Composable
private fun AccountDeletionConsequencesDialog(
    busy: Boolean,
    onDismiss: () -> Unit,
    onOpenDataExport: () -> Unit,
    onContinue: () -> Unit,
) {
    AccountDeletionDialog(onDismiss = onDismiss) {
        Text(
            text = stringResource(R.string.account_delete_consequences_title),
            style = MaterialTheme.typography.headlineSmall,
            color = SideBySideTheme.colors.textPrimary,
            modifier = Modifier.semantics { heading() },
        )
        Text(
            text = stringResource(R.string.account_delete_consequences_intro),
            style = MaterialTheme.typography.bodyMedium,
            color = SideBySideTheme.colors.textSecondary,
        )
        Consequence(R.string.account_delete_consequence_access)
        Consequence(R.string.account_delete_consequence_private)
        Consequence(R.string.account_delete_consequence_shared)
        Consequence(R.string.account_delete_consequence_irreversible)

        OutlinedButton(
            onClick = onOpenDataExport,
            enabled = !busy,
            modifier = Modifier
                .fillMaxWidth()
                .heightIn(min = MinimumTouchTarget),
        ) {
            Text(stringResource(R.string.account_delete_export_first))
        }
        OutlinedButton(
            onClick = onDismiss,
            enabled = !busy,
            modifier = Modifier
                .fillMaxWidth()
                .heightIn(min = MinimumTouchTarget),
        ) {
            Text(stringResource(R.string.account_delete_cancel))
        }
        Button(
            onClick = onContinue,
            enabled = !busy,
            modifier = Modifier
                .fillMaxWidth()
                .heightIn(min = MinimumTouchTarget),
        ) {
            Text(stringResource(R.string.account_delete_continue))
        }
    }
}

@Composable
private fun AccountDeletionConfirmationDialog(
    confirmation: String,
    busy: Boolean,
    problem: UiProblem?,
    onConfirmationChange: (String) -> Unit,
    onBack: () -> Unit,
    onDismiss: () -> Unit,
    onConfirm: () -> Unit,
) {
    val phrase = stringResource(R.string.account_delete_confirmation_phrase)
    val focusRequester = remember { FocusRequester() }

    LaunchedEffect(Unit) { focusRequester.requestFocus() }

    AccountDeletionDialog(onDismiss = onDismiss) {
        Text(
            text = stringResource(R.string.account_delete_confirmation_title),
            style = MaterialTheme.typography.headlineSmall,
            color = SideBySideTheme.colors.textPrimary,
            modifier = Modifier.semantics { heading() },
        )
        Text(
            text = stringResource(R.string.account_delete_confirmation_intro),
            style = MaterialTheme.typography.bodyMedium,
            color = SideBySideTheme.colors.textSecondary,
        )
        Text(
            text = stringResource(R.string.account_delete_confirmation_instruction, phrase),
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
            label = { Text(stringResource(R.string.account_delete_confirmation_label)) },
            supportingText = { Text(stringResource(R.string.account_delete_confirmation_help)) },
            singleLine = true,
            enabled = !busy,
            modifier = Modifier
                .fillMaxWidth()
                .focusRequester(focusRequester),
        )

        if (problem != null) {
            UiProblemPanel(problem = problem)
        }
        if (busy) {
            Column(
                modifier = Modifier.semantics { liveRegion = LiveRegionMode.Polite },
                verticalArrangement = Arrangement.spacedBy(SideBySideTheme.spacing.step2),
            ) {
                CircularProgressIndicator(color = SideBySideTheme.colors.error)
                Text(
                    text = stringResource(R.string.account_delete_pending),
                    style = MaterialTheme.typography.bodyMedium,
                    color = SideBySideTheme.colors.textSecondary,
                )
            }
        }

        OutlinedButton(
            onClick = onBack,
            enabled = !busy,
            modifier = Modifier
                .fillMaxWidth()
                .heightIn(min = MinimumTouchTarget),
        ) {
            Text(stringResource(R.string.account_delete_back))
        }
        OutlinedButton(
            onClick = onDismiss,
            enabled = !busy,
            modifier = Modifier
                .fillMaxWidth()
                .heightIn(min = MinimumTouchTarget),
        ) {
            Text(stringResource(R.string.account_delete_cancel))
        }
        Button(
            onClick = onConfirm,
            enabled = !busy && confirmation == phrase,
            colors = ButtonDefaults.buttonColors(
                containerColor = SideBySideTheme.colors.error,
                contentColor = SideBySideTheme.colors.onAccent,
            ),
            modifier = Modifier
                .fillMaxWidth()
                .heightIn(min = MinimumTouchTarget),
        ) {
            Text(stringResource(R.string.account_delete_confirm_action))
        }
    }
}

@Composable
private fun AccountDeletionDialog(
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
    )
}

private const val DialogStepNone = 0
private const val DialogStepConsequences = 1
private const val DialogStepConfirmation = 2
private val ReadingMeasure = 560.dp
