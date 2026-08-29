# Android

The native Kotlin/Jetpack Compose client is intended to become fully
productized in M5. For **M2-S8 / G2**, it deliberately starts with only a thin
vertical reference flow. It proves the same Memory/Image/Story contract as the
Web slice without pulling navigation, offline sync, or client parity forward.

Android communicates exclusively with the shared Application Core through the
versioned REST/OpenAPI interface and contains no independent domain or privacy
logic.

## Generated API models

`api/generated/` contains the Kotlin data classes generated from
`backend/openapi.json` and is **not edited manually**. Regenerate it with
`tools/openapi/generate.sh`; CI verifies the committed output against the
contract.

For the S8 build, an unchanged temporary compile source root is prepared under
`app/build/generated/`. This unrelated slice omits the two generator-owned
Passkey request models that use `Map<String, Any>` from the compile copy because
kotlinx.serialization cannot produce a concrete `Any` serializer for them.
Issue #138 tracks this generator finding separately; the source files remain
unchanged. Every DTO required for S8, especially the `StoryItem` union fixed by
#119, still comes directly from the generated contract. There is no second,
handwritten DTO layer.

## M2-S8 reference flow

The slice executes exactly one critical flow:

1. password sign-in against `/api/v1/auth/sign-in`;
2. keep the bearer token exclusively in ephemeral ViewModel state;
3. create a Memory against the published contract;
4. select an image through Android Photo Picker;
5. execute an `UploadDescriptor` for `STREAM` or `SIGNED_UPLOAD`;
6. finalize the upload and poll until `READY`;
7. bind the attachment to the Memory with `If-Match`;
8. load the shared `/timeline` and process the generated `StoryItem`;
9. execute an authorized `ReadDescriptor` and display the image minimally.

For `STREAM`, the bearer token is sent to the SideBySide API. For
`SIGNED_UPLOAD`/`SIGNED_URL`, it is deliberately **not** forwarded to the
storage endpoint. The app manifest does not permit cleartext connections, so
real remote operation uses HTTPS.

## Operator configuration

Normal users do not enter technical URLs or IDs. The reference flow receives
these values as Gradle properties at build time:

```bash
./gradlew -PsbsApiBaseUrl=https://sidebyside.example \
  -PsbsSpaceId=00000000-0000-0000-0000-000000000000 \
  :app:assembleDebug
```

Without valid configuration, the UI shows only a clear operator notice and
sends no API request.

## Reproducible Gradle build

The committed Gradle Wrapper is the only supported Gradle entry point for
Android. The project currently pins **Gradle 9.5.0**, AGP 9.3.0, and JDK 17.
`gradle/wrapper/gradle-wrapper.properties` binds the Gradle 9.5.0 binary
distribution to its official SHA-256; CI additionally verifies the committed
Wrapper JAR against its official SHA-256. CI uses
`gradle/actions/setup-gradle` only for caching and Wrapper validation, not to
install a separate Gradle version.

With JDK 17 and Android SDK 37.1 installed:

```bash
./gradlew --version
./gradlew --no-daemon --dependency-verification strict :app:testDebugUnitTest
./gradlew --no-daemon --dependency-verification strict :app:lintDebug
./gradlew --no-daemon --dependency-verification strict :app:assembleDebug
```

Gradle Dependency Verification uses `gradle/verification-metadata.xml`.
Gradle's default mode is already `strict`; CI also sets the mode explicitly.
The file contains concrete SHA-256 values for the build, plugin, test, and
runtime artifacts that are actually resolved. There are no wildcards or broad
trust exceptions. Signature verification is currently disabled because the
used Google Maven and Maven Central artifacts do not provide consistent PGP
coverage across the whole graph. Complete SHA-256 verification therefore
avoids exceptions for unsigned artifacts. CI runs a negative test that changes
checksums only in the working copy and proves that Gradle subsequently rejects
the build through Dependency Verification.

### Updating the Wrapper

Wrapper upgrades are security-sensitive and must include an explicit Gradle/AGP
compatibility review. First verify the new distribution and Wrapper JAR
checksums independently against Gradle's official release checksum page. Then,
from `android/`:

```bash
./gradlew wrapper \
  --gradle-version <VERSION> \
  --distribution-type bin \
  --gradle-distribution-sha256-sum <OFFICIAL_BIN_SHA256>
sha256sum gradle/wrapper/gradle-wrapper.jar
```

Then update the expected Wrapper JAR SHA in the Android CI workflows, review the
complete Wrapper diff, and run every Android and G2 gate. Never accept a Wrapper
JAR from an unofficial source.

### Maintaining Dependency Verification

A legitimate dependency change initially fails as expected on an unapproved
artifact. After reviewing the change's coordinate, version, and source, extend
the metadata file with Gradle's native function:

```bash
./gradlew --write-verification-metadata sha256 \
  :app:testDebugUnitTest :app:lintDebug :app:assembleDebug
```

Do **not** accept the resulting `gradle/verification-metadata.xml` blindly.
Review the diff for unexpected components or versions, additional artifacts,
wildcards, or trust exceptions. Then rerun a normal strict build and the CI
negative test. Remove obsolete entries during dependency changes so the file
remains a narrow allowlist.

### Dependency Locking

Dependency Locking was considered for #185 and deliberately not added. The
current Android build uses no dynamic versions, version ranges, or `SNAPSHOT`
dependencies; direct versions and the Compose BOM are pinned. Strict
verification metadata also prevents newly resolved, unapproved transitive
artifacts from entering silently. Lockfiles would maintain a second,
configuration-heavy version state for the current scope without further
reducing the concrete #185 risk. Re-evaluate locking separately if dynamic
versions or other reproducibility requirements arise.

Focused tests cover flow orchestration, bearer separation for stream and signed
descriptors, real `StoryItem` deserialization, and Compose semantics at a large
system font scale.

## Deliberate S8 boundaries

- no persistent token, read, or offline cache;
- no Room/Paging and no WorkManager;
- no complete navigation or deep links;
- no offline write sync;
- no export/import and no global search;
- no Wishes/Plans/Places/Private Area or M3+ features;
- no video; #88 remains in the future backlog.

These items belong to later, explicitly approved milestones and are not decided
implicitly by the technical G2 proof.
