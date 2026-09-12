# M6 immutable release engineering

**Owner:** #519, #827  
**Depends on:** #190, #193, #194, #375  
**Gate:** G4 is already passed; G5 consumes the final release evidence.

This document records the release-engineering, OCI publication and Android publication
decisions. It deliberately keeps release identity, signing custody and rollback
selection separate from database recovery.

## Decision: build once, publish immutable artifacts

For launch, SideBySide/eimir. uses **build-once release artifacts** while keeping
#375's exact commit SHA as the source identity.

The v1 packaging boundary is:

- one backend image archive shared by API, worker and migrate;
- one Web image archive;
- versioned GHCR backend/Web images loaded from those exact archives **without rebuild**;
- one Self-Hosted image-identity record with digest-qualified registry references;
- final signed Android APK/AAB for the selected distribution channel;
- SPDX 2.3 JSON SBOMs and GitHub Artifact Attestations from #193;
- one machine-readable release manifest plus checksums;
- one Git tag `v<product-version>` pointing to the exact release commit;
- one GitHub Release containing the complete immutable artifact/evidence set.

The protected publication workflow promotes the already-built #193 backend/Web archives
to:

- `ghcr.io/baerenmarke90/eimir-backend:sha-<source-sha>`;
- `ghcr.io/baerenmarke90/eimir-backend:v<product-version>`;
- `ghcr.io/baerenmarke90/eimir-web:sha-<source-sha>`;
- `ghcr.io/baerenmarke90/eimir-web:v<product-version>`.

It never publishes `latest` and never rebuilds the runtime images in the protected job.
If an existing source or version tag points to different image bytes/digest, publication
fails rather than moving the tag.

An OCI/Docker **tag is not immutable identity**, even when its spelling looks like an
immutable product version such as `v1.0.0`. `self-hosted-image-identity.json` therefore
records the resolved digest-qualified references (`repository:vX.Y.Z@sha256:<digest>`)
and the SHA-256 of the #519 archive that was promoted. The digest supplements the #519
release identity; it does not create a second product release identity.

Cloud/Managed Production keeps the stronger #668 rule: the running deployment must use
digest-qualified registry references and retain the actual resolved deployment identity.
The same published backend/Web image bytes may be used, but managed deployment evidence
is still separate from Self-Hosted release publication.

## Version policy

Launch versions use SemVer and have exactly two human-facing representations:

- product version / Android `versionName`: `MAJOR.MINOR.PATCH` with an intentional
  SemVer prerelease/build suffix only when needed;
- Git tag: `v<product-version>`.

`android/app/build.gradle.kts` remains authoritative for `versionName` per #194. A
release fails when the requested product version differs from that value.

Android `versionCode` is a positive monotonically increasing integer supplied by the
publishing workflow. It is not derived from SemVer and is not a second product version.

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

The release manifest contains no credential, token, signing key, `.env` value, user
content or provider secret.

The adjacent `self-hosted-image-identity.json` is transport evidence. It records only:

- product version/tag and source revision;
- exact backend/Web digest-qualified GHCR references;
- #519 backend/Web archive SHA-256 values;
- backend role mapping (`api`, `worker`, `migrate`) and the Web role;
- the canonical release-manifest filename.

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
For Self-Hosted rollback, the previous release's versioned/digest-qualified image
identity is selected together with that application release; database rollback remains
a separate decision.

## Database rollback boundary

Every release manifest states:

- application release selection is independent from database recovery;
- database rollback is **not implied**;
- schema compatibility review is required;
- #190 and #375 remain authoritative for forward-fix, downgrade and restore choices.

An operator must not start an old application merely because its release assets/images
are available. If the current schema is not backward-compatible, use the explicitly
tested forward-fix/downgrade path or restore the coordinated recovery point according
to #190/#375.

## Candidate workflow

`.github/workflows/release-candidate.yml` remains the unprivileged immutable candidate
workflow. It is manual-only for real candidates and has no `contents: write` or
`packages: write` permission.

It:

1. calls the #193 reusable evidence workflow;
2. builds backend/Web and unsigned Android release candidates from one exact SHA;
3. produces SPDX SBOMs and attestations;
4. binds version, source SHA, artifact digests and previous-known-good identity into a
   candidate manifest;
5. verifies all artifact/SBOM digests;
6. uploads an immutable candidate bundle.

An unsigned Android candidate is never a launch/store artifact. Candidate runs also do
not publish OCI packages; registry write access exists only in the protected final
publication job.

## Android signing and Play decision

The release-owner decision is fixed for the first launch.

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
into release evidence, artifacts, logs, SBOMs, manifests, registry metadata or release
notes.

GHCR authentication uses the ephemeral GitHub Actions token. Only the protected
publication job receives `packages: write`; candidate/preflight jobs remain read-only.
No registry password/token is persisted in the repository or release evidence.

The GitHub environment itself and its secret values are operator configuration and are
not represented in repository files. Before the first real publication, G5/#914 must
verify that the environment is protected, the expected approver policy is active and
all four signing secrets are present.

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
turn a candidate source revision into a final launch release and versioned runtime
packages.

The workflow is fail-closed and uses three boundaries before publication:

### 1. Unprivileged preflight

Before requesting access to signing or package-write privileges, it verifies:

- explicit `confirm_publish=true` operator intent;
- the exact source SHA is reachable from `main`;
- existing CI/security checks for that SHA are completed without failure;
- the requested tag and GitHub Release do not already exist;
- product version matches the frozen Android `versionName`;
- previous-known-good selection is valid, or the operator explicitly marks the initial
  release;
- #193 artifact transport checksums are intact.

### 2. Protected signing, OCI promotion and final evidence

Only after preflight succeeds does the `production-release` job start.

It:

1. materializes the Android upload keystore only in `$RUNNER_TEMP`;
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
9. builds and verifies the final release manifest with `--require-signed-android`;
10. loads the exact #193 backend/Web image archives with `docker load`;
11. publishes immutable `sha-<source>` and `v<version>` GHCR tags, refusing any
    pre-existing tag that points to different bytes/digest;
12. writes `self-hosted-image-identity.json` with the digest-qualified references and
    original release-archive hashes;
13. writes and verifies final checksums and human-readable release notes.

Backend/Web are **not rebuilt** in the protected job; the exact #193 build-once
artifacts are retained and promoted. Only Android must be rebuilt because signing
changes its final bytes.

### 3. Immutable publication

Immediately before GitHub Release write access is used, the workflow rechecks that the
release tag and GitHub Release are still unused. It then:

- creates `v<version>` at exactly `github.sha`;
- publishes the complete release-evidence directory as GitHub Release assets;
- downloads both `sidebyside-release-manifest.json` and
  `self-hosted-image-identity.json` again;
- confirms the tag resolves to the original source SHA and both published identity
  files are byte-identical to the locally verified copies.

The workflow never overwrites a conflicting release or registry identity. A retry after
a partial registry publication is permitted only when the existing `sha-<source>` and
`v<version>` identities resolve to the same image bytes/digest as the current exact
#193 archive.

## Released Self-Hosted runtime contract

Repository-root `compose.yaml` is the **released** Self-Hosted topology.

For application services it contains no `build:` fallback:

- `api`, `worker` and `migrate` consume one backend image identity;
- `web` consumes one Web image identity;
- `postgres` remains the upstream PostgreSQL image;
- `demo-init` is not part of the normal `self-hosted` profile/startup chain.

The default release references are the versioned GHCR tags for the repository's current
product version. Operators who want fully locked transport identity set:

- `SBS_SELF_HOSTED_BACKEND_IMAGE` to the digest-qualified backend reference from
  `self-hosted-image-identity.json`;
- `SBS_SELF_HOSTED_WEB_IMAGE` to the digest-qualified Web reference from the same file.

`deploy/self-hosted-release.env.example` is the released installation template.
A clean target host needs the Compose/env configuration plus Docker/Compose and the
released registry images; it does **not** need the application source tree to build
backend or Web images.

### Explicit source-build boundary

Source-building remains supported for local Development, persistent Development,
Arcane source workspaces, CI and exceptional verified-source acceptance. These paths
must explicitly add:

`deploy/compose.source-build.yaml`

The repository `.env.example` and `deploy/persistent-development.env.example` do this
for development. `scripts/compose_checked.py` exports both the canonical Compose file
and this override from one clean immutable Git snapshot before building.

This source-build path is **not** a released Production fallback. A registry outage or
missing release image must fail the released deployment rather than silently compiling
whatever source happens to exist on the target host.

### Demo initialization

`demo-init` is profile `demo`, not `self-hosted`. Normal Self-Hosted startup therefore
does not run Demo seeding. A Demo operator intentionally activates both profiles and
runs the one-shot initialization lifecycle before starting/accepting Demo traffic.
This keeps Demo-specific preparation out of the normal deployment graph while
preserving the existing initializer for the public Demo environment.

## GitHub environment setup before first publication

This repository intentionally cannot create or populate signing secrets itself. The
release owner must configure GitHub before the first production run:

1. create/protect the `production-release` environment;
2. require explicit deployment approval by the release owner;
3. add the four Android environment secrets listed above;
4. generate/store the encrypted offline upload-key recovery copy independently;
5. enable Google Play App Signing and register the matching upload certificate in the
   Play Console;
6. ensure Actions may publish packages for the repository; the workflow grants
   `packages: write` only to the protected publication job;
7. execute the first publication only through `Publish Immutable Release` after normal
   launch gates are green.

If any required condition is absent, the workflow must fail rather than falling back to
debug signing, unsigned publication, source-building Production, or a repository secret.

## Cloud/Managed deployment binding

The final publication now already promotes the exact #519 backend/Web archives to GHCR.
Cloud/Managed may consume those same package bytes, but #668 still requires its own
runtime/deployment identity record. `scripts/release_manifest.py cloud-deployment`
consumes the exact final release manifest and the resolved canonical `cloud` Compose
configuration and emits a small deployment identity record containing only:

- product version/tag, source revision and SHA-256 of the exact #519 release manifest;
- the existing #519 `backend-runtime` and `web-runtime` archive SHA-256 values;
- the exact digest-qualified backend and Web registry references/digests actually
  selected by Compose;
- backend roles (`api`, `worker`, `migrate`) as one shared image identity;
- the exact previous-known-good Cloud deployment identity for a non-initial release.

The command rejects tag-only references (`latest`, `main`, `v1.0.0`, arbitrary branch
or custom tags), missing images, any `build:` fallback, backend-role image divergence,
an unsigned/non-final #519 manifest, and a previous deployment identity that does not
match the canonical #519 `previousKnownGood` record. The output is deployment evidence,
not another release manifest, and contains no Compose environment or secret values.

Because registry manifest digests and `docker save` archive digests identify different
representations, they are recorded side by side rather than incorrectly compared for
string equality. The invariant is: the already verified #519 archive is loaded and
pushed without rebuild; the registry-reported digest of that promoted image becomes the
exact pull identity used by Production.

## Self-Hosted and Cloud/Managed

Both operating models consume the same product release identity:

`product version -> Git tag -> immutable source SHA -> release manifest -> artifact digests`

Self-Hosted consumes the versioned published OCI images, with digest-qualified overrides
available from the release evidence. Cloud/Managed consumes digest-qualified references
only and separately records the actual managed deployment identity. Neither mode builds
application source on the Production target. Commercial entitlement state is unrelated
to artifact identity.

## Focused test contract

`tools/ci/test_release_manifest.py` covers release-manifest invariants plus the #668
Cloud deployment binding, digest-only OCI identity and previous-known-good linkage.

`tools/ci/test_release_publish_workflow.py` covers the privileged publication boundary,
including:

- no privileged `pull_request_target` path;
- protected environment and least-privilege permissions;
- package-write permission only in the protected publication job;
- explicit publish confirmation and source-on-main requirement;
- CI/tag/release preflight;
- environment-only ephemeral Android signing material;
- signed Android identity verification;
- fresh SBOM/attestation generation for signed bytes;
- exact runtime archive loading with no backend/Web rebuild;
- immutable `sha-<source>` / `v<version>` GHCR publication with collision checks;
- digest-qualified `self-hosted-image-identity.json` release evidence;
- final `--require-signed-android` verification;
- immutable GitHub Release/tag publication;
- immutable pins for external Actions and the Syft binary.

The Self-Hosted Deployment Guard additionally proves that repository-root
`compose.yaml` has no application `build:` entries for released Self-Hosted, while the
explicit source-build override still exercises local/CI integration and recovery.

Normal repository CI/security/privacy/reuse/supply-chain gates remain authoritative for
the application revision. #914 performs the real protected operator publication and
captures G5-02/G5-03 evidence.
