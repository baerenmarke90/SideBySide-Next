package de.sidebyside.next.reference

import java.util.UUID

data class ReferenceConfig(
    val apiBaseUrl: String,
    val spaceId: UUID?,
) {
    val isConfigured: Boolean
        get() = apiBaseUrl.isNotBlank() && spaceId != null

    companion object {
        fun fromBuildConfig(): ReferenceConfig {
            val spaceIdValue = BuildConfig.SBS_SPACE_ID.trim()
            return ReferenceConfig(
                apiBaseUrl = BuildConfig.SBS_API_BASE_URL.trimEnd('/'),
                spaceId = if (spaceIdValue.isBlank()) {
                    null
                } else {
                    runCatching { UUID.fromString(spaceIdValue) }.getOrNull()
                },
            )
        }
    }
}
