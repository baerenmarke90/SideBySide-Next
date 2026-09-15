package de.eimir.app.profile

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.heightIn
import androidx.compose.material3.Button
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedButton
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Modifier
import androidx.compose.ui.res.stringResource
import androidx.compose.ui.semantics.LiveRegionMode
import androidx.compose.ui.semantics.heading
import androidx.compose.ui.semantics.liveRegion
import androidx.compose.ui.semantics.semantics
import de.eimir.app.design.MinimumTouchTarget
import de.eimir.app.design.EimirDisplayFamily
import de.eimir.app.design.EimirTheme
import de.eimir.app.reference.R
import de.eimir.app.reference.UiMessage

/** Personal settings rendered inside the existing More destination. */
@Composable
fun ProfileSettingsContent(
    state: ProfileUiState,
    onRetry: () -> Unit,
    onSaveDisplayName: (String) -> Unit,
    onChooseAvatar: () -> Unit,
    onRemoveAvatar: () -> Unit,
    modifier: Modifier = Modifier,
) {
    val self = state.self
    var displayName by remember(self?.displayName) {
        mutableStateOf(self?.displayName.orEmpty())
    }

    Column(
        modifier = modifier.fillMaxWidth(),
        verticalArrangement = Arrangement.spacedBy(EimirTheme.spacing.step4),
    ) {
        Column(verticalArrangement = Arrangement.spacedBy(EimirTheme.spacing.step2)) {
            Text(
                text = stringResource(R.string.profile_settings_title),
                style = MaterialTheme.typography.labelSmall,
                color = EimirTheme.colors.brandStrong,
            )
            // The person's own name is the identity headline, not a generic
            // "Profil" label; the eyebrow above still carries that word for
            // orientation. While loading or on error there is no name yet, so
            // the generic label keeps the heading role.
            Text(
                text = self?.displayName?.takeIf { it.isNotBlank() }
                    ?: stringResource(R.string.profile_settings_title),
                style = MaterialTheme.typography.headlineSmall.copy(fontFamily = EimirDisplayFamily),
                color = EimirTheme.colors.textPrimary,
                modifier = Modifier.semantics { heading() },
            )
            Text(
                text = stringResource(R.string.profile_settings_intro),
                style = MaterialTheme.typography.bodyMedium,
                color = EimirTheme.colors.textSecondary,
            )
        }

        if (self == null) {
            Text(
                text = stringResource(
                    if (state.loading) {
                        R.string.profile_settings_loading
                    } else {
                        R.string.profile_loading_failed
                    },
                ),
                color = if (state.error != null) {
                    MaterialTheme.colorScheme.error
                } else {
                    EimirTheme.colors.textSecondary
                },
            )
            if (!state.loading) {
                OutlinedButton(
                    onClick = onRetry,
                    enabled = !state.busy,
                    modifier = Modifier.heightIn(min = MinimumTouchTarget),
                ) {
                    Text(stringResource(R.string.profile_settings_retry))
                }
            }
        } else {
            Column(verticalArrangement = Arrangement.spacedBy(EimirTheme.spacing.step3)) {
                Text(
                    text = stringResource(R.string.profile_preview_label),
                    style = MaterialTheme.typography.labelMedium,
                    color = EimirTheme.colors.textSecondary,
                )
                PersonIdentity(
                    displayName = self.displayName,
                    avatarBytes = state.selfAvatarBytes,
                    contentDescription = stringResource(
                        R.string.profile_avatar_description,
                        self.displayName,
                    ),
                    size = PersonIdentitySize.LARGE,
                )
            }

            OutlinedTextField(
                value = displayName,
                onValueChange = { displayName = it.take(120) },
                label = { Text(stringResource(R.string.profile_display_name_label)) },
                supportingText = { Text(stringResource(R.string.profile_display_name_help)) },
                singleLine = true,
                enabled = !state.busy,
                modifier = Modifier.fillMaxWidth(),
            )
            Button(
                onClick = { onSaveDisplayName(displayName) },
                enabled = !state.busy && displayName.isNotBlank(),
                modifier = Modifier.heightIn(min = MinimumTouchTarget),
            ) {
                Text(stringResource(R.string.profile_display_name_save))
            }

            Column(verticalArrangement = Arrangement.spacedBy(EimirTheme.spacing.step2)) {
                Text(
                    text = stringResource(R.string.profile_avatar_title),
                    style = MaterialTheme.typography.titleMedium,
                    color = EimirTheme.colors.textPrimary,
                )
                Text(
                    text = stringResource(R.string.profile_avatar_help),
                    style = MaterialTheme.typography.bodyMedium,
                    color = EimirTheme.colors.textSecondary,
                )
                Row(horizontalArrangement = Arrangement.spacedBy(EimirTheme.spacing.step3)) {
                    OutlinedButton(
                        onClick = onChooseAvatar,
                        enabled = !state.busy,
                        modifier = Modifier.heightIn(min = MinimumTouchTarget),
                    ) {
                        Text(stringResource(R.string.profile_avatar_choose))
                    }
                    if (self.profileAttachmentId != null) {
                        OutlinedButton(
                            onClick = onRemoveAvatar,
                            enabled = !state.busy,
                            modifier = Modifier.heightIn(min = MinimumTouchTarget),
                        ) {
                            Text(stringResource(R.string.profile_avatar_remove))
                        }
                    }
                }
            }

            state.partner?.let { partner ->
                Column(verticalArrangement = Arrangement.spacedBy(EimirTheme.spacing.step2)) {
                    Text(
                        text = stringResource(R.string.profile_partner_title),
                        style = MaterialTheme.typography.titleMedium,
                        color = EimirTheme.colors.textPrimary,
                        modifier = Modifier.semantics { heading() },
                    )
                    Text(
                        text = stringResource(R.string.profile_partner_intro),
                        style = MaterialTheme.typography.bodyMedium,
                        color = EimirTheme.colors.textSecondary,
                    )
                    PersonIdentity(
                        displayName = partner.displayName,
                        avatarBytes = state.partnerAvatarBytes,
                        contentDescription = stringResource(
                            R.string.profile_avatar_description,
                            partner.displayName,
                        ),
                        size = PersonIdentitySize.MEDIUM,
                    )
                }
            }
        }

        state.status?.let { message ->
            Text(
                text = message.resolve(),
                color = EimirTheme.colors.textSecondary,
                modifier = Modifier.semantics { liveRegion = LiveRegionMode.Polite },
            )
        }
        state.error?.let { message ->
            Text(
                text = message.resolve(),
                color = MaterialTheme.colorScheme.error,
                modifier = Modifier.semantics { liveRegion = LiveRegionMode.Assertive },
            )
        }
    }
}

@Composable
private fun UiMessage.resolve(): String = stringResource(resourceId, *args.toTypedArray())
