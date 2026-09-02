package de.sidebyside.next.cache

import androidx.room.Entity
import androidx.room.PrimaryKey

/**
 * One persisted read-cache row, per M2-D18's namespace rule: Account +
 * Space + Privacy scope + resource kind + resource id. [cacheKey] encodes
 * all of those so a row can only ever be looked up under the exact context
 * it was written for — there is no query that reads across accounts or
 * Spaces by construction, only by exact key.
 *
 * This table persists `SPACE_SHARED` content only. `OWNER_ONLY`
 * ProtectedPayload content lives encrypted in [ProtectedCacheEntity] instead,
 * per M2-D18's Android decision.
 */
@Entity(tableName = "product_read_cache")
data class ProductCacheEntity(
    @PrimaryKey val cacheKey: String,
    val accountId: String,
    val spaceId: String,
    val kind: String,
    val resourceId: String,
    val payloadJson: String,
    val refreshedAtEpochMs: Long,
)
