package de.sidebyside.next.privatearea

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
import androidx.compose.material3.AlertDialog
import androidx.compose.material3.Button
import androidx.compose.material3.Checkbox
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
import androidx.compose.ui.Alignment
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
import sidebyside.api.models.GiftIdeaDetail
import sidebyside.api.models.GiftIdeaStatus

private val ReadingMeasure: Dp = 560.dp

/**
 * The account's own gift ideas. Owner-only per #356, same as
 * [PrivateNotesScreen]; status buttons only ever propose a target status —
 * M3-D17's transition graph is validated server-side, never re-encoded here.
 */
@Composable
fun GiftIdeasScreen(
    ideas: List<GiftIdeaDetail>,
    busy: Boolean,
    problem: UiProblem?,
    onBack: () -> Unit,
    onAdd: (
        title: String,
        description: String,
        occasion: String,
        recipient: String,
        priceText: String,
        url: String,
        targetOn: String,
        pinned: Boolean,
    ) -> Unit,
    onEdit: (
        idea: GiftIdeaDetail,
        title: String,
        description: String,
        occasion: String,
        recipient: String,
        priceText: String,
        url: String,
        targetOn: String,
        pinned: Boolean,
    ) -> Unit,
    onChangeStatus: (GiftIdeaDetail, GiftIdeaStatus) -> Unit,
    onDelete: (GiftIdeaDetail) -> Unit,
    modifier: Modifier = Modifier,
) {
    var editing by rememberSaveable { mutableStateOf<String?>(null) }
    var deleting by rememberSaveable { mutableStateOf<String?>(null) }

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
                    text = stringResource(R.string.gift_ideas_title),
                    style = MaterialTheme.typography.headlineMedium.copy(fontFamily = FrauncesFamily),
                    color = SideBySideTheme.colors.textPrimary,
                    modifier = Modifier.semantics { heading() },
                )
                Text(
                    text = stringResource(R.string.gift_ideas_intro),
                    style = MaterialTheme.typography.bodyMedium,
                    color = SideBySideTheme.colors.textSecondary,
                    modifier = Modifier.widthIn(max = ReadingMeasure),
                )
            }
        }

        problem?.let { item { UiStatePanel(problem = it) } }

        item {
            Surface(
                shape = RoundedCornerShape(SideBySideTheme.radii.card),
                color = SideBySideTheme.colors.surface,
                modifier = Modifier.fillMaxWidth(),
            ) {
                Column(modifier = Modifier.padding(SideBySideTheme.spacing.cardPadding)) {
                    GiftIdeaForm(
                        submitLabel = stringResource(R.string.gift_idea_add),
                        busy = busy,
                        onSubmit = onAdd,
                    )
                }
            }
        }

        if (ideas.isEmpty() && !busy) {
            item {
                Text(
                    text = stringResource(R.string.gift_ideas_empty),
                    style = MaterialTheme.typography.bodyMedium,
                    color = SideBySideTheme.colors.textSecondary,
                )
            }
        }

        items(count = ideas.size, key = { index -> ideas[index].id.toString() }) { index ->
            val idea = ideas[index]
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
                        text = idea.title,
                        style = MaterialTheme.typography.titleMedium,
                        color = SideBySideTheme.colors.textPrimary,
                    )
                    Text(
                        text = idea.status.labelRes().let { stringResource(it) },
                        style = MaterialTheme.typography.labelMedium,
                        color = SideBySideTheme.colors.brandStrong,
                    )
                    idea.recipient?.takeIf { it.isNotBlank() }?.let {
                        Text(
                            text = it,
                            style = MaterialTheme.typography.bodyMedium,
                            color = SideBySideTheme.colors.textSecondary,
                        )
                    }
                    idea.description?.takeIf { it.isNotBlank() }?.let {
                        Text(
                            text = it,
                            style = MaterialTheme.typography.bodyMedium,
                            color = SideBySideTheme.colors.textSecondary,
                        )
                    }

                    Row(horizontalArrangement = Arrangement.spacedBy(SideBySideTheme.spacing.step3)) {
                        for (target in GiftIdeaStatus.entries) {
                            if (target == idea.status) continue
                            TextButton(
                                onClick = { onChangeStatus(idea, target) },
                                enabled = !busy,
                                modifier = Modifier.heightIn(min = MinimumTouchTarget),
                            ) {
                                Text(stringResource(R.string.gift_idea_mark_as, stringResource(target.labelRes())))
                            }
                        }
                    }

                    Row(horizontalArrangement = Arrangement.spacedBy(SideBySideTheme.spacing.step3)) {
                        TextButton(
                            onClick = { editing = idea.id.toString() },
                            enabled = !busy,
                            modifier = Modifier.heightIn(min = MinimumTouchTarget),
                        ) {
                            Text(stringResource(R.string.gift_idea_edit))
                        }
                        TextButton(
                            onClick = { deleting = idea.id.toString() },
                            enabled = !busy,
                            modifier = Modifier.heightIn(min = MinimumTouchTarget),
                        ) {
                            Text(stringResource(R.string.gift_idea_delete))
                        }
                    }
                }
            }
        }
    }

    editing?.let { id ->
        val target = ideas.firstOrNull { it.id.toString() == id }
        if (target == null) {
            editing = null
            return@let
        }
        EditGiftIdeaDialog(
            idea = target,
            busy = busy,
            onDismiss = { editing = null },
            onSave = { title, description, occasion, recipient, priceText, url, targetOn, pinned ->
                editing = null
                onEdit(target, title, description, occasion, recipient, priceText, url, targetOn, pinned)
            },
        )
    }

    deleting?.let { id ->
        val target = ideas.firstOrNull { it.id.toString() == id }
        if (target == null) {
            deleting = null
            return@let
        }
        AlertDialog(
            onDismissRequest = { deleting = null },
            title = { Text(stringResource(R.string.gift_idea_delete_title, target.title)) },
            text = { Text(stringResource(R.string.gift_idea_delete_warning)) },
            confirmButton = {
                TextButton(
                    onClick = {
                        deleting = null
                        onDelete(target)
                    },
                ) {
                    Text(stringResource(R.string.gift_idea_delete_confirm))
                }
            },
            dismissButton = {
                TextButton(onClick = { deleting = null }) { Text(stringResource(R.string.gift_idea_cancel)) }
            },
        )
    }
}

@Composable
private fun GiftIdeaForm(
    submitLabel: String,
    busy: Boolean,
    initialTitle: String = "",
    initialDescription: String = "",
    initialOccasion: String = "",
    initialRecipient: String = "",
    initialPriceText: String = "",
    initialUrl: String = "",
    initialTargetOn: String = "",
    initialPinned: Boolean = false,
    onSubmit: (
        title: String,
        description: String,
        occasion: String,
        recipient: String,
        priceText: String,
        url: String,
        targetOn: String,
        pinned: Boolean,
    ) -> Unit,
) {
    var title by rememberSaveable { mutableStateOf(initialTitle) }
    var description by rememberSaveable { mutableStateOf(initialDescription) }
    var occasion by rememberSaveable { mutableStateOf(initialOccasion) }
    var recipient by rememberSaveable { mutableStateOf(initialRecipient) }
    var priceText by rememberSaveable { mutableStateOf(initialPriceText) }
    var url by rememberSaveable { mutableStateOf(initialUrl) }
    var targetOn by rememberSaveable { mutableStateOf(initialTargetOn) }
    var pinned by rememberSaveable { mutableStateOf(initialPinned) }

    Column(verticalArrangement = Arrangement.spacedBy(SideBySideTheme.spacing.step3)) {
        OutlinedTextField(
            value = title,
            onValueChange = { title = it.take(200) },
            label = { Text(stringResource(R.string.gift_idea_title_hint)) },
            enabled = !busy,
            modifier = Modifier.fillMaxWidth(),
        )
        OutlinedTextField(
            value = description,
            onValueChange = { description = it },
            label = { Text(stringResource(R.string.gift_idea_description_hint)) },
            enabled = !busy,
            modifier = Modifier.fillMaxWidth(),
        )
        OutlinedTextField(
            value = recipient,
            onValueChange = { recipient = it },
            label = { Text(stringResource(R.string.gift_idea_recipient_hint)) },
            enabled = !busy,
            modifier = Modifier.fillMaxWidth(),
        )
        OutlinedTextField(
            value = occasion,
            onValueChange = { occasion = it },
            label = { Text(stringResource(R.string.gift_idea_occasion_hint)) },
            enabled = !busy,
            modifier = Modifier.fillMaxWidth(),
        )
        OutlinedTextField(
            value = priceText,
            onValueChange = { priceText = it },
            label = { Text(stringResource(R.string.gift_idea_price_hint)) },
            enabled = !busy,
            modifier = Modifier.fillMaxWidth(),
        )
        OutlinedTextField(
            value = url,
            onValueChange = { url = it },
            label = { Text(stringResource(R.string.gift_idea_url_hint)) },
            singleLine = true,
            enabled = !busy,
            modifier = Modifier.fillMaxWidth(),
        )
        OutlinedTextField(
            value = targetOn,
            onValueChange = { targetOn = it },
            label = { Text(stringResource(R.string.gift_idea_target_on_hint)) },
            singleLine = true,
            enabled = !busy,
            modifier = Modifier.fillMaxWidth(),
        )
        Row(verticalAlignment = Alignment.CenterVertically) {
            Checkbox(checked = pinned, onCheckedChange = { pinned = it }, enabled = !busy)
            Text(
                text = stringResource(R.string.gift_idea_pinned),
                style = MaterialTheme.typography.bodyMedium,
                color = SideBySideTheme.colors.textPrimary,
            )
        }
        Button(
            onClick = {
                onSubmit(title, description, occasion, recipient, priceText, url, targetOn, pinned)
                title = ""
                description = ""
                occasion = ""
                recipient = ""
                priceText = ""
                url = ""
                targetOn = ""
                pinned = false
            },
            enabled = !busy && title.isNotBlank(),
            modifier = Modifier.heightIn(min = MinimumTouchTarget),
        ) {
            Text(submitLabel)
        }
    }
}

@Composable
private fun EditGiftIdeaDialog(
    idea: GiftIdeaDetail,
    busy: Boolean,
    onDismiss: () -> Unit,
    onSave: (
        title: String,
        description: String,
        occasion: String,
        recipient: String,
        priceText: String,
        url: String,
        targetOn: String,
        pinned: Boolean,
    ) -> Unit,
) {
    AlertDialog(
        onDismissRequest = onDismiss,
        title = { Text(stringResource(R.string.gift_idea_edit_title)) },
        text = {
            LazyColumn(modifier = Modifier.heightIn(max = 480.dp)) {
                item {
                    GiftIdeaForm(
                        submitLabel = stringResource(R.string.gift_idea_save_changes),
                        busy = busy,
                        initialTitle = idea.title,
                        initialDescription = idea.description.orEmpty(),
                        initialOccasion = idea.occasion.orEmpty(),
                        initialRecipient = idea.recipient.orEmpty(),
                        initialPriceText = idea.priceText.orEmpty(),
                        initialUrl = idea.url.orEmpty(),
                        initialTargetOn = idea.targetOn?.toString().orEmpty(),
                        initialPinned = idea.pinned,
                        onSubmit = { title, description, occasion, recipient, priceText, url, targetOn, pinned ->
                            onSave(title, description, occasion, recipient, priceText, url, targetOn, pinned)
                        },
                    )
                }
            }
        },
        confirmButton = {},
        dismissButton = {
            TextButton(onClick = onDismiss) { Text(stringResource(R.string.gift_idea_cancel)) }
        },
    )
}

private fun GiftIdeaStatus.labelRes(): Int = when (this) {
    GiftIdeaStatus.IDEA -> R.string.gift_idea_status_idea
    GiftIdeaStatus.BOUGHT -> R.string.gift_idea_status_bought
    GiftIdeaStatus.GIVEN -> R.string.gift_idea_status_given
}
