package de.sidebyside.next.cache

import androidx.room.Dao
import androidx.room.Insert
import androidx.room.OnConflictStrategy
import androidx.room.Query

@Dao
interface ProductCacheDao {
    @Query("SELECT * FROM product_read_cache WHERE cacheKey = :cacheKey")
    suspend fun get(cacheKey: String): ProductCacheEntity?

    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun put(entity: ProductCacheEntity)

    @Query("DELETE FROM product_read_cache WHERE cacheKey = :cacheKey")
    suspend fun delete(cacheKey: String)

    /** The full wipe M2-D18 requires on logout, Account switch, and Space switch. */
    @Query("DELETE FROM product_read_cache")
    suspend fun clearAll()
}
