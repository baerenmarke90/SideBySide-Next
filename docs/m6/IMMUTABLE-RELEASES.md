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
- one small Self-Hosted operator bundle containing canonical Compose, release env
  template, mandatory Production launcher and runtime checker;
- final signed Android APK/AAB;
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

It never publishes `latest` and never rebuilds backend/Web in the protected job. An
existing source/version tag is inspected fail-closed: only an authoritative registry
not-found result is treated as absent; authentication, rate-limit, network, server or
unclassified lookup failures abort publication. An existing tag that resolves to
different bytes/digest also aborts publication.

An OCI tag is not immutable identity. `self-hosted-image-identity.json` records the
resolved digest-qualified references (`repository:vX.Y.Z@sha256:<digest>`) together with
the SHA-256 of the original #519 runtime archive that was promoted.

Cloud/Managed keeps the stronger #668 rule: a running managed deployment must itself use
and retain digest-qualified runtime identity. Self-Hosted publication evidence and
managed deployment evidence are related but distinct.

## Version policy

Launch versions use SemVer:

- product version / Android `versionName`: `MAJOR.MINOR.PATCH`, optionally with an
  intentional prerelease/build suffix;
- Git tag: `v<product-version>`.

`android/app/build.gradle.kts` remains authoritative for `versionName`. Android
`versionCode` is a positive monotonically increasing integer supplied by publication.

For Self-Hosted Production, `SBS_RELEASE_VERSION` is mandatory. Versioned or
digest-qualified image overrides must still carry exactly that same release version.
The Production launcher validates this before pull/bootstrap/start.

## Release manifest and image identity

`scripts/release_manifest.py` consumes the exact #193 `evidence-index.json` and creates
one schema-v1 release manifest. It rejects invalid product/source/artifact/Android
identity and final publication when Android is not `signed-release`.

The release manifest contains no credentials, signing key, `.env` values, user content,
tokens, receipts, provider payloads or storage secrets.

`self-hosted-image-identity.json` records only:

- product version/tag and source revision;
- exact backend/Web digest-qualified GHCR references;
- #519 backend/Web archive SHA-256 values;
- backend role mapping (`api`, `worker`, `migrate`) and the Web role;
- canonical release-manifest filename.

Registry manifest digests and `docker save` archive hashes identify different transport
representations and are recorded side by side. The invariant is that the already
verified archive is loaded and pushed without rebuild; the registry-reported digest
becomes the exact pull identity.

## Previous known-good release and rollback boundary

For every non-initial release, the workflow downloads the previous published
`sidebyside-release-manifest.json` and records its product version, release tag, immutable
source revision and manifest hash. A free-form operator SHA is not accepted as known-good.

Application rollback does **not** imply database rollback. Schema compatibility remains
under #190/#375: use the tested forward-fix/downgrade path where appropriate or restore a
coordinated recovery point. Do not start an old image merely because it remains pullable.

## Candidate workflow

`.github/workflows/release-candidate.yml` remains the unprivileged candidate workflow.
It builds backend/Web and unsigned Android candidates from one exact SHA, produces
SBOMs/attestations, binds identity into a candidate manifest and uploads an immutable
candidate bundle. It has no package-write permission and does not publish OCI packages.

An unsigned Android candidate is never a launch/store artifact.

## Android signing custody

Google Play App Signing owns the production application-signing key. SideBySide release
automation uses a distinct upload key supplied only by the protected GitHub Actions
environment:

```text
production-release
```

Required environment secrets are:

- `SBS_RELEASE_KEYSTORE_BASE64`;
- `SBS_RELEASE_KEYSTORE_PASSWORD`;
- `SBS_RELEASE_KEY_ALIAS`;
- `SBS_RELEASE_KEY_PASSWORD`.

The workflow materializes the keystore only under `$RUNNER_TEMP`, removes it after use,
and never copies signing material into evidence/logs/SBOMs/manifests/registry metadata.
GHCR authentication uses the ephemeral Actions token; only the protected publication job
has `packages: write`.

Before the first real publication, #914 must verify the protected environment, approval
policy and signing-secret presence. The release owner separately keeps one encrypted
offline recovery copy of the upload key.

## Protected final publication workflow

`.github/workflows/release-publish.yml` is the only repository workflow that may turn a
candidate source revision into a final GitHub Release and versioned runtime packages.

### 1. Unprivileged preflight

It verifies:

- `confirm_publish=true`;
- exact source SHA reachable from `main`;
- pre-existing CI/security checks completed green;
- requested tag/Release unused;
- requested version matches Android `versionName`;
- valid initial/previous-known-good choice;
- #193 transport checksums intact.

### 2. Protected signing and OCI promotion

After protected environment approval it:

1. signs/verifies final Android APK/AAB from the same `github.sha`;
2. regenerates signed-byte SBOMs and attestations;
3. builds/verifies the final signed release manifest;
4. loads exact #193 backend/Web archives with `docker load`;
5. publishes immutable `sha-<source>` and `v<version>` GHCR tags without rebuild;
6. treats only an authoritative not-found as permission to create a missing registry
   tag and aborts every uncertain lookup;
7. writes `self-hosted-image-identity.json`;
8. creates a deterministic Self-Hosted operator bundle containing only:
   - `compose.yaml`;
   - `deploy/self-hosted-release.env.example`;
   - `scripts/self_hosted_release.py`;
   - `scripts/check_runtime_environment.py`;
9. writes/verifies final checksums and release notes.

The bundle contains no backend/Web application source and no credentials. It is the
supported installation surface for a clean Self-Hosted target host.

### 3. Immutable GitHub publication

Immediately before publication the workflow rechecks tag/Release absence, then creates
`v<version>` at exactly `github.sha`, uploads the complete release-evidence directory and
re-downloads the release/image identity files to prove the published bytes match the
locally validated copies.

A retry after partial registry publication is allowed only when existing package
identities resolve to the exact expected bytes/digest. Conflicting or uncertain identity
always fails closed.

## Released Self-Hosted runtime contract

Repository-root `compose.yaml` is the **only tracked Compose runtime manifest**. Released
application services contain no `build:` fallback:

- `api`, `worker`, `migrate` consume one backend image identity;
- `web` consumes one Web image identity;
- `postgres` remains the upstream image;
- `demo-init` is not part of normal `self-hosted` startup.

The release env template selects `SBS_RELEASE_VERSION`; digest-qualified overrides may
lock transport bytes but must still carry that version.

### Mandatory Production launcher

Released Production is operated through:

```bash
python3 scripts/self_hosted_release.py --env-file .env <operation>
```

The launcher is part of the release bundle and provides `validate`, `pull`,
`bootstrap-deletion-authority`, and `deploy` operations. Before pull/bootstrap/start it
renders canonical Compose and validates the selected release identity. `deploy` also
requires the complete Production runtime-environment contract.

Raw Compose is not the supported Production pull/bootstrap/start path. It is acceptable
for post-deploy diagnostics only. A registry outage, version mismatch or invalid image
identity fails rather than falling back to source.

## Development and verified-source boundary

Development/CI may build local images through `scripts/build_self_hosted_source.py` and
then run canonical Compose with pull disabled. The builder:

- rejects Production declared by dotenv **or** process environment;
- accepts only local SideBySide image repositories/tags as build targets;
- rejects credential/query-bearing remote source URLs before they reach plan output.

`scripts/compose_checked.py` exports one exact clean Git snapshot, builds verified local
images and runs canonical Compose against those images. It likewise rejects Production
from either configuration source.

These are Development/CI evidence paths, never released Production fallbacks.

## Demo initialization

`demo-init` uses profile `demo`, not `self-hosted`. Normal Self-Hosted startup does not
execute Demo seeding. Public Demo operators intentionally run that one-shot lifecycle.

## GitHub environment setup before first publication

Before the first Production publication, the release owner must:

1. protect `production-release` with explicit release-owner approval;
2. configure the four Android upload-key secrets;
3. retain encrypted offline upload-key recovery independently;
4. enable Google Play App Signing/register the upload certificate;
5. allow repository Actions package publication;
6. execute final publication only after launch gates are green.

No missing condition may fall back to debug signing, unsigned publication,
source-building Production or repository-level signing secrets.

## Cloud/Managed deployment binding

The same exact #519 backend/Web archives are promoted to GHCR. Cloud/Managed may consume
those bytes, but #668 requires separate managed runtime/deployment identity evidence.
`scripts/release_manifest.py cloud-deployment` rejects mutable tag-only identities,
missing images, `build:` fallback, backend-role divergence, non-final manifests and
invalid previous-known-good linkage.

Both operating models consume one product release chain:

```text
product version -> Git tag -> immutable source SHA -> release manifest -> artifact hashes
```

Self-Hosted uses published versioned/digest-qualified OCI identity through the released
launcher. Cloud/Managed uses digest-qualified references only and separately records the
actual managed deployment identity. Neither builds application source on a Production
target.

## Focused test contract

`tools/ci/test_release_manifest.py` covers release-manifest and Cloud deployment identity
invariants.

`tools/ci/test_release_publish_workflow.py` covers:

- protected/least-privilege publication;
- package-write only in protected publication;
- source-on-main and green-check preflight;
- ephemeral environment-only Android signing material;
- signed Android identity/SBOM/attestation regeneration;
- exact runtime archive loading with no backend/Web rebuild;
- fail-closed GHCR identity lookup and collision handling;
- digest-qualified Self-Hosted image evidence;
- deterministic Self-Hosted operator bundle contents;
- immutable GitHub tag/Release publication;
- immutable external Action/Syft pins.

Deployment/runtime guards additionally cover one-manifest topology, Production launcher
safety, Development source-build boundaries, release-version/image binding and real
Self-Hosted startup/recovery behavior.

#914 performs the real protected publication and captures G5-02/G5-03 evidence.
