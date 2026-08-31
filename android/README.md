# Android

The native Kotlin/Jetpack Compose client is being productized in M5, planned in
`docs/m5/ANDROID-DELIVERY-PLAN.md` under #350. The **M2-S8 / G2** vertical
reference flow below still runs and remains the G2 evidence; the M5 slices
replace it surface by surface rather than removing it up front.

The M2-S8 slice proves the same Memory/Image/Story contract as the Web slice
without pulling navigation, offline sync, or client parity forward.

Android communicates exclusively with the shared Application Core through the
versioned REST/OpenAPI interface and contains no independent domain or privacy
logic.

## Design foundation

`design/tokens.json` is the single source of truth for colour, spacing, radius
and typography, in the same way `backend/openapi.json` is for the API client.
The `generateDesignTokens` Gradle task reads it and writes
`GeneratedDesignTokens.kt` into `app/build/generated/designTokens`; that file is
generated, not committed, and must not be edited.

`de.sidebyside.next.design` turns those values into the semantic layer the app
consumes:

- `SideBySideColors` carries the product roles Material 3 has no slot for —
  shared, private, discovery, header surface — and `SideBySideTheme` derives the
  Material 3 scheme from them in one mapping;
- `SideBySideSpacing` and `SideBySideRadii` expose the 4-unit grid by step name;
- `SideBySideTypography` maps the token scale onto Material roles, resolving the
  token line-height ratios and `em` letter spacing against the token font size.

`DesignTokenTest` parses `design/tokens.json` directly and asserts that the
generated layer still matches it, so a generator regression fails the build
instead of shipping a stale palette. The same test checks WCAG AA contrast for
every text-on-surface and text-on-accent pair in both schemes.

Appearance follows the system. A manual light/dark override would have to
persist a preference, which needs storage that no delivered slice adds yet.

The token file names `Inter` and `Fraunces`. Neither face is delivered with the
app, so both resolve to their documented fallbacks. Delivering them is a
provider decision with licensing, size and privacy consequences and has not been
made.

## Application shell

`de.sidebyside.next.shell` owns the two things a screen cannot get right on its
own.

**Window insets.** `targetSdk` 36 means the system draws the app edge to edge
and hands back responsibility for the status bar, navigation bar, display
cutout and keyboard. `AppShell` consumes `WindowInsets.safeDrawing` through its
`Scaffold`, and `ShellSurface` does the same for surfaces shown before there is
anything to navigate between. A screen that bypasses both ends up underneath
the clock.

**Navigation.** `AppDestination` is the registry; its route IDs and order come
from `docs/decisions/0003-primary-navigation-and-route-model.md`, so Web and
Android address the same destinations and a Deep Link registry can be built on
one mapping. Bottom navigation at every window size, from one list; see
`docs/decisions/0004-android-uses-bottom-navigation-at-every-size.md`. A rail or
sidebar would spend width the content needs on a handful of destinations, and on
a foldable it would move where the user reaches each time the device opens. The
window size class still selects the content composition.

A destination is only rendered once it has something to show. `declaredDestinations`
is the full contract; the shell receives the implemented subset, so an area
still being built never appears as an empty tab. `discover` stays reserved for
M7 and is not declared as a destination at all.

The active destination is drawn in brand purple rather than the Material
default: Material fills its selection indicator from `secondaryContainer`,
which this product maps to the shared mint, and mint means shared and confirmed
(`docs/DESIGN-PRINCIPLES.md` 3.1).

`problemFor` maps a failure to one of the shared system states. It returns
string resources only — a ProblemDetails `detail` may name resources or
internal reasons and never reaches the user — and 403 and 404 deliberately
share one state so the difference cannot disclose that a resource exists.

## Demo mode

The entry screen offers the public demo alongside sign-in. Entering it points
the session at `DemoEndpoint.BASE_URL` for that session only; the configured
production or Self-Hosted endpoint is never rewritten, so leaving the demo
returns to it unchanged.

The server issues a one-time proof for a persona rather than a password, so no
reusable credential exists in the app, the source or the assets.
`POST /api/v1/demo/entry` is deliberately absent from the OpenAPI contract — it
is a facility of the isolated demo deployment, not a supported authentication
method for a normal installation — so it is the one call in this client written
by hand instead of generated.

The demo Space comes from the account's memberships rather than from the build
configuration, because a persona's Space cannot be known at build time. Only an
`ACTIVE` membership is accepted. #353 replaces the build-time Space for the
ordinary sign-in path as well.

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

Normal users do not enter technical URLs or IDs. The only operator value is the
address of the server:

```bash
./gradlew -PsbsApiBaseUrl=https://sidebyside.example :app:assembleDebug
```

Without it, the UI shows a clear operator notice and sends no API request.

**The Space is not configured.** It is derived after authentication from the
Memberships the server authorises for the account, so one build serves every
couple and a demo persona needs no rebuild. Only an `ACTIVE` membership counts;
an account with none is signed in but has nothing to open, which is a product
state rather than a sign-in failure.

Where an account is active in more than one Space, all of them are offered and
switching drops everything bound to the previous one — drafts, the loaded Story,
and any request still in flight, which would otherwise write into the wrong
couple's Space.

## Release identity

Decided by #194, before any distribution build, because Google Play binds an
application ID to its listing permanently and the M2 name would then have been
frozen as the product's.

| | |
| --- | --- |
| Application ID | `de.sidebyside.app` |
| Debug application ID | `de.sidebyside.app.debug` |
| `versionName` | the product's version, edited by hand when the product moves |
| `versionCode` | supplied by the publisher as `-PsbsVersionCode=<n>` |

`reference` named a technical flow and `next` is this repository's codename;
neither is the product, so neither is in the released identity. The Kotlin
package root is still `de.sidebyside.next.*`. That is internal — it decides
where the `R` and `BuildConfig` classes live and nothing a store or a device
sees — and renaming it is a separate mechanical change.

A debug build carries its own suffix so it is a different application to
Android. Without that, a build from this checkout would replace an installed
release, or refuse to install beside it.

`versionCode` is only an ordering: Android needs each update to carry a higher
integer than the one before, and it means nothing else. Keeping it out of the
build file lets the same source be republished without inventing a new product
version.

### Release signing

Signing material never lives in this repository. It is supplied by whatever
publishes the build, as Gradle properties or environment variables:

| Property | Environment variable |
| --- | --- |
| `sbsReleaseKeystore` | `SBS_RELEASE_KEYSTORE` |
| `sbsReleaseKeystorePassword` | `SBS_RELEASE_KEYSTORE_PASSWORD` |
| `sbsReleaseKeyAlias` | `SBS_RELEASE_KEY_ALIAS` |
| `sbsReleaseKeyPassword` | `SBS_RELEASE_KEY_PASSWORD` |

```bash
./gradlew -PsbsApiBaseUrl=https://sidebyside.example \
  -PsbsVersionCode=42 \
  -PsbsReleaseKeystore=/secure/path/release.jks \
  :app:assembleRelease
```

Two failure modes are deliberate. With no keystore at all, the release build
produces `app-release-unsigned.apk` rather than falling back to the debug key —
an artifact signed with the debug key looks releasable and can never be
replaced by a properly signed update. With a keystore but incomplete
credentials, configuration fails immediately and names the missing value,
instead of building something that fails at install time.

`*.jks`, `*.keystore` and `keystore.properties` are ignored by git.

**Still open, and needed before a first store release:** who holds the upload
key, whether Play App Signing is used, and where the key is escrowed. That is
an operational decision with no code in it, and it is not made here.

## Reproducible Gradle build

The committed Gradle Wrapper is the only supported Gradle entry point for
Android. The project currently pins **Gradle 9.5.0**, AGP 9.3.0, and JDK 17.
`gradle/wrapper/gradle-wrapper.properties` binds the Gradle 9.5.0 binary
distribution to its official SHA-256; CI additionally verifies the committed
Wrapper JAR against its official SHA-256. CI uses
`gradle/actions/setup-gradle` only for caching and Wrapper validation, not to
install a separate Gradle version.

With JDK 17 and Android SDK 37.1 installed:

On a non-Linux workstation, `--dependency-verification strict` fails on the
platform-specific `aapt2` artifact, because the committed metadata covers the
Linux artifact CI resolves. Use `--dependency-verification lenient` locally and
leave the metadata unchanged; CI remains strict.

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
