package de.sidebyside.next.reference

/**
 * Operator configuration.
 *
 * Only the address of the server is configured. The Space is **not**: it is
 * derived after authentication from the Memberships the server authorises for
 * the account, so a build is not tied to one couple and a demo persona works
 * without a rebuild.
 *
 * `docs/AGENTS.md` states the rule this follows — normal couples must not need
 * to configure technical values, and a Space ID is one.
 */
data class ReferenceConfig(
    val apiBaseUrl: String,
) {
    val isConfigured: Boolean
        get() = apiBaseUrl.isNotBlank()

    companion object {
        fun fromBuildConfig(): ReferenceConfig =
            ReferenceConfig(apiBaseUrl = BuildConfig.SBS_API_BASE_URL.trimEnd('/'))
    }
}
