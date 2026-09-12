# M6 immutable release engineering

**Owner:** #519, #827  
**Depends on:** #190, #193, #194, #375  
**Gate:** G4 is already passed; G5 consumes the final release evidence.

This document records the release-engineering, OCI publication and Android publication
contract. Release identity, signing custody, application rollback and database recovery
remain separate concerns.

## Decision: build once, publish immutable artifacts

SideBySide/eimir. uses **build-once release artifacts** while preserving the exact Git
commit SHA as source identity.

The launch artifact set is:

- one backend runtime archive shared by API, worker and migrate;
- one Web runtime archive;
- versioned GHCR backend/Web images loaded from those exact archives without rebuild;
- one Self-Hosted image-identity record containing digest-qualified registry references;
- final signed Android APK/AAB for the selected distribution channel;
- SPDX 2.3 JSON SBOMs and GitHub Artifact Attestations from #193;
- one machine-readable release manifest plus checksums;
- one Git tag `v<product-version>` pointing to the exact release commit;
- one GitHub Release containing the complete immutable artifact/evidence set.

The protected publication workflow promotes the already-built #193 runtime archives to:

```text
ghcr.io/baerenmarke90/eimir-backend:sha-<source-sha>
ghcr.io/baerenmarke90/eimir-backend:v<product-version>
ghcr.io/baerenmarke90/eimir-web:sha-<source-sha>
ghcr.io/baerenmarke90/eimir-web:v<product-version>
```

It never publishes `latest`. It never rebuilds backend/Web in the protected publication
job. If an existing source or version tag resolves to different image bytes/digest,
publication fails rather than moving the tag.

An OCI tag is not immutable identity. `self-hosted-image-identity.json` therefore records
the resolved digest-qualified references (`repository:vX.Y.Z@sha256:<digest>`) together
with the SHA-256 of the original #519 runtime archive that was promoted.

Cloud/Managed keeps the stronger #668 rule: a running managed deployment must itself use
and retain digest-qualified runtime identity. Self-Hosted publication evidence and
managed deployment evidence are related but distinct.

## Version policy

Launch versions use SemVer:

- product version / Android `versionName`: `MAJOR.MINOR.PATCH`, optionally with an
  intentional SemVer prerelease/build suffix;
- Git tag: `v<product-version>`.

`android/app/build.gradle.kts` remains authoritative for `versionName` per #194. The
publication workflow rejects a requested product version that differs from it.

Android `versionCode` is a positive monotonically increasing integer supplied by the
publication workflow. It is not derived from SemVer and is not a second product version.

## Release manifest

`scripts/release_manifest.py` consumes the exact #193 `evidence-index.json` and creates
one schema-v1 release manifest. It rejects, among other invalid states:

- a non-SemVer product version;
- a non-immutable source SHA;
- backend artifacts that do not jointly cover API, worker and migrate;
- missing or mixed backend/Web/APK/AAB evidence;
- Android application IDs other than `de.sidebyside.app`;
- Android `versionName` differing from the product version;
- unsafe artifact paths or malformed digests;
- final publication when Android is not `signed-release`.

The release manifest contains no credentials, signing key, `.env` values, user content,
tokens, receipts, provider payloads or storage secrets.

The adjacent `self-hosted-image-identity.json` records only:

- product version/tag and source revision;
- exact backend/Web digest-qualified GHCR references;
- #519 backend/Web archive SHA-256 values;
- backend role mapping (`api`, `worker`, `migrate`) and the Web role;
- the canonical release-manifest filename.

Registry manifest digests and `docker save` archive hashes identify different transport
representations and are therefore recorded side by side rather than compared for string
equality. The invariant is that the already verified archive is loaded and pushed
without rebuild; the registry-reported digest becomes the exact pull identity.

## Previous known-good release

The previous-known-good identity is never a free-form operator SHA. For every
non-initial release, the workflow downloads `sidebyside-release-manifest.json` from an
explicitly selected previous GitHub Release and records:

- previous product version;
- previous release tag;
- previous immutable source revision;
- SHA-256 of the previous manifest.

The final publication path accepts only a previously published release as known-good
Production. For Self-Hosted rollback, the matching previous published OCI identity is
selected with that application release.

## Database rollback boundary

Application rollback does **not** imply database rollback.

Every release retains the #190/#375 boundary:

- schema compatibility is reviewed independently;
- use the tested forward-fix/downgrade path where appropriate;
- otherwise restore a coordinated recovery point according to the recovery contract;
- do not start an old application merely because its image is still pullable.

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
5. verifies artifact/SBOM digests;
6. uploads an immutable candidate bundle.

An unsigned Android candidate is never a launch/store artifact. Candidate runs do not
publish OCI packages.

## Android signing and Play decision

### App-signing model

- Google Play App Signing owns the production application-signing key.
- SideBySide release automation uses a distinct upload key.
- The application-signing key is not stored in GitHub, the repository or operator
  backups.
- The upload key is the only Android private key consumed by SideBySide automation.

### Online custody

The approved online custody point is the protected GitHub Actions environment:

```text
production-release
```

The environment supplies exactly these secrets:

- `SBS_RELEASE_KEYSTORE_BASE64`;
- `SBS_RELEASE_KEYSTORE_PASSWORD`;
- `SBS_RELEASE_KEY_ALIAS`;
- `SBS_RELEASE_KEY_PASSWORD`.

Repository-level secrets are not the approved custody point. The workflow materializes
the keystore only under `$RUNNER_TEMP`, uses it for final signing and removes it when the
step exits. No signing material is copied into release evidence, artifacts, logs, SBOMs,
manifests, registry metadata or release notes.

GHCR authentication uses the ephemeral GitHub Actions token. Only the protected
publication job receives `packages: write`; candidate/preflight jobs remain read-only.
No registry password/token is persisted as evidence.

Before the first real publication, #914 must verify that `production-release` is
protected, the intended approval policy is active and all required signing secrets are
present.

### Offline recovery / escrow

The release owner keeps one encrypted offline recovery copy of the upload key plus the
alias and recovery procedure in a location independent from GitHub. Passwords protecting
that copy are not stored next to an unencrypted keystore.

If the online upload key is lost, restore from the trusted copy and rotate after any
suspected exposure. If no trustworthy upload key remains, use Google Play's supported
upload-key reset process. Do not create a second Play application as an ad-hoc recovery
mechanism.

## Protected final publication workflow

`.github/workflows/release-publish.yml` is the only repository workflow that may turn a
candidate source revision into the final GitHub Release and versioned runtime packages.

### 1. Unprivileged preflight

Before protected signing/package publication, it verifies:

- explicit `confirm_publish=true` operator intent;
- the exact source SHA is reachable from `main`;
- existing CI/security checks for that SHA are completed without failure;
- the requested tag and GitHub Release are unused;
- product version matches frozen Android `versionName`;
- previous-known-good selection is valid, or the operator explicitly marks the initial
  release;
- #193 artifact transport checksums are intact.

### 2. Protected signing and OCI promotion

Only after preflight succeeds does the `production-release` job start.

It:

1. materializes the Android upload keystore only in `$RUNNER_TEMP`;
2. builds APK/AAB from the same `github.sha` with the supplied monotonic `versionCode`;
3. verifies signatures, application ID, `versionName` and `versionCode`;
4. removes unsigned Android candidates from final evidence;
5. regenerates Android SPDX SBOMs for signed bytes;
6. rebinds Android digests in `evidence-index.json` and marks them `signed-release`;
7. creates fresh provenance/SBOM attestations for signed APK/AAB;
8. re-verifies retained backend/Web attestations and final Android attestations;
9. builds/verifies the final release manifest with `--require-signed-android`;
10. loads the exact #193 backend/Web runtime archives with `docker load`;
11. publishes immutable `sha-<source>` and `v<version>` GHCR tags;
12. refuses any existing tag whose bytes/digest differ;
13. writes `self-hosted-image-identity.json` with digest-qualified registry references
    and original archive hashes;
14. writes/verifies final checksums and release notes.

Backend/Web are not rebuilt in this job. Only Android is rebuilt because final signing
changes its bytes.

### 3. Immutable GitHub publication

Immediately before write access is used, the workflow rechecks that tag and Release are
unused. It then:

- creates `v<version>` at exactly `github.sha`;
- uploads the complete release-evidence directory;
- downloads `sidebyside-release-manifest.json` and
  `self-hosted-image-identity.json` again;
- verifies the tag resolves to the original source SHA;
- verifies both downloaded identity files are byte-identical to the locally validated
  copies.

A retry after partial registry publication is allowed only when existing `sha-<source>`
and `v<version>` package identities resolve to the same bytes/digest as the exact #193
archive. The workflow never overwrites a conflicting release or package identity.

## Released Self-Hosted runtime contract

Repository-root `compose.yaml` is the **only tracked Compose runtime manifest** and the
released Self-Hosted topology.

For application services it contains no `build:` fallback:

- `api`, `worker` and `migrate` consume one backend image identity;
- `web` consumes one Web image identity;
- `postgres` remains the upstream PostgreSQL image;
- `demo-init` is not part of the normal `self-hosted` startup chain.

The released default references are versioned GHCR tags. For fully locked transport
identity, set:

- `SBS_SELF_HOSTED_BACKEND_IMAGE` to the digest-qualified backend reference from the
  release's `self-hosted-image-identity.json`;
- `SBS_SELF_HOSTED_WEB_IMAGE` to the matching Web reference.

`deploy/self-hosted-release.env.example` is the released installation template. A clean
target host needs Docker/Compose, the canonical Compose/env configuration, and access to
the published images. It does not build application source.

Production requires `SBS_SELF_HOSTED_PULL_POLICY=always` (the Compose default). A
registry outage or missing release image fails the deployment rather than compiling
whatever source is present locally.

## Development and verified-source boundary

Source building remains supported for local Development, persistent Development, CI and
exceptional verified-source acceptance **without creating another tracked Compose
manifest**.

`scripts/build_self_hosted_source.py` builds local backend/Web images and the development
environment points canonical `compose.yaml` at those local tags with:

```dotenv
SBS_SELF_HOSTED_PULL_POLICY=never
```

`scripts/compose_checked.py` provides the stronger verified-source path. It exports
`compose.yaml`, backend and Web from one clean exact Git snapshot, builds verified local
images from that snapshot, and runs the exported canonical manifest against those image
tags.

This path is Development/CI evidence, not a released Production fallback.

## Demo initialization

`demo-init` uses profile `demo`, not `self-hosted`. Normal Self-Hosted startup therefore
does not execute Demo seeding. A Demo operator intentionally runs the one-shot Demo
lifecycle when preparing the isolated public Demo environment.

## GitHub environment setup before first publication

Repository code intentionally cannot create or populate signing secrets. Before the
first Production run, the release owner must:

1. create/protect the `production-release` environment;
2. require explicit deployment approval by the release owner;
3. add the four Android environment secrets listed above;
4. retain an encrypted offline upload-key recovery copy independently;
5. enable Google Play App Signing and register the matching upload certificate;
6. ensure GitHub Actions package publication is allowed for this repository;
7. execute final publication only through `Publish Immutable Release` after normal
   launch gates are green.

If any required condition is absent, the workflow must fail rather than falling back to
debug signing, unsigned publication, source-building Production or repository secrets.

## Cloud/Managed deployment binding

The final publication promotes the same exact #519 backend/Web archives to GHCR.
Cloud/Managed may consume those bytes, but #668 still requires a separate managed
runtime/deployment identity record.

`scripts/release_manifest.py cloud-deployment` consumes the final release manifest and
resolved canonical `cloud` Compose configuration and emits only:

- product version/tag, source revision and SHA-256 of the exact release manifest;
- #519 backend/Web archive SHA-256 values;
- exact digest-qualified backend/Web registry references selected by Compose;
- backend roles (`api`, `worker`, `migrate`) sharing one image identity;
- previous-known-good Cloud deployment identity for a non-initial release.

It rejects tag-only managed references, missing images, `build:` fallbacks,
backend-role divergence, non-final manifests and previous deployment identity that does
not match the release manifest's `previousKnownGood` record.

## Self-Hosted and Cloud/Managed identity

Both operating models consume one product release chain:

```text
product version -> Git tag -> immutable source SHA -> release manifest -> artifact hashes
```

Self-Hosted uses the published versioned OCI images, with digest-qualified references
available as release evidence. Cloud/Managed uses digest-qualified references only and
retains its actual managed deployment identity. Neither mode builds application source
on a Production target.

Commercial entitlement state is unrelated to artifact identity.

## Focused test contract

`tools/ci/test_release_manifest.py` covers release-manifest invariants plus #668 Cloud
deployment binding and previous-known-good linkage.

`tools/ci/test_release_publish_workflow.py` covers the protected publication boundary,
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

The Self-Hosted Deployment Guard additionally proves that released `compose.yaml` has no
application `build:` entries and that development/CI can still exercise local source
images through the same canonical manifest.

Normal repository CI/security/privacy/reuse/supply-chain gates remain authoritative for
the source revision. #914 performs the real protected operator publication and captures
G5-02/G5-03 evidence.
