package de.sidebyside.next.reference

import android.content.Context
import java.util.UUID

/**
 * Remembers which Space an account last had active, so relaunching the app
 * returns to it instead of always resolving to the first ACTIVE membership.
 *
 * Not a security boundary: a Space ID carries no secret and is already
 * visible to the signed-in account through its own memberships. Unlike the
 * session tokens this client deliberately keeps in memory only, plain
 * platform storage is enough here — this is exactly the "chosen Space
 * remembered across launches" piece #391 named and #392 deferred.
 */
interface SpacePreferenceStore {
    fun rememberedSpace(accountId: UUID): UUID?

    fun rememberSpace(accountId: UUID, spaceId: UUID)
}

/**
 * Never remembers anything past this instance's own lifetime.
 *
 * The default for [ReferenceViewModel] so existing and new unit tests keep
 * resolving to the first ACTIVE membership without needing a Context —
 * exactly one fresh instance per ViewModel, never a shared singleton, so one
 * test's remembered Space can never leak into another's.
 */
class InMemorySpacePreferenceStore : SpacePreferenceStore {
    private val remembered = mutableMapOf<UUID, UUID>()

    override fun rememberedSpace(accountId: UUID): UUID? = remembered[accountId]

    override fun rememberSpace(accountId: UUID, spaceId: UUID) {
        remembered[accountId] = spaceId
    }
}

/**
 * Backed by [android.content.SharedPreferences], keyed per account so a
 * shared device never opens one account's last Space under another's
 * session.
 */
class SharedPreferencesSpaceStore(context: Context) : SpacePreferenceStore {
    private val prefs = context.applicationContext
        .getSharedPreferences(PREFS_NAME, Context.MODE_PRIVATE)

    override fun rememberedSpace(accountId: UUID): UUID? =
        prefs.getString(accountId.toString(), null)
            ?.let { runCatching { UUID.fromString(it) }.getOrNull() }

    override fun rememberSpace(accountId: UUID, spaceId: UUID) {
        prefs.edit().putString(accountId.toString(), spaceId.toString()).apply()
    }

    private companion object {
        const val PREFS_NAME = "space_preferences"
    }
}
