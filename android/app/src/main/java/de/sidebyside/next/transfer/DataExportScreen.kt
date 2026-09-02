package de.sidebyside.next.transfer

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.heightIn
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.widthIn
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.selection.selectable
import androidx.compose.foundation.selection.selectableGroup
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.Button
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.RadioButton
import androidx.compose.material3.Surface
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.runtime.Composable
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
import de.sidebyside.next.design.FrauncesFamily
import de.sidebyside.next.design.MinimumTouchTarget
import de.sidebyside.next.design.SideBySideTheme
import de.sidebyside.next.reference.R
import de.sidebyside.next.shell.UiProblem
import de.sidebyside.next.shell.UiStatePanel
import sidebyside.api.models.ExportStatus
import sidebyside.api.models.TransferExportDetail
import sidebyside.api.models.TransferScope

private val ReadingMeasure: Dp = 560.dp

/**
 * The M2-D17/S6 Transfer Bundle export.
 *
 * Assembly runs as a background job on the server — this screen starts one,
 * shows its status, and offers a download once it says `READY`. There is no
 * automatic polling: M2-D18's "no fragile implicit sync queue" boundary
 * applies here too, so refreshing status is the user's own explicit action,
 * the same as every other manual-refresh surface in this client.
 */
@Composable
fun DataExportScreen(
    export: TransferExportDetail?,
    busy: Boolean,
    problem: UiProblem?,
    downloaded: Boolean,
    onBack: () -> Unit,
    onCreateExport: (TransferScope) -> Unit,
    onRefreshExport: () -> Unit,
    onDownloadExport: () -> Unit,
    modifier: Modifier = Modifier,
) {
    var scope by rememberSaveable { mutableStateOf(TransferScope.SHARED) }

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
                    text = stringResource(R.string.data_export_title),
                    style = MaterialTheme.typography.headlineMedium.copy(fontFamily = FrauncesFamily),
                    color = SideBySideTheme.colors.textPrimary,
                    modifier = Modifier.semantics { heading() },
                )
                Text(
                    text = stringResource(R.string.data_export_intro),
                    style = MaterialTheme.typography.bodyMedium,
                    color = SideBySideTheme.colors.textSecondary,
                    modifier = Modifier.widthIn(max = ReadingMeasure),
                )
            }
        }

        problem?.let { item { UiStatePanel(problem = it) } }

        if (export == null) {
            item {
                Surface(
                    shape = RoundedCornerShape(SideBySideTheme.radii.card),
                    color = SideBySideTheme.colors.surface,
                    modifier = Modifier.fillMaxWidth(),
                ) {
                    Column(
                        modifier = Modifier.padding(SideBySideTheme.spacing.cardPadding),
                        verticalArrangement = Arrangement.spacedBy(SideBySideTheme.spacing.step3),
                    ) {
                        Column(Modifier.selectableGroup()) {
                            ScopeChoice(
                                selected = scope == TransferScope.SHARED,
                                labelRes = R.string.data_export_scope_shared,
                                enabled = !busy,
                                onClick = { scope = TransferScope.SHARED },
                            )
                            ScopeChoice(
                                selected = scope == TransferScope.PERSONAL,
                                labelRes = R.string.data_export_scope_personal,
                                enabled = !busy,
                                onClick = { scope = TransferScope.PERSONAL },
                            )
                        }
                        Button(
                            onClick = { onCreateExport(scope) },
                            enabled = !busy,
                            modifier = Modifier.heightIn(min = MinimumTouchTarget),
                        ) {
                            Text(stringResource(R.string.data_export_start))
                        }
                    }
                }
            }
        } else {
            item {
                Surface(
                    shape = RoundedCornerShape(SideBySideTheme.radii.card),
                    color = SideBySideTheme.colors.surface,
                    modifier = Modifier.fillMaxWidth(),
                ) {
                    Column(
                        modifier = Modifier.padding(SideBySideTheme.spacing.cardPadding),
                        verticalArrangement = Arrangement.spacedBy(SideBySideTheme.spacing.step3),
                    ) {
                        Text(
                            text = stringResource(export.status.labelRes()),
                            style = MaterialTheme.typography.titleMedium,
                            color = SideBySideTheme.colors.textPrimary,
                        )
                        if (downloaded) {
                            Text(
                                text = stringResource(R.string.data_export_downloaded),
                                style = MaterialTheme.typography.bodyMedium,
                                color = SideBySideTheme.colors.success,
                            )
                        }
                        Row(horizontalArrangement = Arrangement.spacedBy(SideBySideTheme.spacing.step3)) {
                            if (export.status != ExportStatus.READY) {
                                TextButton(
                                    onClick = onRefreshExport,
                                    enabled = !busy,
                                    modifier = Modifier.heightIn(min = MinimumTouchTarget),
                                ) {
                                    Text(stringResource(R.string.data_export_refresh))
                                }
                            }
                            if (export.status == ExportStatus.READY) {
                                Button(
                                    onClick = onDownloadExport,
                                    enabled = !busy,
                                    modifier = Modifier.heightIn(min = MinimumTouchTarget),
                                ) {
                                    Text(stringResource(R.string.data_export_download))
                                }
                            }
                        }
                    }
                }
            }
        }
    }
}

@Composable
private fun ScopeChoice(selected: Boolean, labelRes: Int, enabled: Boolean, onClick: () -> Unit) {
    Row(
        modifier = Modifier
            .fillMaxWidth()
            .heightIn(min = MinimumTouchTarget)
            .selectable(selected = selected, enabled = enabled, role = Role.RadioButton, onClick = onClick),
        verticalAlignment = Alignment.CenterVertically,
    ) {
        RadioButton(selected = selected, onClick = null, enabled = enabled)
        Text(
            text = stringResource(labelRes),
            style = MaterialTheme.typography.bodyLarge,
            color = SideBySideTheme.colors.textPrimary,
            modifier = Modifier.padding(start = SideBySideTheme.spacing.step3),
        )
    }
}

private fun ExportStatus.labelRes(): Int = when (this) {
    ExportStatus.QUEUED -> R.string.data_export_status_queued
    ExportStatus.RUNNING -> R.string.data_export_status_running
    ExportStatus.READY -> R.string.data_export_status_ready
    ExportStatus.FAILED -> R.string.data_export_status_failed
    ExportStatus.EXPIRED -> R.string.data_export_status_expired
}
