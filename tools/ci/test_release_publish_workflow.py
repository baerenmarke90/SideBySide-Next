#!/usr/bin/env python3
"""Fail-closed contract checks for the #519 protected publication workflow."""

from __future__ import annotations

import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
WORKFLOW = ROOT / ".github/workflows/release-publish.yml"

EXTERNAL_ACTION_PINS = {
    "actions/checkout": "3d3c42e5aac5ba805825da76410c181273ba90b1",
    "actions/setup-java": "dd06d9cba3e5552c54d9f8ea23572deb30010f7c",
    "gradle/actions/setup-gradle": "9c971963bec38e04b3d30dcc455b5382be2fdbfb",
    "actions/upload-artifact": "ea165f8d65b6e75b540449e92b4886f43607fa02",
    "actions/download-artifact": "634f93cb2916e3fdff6788551b99b062d0335ce0",
}


def action_uses(text: str) -> list[str]:
    return [match.group(1) for match in re.finditer(r"^\s*-?\s*uses:\s*([^\s#]+)", text, re.MULTILINE)]


class ReleasePublishWorkflowContractTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.workflow = WORKFLOW.read_text(encoding="utf-8")

    def test_no_privileged_pull_request_target_trigger(self) -> None:
        self.assertNotIn("pull_request_target", self.workflow)
        self.assertIn("if: github.event_name == 'workflow_dispatch'", self.workflow)

    def test_privileged_job_is_protected_and_least_privileged(self) -> None:
        self.assertIn("environment:\n      name: production-release", self.workflow)
        self.assertIn(
            "permissions:\n      contents: write\n      id-token: write\n      attestations: write",
            self.workflow,
        )
        self.assertIn("permissions:\n  contents: read", self.workflow)
        self.assertNotIn("packages: write", self.workflow)

    def test_publish_requires_explicit_confirmation_and_merged_main_source(self) -> None:
        self.assertIn("confirm_publish:", self.workflow)
        self.assertIn('if [ "$CONFIRM_PUBLISH" != "true" ]', self.workflow)
        self.assertIn("git merge-base --is-ancestor \"$GITHUB_SHA\" origin/main", self.workflow)
        self.assertIn("Require existing repository checks to be green", self.workflow)

    def test_release_identity_is_immutable_and_not_overwritten(self) -> None:
        self.assertGreaterEqual(self.workflow.count("git ls-remote --exit-code --tags"), 2)
        self.assertGreaterEqual(self.workflow.count("gh release view"), 2)
        self.assertIn('--target "$GITHUB_SHA"', self.workflow)
        self.assertIn('git rev-list -n 1 "$tag"', self.workflow)
        self.assertIn("cmp --silent", self.workflow)

    def test_signing_material_is_environment_only_and_ephemeral(self) -> None:
        required = (
            "${{ secrets.SBS_RELEASE_KEYSTORE_BASE64 }}",
            "${{ secrets.SBS_RELEASE_KEYSTORE_PASSWORD }}",
            "${{ secrets.SBS_RELEASE_KEY_ALIAS }}",
            "${{ secrets.SBS_RELEASE_KEY_PASSWORD }}",
        )
        for marker in required:
            with self.subTest(marker=marker):
                self.assertIn(marker, self.workflow)
        self.assertIn('keystore="$RUNNER_TEMP/sidebyside-upload.jks"', self.workflow)
        self.assertIn("trap 'rm -f \"$keystore\"' EXIT", self.workflow)
        self.assertNotIn("actions/upload-artifact@", self.workflow.split("Build and verify final signed Android artifacts", 1)[0])

    def test_signed_android_is_verified_and_replaces_unsigned_candidate(self) -> None:
        self.assertIn('apksigner" verify "$apk"', self.workflow)
        self.assertIn('jarsigner -verify "$aab"', self.workflow)
        self.assertIn('manifest application-id "$apk"', self.workflow)
        self.assertIn('"de.sidebyside.app"', self.workflow)
        self.assertIn("android/sidebyside-release.apk", self.workflow)
        self.assertIn("android/sidebyside-release.aab", self.workflow)
        self.assertIn('android["signing"] = "signed-release"', self.workflow)
        self.assertIn("sidebyside-release-unsigned.apk", self.workflow)
        self.assertIn("sidebyside-release-unsigned.aab", self.workflow)

    def test_final_signed_bytes_get_fresh_sbom_and_attestations(self) -> None:
        self.assertIn('syft scan "file:release-evidence/android/sidebyside-release.apk"', self.workflow)
        self.assertIn('syft scan "file:release-evidence/android/sidebyside-release.aab"', self.workflow)
        self.assertIn("bundle-prefix: android-apk-signed", self.workflow)
        self.assertIn("bundle-prefix: android-aab-signed", self.workflow)
        self.assertIn("gh attestation verify", self.workflow)
        self.assertIn("release-publish.yml", self.workflow)

    def test_final_manifest_requires_signed_android_and_preserves_rollback_boundary(self) -> None:
        self.assertGreaterEqual(self.workflow.count("--require-signed-android"), 2)
        self.assertIn("previous-known-good/sidebyside-release-manifest.json", self.workflow)
        self.assertIn("#190 and #375", self.workflow)

    def test_external_actions_are_immutable_sha_pins(self) -> None:
        seen: dict[str, set[str]] = {}
        for use in action_uses(self.workflow):
            if use.startswith("./"):
                continue
            self.assertIn("@", use, use)
            name, ref = use.rsplit("@", 1)
            self.assertRegex(ref, r"^[0-9a-f]{40}$", use)
            seen.setdefault(name, set()).add(ref)

        self.assertEqual(set(seen), set(EXTERNAL_ACTION_PINS))
        for name, expected in EXTERNAL_ACTION_PINS.items():
            self.assertEqual(seen[name], {expected})

    def test_syft_is_version_and_digest_pinned(self) -> None:
        self.assertIn('SYFT_VERSION: "1.42.3"', self.workflow)
        self.assertIn(
            'SYFT_LINUX_AMD64_SHA256: "0d6be741479eddd2c8644a288990c04f3df0d609bbc1599a005532a9dff63509"',
            self.workflow,
        )
        self.assertIn("sha256sum --check --strict", self.workflow)


if __name__ == "__main__":
    unittest.main()
