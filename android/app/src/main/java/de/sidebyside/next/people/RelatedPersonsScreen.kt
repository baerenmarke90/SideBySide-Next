package de.sidebyside.next.people

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
import androidx.compose.foundation.selection.toggleable
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.AlertDialog
import androidx.compose.material3.Button
import androidx.compose.material3.Checkbox
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
import de.sidebyside.next.design.FrauncesFamily
import de.sidebyside.next.design.MinimumTouchTarget
import de.sidebyside.next.design.SideBySideTheme
import de.sidebyside.next.reference.R
import de.sidebyside.next.shell.UiProblem
import de.sidebyside.next.shell.UiStatePanel
import java.time.LocalDate
import java.util.UUID
import sidebyside.api.models.ContentVisibility
import sidebyside.api.models.PersonRelationship
import sidebyside.api.models.RelatedPersonDeletePolicy
import sidebyside.api.models.RelatedPersonView

private val ReadingMeasure: Dp = 560.dp

/**
 * The people this couple wants to remember dates for.
 *
 * The delete confirmation is the point of this screen. Per #65 it must not
 * name, count, or otherwise hint at what a `cascade` deletion would remove —
 * not even a correct, already-filtered count, because the gap between what
 * this account can see and what actually gets removed is itself a disclosure.
 * The dialog below is therefore built entirely from fixed strings; nothing
 * about a person's ImportantDates is read to construct it.
 */
@Composable
fun RelatedPersonsScreen(
    people: List<RelatedPersonView>,
    busy: Boolean,
    problem: UiProblem?,
    onBack: () -> Unit,
    onAdd: (
        displayName: String,
        relationship: PersonRelationship,
        birthday: LocalDate?,
        birthdayYearKnown: Boolean,
        visibility: ContentVisibility,
    ) -> Unit,
    onEdit: (
        personId: UUID,
        displayName: String,
        relationship: PersonRelationship,
        birthday: LocalDate?,
        birthdayYearKnown: Boolean,
        visibility: ContentVisibility,
    ) -> Unit,
    onOpenDates: (UUID) -> Unit,
    onDelete: (UUID, RelatedPersonDeletePolicy) -> Unit,
    modifier: Modifier = Modifier,
) {
    var editing by rememberSaveable { mutableStateOf<String?>(null) }
    var deleteTarget by rememberSaveable { mutableStateOf<String?>(null) }

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
                    text = stringResource(R.string.related_persons_title),
                    style = MaterialTheme.typography.headlineMedium
                        .copy(fontFamily = FrauncesFamily),
                    color = SideBySideTheme.colors.textPrimary,
                    modifier = Modifier.semantics { heading() },
                )
                Text(
                    text = stringResource(R.string.related_persons_intro),
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
                    RelatedPersonForm(
                        submitLabel = stringResource(R.string.related_person_add),
                        busy = busy,
                        onSubmit = { displayName, relationship, birthday, birthdayYearKnown, visibility ->
                            onAdd(displayName, relationship, birthday, birthdayYearKnown, visibility)
                        },
                    )
                }
            }
        }

        if (people.isEmpty() && !busy) {
            item {
                Text(
                    text = stringResource(R.string.related_persons_empty),
                    style = MaterialTheme.typography.bodyMedium,
                    color = SideBySideTheme.colors.textSecondary,
                    modifier = Modifier.widthIn(max = ReadingMeasure),
                )
            }
        }

        items(count = people.size, key = { index -> people[index].id.toString() }) { index ->
            val person = people[index]
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
                        text = person.displayName,
                        style = MaterialTheme.typography.titleMedium,
                        color = SideBySideTheme.colors.textPrimary,
                    )
                    Text(
                        text = stringResource(person.relationship.labelRes()),
                        style = MaterialTheme.typography.bodySmall,
                        color = SideBySideTheme.colors.textSecondary,
                    )
                    Row(horizontalArrangement = Arrangement.spacedBy(SideBySideTheme.spacing.step3)) {
                        TextButton(
                            onClick = { onOpenDates(person.id) },
                            modifier = Modifier.heightIn(min = MinimumTouchTarget),
                        ) {
                            Text(stringResource(R.string.related_person_open))
                        }
                        TextButton(
                            onClick = { editing = person.id.toString() },
                            enabled = !busy,
                            modifier = Modifier.heightIn(min = MinimumTouchTarget),
                        ) {
                            Text(stringResource(R.string.related_person_edit))
                        }
                        TextButton(
                            onClick = { deleteTarget = person.id.toString() },
                            enabled = !busy,
                            modifier = Modifier.heightIn(min = MinimumTouchTarget),
                        ) {
                            Text(stringResource(R.string.related_person_delete))
                        }
                    }
                }
            }
        }
    }

    editing?.let { id ->
        val target = people.firstOrNull { it.id.toString() == id }
        if (target == null) {
            editing = null
            return@let
        }
        EditRelatedPersonDialog(
            person = target,
            busy = busy,
            onDismiss = { editing = null },
            onSave = { displayName, relationship, birthday, birthdayYearKnown, visibility ->
                editing = null
                onEdit(target.id, displayName, relationship, birthday, birthdayYearKnown, visibility)
            },
        )
    }

    deleteTarget?.let { id ->
        val person = people.firstOrNull { it.id.toString() == id }
        if (person == null) {
            deleteTarget = null
            return@let
        }
        DeleteRelatedPersonDialog(
            person = person,
            onDismiss = { deleteTarget = null },
            onConfirm = { policy ->
                deleteTarget = null
                onDelete(person.id, policy)
            },
        )
    }
}

/**
 * Shared by the inline add card and [EditRelatedPersonDialog], so the two
 * never drift into two different sets of fields for the same resource.
 */
@Composable
private fun RelatedPersonForm(
    submitLabel: String,
    busy: Boolean,
    initialName: String = "",
    initialRelationship: PersonRelationship = PersonRelationship.OTHER,
    initialBirthday: String = "",
    initialYearUnknown: Boolean = false,
    initialKeepPrivate: Boolean = false,
    onSubmit: (
        displayName: String,
        relationship: PersonRelationship,
        birthday: LocalDate?,
        birthdayYearKnown: Boolean,
        visibility: ContentVisibility,
    ) -> Unit,
) {
    var name by rememberSaveable { mutableStateOf(initialName) }
    var relationship by rememberSaveable { mutableStateOf(initialRelationship) }
    var birthday by rememberSaveable { mutableStateOf(initialBirthday) }
    var yearUnknown by rememberSaveable { mutableStateOf(initialYearUnknown) }
    var keepPrivate by rememberSaveable { mutableStateOf(initialKeepPrivate) }

    Column(verticalArrangement = Arrangement.spacedBy(SideBySideTheme.spacing.step3)) {
        OutlinedTextField(
            value = name,
            onValueChange = { name = it.take(120) },
            label = { Text(stringResource(R.string.related_person_name_hint)) },
            enabled = !busy,
            modifier = Modifier.fillMaxWidth(),
        )
        Text(
            text = stringResource(R.string.related_person_relationship),
            style = MaterialTheme.typography.labelLarge,
            color = SideBySideTheme.colors.textSecondary,
        )
        Column(Modifier.selectableGroup()) {
            for (option in PersonRelationship.entries) {
                Row(
                    modifier = Modifier
                        .fillMaxWidth()
                        .heightIn(min = MinimumTouchTarget)
                        .selectable(
                            selected = option == relationship,
                            enabled = !busy,
                            role = Role.RadioButton,
                            onClick = { relationship = option },
                        ),
                    verticalAlignment = Alignment.CenterVertically,
                ) {
                    RadioButton(selected = option == relationship, onClick = null)
                    Text(
                        text = stringResource(option.labelRes()),
                        style = MaterialTheme.typography.bodyLarge,
                        color = SideBySideTheme.colors.textPrimary,
                        modifier = Modifier.padding(start = SideBySideTheme.spacing.step3),
                    )
                }
            }
        }
        OutlinedTextField(
            value = birthday,
            onValueChange = { birthday = it },
            label = { Text(stringResource(R.string.related_person_birthday_hint)) },
            singleLine = true,
            enabled = !busy,
            modifier = Modifier.fillMaxWidth(),
        )
        Row(
            modifier = Modifier
                .heightIn(min = MinimumTouchTarget)
                .toggleable(
                    value = yearUnknown,
                    enabled = !busy,
                    role = Role.Checkbox,
                    onValueChange = { yearUnknown = it },
                ),
            verticalAlignment = Alignment.CenterVertically,
        ) {
            // The row carries the click; the checkbox must not take a
            // second stop in the screen reader's order.
            Checkbox(checked = yearUnknown, onCheckedChange = null, enabled = !busy)
            Text(
                text = stringResource(R.string.related_person_birthday_year_unknown),
                modifier = Modifier.padding(start = SideBySideTheme.spacing.step2),
            )
        }
        Row(
            modifier = Modifier
                .heightIn(min = MinimumTouchTarget)
                .toggleable(
                    value = keepPrivate,
                    enabled = !busy,
                    role = Role.Checkbox,
                    onValueChange = { keepPrivate = it },
                ),
            verticalAlignment = Alignment.CenterVertically,
        ) {
            Checkbox(checked = keepPrivate, onCheckedChange = null, enabled = !busy)
            Text(
                text = stringResource(R.string.related_person_keep_private),
                modifier = Modifier.padding(start = SideBySideTheme.spacing.step2),
            )
        }
        Button(
            onClick = {
                val parsedBirthday = birthday.trim().takeIf { it.isNotBlank() }
                    ?.let { runCatching { LocalDate.parse(it) }.getOrNull() }
                onSubmit(
                    name,
                    relationship,
                    parsedBirthday,
                    // A known year only means something once a birthday
                    // exists at all; the server rejects year-known without
                    // a date.
                    parsedBirthday != null && !yearUnknown,
                    if (keepPrivate) ContentVisibility.PRIVATE else ContentVisibility.SHARED,
                )
                name = ""
                birthday = ""
            },
            enabled = !busy && name.isNotBlank(),
            modifier = Modifier.heightIn(min = MinimumTouchTarget),
        ) {
            Text(submitLabel)
        }
    }
}

@Composable
private fun EditRelatedPersonDialog(
    person: RelatedPersonView,
    busy: Boolean,
    onDismiss: () -> Unit,
    onSave: (
        displayName: String,
        relationship: PersonRelationship,
        birthday: LocalDate?,
        birthdayYearKnown: Boolean,
        visibility: ContentVisibility,
    ) -> Unit,
) {
    AlertDialog(
        onDismissRequest = onDismiss,
        title = { Text(stringResource(R.string.related_person_edit_title, person.displayName)) },
        text = {
            LazyColumn(modifier = Modifier.heightIn(max = 480.dp)) {
                item {
                    RelatedPersonForm(
                        submitLabel = stringResource(R.string.related_person_save),
                        busy = busy,
                        initialName = person.displayName,
                        initialRelationship = person.relationship,
                        initialBirthday = person.birthday?.toString().orEmpty(),
                        initialYearUnknown = person.birthday != null && !person.birthdayYearKnown,
                        initialKeepPrivate = person.visibility == ContentVisibility.PRIVATE,
                        onSubmit = { displayName, relationship, birthday, birthdayYearKnown, visibility ->
                            onSave(displayName, relationship, birthday, birthdayYearKnown, visibility)
                        },
                    )
                }
            }
        },
        confirmButton = {},
        dismissButton = {
            TextButton(onClick = onDismiss) { Text(stringResource(R.string.related_person_cancel)) }
        },
    )
}

/**
 * Exactly the two named choices from #65, with `cascade` never the default
 * and visually set apart as the destructive one. No count, title, date or
 * owner of any linked ImportantDate appears here or was read to build this.
 */
@Composable
private fun DeleteRelatedPersonDialog(
    person: RelatedPersonView,
    onDismiss: () -> Unit,
    onConfirm: (RelatedPersonDeletePolicy) -> Unit,
) {
    var policy by rememberSaveable { mutableStateOf(RelatedPersonDeletePolicy.preserve) }

    AlertDialog(
        onDismissRequest = onDismiss,
        title = { Text(stringResource(R.string.related_person_delete_title, person.displayName)) },
        text = {
            Column(verticalArrangement = Arrangement.spacedBy(SideBySideTheme.spacing.step4)) {
                Text(
                    text = stringResource(R.string.related_person_delete_warning),
                    style = MaterialTheme.typography.bodyMedium,
                    color = SideBySideTheme.colors.textSecondary,
                )
                Column(Modifier.selectableGroup()) {
                    DeleteChoice(
                        selected = policy == RelatedPersonDeletePolicy.preserve,
                        titleRes = R.string.related_person_delete_preserve_title,
                        bodyRes = R.string.related_person_delete_preserve_body,
                        destructive = false,
                        onClick = { policy = RelatedPersonDeletePolicy.preserve },
                    )
                    DeleteChoice(
                        selected = policy == RelatedPersonDeletePolicy.cascade,
                        titleRes = R.string.related_person_delete_cascade_title,
                        bodyRes = R.string.related_person_delete_cascade_body,
                        destructive = true,
                        onClick = { policy = RelatedPersonDeletePolicy.cascade },
                    )
                }
            }
        },
        confirmButton = {
            TextButton(onClick = { onConfirm(policy) }) {
                Text(
                    if (policy == RelatedPersonDeletePolicy.cascade) {
                        stringResource(R.string.related_person_delete_cascade_title)
                    } else {
                        stringResource(R.string.related_person_delete_preserve_title)
                    },
                )
            }
        },
        dismissButton = {
            TextButton(onClick = onDismiss) { Text(stringResource(R.string.related_person_cancel)) }
        },
    )
}

@Composable
private fun DeleteChoice(
    selected: Boolean,
    titleRes: Int,
    bodyRes: Int,
    destructive: Boolean,
    onClick: () -> Unit,
) {
    Row(
        modifier = Modifier
            .fillMaxWidth()
            .selectable(selected = selected, role = Role.RadioButton, onClick = onClick)
            .padding(vertical = SideBySideTheme.spacing.step2),
    ) {
        RadioButton(selected = selected, onClick = null)
        Column(modifier = Modifier.padding(start = SideBySideTheme.spacing.step2)) {
            Text(
                text = stringResource(titleRes),
                style = MaterialTheme.typography.bodyLarge,
                // Destructive is set apart by more than colour: it is also the
                // one choice with an explicit warning body beneath it.
                color = if (destructive) SideBySideTheme.colors.error else SideBySideTheme.colors.textPrimary,
            )
            Text(
                text = stringResource(bodyRes),
                style = MaterialTheme.typography.bodySmall,
                color = SideBySideTheme.colors.textSecondary,
            )
        }
    }
}

private fun PersonRelationship.labelRes(): Int = when (this) {
    PersonRelationship.CHILD -> R.string.related_relationship_child
    PersonRelationship.PARENT -> R.string.related_relationship_parent
    PersonRelationship.SIBLING -> R.string.related_relationship_sibling
    PersonRelationship.FRIEND -> R.string.related_relationship_friend
    PersonRelationship.OTHER -> R.string.related_relationship_other
}
