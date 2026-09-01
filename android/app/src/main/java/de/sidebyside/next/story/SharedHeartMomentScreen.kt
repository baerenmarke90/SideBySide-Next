package de.sidebyside.next.story

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.aspectRatio
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.widthIn
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.runtime.Composable
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.LocalConfiguration
import androidx.compose.ui.res.stringResource
import androidx.compose.ui.semantics.heading
import androidx.compose.ui.semantics.semantics
import androidx.compose.ui.unit.Dp
import androidx.compose.ui.unit.dp
import de.sidebyside.next.design.SideBySideTheme
import de.sidebyside.next.reference.R
import de.sidebyside.next.shell.UiProblem
import de.sidebyside.next.shell.UiStatePanel
import java.time.format.DateTimeFormatter
import java.time.format.FormatStyle
import java.util.Locale
import sidebyside.api.models.AttachmentReadRequest
import sidebyside.api.models.ContentVisibility
import sidebyside.api.models.HeartMomentDetail
import sidebyside.api.models.MediaType

private val ReadingMeasure: Dp = 560.dp

/**
 * A shared HeartMoment, opened from the Story.
 *
 * Read-only on purpose. Writing, changing and removing a moment live where the
 * account's own moments do, because only its author may do any of that; what is
 * missing from the Story is the ability to open one and say something about it.
 *
 * Deliberately not the memory screen with a discriminator: a HeartMoment has no
 * title, and its emotion and visibility have no counterpart there.
 */
@Composable
fun SharedHeartMomentScreen(
    moment: HeartMomentDetail?,
    imageStore: StoryImageStore,
    generation: Long,
    problem: UiProblem?,
    onBack: () -> Unit,
    modifier: Modifier = Modifier,
    comments: (@Composable () -> Unit)? = null,
) {
    if (moment == null) {
        problem?.let { UiStatePanel(problem = it, modifier = modifier) }
        return
    }

    val locale: Locale = LocalConfiguration.current.locales[0]
    val image = moment.attachment
        ?.takeIf { it.mediaType == MediaType.IMAGE && it.status == "READY" }
        ?.let {
            StoryImageRef(
                attachmentId = it.id,
                parentId = moment.id,
                parentType = AttachmentReadRequest.ParentType.HEART_MOMENT,
            )
        }

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

        problem?.let { current -> item { UiStatePanel(problem = current) } }

        item {
            Column(
                verticalArrangement = Arrangement.spacedBy(SideBySideTheme.spacing.step2),
                modifier = Modifier.padding(top = SideBySideTheme.spacing.step2),
            ) {
                Text(
                    text = moment.happenedOn.format(
                        DateTimeFormatter.ofLocalizedDate(FormatStyle.LONG).withLocale(locale),
                    ) + " · " + stringResource(moment.emotion.labelRes()),
                    style = MaterialTheme.typography.labelLarge,
                    color = SideBySideTheme.colors.brandStrong,
                )
                // The moment's own words are its heading; there is no title.
                Text(
                    text = moment.text,
                    style = MaterialTheme.typography.headlineSmall,
                    color = SideBySideTheme.colors.textPrimary,
                    modifier = Modifier
                        .widthIn(max = ReadingMeasure)
                        .semantics { heading() },
                )
                Text(
                    text = stringResource(
                        R.string.heart_moment_shared_by,
                        moment.author.displayName,
                    ),
                    style = MaterialTheme.typography.bodySmall,
                    color = SideBySideTheme.colors.textSecondary,
                )
            }
        }

        image?.let { ref ->
            item {
                StoryImage(
                    image = ref,
                    store = imageStore,
                    generation = generation,
                    modifier = Modifier
                        .fillMaxWidth()
                        .aspectRatio(4f / 3f),
                )
            }
        }

        // Only a shared moment has comments at all: making one private deletes
        // them, which is why the owner's screen offers no thread.
        if (moment.visibility == ContentVisibility.SHARED) {
            comments?.let { thread -> item { thread() } }
        }
    }
}
