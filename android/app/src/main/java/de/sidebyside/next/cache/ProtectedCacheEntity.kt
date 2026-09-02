package de.sidebyside.next.cache

import androidx.room.Entity
import androidx.room.PrimaryKey

/**
 * One persisted `OWNER_ONLY` read-cache row. [cacheKey] additionally carries
 * [ownerId], per M2-D18's Android decision: an owner-only cache namespace is
 * Account + Space + Owner + resource kind + resource id, not just Account +
 * Space. [ciphertext]/[iv] are the AES/GCM output of a key that never leaves
 * Android Keystore — this table never stores plaintext.
 */
@Entity(tableName = "protected_read_cache")
data class ProtectedCacheEntity(
    @PrimaryKey val cacheKey: String,
    val accountId: String,
    val spaceId: String,
    val ownerId: String,
    val kind: String,
    val resourceId: String,
    val ciphertext: ByteArray,
    val iv: ByteArray,
    val refreshedAtEpochMs: Long,
)
