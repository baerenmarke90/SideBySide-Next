plugins {
    id("com.android.application")
    id("org.jetbrains.kotlin.plugin.compose")
    id("org.jetbrains.kotlin.plugin.serialization")
}

val sbsApiBaseUrl = providers.gradleProperty("sbsApiBaseUrl").orElse("").get()
val sbsSpaceId = providers.gradleProperty("sbsSpaceId").orElse("").get()
val preparedGeneratedModels = layout.buildDirectory.dir("generated/s8ApiModels")
val prepareS8GeneratedModels by tasks.registering(org.gradle.api.tasks.Sync::class) {
    from(layout.projectDirectory.dir("../api/generated"))
    into(preparedGeneratedModels)
    // The generator-owned passkey request models use Map<String, Any>. They
    // are outside this M2-S8 slice and kotlinx.serialization cannot generate
    // a concrete Any serializer. Keep the source files untouched and compile
    // the generated contract surface S8 actually consumes.
    exclude(
        "sidebyside/api/models/PasskeyAuthenticationRequest.kt",
        "sidebyside/api/models/PasskeyRegistrationRequest.kt",
    )
}

fun quotedBuildConfig(value: String): String = "\"${value.replace("\\", "\\\\").replace("\"", "\\\"")}\""

android {
    namespace = "de.sidebyside.next.reference"
    compileSdk = 37
    compileSdkMinor = 1

    defaultConfig {
        applicationId = "de.sidebyside.next.reference"
        minSdk = 26
        targetSdk = 36
        versionCode = 1
        versionName = "0.0.1-m2-s8"

        testInstrumentationRunner = "androidx.test.runner.AndroidJUnitRunner"
        buildConfigField("String", "SBS_API_BASE_URL", quotedBuildConfig(sbsApiBaseUrl))
        buildConfigField("String", "SBS_SPACE_ID", quotedBuildConfig(sbsSpaceId))
    }

    buildFeatures {
        buildConfig = true
        compose = true
    }

    compileOptions {
        sourceCompatibility = JavaVersion.VERSION_17
        targetCompatibility = JavaVersion.VERSION_17
    }

    testOptions {
        unitTests.isIncludeAndroidResources = true
    }
}

android.sourceSets.named("main") {
    kotlin.directories += preparedGeneratedModels.get().asFile.path
}

tasks.named("preBuild").configure {
    dependsOn(prepareS8GeneratedModels)
}

dependencies {
    val composeBom = platform("androidx.compose:compose-bom:2026.08.00")

    implementation(composeBom)
    implementation("androidx.activity:activity-compose:1.13.0")
    implementation("androidx.lifecycle:lifecycle-viewmodel-compose:2.11.0")
    implementation("androidx.compose.ui:ui")
    implementation("androidx.compose.ui:ui-tooling-preview")
    implementation("androidx.compose.material3:material3")
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
