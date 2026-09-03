package de.sidebyside.next.profile

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.PaddingValues
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.heightIn
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.widthIn
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.selection.selectable
import androidx.compose.foundation.selection.selectableGroup
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.AlertDialog
import androidx.compose.material3.Button
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedTextField
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
import de.sidebyside.next.design.SideBySideDisplayFamily
import de.sidebyside.next.design.MinimumTouchTarget
import de.sidebyside.next.design.SideBySideTheme
import de.sidebyside.next.reference.R
import de.sidebyside.next.shell.UiProblem
import de.sidebyside.next.shell.UiStatePanel
import sidebyside.api.models.PreferenceCategory
import sidebyside.api.models.PreferenceSentiment
import sidebyside.api.models.ProfilePreferenceView

private val ReadingMeasure: Dp = 560.dp

/**
 * What each partner likes, and the private notes kept about the other one.
 *
 * Three sections, never merged: my own preferences (editable, shared with my
 * partner's profile), my partner's preferences (read-only — the server
 * already filtered this to what they chose to share), and my private notes
 * about my partner (editable, and per their own visibility never readable by
 * anyone but me — the assurance text below is a fact about the server, not a
 * request the client makes of it).
 */
@Composable
fun ProfilePreferencesScreen(
    selfPreferences: List<ProfilePreferenceView>,
    partnerPreferences: List<ProfilePreferenceView>,
    privateNotes: List<ProfilePreferenceView>,
    partnerName: String?,
    busy: Boolean,
    problem: UiProblem?,
    onBack: () -> Unit,
    onAddSelf: (PreferenceCategory, String, PreferenceSentiment, String) -> Unit,
    onAddPrivateNote: (PreferenceCategory, String, PreferenceSentiment, String) -> Unit,
    onEdit: (ProfilePreferenceView, PreferenceCategory, String, PreferenceSentiment, String) -> Unit,
    onDelete: (ProfilePreferenceView) -> Unit,
    modifier: Modifier = Modifier,
) {
    var editing by rememberSaveable { mutableStateOf<String?>(null) }

    LazyColumn(
        modifier = modifier.fillMaxWidth(),
        contentPadding = PaddingValues(SideBySideTheme.spacing.pageMargin),
        verticalArrangement = Arrangement.spacedBy(SideBySideTheme.spacing.step5),
    ) {
        item {
            TextButton(onClick = onBack) { Text(stringResource(R.string.memory_back)) }
        }

        item {
            Text(
                text = stringResource(R.string.preferences_title),
                style = MaterialTheme.typography.headlineMedium.copy(fontFamily = SideBySideDisplayFamily),
                color = SideBySideTheme.colors.textPrimary,
                modifier = Modifier.semantics { heading() },
            )
        }

        problem?.let { item { UiStatePanel(problem = it) } }

        item {
            PreferenceSection(
                title = stringResource(R.string.preferences_self_title),
                intro = stringResource(R.string.preferences_self_intro),
                entries = selfPreferences,
                emptyText = stringResource(R.string.preferences_self_empty),
                busy = busy,
                editable = true,
                onEditRequest = { editing = it.id.toString() },
                onDelete = onDelete,
                addForm = {
                    PreferenceForm(
                        topicHint = stringResource(R.string.preferences_self_topic_hint),
                        valueHint = stringResource(R.string.preferences_self_value_hint),
                        busy = busy,
                        onSubmit = onAddSelf,
                    )
                },
            )
        }

        if (partnerName != null) {
            item {
                PreferenceSection(
                    title = stringResource(R.string.preferences_partner_title, partnerName),
                    intro = stringResource(R.string.preferences_partner_intro),
                    entries = partnerPreferences,
                    emptyText = stringResource(R.string.preferences_partner_empty),
                    busy = busy,
                    editable = false,
                    onEditRequest = {},
                    onDelete = {},
                    addForm = null,
                )
            }

            item {
                PreferenceSection(
                    title = stringResource(R.string.preferences_private_title, partnerName),
                    intro = stringResource(R.string.preferences_private_intro),
                    entries = privateNotes,
                    emptyText = stringResource(R.string.preferences_private_empty),
                    busy = busy,
                    editable = true,
                    onEditRequest = { editing = it.id.toString() },
                    onDelete = onDelete,
                    addForm = {
                        PreferenceForm(
                            topicHint = stringResource(R.string.preferences_private_topic_hint),
                            valueHint = stringResource(R.string.preferences_private_value_hint),
                            busy = busy,
                            onSubmit = onAddPrivateNote,
                        )
                    },
                )
            }
        }
    }

    editing?.let { id ->
        val target = (selfPreferences + partnerPreferences + privateNotes)
            .firstOrNull { it.id.toString() == id }
        if (target == null) {
            editing = null
            return@let
        }
        EditPreferenceDialog(
            preference = target,
            onDismiss = { editing = null },
            onSave = { category, topic, sentiment, value ->
                editing = null
                onEdit(target, category, topic, sentiment, value)
            },
        )
    }
}

@Composable
private fun PreferenceSection(
    title: String,
    intro: String,
    entries: List<ProfilePreferenceView>,
    emptyText: String,
    busy: Boolean,
    editable: Boolean,
    onEditRequest: (ProfilePreferenceView) -> Unit,
    onDelete: (ProfilePreferenceView) -> Unit,
    addForm: (@Composable () -> Unit)?,
) {
    Column(verticalArrangement = Arrangement.spacedBy(SideBySideTheme.spacing.step3)) {
        Text(
            text = title,
            style = MaterialTheme.typography.titleLarge,
            color = SideBySideTheme.colors.textPrimary,
            modifier = Modifier.semantics { heading() },
        )
        Text(
            text = intro,
            style = MaterialTheme.typography.bodyMedium,
            color = SideBySideTheme.colors.textSecondary,
            modifier = Modifier.widthIn(max = ReadingMeasure),
        )

        addForm?.let {
            Surface(
                shape = RoundedCornerShape(SideBySideTheme.radii.card),
                color = SideBySideTheme.colors.surface,
                modifier = Modifier.fillMaxWidth(),
            ) {
                Column(modifier = Modifier.padding(SideBySideTheme.spacing.cardPadding)) { it() }
            }
        }

        if (entries.isEmpty() && !busy) {
            Text(
                text = emptyText,
                style = MaterialTheme.typography.bodyMedium,
                color = SideBySideTheme.colors.textSecondary,
            )
        }

        entries.forEach { entry ->
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
                        text = entry.topic,
                        style = MaterialTheme.typography.titleMedium,
                        color = SideBySideTheme.colors.textPrimary,
                    )
                    Text(
                        text = "${stringResource(entry.category.labelRes())} · " +
                            stringResource(entry.sentiment.labelRes()),
                        style = MaterialTheme.typography.labelMedium,
                        color = SideBySideTheme.colors.brandStrong,
                    )
                    Text(
                        text = entry.value,
                        style = MaterialTheme.typography.bodyMedium,
                        color = SideBySideTheme.colors.textSecondary,
                    )
                    if (editable) {
                        Row(horizontalArrangement = Arrangement.spacedBy(SideBySideTheme.spacing.step3)) {
                            TextButton(
                                onClick = { onEditRequest(entry) },
                                enabled = !busy,
                                modifier = Modifier.heightIn(min = MinimumTouchTarget),
                            ) {
                                Text(stringResource(R.string.preference_edit))
                            }
                            TextButton(
                                onClick = { onDelete(entry) },
                                enabled = !busy,
                                modifier = Modifier.heightIn(min = MinimumTouchTarget),
                            ) {
                                Text(stringResource(R.string.preference_delete))
                            }
                        }
                    }
                }
            }
        }
    }
}

@Composable
private fun PreferenceForm(
    topicHint: String,
    valueHint: String,
    busy: Boolean,
    onSubmit: (PreferenceCategory, String, PreferenceSentiment, String) -> Unit,
) {
    var category by rememberSaveable { mutableStateOf(PreferenceCategory.OTHER) }
    var sentiment by rememberSaveable { mutableStateOf(PreferenceSentiment.LIKE) }
    var topic by rememberSaveable { mutableStateOf("") }
    var value by rememberSaveable { mutableStateOf("") }

    Column(verticalArrangement = Arrangement.spacedBy(SideBySideTheme.spacing.step3)) {
        OutlinedTextField(
            value = topic,
            onValueChange = { topic = it.take(120) },
            label = { Text(topicHint) },
            enabled = !busy,
            modifier = Modifier.fillMaxWidth(),
        )
        OutlinedTextField(
            value = value,
            onValueChange = { value = it.take(2000) },
            label = { Text(valueHint) },
            enabled = !busy,
            modifier = Modifier.fillMaxWidth(),
        )
        CategoryPicker(selected = category, enabled = !busy, onSelect = { category = it })
        SentimentPicker(selected = sentiment, enabled = !busy, onSelect = { sentiment = it })
        Button(
            onClick = {
                onSubmit(category, topic, sentiment, value)
                topic = ""
                value = ""
            },
            enabled = !busy && topic.isNotBlank() && value.isNotBlank(),
            modifier = Modifier.heightIn(min = MinimumTouchTarget),
        ) {
            Text(stringResource(R.string.preference_add))
        }
    }
}

@Composable
private fun EditPreferenceDialog(
    preference: ProfilePreferenceView,
    onDismiss: () -> Unit,
    onSave: (PreferenceCategory, String, PreferenceSentiment, String) -> Unit,
) {
    var category by rememberSaveable { mutableStateOf(preference.category) }
    var sentiment by rememberSaveable { mutableStateOf(preference.sentiment) }
    var topic by rememberSaveable { mutableStateOf(preference.topic) }
    var value by rememberSaveable { mutableStateOf(preference.value) }

    AlertDialog(
        onDismissRequest = onDismiss,
        title = { Text(stringResource(R.string.preference_edit_title)) },
        text = {
            // AlertDialog does not bound or scroll its text slot on its own;
            // two fields plus twelve categories and five sentiments overflow
            // most screens. Modifier.verticalScroll on a plain Column never
            // received the touch here (confirmed by hand on the device: the
            // picker stayed cut off, unreachable, no matter the swipe) —
            // LazyColumn is the one scroll container this codebase already
            // relies on elsewhere, so it replaces the Column here too.
            LazyColumn(
                modifier = Modifier.heightIn(max = 420.dp),
                verticalArrangement = Arrangement.spacedBy(SideBySideTheme.spacing.step3),
            ) {
                item {
                    OutlinedTextField(
                        value = topic,
                        onValueChange = { topic = it.take(120) },
                        label = { Text(stringResource(R.string.preference_topic_label)) },
                        modifier = Modifier.fillMaxWidth(),
                    )
                }
                item {
                    OutlinedTextField(
                        value = value,
                        onValueChange = { value = it.take(2000) },
                        label = { Text(stringResource(R.string.preferences_self_value_hint)) },
                        modifier = Modifier.fillMaxWidth(),
                    )
                }
                item {
                    CategoryPicker(selected = category, enabled = true, onSelect = { category = it })
                }
                item {
                    SentimentPicker(selected = sentiment, enabled = true, onSelect = { sentiment = it })
                }
            }
        },
        confirmButton = {
            TextButton(
                onClick = { onSave(category, topic, sentiment, value) },
                enabled = topic.isNotBlank() && value.isNotBlank(),
            ) {
                Text(stringResource(R.string.preference_save_changes))
            }
        },
        dismissButton = {
            TextButton(onClick = onDismiss) { Text(stringResource(R.string.preference_cancel)) }
        },
    )
}

@Composable
private fun CategoryPicker(
    selected: PreferenceCategory,
    enabled: Boolean,
    onSelect: (PreferenceCategory) -> Unit,
) {
    Column {
        Text(
            text = stringResource(R.string.preference_category),
            style = MaterialTheme.typography.labelLarge,
            color = SideBySideTheme.colors.textSecondary,
        )
        Column(Modifier.selectableGroup()) {
            for (option in PreferenceCategory.entries) {
                Row(
                    modifier = Modifier
                        .fillMaxWidth()
                        .heightIn(min = MinimumTouchTarget)
                        .selectable(
                            selected = option == selected,
                            enabled = enabled,
                            role = Role.RadioButton,
                            onClick = { onSelect(option) },
                        ),
                    verticalAlignment = Alignment.CenterVertically,
                ) {
                    RadioButton(selected = option == selected, onClick = null)
                    Text(
                        text = stringResource(option.labelRes()),
                        style = MaterialTheme.typography.bodyLarge,
                        color = SideBySideTheme.colors.textPrimary,
                        modifier = Modifier.padding(start = SideBySideTheme.spacing.step3),
                    )
                }
            }
        }
    }
}

@Composable
private fun SentimentPicker(
    selected: PreferenceSentiment,
    enabled: Boolean,
    onSelect: (PreferenceSentiment) -> Unit,
) {
    Column {
        Text(
            text = stringResource(R.string.preference_sentiment),
            style = MaterialTheme.typography.labelLarge,
            color = SideBySideTheme.colors.textSecondary,
        )
        Column(Modifier.selectableGroup()) {
            for (option in PreferenceSentiment.entries) {
                Row(
                    modifier = Modifier
                        .fillMaxWidth()
                        .heightIn(min = MinimumTouchTarget)
                        .selectable(
                            selected = option == selected,
                            enabled = enabled,
                            role = Role.RadioButton,
                            onClick = { onSelect(option) },
                        ),
                    verticalAlignment = Alignment.CenterVertically,
                ) {
                    RadioButton(selected = option == selected, onClick = null)
                    Text(
                        text = stringResource(option.labelRes()),
                        style = MaterialTheme.typography.bodyLarge,
                        color = SideBySideTheme.colors.textPrimary,
                        modifier = Modifier.padding(start = SideBySideTheme.spacing.step3),
                    )
                }
            }
        }
    }
}

private fun PreferenceCategory.labelRes(): Int = when (this) {
    PreferenceCategory.FOOD -> R.string.preference_category_food
    PreferenceCategory.DRINK -> R.string.preference_category_drink
    PreferenceCategory.FLOWERS -> R.string.preference_category_flowers
    PreferenceCategory.MOVIES -> R.string.preference_category_movies
    PreferenceCategory.SERIES -> R.string.preference_category_series
    PreferenceCategory.MUSIC -> R.string.preference_category_music
    PreferenceCategory.HOBBIES -> R.string.preference_category_hobbies
    PreferenceCategory.ACTIVITIES -> R.string.preference_category_activities
    PreferenceCategory.TRAVEL -> R.string.preference_category_travel
    PreferenceCategory.RESTAURANTS -> R.string.preference_category_restaurants
    PreferenceCategory.COLORS -> R.string.preference_category_colors
    PreferenceCategory.OTHER -> R.string.preference_category_other
}

private fun PreferenceSentiment.labelRes(): Int = when (this) {
    PreferenceSentiment.LOVE -> R.string.preference_sentiment_love
    PreferenceSentiment.LIKE -> R.string.preference_sentiment_like
    PreferenceSentiment.NEUTRAL -> R.string.preference_sentiment_neutral
    PreferenceSentiment.DISLIKE -> R.string.preference_sentiment_dislike
    PreferenceSentiment.AVOID -> R.string.preference_sentiment_avoid
}
