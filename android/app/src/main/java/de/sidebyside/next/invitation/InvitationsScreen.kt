package de.sidebyside.next.invitation

import android.content.Intent
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.heightIn
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.widthIn
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.AlertDialog
import androidx.compose.material3.Button
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Surface
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.runtime.Composable
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.platform.LocalConfiguration
import androidx.compose.ui.res.stringResource
import androidx.compose.ui.semantics.heading
import androidx.compose.ui.semantics.semantics
import androidx.compose.ui.unit.Dp
import androidx.compose.ui.unit.dp
import de.sidebyside.next.design.MinimumTouchTarget
import de.sidebyside.next.design.SideBySideTheme
import de.sidebyside.next.reference.R
import de.sidebyside.next.shell.UiProblem
import de.sidebyside.next.shell.UiStatePanel
import java.time.format.DateTimeFormatter
import java.time.format.FormatStyle
import java.util.Locale
import java.util.UUID
import sidebyside.api.models.InvitationView

private val ReadingMeasure: Dp = 560.dp

/**
 * Inviting a partner into this Space.
 *
 * A freshly issued token is shown exactly once, per the contract: the server
 * never returns it again once this screen is left, so the only way off it is
 * the system share sheet or a deliberate dismissal.
 */
@Composable
fun InvitationsScreen(
    invitations: List<InvitationView>,
    issuedToken: String?,
    busy: Boolean,
    problem: UiProblem?,
    onBack: () -> Unit,
    onCreate: () -> Unit,
    onDismissToken: () -> Unit,
    onRevoke: (UUID) -> Unit,
    modifier: Modifier = Modifier,
) {
    val context = LocalContext.current
    val locale: Locale = LocalConfiguration.current.locales[0]
    val dateFormat = DateTimeFormatter.ofLocalizedDate(FormatStyle.LONG).withLocale(locale)

    LazyColumn(
        modifier = modifier.fillMaxWidth(),
        contentPadding = androidx.compose.foundation.layout.PaddingValues(
            SideBySideTheme.spacing.pageMargin,
        ),
        verticalArrangement = Arrangement.spacedBy(SideBySideTheme.spacing.step5),
    ) {
        item {
            TextButton(onClick = onBack) { Text(stringResource(R.string.memory_back)) }
        }

        item {
            Column(verticalArrangement = Arrangement.spacedBy(SideBySideTheme.spacing.step2)) {
                Text(
                    text = stringResource(R.string.invitations_title),
                    style = MaterialTheme.typography.headlineMedium,
                    color = SideBySideTheme.colors.textPrimary,
                    modifier = Modifier.semantics { heading() },
                )
                Text(
                    text = stringResource(R.string.invitations_intro),
                    style = MaterialTheme.typography.bodyMedium,
                    color = SideBySideTheme.colors.textSecondary,
                    modifier = Modifier.widthIn(max = ReadingMeasure),
                )
            }
        }

        problem?.let { item { UiStatePanel(problem = it) } }

        item {
            Button(
                onClick = onCreate,
                enabled = !busy,
                modifier = Modifier.heightIn(min = MinimumTouchTarget),
            ) {
                Text(stringResource(R.string.invitation_create))
            }
        }

        if (invitations.isEmpty() && !busy) {
            item {
                Text(
                    text = stringResource(R.string.invitations_empty),
                    style = MaterialTheme.typography.bodyMedium,
                    color = SideBySideTheme.colors.textSecondary,
                    modifier = Modifier.widthIn(max = ReadingMeasure),
                )
            }
        }

        items(count = invitations.size, key = { index -> invitations[index].id.toString() }) { index ->
            val invitation = invitations[index]
            Surface(
                shape = RoundedCornerShape(SideBySideTheme.radii.card),
                color = SideBySideTheme.colors.surface,
                modifier = Modifier.fillMaxWidth(),
            ) {
                Column(
                    modifier = Modifier.padding(SideBySideTheme.spacing.cardPadding),
                    verticalArrangement = Arrangement.spacedBy(SideBySideTheme.spacing.step2),
                ) {
                    Text(
                        text = stringResource(
                            R.string.invitation_expires,
                            invitation.expiresAt.toLocalDate().format(dateFormat),
                        ),
                        style = MaterialTheme.typography.bodyMedium,
                        color = SideBySideTheme.colors.textPrimary,
                    )
                    TextButton(
                        onClick = { onRevoke(invitation.id) },
                        enabled = !busy,
                        modifier = Modifier.heightIn(min = MinimumTouchTarget),
                    ) {
                        Text(stringResource(R.string.invitation_revoke))
                    }
                }
            }
        }
    }

    issuedToken?.let { token ->
        val shareText = stringResource(R.string.invitation_share_text, token)
        AlertDialog(
            onDismissRequest = onDismissToken,
            title = { Text(stringResource(R.string.invitation_create)) },
            text = {
                Column(verticalArrangement = Arrangement.spacedBy(SideBySideTheme.spacing.step2)) {
                    Text(token, style = MaterialTheme.typography.titleMedium)
                    Text(
                        stringResource(R.string.invitation_token_notice),
                        style = MaterialTheme.typography.bodySmall,
                        color = SideBySideTheme.colors.textSecondary,
                    )
                }
            },
            confirmButton = {
                TextButton(
                    onClick = {
                        val send = Intent(Intent.ACTION_SEND).apply {
                            type = "text/plain"
                            putExtra(Intent.EXTRA_TEXT, shareText)
                        }
                        context.startActivity(Intent.createChooser(send, null))
                        onDismissToken()
                    },
                ) {
                    Text(stringResource(R.string.invitation_share))
                }
            },
            dismissButton = {
                TextButton(onClick = onDismissToken) {
                    Text(stringResource(R.string.memory_cancel))
                }
            },
        )
    }
}
