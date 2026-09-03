package de.sidebyside.next.invitation

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.heightIn
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.widthIn
import androidx.compose.material3.Button
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.saveable.rememberSaveable
import androidx.compose.runtime.setValue
import androidx.compose.ui.Modifier
import androidx.compose.ui.res.stringResource
import androidx.compose.ui.semantics.heading
import androidx.compose.ui.semantics.semantics
import androidx.compose.ui.unit.Dp
import androidx.compose.ui.unit.dp
import de.sidebyside.next.design.SideBySideDisplayFamily
import de.sidebyside.next.design.MinimumTouchTarget
import de.sidebyside.next.design.SideBySideTheme
import de.sidebyside.next.reference.R
import de.sidebyside.next.shell.UiProblem
import de.sidebyside.next.shell.UiStatePanel

private val ReadingMeasure: Dp = 560.dp

/**
 * An authenticated account with no Space to open.
 *
 * The only affordance here is entering an invitation. That is deliberate: this
 * is a waiting room, not a dead end, and the one thing that moves an account
 * out of it is someone's partner handing them a code.
 */
@Composable
fun AwaitingSpaceScreen(
    busy: Boolean,
    problem: UiProblem?,
    onAcceptInvitation: (String) -> Unit,
    onSignOut: () -> Unit,
    modifier: Modifier = Modifier,
) {
    var code by rememberSaveable { mutableStateOf("") }

    Column(
        modifier = modifier
            .fillMaxSize()
            .padding(SideBySideTheme.spacing.pageMargin),
        verticalArrangement = Arrangement.spacedBy(SideBySideTheme.spacing.step5),
    ) {
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
