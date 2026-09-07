package de.sidebyside.next.invitation

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.heightIn
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.widthIn
import androidx.compose.foundation.selection.selectable
import androidx.compose.foundation.selection.selectableGroup
import androidx.compose.material3.Button
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.RadioButton
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.runtime.Composable
import androidx.compose.runtime.collectAsState
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.saveable.rememberSaveable
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.res.stringResource
import androidx.compose.ui.semantics.Role
import androidx.compose.ui.semantics.heading
import androidx.compose.ui.semantics.semantics
import androidx.compose.ui.unit.Dp
import androidx.compose.ui.unit.dp
import androidx.lifecycle.viewmodel.compose.viewModel
import de.sidebyside.next.design.SideBySideDisplayFamily
import de.sidebyside.next.design.MinimumTouchTarget
import de.sidebyside.next.design.SideBySideTheme
import de.sidebyside.next.reference.R
import de.sidebyside.next.reference.ReferenceViewModel
import de.sidebyside.next.shell.UiProblem
import de.sidebyside.next.shell.UiStatePanel
import java.util.UUID
import sidebyside.api.models.AccountMembershipView

private val ReadingMeasure: Dp = 560.dp

/**
 * An authenticated account that cannot enter a Space yet.
 *
 * The surrounding reference route already owns the authenticated
 * [ReferenceViewModel]. Looking it up by the same Activity-scoped ViewModel key
 * keeps this waiting-room route non-Space-bound while allowing it to render the
 * explicit chooser when the account has several active memberships.
 */
@Composable
fun AwaitingSpaceScreen(
    busy: Boolean,
    problem: UiProblem?,
    onAcceptInvitation: (String) -> Unit,
    onSignOut: () -> Unit,
    modifier: Modifier = Modifier,
    referenceViewModel: ReferenceViewModel = viewModel(),
) {
    val referenceState by referenceViewModel.uiState.collectAsState()

    AwaitingSpaceContent(
        busy = busy,
        problem = problem,
        onAcceptInvitation = onAcceptInvitation,
        onSignOut = onSignOut,
        spaces = referenceState.availableSpaces,
        onSelectSpace = referenceViewModel::selectSpace,
        modifier = modifier,
    )
}

@Composable
private fun AwaitingSpaceContent(
    busy: Boolean,
    problem: UiProblem?,
    onAcceptInvitation: (String) -> Unit,
    onSignOut: () -> Unit,
    spaces: List<AccountMembershipView>,
    onSelectSpace: (UUID) -> Unit,
    modifier: Modifier = Modifier,
) {
    Column(
        modifier = modifier
            .fillMaxSize()
            .padding(SideBySideTheme.spacing.pageMargin),
        verticalArrangement = Arrangement.spacedBy(SideBySideTheme.spacing.step5),
    ) {
        if (spaces.size > 1) {
            Column(verticalArrangement = Arrangement.spacedBy(SideBySideTheme.spacing.step2)) {
                Text(
                    text = stringResource(R.string.more_space_title),
                    style = MaterialTheme.typography.headlineMedium.copy(fontFamily = SideBySideDisplayFamily),
                    color = SideBySideTheme.colors.textPrimary,
                    modifier = Modifier.semantics { heading() },
                )
                Text(
                    text = stringResource(R.string.more_space_body),
                    style = MaterialTheme.typography.bodyLarge,
                    color = SideBySideTheme.colors.textSecondary,
                    modifier = Modifier.widthIn(max = ReadingMeasure),
                )
            }

            problem?.let { UiStatePanel(problem = it) }

            Column(Modifier.selectableGroup()) {
                spaces.forEachIndexed { index, membership ->
                    Row(
                        modifier = Modifier
                            .fillMaxWidth()
                            .heightIn(min = MinimumTouchTarget)
                            .selectable(
                                selected = false,
                                enabled = !busy,
                                role = Role.RadioButton,
                                onClick = { onSelectSpace(membership.spaceId) },
                            ),
                        verticalAlignment = Alignment.CenterVertically,
                    ) {
                        RadioButton(selected = false, onClick = null)
                        Text(
                            text = stringResource(R.string.more_space_option, index + 1),
                            style = MaterialTheme.typography.bodyLarge,
                            color = SideBySideTheme.colors.textPrimary,
                        )
                    }
                }
            }

            TextButton(onClick = onSignOut, enabled = !busy) {
                Text(stringResource(R.string.ref_logout))
            }
            return@Column
        }

        var code by rememberSaveable { mutableStateOf("") }

        Column(verticalArrangement = Arrangement.spacedBy(SideBySideTheme.spacing.step2)) {
            Text(
                text = stringResource(R.string.awaiting_space_title),
                style = MaterialTheme.typography.headlineMedium.copy(fontFamily = SideBySideDisplayFamily),
                color = SideBySideTheme.colors.textPrimary,
                modifier = Modifier.semantics { heading() },
            )
            Text(
                text = stringResource(R.string.awaiting_space_body),
                style = MaterialTheme.typography.bodyLarge,
                color = SideBySideTheme.colors.textSecondary,
                modifier = Modifier.widthIn(max = ReadingMeasure),
            )
        }

        problem?.let { UiStatePanel(problem = it) }

        OutlinedTextField(
            value = code,
            onValueChange = { code = it.trim() },
            label = { Text(stringResource(R.string.invitation_code_hint)) },
            singleLine = true,
            modifier = Modifier.fillMaxWidth().widthIn(max = ReadingMeasure),
        )
        Button(
            onClick = { onAcceptInvitation(code) },
            enabled = !busy && code.isNotBlank(),
            modifier = Modifier.heightIn(min = MinimumTouchTarget),
        ) {
            Text(stringResource(R.string.invitation_accept))
        }

        TextButton(onClick = onSignOut, enabled = !busy) {
            Text(stringResource(R.string.ref_logout))
        }
    }
}
