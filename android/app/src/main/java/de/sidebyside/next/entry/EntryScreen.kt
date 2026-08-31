package de.sidebyside.next.entry

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.heightIn
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.widthIn
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.text.KeyboardActions
import androidx.compose.foundation.text.KeyboardOptions
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.Button
import androidx.compose.material3.HorizontalDivider
import androidx.compose.material3.OutlinedButton
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.Surface
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.saveable.rememberSaveable
import androidx.compose.runtime.setValue
import androidx.compose.ui.Modifier
import androidx.compose.ui.res.stringResource
import androidx.compose.ui.semantics.LiveRegionMode
import androidx.compose.ui.semantics.heading
import androidx.compose.ui.semantics.liveRegion
import androidx.compose.ui.semantics.semantics
import androidx.compose.ui.text.input.ImeAction
import androidx.compose.ui.text.input.KeyboardType
import androidx.compose.ui.text.input.PasswordVisualTransformation
import de.sidebyside.next.demo.DemoPersona
import de.sidebyside.next.design.BrandLockup
import de.sidebyside.next.design.MinimumTouchTarget
import de.sidebyside.next.design.SideBySideTheme
import androidx.compose.ui.unit.Dp
import de.sidebyside.next.reference.R

/**
 * The product entry surface.
 *
 * This is what someone sees before they are signed in, so it says what the
 * product is for rather than which engineering slice is running. Real session
 * handling, recovery paths and Space context belong to S1; this slice owns the
 * surface, its copy and its accessibility.
 */
@Composable
fun EntryScreen(
    onSignIn: (String, String) -> Unit,
    busy: Boolean,
    modifier: Modifier = Modifier,
    notice: String? = null,
    signInEnabled: Boolean = true,
    onEnterDemo: ((DemoPersona) -> Unit)? = null,
) {
    // The email survives configuration change; the password deliberately does
    // not, because saved instance state is written to disk by the system.
    var email by rememberSaveable { mutableStateOf("") }
    var password by remember { mutableStateOf("") }

    val canSubmit = signInEnabled && !busy && email.isNotBlank() && password.isNotBlank()
    fun submit() {
        if (canSubmit) onSignIn(email, password)
    }

    Column(
        modifier = modifier
            .fillMaxWidth()
            .verticalScroll(rememberScrollState())
            .padding(SideBySideTheme.spacing.pageMargin),
        verticalArrangement = Arrangement.spacedBy(SideBySideTheme.spacing.step6),
    ) {
        BrandLockup()

        Column(verticalArrangement = Arrangement.spacedBy(SideBySideTheme.spacing.step3)) {
            Text(
                text = stringResource(R.string.entry_eyebrow),
                style = MaterialTheme.typography.labelSmall,
                color = SideBySideTheme.colors.brandStrong,
            )
            Text(
                text = stringResource(R.string.entry_headline),
                style = MaterialTheme.typography.headlineMedium,
                color = MaterialTheme.colorScheme.onBackground,
                modifier = Modifier.semantics { heading() },
            )
            Text(
                text = stringResource(R.string.entry_lede),
                style = MaterialTheme.typography.bodyLarge,
                color = SideBySideTheme.colors.textSecondary,
                modifier = Modifier.widthIn(max = ReadingMeasure),
            )
        }

        if (notice != null) {
            Surface(
                shape = MaterialTheme.shapes.medium,
                color = SideBySideTheme.colors.warningSurface,
                modifier = Modifier.fillMaxWidth(),
            ) {
                Text(
                    text = notice,
                    style = MaterialTheme.typography.bodyMedium,
                    color = SideBySideTheme.colors.textPrimary,
                    modifier = Modifier
                        .padding(SideBySideTheme.spacing.step4)
                        .semantics { liveRegion = LiveRegionMode.Assertive },
                )
            }
        }

        Column(verticalArrangement = Arrangement.spacedBy(SideBySideTheme.spacing.step3)) {
            Text(
                text = stringResource(R.string.entry_sign_in_heading),
                style = MaterialTheme.typography.titleMedium,
                color = MaterialTheme.colorScheme.onBackground,
                modifier = Modifier.semantics { heading() },
            )
            OutlinedTextField(
                value = email,
                onValueChange = { email = it },
                label = { Text(stringResource(R.string.entry_email)) },
                singleLine = true,
                enabled = signInEnabled && !busy,
                keyboardOptions = KeyboardOptions(
                    keyboardType = KeyboardType.Email,
                    imeAction = ImeAction.Next,
                ),
                modifier = Modifier.fillMaxWidth(),
            )
            OutlinedTextField(
                value = password,
                onValueChange = { password = it },
                label = { Text(stringResource(R.string.entry_password)) },
                singleLine = true,
                enabled = signInEnabled && !busy,
                visualTransformation = PasswordVisualTransformation(),
                keyboardOptions = KeyboardOptions(
                    keyboardType = KeyboardType.Password,
                    imeAction = ImeAction.Done,
                ),
                keyboardActions = KeyboardActions(onDone = { submit() }),
                modifier = Modifier.fillMaxWidth(),
            )
            Button(
                onClick = ::submit,
                enabled = canSubmit,
                modifier = Modifier
                    .fillMaxWidth()
                    .heightIn(min = MinimumTouchTarget),
            ) {
                Text(
                    stringResource(
                        if (busy) R.string.entry_sign_in_pending else R.string.entry_sign_in,
                    ),
                )
            }
        }

        if (onEnterDemo != null) {
            DemoEntrySection(onEnterDemo = onEnterDemo, busy = busy)
        }

        Text(
            text = stringResource(R.string.entry_assurance),
            style = MaterialTheme.typography.bodySmall,
            color = SideBySideTheme.colors.textMuted,
            modifier = Modifier.widthIn(max = ReadingMeasure),
        )
    }
}

/**
 * The way into the public demo.
 *
 * Kept visually secondary to sign-in: it is a way to look around, not the way
 * into your own Space. The personas are named because the demo content is
 * written from their point of view.
 */
@Composable
private fun DemoEntrySection(onEnterDemo: (DemoPersona) -> Unit, busy: Boolean) {
    Column(
        verticalArrangement = Arrangement.spacedBy(SideBySideTheme.spacing.step3),
    ) {
        HorizontalDivider(color = SideBySideTheme.colors.borderSubtle)
        Text(
            text = stringResource(R.string.demo_heading),
            style = MaterialTheme.typography.titleMedium,
            color = MaterialTheme.colorScheme.onBackground,
            modifier = Modifier.semantics { heading() },
        )
        Text(
            text = stringResource(R.string.demo_body),
            style = MaterialTheme.typography.bodyMedium,
            color = SideBySideTheme.colors.textSecondary,
            modifier = Modifier.widthIn(max = ReadingMeasure),
        )
        for (persona in DemoPersona.entries) {
            OutlinedButton(
                onClick = { onEnterDemo(persona) },
                enabled = !busy,
                modifier = Modifier
                    .fillMaxWidth()
                    .heightIn(min = MinimumTouchTarget),
            ) {
                Text(
                    stringResource(
                        when (persona) {
                            DemoPersona.Lea -> R.string.demo_join_as_lea
                            DemoPersona.Alex -> R.string.demo_join_as_alex
                        },
                    ),
                )
            }
        }
    }
}

/**
 * Reading measure for running text. `docs/DESIGN-PRINCIPLES.md` caps long-form
 * text at roughly 70 characters, which matters once the app runs on a tablet or
 * an unfolded device.
 */
private val ReadingMeasure = Dp(560f)
