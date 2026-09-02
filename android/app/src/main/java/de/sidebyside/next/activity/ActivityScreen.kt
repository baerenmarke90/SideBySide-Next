package de.sidebyside.next.activity

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.PaddingValues
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.widthIn
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.shape.RoundedCornerShape
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
import de.sidebyside.next.design.FrauncesFamily
import de.sidebyside.next.design.SideBySideTheme
import de.sidebyside.next.reference.R
import de.sidebyside.next.shell.UiProblem
import de.sidebyside.next.shell.UiStatePanel
import sidebyside.api.models.ActivityItem
import sidebyside.api.models.ActivityKind

private val ReadingMeasure: Dp = 560.dp

/**
 * The couple's shared Activity feed. Read-only per #357: an entry links to
 * nothing yet, the same deliberate scope boundary as Notifications — no
 * per-[sidebyside.api.models.EngagementTarget]-kind navigation resolver
 * exists on Android yet, so this shows what happened without pretending it
 * can open it.
 */
@Composable
fun ActivityScreen(
    entries: List<ActivityItem>,
    busy: Boolean,
    problem: UiProblem?,
    onBack: () -> Unit,
    modifier: Modifier = Modifier,
) {
    LazyColumn(
        modifier = modifier.fillMaxWidth(),
        contentPadding = PaddingValues(SideBySideTheme.spacing.pageMargin),
        verticalArrangement = Arrangement.spacedBy(SideBySideTheme.spacing.step5),
    ) {
        item {
            TextButton(onClick = onBack) { Text(stringResource(R.string.memory_back)) }
        }

        item {
            Column(verticalArrangement = Arrangement.spacedBy(SideBySideTheme.spacing.step2)) {
                Text(
                    text = stringResource(R.string.activity_title),
                    style = MaterialTheme.typography.headlineMedium.copy(fontFamily = FrauncesFamily),
                    color = SideBySideTheme.colors.textPrimary,
                    modifier = Modifier.semantics { heading() },
                )
                Text(
                    text = stringResource(R.string.activity_intro),
                    style = MaterialTheme.typography.bodyMedium,
                    color = SideBySideTheme.colors.textSecondary,
                    modifier = Modifier.widthIn(max = ReadingMeasure),
                )
            }
        }

        problem?.let { item { UiStatePanel(problem = it) } }

        if (entries.isEmpty() && !busy) {
            item {
                Text(
                    text = stringResource(R.string.activity_empty),
                    style = MaterialTheme.typography.bodyMedium,
                    color = SideBySideTheme.colors.textSecondary,
                )
            }
        }

        items(count = entries.size, key = { index -> entries[index].id.toString() }) { index ->
            val entry = entries[index]
            Surface(
                shape = RoundedCornerShape(SideBySideTheme.radii.card),
                color = SideBySideTheme.colors.surface,
                modifier = Modifier.fillMaxWidth(),
            ) {
                Text(
                    text = stringResource(entry.kind.labelRes()),
                    style = MaterialTheme.typography.bodyLarge,
                    color = SideBySideTheme.colors.textPrimary,
                    modifier = Modifier.padding(SideBySideTheme.spacing.cardPadding),
                )
            }
        }
    }
}

private fun ActivityKind.labelRes(): Int = when (this) {
    ActivityKind.MEMORY_CREATED -> R.string.activity_kind_memory_created
    ActivityKind.MILESTONE_CREATED -> R.string.activity_kind_milestone_created
    ActivityKind.HEART_MOMENT_CREATED -> R.string.activity_kind_heart_moment_created
    ActivityKind.WISH_CREATED -> R.string.activity_kind_wish_created
    ActivityKind.PLAN_CREATED -> R.string.activity_kind_plan_created
    ActivityKind.PLAN_COMPLETED -> R.string.activity_kind_plan_completed
    ActivityKind.PLACE_CREATED -> R.string.activity_kind_place_created
    ActivityKind.CHAPTER_CREATED -> R.string.activity_kind_chapter_created
    ActivityKind.COLLECTION_CREATED -> R.string.activity_kind_collection_created
    ActivityKind.COMMENT_CREATED -> R.string.activity_kind_comment_created
}
