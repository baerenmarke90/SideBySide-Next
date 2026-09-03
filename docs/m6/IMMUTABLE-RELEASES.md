# M6 immutable release engineering

**Owner:** #519  
**Depends on:** #190, #193, #194, #375  
**Gate:** G4 is already passed; G5 consumes the final release evidence.

This document records the #519 release-engineering decision and the remaining
operator decision that cannot be made safely without the release owner.

## Decision: build once, publish immutable artifacts

For launch, SideBySide should move from #375's permitted immutable-source build model
to **build-once release artifacts** while keeping #375's immutable commit SHA as the
source identity.

The selected v1 packaging boundary is deliberately conservative:

- one backend image archive serves API, worker and migrate;
- one Web image archive;
- Android APK/AAB according to the selected distribution channel;
- SPDX SBOMs and GitHub Artifact Attestations from #193;
- one machine-readable release manifest plus checksums;
- GitHub Releases is the intended publication surface for the first launch rather
  than introducing Kubernetes, a custom orchestrator or a mandatory external
  registry.

A Cloud/Managed operator may later load the exact released image archive and push it
to a registry, recording the resulting immutable registry digest as an additional
transport identity. The product must not be rebuilt for that promotion. Self-Hosted
operators retain both the #375 verified-source path and, after publication, the
released image-archive path. Neither mode may identify Production by mutable `main`.

The current PR intentionally stops at an immutable **release candidate** workflow.
Final GitHub Release/store publication remains disabled until the Android signing
custody decision below is made. An unsigned Android candidate is not a launch
artifact.

## Version policy

Launch versions use SemVer and have exactly two representations:

- product version / Android `versionName`: `MAJOR.MINOR.PATCH` (optionally a SemVer
  prerelease/build suffix when intentionally used);
- Git tag: `v<product-version>`.

`android/app/build.gradle.kts` remains the authoritative `versionName` source per
#194. A release candidate fails when its requested product version differs from that
value.

Android `versionCode` is a positive monotonically increasing integer supplied by the
publishing environment. It is not derived from the SemVer string and is not a second
product version.

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
- a final-publication verification request when Android is not `signed-release`.

The manifest contains no credential, token, signing key, `.env` value, user content or
provider secret.

## Previous known-good release

The previous-known-good identity is never a free-form operator SHA in the release
manifest. For every non-initial release, the candidate workflow downloads
`sidebyside-release-manifest.json` from the explicitly selected previous GitHub
Release and embeds:

- previous product version;
- previous release tag;
- previous immutable source revision;
- SHA-256 of the previous manifest.

This makes rollback selection deterministic without pretending application rollback
also rolls back the database.

## Database rollback boundary

Every release manifest states:

- application release selection is independent from database recovery;
- database rollback is **not implied**;
- schema compatibility review is required;
- #190 and #375 remain authoritative for forward-fix, downgrade and restore choices.

An operator must not start an old application merely because its release assets are
available. If the current schema is not backward-compatible, choose an explicitly
tested forward fix/downgrade or restore the coordinated pre-change backup according
to #190/#375.

## Controlled candidate workflow

`.github/workflows/release-candidate.yml` is manual-only. The operator selects the
Git ref in GitHub Actions; `github.sha` is therefore the exact source identity for all
artifacts in that run.

The workflow:

1. calls the #193 reusable release-evidence workflow rather than rebuilding SBOM or
   attestation logic;
2. verifies #193 transport checksums;
3. resolves the previous-known-good manifest from a prior GitHub Release, or records
   that this is the initial release;
4. builds the release manifest;
5. re-hashes every artifact and SBOM against the manifest;
6. creates human-readable candidate notes;
7. uploads one immutable workflow artifact named with version plus source SHA.

The workflow has no `contents: write` permission and cannot publish a Git tag or
Release. This is intentional until the signing decision is closed.

## Android signing / Play decision still required

The code boundary is already safe: #194 prevents debug-signing fallback and accepts
release signing material only from the publishing environment. What remains is an
operator/security decision.

### Recommended operating model

Use **Google Play App Signing** for the app-signing key. Use a distinct upload key for
release automation.

Recommended custody:

- Google Play holds the production app-signing key;
- the release owner keeps an encrypted offline recovery copy of the upload key and
  recovery documentation;
- a protected GitHub Actions environment such as `production-release` receives only
  the upload-key material needed for a release job;
- access to that environment is least-privilege and requires explicit approval;
- secrets are materialized only for the Gradle signing step, masked, and deleted at
  job end;
- no keystore, password, alias, base64 key material or recovery data is uploaded as a
  workflow artifact or written to the release manifest.

### Decision needed from release owner

Before final store publication, explicitly choose and record:

1. whether Google Play App Signing is enabled;
2. who is the human owner of the offline upload-key recovery copy;
3. whether GitHub's `production-release` environment is the approved online custody
   point for the upload key;
4. who may approve/use that environment.

Until those points are decided and configured, SideBySide can produce fully coherent
unsigned candidates but **must not publish them as launch releases**.

## Final publication slice after the decision

The remaining implementation is intentionally small and reuses this contract:

1. materialize the upload keystore only inside the protected publishing job;
2. build the final signed AAB/APK from the same `github.sha`, product version and
   `versionCode`;
3. regenerate the Android SBOM for the final bytes and use #193's attestation
   primitive for those final signed subjects;
4. rebuild the release manifest with Android signing state `signed-release` and run
   `release_manifest.py verify --require-signed-android`;
5. create tag `v<version>` pointing to the exact source SHA;
6. publish one GitHub Release containing backend/Web artifacts, signed Android
   artifacts, SBOMs, manifest, checksums and release notes;
7. verify the published tag, manifest and attestation subjects before G5 approval.

No database migration is reversed by any of these publication steps.

## Focused test contract

`tools/ci/test_release_manifest.py` exercises the key negative cases: mixed Android
version, split backend roles, unsigned final publication, artifact tampering and
previous-known-good identity sourced from a real manifest rather than a free-form
SHA. Normal repository CI remains the gate for the underlying application revision.
