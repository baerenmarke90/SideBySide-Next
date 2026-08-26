package de.sidebyside.next.reference

import java.util.UUID

data class ReferenceConfig(
    val apiBaseUrl: String,
    val spaceId: UUID?,
) {
    val isConfigured: Boolean
        get() = apiBaseUrl.isNotBlank() && spaceId != null

    companion object {
        fun fromBuildConfig(): ReferenceConfig = ReferenceConfig(
            apiBaseUrl = BuildConfig.SBS_API_BASE_URL.trimEnd('/'),
            spaceId = BuildConfig.SBS_SPACE_ID.takeIf(String::isNotBlank)?.let {
                runCatching(UUID::fromString).getOrNull()
            },
        )
    }
}
