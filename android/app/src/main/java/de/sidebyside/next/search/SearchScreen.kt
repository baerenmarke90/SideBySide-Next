package de.sidebyside.next.search

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.PaddingValues
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.heightIn
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.widthIn
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.Button
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.Surface
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
import de.sidebyside.next.design.FrauncesFamily
import de.sidebyside.next.design.MinimumTouchTarget
import de.sidebyside.next.design.SideBySideTheme
import de.sidebyside.next.reference.R
import de.sidebyside.next.shell.UiProblem
import de.sidebyside.next.shell.UiStatePanel
import sidebyside.api.models.SearchKind
import sidebyside.api.models.SearchResult

private val ReadingMeasure: Dp = 560.dp

/**
 * Global Search. #357 scopes this to a query and a flat result list — the
 * server already restricts results to shared Space content plus the
 * caller's own private content, so nothing here needs a scope filter to
 * stay correct; a type filter is left for later since the query alone
 * already satisfies the slice.
 */
@Composable
fun SearchScreen(
    results: List<SearchResult>,
    busy: Boolean,
    problem: UiProblem?,
    onBack: () -> Unit,
    onSearch: (String) -> Unit,
    modifier: Modifier = Modifier,
) {
    var query by rememberSaveable { mutableStateOf("") }
    var submitted by rememberSaveable { mutableStateOf(false) }

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
                    text = stringResource(R.string.search_title),
                    style = MaterialTheme.typography.headlineMedium.copy(fontFamily = FrauncesFamily),
                    color = SideBySideTheme.colors.textPrimary,
                    modifier = Modifier.semantics { heading() },
                )
                Text(
                    text = stringResource(R.string.search_intro),
                    style = MaterialTheme.typography.bodyMedium,
                    color = SideBySideTheme.colors.textSecondary,
                    modifier = Modifier.widthIn(max = ReadingMeasure),
                )
            }
        }

        item {
            Column(verticalArrangement = Arrangement.spacedBy(SideBySideTheme.spacing.step3)) {
                OutlinedTextField(
                    value = query,
                    onValueChange = { query = it },
                    label = { Text(stringResource(R.string.search_query_hint)) },
                    singleLine = true,
                    enabled = !busy,
                    modifier = Modifier.fillMaxWidth(),
                )
                Button(
                    onClick = {
                        submitted = true
                        onSearch(query)
                    },
                    enabled = !busy && query.isNotBlank(),
                    modifier = Modifier.heightIn(min = MinimumTouchTarget),
                ) {
                    Text(stringResource(R.string.search_submit))
                }
            }
        }

        problem?.let { item { UiStatePanel(problem = it) } }

        if (submitted && results.isEmpty() && !busy) {
            item {
                Text(
                    text = stringResource(R.string.search_empty),
                    style = MaterialTheme.typography.bodyMedium,
                    color = SideBySideTheme.colors.textSecondary,
                )
            }
        }

        items(count = results.size, key = { index -> results[index].id.toString() }) { index ->
            val result = results[index]
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
                        text = result.title?.takeIf { it.isNotBlank() } ?: stringResource(R.string.search_result_untitled),
                        style = MaterialTheme.typography.titleMedium,
                        color = SideBySideTheme.colors.textPrimary,
                    )
                    Text(
                        text = stringResource(result.type.labelRes()),
                        style = MaterialTheme.typography.labelMedium,
                        color = SideBySideTheme.colors.brandStrong,
                    )
                    result.excerpt?.takeIf { it.isNotBlank() }?.let {
                        Text(
                            text = it,
                            style = MaterialTheme.typography.bodyMedium,
                            color = SideBySideTheme.colors.textSecondary,
                        )
                    }
                }
            }
        }
    }
}

private fun SearchKind.labelRes(): Int = when (this) {
    SearchKind.MEMORY -> R.string.search_result_kind_memory
    SearchKind.HEART_MOMENT -> R.string.search_result_kind_heart_moment
    SearchKind.MILESTONE -> R.string.search_result_kind_milestone
    SearchKind.WISH -> R.string.search_result_kind_wish
    SearchKind.PLAN -> R.string.search_result_kind_plan
    SearchKind.PLACE -> R.string.search_result_kind_place
    SearchKind.CHAPTER -> R.string.search_result_kind_chapter
    SearchKind.COLLECTION -> R.string.search_result_kind_collection
    SearchKind.COLLECTION_ITEM -> R.string.search_result_kind_collection_item
    SearchKind.PRIVATE_NOTE -> R.string.search_result_kind_private_note
    SearchKind.GIFT_IDEA -> R.string.search_result_kind_gift_idea
    SearchKind.PRIVATE_COLLECTION -> R.string.search_result_kind_private_collection
    SearchKind.PRIVATE_COLLECTION_ITEM -> R.string.search_result_kind_private_collection_item
}
