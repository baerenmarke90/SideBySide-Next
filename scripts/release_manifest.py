#!/usr/bin/env python3
"""Build and verify the immutable SideBySide release manifest.

The manifest consumes #193 release evidence. It does not build artifacts, sign
Android packages or infer database rollback safety.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path, PurePosixPath
from typing import Any

SEMVER = re.compile(r"^(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)(?:-([0-9A-Za-z.-]+))?(?:\+([0-9A-Za-z.-]+))?$")
SHA40 = re.compile(r"^[0-9a-f]{40}$")
SHA256 = re.compile(r"^[0-9a-f]{64}$")
REQUIRED_ARTIFACTS = {"backend-runtime", "web-runtime", "android-apk", "android-aab"}
BACKEND_ROLES = {"api", "worker", "migrate"}


class ManifestError(ValueError):
    pass


def load_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ManifestError(f"Cannot read JSON from {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise ManifestError(f"{path} must contain a JSON object")
    return value


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def safe_relative_path(value: str) -> PurePosixPath:
    path = PurePosixPath(value)
    if path.is_absolute() or ".." in path.parts or not path.parts:
        raise ManifestError(f"Unsafe artifact path: {value!r}")
    return path


def require_semver(version: str) -> None:
    if not SEMVER.fullmatch(version):
        raise ManifestError(f"Product version is not SemVer: {version!r}")


def validate_evidence(evidence: dict[str, Any], version: str) -> tuple[str, list[dict[str, Any]], dict[str, Any]]:
    require_semver(version)
    if evidence.get("schemaVersion") != 1:
        raise ManifestError("Unsupported #193 evidence schema")
    source = evidence.get("sourceRevision")
    if not isinstance(source, str) or not SHA40.fullmatch(source):
        raise ManifestError("Evidence sourceRevision must be one immutable 40-hex commit SHA")
    if evidence.get("sbomFormat") != "SPDX-2.3 JSON":
        raise ManifestError("Release evidence must use SPDX-2.3 JSON")

    artifacts = evidence.get("artifacts")
    if not isinstance(artifacts, list):
        raise ManifestError("Evidence artifacts must be a list")
    by_id: dict[str, dict[str, Any]] = {}
    for artifact in artifacts:
        if not isinstance(artifact, dict):
            raise ManifestError("Every evidence artifact must be an object")
        artifact_id = artifact.get("id")
        if not isinstance(artifact_id, str) or artifact_id in by_id:
            raise ManifestError(f"Duplicate or invalid artifact id: {artifact_id!r}")
        safe_relative_path(str(artifact.get("path", "")))
        safe_relative_path(str(artifact.get("sbom", "")))
        if not SHA256.fullmatch(str(artifact.get("sha256", ""))):
            raise ManifestError(f"Invalid SHA-256 for {artifact_id}")
        if not SHA256.fullmatch(str(artifact.get("sbomSha256", ""))):
            raise ManifestError(f"Invalid SBOM SHA-256 for {artifact_id}")
        by_id[artifact_id] = artifact

    if set(by_id) != REQUIRED_ARTIFACTS:
        raise ManifestError(
            "Release evidence must contain exactly backend, Web, APK and AAB artifacts"
        )
    if set(by_id["backend-runtime"].get("roles", [])) != BACKEND_ROLES:
        raise ManifestError("Backend artifact must cover API, worker and migrate together")
    if set(by_id["web-runtime"].get("roles", [])) != {"web"}:
        raise ManifestError("Web artifact role is inconsistent")

    android = evidence.get("android")
    if not isinstance(android, dict):
        raise ManifestError("Evidence lacks Android release identity")
    if android.get("applicationId") != "de.sidebyside.app":
        raise ManifestError("Android release applicationId must be de.sidebyside.app")
    if android.get("versionName") != version:
        raise ManifestError(
            f"Android versionName {android.get('versionName')!r} does not match product version {version!r}"
        )
    version_code = android.get("versionCode")
    if not isinstance(version_code, int) or isinstance(version_code, bool) or version_code <= 0:
        raise ManifestError("Android versionCode must be a positive integer")

    return source, [by_id[key] for key in sorted(by_id)], android


def previous_identity(path: Path | None, initial_release: bool) -> dict[str, Any] | None:
    if initial_release and path is not None:
        raise ManifestError("Initial release cannot also declare a previous-known-good manifest")
    if initial_release:
        return None
    if path is None:
        raise ManifestError("Non-initial release requires the previous-known-good release manifest")
    previous = load_json(path)
    validate_manifest_shape(previous, require_signed_android=False)
    product = previous["product"]
    return {
        "version": product["version"],
        "tag": product["tag"],
        "sourceRevision": previous["sourceRevision"],
        "manifestSha256": sha256(path),
    }


def validate_manifest_shape(manifest: dict[str, Any], *, require_signed_android: bool) -> None:
    if manifest.get("schemaVersion") != 1:
        raise ManifestError("Unsupported release-manifest schema")
    product = manifest.get("product")
    if not isinstance(product, dict):
        raise ManifestError("Release manifest has no product identity")
    version = product.get("version")
    if not isinstance(version, str):
        raise ManifestError("Release version is missing")
    require_semver(version)
    if product.get("tag") != f"v{version}":
        raise ManifestError("Release tag must be exactly v<product-version>")
    source = manifest.get("sourceRevision")
    if not isinstance(source, str) or not SHA40.fullmatch(source):
        raise ManifestError("Release sourceRevision is not an immutable commit SHA")

    artifacts = manifest.get("artifacts")
    if not isinstance(artifacts, list):
        raise ManifestError("Release artifacts must be a list")
    ids = set()
    for artifact in artifacts:
        if not isinstance(artifact, dict):
            raise ManifestError("Invalid release artifact entry")
        artifact_id = artifact.get("id")
        ids.add(artifact_id)
        safe_relative_path(str(artifact.get("path", "")))
        safe_relative_path(str(artifact.get("sbom", "")))
        if not SHA256.fullmatch(str(artifact.get("sha256", ""))):
            raise ManifestError(f"Invalid release artifact SHA-256: {artifact_id}")
        if not SHA256.fullmatch(str(artifact.get("sbomSha256", ""))):
            raise ManifestError(f"Invalid release SBOM SHA-256: {artifact_id}")
    if ids != REQUIRED_ARTIFACTS:
        raise ManifestError("Release artifact set is incomplete or mixed")

    android = manifest.get("android")
    if not isinstance(android, dict):
        raise ManifestError("Release manifest lacks Android identity")
    if android.get("applicationId") != "de.sidebyside.app":
        raise ManifestError("Release manifest has the wrong Android applicationId")
    if android.get("versionName") != version:
        raise ManifestError("Release Android versionName differs from product version")
    if require_signed_android and android.get("signing") != "signed-release":
        raise ManifestError("Final publication requires a signed-release Android artifact set")

    rollback = manifest.get("rollback")
    if not isinstance(rollback, dict) or rollback.get("databaseRollbackImplied") is not False:
        raise ManifestError("Manifest must preserve the explicit database rollback boundary")


def build_manifest(args: argparse.Namespace) -> int:
    evidence = load_json(args.evidence_index)
    source, artifacts, android = validate_evidence(evidence, args.version)
    previous = previous_identity(args.previous_manifest, args.initial_release)

    manifest = {
        "schemaVersion": 1,
        "product": {
            "name": "SideBySide",
            "version": args.version,
            "tag": f"v{args.version}",
        },
        "sourceRevision": source,
        "artifacts": artifacts,
        "android": android,
        "evidence": {
            "format": evidence["sbomFormat"],
            "source": "#193 release-evidence",
        },
        "previousKnownGood": previous,
        "rollback": {
            "applicationReleaseSelectable": previous is not None,
            "databaseRollbackImplied": False,
            "schemaCompatibilityReviewRequired": True,
            "authority": ["#190", "#375"],
        },
    }
    validate_manifest_shape(manifest, require_signed_android=args.require_signed_android)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"Wrote release manifest for {args.version} at {source}")
    return 0


def verify_manifest(args: argparse.Namespace) -> int:
    manifest = load_json(args.manifest)
    validate_manifest_shape(manifest, require_signed_android=args.require_signed_android)
    root = args.artifact_root.resolve()
    for artifact in manifest["artifacts"]:
        artifact_path = root.joinpath(*safe_relative_path(artifact["path"]).parts)
        sbom_path = root.joinpath(*safe_relative_path(artifact["sbom"]).parts)
        if not artifact_path.is_file() or sha256(artifact_path) != artifact["sha256"]:
            raise ManifestError(f"Artifact digest mismatch: {artifact['id']}")
        if not sbom_path.is_file() or sha256(sbom_path) != artifact["sbomSha256"]:
            raise ManifestError(f"SBOM digest mismatch: {artifact['id']}")
    print(
        f"Verified release manifest {manifest['product']['tag']} at {manifest['sourceRevision']}"
    )
    return 0


def parser() -> argparse.ArgumentParser:
    root = argparse.ArgumentParser(description=__doc__)
    sub = root.add_subparsers(dest="command", required=True)

    build = sub.add_parser("build", help="Build a release manifest from #193 evidence")
    build.add_argument("--evidence-index", type=Path, required=True)
    build.add_argument("--version", required=True)
    previous = build.add_mutually_exclusive_group(required=True)
    previous.add_argument("--previous-manifest", type=Path)
    previous.add_argument("--initial-release", action="store_true")
    build.add_argument("--require-signed-android", action="store_true")
    build.add_argument("--output", type=Path, required=True)
    build.set_defaults(handler=build_manifest)

    verify = sub.add_parser("verify", help="Verify manifest structure and artifact digests")
    verify.add_argument("--manifest", type=Path, required=True)
    verify.add_argument("--artifact-root", type=Path, required=True)
    verify.add_argument("--require-signed-android", action="store_true")
    verify.set_defaults(handler=verify_manifest)
    return root


def main() -> int:
    args = parser().parse_args()
    try:
        return args.handler(args)
    except ManifestError as exc:
        print(f"release-manifest error: {exc}")
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
