package de.sidebyside.next.cache

import android.content.Context
import androidx.room.Database
import androidx.room.Room
import androidx.room.RoomDatabase

/**
 * The M2-D18 read-cache store. A schema change destroys and recreates the
 * database rather than migrating it — a read cache is an optimization, not
 * a source of truth, and an unreadable/incompatible schema must fail closed
 * (evict) rather than risk serving a malformed row.
 */
@Database(
    entities = [ProductCacheEntity::class, CacheContextEntity::class],
    version = 1,
    exportSchema = false,
)
abstract class ReadCacheDatabase : RoomDatabase() {
    abstract fun productCacheDao(): ProductCacheDao
    abstract fun cacheContextDao(): CacheContextDao

    companion object {
        private const val DATABASE_NAME = "sidebyside-read-cache.db"

        @Volatile
        private var instance: ReadCacheDatabase? = null

        fun getInstance(context: Context): ReadCacheDatabase =
            instance ?: synchronized(this) {
                instance ?: Room.databaseBuilder(
                    context.applicationContext,
                    ReadCacheDatabase::class.java,
                    DATABASE_NAME,
                )
                    .fallbackToDestructiveMigration(dropAllTables = true)
                    .build()
                    .also { instance = it }
            }
    }
}
