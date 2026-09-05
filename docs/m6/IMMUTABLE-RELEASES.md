# M6 immutable release engineering

**Owner:** #519  
**Depends on:** #190, #193, #194, #375  
**Gate:** G4 is already passed; G5 consumes the final release evidence.

This document records the #519 release-engineering and Android publication decisions.
It deliberately keeps release identity, signing custody and rollback selection separate
from database recovery.

## Decision: build once, publish immutable artifacts

For launch, SideBySide uses **build-once release artifacts** while keeping #375's exact
commit SHA as the source identity.

The v1 packaging boundary is:

- one backend image archive shared by API, worker and migrate;
- one Web image archive;
- final signed Android APK/AAB for the selected distribution channel;
- SPDX 2.3 JSON SBOMs and GitHub Artifact Attestations from #193;
- one machine-readable release manifest plus checksums;
- one Git tag `v<product-version>` pointing to the exact release commit;
- one GitHub Release containing the complete immutable artifact/evidence set.

Cloud/Managed may later load the exact released image archives and push them to a
registry, recording immutable registry digests as additional transport identities.
The product is not rebuilt for that promotion. Self-Hosted retains the #375 verified
source path and the released image-archive path. Neither mode identifies Production
by mutable `main`.

## Version policy

Launch versions use SemVer and have exactly two human-facing representations:

- product version / Android `versionName`: `MAJOR.MINOR.PATCH` with an intentional
  SemVer prerelease/build suffix only when needed;
- Git tag: `v<product-version>`.

`android/app/build.gradle.kts` remains authoritative for `versionName` per #194. A
release fails when the requested product version differs from that value.

Android `versionCode` is a positive monotonically increasing integer supplied by the
publishing workflow. It is not derived from SemVer and is not a second product
version.

## Release identity

`scripts/release_manifest.py` consumes the exact #193 `evidence-index.json` and
creates one schema-v1 release manifest. It rejects:

- a non-SemVer product version;
- a non-immutable source SHA;
- a backend artifact that does not jointly cover API, worker and migrate;
- a missing/mixed backend, Web, APK or AAB set;
- Android application IDs other than `de.sidebyside.app`;
- Android `versionName` differing from the product version;
- unsafe artifact paths or invalid digests;
- final-publication verification when Android is not `signed-release`.

The manifest contains no credential, token, signing key, `.env` value, user content or
provider secret.

## Previous known-good release

The previous-known-good identity is never a free-form operator SHA. For every
non-initial release, the workflow downloads `sidebyside-release-manifest.json` from an
explicitly selected previous GitHub Release and records:

- previous product version;
- previous release tag;
- previous immutable source revision;
- SHA-256 of the previous manifest.

The final publication path accepts only a previously published release as the rollback
reference. G5 must not treat an unsigned release candidate as known-good Production.

## Database rollback boundary

Every release manifest states:

- application release selection is independent from database recovery;
- database rollback is **not implied**;
- schema compatibility review is required;
- #190 and #375 remain authoritative for forward-fix, downgrade and restore choices.

An operator must not start an old application merely because its release assets are
available. If the current schema is not backward-compatible, use the explicitly tested
forward-fix/downgrade path or restore the coordinated recovery point according to
#190/#375.

## Candidate workflow

`.github/workflows/release-candidate.yml` remains the unprivileged immutable candidate
workflow. It is manual-only for real candidates and has no `contents: write`
permission.

It:

1. calls the #193 reusable evidence workflow;
2. builds backend/Web and unsigned Android release candidates from one exact SHA;
3. produces SPDX SBOMs and attestations;
4. binds version, source SHA, artifact digests and previous-known-good identity into a
   candidate manifest;
5. verifies all artifact/SBOM digests;
6. uploads an immutable candidate bundle.

An unsigned Android candidate is never a launch/store artifact.

## Android signing and Play decision

The release-owner decision is now fixed for the first launch.

### App-signing model

- **Google Play App Signing is enabled** for the production application-signing key.
- SideBySide release automation uses a **distinct upload key**.
- The application-signing key is not stored in GitHub, the repository or operator
  backups; Google Play owns that key boundary.
- The upload key is the only Android private key consumed by SideBySide release
  automation.

### Online custody

The approved online custody point is the protected GitHub Actions environment:

`production-release`

For the first launch, environment approval/use is restricted to the repository release
owner. Additional approvers may be added only deliberately as release responsibility
is delegated.

The environment supplies exactly these signing secrets:

- `SBS_RELEASE_KEYSTORE_BASE64` — base64-encoded upload keystore;
- `SBS_RELEASE_KEYSTORE_PASSWORD`;
- `SBS_RELEASE_KEY_ALIAS`;
- `SBS_RELEASE_KEY_PASSWORD`.

Repository-level secrets are not the approved custody point for these values. The
workflow materializes the keystore only under `$RUNNER_TEMP`, uses it for the Gradle
release-signing step and removes it when that step exits. No signing secret is copied
into release evidence, artifacts, logs, SBOMs, manifests or release notes.

The GitHub environment itself and its secret values are operator configuration and are
not represented in repository files. Before the first real publication, G5/#524 must
verify that the environment is protected, the expected approver policy is active and
all four secrets are present.

### Offline recovery / escrow

The human release owner keeps one encrypted offline recovery copy of the **upload
key**, plus the alias and recovery procedure, in a location independent from GitHub.
Passwords protecting that copy must not be stored next to an unencrypted keystore.

If the online upload key is lost but the offline copy is intact, restore the protected
GitHub environment from that copy and rotate credentials afterward if exposure is
suspected.

If the upload key is lost or compromised and no trustworthy copy remains, use Google
Play's supported upload-key reset/rotation process. Do not replace the package identity
or create a second Play application as an ad-hoc recovery mechanism.

Loss/rotation of the Google-held application-signing key follows Google Play App
Signing's platform recovery/support process; SideBySide does not invent a second key
escrow mechanism for it.

## Protected final publication workflow

`.github/workflows/release-publish.yml` is the only repository workflow allowed to
turn a candidate source revision into a final launch release.

The workflow is fail-closed and uses three boundaries before publication:

### 1. Unprivileged preflight

Before requesting access to signing material, it verifies:

- explicit `confirm_publish=true` operator intent;
- the exact source SHA is reachable from `main`;
- existing CI/security checks for that SHA are completed without failure;
- the requested tag and GitHub Release do not already exist;
- product version matches the frozen Android `versionName`;
- previous-known-good selection is valid, or the operator explicitly marks the initial
  release;
- #193 artifact transport checksums are intact.

### 2. Protected signing and final evidence

Only after preflight succeeds does the `production-release` job start.

It:

1. materializes the upload keystore only in `$RUNNER_TEMP`;
2. builds APK and AAB from the same `github.sha` and supplied monotonic `versionCode`;
3. verifies APK/AAB signatures and checks APK application ID, `versionName` and
   `versionCode`;
4. removes the unsigned Android candidate from the final evidence set;
5. regenerates Android SPDX SBOMs for the **signed bytes**;
6. replaces Android digests in `evidence-index.json` and marks signing as
   `signed-release`;
7. discards unsigned Android attestation bundles and creates fresh provenance/SBOM
   attestations for the signed APK/AAB;
8. re-verifies retained backend/Web attestations and the new signed Android
   attestations;
9. builds and verifies the final release manifest with
   `--require-signed-android`;
10. writes and verifies final checksums and human-readable release notes.

Backend/Web are not rebuilt in the protected job; the exact #193 build-once artifacts
are retained. Only Android must be rebuilt because signing changes its final bytes.

### 3. Immutable publication

Immediately before write access is used, the workflow rechecks that the release tag
and GitHub Release are still unused. It then:

- creates `v<version>` at exactly `github.sha`;
- publishes the complete release-evidence directory as GitHub Release assets;
- downloads the published release manifest again;
- confirms the tag resolves to the original source SHA and the published manifest is
  byte-identical to the locally verified one.

The workflow never overwrites an existing release identity.

## GitHub environment setup before first publication

This repository intentionally cannot create or populate signing secrets itself. The
release owner must configure GitHub before the first production run:

1. create/protect the `production-release` environment;
2. require explicit deployment approval by the release owner;
3. add the four environment secrets listed above;
4. generate/store the encrypted offline upload-key recovery copy independently;
5. enable Google Play App Signing and register the matching upload certificate in the
   Play Console;
6. execute the first publication only through `Publish Immutable Release` after normal
   launch gates are green.

If any of these conditions is absent, the workflow must fail rather than falling back
to debug signing, unsigned publication or a repository secret.

## Self-Hosted and Cloud/Managed

Both operating models consume the same release identity:

`product version -> Git tag -> immutable source SHA -> release manifest -> artifact digests`

Self-Hosted may deploy the released archives directly or use the verified-source path
from #375. Cloud/Managed may promote the exact archives to an OCI registry and record
registry digests, but must not rebuild them. Commercial entitlement state is unrelated
to artifact identity.

## Focused test contract

`tools/ci/test_release_manifest.py` covers release-manifest invariants.

`tools/ci/test_release_publish_workflow.py` covers the privileged publication boundary,
including:

- no privileged `pull_request_target` path;
- protected environment and least-privilege permissions;
- explicit publish confirmation and source-on-main requirement;
- CI/tag/release preflight;
- environment-only ephemeral signing material;
- signed Android identity verification;
- fresh SBOM/attestation generation for signed bytes;
- final `--require-signed-android` verification;
- immutable GitHub Release/tag publication;
- immutable pins for external Actions and the Syft binary.

Normal repository CI/security/privacy/reuse/supply-chain gates remain authoritative for
the application revision. G5/#524 performs the real operator rehearsal and captures
the protected-environment/publication evidence.
