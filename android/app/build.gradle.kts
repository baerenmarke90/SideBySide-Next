plugins {
    id("com.android.application")
    id("org.jetbrains.kotlin.plugin.compose")
    id("org.jetbrains.kotlin.plugin.serialization")
}

val sbsApiBaseUrl = providers.gradleProperty("sbsApiBaseUrl").orElse("").get()

// Release identity, per #194.
//
// `versionName` is the product's version and is edited by hand when the
// product moves. `versionCode` is the monotonic integer Android orders updates
// by; it carries no meaning beyond "later than the last one" and is supplied by
// whatever publishes the build, so a rebuild of the same source can be
// republished without inventing a new product version.
val sbsVersionName = "0.1.0"
val sbsVersionCode = providers.gradleProperty("sbsVersionCode").orElse("1").get().toInt()

// Release signing material never lives in this repository. It is supplied by
// the publishing environment, and when it is absent the release build stays
// unsigned rather than silently falling back to the debug key — an artifact
// signed with the debug key looks releasable and can never be updated by a
// properly signed one.
val releaseKeystore = providers.gradleProperty("sbsReleaseKeystore")
    .orElse(providers.environmentVariable("SBS_RELEASE_KEYSTORE"))
    .orNull
// The Material 3 scheme and the semantic scale are derived from the shared
// token set instead of restating its values. `design/tokens.json` stays the
// single source of truth, exactly as `backend/openapi.json` is for the API
// client. Gradle bundles Groovy, so parsing needs no additional dependency.
abstract class GenerateDesignTokens : DefaultTask() {
    @get:InputFile
    abstract val tokensFile: RegularFileProperty

    @get:OutputDirectory
    abstract val outputDirectory: DirectoryProperty

    // The design-token format names its payload key "$value".
    private val valueKey = "\u0024value"

    @TaskAction
    fun generate() {
        val parsed = groovy.json.JsonSlurper().parse(tokensFile.get().asFile)
        val tokens = parsed.asMap()
        val color = tokens.getValue("color").asMap()
        val scheme = color.getValue("scheme").asMap()
        val semantic = color.getValue("semantic").asMap()

        val text = buildString {
            appendLine("package de.sidebyside.next.design")
            appendLine()
            appendLine("// Generated from design/tokens.json by the generateDesignTokens task.")
            appendLine("// Do not edit; change the token file instead.")
            appendLine()
            appendLine("internal object GeneratedColorTokens {")
            appendColorObject("Light", resolveScheme(scheme, semantic, "light"))
            appendColorObject("Dark", resolveScheme(scheme, semantic, "dark"))
            appendLine("}")
            appendLine()
            appendDimensionObject(tokens)
            appendLine()
            appendTypographyObject(tokens)
        }

        val target = outputDirectory.get().asFile.resolve("de/sidebyside/next/design")
        target.mkdirs()
        target.resolve("GeneratedDesignTokens.kt").writeText(text)
    }

    /** Scheme entries are aliases such as `{color.semantic.background}`. */
    private fun resolveScheme(
        scheme: Map<String, Any?>,
        semantic: Map<String, Any?>,
        name: String,
    ): Map<String, String> {
        val entries = scheme.getValue(name).asMap()
        val resolved = LinkedHashMap<String, String>()
        for ((key, raw) in entries) {
            val value = raw.asMap().getValue(valueKey) as String
            resolved[key] = if (value.startsWith("{")) {
                val alias = value.trim('{', '}').substringAfterLast('.')
                val target = semantic[alias]
                    ?: throw GradleException("Token alias cannot be resolved: " + value)
                target.asMap().getValue(valueKey) as String
            } else {
                value
            }
        }
        return resolved
    }

    private fun StringBuilder.appendColorObject(name: String, entries: Map<String, String>) {
        appendLine("    object " + name + " {")
        for ((key, hex) in entries) {
            appendLine("        const val " + constantName(key) + ": Long = 0x" + argb(hex))
        }
        appendLine("    }")
        appendLine()
    }

    /** Token colours are `#RRGGBB` or `#RRGGBBAA`; Compose expects `AARRGGBB`. */
    private fun argb(hex: String): String {
        val value = hex.removePrefix("#").uppercase()
        return when (value.length) {
            6 -> "FF" + value
            8 -> value.substring(6, 8) + value.substring(0, 6)
            else -> throw GradleException("Unsupported colour token: " + hex)
        }
    }

    private fun StringBuilder.appendDimensionObject(tokens: Map<String, Any?>) {
        appendLine("internal object GeneratedDimensionTokens {")
        appendScale(tokens.getValue("spacing").asMap(), "SPACING_")
        appendScale(tokens.getValue("radius").asMap(), "RADIUS_")
        appendLine("}")
    }

    private fun StringBuilder.appendScale(entries: Map<String, Any?>, prefix: String) {
        for ((key, raw) in entries) {
            if (!raw.isTokenValue()) continue
            val size = (raw.asMap().getValue(valueKey) as String).removeSuffix("px")
            appendLine("    const val " + prefix + constantName(key) + ": Float = " + size + "f")
        }
    }

    private fun StringBuilder.appendTypographyObject(tokens: Map<String, Any?>) {
        appendLine("internal object GeneratedTypographyTokens {")
        for ((key, raw) in tokens.getValue("typography").asMap()) {
            if (!raw.isTokenValue()) continue
            val value = raw.asMap().getValue(valueKey).asMap()
            val fontSize = (value.getValue("fontSize") as String).removeSuffix("px")
            val lineHeight = (value.getValue("lineHeight") as Number).toFloat()
            val fontWeight = (value.getValue("fontWeight") as Number).toInt()
            val letterSpacing = (value.getValue("letterSpacing") as String).removeSuffix("em")
            appendLine("    object " + key.replaceFirstChar { it.uppercaseChar() } + " {")
            appendLine("        const val FONT_SIZE_SP: Float = " + fontSize + "f")
            appendLine("        const val LINE_HEIGHT_RATIO: Float = " + lineHeight + "f")
            appendLine("        const val FONT_WEIGHT: Int = " + fontWeight)
            appendLine("        const val LETTER_SPACING_EM: Float = " + letterSpacing + "f")
            appendLine("    }")
        }
        appendLine("}")
    }

    @Suppress("UNCHECKED_CAST")
    private fun Any?.asMap(): Map<String, Any?> =
        this as? Map<String, Any?> ?: throw GradleException("Expected a token object.")

    private fun Any?.isTokenValue(): Boolean = this is Map<*, *> && containsKey(valueKey)

    private fun constantName(key: String): String =
        key.replace(Regex("([a-z0-9])([A-Z])"), "$1_$2").uppercase()
}

val generatedDesignTokens = layout.buildDirectory.dir("generated/designTokens")
val generateDesignTokens by tasks.registering(GenerateDesignTokens::class) {
    tokensFile.set(layout.projectDirectory.file("../../design/tokens.json"))
    outputDirectory.set(generatedDesignTokens)
}

val preparedGeneratedModels = layout.buildDirectory.dir("generated/s8ApiModels")
val prepareS8GeneratedModels by tasks.registering(org.gradle.api.tasks.Sync::class) {
    from(layout.projectDirectory.dir("../api/generated"))
    into(preparedGeneratedModels)
}

fun quotedBuildConfig(value: String): String = "\"${value.replace("\\", "\\\\").replace("\"", "\\\"")}\""

/**
 * One piece of signing material, from a Gradle property or the environment.
 *
 * Missing material fails the configuration rather than producing a signing
 * config with an empty password, which fails much later and less clearly.
 */
fun Project.secret(property: String, environmentVariable: String): String =
    providers.gradleProperty(property)
        .orElse(providers.environmentVariable(environmentVariable))
        .orNull
        ?: error(
            "Release signing needs $property or $environmentVariable. " +
                "Supply it from the publishing environment; it must never be committed.",
        )

android {
    namespace = "de.sidebyside.next.reference"
    compileSdk = 37
    compileSdkMinor = 1

    defaultConfig {
        // Frozen by #194. Google Play binds an application ID to its listing
        // permanently, so this cannot be corrected after a first release —
        // which is why the M2 name `de.sidebyside.next.reference` had to go
        // before distribution rather than after. `reference` named a technical
        // flow and `next` is this repository's codename; neither is the
        // product.
        applicationId = "de.sidebyside.app"
        minSdk = 26
        targetSdk = 36
        versionCode = sbsVersionCode
        versionName = sbsVersionName

        testInstrumentationRunner = "androidx.test.runner.AndroidJUnitRunner"
        buildConfigField("String", "SBS_API_BASE_URL", quotedBuildConfig(sbsApiBaseUrl))
    }

    signingConfigs {
        if (releaseKeystore != null) {
            create("release") {
                storeFile = file(releaseKeystore)
                storePassword = secret("sbsReleaseKeystorePassword", "SBS_RELEASE_KEYSTORE_PASSWORD")
                keyAlias = secret("sbsReleaseKeyAlias", "SBS_RELEASE_KEY_ALIAS")
                keyPassword = secret("sbsReleaseKeyPassword", "SBS_RELEASE_KEY_PASSWORD")
            }
        }
    }

    buildTypes {
        debug {
            // A debug build is a different application to Android, so a
            // developer's own installation cannot be replaced by, or replace,
            // the one from the store.
            applicationIdSuffix = ".debug"
            versionNameSuffix = "-debug"
        }

        release {
            signingConfig = signingConfigs.findByName("release")
            isMinifyEnabled = false
        }
    }

    buildFeatures {
        buildConfig = true
        compose = true
    }

    compileOptions {
        sourceCompatibility = JavaVersion.VERSION_17
        targetCompatibility = JavaVersion.VERSION_17
    }

    androidResources {
        // Keeps AndroidX and Material from bringing roughly eighty of their own
        // translations into the package. Without it a device set to any other
        // language resolves library strings — dialog buttons, content
        // descriptions, the text a screen reader announces — to that language
        // while every string this app owns stays German.
        localeFilters += "de"
    }

    testOptions {
        unitTests.isIncludeAndroidResources = true
    }
}

android.sourceSets.named("main") {
    kotlin.directories += preparedGeneratedModels.get().asFile.path
    kotlin.directories += generatedDesignTokens.get().asFile.path
}

tasks.named("preBuild").configure {
    dependsOn(prepareS8GeneratedModels, generateDesignTokens)
}

dependencies {
    val composeBom = platform("androidx.compose:compose-bom:2026.08.00")

    implementation(composeBom)
    implementation("androidx.activity:activity-compose:1.13.0")
    implementation("androidx.lifecycle:lifecycle-viewmodel-compose:2.11.0")
    implementation("androidx.compose.ui:ui")
    implementation("androidx.compose.ui:ui-tooling-preview")
    implementation("androidx.compose.material3:material3")
    implementation("androidx.navigation:navigation-compose:2.10.0")
    implementation("com.squareup.okhttp3:okhttp:5.4.0")
    implementation("org.jetbrains.kotlinx:kotlinx-coroutines-android:1.11.0")
    implementation("org.jetbrains.kotlinx:kotlinx-serialization-json:1.11.0")

    debugImplementation("androidx.compose.ui:ui-tooling")
    debugImplementation("androidx.compose.ui:ui-test-manifest")

    testImplementation(composeBom)
    testImplementation("junit:junit:4.13.2")
    testImplementation("androidx.test:core:1.7.0")
    testImplementation("androidx.compose.ui:ui-test-junit4")
    testImplementation("org.jetbrains.kotlinx:kotlinx-coroutines-test:1.11.0")
    testImplementation("org.robolectric:robolectric:4.16.1")
}
