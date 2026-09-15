package de.eimir.app.transfer

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.PaddingValues
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.heightIn
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.widthIn
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.Button
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Surface
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.runtime.Composable
import androidx.compose.ui.Modifier
import androidx.compose.ui.res.stringResource
import androidx.compose.ui.semantics.heading
import androidx.compose.ui.semantics.semantics
import androidx.compose.ui.unit.Dp
import androidx.compose.ui.unit.dp
import de.eimir.app.design.EimirDisplayFamily
import de.eimir.app.design.MinimumTouchTarget
import de.eimir.app.design.EimirTheme
import de.eimir.app.reference.R
import de.eimir.app.shell.UiProblem
import de.eimir.app.shell.UiStatePanel
import eimir.api.models.ImportStatus
import eimir.api.models.TransferImportDetail

private val ReadingMeasure: Dp = 560.dp

/**
 * The M2-D17/S6 Transfer Bundle import.
 *
 * Explicit two-step behavior per the M2-D18 contract: staging an archive
 * only validates it — the validated [TransferImportDetail.summary] must be
 * shown before [onApplyImport] is ever offered, and apply itself is the
 * user's own separate tap, never automatic once validation finishes.
 */
@Composable
fun DataImportScreen(
    import: TransferImportDetail?,
    busy: Boolean,
    problem: UiProblem?,
    onBack: () -> Unit,
    onPickArchive: () -> Unit,
    onRefreshImport: () -> Unit,
    onApplyImport: () -> Unit,
    onStartOver: () -> Unit,
    modifier: Modifier = Modifier,
) {
    LazyColumn(
        modifier = modifier.fillMaxWidth(),
        contentPadding = PaddingValues(EimirTheme.spacing.pageMargin),
        verticalArrangement = Arrangement.spacedBy(EimirTheme.spacing.step5),
    ) {
        item {
            TextButton(onClick = onBack) { Text(stringResource(R.string.memory_back)) }
        }

        item {
            Column(verticalArrangement = Arrangement.spacedBy(EimirTheme.spacing.step2)) {
                Text(
                    text = stringResource(R.string.data_import_title),
                    style = MaterialTheme.typography.headlineMedium.copy(fontFamily = EimirDisplayFamily),
                    color = EimirTheme.colors.textPrimary,
                    modifier = Modifier.semantics { heading() },
                )
                Text(
                    text = stringResource(R.string.data_import_intro),
                    style = MaterialTheme.typography.bodyMedium,
                    color = EimirTheme.colors.textSecondary,
                    modifier = Modifier.widthIn(max = ReadingMeasure),
                )
            }
        }

        problem?.let { item { UiStatePanel(problem = it) } }

        if (import == null) {
            item {
                Surface(
                    shape = RoundedCornerShape(EimirTheme.radii.card),
                    color = EimirTheme.colors.surface,
                    modifier = Modifier.fillMaxWidth(),
                ) {
                    Column(
                        modifier = Modifier.padding(EimirTheme.spacing.cardPadding),
                        verticalArrangement = Arrangement.spacedBy(EimirTheme.spacing.step3),
                    ) {
                        Button(
                            onClick = onPickArchive,
                            enabled = !busy,
                            modifier = Modifier.heightIn(min = MinimumTouchTarget),
                        ) {
                            Text(stringResource(R.string.data_import_pick_archive))
                        }
                    }
                }
            }
        } else {
            item {
                Surface(
                    shape = RoundedCornerShape(EimirTheme.radii.card),
                    color = EimirTheme.colors.surface,
                    modifier = Modifier.fillMaxWidth(),
                ) {
                    Column(
                        modifier = Modifier.padding(EimirTheme.spacing.cardPadding),
                        verticalArrangement = Arrangement.spacedBy(EimirTheme.spacing.step3),
                    ) {
                        Text(
                            text = stringResource(import.status.labelRes()),
                            style = MaterialTheme.typography.titleMedium,
                            color = EimirTheme.colors.textPrimary,
                        )
                        import.summary?.let { summary ->
                            Text(
                                text = stringResource(
                                    R.string.data_import_summary,
                                    summary.recordCounts.values.sum(),
                                    summary.mediaCount,
                                    summary.sourceMemberCount,
                                ),
                                style = MaterialTheme.typography.bodyMedium,
                                color = EimirTheme.colors.textSecondary,
                            )
                        }
                        Row(horizontalArrangement = Arrangement.spacedBy(EimirTheme.spacing.step3)) {
                            if (import.status == ImportStatus.QUEUED ||
                                import.status == ImportStatus.VALIDATING ||
                                import.status == ImportStatus.APPLYING
                            ) {
                                TextButton(
                                    onClick = onRefreshImport,
                                    enabled = !busy,
                                    modifier = Modifier.heightIn(min = MinimumTouchTarget),
                                ) {
                                    Text(stringResource(R.string.data_import_refresh))
                                }
                            }
                            if (import.status == ImportStatus.READY_TO_APPLY) {
                                Button(
                                    onClick = onApplyImport,
                                    enabled = !busy,
                                    modifier = Modifier.heightIn(min = MinimumTouchTarget),
                                ) {
                                    Text(stringResource(R.string.data_import_apply))
                                }
                            }
                            if (import.status == ImportStatus.COMPLETED ||
                                import.status == ImportStatus.FAILED ||
                                import.status == ImportStatus.EXPIRED
                            ) {
                                TextButton(
                                    onClick = onStartOver,
                                    enabled = !busy,
                                    modifier = Modifier.heightIn(min = MinimumTouchTarget),
                                ) {
                                    Text(stringResource(R.string.data_import_start_over))
                                }
                            }
                        }
                    }
                }
            }
        }
    }
}

private fun ImportStatus.labelRes(): Int = when (this) {
    ImportStatus.QUEUED -> R.string.data_import_status_queued
    ImportStatus.VALIDATING -> R.string.data_import_status_validating
    ImportStatus.READY_TO_APPLY -> R.string.data_import_status_ready_to_apply
    ImportStatus.APPLYING -> R.string.data_import_status_applying
    ImportStatus.COMPLETED -> R.string.data_import_status_completed
    ImportStatus.FAILED -> R.string.data_import_status_failed
    ImportStatus.EXPIRED -> R.string.data_import_status_expired
}
