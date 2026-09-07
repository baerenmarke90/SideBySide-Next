package de.sidebyside.next.shell

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.ColumnScope
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.heightIn
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.widthIn
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.selection.selectable
import androidx.compose.foundation.selection.selectableGroup
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedButton
import androidx.compose.material3.RadioButton
import androidx.compose.material3.Surface
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.res.stringResource
import androidx.compose.ui.semantics.Role
import androidx.compose.ui.semantics.heading
import androidx.compose.ui.semantics.semantics
import androidx.compose.ui.unit.Dp
import de.sidebyside.next.design.MinimumTouchTarget
import de.sidebyside.next.design.SideBySideTheme
import de.sidebyside.next.reference.R
import java.util.UUID
import sidebyside.api.models.AccountMembershipView

/**
 * The Mehr area.
 *
 * Direction B ("Living Sanctuary") reads this as a human-first Settings
 * hierarchy rather than a flat CRUD menu: identity comes first, relationship
 * context second, day-to-day preferences third, data/privacy fourth, and
 * account/Space actions that cannot be undone last and visually apart. It
 * owns the existing signed-in utility surface. Personal identity and the
 * sensitive Account/Space actions insert their real content through
 * [identityContent] and [sensitiveContent] without creating a new top-level
 * destination.
 */
@Composable
fun MoreScreen(
    onSignOut: () -> Unit,
    /**
     * Opens the account's own HeartMoments.
     *
     * Deliberately without a default. An optional navigation entry that a
     * caller forgets to pass disappears from the product without breaking the
     * build, which is how this one was lost once already.
     */
    onOpenHeartMoments: () -> Unit,
    onOpenInvitations: () -> Unit,
    /**
     * Opens the people the couple wants to remember dates for.
     *
     * Deliberately without a default, for the same reason as
     * [onOpenHeartMoments]: an optional navigation entry a caller forgets to
     * pass disappears from the product without breaking the build.
     */
    onOpenRelatedPersons: () -> Unit,
    /**
     * Opens the couple's shared and private preferences.
     *
     * Deliberately without a default, for the same reason as
     * [onOpenHeartMoments].
     */
    onOpenPreferences: () -> Unit,
    /**
     * Opens the owner-only Private Area.
     *
     * Deliberately without a default, for the same reason as
     * [onOpenHeartMoments].
     */
    onOpenPrivateArea: () -> Unit,
    /**
     * Opens the M2-D17/S6 Transfer Bundle data export.
     *
     * Deliberately without a default, for the same reason as
     * [onOpenHeartMoments].
     */
    onOpenDataExport: () -> Unit,
    /**
     * Opens the M2-D17/S6 Transfer Bundle data import.
     *
     * Deliberately without a default, for the same reason as
     * [onOpenHeartMoments].
     */
    onOpenDataImport: () -> Unit,
    /**
     * Opens the account's notifications.
     *
     * Deliberately without a default, for the same reason as
     * [onOpenHeartMoments].
     */
    onOpenNotifications: () -> Unit,
    /**
     * Opens global Search.
     *
     * Deliberately without a default, for the same reason as
     * [onOpenHeartMoments].
     */
    onOpenSearch: () -> Unit,
    modifier: Modifier = Modifier,
    signOutEnabled: Boolean = true,
    unreadNotificationCount: Int = 0,
    spaces: List<AccountMembershipView> = emptyList(),
    spacePartnerNames: Map<UUID, String> = emptyMap(),
    activeSpaceId: UUID? = null,
    onSelectSpace: (UUID) -> Unit = {},
    /** The person/identity surface (avatar, display name, partner preview). */
    identityContent: @Composable () -> Unit = {},
    /**
     * Account deletion and Space offboarding.
     *
     * Rendered last, under its own eyebrow, deliberately apart from every
     * other section: Direction B keeps irreversible actions calm and
     * unmistakably separate rather than one more equal-weight card.
     */
    sensitiveContent: @Composable () -> Unit = {},
) {
    Column(
        modifier = modifier
            .fillMaxWidth()
            .verticalScroll(rememberScrollState())
            .padding(SideBySideTheme.spacing.pageMargin),
        verticalArrangement = Arrangement.spacedBy(SideBySideTheme.spacing.sectionGap),
    ) {
        Column(
            verticalArrangement = Arrangement.spacedBy(SideBySideTheme.spacing.step2),
        ) {
            Text(
                text = stringResource(R.string.more_eyebrow),
                style = MaterialTheme.typography.labelSmall,
                color = SideBySideTheme.colors.brandStrong,
            )
            Text(
                text = stringResource(R.string.more_title),
                style = MaterialTheme.typography.headlineMedium,
                color = SideBySideTheme.colors.textPrimary,
                modifier = Modifier.semantics { heading() },
            )
            Text(
                text = stringResource(R.string.more_intro),
                style = MaterialTheme.typography.bodyLarge,
                color = SideBySideTheme.colors.textSecondary,
                modifier = Modifier.widthIn(max = ReadingMeasure),
            )
        }

        // Direction B: the person comes before their configuration. Unboxed,
        // like the identity content itself already renders.
        identityContent()

        SectionGroup(
            eyebrow = stringResource(R.string.more_section_relationship_eyebrow),
            title = stringResource(R.string.more_section_relationship_title),
            intro = stringResource(R.string.more_section_relationship_intro),
        ) {
            if (spaces.size > 1) {
                SpaceChoice(
                    spaces = spaces,
                    activeSpaceId = activeSpaceId,
                    enabled = signOutEnabled,
                    onSelectSpace = onSelectSpace,
                    partnerNames = spacePartnerNames,
                )
            }
            MoreEntryRow(
                title = stringResource(R.string.heart_moments_title),
                intro = stringResource(R.string.heart_moments_intro),
                actionLabel = stringResource(R.string.heart_moments_open),
                onClick = onOpenHeartMoments,
            )
            MoreEntryRow(
                title = stringResource(R.string.invitations_title),
                intro = stringResource(R.string.invitations_intro),
                actionLabel = stringResource(R.string.invitation_create),
                onClick = onOpenInvitations,
            )
            MoreEntryRow(
                title = stringResource(R.string.related_persons_title),
                intro = stringResource(R.string.related_persons_intro),
                actionLabel = stringResource(R.string.related_persons_open),
                onClick = onOpenRelatedPersons,
            )
        }

        SectionGroup(
            eyebrow = stringResource(R.string.more_section_daily_eyebrow),
            title = stringResource(R.string.more_section_daily_title),
            intro = stringResource(R.string.more_section_daily_intro),
        ) {
            MoreEntryRow(
                title = if (unreadNotificationCount > 0) {
                    "${stringResource(R.string.notifications_title)} · " +
                        stringResource(R.string.notifications_unread_count, unreadNotificationCount)
                } else {
                    stringResource(R.string.notifications_title)
                },
                intro = stringResource(R.string.notifications_intro),
                actionLabel = stringResource(R.string.notifications_open),
                onClick = onOpenNotifications,
            )
            MoreEntryRow(
                title = stringResource(R.string.preferences_title),
                intro = stringResource(R.string.preferences_self_intro),
                actionLabel = stringResource(R.string.preferences_open),
                onClick = onOpenPreferences,
            )
            MoreEntryRow(
                title = stringResource(R.string.search_title),
                intro = stringResource(R.string.search_intro),
                actionLabel = stringResource(R.string.search_open),
                onClick = onOpenSearch,
            )
        }

        SectionGroup(
            eyebrow = stringResource(R.string.more_section_data_eyebrow),
            title = stringResource(R.string.more_section_data_title),
            intro = stringResource(R.string.more_section_data_intro),
        ) {
            MoreEntryRow(
                title = stringResource(R.string.private_area_card_title),
                intro = stringResource(R.string.private_area_card_intro),
                actionLabel = stringResource(R.string.private_area_open),
                onClick = onOpenPrivateArea,
            )
            MoreEntryRow(
                title = stringResource(R.string.data_export_card_title),
                intro = stringResource(R.string.data_export_card_intro),
                actionLabel = stringResource(R.string.data_export_open),
                onClick = onOpenDataExport,
            )
            MoreEntryRow(
                title = stringResource(R.string.data_import_card_title),
                intro = stringResource(R.string.data_import_card_intro),
                actionLabel = stringResource(R.string.data_import_open),
                onClick = onOpenDataImport,
            )
        }

        Surface(
            shape = RoundedCornerShape(SideBySideTheme.radii.card),
            color = SideBySideTheme.colors.surface,
            modifier = Modifier.fillMaxWidth(),
        ) {
            Column(
                modifier = Modifier.padding(SideBySideTheme.spacing.cardPadding),
                verticalArrangement = Arrangement.spacedBy(
                    SideBySideTheme.spacing.step4,
                ),
            ) {
                Text(
                    text = stringResource(R.string.more_session_title),
                    style = MaterialTheme.typography.titleMedium,
                    color = SideBySideTheme.colors.textPrimary,
                    modifier = Modifier.semantics { heading() },
                )
                Text(
                    text = stringResource(R.string.more_session_body),
                    style = MaterialTheme.typography.bodyMedium,
                    color = SideBySideTheme.colors.textSecondary,
                )
                OutlinedButton(
                    onClick = onSignOut,
                    enabled = signOutEnabled,
                    modifier = Modifier.heightIn(min = MinimumTouchTarget),
                ) {
                    Text(stringResource(R.string.more_sign_out))
                }
            }
        }

        // Direction B sensitive zone: consequence-first, sober, and set apart
        // with generous space rather than another equal-weight card.
        Column(verticalArrangement = Arrangement.spacedBy(SideBySideTheme.spacing.step2)) {
            Text(
                text = stringResource(R.string.more_section_sensitive_eyebrow),
                style = MaterialTheme.typography.labelSmall,
                color = SideBySideTheme.colors.error,
            )
            Text(
                text = stringResource(R.string.more_section_sensitive_title),
                style = MaterialTheme.typography.titleLarge,
                color = SideBySideTheme.colors.textPrimary,
                modifier = Modifier.semantics { heading() },
            )
            Text(
                text = stringResource(R.string.more_section_sensitive_intro),
                style = MaterialTheme.typography.bodyMedium,
                color = SideBySideTheme.colors.textSecondary,
                modifier = Modifier.widthIn(max = ReadingMeasure),
            )
            Column(
                modifier = Modifier.padding(top = SideBySideTheme.spacing.step2),
                verticalArrangement = Arrangement.spacedBy(SideBySideTheme.spacing.step4),
            ) {
                sensitiveContent()
            }
        }
    }
}

/**
 * One quiet section: an eyebrow/title/intro header followed by its entries
 * inside a single Surface, so several related destinations read as one
 * grouped section rather than as separate equal-weight cards.
 */
@Composable
private fun SectionGroup(
    eyebrow: String,
    title: String,
    intro: String,
    modifier: Modifier = Modifier,
    content: @Composable ColumnScope.() -> Unit,
) {
    Column(
        modifier = modifier.fillMaxWidth(),
        verticalArrangement = Arrangement.spacedBy(SideBySideTheme.spacing.step2),
    ) {
        Text(
            text = eyebrow,
            style = MaterialTheme.typography.labelSmall,
            color = SideBySideTheme.colors.brandStrong,
        )
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
        Surface(
            shape = RoundedCornerShape(SideBySideTheme.radii.card),
            color = SideBySideTheme.colors.surface,
            modifier = Modifier
                .fillMaxWidth()
                .padding(top = SideBySideTheme.spacing.step2),
        ) {
            Column(
                modifier = Modifier.padding(SideBySideTheme.spacing.cardPadding),
                verticalArrangement = Arrangement.spacedBy(SideBySideTheme.spacing.step5),
                content = content,
            )
        }
    }
}

/** One destination inside a [SectionGroup]: a quiet row, not its own card. */
@Composable
private fun MoreEntryRow(
    title: String,
    intro: String,
    actionLabel: String,
    onClick: () -> Unit,
    modifier: Modifier = Modifier,
) {
    Column(
        modifier = modifier.fillMaxWidth(),
        verticalArrangement = Arrangement.spacedBy(SideBySideTheme.spacing.step3),
    ) {
        Text(
            text = title,
            style = MaterialTheme.typography.titleMedium,
            color = SideBySideTheme.colors.textPrimary,
            modifier = Modifier.semantics { heading() },
        )
        Text(
            text = intro,
            style = MaterialTheme.typography.bodyMedium,
            color = SideBySideTheme.colors.textSecondary,
        )
        OutlinedButton(
            onClick = onClick,
            modifier = Modifier.heightIn(min = MinimumTouchTarget),
        ) {
            Text(actionLabel)
        }
    }
}

/**
 * Offered only where the account really is active in more than one Space, so
 * the ordinary couple never meets a choice they do not have.
 *
 * The Spaces are numbered rather than named: a Space ID is a technical value a
 * couple must never be asked to read, and the human name belongs to the Space
 * resource, which arrives with the identity surfaces slice.
 *
 * Rendered as one entry inside the relationship [SectionGroup] rather than in
 * its own Surface, so it does not nest a card inside a card.
 */
@Composable
private fun SpaceChoice(
    spaces: List<AccountMembershipView>,
    activeSpaceId: UUID?,
    enabled: Boolean,
    onSelectSpace: (UUID) -> Unit,
    /** Falls back to a position where a name has not resolved yet. */
    partnerNames: Map<UUID, String> = emptyMap(),
) {
    Column(verticalArrangement = Arrangement.spacedBy(SideBySideTheme.spacing.step4)) {
        Text(
            text = stringResource(R.string.more_space_title),
            style = MaterialTheme.typography.titleMedium,
            color = SideBySideTheme.colors.textPrimary,
            modifier = Modifier.semantics { heading() },
        )
        Text(
            text = stringResource(R.string.more_space_body),
            style = MaterialTheme.typography.bodyMedium,
            color = SideBySideTheme.colors.textSecondary,
            modifier = Modifier.widthIn(max = ReadingMeasure),
        )
        Column(Modifier.selectableGroup()) {
            spaces.forEachIndexed { index, membership ->
                val selected = membership.spaceId == activeSpaceId
                Row(
                    modifier = Modifier
                        .fillMaxWidth()
                        .heightIn(min = MinimumTouchTarget)
                        .selectable(
                            selected = selected,
                            enabled = enabled,
                            role = Role.RadioButton,
                            onClick = { onSelectSpace(membership.spaceId) },
                        ),
                    verticalAlignment = Alignment.CenterVertically,
                ) {
                    // The row carries the click; the button must not take
                    // a second stop in the screen reader's order.
                    RadioButton(selected = selected, onClick = null)
                    Text(
                        text = partnerNames[membership.spaceId]
                            ?: stringResource(R.string.more_space_option, index + 1),
                        style = MaterialTheme.typography.bodyLarge,
                        color = SideBySideTheme.colors.textPrimary,
                        modifier = Modifier.padding(
                            start = SideBySideTheme.spacing.step3,
                        ),
                    )
                }
            }
        }
    }
}

private val ReadingMeasure: Dp = androidx.compose.ui.unit.Dp(560f)
