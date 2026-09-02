package de.sidebyside.next.cache

import androidx.room.Entity
import androidx.room.PrimaryKey

/**
 * A single durable marker of which Account+Space the cache currently
 * belongs to, so a fresh process can detect a context change even when
 * nothing in this session explicitly called [ProductReadCache.clearAll] —
 * the defensive half of M2-D18's clearing rule, matching the Web client's
 * `ensureCacheContext` check on every read/write rather than relying only
 * on the caller to clear at the right moment.
 */
@Entity(tableName = "cache_context")
data class CacheContextEntity(
    @PrimaryKey val id: Int = SINGLETON_ID,
    val accountId: String,
    val spaceId: String,
) {
    companion object {
        const val SINGLETON_ID = 0
    }
}
