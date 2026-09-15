package de.eimir.app.account

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.ColumnScope
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.heightIn
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.widthIn
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.text.KeyboardOptions
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
import androidx.compose.ui.text.input.KeyboardType
import androidx.compose.ui.text.input.PasswordVisualTransformation
import androidx.compose.ui.unit.dp
import androidx.compose.ui.window.Dialog
import de.eimir.app.design.MinimumTouchTarget
import de.eimir.app.design.EimirTheme
import de.eimir.app.reference.AccountDeletionRecentAuthenticationCapabilities
import de.eimir.app.reference.R
import de.eimir.app.shell.UiProblem
import de.eimir.app.shell.UiProblemPanel

/**
 * Account-level settings inside the existing More destination.
 *
 * Relationship/Space actions intentionally live elsewhere. This surface owns
 * only the signed-in Account and delegates both recent-authentication and the
 * destructive authority to server-side contracts.
 */
@Composable
fun AccountSettingsContent(
    demoMode: Boolean,
    busy: Boolean,
    problem: UiProblem?,
    recentAuthenticationCapabilities: AccountDeletionRecentAuthenticationCapabilities?,
    recentAuthenticationBusy: Boolean,
    recentAuthenticationProblem: UiProblem?,
    recentAuthenticationComplete: Boolean,
    onLoadRecentAuthentication: () -> Unit,
    onRecentAuthenticationPassword: (String) -> Unit,
    onRecentAuthenticationPasskey: () -> Unit,
    onRecentAuthenticationOidc: (String) -> Unit,
    onResetRecentAuthentication: () -> Unit,
    onOpenDataExport: () -> Unit,
    onDeleteAccount: () -> Unit,
    modifier: Modifier = Modifier,
) {
    var dialogStep by rememberSaveable { mutableIntStateOf(DialogStepNone) }
    var confirmation by rememberSaveable { mutableStateOf("") }
    var password by remember { mutableStateOf("") }
    val operationBusy = busy || recentAuthenticationBusy

    LaunchedEffect(recentAuthenticationComplete, dialogStep) {
        if (recentAuthenticationComplete && dialogStep == DialogStepRecentAuthentication) {
            password = ""
            confirmation = ""
            dialogStep = DialogStepConfirmation
        }
    }

    Surface(
        shape = RoundedCornerShape(EimirTheme.radii.card),
        color = EimirTheme.colors.surface,
        modifier = modifier.fillMaxWidth(),
    ) {
        Column(
            modifier = Modifier.padding(EimirTheme.spacing.cardPadding),
            verticalArrangement = Arrangement.spacedBy(EimirTheme.spacing.step4),
        ) {
            Column(verticalArrangement = Arrangement.spacedBy(EimirTheme.spacing.step2)) {
                Text(
                    text = stringResource(R.string.account_settings_title),
                    style = MaterialTheme.typography.titleLarge,
                    color = EimirTheme.colors.textPrimary,
                    modifier = Modifier.semantics { heading() },
                )
                Text(
                    text = stringResource(R.string.account_settings_intro),
                    style = MaterialTheme.typography.bodyMedium,
                    color = EimirTheme.colors.textSecondary,
                    modifier = Modifier.widthIn(max = ReadingMeasure),
                )
            }

            Surface(
                shape = RoundedCornerShape(EimirTheme.radii.medium),
                color = EimirTheme.colors.errorSurface,
                modifier = Modifier.fillMaxWidth(),
            ) {
                Column(
                    modifier = Modifier.padding(EimirTheme.spacing.step4),
                    verticalArrangement = Arrangement.spacedBy(EimirTheme.spacing.step3),
                ) {
                    Text(
                        text = stringResource(R.string.account_delete_danger_label),
                        style = MaterialTheme.typography.labelLarge,
                        color = EimirTheme.colors.error,
                    )
                    Text(
                        text = stringResource(R.string.account_delete_title),
                        style = MaterialTheme.typography.titleMedium,
                        color = EimirTheme.colors.textPrimary,
                        modifier = Modifier.semantics { heading() },
                    )
                    Text(
                        text = stringResource(R.string.account_delete_intro),
                        style = MaterialTheme.typography.bodyMedium,
                        color = EimirTheme.colors.textSecondary,
                        modifier = Modifier.widthIn(max = ReadingMeasure),
                    )

                    if (demoMode) {
                        Text(
                            text = stringResource(R.string.account_delete_demo_unavailable),
                            style = MaterialTheme.typography.bodyMedium,
                            color = EimirTheme.colors.textSecondary,
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
                            onClick = {
                                confirmation = ""
                                password = ""
                                onResetRecentAuthentication()
                                dialogStep = DialogStepConsequences
                            },
                            enabled = !operationBusy,
                            colors = ButtonDefaults.buttonColors(
                                containerColor = EimirTheme.colors.error,
                                contentColor = EimirTheme.colors.onAccent,
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
            busy = operationBusy,
            onDismiss = {
                if (!operationBusy) {
                    onResetRecentAuthentication()
                    dialogStep = DialogStepNone
                }
            },
            onOpenDataExport = {
                if (!operationBusy) {
                    onResetRecentAuthentication()
                    dialogStep = DialogStepNone
                    onOpenDataExport()
                }
            },
            onContinue = {
                confirmation = ""
                password = ""
                onResetRecentAuthentication()
                dialogStep = DialogStepRecentAuthentication
                onLoadRecentAuthentication()
            },
        )

        DialogStepRecentAuthentication -> AccountDeletionRecentAuthenticationDialog(
            capabilities = recentAuthenticationCapabilities,
            password = password,
            busy = recentAuthenticationBusy,
            problem = recentAuthenticationProblem,
            onPasswordChange = { password = it },
            onPassword = { onRecentAuthenticationPassword(password) },
            onPasskey = onRecentAuthenticationPasskey,
            onOidc = onRecentAuthenticationOidc,
            onBack = {
                if (!recentAuthenticationBusy) {
                    password = ""
                    onResetRecentAuthentication()
                    dialogStep = DialogStepConsequences
                }
            },
            onDismiss = {
                if (!recentAuthenticationBusy) {
                    password = ""
                    onResetRecentAuthentication()
                    dialogStep = DialogStepNone
                }
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
                    password = ""
                    onResetRecentAuthentication()
                    dialogStep = DialogStepConsequences
                }
            },
            onDismiss = {
                if (!busy) {
                    confirmation = ""
                    password = ""
                    onResetRecentAuthentication()
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
            color = EimirTheme.colors.textPrimary,
            modifier = Modifier.semantics { heading() },
        )
        Text(
            text = stringResource(R.string.account_delete_consequences_intro),
            style = MaterialTheme.typography.bodyMedium,
            color = EimirTheme.colors.textSecondary,
        )
        Consequence(R.string.account_delete_consequence_access)
        Consequence(R.string.account_delete_consequence_private)
        Consequence(R.string.account_delete_consequence_shared)
        Consequence(R.string.account_delete_consequence_irreversible)

        OutlinedButton(
            onClick = onOpenDataExport,
            enabled = !busy,
            modifier = Modifier.fillMaxWidth().heightIn(min = MinimumTouchTarget),
        ) {
            Text(stringResource(R.string.account_delete_export_first))
        }
        OutlinedButton(
            onClick = onDismiss,
            enabled = !busy,
            modifier = Modifier.fillMaxWidth().heightIn(min = MinimumTouchTarget),
        ) {
            Text(stringResource(R.string.account_delete_cancel))
        }
        Button(
            onClick = onContinue,
            enabled = !busy,
            modifier = Modifier.fillMaxWidth().heightIn(min = MinimumTouchTarget),
        ) {
            Text(stringResource(R.string.account_delete_continue))
        }
    }
}

@Composable
private fun AccountDeletionRecentAuthenticationDialog(
    capabilities: AccountDeletionRecentAuthenticationCapabilities?,
    password: String,
    busy: Boolean,
    problem: UiProblem?,
    onPasswordChange: (String) -> Unit,
    onPassword: () -> Unit,
    onPasskey: () -> Unit,
    onOidc: (String) -> Unit,
    onBack: () -> Unit,
    onDismiss: () -> Unit,
) {
    AccountDeletionDialog(onDismiss = onDismiss) {
        Text(
            text = stringResource(R.string.account_delete_reauth_title),
            style = MaterialTheme.typography.headlineSmall,
            color = EimirTheme.colors.textPrimary,
            modifier = Modifier.semantics { heading() },
        )
        Text(
            text = stringResource(R.string.account_delete_reauth_intro),
            style = MaterialTheme.typography.bodyMedium,
            color = EimirTheme.colors.textSecondary,
        )

        if (capabilities == null && problem == null) {
            Column(
                modifier = Modifier.semantics { liveRegion = LiveRegionMode.Polite },
                verticalArrangement = Arrangement.spacedBy(EimirTheme.spacing.step2),
            ) {
                CircularProgressIndicator()
                Text(stringResource(R.string.account_delete_reauth_loading))
            }
        }

        if (capabilities?.localPassword == true) {
            OutlinedTextField(
                value = password,
                onValueChange = onPasswordChange,
                label = { Text(stringResource(R.string.account_delete_reauth_password_label)) },
                singleLine = true,
                enabled = !busy,
                keyboardOptions = KeyboardOptions(keyboardType = KeyboardType.Password),
                visualTransformation = PasswordVisualTransformation(),
                modifier = Modifier.fillMaxWidth(),
            )
            Button(
                onClick = onPassword,
                enabled = !busy && password.isNotBlank(),
                modifier = Modifier.fillMaxWidth().heightIn(min = MinimumTouchTarget),
            ) {
                Text(stringResource(R.string.account_delete_reauth_password_action))
            }
        }

        if (capabilities?.passkey == true) {
            OutlinedButton(
                onClick = onPasskey,
                enabled = !busy,
                modifier = Modifier.fillMaxWidth().heightIn(min = MinimumTouchTarget),
            ) {
                Text(stringResource(R.string.account_delete_reauth_passkey_action))
            }
        }

        capabilities?.oidcConnections?.forEach { connectionId ->
            OutlinedButton(
                onClick = { onOidc(connectionId) },
                enabled = !busy,
                modifier = Modifier.fillMaxWidth().heightIn(min = MinimumTouchTarget),
            ) {
                Text(stringResource(R.string.account_delete_reauth_oidc_action, connectionId))
            }
        }

        if (
            capabilities != null &&
            !capabilities.localPassword &&
            !capabilities.passkey &&
            capabilities.oidcConnections.isEmpty()
        ) {
            Text(
                text = stringResource(R.string.account_delete_reauth_unavailable),
                style = MaterialTheme.typography.bodyMedium,
                color = EimirTheme.colors.error,
            )
        }

        if (problem != null) UiProblemPanel(problem = problem)
        if (busy) {
            Text(
                text = stringResource(R.string.account_delete_reauth_pending),
                style = MaterialTheme.typography.bodyMedium,
                color = EimirTheme.colors.textSecondary,
                modifier = Modifier.semantics { liveRegion = LiveRegionMode.Polite },
            )
        }

        OutlinedButton(
            onClick = onBack,
            enabled = !busy,
            modifier = Modifier.fillMaxWidth().heightIn(min = MinimumTouchTarget),
        ) {
            Text(stringResource(R.string.account_delete_back))
        }
        OutlinedButton(
            onClick = onDismiss,
            enabled = !busy,
            modifier = Modifier.fillMaxWidth().heightIn(min = MinimumTouchTarget),
        ) {
            Text(stringResource(R.string.account_delete_cancel))
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
            color = EimirTheme.colors.textPrimary,
            modifier = Modifier.semantics { heading() },
        )
        Text(
            text = stringResource(R.string.account_delete_confirmation_intro),
            style = MaterialTheme.typography.bodyMedium,
            color = EimirTheme.colors.textSecondary,
        )
        Text(
            text = stringResource(R.string.account_delete_confirmation_instruction, phrase),
            style = MaterialTheme.typography.bodyMedium,
            color = EimirTheme.colors.textSecondary,
        )
        Surface(
            shape = RoundedCornerShape(EimirTheme.radii.small),
            color = EimirTheme.colors.surfaceSubtle,
            modifier = Modifier.fillMaxWidth(),
        ) {
            Text(
                text = phrase,
                style = MaterialTheme.typography.titleMedium,
                color = EimirTheme.colors.textPrimary,
                modifier = Modifier.padding(EimirTheme.spacing.step3),
            )
        }
        OutlinedTextField(
            value = confirmation,
            onValueChange = onConfirmationChange,
            label = { Text(stringResource(R.string.account_delete_confirmation_label)) },
            supportingText = { Text(stringResource(R.string.account_delete_confirmation_help)) },
            singleLine = true,
            enabled = !busy,
            modifier = Modifier.fillMaxWidth().focusRequester(focusRequester),
        )

        if (problem != null) UiProblemPanel(problem = problem)
        if (busy) {
            Column(
                modifier = Modifier.semantics { liveRegion = LiveRegionMode.Polite },
                verticalArrangement = Arrangement.spacedBy(EimirTheme.spacing.step2),
            ) {
                CircularProgressIndicator(color = EimirTheme.colors.error)
                Text(
                    text = stringResource(R.string.account_delete_pending),
                    style = MaterialTheme.typography.bodyMedium,
                    color = EimirTheme.colors.textSecondary,
                )
            }
        }

        OutlinedButton(
            onClick = onBack,
            enabled = !busy,
            modifier = Modifier.fillMaxWidth().heightIn(min = MinimumTouchTarget),
        ) {
            Text(stringResource(R.string.account_delete_back))
        }
        OutlinedButton(
            onClick = onDismiss,
            enabled = !busy,
            modifier = Modifier.fillMaxWidth().heightIn(min = MinimumTouchTarget),
        ) {
            Text(stringResource(R.string.account_delete_cancel))
        }
        Button(
            onClick = onConfirm,
            enabled = !busy && confirmation == phrase,
            colors = ButtonDefaults.buttonColors(
                containerColor = EimirTheme.colors.error,
                contentColor = EimirTheme.colors.onAccent,
            ),
            modifier = Modifier.fillMaxWidth().heightIn(min = MinimumTouchTarget),
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
            shape = RoundedCornerShape(EimirTheme.radii.large),
            color = EimirTheme.colors.surfaceRaised,
            tonalElevation = 6.dp,
            modifier = Modifier.fillMaxWidth(),
        ) {
            Column(
                modifier = Modifier
                    .verticalScroll(rememberScrollState())
                    .padding(EimirTheme.spacing.cardPadding),
                verticalArrangement = Arrangement.spacedBy(EimirTheme.spacing.step4),
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
        color = EimirTheme.colors.textSecondary,
    )
}

private const val DialogStepNone = 0
private const val DialogStepConsequences = 1
private const val DialogStepRecentAuthentication = 2
private const val DialogStepConfirmation = 3
private val ReadingMeasure = 560.dp
