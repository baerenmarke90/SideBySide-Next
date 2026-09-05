#!/usr/bin/env python3
"""Focused tests for #519 immutable release-manifest invariants."""

from __future__ import annotations

import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
MODULE_PATH = ROOT / "scripts/release_manifest.py"
spec = importlib.util.spec_from_file_location("release_manifest", MODULE_PATH)
assert spec and spec.loader
release_manifest = importlib.util.module_from_spec(spec)
spec.loader.exec_module(release_manifest)


class ReleaseManifestTest(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.artifacts = [
            ("backend-runtime", "backend-runtime.image.tar", ["api", "worker", "migrate"]),
            ("web-runtime", "web-runtime.image.tar", ["web"]),
            ("android-apk", "android/sidebyside-release-unsigned.apk", ["android-apk"]),
            ("android-aab", "android/sidebyside-release-unsigned.aab", ["android-aab"]),
        ]
        evidence_artifacts = []
        for artifact_id, relative, roles in self.artifacts:
            artifact = self.root / relative
            artifact.parent.mkdir(parents=True, exist_ok=True)
            artifact.write_bytes((artifact_id + "-artifact").encode())
            sbom = self.root / "sbom" / f"{artifact_id}.spdx.json"
            sbom.parent.mkdir(parents=True, exist_ok=True)
            sbom.write_text('{"spdxVersion":"SPDX-2.3"}\n', encoding="utf-8")
            evidence_artifacts.append(
                {
                    "id": artifact_id,
                    "roles": roles,
                    "path": relative,
                    "sha256": release_manifest.sha256(artifact),
                    "sbom": sbom.relative_to(self.root).as_posix(),
                    "sbomSha256": release_manifest.sha256(sbom),
                }
            )
        self.evidence = {
            "schemaVersion": 1,
            "sourceRevision": "a" * 40,
            "sbomFormat": "SPDX-2.3 JSON",
            "artifacts": evidence_artifacts,
            "android": {
                "applicationId": "de.sidebyside.app",
                "versionName": "0.1.0",
                "versionCode": 7,
                "signing": "unsigned-evidence-only",
            },
        }

    def tearDown(self) -> None:
        self.temp.cleanup()

    def _previous_manifest(self, *, signing: str = "signed-release") -> dict[str, object]:
        return {
            "schemaVersion": 1,
            "product": {"name": "SideBySide", "version": "0.0.9", "tag": "v0.0.9"},
            "sourceRevision": "b" * 40,
            "artifacts": self.evidence["artifacts"],
            "android": {
                **self.evidence["android"],
                "versionName": "0.0.9",
                "signing": signing,
            },
            "previousKnownGood": None,
            "rollback": {
                "applicationReleaseSelectable": False,
                "databaseRollbackImplied": False,
                "schemaCompatibilityReviewRequired": True,
                "authority": ["#190", "#375"],
            },
        }

    def test_valid_evidence_has_one_coherent_release_identity(self) -> None:
        source, artifacts, android = release_manifest.validate_evidence(self.evidence, "0.1.0")
        self.assertEqual(source, "a" * 40)
        self.assertEqual({item["id"] for item in artifacts}, release_manifest.REQUIRED_ARTIFACTS)
        self.assertEqual(android["applicationId"], "de.sidebyside.app")

    def test_mixed_android_version_is_rejected(self) -> None:
        self.evidence["android"]["versionName"] = "0.1.1"
        with self.assertRaises(release_manifest.ManifestError):
            release_manifest.validate_evidence(self.evidence, "0.1.0")

    def test_backend_roles_cannot_split_release_identity(self) -> None:
        self.evidence["artifacts"][0]["roles"] = ["api"]
        with self.assertRaises(release_manifest.ManifestError):
            release_manifest.validate_evidence(self.evidence, "0.1.0")

    def test_final_manifest_rejects_unsigned_android(self) -> None:
        source, artifacts, android = release_manifest.validate_evidence(self.evidence, "0.1.0")
        manifest = {
            "schemaVersion": 1,
            "product": {"name": "SideBySide", "version": "0.1.0", "tag": "v0.1.0"},
            "sourceRevision": source,
            "artifacts": artifacts,
            "android": android,
            "previousKnownGood": None,
            "rollback": {
                "applicationReleaseSelectable": False,
                "databaseRollbackImplied": False,
                "schemaCompatibilityReviewRequired": True,
                "authority": ["#190", "#375"],
            },
        }
        with self.assertRaises(release_manifest.ManifestError):
            release_manifest.validate_manifest_shape(manifest, require_signed_android=True)

    def test_verifier_detects_artifact_tampering(self) -> None:
        source, artifacts, android = release_manifest.validate_evidence(self.evidence, "0.1.0")
        manifest = {
            "schemaVersion": 1,
            "product": {"name": "SideBySide", "version": "0.1.0", "tag": "v0.1.0"},
            "sourceRevision": source,
            "artifacts": artifacts,
            "android": android,
            "previousKnownGood": None,
            "rollback": {
                "applicationReleaseSelectable": False,
                "databaseRollbackImplied": False,
                "schemaCompatibilityReviewRequired": True,
                "authority": ["#190", "#375"],
            },
        }
        path = self.root / "release-manifest.json"
        path.write_text(json.dumps(manifest), encoding="utf-8")
        (self.root / "backend-runtime.image.tar").write_bytes(b"tampered")
        args = type("Args", (), {"manifest": path, "artifact_root": self.root, "require_signed_android": False})()
        with self.assertRaises(release_manifest.ManifestError):
            release_manifest.verify_manifest(args)

    def test_previous_known_good_comes_from_a_signed_manifest_not_free_form_sha(self) -> None:
        previous = self.root / "previous.json"
        previous.write_text(json.dumps(self._previous_manifest()), encoding="utf-8")
        identity = release_manifest.previous_identity(previous, False)
        self.assertEqual(identity["sourceRevision"], "b" * 40)
        self.assertEqual(identity["tag"], "v0.0.9")

    def test_previous_known_good_rejects_unsigned_candidate_manifest(self) -> None:
        previous = self.root / "unsigned-previous.json"
        previous.write_text(
            json.dumps(self._previous_manifest(signing="unsigned-evidence-only")),
            encoding="utf-8",
        )
        with self.assertRaises(release_manifest.ManifestError):
            release_manifest.previous_identity(previous, False)


if __name__ == "__main__":
    unittest.main()
