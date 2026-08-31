package de.sidebyside.next.demo

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Surface
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.res.stringResource
import androidx.compose.ui.semantics.LiveRegionMode
import androidx.compose.ui.semantics.liveRegion
import androidx.compose.ui.semantics.semantics
import de.sidebyside.next.design.SideBySideTheme
import de.sidebyside.next.reference.R

/**
 * Says that the current session is the public demo.
 *
 * The state is carried by the text, not by the colour, so it survives a
 * colour-blind reading and a screen reader. It is announced politely once when
 * it appears, because entering the demo is a context change the user should
 * hear confirmed.
 */
@Composable
fun DemoBanner(
    persona: DemoPersona,
    onLeave: () -> Unit,
    modifier: Modifier = Modifier,
) {
    Surface(
        modifier = modifier
            .fillMaxWidth()
            .semantics { liveRegion = LiveRegionMode.Polite },
        color = SideBySideTheme.colors.discoverySurface,
    ) {
        Row(
            modifier = Modifier.padding(
                horizontal = SideBySideTheme.spacing.step4,
                vertical = SideBySideTheme.spacing.step2,
            ),
            verticalAlignment = Alignment.CenterVertically,
            horizontalArrangement = Arrangement.SpaceBetween,
        ) {
            Text(
                text = stringResource(
                    R.string.demo_banner,
                    stringResource(
                        when (persona) {
                            DemoPersona.Lea -> R.string.demo_persona_lea
                            DemoPersona.Alex -> R.string.demo_persona_alex
                        },
                    ),
                ),
                style = MaterialTheme.typography.bodySmall,
                color = SideBySideTheme.colors.textPrimary,
            )
            TextButton(onClick = onLeave) {
                Text(stringResource(R.string.demo_leave))
            }
        }
    }
}
