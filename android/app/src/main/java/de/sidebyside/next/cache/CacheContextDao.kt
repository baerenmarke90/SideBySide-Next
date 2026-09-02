package de.sidebyside.next.cache

import androidx.room.Dao
import androidx.room.Insert
import androidx.room.OnConflictStrategy
import androidx.room.Query

@Dao
interface CacheContextDao {
    @Query("SELECT * FROM cache_context WHERE id = ${CacheContextEntity.SINGLETON_ID}")
    suspend fun get(): CacheContextEntity?

    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun set(entity: CacheContextEntity)

    @Query("DELETE FROM cache_context")
    suspend fun clear()
}
