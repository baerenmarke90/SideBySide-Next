package de.sidebyside.next.cache

import androidx.room.Entity
import androidx.room.PrimaryKey

/**
 * A single durable marker of which Account+Space the cache currently
 * belongs to, plus the [generation] that context was established under —
 * so a fresh process can detect a context change even when nothing in this
 * session explicitly called [ProductReadCache.clearAll], and an in-flight
 * read can tell whether the context it started under is still the one on
 * disk. This is the defensive half of M2-D18's clearing rule, matching the
 * Web client's `captureCacheLease` check on every read/write rather than
 * relying only on the caller to clear at the right moment.
 *
 * [generation] changes on every context transition, including a switch back
 * to a previously cached Account+Space, so a lease captured before the
 * transition can never be mistaken for a current one afterwards.
 */
@Entity(tableName = "cache_context")
data class CacheContextEntity(
    @PrimaryKey val id: Int = SINGLETON_ID,
    val accountId: String,
    val spaceId: String,
    val generation: String,
) {
    companion object {
        const val SINGLETON_ID = 0
    }
}
