package de.sidebyside.next.notifications

import androidx.compose.foundation.clickable
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
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Surface
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.runtime.Composable
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
import sidebyside.api.models.NotificationItem
import sidebyside.api.models.NotificationKind

private val ReadingMeasure: Dp = 560.dp

/**
 * The account's own notifications.
 *
 * A notification whose [NotificationItem.targetType]/[NotificationItem.targetId]
 * resolves to a route (see `engagementTargetRoute` in `MainActivity.kt`)
 * opens it on tap, per the M2-D18 cross-client Deep Link contract's "small
 * logical target tuple" — #357's original "no speculative destination"
 * exclusion no longer applies now that a resolver exists. A kind Android has
 * no detail route for yet (Wish, Plan) stays a plain, unclickable row.
 */
@Composable
fun NotificationsScreen(
    notifications: List<NotificationItem>,
    unreadCount: Int,
    busy: Boolean,
    problem: UiProblem?,
    onBack: () -> Unit,
    onMarkRead: (NotificationItem) -> Unit,
    onMarkAllRead: () -> Unit,
    onOpen: (NotificationItem) -> Unit,
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
                    text = stringResource(R.string.notifications_title),
                    style = MaterialTheme.typography.headlineMedium.copy(fontFamily = FrauncesFamily),
                    color = SideBySideTheme.colors.textPrimary,
                    modifier = Modifier.semantics { heading() },
                )
                Text(
                    text = stringResource(R.string.notifications_intro),
                    style = MaterialTheme.typography.bodyMedium,
                    color = SideBySideTheme.colors.textSecondary,
                    modifier = Modifier.widthIn(max = ReadingMeasure),
                )
            }
        }

        problem?.let { item { UiStatePanel(problem = it) } }

        item {
            Row(
                horizontalArrangement = Arrangement.spacedBy(SideBySideTheme.spacing.step3),
                verticalAlignment = Alignment.CenterVertically,
            ) {
                if (unreadCount > 0) {
                    Text(
                        text = stringResource(R.string.notifications_unread_count, unreadCount),
                        style = MaterialTheme.typography.labelLarge,
                        color = SideBySideTheme.colors.brandStrong,
                    )
                }
                TextButton(
                    onClick = onMarkAllRead,
                    enabled = !busy && unreadCount > 0,
                    modifier = Modifier.heightIn(min = MinimumTouchTarget),
                ) {
                    Text(stringResource(R.string.notification_mark_all_read))
                }
            }
        }

        if (notifications.isEmpty() && !busy) {
            item {
                Text(
                    text = stringResource(R.string.notifications_empty),
                    style = MaterialTheme.typography.bodyMedium,
                    color = SideBySideTheme.colors.textSecondary,
                )
            }
        }

        items(count = notifications.size, key = { index -> notifications[index].id.toString() }) { index ->
            val notification = notifications[index]
            val unread = notification.readAt == null
            // The same resolver `onOpen` ultimately navigates with, so a row
            // never looks tappable without actually having somewhere to go.
            val opensSomewhere = de.sidebyside.next.reference
                .engagementTargetRoute(notification.targetType, notification.targetId) != null
            Surface(
                shape = RoundedCornerShape(SideBySideTheme.radii.card),
                color = if (unread) SideBySideTheme.colors.surfaceSubtle else SideBySideTheme.colors.surface,
                modifier = Modifier
                    .fillMaxWidth()
                    .then(if (opensSomewhere) Modifier.clickable { onOpen(notification) } else Modifier),
            ) {
                Row(
                    modifier = Modifier
                        .padding(SideBySideTheme.spacing.cardPadding)
                        .fillMaxWidth(),
                    horizontalArrangement = Arrangement.SpaceBetween,
                    verticalAlignment = Alignment.CenterVertically,
                ) {
                    Text(
                        text = stringResource(notification.kind.labelRes()),
                        style = if (unread) MaterialTheme.typography.titleMedium else MaterialTheme.typography.bodyLarge,
                        color = SideBySideTheme.colors.textPrimary,
                    )
                    if (unread) {
                        TextButton(
                            onClick = { onMarkRead(notification) },
                            enabled = !busy,
                            modifier = Modifier.heightIn(min = MinimumTouchTarget),
                        ) {
                            Text(stringResource(R.string.notification_mark_read))
                        }
                    }
                }
            }
        }
    }
}

private fun NotificationKind.labelRes(): Int = when (this) {
    NotificationKind.COMMENT_CREATED -> R.string.notification_kind_comment_created
    NotificationKind.THINKING_OF_YOU -> R.string.notification_kind_thinking_of_you
    NotificationKind.REMINDER_DUE -> R.string.notification_kind_reminder_due
}
